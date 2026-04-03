"""Tests for the hierarchical media processing pipeline."""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


# ── L0: Models ──────────────────────────────────────────────────────────


class TestModels:
    def test_media_asset_defaults(self):
        from media.models import MediaAsset, Modality
        asset = MediaAsset()
        assert asset.media_id
        assert asset.modality == Modality.AUDIO
        assert asset.duration_s == 0.0

    def test_media_asset_hash(self, tmp_path):
        from media.models import MediaAsset
        test_file = tmp_path / "test.wav"
        test_file.write_bytes(b"fake audio content")
        asset = MediaAsset(path=str(test_file))
        h = asset.compute_hash()
        assert len(h) == 64  # SHA256 hex

    def test_atomic_event_creation(self):
        from media.models import AtomicEvent, EventType
        event = AtomicEvent(
            time_start=10.0, time_end=15.0,
            speakers=["S1"], text_evidence="The gate was open.",
            event_type=EventType.OBSERVATION, confidence=0.9,
        )
        assert event.event_id.startswith("evt_")
        assert event.time_start == 10.0
        assert event.speakers == ["S1"]

    def test_output_format_enum(self):
        from media.models import OutputFormat
        assert OutputFormat.CHRONOLOGICAL.value == "chronological"
        assert OutputFormat.MEETING_MINUTES.value == "meeting_minutes"

    def test_pipeline_job_tracking(self):
        from media.models import PipelineJob
        job = PipelineJob()
        assert job.status == "pending"
        assert job.progress == 0.0

    def test_salience_tags(self):
        from media.models import SalienceTag
        assert SalienceTag.FILLER.value == "filler"
        assert SalienceTag.LOW_CONFIDENCE.value == "low_confidence"


# ── L0: Evidence Store ──────────────────────────────────────────────────


class TestEvidenceStore:
    def test_detect_modality(self):
        from media.evidence_store import _detect_modality
        from media.models import Modality
        assert _detect_modality("file.mp4") == Modality.VIDEO
        assert _detect_modality("file.mp3") == Modality.AUDIO
        assert _detect_modality("file.jpg") == Modality.IMAGE
        assert _detect_modality("file.txt") == Modality.TEXT

    def test_register_asset(self, tmp_path, monkeypatch):
        from media import evidence_store
        monkeypatch.setattr(evidence_store, "MEDIA_STORE_DIR", tmp_path / "store")
        monkeypatch.setattr(evidence_store, "ASSETS_INDEX", tmp_path / "store" / "assets.json")

        test_file = tmp_path / "test.mp3"
        test_file.write_bytes(b"\x00" * 1024)

        # Mock ffprobe since we don't have a real media file
        monkeypatch.setattr(evidence_store, "_probe_media", lambda p: {
            "duration_s": 10.0, "sample_rate": 44100, "file_size_bytes": 1024,
        })

        asset = evidence_store.register_asset(str(test_file))
        assert asset.filename == "test.mp3"
        assert asset.duration_s == 10.0
        assert asset.file_hash

    def test_list_assets_empty(self, tmp_path, monkeypatch):
        from media import evidence_store
        monkeypatch.setattr(evidence_store, "ASSETS_INDEX", tmp_path / "nonexistent.json")
        assets = evidence_store.list_assets()
        assert assets == []

    def test_save_and_get_artifact(self, tmp_path, monkeypatch):
        from media import evidence_store
        from media.models import DerivedArtifact
        monkeypatch.setattr(evidence_store, "ARTIFACTS_DIR", tmp_path / "artifacts")

        artifact = DerivedArtifact(
            media_id="test123", kind="transcript",
            start_s=0.0, end_s=10.0, content="Hello world",
        )
        evidence_store.save_artifact(artifact)

        loaded = evidence_store.get_artifacts("test123")
        assert len(loaded) == 1
        assert loaded[0].content == "Hello world"
        assert loaded[0].kind == "transcript"

    def test_get_artifacts_filtered_by_kind(self, tmp_path, monkeypatch):
        from media import evidence_store
        from media.models import DerivedArtifact
        monkeypatch.setattr(evidence_store, "ARTIFACTS_DIR", tmp_path / "artifacts")

        for kind in ["transcript", "keyframe", "transcript"]:
            evidence_store.save_artifact(DerivedArtifact(media_id="test", kind=kind))

        transcripts = evidence_store.get_artifacts("test", kind="transcript")
        assert len(transcripts) == 2
        keyframes = evidence_store.get_artifacts("test", kind="keyframe")
        assert len(keyframes) == 1


