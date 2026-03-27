from __future__ import annotations

import os
import re
from hashlib import sha256

from documents.extract import ExtractedDocumentSegment
from transcripts.chunking import TranscriptChunk


def _chunk_id(source_id: str, tag: str, index: int) -> str:
    seed = f"{source_id}|{tag}|{index}"
    return sha256(seed.encode("utf-8")).hexdigest()[:24]


def _normalize_text(value: str) -> str:
    text = str(value or "").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _is_informative_text(value: str, min_words: int = 6, min_chars: int = 80) -> bool:
    clean = _normalize_text(value)
    if len(clean) < min_chars:
        return False
    words = re.findall(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?", clean)
    return len(words) >= min_words


def _word_count(value: str) -> int:
    return len(re.findall(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?", value))


def _split_sentences(text: str) -> list[str]:
    clean = re.sub(r"\s+", " ", text).strip()
    if not clean:
        return []
    pieces = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", clean)
    return [piece.strip() for piece in pieces if piece.strip()]


def _segment_units(segment: ExtractedDocumentSegment) -> list[tuple[str, str]]:
    if segment.kind == "heading":
        return [("heading", _normalize_text(segment.text))]
    text = _normalize_text(segment.text)
    if not text:
        return []
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n+", text) if part.strip()]
    if not paragraphs:
        paragraphs = [text]
    units: list[tuple[str, str]] = []
    for paragraph in paragraphs:
        normalized = _normalize_text(paragraph)
        if not normalized:
            continue
        if _word_count(normalized) > 180:
            for sentence in _split_sentences(normalized):
                if sentence:
                    units.append(("sentence", sentence))
        else:
            units.append(("paragraph", normalized))
    return units


def _trim_overlap_text(text: str, overlap_words: int) -> str:
    words = re.findall(r"\S+", text)
    if len(words) <= overlap_words:
        return text.strip()
    return " ".join(words[-overlap_words:]).strip()


def _split_word_windows(text: str, max_words: int, overlap_words: int) -> list[str]:
    words = re.findall(r"\S+", text)
    if not words:
        return []
    if len(words) <= max_words:
        return [" ".join(words)]
    out: list[str] = []
    start = 0
    step = max(1, max_words - overlap_words)
    while start < len(words):
        piece = " ".join(words[start : start + max_words]).strip()
        if piece:
            out.append(piece)
        if start + max_words >= len(words):
            break
        start += step
    return out


def chunk_document_segments(
    segments: list[ExtractedDocumentSegment],
    *,
    path: str,
    source_id: str,
    doc_type: str,
    source_type: str = "document",
    language: str | None = None,
) -> list[TranscriptChunk]:
    target_words = max(120, int(os.getenv("DOCUMENT_CHUNK_TARGET_WORDS", "320")))
    max_words = max(target_words, int(os.getenv("DOCUMENT_CHUNK_MAX_WORDS", "520")))
    overlap_words = max(20, int(os.getenv("DOCUMENT_CHUNK_OVERLAP_WORDS", "80")))
    chunks: list[TranscriptChunk] = []
    pending_heading: str | None = None
    current_parts: list[str] = []
    current_tags: list[str] = []
    current_words = 0
    chunk_index = 0

    def flush_chunk() -> None:
        nonlocal current_parts, current_tags, current_words, chunk_index, pending_heading
        if not current_parts:
            return
        piece = "\n\n".join(part.strip() for part in current_parts if part.strip()).strip()
        if not _is_informative_text(piece):
            current_parts = []
            current_tags = []
            current_words = 0
            return
        chunk_index += 1
        if current_tags:
            tag = current_tags[0] if len(current_tags) == 1 else f"{current_tags[0]}__{current_tags[-1]}"
        else:
            tag = f"chunk_{chunk_index}"
        overlap_seed = _trim_overlap_text(piece, overlap_words=overlap_words)
        chunks.append(
            TranscriptChunk(
                chunk_id=_chunk_id(source_id, tag, chunk_index),
                source_id=source_id,
                path=path,
                text=piece,
                t_start_ms=0,
                t_end_ms=0,
                chunk_duration_s=0,
                level=0,
                parent_id=None,
                doc_type=doc_type,
                source_type=source_type,
                topic_label=None,
                language=language,
                tag=tag,
            )
        )
        current_parts = [overlap_seed] if overlap_seed else []
        current_tags = [current_tags[-1]] if current_tags else []
        current_words = _word_count(overlap_seed)
        if pending_heading and not current_parts:
            current_parts = [pending_heading]
            current_words = _word_count(pending_heading)
            pending_heading = None

    for segment in segments:
        for unit_kind, text in _segment_units(segment):
            if unit_kind == "heading":
                heading_text = text.strip()
                if not heading_text:
                    continue
                if current_parts and current_words >= target_words:
                    flush_chunk()
                pending_heading = heading_text
                continue
            piece = text.strip()
            if not piece:
                continue
            sub_parts = [piece]
            if _word_count(piece) > max_words:
                sub_parts = _split_word_windows(piece, max_words=max_words, overlap_words=overlap_words)
            for sub_piece in sub_parts:
                if not sub_piece:
                    continue
                part_words = _word_count(sub_piece)
                if pending_heading:
                    heading_words = _word_count(pending_heading)
                    if not current_parts:
                        current_parts.append(pending_heading)
                        current_words += heading_words
                    elif current_parts[0] != pending_heading:
                        current_parts.append(pending_heading)
                        current_words += heading_words
                    pending_heading = None
                if current_parts and current_words + part_words > max_words:
                    flush_chunk()
                    if pending_heading:
                        current_parts.append(pending_heading)
                        current_words += _word_count(pending_heading)
                        pending_heading = None
                current_parts.append(sub_piece)
                current_tags.append(segment.tag)
                current_words += part_words
                if current_words >= target_words:
                    flush_chunk()

    if pending_heading and not current_parts:
        current_parts = [pending_heading]
        current_words = _word_count(pending_heading)
    if current_parts:
        flush_chunk()

    normalized_chunks: list[TranscriptChunk] = []
    for chunk in chunks:
        piece = _normalize_text(chunk.text)
        if not _is_informative_text(piece):
            continue
        normalized_chunks.append(
            TranscriptChunk(
                chunk_id=chunk.chunk_id,
                source_id=source_id,
                path=path,
                text=piece,
                t_start_ms=0,
                t_end_ms=0,
                chunk_duration_s=0,
                level=0,
                parent_id=None,
                doc_type=doc_type,
                source_type=source_type,
                topic_label=None,
                language=language,
                tag=chunk.tag,
            )
        )
    return normalized_chunks
