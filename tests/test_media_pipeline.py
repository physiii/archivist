"""Tests for the hierarchical media processing pipeline."""

import json
import subprocess
import sys
import threading
import types
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

    def test_register_asset_reuses_media_id_for_same_path(self, tmp_path, monkeypatch):
        from media import evidence_store
        monkeypatch.setattr(evidence_store, "MEDIA_STORE_DIR", tmp_path / "store")
        monkeypatch.setattr(evidence_store, "ASSETS_INDEX", tmp_path / "store" / "assets.json")

        test_file = tmp_path / "test.mp3"
        test_file.write_bytes(b"\x00" * 1024)
        monkeypatch.setattr(evidence_store, "_probe_media", lambda p: {"duration_s": 10.0, "file_size_bytes": 1024})

        first = evidence_store.register_asset(str(test_file))
        second = evidence_store.register_asset(str(test_file))
        assert first.media_id == second.media_id
        assert len(evidence_store.list_assets()) == 1

    def test_get_artifacts_from_pipeline_result(self, tmp_path, monkeypatch):
        from media import evidence_store
        monkeypatch.setattr(evidence_store, "PIPELINE_RESULTS_DIR", tmp_path / "pipeline")
        monkeypatch.setattr(evidence_store, "ARTIFACTS_DIR", tmp_path / "artifacts")
        evidence_store.PIPELINE_RESULTS_DIR.mkdir(parents=True)

        (evidence_store.PIPELINE_RESULTS_DIR / "abc123.json").write_text(
            '{"artifacts":[{"artifact_id":"a1","media_id":"abc123","kind":"transcript","start_s":0,"end_s":1,"content":"hello","confidence":1.0,"metadata":{},"source_refs":[]}]}',
            encoding="utf-8",
        )

        artifacts = evidence_store.get_artifacts("abc123")
        assert len(artifacts) == 1
        assert artifacts[0].kind == "transcript"
        assert artifacts[0].content == "hello"

    def test_get_artifacts_scope_trace_prefers_raw_bundle(self, tmp_path, monkeypatch):
        from media import evidence_store

        monkeypatch.setattr(evidence_store, "PIPELINE_RESULTS_DIR", tmp_path / "pipeline")
        monkeypatch.setattr(evidence_store, "ARTIFACTS_DIR", tmp_path / "artifacts")
        evidence_store.PIPELINE_RESULTS_DIR.mkdir(parents=True)
        evidence_store.ARTIFACTS_DIR.mkdir(parents=True)

        (evidence_store.PIPELINE_RESULTS_DIR / "abc123.json").write_text(
            '{"artifacts":[{"artifact_id":"pub1","media_id":"abc123","kind":"transcript","start_s":0,"end_s":1,"content":"hello","confidence":1.0,"metadata":{},"source_refs":[]}]}',
            encoding="utf-8",
        )
        (evidence_store.ARTIFACTS_DIR / "abc123.json").write_text(
            '{"media_id":"abc123","artifacts":[{"artifact_id":"raw1","media_id":"abc123","kind":"speech_segment","start_s":0,"end_s":1,"content":"hello there","confidence":1.0,"metadata":{},"source_refs":[]}]}',
            encoding="utf-8",
        )

        public_artifacts = evidence_store.get_artifacts("abc123")
        trace_artifacts = evidence_store.get_artifacts("abc123", scope="trace")

        assert [artifact.kind for artifact in public_artifacts] == ["transcript"]
        assert [artifact.kind for artifact in trace_artifacts] == ["speech_segment"]

    def test_save_artifact_bundle_persists_archivist_pipeline_root_metadata(self, tmp_path, monkeypatch):
        from media import evidence_store
        from media.models import DerivedArtifact

        monkeypatch.setattr(evidence_store, "ARTIFACTS_DIR", tmp_path / "artifacts")
        stamp = {
            "pipeline_version": "5679262e3c86",
            "pipeline_compat_version": "2026-04-11.1",
            "repo_commit": "e96b26af4e9a3dc240b202fd35025679262e3c86",
            "repo_commit_suffix": "5679262e3c86",
        }
        artifacts = [
            DerivedArtifact(
                media_id="abc123",
                kind="transcript",
                content="hello there",
            ),
        ]

        evidence_store.save_artifact_bundle(
            "abc123",
            artifacts,
            bundle_metadata={"archivist_pipeline": stamp},
        )

        payload = json.loads((tmp_path / "artifacts" / "abc123.json").read_text(encoding="utf-8"))
        assert payload["archivist_pipeline"] == stamp
        assert payload["bundle_metadata"]["archivist_pipeline"] == stamp

    def test_load_assets_index_deduplicates_by_path_and_prefers_pipeline_result(self, tmp_path, monkeypatch):
        from media import evidence_store

        store_dir = tmp_path / "store"
        monkeypatch.setattr(evidence_store, "MEDIA_STORE_DIR", store_dir)
        monkeypatch.setattr(evidence_store, "ASSETS_INDEX", store_dir / "assets.json")
        monkeypatch.setattr(evidence_store, "PIPELINE_RESULTS_DIR", tmp_path / "pipeline")
        monkeypatch.setattr(evidence_store, "ARTIFACTS_DIR", tmp_path / "artifacts")
        evidence_store.PIPELINE_RESULTS_DIR.mkdir(parents=True)
        store_dir.mkdir(parents=True)

        clip_path = tmp_path / "clip.mkv"
        clip_path.write_bytes(b"clip")
        path = str(clip_path.resolve())
        payload = {
            "newer_with_pipeline": {
                "media_id": "newer_with_pipeline",
                "path": path,
                "filename": "clip.mkv",
                "modality": "video",
                "file_hash": "hash123",
                "indexed_at": 20,
            },
            "older_duplicate": {
                "media_id": "older_duplicate",
                "path": path,
                "filename": "clip.mkv",
                "modality": "video",
                "file_hash": "hash123",
                "indexed_at": 10,
            },
        }
        evidence_store.ASSETS_INDEX.write_text(json.dumps(payload), encoding="utf-8")
        (evidence_store.PIPELINE_RESULTS_DIR / "newer_with_pipeline.json").write_text("{}", encoding="utf-8")

        index = evidence_store._load_assets_index()
        assert list(index) == ["newer_with_pipeline"]


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

    def test_classify_event_type_treats_mic_check_as_speech(self):
        from media.event_extraction import _classify_event_type
        from media.models import EventType

        text = "check one two hey hello good morning can you hear me right i didn't come in muted"
        assert _classify_event_type(text) == EventType.SPEECH

    def test_classify_event_type_keeps_setup_walkthrough_as_speech(self):
        from media.event_extraction import _classify_event_type
        from media.models import EventType

        text = (
            "I'm going to show you what this looks like because it actually has the SSH feature. "
            "What's going on here? This looks different when I click on it."
        )
        assert _classify_event_type(text) not in {EventType.DECISION, EventType.ACTION}

    def test_extract_entities(self):
        from media.event_extraction import _extract_entities
        entities = _extract_entities("John Smith met with Alice at Central Park")
        assert "John Smith" in entities or "Central Park" in entities

    def test_extract_events_from_speech(self):
        from media.event_extraction import extract_events_from_speech
        from media.models import SpeechSegment

        segments = [
            SpeechSegment(
                start_s=0,
                end_s=2,
                text="Hello everyone, let's begin.",
                speaker="Alice",
                word_timestamps=[{"start": 0.0, "end": 0.3, "word": "Hello", "confidence": 0.9}],
            ),
            SpeechSegment(start_s=2, end_s=5, text="What should we discuss first?"),
            SpeechSegment(start_s=20, end_s=25, text="I noticed something unusual."),
        ]

        events = extract_events_from_speech(segments, media_id="test", merge_window_s=5.0)
        assert len(events) >= 2  # First two should merge, third is separate
        assert events[0].source_refs[0].startswith("test:")
        assert events[0].metadata["transcript_span"]["start_s"] == 0
        assert events[0].metadata["speaker_turns"][0]["speaker"] == "Alice"
        assert events[0].metadata["word_timestamps"][0]["word"] == "Hello"
        assert events[0].metadata["evidence_refs"][0]["kind"] == "speech_segment"

    def test_extract_events_empty(self):
        from media.event_extraction import extract_events_from_speech
        events = extract_events_from_speech([])
        assert events == []

    def test_extract_events_from_speech_caps_group_size(self):
        from media.event_extraction import extract_events_from_speech
        from media.models import SpeechSegment

        segments = [
            SpeechSegment(
                start_s=float(i * 4),
                end_s=float(i * 4 + 3),
                text=f"Segment {i} with enough words to count as meaningful content.",
            )
            for i in range(30)
        ]

        events = extract_events_from_speech(segments, media_id="test", merge_window_s=5.0)
        assert len(events) >= 2
        assert max((evt.time_end - evt.time_start) for evt in events) <= 95

    def test_extract_entities_filters_common_sentence_starters(self):
        from media.event_extraction import _extract_entities

        entities = _extract_entities(
            "Because Andy met Brianna, Yeah, Evan joined later and James asked a question."
        )
        assert "Andy" in entities
        assert "Brianna" in entities
        assert "Evan" in entities
        assert "James" in entities
        assert "Because" not in entities
        assert "Yeah" not in entities

    def test_extract_entities_keeps_acronyms_and_filters_noise(self):
        from media.event_extraction import _extract_entities

        entities = _extract_entities(
            "Who was that? Casey said the VOA and VOI routing should hit EPA after deployment."
        )
        assert "VOA" in entities
        assert "VOI" in entities
        assert "EPA" in entities
        assert "Casey" in entities
        assert "Who" not in entities

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
        assert "cross_modal_refs" in merged[0].metadata or "cross_modal_refs" in merged[1].metadata


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
        assert recap.window_summary
        assert len(recap.event_ids) == 2
        assert recap.summary_refs
        assert recap.ledger_entries[0]["event_id"] == events[0].event_id
        assert "What about the deadline?" in recap.unresolved_questions

    def test_build_recap_filters_noise_and_answered_questions(self):
        from media.models import AtomicEvent, EventType
        from media.recaps import build_recap_from_events

        events = [
            AtomicEvent(
                time_start=0,
                time_end=3,
                text_evidence="What's up? What's up?",
                event_type=EventType.QUESTION,
                metadata={"question_text": "What's up? What's up?"},
            ),
            AtomicEvent(
                time_start=3,
                time_end=10,
                text_evidence="Any updates from your side? Yeah, I pushed a PR for the manual review routing.",
                event_type=EventType.QUESTION,
                metadata={"question_text": "Any updates from your side?"},
            ),
            AtomicEvent(
                time_start=10,
                time_end=18,
                text_evidence="What should happen to reports that missed manual review?",
                event_type=EventType.QUESTION,
                metadata={"question_text": "What should happen to reports that missed manual review?"},
            ),
        ]

        recap = build_recap_from_events(events, group_type="conversation")
        assert "What's up? What's up?" not in recap.unresolved_questions
        assert "Any updates from your side?" not in recap.unresolved_questions
        assert "What should happen to reports that missed manual review?" in recap.unresolved_questions
        assert "What's up? What's up?" not in recap.recap_text
        assert "pushed a PR for the manual review routing" in recap.recap_text

    def test_extract_topic_phrases_filters_noise_bigrams(self):
        from media.text_cleanup import extract_topic_phrases

        phrases = extract_topic_phrases(
            [
                "Discussion focused on You Know and Alpha Evolve.",
                "Alpha Evolve should help the VOA rollout.",
                "You know, the VOA rollout needs validation.",
            ],
            limit=4,
        )

        assert "Alpha Evolve" in phrases
        assert "VOA" in phrases
        assert "You Know" not in phrases

    def test_extract_topic_phrases_prefers_domain_terms_over_conversational_glue(self):
        from media.text_cleanup import extract_topic_phrases

        phrases = extract_topic_phrases(
            [
                "The segment covers talk about and follow-up work.",
                "I've been thinking about AI, FPGA, chip design, and silicon.",
                "We talked about semiconductor design and the chip model.",
                "The chip design and FPGA work connect to AI models.",
            ],
            limit=6,
        )

        assert any(term in phrases for term in ["AI", "FPGA", "Chip", "Semiconductor", "Silicon"])
        assert "And" not in phrases
        assert "Talk About" not in phrases
        assert "And Follow" not in phrases
        assert "Thinking About" not in phrases

    def test_extract_inline_topic_terms_filters_contractions_and_greetings(self):
        from media.text_cleanup import extract_inline_topic_terms

        terms = extract_inline_topic_terms(
            "Good morning. I've been thinking about FPGA, chip design, RTL, and semiconductor work.",
            limit=6,
        )

        assert any(term in terms for term in ["FPGA", "Chip Design", "RTL", "Semiconductor"])
        assert "Morning" not in terms
        assert "I'Ve" not in terms

    def test_build_recap_summary_avoids_greeting_fragments(self):
        from media.models import AtomicEvent, EventType
        from media.recaps import build_recap_from_events

        events = [
            AtomicEvent(
                time_start=0,
                time_end=30,
                text_evidence="Good morning and thanks for joining. We should review the FPGA prototype and chip design.",
                event_type=EventType.DECISION,
                metadata={"brief": "We should review the FPGA prototype and chip design."},
            )
        ]

        recap = build_recap_from_events(events, group_type="conversation")
        assert "Morning" not in recap.window_summary
        assert "follow-up work" not in recap.window_summary
        assert any(term in recap.window_summary for term in ["FPGA", "Prototype", "Chip"])

    def test_build_recap_prompt(self):
        from media.models import AtomicEvent, EventType
        from media.recaps import build_recap_prompt

        events = [AtomicEvent(time_start=0, time_end=5, text_evidence="Hello", event_type=EventType.SPEECH)]
        sys_prompt, user_prompt = build_recap_prompt(events)
        assert "step-by-step" in sys_prompt.lower()
        assert "event ledger" in user_prompt.lower()
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
        assert memory.context_overview
        # Project X appears in both recaps
        assert "Project X" in memory.main_actors or "Project X" in memory.inferred_themes
        assert len(memory.timeline_anchors) >= 2
        assert "final_takeaways" in memory.evidence_map

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
        assert "compressed context layer" in user_prompt.lower()
        assert "interpretive notes" in user_prompt.lower()
        assert "evidence anchors" in user_prompt.lower()
        assert "Test recap" in user_prompt

    def test_build_memory_filters_noisy_entities(self):
        from media.memory import build_memory_from_recaps
        from media.models import LocalRecap

        recaps = [
            LocalRecap(
                time_start=0,
                time_end=60,
                recap_text="Recap one",
                salient_entities=["Andy", "They", "Brianna", "Yep"],
            ),
            LocalRecap(
                time_start=60,
                time_end=120,
                recap_text="Recap two",
                salient_entities=["Andy", "Brianna", "Whereas", "Yep"],
            ),
        ]

        memory = build_memory_from_recaps(recaps, media_id="test123")
        assert "Andy" in memory.main_actors
        assert "Brianna" in memory.main_actors
        assert "They" not in memory.main_actors
        assert "Yep" not in memory.main_actors
        assert "Whereas" not in memory.inferred_themes

    def test_build_memory_does_not_treat_technical_nouns_as_people(self):
        from media.memory import build_memory_from_recaps
        from media.models import LocalRecap

        recaps = [
            LocalRecap(
                time_start=0,
                time_end=60,
                recap_text="Recap one",
                salient_entities=["Drive", "Studio", "Andy"],
            ),
            LocalRecap(
                time_start=60,
                time_end=120,
                recap_text="Recap two",
                salient_entities=["Drive", "Studio", "Andy"],
            ),
        ]

        memory = build_memory_from_recaps(recaps, media_id="test123")
        assert "Andy" in memory.main_actors
        assert "Drive" not in memory.main_actors
        assert "Studio" not in memory.main_actors

    def test_build_memory_uses_event_vocatives_and_dedupes_questions(self):
        from media.memory import build_memory_from_recaps
        from media.models import AtomicEvent, EventType, LocalRecap

        recaps = [
            LocalRecap(
                time_start=0,
                time_end=60,
                recap_text="Summary: Discussion focused on VOA, VOI, and manual review.",
                salient_entities=["Rocky", "VOA", "VOI"],
                unresolved_questions=[
                    "What should happen to reports that missed manual review?",
                    "What should happen to reports that missed manual review?",
                ],
            )
        ]
        events = [
            AtomicEvent(
                time_start=0,
                time_end=10,
                text_evidence="Hey, Rocky, can you review the VOA change?",
                metadata={"entities": ["Rocky", "VOA"]},
            ),
            AtomicEvent(
                time_start=10,
                time_end=20,
                text_evidence="Well, Grayson, let's verify the VOI rollout.",
                metadata={"entities": ["Grayson", "VOI"]},
            ),
        ]

        memory = build_memory_from_recaps(recaps, media_id="test123", events=events)
        assert "Rocky" in memory.main_actors
        assert "Grayson" in memory.main_actors
        assert "Hey" not in memory.main_actors
        assert "Well" not in memory.main_actors
        assert memory.open_loops == ["What should happen to reports that missed manual review?"]
        assert any(theme in memory.inferred_themes for theme in ["VOA", "VOI"])
        assert any(item.get("source_refs") for item in memory.evidence_map["final_takeaways"])
        assert any(item.get("source_refs") for item in memory.evidence_map["open_loops"])

    def test_build_memory_vocatives_ignore_product_names(self):
        from media.memory import build_memory_from_recaps
        from media.models import AtomicEvent, LocalRecap

        recaps = [LocalRecap(time_start=0, time_end=60, recap_text="Recap")]
        events = [
            AtomicEvent(
                time_start=0,
                time_end=10,
                text_evidence="Hey, Rocky, can you review the rollout?",
                metadata={"entities": ["Rocky"]},
            ),
            AtomicEvent(
                time_start=10,
                time_end=20,
                text_evidence="I call it Sonic, right? It has two GPUs in it.",
                metadata={"entities": ["Sonic"]},
            ),
        ]

        memory = build_memory_from_recaps(recaps, media_id="test123", events=events)
        assert "Rocky" in memory.main_actors
        assert "Sonic" not in memory.main_actors

    def test_build_memory_ignores_generic_summary_boilerplate(self):
        from media.memory import build_memory_from_recaps
        from media.models import AtomicEvent, EventType, LocalRecap

        recaps = [
            LocalRecap(
                time_start=0,
                time_end=60,
                recap_text="Window summary: Discussion focused on the current workstream.\n\nEvent ledger:\n- [5.0s] [decision] Review AI and ID scope.",
                window_summary="Discussion focused on the current workstream.",
                salient_entities=["AI", "ID", "Sean"],
            )
        ]
        events = [
            AtomicEvent(
                time_start=5,
                time_end=20,
                text_evidence="Sean reviewed AI and ID scope and raised open questions.",
                event_type=EventType.DECISION,
                metadata={"entities": ["Sean", "AI", "ID"], "brief": "Review AI and ID scope."},
            )
        ]

        memory = build_memory_from_recaps(recaps, media_id="test123", events=events)
        assert "Current Workstream" not in memory.inferred_themes
        assert any(theme in memory.inferred_themes for theme in ["AI", "ID"])

    def test_build_memory_prefers_event_topic_terms_over_weak_window_summary(self):
        from media.memory import build_memory_from_recaps
        from media.models import AtomicEvent, EventType, LocalRecap

        recaps = [
            LocalRecap(
                time_start=0,
                time_end=60,
                recap_text="Window summary: The segment covers This and follow-up work.",
                window_summary="The segment covers This and follow-up work.",
                salient_entities=[],
            )
        ]
        events = [
            AtomicEvent(
                time_start=0,
                time_end=30,
                text_evidence="We should review the FPGA prototype and chip design.",
                event_type=EventType.DECISION,
                metadata={"brief": "Review the FPGA prototype and chip design.", "topic_terms": ["FPGA", "Prototype", "Chip Design"]},
            )
        ]

        memory = build_memory_from_recaps(recaps, media_id="test123", events=events)
        assert "This" not in memory.inferred_themes
        assert any(theme in memory.inferred_themes for theme in ["FPGA", "Prototype", "Chip Design"])


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

    def test_select_output_format_meeting_from_memory_participants(self):
        from media.composer import select_output_format
        from media.models import AtomicEvent, ContextualMemory, EventType, OutputFormat

        events = [
            AtomicEvent(time_start=0, time_end=5, event_type=EventType.DECISION, text_evidence="We decided to ship."),
            AtomicEvent(time_start=5, time_end=10, event_type=EventType.QUESTION, text_evidence="When should we launch?"),
        ]
        memory = ContextualMemory(main_actors=["Andy", "Brianna", "Dan"])

        fmt = select_output_format(memory, events)
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
        assert any(section.get("kind") == "context" for section in doc.sections)
        assert any(section.get("kind") == "walkthrough" for section in doc.sections)

    def test_compose_prompt(self):
        from media.composer import build_compose_prompt
        from media.models import AtomicEvent, ContextualMemory, LocalRecap, OutputFormat

        events = [AtomicEvent(time_start=0, time_end=5, text_evidence="Event")]
        recaps = [LocalRecap(time_start=0, time_end=5, recap_text="Recap")]
        memory = ContextualMemory(main_actors=["Alice"])

        sys_p, user_p = build_compose_prompt(memory, recaps, events, OutputFormat.MEETING_MINUTES)
        assert "document composer" in sys_p.lower()
        assert "meeting minutes" in user_p.lower()
        assert "context overview" in user_p.lower()
        assert "walkthrough" in user_p.lower()
        assert "chronology is the canonical truth" in user_p.lower()
        assert "prefer evidence anchors" in user_p.lower()

    def test_recap_summary_line_falls_back_from_weak_summary(self):
        from media.composer import _recap_summary_line
        from media.models import LocalRecap

        recap = LocalRecap(
            time_start=0,
            time_end=30,
            recap_text="Window summary: The segment covers Morning and follow-up work.",
            summary_refs=[{"summary": "Review AI and FPGA architecture."}],
            ledger_entries=[{"summary": "Review AI and FPGA architecture."}],
        )

        summary = _recap_summary_line(recap)
        assert "Morning" not in summary
        assert any(term in summary for term in ["AI", "FPGA", "architecture"])

    def test_compose_meeting_minutes_uses_structured_sections(self):
        from media.composer import compose_document
        from media.models import AtomicEvent, ContextualMemory, EventType, LocalRecap, OutputFormat

        events = [
            AtomicEvent(
                time_start=5,
                time_end=15,
                text_evidence="We should deploy the routing fix after the release note.",
                event_type=EventType.DECISION,
                metadata={"brief": "Deploy the routing fix after the release note."},
            ),
            AtomicEvent(
                time_start=15,
                time_end=30,
                text_evidence="I'll check the logs after this meeting.",
                event_type=EventType.ACTION,
                metadata={"brief": "Check the logs after the meeting."},
            ),
        ]
        recaps = [
            LocalRecap(
                time_start=0,
                time_end=30,
                recap_text=(
                    "Window summary: Discussion focused on VOA and VOI rollout.\n\n"
                    "Event ledger:\n"
                    "- [5.0s] [decision] Deploy the routing fix after the release note.\n"
                    "- [15.0s] [action] Check the logs after the meeting.\n"
                ),
            )
        ]
        memory = ContextualMemory(
            media_id="test",
            main_actors=["Rocky", "Grayson"],
            open_loops=["What should happen to reports that missed manual review?"],
            inferred_themes=["VOA", "VOI"],
        )

        doc = compose_document(memory, recaps, events, output_format=OutputFormat.MEETING_MINUTES)
        assert "## Context Overview" in doc.full_text
        assert "## Key Topics" in doc.full_text
        assert "## Decisions and Follow-Ups" in doc.full_text
        assert "## Walkthrough" in doc.full_text
        assert any(section.get("kind") == "walkthrough" for section in doc.sections)
        walkthrough = next(section for section in doc.sections if section.get("kind") == "walkthrough")
        assert "### [0.0s - 30.0s]" in walkthrough["content"]
        for section in doc.sections:
            if section.get("kind") == "context":
                assert "### [0.0s - 30.0s]" not in section.get("content", "")

    def test_build_layer_artifacts_persists_recap_and_memory_provenance(self):
        from media.pipeline import _build_layer_artifacts
        from media.models import ComposedDocument, ContextualMemory, LocalRecap, MediaAsset, PipelineJob, OutputFormat

        asset = MediaAsset(media_id="media123", filename="clip.mkv", duration_s=30.0)
        recap = LocalRecap(
            recap_id="recap_1",
            group_type="segment",
            time_start=0.0,
            time_end=30.0,
            recap_text="Window summary: Discussion focused on launch readiness.\n\nEvent ledger:\n- [5.0s] [decision] Ship on Friday.",
            window_summary="Discussion focused on launch readiness.",
            summary_refs=[{"event_id": "evt_1", "time_start": 5.0, "time_end": 8.0, "source_refs": ["speech_5.00"]}],
            ledger_entries=[{"event_id": "evt_1", "summary": "Ship on Friday.", "source_refs": ["speech_5.00"]}],
            source_refs=["speech_5.00"],
        )
        memory = ContextualMemory(
            media_id="media123",
            context_overview="This media is primarily about launch readiness.",
            main_actors=["Alice"],
            final_takeaways=["Discussion focused on launch readiness."],
            evidence_map={"final_takeaways": [{"text": "Discussion focused on launch readiness.", "source_refs": ["speech_5.00"]}]},
        )
        document = ComposedDocument(media_id="media123", format=OutputFormat.CHRONOLOGICAL, title="Chronological - media123")

        artifacts = _build_layer_artifacts(
            asset=asset,
            transcript_payload=None,
            filter_results={},
            events=[],
            recaps=[recap],
            memory=memory,
            document=document,
            job=PipelineJob(media_id="media123"),
        )

        recap_artifact = next(artifact for artifact in artifacts if artifact.kind == "recap")
        memory_artifact = next(artifact for artifact in artifacts if artifact.kind == "memory")
        memory_payload = json.loads(memory_artifact.content)

        assert recap_artifact.metadata["window_summary"] == "Discussion focused on launch readiness."
        assert recap_artifact.metadata["summary_refs"][0]["event_id"] == "evt_1"
        assert recap_artifact.metadata["ledger_entries"][0]["source_refs"] == ["speech_5.00"]
        assert memory_payload["context_overview"] == "This media is primarily about launch readiness."
        assert memory_payload["evidence_map"]["final_takeaways"][0]["source_refs"] == ["speech_5.00"]


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

    def test_get_pipeline_result_hydrates_vtt_from_sidecar(self, tmp_path, monkeypatch):
        from media import pipeline

        monkeypatch.setattr(pipeline, "PIPELINE_STORE_DIR", tmp_path)
        sidecar_path = tmp_path / "clip.vtt"
        sidecar_path.write_text("WEBVTT\n\n00:00.000 --> 00:01.000\nHello world\n", encoding="utf-8")
        (tmp_path / "clip123.json").write_text(
            json.dumps(
                {
                    "media_id": "clip123",
                    "transcript": {"text": "Hello world"},
                    "injection": {"transcript_sidecar_path": str(sidecar_path)},
                }
            ),
            encoding="utf-8",
        )

        result = pipeline.get_pipeline_result("clip123")

        assert result is not None
        assert result["transcript"]["vtt_text"].startswith("WEBVTT")
        assert "Hello world" in result["transcript"]["vtt_text"]

    def test_get_pipeline_result_rebuilds_clean_readable_transcript_from_sidecar(self, tmp_path, monkeypatch):
        from media import pipeline

        monkeypatch.setattr(pipeline, "PIPELINE_STORE_DIR", tmp_path)
        media_path = tmp_path / "clip.mkv"
        media_path.write_bytes(b"video")
        sidecar_path = media_path.with_suffix(".vtt")
        sidecar_path.write_text(
            "WEBVTT\n\nNOTE\nSource: clip.mkv\nLanguage: en\n\n"
            "00:00:00.000 --> 00:00:01.000\nYou\n\n"
            "00:00:01.000 --> 00:00:02.000\nThanks for watching!\n\n"
            "00:00:02.000 --> 00:00:04.000\nActual discussion.\n",
            encoding="utf-8",
        )
        (tmp_path / "clip123.json").write_text(
            json.dumps(
                {
                    "media_id": "clip123",
                    "asset": {"path": str(media_path)},
                    "transcript": {"text": "You Thanks for watching! Actual discussion."},
                    "injection": {"transcript_sidecar_path": str(sidecar_path)},
                }
            ),
            encoding="utf-8",
        )

        result = pipeline.get_pipeline_result("clip123")

        assert result is not None
        assert result["transcript"]["text"] == "Actual discussion."
        assert result["transcript"]["meta"]["removed_segment_count"] == 2
        assert "Thanks for watching!" in result["transcript"]["vtt_text"]

    def test_insert_vectorstore_chunks_releases_loaded_collection(self, monkeypatch):
        import indexing_service
        from media import pipeline
        from media.models import MediaAsset

        calls: list[str] = []

        class FakeCollection:
            def load(self):
                calls.append("load")

            def delete(self, _expr):
                calls.append("delete")

            def flush(self):
                calls.append("flush")

            def release(self):
                calls.append("release")

        fake_collection = FakeCollection()
        monkeypatch.setattr(
            indexing_service,
            "_ensure_chunk_collection",
            lambda *args, **kwargs: fake_collection,
        )
        monkeypatch.setattr(
            indexing_service,
            "_insert_chunks",
            lambda collection, chunks, filehash, embedding_host, embedding_port: len(chunks),
        )

        asset = MediaAsset(media_id="media123", path="/tmp/clip.mkv", filename="clip.mkv", file_hash="hash123")

        stats = pipeline._insert_vectorstore_chunks(asset, [object()])

        assert stats["chunks_inserted"] == 1
        assert calls[-1] == "release"

    def test_write_transcript_sidecar(self, tmp_path):
        from media.pipeline import _write_transcript_sidecar
        from media.models import MediaAsset

        media_path = tmp_path / "clip.mkv"
        media_path.write_bytes(b"video")
        asset = MediaAsset(path=str(media_path), filename=media_path.name)
        payload = {
            "meta": {"lang": "en"},
            "segments": [{"start": 0.0, "end": 1.25, "text": "Hello world"}],
        }

        vtt_path = _write_transcript_sidecar(asset, payload)
        assert vtt_path is not None
        assert vtt_path.exists()
        content = vtt_path.read_text(encoding="utf-8")
        assert "WEBVTT" in content
        assert "Hello world" in content

    def test_write_transcript_sidecar_falls_back_when_default_path_is_directory(self, tmp_path):
        from media.pipeline import _write_transcript_sidecar
        from media.models import MediaAsset

        media_path = tmp_path / "clip.mkv"
        media_path.write_bytes(b"video")
        media_path.with_suffix(".vtt").mkdir()
        asset = MediaAsset(path=str(media_path), filename=media_path.name)
        payload = {
            "meta": {"lang": "en"},
            "segments": [{"start": 0.0, "end": 1.25, "text": "Hello world"}],
        }

        vtt_path = _write_transcript_sidecar(asset, payload)

        assert vtt_path == media_path.with_name("clip.archivist.vtt")
        assert vtt_path.exists()
        assert "Hello world" in vtt_path.read_text(encoding="utf-8")

    def test_sidecar_path_for_write_skips_candidates_that_raise_oserror(self, monkeypatch):
        from media import pipeline

        class _FakeCandidate:
            def __init__(self, label, exists_error=False, exists_value=False, is_file_value=False):
                self.label = label
                self.exists_error = exists_error
                self.exists_value = exists_value
                self.is_file_value = is_file_value

            def exists(self):
                if self.exists_error:
                    raise OSError(24, "Too many open files")
                return self.exists_value

            def is_file(self):
                return self.is_file_value

        broken = _FakeCandidate("broken", exists_error=True)
        fallback = _FakeCandidate("fallback", exists_value=False)
        monkeypatch.setattr(pipeline, "_sidecar_candidate_paths", lambda asset_path, suffix: [broken, fallback])

        chosen = pipeline._sidecar_path_for_write("/tmp/clip.mkv", ".vtt")

        assert chosen is fallback

    def test_refresh_asset_state_from_disk_updates_saved_hash_and_size(self, tmp_path, monkeypatch):
        from media import pipeline
        from media.models import MediaAsset, Modality

        media_path = tmp_path / "clip.mkv"
        media_path.write_bytes(b"old")
        asset = MediaAsset(
            media_id="media123",
            path=str(media_path),
            filename=media_path.name,
            modality=Modality.VIDEO,
            file_hash="stale",
            file_size_bytes=1,
        )
        media_path.write_bytes(b"updated-content")

        saved_hashes = []
        monkeypatch.setattr(pipeline, "_save_asset", lambda saved_asset: saved_hashes.append(saved_asset.file_hash))

        refreshed = pipeline._refresh_asset_state_from_disk(asset)

        assert refreshed.file_size_bytes == len(b"updated-content")
        assert refreshed.file_hash == asset.compute_hash()
        assert saved_hashes == [refreshed.file_hash]

    def test_load_existing_transcript_payload(self, tmp_path):
        from media.pipeline import _load_existing_transcript_payload
        from media.models import MediaAsset

        media_path = tmp_path / "clip.mkv"
        media_path.write_bytes(b"video")
        vtt_path = media_path.with_suffix(".vtt")
        vtt_path.write_text(
            "WEBVTT\n\nNOTE\nSource: clip.mkv\nLanguage: en\n\n"
            "00:00:00.000 --> 00:00:01.250\nHello world\n\n"
            "00:00:01.250 --> 00:00:02.000\nSecond line\n",
            encoding="utf-8",
        )

        asset = MediaAsset(path=str(media_path), filename=media_path.name)
        payload = _load_existing_transcript_payload(asset)

        assert payload is not None
        assert payload["meta"]["source"] == "transcript_sidecar"
        assert payload["meta"]["reused"] is True
        assert payload["meta"]["segment_count"] == 2
        assert payload["segments"][0]["start"] == pytest.approx(0.0)
        assert payload["segments"][0]["end"] == pytest.approx(1.25)
        assert payload["segments"][0]["text"] == "Hello world"
        assert payload["text"] == "Hello world Second line"

    def test_load_existing_transcript_payload_finds_archivist_fallback_sidecar(self, tmp_path):
        from media.pipeline import _load_existing_transcript_payload
        from media.models import MediaAsset

        media_path = tmp_path / "clip.mkv"
        media_path.write_bytes(b"video")
        media_path.with_suffix(".vtt").mkdir()
        media_path.with_name("clip.archivist.vtt").write_text(
            "WEBVTT\n\nNOTE\nSource: clip.mkv\nLanguage: en\n\n"
            "00:00:00.000 --> 00:00:01.000\nFallback transcript\n",
            encoding="utf-8",
        )

        asset = MediaAsset(path=str(media_path), filename=media_path.name)
        payload = _load_existing_transcript_payload(asset)

        assert payload is not None
        assert payload["segments"][0]["text"] == "Fallback transcript"

    def test_load_existing_transcript_payload_filters_repeated_whisper_noise(self, tmp_path):
        from media.pipeline import _load_existing_transcript_payload
        from media.models import MediaAsset

        media_path = tmp_path / "clip.mkv"
        media_path.write_bytes(b"video")
        media_path.with_suffix(".vtt").write_text(
            "WEBVTT\n\nNOTE\nSource: clip.mkv\nLanguage: en\n\n"
            "00:00:00.000 --> 00:00:01.000\nYou\n\n"
            "00:00:01.000 --> 00:00:02.000\nThanks for watching!\n\n"
            "00:00:02.000 --> 00:00:05.000\nActual roadmap discussion starts here.\n\n"
            "00:00:05.000 --> 00:00:06.000\nThank you.\n",
            encoding="utf-8",
        )

        asset = MediaAsset(path=str(media_path), filename=media_path.name)
        payload = _load_existing_transcript_payload(asset)

        assert payload is not None
        assert payload["text"] == "Actual roadmap discussion starts here."
        assert [segment["text"] for segment in payload["segments"]] == ["Actual roadmap discussion starts here."]
        assert payload["meta"]["raw_segment_count"] == 4
        assert payload["meta"]["clean_segment_count"] == 1
        assert payload["meta"]["removed_segment_count"] == 3

    def test_derive_transcript_prefers_existing_sidecar(self, tmp_path, monkeypatch):
        from media.pipeline import _derive_transcript
        from media.models import MediaAsset, PipelineJob

        media_path = tmp_path / "clip.mkv"
        media_path.write_bytes(b"video")
        media_path.with_suffix(".vtt").write_text(
            "WEBVTT\n\n00:00:00.000 --> 00:00:01.000\nHello world\n",
            encoding="utf-8",
        )

        asset = MediaAsset(path=str(media_path), filename=media_path.name)
        fake_transcription = types.SimpleNamespace(
            is_available=lambda: (_ for _ in ()).throw(AssertionError("transcription backend should not be used")),
            init_transcription_model=lambda: (_ for _ in ()).throw(AssertionError("transcription init should not run")),
            transcribe_media_file=lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("transcription should not run")),
        )
        monkeypatch.setitem(sys.modules, "transcription_service", fake_transcription)

        payload = _derive_transcript(asset, PipelineJob())

        assert payload is not None
        assert payload["meta"]["source"] == "transcript_sidecar"
        assert payload["segments"][0]["text"] == "Hello world"

    def test_derive_transcript_filters_whisper_boilerplate_from_backend_segments(self, tmp_path, monkeypatch):
        from media.pipeline import _derive_transcript
        from media.models import MediaAsset, PipelineJob

        media_path = tmp_path / "clip.mkv"
        media_path.write_bytes(b"video")
        asset = MediaAsset(path=str(media_path), filename=media_path.name)

        fake_transcription = types.SimpleNamespace(
            is_available=lambda: True,
            init_transcription_model=lambda: None,
            transcribe_media_file=lambda *args, **kwargs: (
                "You Thanks for watching! Real planning discussion. Thank you.",
                {"lang": "en"},
                [
                    {"text": "You", "start": 0.0, "end": 1.0, "no_speech_prob": 0.0},
                    {"text": "Thanks for watching!", "start": 1.0, "end": 2.0, "no_speech_prob": 0.0},
                    {"text": "Real planning discussion.", "start": 2.0, "end": 5.0, "no_speech_prob": 0.0},
                    {"text": "Thank you.", "start": 5.0, "end": 6.0, "no_speech_prob": 0.0},
                ],
            ),
        )
        monkeypatch.setitem(sys.modules, "transcription_service", fake_transcription)

        payload = _derive_transcript(asset, PipelineJob())

        assert payload is not None
        assert payload["text"] == "Real planning discussion."
        assert [segment["text"] for segment in payload["segments"]] == ["Real planning discussion."]
        assert payload["meta"]["raw_segment_count"] == 4
        assert payload["meta"]["clean_segment_count"] == 1
        assert payload["meta"]["removed_segment_count"] == 3

    def test_write_pipeline_sidecar(self, tmp_path):
        from media.pipeline import _write_pipeline_sidecar
        from media.models import MediaAsset

        media_path = tmp_path / "clip.mkv"
        media_path.write_bytes(b"video")
        asset = MediaAsset(path=str(media_path), filename=media_path.name)
        result = {"media_id": "abc123", "artifacts": [{"kind": "transcript"}]}

        sidecar_path = _write_pipeline_sidecar(asset, result)
        assert sidecar_path == media_path.with_suffix(".json")
        assert sidecar_path.exists()
        payload = json.loads(sidecar_path.read_text(encoding="utf-8"))
        assert payload["media_id"] == "abc123"

    def test_write_pipeline_sidecar_falls_back_when_default_path_is_directory(self, tmp_path):
        from media.pipeline import _write_pipeline_sidecar
        from media.models import MediaAsset

        media_path = tmp_path / "clip.mkv"
        media_path.write_bytes(b"video")
        media_path.with_suffix(".json").mkdir()
        asset = MediaAsset(path=str(media_path), filename=media_path.name)
        result = {"media_id": "abc123", "artifacts": [{"kind": "transcript"}]}

        sidecar_path = _write_pipeline_sidecar(asset, result)

        assert sidecar_path == media_path.with_name("clip.archivist.json")
        assert sidecar_path.exists()
        payload = json.loads(sidecar_path.read_text(encoding="utf-8"))
        assert payload["media_id"] == "abc123"

    def test_generate_subject_line_falls_back_without_executor(self, monkeypatch):
        from media import pipeline
        from media.models import ComposedDocument, ContextualMemory, DerivedArtifact, MediaAsset, Modality, OutputFormat

        monkeypatch.setattr(pipeline, "AGENT_EXECUTOR_TOKEN", "")

        asset = MediaAsset(
            media_id="abc123",
            filename="clip.mkv",
            modality=Modality.VIDEO,
            duration_s=90.0,
        )
        memory = ContextualMemory(
            main_actors=["Andy", "Brianna"],
            inferred_themes=["launch planning"],
        )
        document = ComposedDocument(format=OutputFormat.MEETING_MINUTES, title="Meeting Minutes - abc123")
        artifacts = [
            DerivedArtifact(
                artifact_id="evt1",
                media_id="abc123",
                kind="event",
                content="We decided to move the launch to Friday.",
                metadata={"event_type": "decision", "entities": ["Friday"]},
            ),
        ]

        subject_line, details = pipeline._generate_subject_line(asset, artifacts, memory, document)
        assert subject_line == "Meeting on launch planning reaches concrete decisions."
        assert details["generator"] == "heuristic"
        assert details["reason"] == "executor_unconfigured"

    def test_generate_subject_line_uses_executor_when_configured(self, monkeypatch):
        from media import pipeline
        from media.models import ComposedDocument, ContextualMemory, DerivedArtifact, MediaAsset, Modality, OutputFormat

        asset = MediaAsset(
            media_id="abc123",
            filename="clip.mkv",
            modality=Modality.VIDEO,
            duration_s=90.0,
        )
        memory = ContextualMemory(main_actors=["Andy"], inferred_themes=["launch planning"])
        document = ComposedDocument(format=OutputFormat.EXECUTIVE_BRIEF, title="Executive Brief - abc123")
        artifacts = [
            DerivedArtifact(
                artifact_id="doc1",
                media_id="abc123",
                kind="document",
                content="Andy reviews launch planning and timelines with the team.",
            ),
        ]

        class _FakeResponse:
            def raise_for_status(self):
                return None

            def json(self):
                return {
                    "choices": [
                        {
                            "message": {
                                "content": "\"Andy reviews launch planning and timelines with the team.\"\nSecond sentence."
                            }
                        }
                    ]
                }

        class _FakeRequests:
            @staticmethod
            def post(url, json=None, headers=None, timeout=None):
                assert url == "http://executor/v1/chat/completions"
                assert json["model"] == "test-model"
                assert headers["x-agent-id"] == "archivist-main"
                assert headers["x-agent-session-key"] == "agent:archivist-main:media-subject:abc123"
                assert json["user"] == "agent:archivist-main:media-subject:abc123"
                return _FakeResponse()

        monkeypatch.setattr(pipeline, "AGENT_EXECUTOR_TOKEN", "token")
        monkeypatch.setattr(pipeline, "AGENT_EXECUTOR_URL", "http://executor")
        monkeypatch.setattr(pipeline, "AGENT_CHAT_MODEL", "test-model")
        monkeypatch.setenv("ARCHIVIST_MEDIA_AGENT_ID", "archivist-main")
        monkeypatch.setitem(sys.modules, "requests", _FakeRequests)

        subject_line, details = pipeline._generate_subject_line(asset, artifacts, memory, document)
        assert subject_line == "Andy reviews launch planning and timelines with the team."
        assert details["generator"] == "agent-executor"
        assert details["model"] == "test-model"

    def test_generate_subject_line_filters_noisy_participants(self, monkeypatch):
        from media import pipeline
        from media.models import ComposedDocument, ContextualMemory, DerivedArtifact, MediaAsset, Modality, OutputFormat

        monkeypatch.setattr(pipeline, "AGENT_EXECUTOR_TOKEN", "")

        asset = MediaAsset(
            media_id="abc123",
            filename="clip.mkv",
            modality=Modality.VIDEO,
            duration_s=90.0,
        )
        memory = ContextualMemory(main_actors=["Evan", "Andy", "They", "Yep", "Brianna"])
        document = ComposedDocument(format=OutputFormat.MEETING_MINUTES, title="Meeting Minutes - abc123")
        artifacts = [
            DerivedArtifact(
                artifact_id="evt1",
                media_id="abc123",
                kind="event",
                content="We decided to move the launch to Friday.",
                metadata={"event_type": "decision", "entities": ["Are", "California"]},
            ),
        ]

        subject_line, details = pipeline._generate_subject_line(asset, artifacts, memory, document)
        assert subject_line == "Decision to move the launch to Friday."
        assert details["generator"] == "heuristic"

    def test_generate_subject_line_rejects_conjunction_led_output(self, monkeypatch):
        from media import pipeline
        from media.models import ComposedDocument, ContextualMemory, DerivedArtifact, MediaAsset, Modality, OutputFormat

        asset = MediaAsset(
            media_id="abc123",
            filename="clip.mkv",
            modality=Modality.VIDEO,
            duration_s=90.0,
        )
        memory = ContextualMemory(
            main_actors=["Sean"],
            inferred_themes=["AI", "ID"],
        )
        document = ComposedDocument(format=OutputFormat.MEETING_MINUTES, title="Meeting Minutes - abc123")
        artifacts = [
            DerivedArtifact(
                artifact_id="evt1",
                media_id="abc123",
                kind="event",
                content="We decided to keep AI and ID linked.",
                metadata={"event_type": "decision", "entities": ["AI", "ID"]},
            ),
            DerivedArtifact(
                artifact_id="evt2",
                media_id="abc123",
                kind="event",
                content="What should happen to the fallback identity flow?",
                metadata={"event_type": "question", "entities": ["identity"]},
            ),
        ]

        class _FakeResponse:
            def raise_for_status(self):
                return None

            def json(self):
                return {
                    "choices": [
                        {
                            "message": {
                                "content": "And, Atlassian, and Sean discuss decisions and open questions around AI and ID."
                            }
                        }
                    ]
                }

        class _FakeRequests:
            @staticmethod
            def post(url, json=None, headers=None, timeout=None):
                assert url == "http://executor/v1/chat/completions"
                assert json["model"] == "test-model"
                assert headers["x-agent-id"] == "archivist-main"
                assert headers["x-agent-session-key"] == "agent:archivist-main:media-subject:abc123"
                assert json["user"] == "agent:archivist-main:media-subject:abc123"
                return _FakeResponse()

        monkeypatch.setattr(pipeline, "AGENT_EXECUTOR_TOKEN", "token")
        monkeypatch.setattr(pipeline, "AGENT_EXECUTOR_URL", "http://executor")
        monkeypatch.setattr(pipeline, "AGENT_CHAT_MODEL", "test-model")
        monkeypatch.setenv("ARCHIVIST_MEDIA_AGENT_ID", "archivist-main")
        monkeypatch.setitem(sys.modules, "requests", _FakeRequests)

        subject_line, details = pipeline._generate_subject_line(asset, artifacts, memory, document)
        assert subject_line == "Meeting on AI and ID covers decisions and open questions."
        assert details["generator"] == "agent-executor"

    def test_select_public_artifacts_keeps_only_clean_bundle_outputs(self):
        from media import pipeline
        from media.models import DerivedArtifact

        artifacts = [
            DerivedArtifact(artifact_id="evt1", media_id="abc123", kind="event"),
            DerivedArtifact(artifact_id="seg1", media_id="abc123", kind="speech_segment"),
            DerivedArtifact(artifact_id="doc1", media_id="abc123", kind="document"),
            DerivedArtifact(artifact_id="mem1", media_id="abc123", kind="memory"),
            DerivedArtifact(artifact_id="tx1", media_id="abc123", kind="transcript"),
            DerivedArtifact(artifact_id="sub1", media_id="abc123", kind="subject_line"),
            DerivedArtifact(artifact_id="rec1", media_id="abc123", kind="recap"),
            DerivedArtifact(artifact_id="kf1", media_id="abc123", kind="keyframe"),
        ]

        public_artifacts = pipeline._select_public_artifacts(artifacts)
        assert [artifact.kind for artifact in public_artifacts] == [
            "subject_line",
            "memory",
            "document",
            "transcript",
        ]

    def test_inject_metadata_into_mkv_embeds_transcript_and_bundle(self, tmp_path, monkeypatch):
        from media import pipeline
        from media.models import ComposedDocument, ContextualMemory, MediaAsset, Modality, OutputFormat

        media_path = tmp_path / "clip.mkv"
        media_path.write_bytes(b"source")
        bundle_path = tmp_path / "bundle.json"
        bundle_path.write_text("{}", encoding="utf-8")

        commands = []
        real_run = subprocess.run

        def fake_run(cmd, *args, **kwargs):
            commands.append(cmd)
            if cmd[0] == "ffprobe":
                return subprocess.CompletedProcess(cmd, 0, stdout='{"streams":[]}', stderr="")
            if cmd[0] == "ffmpeg":
                tmp_output = tmp_path / "clip.archivist_tmp.mkv"
                tmp_output.write_bytes(b"remuxed")
                return subprocess.CompletedProcess(cmd, 0, stdout=b"", stderr=b"")
            return real_run(cmd, *args, **kwargs)

        monkeypatch.setattr(subprocess, "run", fake_run)

        asset = MediaAsset(path=str(media_path), filename=media_path.name, modality=Modality.VIDEO)
        memory = ContextualMemory(main_actors=["Alice"], inferred_themes=["Demo"])
        document = ComposedDocument(format=OutputFormat.CHRONOLOGICAL, title="Chronological - test")
        payload = {"meta": {"lang": "en"}, "segments": [{"start": 0.0, "end": 1.0, "text": "Hello"}]}

        info = pipeline._inject_metadata_into_file(
            asset,
            memory,
            document,
            transcript_payload=payload,
            result_path=bundle_path,
        )

        ffmpeg_cmd = next(cmd for cmd in commands if cmd[0] == "ffmpeg")
        assert info["status"] == "embedded"
        assert info["transcript_stream_embedded"] is True
        assert info["artifact_bundle_attached"] is True
        assert "-attach" in ffmpeg_cmd
        assert str(bundle_path) in ffmpeg_cmd
        assert str(media_path.with_suffix(".vtt")) in ffmpeg_cmd

    def test_inject_metadata_prefers_subject_line_for_title(self, tmp_path, monkeypatch):
        from media import pipeline
        from media.models import ComposedDocument, ContextualMemory, MediaAsset, Modality, OutputFormat

        media_path = tmp_path / "clip.mkv"
        media_path.write_bytes(b"source")
        bundle_path = tmp_path / "bundle.json"
        bundle_path.write_text("{}", encoding="utf-8")

        commands = []
        real_run = subprocess.run

        def fake_run(cmd, *args, **kwargs):
            commands.append(cmd)
            if cmd[0] == "ffprobe":
                return subprocess.CompletedProcess(cmd, 0, stdout='{"streams":[]}', stderr="")
            if cmd[0] == "ffmpeg":
                tmp_output = tmp_path / "clip.archivist_tmp.mkv"
                tmp_output.write_bytes(b"remuxed")
                return subprocess.CompletedProcess(cmd, 0, stdout=b"", stderr=b"")
            return real_run(cmd, *args, **kwargs)

        monkeypatch.setattr(subprocess, "run", fake_run)

        asset = MediaAsset(path=str(media_path), filename=media_path.name, modality=Modality.VIDEO)
        memory = ContextualMemory(main_actors=["Andy", "Brianna"])
        document = ComposedDocument(format=OutputFormat.MEETING_MINUTES, title="Meeting Minutes - test")
        payload = {"meta": {"lang": "en"}, "segments": [{"start": 0.0, "end": 1.0, "text": "Hello"}]}

        pipeline._inject_metadata_into_file(
            asset,
            memory,
            document,
            transcript_payload=payload,
            result_path=bundle_path,
            subject_line="Andy and Brianna review launch planning and next steps.",
        )

        ffmpeg_cmd = next(cmd for cmd in commands if cmd[0] == "ffmpeg")
        assert "title=Andy and Brianna review launch planning and next steps." in ffmpeg_cmd
        assert "description=Meeting Minutes - test" in ffmpeg_cmd

    def test_inject_metadata_reuses_existing_transcript_sidecar(self, tmp_path, monkeypatch):
        from media import pipeline
        from media.models import ComposedDocument, ContextualMemory, MediaAsset, Modality, OutputFormat

        media_path = tmp_path / "clip.mkv"
        media_path.write_bytes(b"source")
        vtt_path = media_path.with_suffix(".vtt")
        vtt_path.write_text("WEBVTT\n\n00:00:00.000 --> 00:00:01.000\nHello\n", encoding="utf-8")
        bundle_path = tmp_path / "bundle.json"
        bundle_path.write_text("{}", encoding="utf-8")

        commands = []
        real_run = subprocess.run

        def fake_run(cmd, *args, **kwargs):
            commands.append(cmd)
            if cmd[0] == "ffprobe":
                return subprocess.CompletedProcess(
                    cmd,
                    0,
                    stdout=json.dumps(
                        {
                            "streams": [
                                {"index": 4, "codec_type": "subtitle", "tags": {"title": "Archivist Transcript"}},
                            ]
                        }
                    ),
                    stderr="",
                )
            if cmd[0] == "ffmpeg":
                tmp_output = tmp_path / "clip.archivist_tmp.mkv"
                tmp_output.write_bytes(b"remuxed")
                return subprocess.CompletedProcess(cmd, 0, stdout=b"", stderr=b"")
            return real_run(cmd, *args, **kwargs)

        monkeypatch.setattr(subprocess, "run", fake_run)

        asset = MediaAsset(path=str(media_path), filename=media_path.name, modality=Modality.VIDEO)
        memory = ContextualMemory(main_actors=["Andy", "They", "Brianna", "Yep"])
        document = ComposedDocument(format=OutputFormat.MEETING_MINUTES, title="Meeting Minutes - test")

        info = pipeline._inject_metadata_into_file(
            asset,
            memory,
            document,
            transcript_payload=None,
            result_path=bundle_path,
            subject_line="Andy and Brianna discuss the launch plan.",
        )

        ffmpeg_cmd = next(cmd for cmd in commands if cmd[0] == "ffmpeg")
        assert info["status"] == "embedded"
        assert info["transcript_sidecar_path"] == str(vtt_path)
        assert info["transcript_stream_embedded"] is True
        assert str(vtt_path) in ffmpeg_cmd
        assert any("artist=Andy, Brianna" == item for item in ffmpeg_cmd)
        assert any("Participants: Andy, Brianna" in item for item in ffmpeg_cmd)

    def test_inject_metadata_replaces_existing_archivist_streams(self, tmp_path, monkeypatch):
        from media import pipeline
        from media.models import ComposedDocument, ContextualMemory, MediaAsset, Modality, OutputFormat

        media_path = tmp_path / "clip.mkv"
        media_path.write_bytes(b"source")
        bundle_path = tmp_path / "bundle.json"
        bundle_path.write_text("{}", encoding="utf-8")

        commands = []
        real_run = subprocess.run

        def fake_run(cmd, *args, **kwargs):
            commands.append(cmd)
            if cmd[0] == "ffprobe":
                return subprocess.CompletedProcess(
                    cmd,
                    0,
                    stdout=json.dumps(
                        {
                            "streams": [
                                {"index": 4, "codec_type": "subtitle", "tags": {"title": "Archivist Transcript"}},
                                {"index": 5, "codec_type": "attachment", "tags": {"filename": "archivist_media_pipeline.json"}},
                            ]
                        }
                    ),
                    stderr="",
                )
            if cmd[0] == "ffmpeg":
                tmp_output = tmp_path / "clip.archivist_tmp.mkv"
                tmp_output.write_bytes(b"remuxed")
                return subprocess.CompletedProcess(cmd, 0, stdout=b"", stderr=b"")
            return real_run(cmd, *args, **kwargs)

        monkeypatch.setattr(subprocess, "run", fake_run)

        asset = MediaAsset(path=str(media_path), filename=media_path.name, modality=Modality.VIDEO)
        memory = ContextualMemory(main_actors=["Andy", "Brianna"])
        document = ComposedDocument(format=OutputFormat.MEETING_MINUTES, title="Meeting Minutes - test")
        payload = {"meta": {"lang": "en"}, "segments": [{"start": 0.0, "end": 1.0, "text": "Hello"}]}

        info = pipeline._inject_metadata_into_file(
            asset,
            memory,
            document,
            transcript_payload=payload,
            result_path=bundle_path,
        )

        ffmpeg_cmd = next(cmd for cmd in commands if cmd[0] == "ffmpeg")
        assert info["status"] == "embedded"
        assert "-0:4" in ffmpeg_cmd
        assert "-0:5" in ffmpeg_cmd

    def test_inject_metadata_writes_processing_stamp(self, tmp_path, monkeypatch):
        from media import pipeline
        from media.models import ComposedDocument, ContextualMemory, MediaAsset, Modality, OutputFormat

        media_path = tmp_path / "clip.mkv"
        media_path.write_bytes(b"source")
        bundle_path = tmp_path / "bundle.json"
        bundle_path.write_text("{}", encoding="utf-8")

        commands = []
        real_run = subprocess.run

        def fake_run(cmd, *args, **kwargs):
            commands.append(cmd)
            if cmd[0] == "ffprobe":
                return subprocess.CompletedProcess(cmd, 0, stdout='{"streams":[]}', stderr="")
            if cmd[0] == "ffmpeg":
                tmp_output = tmp_path / "clip.archivist_tmp.mkv"
                tmp_output.write_bytes(b"remuxed")
                return subprocess.CompletedProcess(cmd, 0, stdout=b"", stderr=b"")
            return real_run(cmd, *args, **kwargs)

        monkeypatch.setattr(subprocess, "run", fake_run)

        asset = MediaAsset(path=str(media_path), filename=media_path.name, modality=Modality.VIDEO, file_hash="abc123def456")
        memory = ContextualMemory(main_actors=["Andy"], inferred_themes=["Journal"])
        document = ComposedDocument(format=OutputFormat.MEETING_MINUTES, title="Meeting Minutes - test")
        payload = {"meta": {"lang": "en"}, "segments": [{"start": 0.0, "end": 1.0, "text": "Hello"}]}
        stamp = {
            "pipeline_version": "test-version",
            "pipeline_compat_version": "compat-version",
            "repo_commit": "0123456789abcdef0123456789abcdef01234567",
            "repo_commit_suffix": "456789abcdef",
            "source_file_hash": "abc123def4567890",
            "source_mtime_ns": 123456789,
            "document_format": "meeting_minutes",
        }

        pipeline._inject_metadata_into_file(
            asset,
            memory,
            document,
            transcript_payload=payload,
            result_path=bundle_path,
            subject_line="Andy reviews the journal pipeline behavior.",
            pipeline_stamp=stamp,
        )

        ffmpeg_cmd = next(cmd for cmd in commands if cmd[0] == "ffmpeg")
        joined = " ".join(str(part) for part in ffmpeg_cmd)
        assert "Archivist pipeline 456789abcdef" in joined
        assert "keywords=archivist,media-pipeline,version:456789abcdef,compat:compat-version,hash:abc123def456" in joined

    def test_resolve_repo_version_tag_uses_commit_suffix(self):
        from media import pipeline

        commit_hash = "e96b26af4e9a3dc240b202fd35025679262e3c86"
        assert pipeline._resolve_repo_version_tag(commit_hash) == "5679262e3c86"

    def test_resolve_repo_commit_hash_reads_git_files_without_git_binary(self, tmp_path, monkeypatch):
        from media import pipeline

        repo_root = tmp_path / "repo"
        git_dir = repo_root / ".git"
        refs_dir = git_dir / "refs" / "heads"
        refs_dir.mkdir(parents=True)
        commit_hash = "e96b26af4e9a3dc240b202fd35025679262e3c86"
        (git_dir / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
        (refs_dir / "main").write_text(f"{commit_hash}\n", encoding="utf-8")

        def fake_run(*args, **kwargs):
            raise FileNotFoundError("git not installed")

        monkeypatch.setattr(pipeline.subprocess, "run", fake_run)

        assert pipeline._resolve_repo_commit_hash(repo_root) == commit_hash

    def test_asset_record_complete_requires_pipeline_result(self, tmp_path, monkeypatch):
        from media import pipeline

        monkeypatch.setattr(pipeline, "PIPELINE_STORE_DIR", tmp_path / "pipeline")
        pipeline.PIPELINE_STORE_DIR.mkdir(parents=True)
        media_path = tmp_path / "clip.mkv"
        media_path.write_bytes(b"video")

        asset_data = {
            "media_id": "abc123",
            "path": str(media_path),
            "file_hash": "hash123",
            "file_size_bytes": media_path.stat().st_size,
        }
        assert pipeline._asset_record_complete(asset_data) is False

        (pipeline.PIPELINE_STORE_DIR / "abc123.json").write_text(
            json.dumps(
                {
                    "archivist_pipeline": {
                        "pipeline_version": pipeline.MEDIA_PIPELINE_VERSION,
                        "pipeline_compat_version": pipeline.MEDIA_PIPELINE_COMPAT_VERSION,
                        "source_path": str(media_path.resolve()),
                        "source_file_hash": "hash123",
                        "source_size_bytes": media_path.stat().st_size,
                        "source_mtime_ns": media_path.stat().st_mtime_ns,
                    },
                    "layers": {
                        "L6_vectorstore": {
                            "chunks_created": 3,
                            "chunks_inserted": 3,
                            "collection": "documents_transcripts",
                            "error": None,
                            "source_id": "media:abc123",
                            "file_hash": "hash123",
                        }
                    },
                }
            ),
            encoding="utf-8",
        )
        assert pipeline._asset_record_complete(asset_data) is True

    def test_asset_record_complete_requires_current_pipeline_stamp(self, tmp_path, monkeypatch):
        from media import pipeline

        monkeypatch.setattr(pipeline, "PIPELINE_STORE_DIR", tmp_path / "pipeline")
        pipeline.PIPELINE_STORE_DIR.mkdir(parents=True)
        media_path = tmp_path / "clip.mkv"
        media_path.write_bytes(b"video")

        current_mtime_ns = media_path.stat().st_mtime_ns
        asset_data = {
            "media_id": "abc123",
            "path": str(media_path),
            "file_hash": "hash123",
            "file_size_bytes": media_path.stat().st_size,
        }

        stale_result = {
            "archivist_pipeline": {
                "pipeline_version": "old-version",
                "source_path": str(media_path.resolve()),
                "source_file_hash": "hash123",
                "source_size_bytes": media_path.stat().st_size,
                "source_mtime_ns": current_mtime_ns,
            }
        }
        (pipeline.PIPELINE_STORE_DIR / "abc123.json").write_text(json.dumps(stale_result), encoding="utf-8")
        assert pipeline._asset_record_complete(asset_data) is False

        current_result = {
            "archivist_pipeline": {
                "pipeline_version": "repo-tag-123456",
                "pipeline_compat_version": pipeline.MEDIA_PIPELINE_COMPAT_VERSION,
                "source_path": str(media_path.resolve()),
                "source_file_hash": "hash123",
                "source_size_bytes": media_path.stat().st_size,
                "source_mtime_ns": current_mtime_ns,
            },
            "layers": {
                "L6_vectorstore": {
                    "chunks_created": 2,
                    "chunks_inserted": 2,
                    "collection": "documents_transcripts",
                    "error": None,
                    "source_id": "media:abc123",
                    "file_hash": "hash123",
                }
            },
        }
        (pipeline.PIPELINE_STORE_DIR / "abc123.json").write_text(json.dumps(current_result), encoding="utf-8")
        assert pipeline._asset_record_complete(asset_data) is True

    def test_process_media_file_reuses_current_result(self, tmp_path, monkeypatch):
        from media import pipeline
        from media.models import MediaAsset, Modality

        pipeline_dir = tmp_path / "pipeline"
        pipeline_dir.mkdir()
        monkeypatch.setattr(pipeline, "PIPELINE_STORE_DIR", pipeline_dir)

        media_path = tmp_path / "clip.mkv"
        media_path.write_bytes(b"video")
        asset = MediaAsset(
            media_id="media123",
            path=str(media_path.resolve()),
            filename=media_path.name,
            modality=Modality.VIDEO,
            file_size_bytes=media_path.stat().st_size,
            created_at=media_path.stat().st_mtime,
            indexed_at=media_path.stat().st_mtime,
        )
        asset.compute_hash()

        existing_result = {
            "media_id": asset.media_id,
            "document": {"format": "meeting_minutes", "title": "Current result"},
            "layers": {
                "L6_vectorstore": {
                    "chunks_created": 4,
                    "chunks_inserted": 4,
                    "collection": "documents_transcripts",
                    "error": None,
                    "source_id": f"media:{asset.media_id}",
                    "file_hash": asset.file_hash,
                }
            },
            "archivist_pipeline": {
                "pipeline_version": "repo-tag-123456",
                "pipeline_compat_version": pipeline.MEDIA_PIPELINE_COMPAT_VERSION,
                "source_path": asset.path,
                "source_file_hash": asset.file_hash,
                "source_size_bytes": asset.file_size_bytes,
                "source_mtime_ns": media_path.stat().st_mtime_ns,
                "document_format": "meeting_minutes",
            },
        }
        (pipeline_dir / f"{asset.media_id}.json").write_text(json.dumps(existing_result), encoding="utf-8")

        monkeypatch.setattr(pipeline, "register_asset", lambda path, metadata=None: asset)

        def fail_if_called(*args, **kwargs):
            raise AssertionError("pipeline should have reused the existing current result")

        monkeypatch.setattr(pipeline, "_derive_transcript", fail_if_called)

        result = pipeline.process_media_file(str(media_path))

        assert result["reused_existing_result"] is True
        assert result["skip_reason"] == "current_pipeline_result"
        assert result["media_id"] == asset.media_id

    def test_process_media_file_backfills_vectorstore_for_current_result(self, tmp_path, monkeypatch):
        from media import pipeline
        from media.models import MediaAsset, Modality

        pipeline_dir = tmp_path / "pipeline"
        pipeline_dir.mkdir()
        monkeypatch.setattr(pipeline, "PIPELINE_STORE_DIR", pipeline_dir)

        media_path = tmp_path / "clip.mkv"
        media_path.write_bytes(b"video")
        asset = MediaAsset(
            media_id="media123",
            path=str(media_path.resolve()),
            filename=media_path.name,
            modality=Modality.VIDEO,
            file_size_bytes=media_path.stat().st_size,
            created_at=media_path.stat().st_mtime,
            indexed_at=media_path.stat().st_mtime,
        )
        asset.compute_hash()

        existing_result = {
            "media_id": asset.media_id,
            "document": {"format": "meeting_minutes", "title": "Current result"},
            "layers": {},
            "archivist_pipeline": {
                "pipeline_version": "repo-tag-123456",
                "pipeline_compat_version": pipeline.MEDIA_PIPELINE_COMPAT_VERSION,
                "source_path": asset.path,
                "source_file_hash": asset.file_hash,
                "source_size_bytes": asset.file_size_bytes,
                "source_mtime_ns": media_path.stat().st_mtime_ns,
                "document_format": "meeting_minutes",
            },
        }
        (pipeline_dir / f"{asset.media_id}.json").write_text(json.dumps(existing_result), encoding="utf-8")

        monkeypatch.setattr(pipeline, "register_asset", lambda path, metadata=None: asset)
        monkeypatch.setattr(
            pipeline,
            "_backfill_saved_vectorstore_projection",
            lambda asset, result: {
                "chunks_created": 4,
                "chunks_inserted": 4,
                "collection": "documents_transcripts",
                "error": None,
                "source_id": f"media:{asset.media_id}",
                "file_hash": asset.file_hash,
            },
        )

        def fail_if_called(*args, **kwargs):
            raise AssertionError("pipeline should not rerun when vectorstore backfill succeeds")

        monkeypatch.setattr(pipeline, "_derive_transcript", fail_if_called)

        result = pipeline.process_media_file(str(media_path))

        assert result["reused_existing_result"] is True
        assert result["skip_reason"] == "current_pipeline_result"
        assert result["layers"]["L6_vectorstore"]["file_hash"] == asset.file_hash


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
