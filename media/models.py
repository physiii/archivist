"""Data models for the hierarchical media processing pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
from pathlib import Path
from typing import Optional
from uuid import uuid4


class Modality(str, Enum):
    AUDIO = "audio"
    VIDEO = "video"
    IMAGE = "image"
    TEXT = "text"


class EventType(str, Enum):
    SPEECH = "speech"
    OBSERVATION = "observation"
    ACTION = "action"
    DECISION = "decision"
    QUESTION = "question"
    SCENE_CHANGE = "scene_change"
    SILENCE = "silence"
    NOISE = "noise"
    OCR_TEXT = "ocr_text"
    UNKNOWN = "unknown"


class SalienceTag(str, Enum):
    """Tags for marking content salience without deletion."""
    FILLER = "filler"
    UNCERTAINTY = "uncertainty"
    INTERRUPTION = "interruption"
    EMPHASIS = "emphasis"
    DECISION = "decision"
    ACTION_ITEM = "action_item"
    CONTRADICTION = "contradiction"
    REFERENCE = "reference"
    LOW_CONFIDENCE = "low_confidence"
    BOILERPLATE = "boilerplate"
    DUPLICATE = "duplicate"


class OutputFormat(str, Enum):
    CHRONOLOGICAL = "chronological"
    THEMATIC = "thematic"
    NARRATIVE = "narrative"
    HYBRID = "hybrid"
    MEETING_MINUTES = "meeting_minutes"
    INCIDENT_REPORT = "incident_report"
    EXECUTIVE_BRIEF = "executive_brief"


# ── L0: Raw Evidence ────────────────────────────────────────────────────


@dataclass
class MediaAsset:
    """A raw media file registered in the evidence store."""
    media_id: str = field(default_factory=lambda: uuid4().hex[:16])
    path: str = ""
    filename: str = ""
    modality: Modality = Modality.AUDIO
    file_hash: str = ""
    file_size_bytes: int = 0
    duration_s: float = 0.0
    sample_rate: int = 0
    width: int = 0
    height: int = 0
    fps: float = 0.0
    codec: str = ""
    created_at: float = 0.0
    indexed_at: float = 0.0
    metadata: dict = field(default_factory=dict)

    def compute_hash(self) -> str:
        if self.path and Path(self.path).exists():
            h = sha256()
            with open(self.path, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    h.update(chunk)
            self.file_hash = h.hexdigest()
        return self.file_hash


@dataclass
class DerivedArtifact:
    """An artifact derived from a media asset (transcript, keyframe, OCR, etc.)."""
    artifact_id: str = field(default_factory=lambda: uuid4().hex[:16])
    media_id: str = ""
    kind: str = ""  # transcript, keyframe, ocr, caption, embedding, diarization
    start_s: float = 0.0
    end_s: float = 0.0
    content: str = ""
    confidence: float = 1.0
    metadata: dict = field(default_factory=dict)
    source_refs: list[str] = field(default_factory=list)


# ── L1: Filtered Evidence ───────────────────────────────────────────────


@dataclass
class FilterResult:
    """Result of filtering a media span for salience."""
    artifact_id: str = ""
    keep: bool = True
    reason: str = ""
    score: float = 1.0  # 0.0 = discard, 1.0 = keep
    tags: list[SalienceTag] = field(default_factory=list)


@dataclass
class SceneSegment:
    """A detected scene or shot boundary in video."""
    start_s: float = 0.0
    end_s: float = 0.0
    scene_score: float = 0.0
    motion_score: float = 0.0
    sharpness_score: float = 0.0
    keyframe_path: str = ""
    ocr_text: str = ""
    labels: list[str] = field(default_factory=list)


@dataclass
class SpeechSegment:
    """A speech segment from VAD/diarization."""
    start_s: float = 0.0
    end_s: float = 0.0
    speaker: str = ""
    text: str = ""
    confidence: float = 1.0
    salience_tags: list[SalienceTag] = field(default_factory=list)
    word_timestamps: list[dict] = field(default_factory=list)


# ── L2: Atomic Events ──────────────────────────────────────────────────


@dataclass
class AtomicEvent:
    """A timestamped structured event extracted from evidence.

    The canonical truth of the pipeline lives here. Each event should retain
    provenance-rich metadata so higher layers can compress aggressively without
    losing inspectability.
    """
    event_id: str = field(default_factory=lambda: f"evt_{uuid4().hex[:8]}")
    time_start: float = 0.0
    time_end: float = 0.0
    speakers: list[str] = field(default_factory=list)
    visual_entities: list[str] = field(default_factory=list)
    text_evidence: str = ""
    event_type: EventType = EventType.UNKNOWN
    confidence: float = 0.0
    source_refs: list[str] = field(default_factory=list)
    salience_tags: list[SalienceTag] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


# ── L3: Local Recaps ───────────────────────────────────────────────────


@dataclass
class LocalRecap:
    """A step-by-step event-ledger view over a group of atomic events."""
    recap_id: str = field(default_factory=lambda: f"recap_{uuid4().hex[:8]}")
    group_type: str = ""  # scene, conversation_turn, chapter, episode, incident_phase
    time_start: float = 0.0
    time_end: float = 0.0
    recap_text: str = ""
    window_summary: str = ""
    salient_entities: list[str] = field(default_factory=list)
    unresolved_questions: list[str] = field(default_factory=list)
    emotional_tone: str = ""
    causal_links: list[str] = field(default_factory=list)
    event_ids: list[str] = field(default_factory=list)
    summary_refs: list[dict] = field(default_factory=list)
    ledger_entries: list[dict] = field(default_factory=list)
    source_refs: list[str] = field(default_factory=list)


# ── L4: Contextual Memory ──────────────────────────────────────────────


@dataclass
class ContextualMemory:
    """Compressed contextual account built from local recaps and event provenance."""
    memory_id: str = field(default_factory=lambda: f"mem_{uuid4().hex[:8]}")
    media_id: str = ""
    context_overview: str = ""
    main_actors: list[str] = field(default_factory=list)
    timeline_anchors: list[dict] = field(default_factory=list)
    locations: list[str] = field(default_factory=list)
    open_loops: list[str] = field(default_factory=list)
    inferred_themes: list[str] = field(default_factory=list)
    risk_safety_issues: list[str] = field(default_factory=list)
    contradictions: list[str] = field(default_factory=list)
    notable_evidence: list[str] = field(default_factory=list)
    final_takeaways: list[str] = field(default_factory=list)
    interpretive_notes: list[dict] = field(default_factory=list)
    evidence_map: dict[str, list[dict]] = field(default_factory=dict)
    recap_ids: list[str] = field(default_factory=list)


# ── L5: Composed Document ──────────────────────────────────────────────


@dataclass
class ComposedDocument:
    """A task-specific final document generated from contextual memory."""
    document_id: str = field(default_factory=lambda: f"doc_{uuid4().hex[:8]}")
    media_id: str = ""
    format: OutputFormat = OutputFormat.CHRONOLOGICAL
    title: str = ""
    sections: list[dict] = field(default_factory=list)
    full_text: str = ""
    memory_id: str = ""
    source_refs: list[str] = field(default_factory=list)
    generated_at: float = 0.0


# ── Pipeline Job Tracking ───────────────────────────────────────────────


@dataclass
class PipelineJob:
    """Tracks the state of a media processing job."""
    job_id: str = field(default_factory=lambda: uuid4().hex[:12])
    media_id: str = ""
    status: str = "pending"  # pending, deriving, filtering, extracting, recapping, composing, done, error
    current_layer: str = ""
    progress: float = 0.0
    started_at: float = 0.0
    finished_at: float = 0.0
    error: str = ""
    artifacts_count: int = 0
    events_count: int = 0
    recaps_count: int = 0
