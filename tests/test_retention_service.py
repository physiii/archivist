"""Unit tests for retention_service — policy decisions, dry-run safety, deletion."""

import json
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def _write_sidecar(root: Path, source: str, start_offset_s: float, duration_s: float, labels, has_speech=False, transcript_text=None):
    """Create a sidecar + zero-byte segment file at a given age relative to now."""
    now = time.time()
    start = now + start_offset_s
    end = start + duration_s
    ts = time.strftime("%H%M%S", time.gmtime(start))
    day = time.strftime("%Y-%m-%d", time.gmtime(start))
    src_dir = root / "segments" / source / day
    src_dir.mkdir(parents=True, exist_ok=True)
    seg_path = src_dir / f"{ts}.mp4"
    sidecar_path = src_dir / f"{ts}.json"
    seg_path.write_bytes(b"x" * 100)
    transcript_path = None
    if has_speech and transcript_text:
        tdir = root / "transcripts" / source / day
        tdir.mkdir(parents=True, exist_ok=True)
        transcript_path = tdir / f"{ts}.vtt"
        transcript_path.write_text(transcript_text)
    sidecar = {
        "segment_path": str(seg_path),
        "source": source,
        "start_wall_ts": start,
        "end_wall_ts": end,
        "duration_s": duration_s,
        "bytes": 100,
        "labels": labels,
        "has_speech": has_speech,
        "transcript_path": str(transcript_path) if transcript_path else None,
    }
    sidecar_path.write_text(json.dumps(sidecar))
    return sidecar_path, seg_path, transcript_path


@pytest.fixture
def tmp_media(tmp_path, monkeypatch):
    import retention_service as rs
    import events_bus

    monkeypatch.setattr(rs, "SEGMENTS_ROOT", tmp_path / "segments")
    monkeypatch.setattr(rs, "NAS_SEGMENTS_ROOT", tmp_path / "segments")  # tests scan tmp, not the NAS
    monkeypatch.setattr(rs, "KEYFRAMES_ROOT", tmp_path / "keyframes")
    monkeypatch.setattr(rs, "TRANSCRIPTS_ROOT", tmp_path / "transcripts")
    (tmp_path / "segments").mkdir()

    published = []
    monkeypatch.setattr(events_bus, "publish",
                        lambda t, s, p, **k: published.append((t, s, p)))
    return rs, tmp_path, published


def test_keeps_young_segment_regardless_of_labels(tmp_media, monkeypatch):
    rs, tmp, _ = tmp_media
    monkeypatch.setattr(rs, "FALLBACK_CONTINUOUS_DAYS", 1.0)  # <1d = continuous
    # 1h old, no labels → kept because age < 1d continuous window
    _write_sidecar(tmp, "office", -3600, 60, [])
    out = rs.run_gc_pass(dry_run=True)
    assert out["kept"] == 1
    assert out["deleted"] == 0


def test_keeps_old_segment_with_keep_label(tmp_media, monkeypatch):
    rs, tmp, _ = tmp_media
    # Very short continuous window so the 2h-old segment enters event-only phase
    monkeypatch.setattr(rs, "FALLBACK_CONTINUOUS_DAYS", 0.01)  # ~14 min
    monkeypatch.setattr(rs, "FALLBACK_EVENT_DAYS", 365)
    _write_sidecar(tmp, "office", -7200, 60, ["person", "motion"])
    out = rs.run_gc_pass(dry_run=True)
    assert out["kept"] == 1
    assert out["deleted"] == 0


def test_keeps_old_segment_with_speech(tmp_media, monkeypatch):
    rs, tmp, _ = tmp_media
    monkeypatch.setattr(rs, "FALLBACK_CONTINUOUS_DAYS", 0.01)
    monkeypatch.setattr(rs, "FALLBACK_EVENT_DAYS", 365)
    _write_sidecar(tmp, "office", -7200, 60, [], has_speech=True,
                   transcript_text="Hello there, this is real speech content.")
    out = rs.run_gc_pass(dry_run=True)
    assert out["kept"] == 1
    assert out["deleted"] == 0


def test_deletes_old_unlabeled_segment_dry_run(tmp_media, monkeypatch):
    rs, tmp, published = tmp_media
    monkeypatch.setattr(rs, "FALLBACK_CONTINUOUS_DAYS", 0.01)
    monkeypatch.setattr(rs, "FALLBACK_EVENT_DAYS", 365)
    sidecar, seg, _ = _write_sidecar(tmp, "office", -7200, 60, [])
    out = rs.run_gc_pass(dry_run=True)
    assert out["deleted"] == 1
    # Dry-run must NOT remove files
    assert sidecar.exists()
    assert seg.exists()
    topics = [t for t, _, _ in published]
    assert "segment.deleted" in topics
    payload = [p for t, _, p in published if t == "segment.deleted"][0]
    assert payload["dry_run"] is True


def test_deletes_old_unlabeled_segment_apply(tmp_media, monkeypatch):
    rs, tmp, published = tmp_media
    monkeypatch.setattr(rs, "FALLBACK_CONTINUOUS_DAYS", 0.01)
    monkeypatch.setattr(rs, "FALLBACK_EVENT_DAYS", 365)
    sidecar, seg, tvtt = _write_sidecar(tmp, "office", -7200, 60, [],
                                         has_speech=True, transcript_text="hi")  # short => no speech keep
    out = rs.run_gc_pass(dry_run=False)
    assert out["deleted"] == 1
    assert out["bytes_freed"] > 0
    assert not sidecar.exists()
    assert not seg.exists()
    assert not tvtt.exists()
    payload = [p for t, _, p in published if t == "segment.deleted"][0]
    assert payload["dry_run"] is False


def test_short_speech_does_not_save_segment(tmp_media, monkeypatch):
    rs, tmp, _ = tmp_media
    monkeypatch.setattr(rs, "FALLBACK_CONTINUOUS_DAYS", 0.01)
    monkeypatch.setattr(rs, "FALLBACK_EVENT_DAYS", 365)
    monkeypatch.setattr(rs, "KEEP_SPEECH_MIN_CHARS", 10)
    _write_sidecar(tmp, "office", -7200, 60, [], has_speech=True, transcript_text="hi")
    out = rs.run_gc_pass(dry_run=True)
    assert out["deleted"] == 1


def test_custom_keep_labels_override(tmp_media, monkeypatch):
    rs, tmp, _ = tmp_media
    monkeypatch.setattr(rs, "FALLBACK_CONTINUOUS_DAYS", 0.01)
    monkeypatch.setattr(rs, "FALLBACK_EVENT_DAYS", 365)
    monkeypatch.setattr(rs, "FALLBACK_KEEP_LABELS", {"doorbell"})
    _write_sidecar(tmp, "office", -7200, 60, ["person"])  # 'person' no longer a keeper
    _write_sidecar(tmp, "office", -7300, 60, ["doorbell"])  # keeper
    out = rs.run_gc_pass(dry_run=True)
    assert out["kept"] == 1
    assert out["deleted"] == 1


def test_past_event_window_expires(tmp_media, monkeypatch):
    rs, tmp, _ = tmp_media
    monkeypatch.setattr(rs, "FALLBACK_CONTINUOUS_DAYS", 0.01)
    monkeypatch.setattr(rs, "FALLBACK_EVENT_DAYS", 0.02)  # tiny event window
    # Even with a keep label, past the event window it expires.
    _write_sidecar(tmp, "office", -7200, 60, ["person"])
    out = rs.run_gc_pass(dry_run=True)
    assert out["deleted"] == 1
    assert out["reasons"]["expired"] == 1