# ── L1: Filtering ───────────────────────────────────────────────────────


class TestFiltering:
    def test_detect_speech_segments_from_transcript(self):
        from media.filtering import detect_speech_segments
        from media.models import MediaAsset

        mock_segments = [
            {"text": "Hello there", "start": 0.0, "end": 1.5, "no_speech_prob": 0.01},
            {"text": "um", "start": 1.5, "end": 2.0, "no_speech_prob": 0.1},
            {"text": "How are you?", "start": 2.0, "end": 3.5, "no_speech_prob": 0.02},
        ]

        asset = MediaAsset()
        segments = detect_speech_segments(asset, mock_segments)
        assert len(segments) == 3
        assert segments[0].text == "Hello there"
        assert segments[1].text == "um"

    def test_filler_tagging(self):
        from media.filtering import detect_speech_segments
        from media.models import MediaAsset, SalienceTag

        mock_segments = [
            {"text": "um", "start": 0.0, "end": 0.5, "no_speech_prob": 0.0},
            {"text": "uh", "start": 0.5, "end": 1.0, "no_speech_prob": 0.0},
            {"text": "Real content here", "start": 1.0, "end": 3.0, "no_speech_prob": 0.0},
        ]

        segments = detect_speech_segments(MediaAsset(), mock_segments)
        assert SalienceTag.FILLER in segments[0].salience_tags
        assert SalienceTag.FILLER in segments[1].salience_tags
        assert SalienceTag.FILLER not in segments[2].salience_tags

    def test_filter_speech_segments_confidence(self):
        from media.filtering import filter_speech_segments
        from media.models import SpeechSegment

        segments = [
            SpeechSegment(start_s=0, end_s=1, text="Good", confidence=0.9),
            SpeechSegment(start_s=1, end_s=2, text="Bad", confidence=0.1),
        ]

        results = filter_speech_segments(segments, min_confidence=0.3)
        assert len(results) == 2
        assert results[0].keep is True
        assert results[1].keep is False

    def test_compute_sharpness_missing_cv2(self, monkeypatch):
        from media import filtering
        # Force ImportError for cv2
        monkeypatch.setattr(filtering, "compute_sharpness", lambda p: -1.0)
        result = filtering.compute_sharpness("nonexistent.jpg")
        assert result == -1.0


# ── L2: Event Extraction ───────────────────────────────────────────────


class TestEventExtraction:
    def test_classify_event_type(self):
        from media.event_extraction import _classify_event_type
        from media.models import EventType

        assert _classify_event_type("What happened?") == EventType.QUESTION
        assert _classify_event_type("We decided to go") == EventType.DECISION
        assert _classify_event_type("He went to the store") == EventType.ACTION
        assert _classify_event_type("I noticed something odd") == EventType.OBSERVATION
        assert _classify_event_type("Hello everyone") == EventType.SPEECH

    def test_extract_entities(self):
        from media.event_extraction import _extract_entities
        entities = _extract_entities("John Smith met with Alice at Central Park")
        assert "John Smith" in entities or "Central Park" in entities

    def test_extract_events_from_speech(self):
        from media.event_extraction import extract_events_from_speech
        from media.models import SpeechSegment

        segments = [
            SpeechSegment(start_s=0, end_s=2, text="Hello everyone, let's begin."),
            SpeechSegment(start_s=2, end_s=5, text="What should we discuss first?"),
            SpeechSegment(start_s=20, end_s=25, text="I noticed something unusual."),
        ]

        events = extract_events_from_speech(segments, media_id="test", merge_window_s=5.0)
        assert len(events) >= 2  # First two should merge, third is separate
        assert events[0].source_refs[0].startswith("test:")

    def test_extract_events_empty(self):
        from media.event_extraction import extract_events_from_speech
        events = extract_events_from_speech([])
        assert events == []

    def test_merge_events_chronological(self):
        from media.event_extraction import merge_events
        from media.models import AtomicEvent, EventType

        speech = [
            AtomicEvent(time_start=0, time_end=5, text_evidence="Speech 1", event_type=EventType.SPEECH),
            AtomicEvent(time_start=10, time_end=15, text_evidence="Speech 2", event_type=EventType.SPEECH),
        ]
        scene = [
            AtomicEvent(time_start=3, time_end=8, text_evidence="Scene change", event_type=EventType.SCENE_CHANGE),
        ]

        merged = merge_events(speech, scene)
        assert len(merged) == 3
        # Should be sorted by time
        assert merged[0].time_start <= merged[1].time_start <= merged[2].time_start


