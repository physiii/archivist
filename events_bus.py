"""Redis Streams event bus for archivist.

Publishes versioned envelopes to `archivist:v1:<topic>` streams. Consumers use
XREADGROUP via consume(). Kept minimal; no framework, no async.

Envelope:
    {
        "v": 1,
        "type": "<topic>",
        "source": "<source_id>",
        "wall_ts": <float unix seconds>,
        "stream_ts": <float seconds into stream, or None>,
        "seq": <monotonic int per (source, topic)>,
        "payload": "<json-serialized topic-specific dict>"
    }

Redis stores stream fields as strings, so we JSON-encode `payload` and the
primitive fields are stringified by redis-py. Consumers decode with parse_entry().
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from collections import defaultdict
from typing import Callable, Iterable, Optional

logger = logging.getLogger("archivist.events")

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
STREAM_PREFIX = os.getenv("ARCHIVIST_STREAM_PREFIX", "archivist:v1")
STREAM_MAXLEN = int(os.getenv("ARCHIVIST_STREAM_MAXLEN", "100000"))

_client = None
_client_lock = threading.Lock()
_seq_lock = threading.Lock()
_seq: dict[tuple[str, str], int] = defaultdict(int)


def _get_client():
    """Lazy-import redis so tests can monkeypatch with fakeredis."""
    global _client
    if _client is not None:
        return _client
    with _client_lock:
        if _client is None:
            import redis  # local import so missing dep doesn't block module import
            _client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    return _client


def set_client(client) -> None:
    """Inject a client for tests (e.g., fakeredis)."""
    global _client
    with _client_lock:
        _client = client
    with _seq_lock:
        _seq.clear()


def stream_name(topic: str) -> str:
    return f"{STREAM_PREFIX}:{topic}"


def _next_seq(source: str, topic: str) -> int:
    with _seq_lock:
        _seq[(source, topic)] += 1
        return _seq[(source, topic)]


def publish(
    topic: str,
    source: str,
    payload: dict,
    stream_ts: Optional[float] = None,
    wall_ts: Optional[float] = None,
) -> Optional[str]:
    """Publish one event to Redis Streams. Returns the entry id, or None on failure."""
    wall = wall_ts if wall_ts is not None else time.time()
    seq = _next_seq(source, topic)
    entry = {
        "v": "1",
        "type": topic,
        "source": source,
        "wall_ts": f"{wall:.6f}",
        "stream_ts": "" if stream_ts is None else f"{stream_ts:.6f}",
        "seq": str(seq),
        "payload": json.dumps(payload, separators=(",", ":"), ensure_ascii=False),
    }
    try:
        client = _get_client()
        return client.xadd(
            stream_name(topic),
            entry,
            maxlen=STREAM_MAXLEN,
            approximate=True,
        )
    except Exception:
        logger.exception("publish failed: topic=%s source=%s", topic, source)
        return None


def parse_entry(entry: dict) -> dict:
    """Decode a raw XREAD/XREADGROUP entry back into typed fields."""
    out = {
        "v": int(entry.get("v", "1")),
        "type": entry.get("type", ""),
        "source": entry.get("source", ""),
        "wall_ts": float(entry.get("wall_ts") or 0.0),
        "stream_ts": float(entry["stream_ts"]) if entry.get("stream_ts") else None,
        "seq": int(entry.get("seq") or 0),
    }
    raw_payload = entry.get("payload") or "{}"
    try:
        out["payload"] = json.loads(raw_payload)
    except Exception:
        out["payload"] = {"_raw": raw_payload}
    return out


def ensure_group(topic: str, group: str) -> None:
    """Create consumer group if missing; idempotent."""
    client = _get_client()
    stream = stream_name(topic)
    try:
        client.xgroup_create(stream, group, id="$", mkstream=True)
    except Exception as exc:
        if "BUSYGROUP" not in str(exc):
            raise


def consume(
    topics: Iterable[str],
    group: str,
    consumer: str,
    handler: Callable[[str, str, dict], None],
    stop_event: threading.Event,
    block_ms: int = 2000,
    batch: int = 16,
) -> None:
    """Block-read events from one or more topics into a consumer group.

    `handler(topic, entry_id, parsed_entry)` is called for each event.
    Auto-acks after the handler returns without exception.
    """
    client = _get_client()
    streams = [stream_name(t) for t in topics]
    for t in topics:
        ensure_group(t, group)
    last_ids = {s: ">" for s in streams}
    while not stop_event.is_set():
        try:
            resp = client.xreadgroup(
                group,
                consumer,
                last_ids,
                count=batch,
                block=block_ms,
            )
        except Exception:
            logger.exception("xreadgroup failed; sleeping 1s")
            if stop_event.wait(1.0):
                return
            continue
        if not resp:
            continue
        for stream, entries in resp:
            topic = stream.split(":", 2)[-1] if ":" in stream else stream
            for entry_id, raw in entries:
                try:
                    handler(topic, entry_id, parse_entry(raw))
                    client.xack(stream, group, entry_id)
                except Exception:
                    logger.exception(
                        "handler raised for topic=%s id=%s", topic, entry_id
                    )
