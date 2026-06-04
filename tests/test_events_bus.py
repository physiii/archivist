"""Unit tests for events_bus — envelope shape, monotonic seq, round-trip."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class _FakeRedis:
    """Minimal XADD/XREAD/XGROUP stub for unit tests."""

    def __init__(self):
        self.streams: dict[str, list[tuple[str, dict]]] = {}
        self.maxlen_calls: list[int] = []

    def xadd(self, stream, fields, maxlen=None, approximate=False):
        # Simulate approximate MAXLEN trim.
        entries = self.streams.setdefault(stream, [])
        entry_id = f"{len(entries)+1}-0"
        entries.append((entry_id, dict(fields)))
        if maxlen is not None:
            self.maxlen_calls.append(maxlen)
            if len(entries) > maxlen:
                del entries[: len(entries) - maxlen]
        return entry_id

    def xgroup_create(self, stream, group, id="$", mkstream=True):
        self.streams.setdefault(stream, [])

    def xreadgroup(self, group, consumer, streams, count=10, block=0):
        return []

    def xack(self, stream, group, entry_id):
        return 1


@pytest.fixture
def bus():
    import events_bus
    fake = _FakeRedis()
    events_bus.set_client(fake)
    yield events_bus, fake
    events_bus.set_client(None)


def test_publish_envelope_shape(bus):
    events_bus, fake = bus
    entry_id = events_bus.publish("transcript.final", "office", {"text": "hello"}, stream_ts=1.25)
    assert entry_id is not None
    stream = events_bus.stream_name("transcript.final")
    assert stream in fake.streams
    _, fields = fake.streams[stream][0]
    assert fields["v"] == "1"
    assert fields["type"] == "transcript.final"
    assert fields["source"] == "office"
    assert fields["seq"] == "1"
    assert fields["stream_ts"] == "1.250000"
    assert json.loads(fields["payload"])["text"] == "hello"


def test_monotonic_seq_per_source_topic(bus):
    events_bus, fake = bus
    for _ in range(3):
        events_bus.publish("transcript.final", "office", {})
    events_bus.publish("transcript.final", "kids", {})
    events_bus.publish("detection.motion", "office", {})

    stream = events_bus.stream_name("transcript.final")
    office_seqs = [int(f["seq"]) for _, f in fake.streams[stream] if f["source"] == "office"]
    kids_seqs = [int(f["seq"]) for _, f in fake.streams[stream] if f["source"] == "kids"]
    assert office_seqs == [1, 2, 3]
    assert kids_seqs == [1]
    motion_stream = events_bus.stream_name("detection.motion")
    motion_seqs = [int(f["seq"]) for _, f in fake.streams[motion_stream]]
    assert motion_seqs == [1]


def test_parse_entry_roundtrip(bus):
    events_bus, fake = bus
    events_bus.publish("transcript.final", "office", {"text": "hi", "n": 7}, stream_ts=42.0)
    stream = events_bus.stream_name("transcript.final")
    _, fields = fake.streams[stream][0]
    parsed = events_bus.parse_entry(fields)
    assert parsed["type"] == "transcript.final"
    assert parsed["source"] == "office"
    assert parsed["stream_ts"] == pytest.approx(42.0)
    assert parsed["seq"] == 1
    assert parsed["payload"] == {"text": "hi", "n": 7}
    assert parsed["wall_ts"] > 0


def test_maxlen_honored(bus, monkeypatch):
    events_bus, fake = bus
    monkeypatch.setattr(events_bus, "STREAM_MAXLEN", 5)
    for i in range(20):
        events_bus.publish("detection.motion", "office", {"i": i})
    stream = events_bus.stream_name("detection.motion")
    assert len(fake.streams[stream]) == 5
    assert 5 in fake.maxlen_calls