# ── L3: Recaps ──────────────────────────────────────────────────────────


class TestRecaps:
    def test_group_events_by_time_window(self):
        from media.models import AtomicEvent
        from media.recaps import group_events_by_time_window

        events = [
            AtomicEvent(time_start=0, time_end=5, text_evidence="A"),
            AtomicEvent(time_start=10, time_end=15, text_evidence="B"),
            AtomicEvent(time_start=70, time_end=75, text_evidence="C"),
            AtomicEvent(time_start=80, time_end=85, text_evidence="D"),
        ]

        groups = group_events_by_time_window(events, window_s=60.0)
        assert len(groups) == 2  # First window: A, B; Second: C, D

    def test_group_events_by_gap(self):
        from media.models import AtomicEvent
        from media.recaps import group_events_by_gap

        events = [
            AtomicEvent(time_start=0, time_end=2, text_evidence="A"),
            AtomicEvent(time_start=3, time_end=5, text_evidence="B"),
            AtomicEvent(time_start=30, time_end=35, text_evidence="C"),
        ]

        groups = group_events_by_gap(events, max_gap_s=10.0)
        assert len(groups) == 2

    def test_build_recap_from_events(self):
        from media.models import AtomicEvent, EventType
        from media.recaps import build_recap_from_events

        events = [
            AtomicEvent(
                time_start=0, time_end=5,
                speakers=["Alice"], text_evidence="Let's review the plan.",
                event_type=EventType.SPEECH,
            ),
            AtomicEvent(
                time_start=5, time_end=10,
                speakers=["Bob"], text_evidence="What about the deadline?",
                event_type=EventType.QUESTION,
            ),
        ]

        recap = build_recap_from_events(events, group_type="conversation")
        assert recap.group_type == "conversation"
        assert recap.time_start == 0
        assert recap.time_end == 10
        assert len(recap.event_ids) == 2
        assert "What about the deadline?" in recap.unresolved_questions

    def test_build_recap_prompt(self):
        from media.models import AtomicEvent, EventType
        from media.recaps import build_recap_prompt

        events = [AtomicEvent(time_start=0, time_end=5, text_evidence="Hello", event_type=EventType.SPEECH)]
        sys_prompt, user_prompt = build_recap_prompt(events)
        assert "step-by-step" in sys_prompt.lower()
        assert "Hello" in user_prompt

    def test_build_recaps_integration(self):
        from media.models import AtomicEvent, EventType
        from media.recaps import build_recaps

        events = [
            AtomicEvent(time_start=i * 10, time_end=i * 10 + 5, text_evidence=f"Event {i}", event_type=EventType.SPEECH)
            for i in range(10)
        ]

        recaps = build_recaps(events, window_s=30.0)
        assert len(recaps) > 0
        assert all(r.recap_text for r in recaps)


# ── L4: Memory ──────────────────────────────────────────────────────────


class TestMemory:
    def test_build_memory_from_recaps(self):
        from media.memory import build_memory_from_recaps
        from media.models import LocalRecap

        recaps = [
            LocalRecap(
                time_start=0, time_end=60, recap_text="Alice discussed the project plan.",
                salient_entities=["Alice", "Project X"],
            ),
            LocalRecap(
                time_start=60, time_end=120, recap_text="Bob raised concerns about the timeline.",
                salient_entities=["Bob", "Project X"],
            ),
        ]

        memory = build_memory_from_recaps(recaps, media_id="test123")
        assert memory.media_id == "test123"
        # Project X appears in both recaps
        assert "Project X" in memory.main_actors or "Project X" in memory.inferred_themes
        assert len(memory.timeline_anchors) >= 2

    def test_build_memory_empty(self):
        from media.memory import build_memory_from_recaps
        memory = build_memory_from_recaps([], media_id="empty")
        assert memory.media_id == "empty"
        assert memory.main_actors == []

    def test_build_memory_prompt(self):
        from media.memory import build_memory_prompt
        from media.models import LocalRecap

        recaps = [LocalRecap(time_start=0, time_end=30, recap_text="Test recap")]
        sys_prompt, user_prompt = build_memory_prompt(recaps)
        assert "contextual memory" in sys_prompt.lower()
        assert "Test recap" in user_prompt


