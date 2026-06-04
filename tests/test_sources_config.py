"""Unit tests for sources_config — YAML parse, enabled filter, zones/mask decode."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


FIXTURE = """\
defaults:
  rtsp_transport: tcp
  reconnect_min_s: 3
  reconnect_max_s: 30
  audio:
    sample_rate: 16000
sources:
  - id: office
    enabled: true
    kind: camera
    location: office
    audio_url: "rtsp://cam/office"
    video_main_url: "rtsp://cam/office"
    video_sub_url: "rtsp://cam/office_sub"
    detect: {width: 704, height: 480, fps: 10}
    motion:
      threshold: 40
      contour_area: 11
      mask: [0.1, 0.2, 0.3, 0.4]
    zones:
      Door: [0.1, 0.1, 0.9, 0.9]
  - id: kids
    enabled: false
    kind: camera
    location: kids
    audio_url: "rtsp://cam/kids"
    video_main_url: "rtsp://cam/kids"
    video_sub_url: null
  - id: mic
    enabled: true
    kind: mic
    location: office
    audio_url: "rtsp://mic"
    video_main_url: null
    video_sub_url: null
"""


@pytest.fixture
def config_path(tmp_path):
    p = tmp_path / "sources.yml"
    p.write_text(FIXTURE)
    return str(p)


def test_load_returns_all_sources(config_path):
    import sources_config
    sources = sources_config.load_sources(config_path, force=True)
    assert set(sources.keys()) == {"office", "kids", "mic"}


def test_enabled_filter(config_path):
    import sources_config
    sources_config.load_sources(config_path, force=True)
    enabled = sources_config.enabled_sources(config_path)
    ids = sorted(s.id for s in enabled)
    assert ids == ["mic", "office"]


def test_defaults_applied(config_path):
    import sources_config
    office = sources_config.get_source("office", config_path)
    assert office is not None
    assert office.rtsp_transport == "tcp"
    assert office.reconnect_min_s == 3.0
    assert office.reconnect_max_s == 30.0
    assert office.audio.sample_rate == 16000


def test_motion_and_zones_decoded(config_path):
    import sources_config
    office = sources_config.get_source("office", config_path)
    assert office.motion is not None
    assert office.motion.threshold == 40
    assert office.motion.mask == (0.1, 0.2, 0.3, 0.4)
    assert "Door" in office.zones
    assert office.zones["Door"] == (0.1, 0.1, 0.9, 0.9)


def test_mic_source_has_no_video(config_path):
    import sources_config
    mic = sources_config.get_source("mic", config_path)
    assert mic.kind == "mic"
    assert mic.video_main_url is None
    assert mic.video_sub_url is None


def test_mtime_cache(config_path, tmp_path):
    import sources_config
    sources_config.load_sources(config_path, force=True)
    # Re-read should hit cache (mtime unchanged)
    before = sources_config.load_sources(config_path)
    assert before is sources_config.load_sources(config_path)
    # Rewrite file with different mtime — should invalidate
    import time as _t, os as _os
    new_mtime = _os.path.getmtime(config_path) + 10
    _os.utime(config_path, (new_mtime, new_mtime))
    Path(config_path).write_text(FIXTURE.replace("enabled: true", "enabled: false", 1))
    after = sources_config.load_sources(config_path)
    assert "office" in after
    assert after["office"].enabled is False
