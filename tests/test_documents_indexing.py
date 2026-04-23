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


def test_indexing_file_discovery_dedupes_media_sidecars(tmp_path):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "meeting.mkv").write_bytes(b"media")
    (docs_dir / "meeting.vtt").write_text(
        "WEBVTT\n\n00:00:00.000 --> 00:00:04.000\nhello from the sidecar\n",
        encoding="utf-8",
    )
    (docs_dir / "audio.mp3").write_bytes(b"media")

    files = indexing_service._iter_target_files(str(docs_dir), recursive=False)
    count, timed_out = indexing_service._target_scan_count(str(docs_dir), recursive=False)

    assert timed_out is False
    assert count == 2
    assert [Path(path).name for path in files] == ["audio.mp3", "meeting.vtt"]


def test_media_files_routed_to_pipeline(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "media.pipeline.process_media_file",
        lambda path, **kwargs: calls.append(path) or {"media_id": "test"},
    )
    chunks, reason = indexing_service._parse_file_job("/tmp/test.mp4", "/tmp/test.mp4")
    assert chunks == []
    assert reason == "routed:media"
    assert len(calls) == 1
    assert calls[0] == "/tmp/test.mp4"


def test_media_extensions_excluded_from_direct_indexing():
    for ext in indexing_service.MEDIA_EXTS:
        assert indexing_service._is_media_file(f"/tmp/test{ext}"), f"{ext} should be recognized as media"


def test_parent_target_scan_excludes_nested_target(tmp_path):
    root = tmp_path / "docs"
    child = root / "versant-home"
    child.mkdir(parents=True)
    (root / "parent.pdf").write_text("parent", encoding="utf-8")
    (child / "child.pdf").write_text("child", encoding="utf-8")
    parent_target = {"id": "parent", "path": str(root), "recursive": True, "enabled": True}
    child_target = {"id": "child", "path": str(child), "recursive": True, "enabled": True}

    exclude_roots = indexing_service._target_exclude_roots(parent_target, [parent_target, child_target])
    parent_count, parent_timed_out = indexing_service._target_scan_count(
        str(root),
        recursive=True,
        exclude_roots=exclude_roots,
    )
    child_count, child_timed_out = indexing_service._target_scan_count(str(child), recursive=True)

    assert parent_timed_out is False
    assert child_timed_out is False
    assert parent_count == 1
    assert child_count == 1


def test_indexing_scan_prunes_generated_directories(tmp_path):
    root = tmp_path / "docs"
    (root / "node_modules" / "package").mkdir(parents=True)
    (root / ".cache").mkdir(parents=True)
    (root / "notes").mkdir(parents=True)
    (root / "node_modules" / "package" / "dependency.pdf").write_text("dependency", encoding="utf-8")
    (root / ".cache" / "cached.pdf").write_text("cached", encoding="utf-8")
    (root / "notes" / "real.pdf").write_text("real", encoding="utf-8")

    files = indexing_service._iter_target_files(str(root), recursive=True)
    count, timed_out = indexing_service._target_scan_count(str(root), recursive=True)

    assert timed_out is False
    assert count == 1
    assert [Path(path).name for path in files] == ["real.pdf"]


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


def test_serialize_tags_caps_payload_length():
    tags = [
        "integration:google",
        "service:drive",
        "account:physiphile-gmail-com",
        "mime:application-vnd-google-apps-presentation",
        "drive_owner:very-long-owner-name-that-keeps-going-and-going@example.com",
        "topic:" + ("x" * 220),
        "path:" + ("nested/" * 40),
    ]

    encoded = indexing_service._serialize_tags(tags)

    assert len(encoded) <= indexing_service.TAGS_FIELD_MAX_LENGTH
    assert "integration:google" in encoded
    assert "service:drive" in encoded
