from __future__ import annotations

from hashlib import sha256
from dataclasses import dataclass
from pathlib import Path
import re
from collections import Counter

try:
    from .parsers import Cue
except Exception:
    from transcripts_parsers import Cue


@dataclass(frozen=True)
class TranscriptChunk:
    chunk_id: str
    source_id: str
    path: str
    text: str
    t_start_ms: int
    t_end_ms: int
    chunk_duration_s: int
    level: int
    parent_id: str | None
    doc_type: str
    source_type: str
    topic_label: str | None
    language: str | None
    tag: str


def _chunk_id(source_id: str, level: int, start_ms: int, duration_s: int) -> str:
    seed = f"{source_id}|{level}|{start_ms}|{duration_s}"
    return sha256(seed.encode("utf-8")).hexdigest()[:24]


def _is_informative_text(text: str, min_words: int, min_chars: int = 16) -> bool:
    normalized = " ".join((text or "").split())
    if len(normalized) < min_chars:
        return False
    if not re.search(r"[A-Za-z0-9]", normalized):
        return False
    words = [tok.lower() for tok in re.findall(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?", normalized)]
    if len(words) < min_words:
        return False
    unique = set(words)
    if len(words) >= 4 and len(unique) == 1:
        return False
    short_dominance = Counter(words).most_common(1)[0][1] / float(len(words))
    if len(words) <= 5 and short_dominance >= 0.5 and len(unique) <= 3:
        return False
    if len(words) >= 5 and len(unique) < 3:
        return False
    if len(words) >= 8:
        unique_ratio = len(unique) / float(len(words))
        if unique_ratio < 0.35:
            return False
    dominant = Counter(words).most_common(1)[0][1]
    if len(words) >= 6 and (dominant / float(len(words))) >= 0.5 and len(unique) <= 4:
        return False
    return True


def build_time_window_chunks(
    cues: list[Cue],
    path: str | Path,
    source_id: str | None = None,
    source_type: str = "transcript",
    doc_type: str = "transcript",
    topic_label: str | None = None,
    language: str | None = None,
    durations_s: tuple[int, ...] = (60, 3600),
    strides_s: tuple[int, ...] | None = None,
    min_words_level1: int = 0,
    min_words_level2: int = 0,
) -> list[TranscriptChunk]:
    clean_path = str(path)
    clean_source_id = source_id or clean_path
    chunks: list[TranscriptChunk] = []
    if not cues:
        return chunks

    min_start = min(cue.start_ms for cue in cues)
    max_end = max(cue.end_ms for cue in cues)
    doc_level = 3
    doc_id = _chunk_id(clean_source_id, doc_level, min_start, max(1, int((max_end - min_start) / 1000)))

    # Build higher-level windows first so 1-minute chunks can point to parent hour chunk IDs.
    by_duration: dict[int, dict[int, list[str]]] = {}
    stride_by_duration: dict[int, int] = {}
    strides_lookup = {dur: dur for dur in durations_s}
    if strides_s and len(strides_s) == len(durations_s):
        strides_lookup = {dur: max(1, int(stride)) for dur, stride in zip(durations_s, strides_s)}
    for duration_s in durations_s:
        if duration_s <= 0:
            continue
        duration_ms = duration_s * 1000
        stride_s = max(1, int(strides_lookup.get(duration_s, duration_s)))
        stride_ms = stride_s * 1000
        stride_by_duration[duration_s] = stride_ms
        by_window: dict[int, list[str]] = {}
        for cue in cues:
            rel = max(0, cue.start_ms - min_start)
            last_idx = rel // stride_ms
            first_idx = max(0, (rel - duration_ms + stride_ms) // stride_ms)
            for window_idx in range(first_idx, last_idx + 1):
                by_window.setdefault(window_idx, []).append(cue.text)
        by_duration[duration_s] = by_window

    hour_ids_by_window: dict[int, str] = {}
    hour_windows: list[tuple[int, int, str]] = []
    if max_end - min_start <= 3600 * 1000:
        # For sub-hour files, make the hour chunk span the actual file bounds.
        chunk_start = min_start
        chunk_end = max_end
        chunk_text = " ".join(" ".join(cue.text for cue in cues).split())
        if chunk_text and (min_words_level2 <= 0 or _is_informative_text(chunk_text, min_words=min_words_level2)):
            chunk_id = _chunk_id(clean_source_id, 2, chunk_start, 3600)
            hour_ids_by_window[min_start // (3600 * 1000)] = chunk_id
            hour_windows.append((chunk_start, chunk_end, chunk_id))
            chunks.append(
                TranscriptChunk(
                    chunk_id=chunk_id,
                    source_id=clean_source_id,
                    path=clean_path,
                    text=chunk_text,
                    t_start_ms=chunk_start,
                    t_end_ms=chunk_end,
                    chunk_duration_s=3600,
                    level=2,
                    parent_id=doc_id,
                    doc_type=doc_type,
                    source_type=source_type,
                    topic_label=topic_label,
                    language=language,
                    tag="60_min_chunk",
                )
            )
    else:
        hour_stride_ms = stride_by_duration.get(3600, 3600 * 1000)
        for window_idx in sorted(by_duration.get(3600, {}).keys()):
            duration_ms = 3600 * 1000
            chunk_start = min_start + window_idx * hour_stride_ms
            chunk_end = chunk_start + duration_ms
            chunk_text = " ".join(" ".join(by_duration[3600][window_idx]).split())
            if not chunk_text or (min_words_level2 > 0 and not _is_informative_text(chunk_text, min_words=min_words_level2)):
                continue
            chunk_id = _chunk_id(clean_source_id, 2, chunk_start, 3600)
            hour_ids_by_window[window_idx] = chunk_id
            hour_windows.append((chunk_start, chunk_end, chunk_id))
            chunks.append(
                TranscriptChunk(
                    chunk_id=chunk_id,
                    source_id=clean_source_id,
                    path=clean_path,
                    text=chunk_text,
                    t_start_ms=chunk_start,
                    t_end_ms=chunk_end,
                    chunk_duration_s=3600,
                    level=2,
                    parent_id=doc_id,
                    doc_type=doc_type,
                    source_type=source_type,
                    topic_label=topic_label,
                    language=language,
                    tag="60_min_chunk",
                )
            )

    for duration_s in sorted(by_duration.keys()):
        if duration_s == 3600:
            continue
        duration_ms = duration_s * 1000
        stride_ms = stride_by_duration.get(duration_s, duration_ms)
        level = 1 if duration_s == 60 else 0
        tag = "1_min_chunk" if duration_s == 60 else f"{duration_s}_sec_chunk"
        for window_idx in sorted(by_duration[duration_s].keys()):
            joined = " ".join(by_duration[duration_s][window_idx]).strip()
            if not joined:
                continue
            if level == 1 and min_words_level1 > 0 and not _is_informative_text(joined, min_words=min_words_level1):
                continue
            chunk_start = min_start + window_idx * stride_ms
            chunk_end = chunk_start + duration_ms
            parent_id = None
            if level == 1:
                parent_id = doc_id
                for h_start, h_end, h_id in hour_windows:
                    if chunk_start >= h_start and chunk_start < h_end:
                        parent_id = h_id
                        break
            chunk_id = _chunk_id(clean_source_id, level, chunk_start, duration_s)
            chunks.append(
                TranscriptChunk(
                    chunk_id=chunk_id,
                    source_id=clean_source_id,
                    path=clean_path,
                    text=" ".join(joined.split()),
                    t_start_ms=chunk_start,
                    t_end_ms=chunk_end,
                    chunk_duration_s=duration_s,
                    level=level,
                    parent_id=parent_id,
                    doc_type=doc_type,
                    source_type=source_type,
                    topic_label=topic_label,
                    language=language,
                    tag=tag,
                )
            )

    # Add a doc-level row for routing/classification workflows.
    full_text = " ".join(" ".join(cue.text for cue in cues).split())
    doc_min_words = max(8, int(min_words_level2 or 0))
    if full_text and _is_informative_text(full_text, min_words=doc_min_words, min_chars=24):
        chunks.append(
            TranscriptChunk(
                chunk_id=doc_id,
                source_id=clean_source_id,
                path=clean_path,
                text=full_text,
                t_start_ms=min_start,
                t_end_ms=max_end,
                chunk_duration_s=max(1, int((max_end - min_start) / 1000)),
                level=doc_level,
                parent_id=None,
                doc_type=doc_type,
                source_type=source_type,
                topic_label=topic_label,
                language=language,
                tag="doc_chunk",
            )
        )

    chunks.sort(key=lambda item: (item.level, item.t_start_ms, item.chunk_duration_s))
    return chunks
