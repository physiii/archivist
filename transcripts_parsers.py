from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import webvtt
try:
    import srt
except Exception:  # pragma: no cover
    srt = None  # type: ignore


@dataclass(frozen=True)
class Cue:
    start_ms: int
    end_ms: int
    text: str


def _parse_timecode_ms(value: str) -> int | None:
    raw = str(value or "").strip().replace(",", ".")
    if not raw:
        return None
    if raw.isdigit():
        return int(raw) * 1000
    if re.fullmatch(r"\d+\.\d+", raw):
        return int(float(raw) * 1000)
    parts = raw.split(":")
    if len(parts) > 3:
        return None
    try:
        if len(parts) == 3:
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = float(parts[2])
        elif len(parts) == 2:
            hours = 0
            minutes = int(parts[0])
            seconds = float(parts[1])
        else:
            return None
    except ValueError:
        return None
    total_ms = int((hours * 3600 + minutes * 60 + seconds) * 1000)
    return max(total_ms, 0)


def _clean_text(value: str) -> str:
    cleaned = " ".join(str(value or "").split()).strip()
    # Ignore punctuation-only fragments like ".", "...", or ". . . ."
    # that often appear in subtitle exports and pollute search quality.
    if not cleaned:
        return ""
    if not re.search(r"[A-Za-z0-9]", cleaned):
        return ""
    return cleaned


def parse_vtt(path: Path) -> list[Cue]:
    cues: list[Cue] = []
    for caption in webvtt.read(str(path)):
        start_ms = _parse_timecode_ms(caption.start)
        end_ms = _parse_timecode_ms(caption.end)
        text = _clean_text(caption.text)
        if start_ms is None or end_ms is None or end_ms <= start_ms or not text:
            continue
        cues.append(Cue(start_ms=start_ms, end_ms=end_ms, text=text))
    return cues


def parse_srt_file(path: Path) -> list[Cue]:
    content = path.read_text(encoding="utf-8", errors="replace")
    cues: list[Cue] = []
    if srt is not None:
        for item in srt.parse(content):
            start_ms = int(item.start.total_seconds() * 1000)
            end_ms = int(item.end.total_seconds() * 1000)
            text = _clean_text(item.content)
            if end_ms <= start_ms or not text:
                continue
            cues.append(Cue(start_ms=start_ms, end_ms=end_ms, text=text))
        return cues

    blocks = re.split(r"\n\s*\n", content.replace("\r\n", "\n"))
    for block in blocks:
        lines = [line.strip() for line in block.split("\n") if line.strip()]
        if len(lines) < 2:
            continue
        time_line_idx = 1 if "-->" in lines[1] else 0
        if "-->" not in lines[time_line_idx]:
            continue
        start_raw, end_raw = [part.strip() for part in lines[time_line_idx].split("-->", 1)]
        start_ms = _parse_timecode_ms(start_raw)
        end_ms = _parse_timecode_ms(end_raw)
        text = _clean_text(" ".join(lines[time_line_idx + 1 :]))
        if start_ms is None or end_ms is None or end_ms <= start_ms or not text:
            continue
        cues.append(Cue(start_ms=start_ms, end_ms=end_ms, text=text))
    return cues


def _pick_key(keys: Iterable[str], row: dict[str, str]) -> str | None:
    lookup = {str(k).strip().lower(): k for k in row.keys()}
    for key in keys:
        if key in lookup:
            return lookup[key]
    return None


def parse_tsv_file(path: Path) -> list[Cue]:
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if not reader.fieldnames:
            return []
        field_row = {name: name for name in reader.fieldnames}
        start_key = _pick_key(("start", "start_time", "start_ms", "timestamp", "time"), field_row)
        end_key = _pick_key(("end", "end_time", "end_ms", "stop"), field_row)
        text_key = _pick_key(("text", "transcript", "caption", "content", "utterance"), field_row)
        if not start_key or not end_key or not text_key:
            return []

        cues: list[Cue] = []
        for row in reader:
            start_raw = str(row.get(start_key, "") or "").strip()
            end_raw = str(row.get(end_key, "") or "").strip()
            start_ms = _parse_timecode_ms(start_raw)
            end_ms = _parse_timecode_ms(end_raw)
            # Heuristic for numeric TSV timestamps:
            # Many transcript exports store start/end as milliseconds (e.g. 120000, 121000).
            # If integer parsing implies unrealistically long cue durations, treat values as ms.
            if (
                start_ms is not None
                and end_ms is not None
                and start_raw.isdigit()
                and end_raw.isdigit()
                and end_ms > start_ms
                and (end_ms - start_ms) > 120_000
            ):
                start_num = int(start_raw)
                end_num = int(end_raw)
                if end_num > start_num:
                    numeric_duration = end_num - start_num
                    if 50 <= numeric_duration <= 120_000:
                        start_ms = start_num
                        end_ms = end_num
            text = _clean_text(row.get(text_key, ""))
            if start_ms is None or end_ms is None or end_ms <= start_ms or not text:
                continue
            cues.append(Cue(start_ms=start_ms, end_ms=end_ms, text=text))
        return cues


def parse_txt_file(path: Path) -> list[Cue]:
    text = path.read_text(encoding="utf-8", errors="replace")
    cleaned = _clean_text(text)
    if not cleaned:
        return []
    approx_words = max(1, len(cleaned.split()))
    approx_duration_ms = max(8_000, approx_words * 350)
    return [Cue(start_ms=0, end_ms=approx_duration_ms, text=cleaned)]


def parse_transcript(path: str | Path) -> tuple[list[Cue], str | None]:
    file_path = Path(path)
    ext = file_path.suffix.lower()
    try:
        if ext == ".vtt":
            cues = parse_vtt(file_path)
            return cues, None if cues else "No valid VTT cues found"
        if ext == ".srt":
            cues = parse_srt_file(file_path)
            return cues, None if cues else "No valid SRT cues found"
        if ext == ".tsv":
            cues = parse_tsv_file(file_path)
            if cues:
                return cues, None
            return [], "TSV missing confident timecode columns (start/end/text)"
        if ext == ".txt":
            cues = parse_txt_file(file_path)
            return cues, None if cues else "No readable TXT transcript content found"
        return [], f"Unsupported transcript extension: {ext}"
    except Exception as exc:
        return [], f"Failed to parse transcript: {exc}"
