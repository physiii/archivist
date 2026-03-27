from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import indexing_service
from documents.chunking import chunk_document_segments
from documents.extract import ExtractedDocumentSegment, extract_document_segments


def test_extract_document_segments_pdf(monkeypatch):
    class FakePage:
        def __init__(self, text: str) -> None:
            self._text = text

        def extract_text(self) -> str:
            return self._text

    class FakePdfReader:
        def __init__(self, _path: str) -> None:
            self.pages = [FakePage("Page one text"), FakePage(""), FakePage("Page three text")]

    monkeypatch.setattr("documents.extract.PdfReader", FakePdfReader)

    segments, reason = extract_document_segments("/tmp/sample.pdf")

    assert reason is None
    assert segments == [
        ExtractedDocumentSegment(tag="page_1", text="Page one text", kind="page"),
        ExtractedDocumentSegment(tag="page_3", text="Page three text", kind="page"),
    ]


def test_extract_document_segments_docx(monkeypatch):
    class FakeParagraph:
        def __init__(self, text: str) -> None:
            self.text = text

    class FakeDocument:
        def __init__(self, _path: str) -> None:
            self.paragraphs = [FakeParagraph("Intro"), FakeParagraph(""), FakeParagraph("Body text here")]

    monkeypatch.setattr("documents.extract.Document", FakeDocument)

    segments, reason = extract_document_segments("/tmp/sample.docx")

    assert reason is None
    assert segments == [
        ExtractedDocumentSegment(tag="block_1", text="Intro"),
        ExtractedDocumentSegment(tag="block_2", text="Body text here"),
    ]


def test_chunk_document_segments_splits_long_text(monkeypatch):
    monkeypatch.setenv("DOCUMENT_CHUNK_TARGET_WORDS", "30")
    monkeypatch.setenv("DOCUMENT_CHUNK_MAX_WORDS", "45")
    monkeypatch.setenv("DOCUMENT_CHUNK_OVERLAP_WORDS", "10")
    long_text = " ".join(["document"] * 260)

    chunks = chunk_document_segments(
        [ExtractedDocumentSegment(tag="page_1", text=long_text)],
        path="/docs/example.pdf",
        source_id="/docs/example.pdf",
        doc_type="pdf",
    )

    assert len(chunks) >= 2
    assert all(chunk.source_type == "document" for chunk in chunks)
    assert all(chunk.doc_type == "pdf" for chunk in chunks)
    assert all(chunk.t_start_ms == 0 for chunk in chunks)
    assert chunks[0].tag.startswith("page_1")


def test_indexing_file_discovery_includes_documents(tmp_path):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    for name in ["a.pdf", "b.docx", "c.txt", "ignore.jpg"]:
        (docs_dir / name).write_text("x", encoding="utf-8")

    files = indexing_service._iter_target_files(str(docs_dir), recursive=False)
    count, timed_out = indexing_service._target_scan_count(str(docs_dir), recursive=False)

    assert timed_out is False
    assert count == 3
    assert [Path(path).name for path in files] == ["a.pdf", "b.docx", "c.txt"]


def test_collection_and_version_dispatch_for_documents():
    assert indexing_service._collection_name_for_path("/docs/file.pdf") == indexing_service.DOCUMENTS_COLLECTION
    assert indexing_service._collection_name_for_path("/docs/file.docx") == indexing_service.DOCUMENTS_COLLECTION
    assert indexing_service._content_version_for_path("/docs/file.pdf") == indexing_service.DOCUMENT_CONTENT_VERSION
    assert indexing_service._collection_name_for_path("/docs/file.vtt") == indexing_service.TRANSCRIPT_COLLECTION


def test_plain_txt_defaults_to_documents(tmp_path):
    path = tmp_path / "notes.txt"
    path.write_text("These are plain notes without timestamps.\nThey should be chunked like a document.", encoding="utf-8")

    assert indexing_service._collection_name_for_path(str(path)) == indexing_service.DOCUMENTS_COLLECTION
    assert indexing_service._content_version_for_path(str(path)) == indexing_service.DOCUMENT_CONTENT_VERSION


def test_timestamped_txt_stays_transcript(tmp_path):
    path = tmp_path / "transcript.txt"
    path.write_text(
        "00:00:01 Speaker one starts here\n00:00:07 Speaker two responds\n00:00:12 Closing line",
        encoding="utf-8",
    )

    assert indexing_service._collection_name_for_path(str(path)) == indexing_service.TRANSCRIPT_COLLECTION
    assert indexing_service._content_version_for_path(str(path)) == indexing_service.INDEXING_CONTENT_VERSION
