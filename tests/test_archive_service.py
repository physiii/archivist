"""Unit tests for archive_service — local→NAS moves, sidecar rewrite, milvus rewrite call."""

import json
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture
def staged(tmp_path, monkeypatch):
    """Set up a fake local SSD staging dir and fake NAS dir, redirect globals, stub milvus + events."""
    import archive_service as arc
    import events_bus

    local = tmp_path / "local" / "segments"
    keyframes = tmp_path / "local" / "keyframes"
    nas = tmp_path / "nas" / "recording"
    local.mkdir(parents=True)
    keyframes.mkdir(parents=True)

    monkeypatch.setattr(arc, "LOCAL_SEGMENTS_ROOT", local)
    monkeypatch.setattr(arc, "LOCAL_KEYFRAMES_ROOT", keyframes)
    monkeypatch.setattr(arc, "NAS_SEGMENTS_ROOT", nas)

    published = []
    monkeypatch.setattr(events_bus, "publish",
                        lambda t, s, p, **k: published.append((t, s, p)))

    milvus_calls = []
    def _fake_batch(pairs):
        for old, new in pairs.items():
            milvus_calls.append((old, new))
        return len(pairs) * 3  # pretend ~3 rows per segment
    monkeypatch.setattr(arc, "_milvus_rewrite_segment_path",
                        lambda old, new: (milvus_calls.append((old, new)), 3)[1])
    monkeypatch.setattr(arc, "_milvus_rewrite_batch", _fake_batch)

    return arc, local, keyframes, nas, published, milvus_calls


def _make_segment(local_root: Path, keyframes_root: Path, source: str, age_hours: float,
                  labels=None, n_keyframes: int = 2):
    now = time.time()
    start = now - age_hours * 3600
    end = start + 60
    day = time.strftime("%Y-%m-%d", time.gmtime(start))
    hms = time.strftime("%H%M%S", time.gmtime(start))
    seg_dir = local_root / source / day
    kf_dir = keyframes_root / source / day
    seg_dir.mkdir(parents=True, exist_ok=True)
    kf_dir.mkdir(parents=True, exist_ok=True)
    seg_file = seg_dir / f"{hms}.mp4"
    seg_file.write_bytes(b"x" * 1024)
    sidecar_file = seg_dir / f"{hms}.json"
    sidecar_file.write_text(json.dumps({
        "segment_path": str(seg_file),
        "source": source,
        "start_wall_ts": start,
        "end_wall_ts": end,
        "labels": labels or [],
        "has_speech": False,
        "transcript_path": None,
    }))
    kf_files = []
    for i in range(n_keyframes):
        kf = kf_dir / f"{hms}_{i:03d}.jpg"
        kf.write_bytes(b"j" * 256)
        # Set mtime within the segment window so the mover picks it up
        import os as _os
        _os.utime(kf, (start + 1 + i, start + 1 + i))
        kf_files.append(kf)
    return sidecar_file, seg_file, kf_files


def test_holds_young_segments(staged):
    arc, local, kfs, nas, published, _ = staged
    sidecar, seg, _ = _make_segment(local, kfs, "office", age_hours=1)  # 1h < 48h default
    out = arc.run_archive_pass(backfill=False, dry_run=False)
    assert out["moved"] == 0
    assert out["skipped_young"] == 1
    assert sidecar.exists()
    assert seg.exists()


def test_moves_old_segment_on_sweep(staged):
    arc, local, kfs, nas, published, milvus_calls = staged
    sidecar, seg, kf_files = _make_segment(local, kfs, "office", age_hours=72, n_keyframes=3)
    out = arc.run_archive_pass(backfill=False, dry_run=False)
    assert out["moved"] == 1
    assert out["failed"] == 0
    # Local files gone
    assert not seg.exists()
    assert not sidecar.exists()
    for kf in kf_files:
        assert not kf.exists()
    # NAS has the segment + sidecar + keyframes
    nas_files = list(nas.rglob("*"))
    names = sorted(p.name for p in nas_files if p.is_file())
    assert any(n.endswith(".mp4") for n in names)
    assert any(n.endswith(".json") for n in names)
    assert sum(1 for n in names if n.endswith(".jpg")) == 3
    # Milvus rewrite was called
    assert len(milvus_calls) == 1
    old, new = milvus_calls[0]
    assert str(seg) == old
    assert new.startswith(str(nas))
    # segment.archived event published
    topics = [t for t, _, _ in published]
    assert "segment.archived" in topics


def test_sidecar_rewritten_on_move(staged):
    arc, local, kfs, nas, _, _ = staged
    _, seg, _ = _make_segment(local, kfs, "office", age_hours=72)
    arc.run_archive_pass(backfill=False, dry_run=False)
    # Locate the new sidecar on NAS
    sidecars = list(nas.rglob("*.json"))
    assert len(sidecars) == 1
    new_sidecar = json.loads(sidecars[0].read_text())
    assert new_sidecar["segment_path"].startswith(str(nas))
    assert new_sidecar["archived_to"] == "nas"
    assert new_sidecar["archived_wall_ts"] > 0


def test_backfill_ignores_hold(staged):
    arc, local, kfs, nas, _, _ = staged
    # 1h old — normally below hold, but backfill moves anyway
    _make_segment(local, kfs, "office", age_hours=1)
    out = arc.run_archive_pass(backfill=True, dry_run=False)
    assert out["moved"] == 1


def test_dry_run_does_not_move(staged):
    arc, local, kfs, nas, _, milvus_calls = staged
    sidecar, seg, _ = _make_segment(local, kfs, "office", age_hours=72)
    out = arc.run_archive_pass(backfill=False, dry_run=True)
    assert out["moved"] == 1  # "would move" counter
    # But files are still local
    assert sidecar.exists()
    assert seg.exists()
    assert not any(nas.rglob("*.mp4"))
    # And milvus wasn't called
    assert len(milvus_calls) == 0


def test_skips_already_archived_sidecars(staged):
    arc, local, kfs, nas, _, _ = staged
    # Create an already-archived sidecar (archived_to=nas) in local — the sweep should skip it
    day = time.strftime("%Y-%m-%d", time.gmtime())
    d = local / "office" / day
    d.mkdir(parents=True)
    (d / "000000.mp4").write_bytes(b"x")
    (d / "000000.json").write_text(json.dumps({
        "segment_path": str(d / "000000.mp4"),
        "source": "office",
        "start_wall_ts": time.time() - 100000,
        "end_wall_ts": time.time() - 99940,
        "labels": [],
        "archived_to": "nas",
    }))
    out = arc.run_archive_pass(backfill=True, dry_run=False)
    assert out["moved"] == 0


def test_missing_segment_file_cleans_up_stale_sidecar(staged):
    arc, local, kfs, nas, _, _ = staged
    day = time.strftime("%Y-%m-%d", time.gmtime())
    d = local / "office" / day
    d.mkdir(parents=True)
    sidecar = d / "111111.json"
    sidecar.write_text(json.dumps({
        "segment_path": str(d / "does_not_exist.mp4"),
        "source": "office",
        "start_wall_ts": time.time() - 100000,
        "end_wall_ts": time.time() - 99940,
        "labels": [],
    }))
    arc.run_archive_pass(backfill=True, dry_run=False)
    # Stale sidecar was cleaned up
    assert not sidecar.exists()