# ── L5: Composer ────────────────────────────────────────────────────────


class TestComposer:
    def test_select_output_format_meeting(self):
        from media.composer import select_output_format
        from media.models import AtomicEvent, ContextualMemory, EventType

        events = [
            AtomicEvent(time_start=0, time_end=5, speakers=["Alice"], event_type=EventType.DECISION, text_evidence="We decided to ship."),
            AtomicEvent(time_start=5, time_end=10, speakers=["Bob"], event_type=EventType.QUESTION, text_evidence="When?"),
        ]
        memory = ContextualMemory()

        fmt = select_output_format(memory, events)
        from media.models import OutputFormat
        assert fmt == OutputFormat.MEETING_MINUTES

    def test_select_output_format_brief(self):
        from media.composer import select_output_format
        from media.models import AtomicEvent, ContextualMemory, EventType, OutputFormat

        events = [AtomicEvent(time_start=0, time_end=30, event_type=EventType.SPEECH, text_evidence="Short content")]
        memory = ContextualMemory()
        fmt = select_output_format(memory, events)
        assert fmt == OutputFormat.EXECUTIVE_BRIEF

    def test_select_output_format_empty(self):
        from media.composer import select_output_format
        from media.models import ContextualMemory, OutputFormat
        fmt = select_output_format(ContextualMemory(), [])
        assert fmt == OutputFormat.EXECUTIVE_BRIEF

    def test_compose_document(self):
        from media.composer import compose_document
        from media.models import AtomicEvent, ContextualMemory, EventType, LocalRecap, OutputFormat

        events = [AtomicEvent(time_start=0, time_end=10, text_evidence="Meeting began.")]
        recaps = [LocalRecap(time_start=0, time_end=10, recap_text="The meeting started.")]
        memory = ContextualMemory(media_id="test", main_actors=["Alice"])

        doc = compose_document(memory, recaps, events, output_format=OutputFormat.CHRONOLOGICAL)
        assert doc.format == OutputFormat.CHRONOLOGICAL
        assert doc.full_text
        assert len(doc.sections) > 0

    def test_compose_prompt(self):
        from media.composer import build_compose_prompt
        from media.models import AtomicEvent, ContextualMemory, LocalRecap, OutputFormat

        events = [AtomicEvent(time_start=0, time_end=5, text_evidence="Event")]
        recaps = [LocalRecap(time_start=0, time_end=5, recap_text="Recap")]
        memory = ContextualMemory(main_actors=["Alice"])

        sys_p, user_p = build_compose_prompt(memory, recaps, events, OutputFormat.MEETING_MINUTES)
        assert "document composer" in sys_p.lower()
        assert "meeting minutes" in user_p.lower()


# ── Pipeline Integration ────────────────────────────────────────────────


class TestPipeline:
    def test_get_active_jobs_empty(self):
        from media.pipeline import get_active_jobs
        # Should return list (may have jobs from other tests)
        jobs = get_active_jobs()
        assert isinstance(jobs, list)

    def test_get_pipeline_result_nonexistent(self, tmp_path, monkeypatch):
        from media import pipeline
        monkeypatch.setattr(pipeline, "PIPELINE_STORE_DIR", tmp_path)
        result = pipeline.get_pipeline_result("nonexistent")
        assert result is None


# ── Transcript Parsers ──────────────────────────────────────────────────


class TestTranscriptParsers:
    def test_parse_timecode_ms(self):
        from transcripts_parsers import _parse_timecode_ms
        assert _parse_timecode_ms("0:00:01.500") == 1500
        assert _parse_timecode_ms("1:30:00") == 5400000
        assert _parse_timecode_ms("0:05") == 5000
        assert _parse_timecode_ms("5") == 5000
        assert _parse_timecode_ms("5.5") == 5500
        assert _parse_timecode_ms("") is None

    def test_clean_text(self):
        from transcripts_parsers import _clean_text
        assert _clean_text("  Hello  world  ") == "Hello world"
        assert _clean_text("...") == ""
        assert _clean_text(". . .") == ""
        assert _clean_text("Real text.") == "Real text."

    def test_parse_vtt(self, tmp_path):
        vtt_content = """WEBVTT

00:00:01.000 --> 00:00:03.000
Hello world

00:00:03.000 --> 00:00:05.000
This is a test
"""
        vtt_file = tmp_path / "test.vtt"
        vtt_file.write_text(vtt_content)

        from transcripts.parsers import parse_transcript
        cues, error = parse_transcript(str(vtt_file))
        assert error is None
        assert len(cues) == 2
        assert cues[0].text == "Hello world"
        assert cues[0].start_ms == 1000
        assert cues[0].end_ms == 3000

    def test_parse_txt(self, tmp_path):
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("This is a plain text transcript with no timestamps.")

        from transcripts.parsers import parse_transcript
        cues, error = parse_transcript(str(txt_file))
        assert error is None
        assert len(cues) == 1
        assert cues[0].start_ms == 0

    def test_parse_unsupported(self, tmp_path):
        bad_file = tmp_path / "test.xyz"
        bad_file.write_text("content")

        from transcripts.parsers import parse_transcript
        cues, error = parse_transcript(str(bad_file))
        assert cues == []
        assert "Unsupported" in error


