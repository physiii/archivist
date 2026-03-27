from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from docx import Document
from pypdf import PdfReader


@dataclass(frozen=True)
class ExtractedDocumentSegment:
    tag: str
    text: str
    kind: str = "body"


def _normalize_text(value: str) -> str:
    lines = [line.strip() for line in str(value or "").replace("\r", "\n").split("\n")]
    cleaned = [line for line in lines if line]
    return "\n".join(cleaned).strip()


def _normalize_pdf_text(value: str) -> str:
    raw_lines = [line.strip() for line in str(value or "").replace("\r", "\n").split("\n")]
    merged: list[str] = []
    current = ""
    for line in raw_lines:
        if not line:
            if current:
                merged.append(current.strip())
                current = ""
            continue
        if not current:
            current = line
            continue
        if current.endswith((".", ":", ";", "?", "!")) or line[:1].isupper():
            merged.append(current.strip())
            current = line
        else:
            current = f"{current} {line}"
    if current:
        merged.append(current.strip())
    return "\n\n".join(item for item in merged if item).strip()


def _extract_pdf_segments(path: str) -> tuple[list[ExtractedDocumentSegment], str | None]:
    try:
        reader = PdfReader(path)
    except Exception as exc:
        return [], f"PDF parse failed ({exc})"
    segments: list[ExtractedDocumentSegment] = []
    for index, page in enumerate(reader.pages, start=1):
        try:
            text = _normalize_pdf_text(page.extract_text() or "")
        except Exception as exc:
            return [], f"PDF page extraction failed on page {index} ({exc})"
        if text:
            segments.append(ExtractedDocumentSegment(tag=f"page_{index}", text=text, kind="page"))
    if not segments:
        return [], "No extractable text found in PDF"
    return segments, None


def _extract_docx_segments(path: str) -> tuple[list[ExtractedDocumentSegment], str | None]:
    try:
        document = Document(path)
    except Exception as exc:
        return [], f"DOCX parse failed ({exc})"
    segments: list[ExtractedDocumentSegment] = []
    block_index = 0
    for paragraph in document.paragraphs:
        text = _normalize_text(paragraph.text)
        if not text:
            continue
        block_index += 1
        style_name = str(getattr(getattr(paragraph, "style", None), "name", "") or "").lower()
        kind = "heading" if style_name.startswith("heading") or style_name == "title" else "body"
        tag_prefix = "heading" if kind == "heading" else "block"
        segments.append(ExtractedDocumentSegment(tag=f"{tag_prefix}_{block_index}", text=text, kind=kind))
    if not segments:
        return [], "No extractable text found in DOCX"
    return segments, None


def _extract_txt_segments(path: str) -> tuple[list[ExtractedDocumentSegment], str | None]:
    try:
        text = _normalize_text(Path(path).read_text(encoding="utf-8", errors="replace"))
    except Exception as exc:
        return [], f"TXT parse failed ({exc})"
    if not text:
        return [], "No extractable text found in TXT"
    return [ExtractedDocumentSegment(tag="text_1", text=text, kind="body")], None


def extract_document_segments(path: str) -> tuple[list[ExtractedDocumentSegment], str | None]:
    suffix = Path(path).suffix.lower()
    if suffix == ".pdf":
        return _extract_pdf_segments(path)
    if suffix == ".docx":
        return _extract_docx_segments(path)
    if suffix == ".txt":
        return _extract_txt_segments(path)
    return [], f"Unsupported document type: {suffix or 'unknown'}"