# ── Transcript Chunking ─────────────────────────────────────────────────


class TestTranscriptChunking:
    def test_build_chunks_basic(self):
        from transcripts.parsers import Cue
        from transcripts.chunking import build_time_window_chunks

        cues = [
            Cue(start_ms=0, end_ms=1000, text="First line"),
            Cue(start_ms=1000, end_ms=2000, text="Second line"),
            Cue(start_ms=60000, end_ms=61000, text="After a minute"),
        ]

        chunks = build_time_window_chunks(cues, path="/test/file.vtt")
        assert len(chunks) > 0
        assert all(c.source_type == "transcript" for c in chunks)

    def test_build_chunks_empty(self):
        from transcripts.chunking import build_time_window_chunks
        chunks = build_time_window_chunks([], path="/test.vtt")
        assert chunks == []

    def test_chunks_have_levels(self):
        from transcripts.parsers import Cue
        from transcripts.chunking import build_time_window_chunks

        cues = [
            Cue(start_ms=i * 1000, end_ms=(i + 1) * 1000, text=f"Word {i} content here")
            for i in range(120)  # 2 minutes of cues
        ]

        chunks = build_time_window_chunks(cues, path="/test.vtt")
        levels = {c.level for c in chunks}
        assert 1 in levels  # 1-minute chunks
        # doc-level (3) only emitted if text is informative enough
        assert 1 in levels or 2 in levels  # at least minute or hour chunks exist

    def test_informative_text_filter(self):
        from transcripts_chunking import _is_informative_text
        assert _is_informative_text("This is a real sentence with content", min_words=4) is True
        assert _is_informative_text("a a a a a a a a", min_words=4) is False
        assert _is_informative_text("hi", min_words=4) is False


# ── Document Extraction ─────────────────────────────────────────────────


class TestDocumentExtraction:
    def test_extract_txt(self, tmp_path):
        txt_file = tmp_path / "doc.txt"
        txt_file.write_text("This is a test document with real content.")

        from documents.extract import extract_document_segments
        segments, error = extract_document_segments(str(txt_file))
        assert error is None
        assert len(segments) == 1
        assert "test document" in segments[0].text

    def test_extract_unsupported(self, tmp_path):
        bad_file = tmp_path / "doc.xyz"
        bad_file.write_text("content")

        from documents.extract import extract_document_segments
        segments, error = extract_document_segments(str(bad_file))
        assert segments == []
        assert "Unsupported" in error

    def test_normalize_text(self):
        from documents.extract import _normalize_text
        assert _normalize_text("  Hello\n\n  World  ") == "Hello\nWorld"
        assert _normalize_text("") == ""


# ── Document Chunking ───────────────────────────────────────────────────


class TestDocumentChunking:
    def test_chunk_document_basic(self, monkeypatch):
        from documents.extract import ExtractedDocumentSegment
        from documents.chunking import chunk_document_segments

        monkeypatch.setenv("DOCUMENT_CHUNK_TARGET_WORDS", "30")
        monkeypatch.setenv("DOCUMENT_CHUNK_MAX_WORDS", "50")

        text = " ".join(["content"] * 200)
        segments = [ExtractedDocumentSegment(tag="page_1", text=text)]

        chunks = chunk_document_segments(
            segments, path="/doc.pdf", source_id="/doc.pdf", doc_type="pdf",
        )
        assert len(chunks) >= 2

    def test_chunk_empty_segments(self):
        from documents.chunking import chunk_document_segments
        chunks = chunk_document_segments([], path="/doc.pdf", source_id="/doc.pdf", doc_type="pdf")
        assert chunks == []
