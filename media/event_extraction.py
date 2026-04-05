"""L2: Atomic event extraction - convert filtered evidence into structured event records.

Each event is a timestamped fact with references back to source evidence.
This is the bridge between raw evidence and higher-level narrative.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Optional

from media.models import (
    AtomicEvent,
    DerivedArtifact,
    EventType,
    SalienceTag,
    SceneSegment,
    SpeechSegment,
)

logger = logging.getLogger("archivist.media.events")

MAX_EVENT_DURATION_S = max(15.0, float(os.getenv("MEDIA_MAX_EVENT_DURATION_S", "90")))
MAX_EVENT_SEGMENTS = max(3, int(os.getenv("MEDIA_MAX_EVENT_SEGMENTS", "40")))
MAX_EVENT_WORDS = max(40, int(os.getenv("MEDIA_MAX_EVENT_WORDS", "220")))

ENTITY_STOP_WORDS = {
    "a", "actually", "again", "all", "also", "amazing", "and", "another", "any", "anything",
    "basically", "because", "best", "better", "brief", "but", "bye", "can", "chatgpt",
    "classification", "classifier", "cool", "course", "data", "december", "demo",
    "document", "documents", "done", "easy", "energy", "exactly", "extraction", "first",
    "forget", "get", "going", "great", "guys", "have", "hello", "here", "hey", "hopefully",
    "how", "however", "i", "idea", "if", "immediately", "in", "it", "january", "jump",
    "just", "kind", "last", "let", "like", "look", "makes", "manual", "maybe", "meeting",
    "more", "mosfet", "my", "next", "no", "not", "now",
    "okay", "our", "over", "pay", "pay stub", "pay stubs", "pdf", "please", "product", "prompt",
    "prompts", "quality", "really", "right", "same", "second", "see", "since", "slack", "snacks",
    "so", "sorry", "summary", "system", "thank", "thanks", "that", "the", "then", "there",
    "these", "this", "those", "transcript", "true", "up", "use", "vector", "well", "what",
    "when", "where", "which", "why", "with", "workflow", "yeah", "yes", "you", "your",
}


def _classify_event_type(text: str) -> EventType:
    """Classify the type of event from its text content.

    Uses keyword heuristics. A proper implementation would use an LLM
    for nuanced classification.
    """
    lower = text.lower()

    question_patterns = [r"\?$", r"^(who|what|when|where|why|how|is|are|do|does|can|could|would|should)\b"]
    for pattern in question_patterns:
        if re.search(pattern, lower):
            return EventType.QUESTION

    decision_keywords = ["decided", "agreed", "approved", "rejected", "will", "going to", "plan to", "let's"]
    if any(kw in lower for kw in decision_keywords):
        return EventType.DECISION

    action_keywords = ["did", "went", "made", "created", "built", "fixed", "moved", "started", "stopped"]
    if any(kw in lower for kw in action_keywords):
        return EventType.ACTION

    observation_keywords = ["saw", "noticed", "found", "appears", "seems", "looks like", "there is", "there are"]
    if any(kw in lower for kw in observation_keywords):
        return EventType.OBSERVATION

    return EventType.SPEECH


def _extract_entities(text: str) -> list[str]:
    """Extract named entities from text using simple heuristics.

    Finds capitalized multi-word phrases that likely represent names,
    places, or organizations.
    """
    entities = []
    matches = re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b", text)
    for match in matches:
        parts = match.strip().split()
        while parts and parts[0].lower() in ENTITY_STOP_WORDS:
            parts = parts[1:]
        while parts and parts[-1].lower() in ENTITY_STOP_WORDS:
            parts = parts[:-1]
        if not parts:
            continue
        candidate = " ".join(parts)
        lower = candidate.lower()
        if lower in ENTITY_STOP_WORDS:
            continue
        if any(part.lower() in ENTITY_STOP_WORDS for part in candidate.split()):
            if len(candidate.split()) == 1:
                continue
        if len(candidate) <= 2:
            continue
        entities.append(candidate)
    return sorted(set(entities))


def extract_events_from_speech(
    segments: list[SpeechSegment],
    media_id: str = "",
    merge_window_s: float = 5.0,
) -> list[AtomicEvent]:
    """Extract atomic events from speech segments.

    Groups nearby speech into coherent events and classifies them.

    Args:
        segments: Speech segments from filtering layer.
        media_id: ID of the source media asset.
        merge_window_s: Maximum gap (seconds) to merge adjacent segments.
    """
    if not segments:
        return []

    # Group nearby segments into event windows
    groups: list[list[SpeechSegment]] = []
    current_group: list[SpeechSegment] = [segments[0]]

    current_word_count = len(current_group[0].text.split())

    for seg in segments[1:]:
        gap = seg.start_s - current_group[-1].end_s
        projected_duration = seg.end_s - current_group[0].start_s
        seg_word_count = len(seg.text.split())
        would_exceed_limits = (
            projected_duration > MAX_EVENT_DURATION_S or
            len(current_group) >= MAX_EVENT_SEGMENTS or
            (current_word_count + seg_word_count) > MAX_EVENT_WORDS
        )
        if gap <= merge_window_s and not would_exceed_limits:
            current_group.append(seg)
            current_word_count += seg_word_count
        else:
            groups.append(current_group)
            current_group = [seg]
            current_word_count = seg_word_count
    groups.append(current_group)

    events = []
    for group in groups:
        combined_text = " ".join(seg.text for seg in group).strip()
        if not combined_text:
            continue

        speakers = list({seg.speaker for seg in group if seg.speaker})
        all_tags = []
        for seg in group:
            all_tags.extend(seg.salience_tags)
        avg_confidence = sum(seg.confidence for seg in group) / len(group) if group else 0.0

        source_refs = [f"speech_{seg.start_s:.2f}" for seg in group]
        if media_id:
            source_refs = [f"{media_id}:{ref}" for ref in source_refs]

        event = AtomicEvent(
            time_start=group[0].start_s,
            time_end=group[-1].end_s,
            speakers=speakers,
            text_evidence=combined_text,
            event_type=_classify_event_type(combined_text),
            confidence=avg_confidence,
            source_refs=source_refs,
            salience_tags=list(set(all_tags)),
            metadata={
                "entities": _extract_entities(combined_text),
                "word_count": len(combined_text.split()),
                "segment_count": len(group),
            },
        )
        events.append(event)

    return events


def extract_events_from_scenes(
    scenes: list[SceneSegment],
    media_id: str = "",
) -> list[AtomicEvent]:
    """Extract events from video scene changes."""
    events = []
    for scene in scenes:
        labels = scene.labels or []
        description_parts = []
        if labels:
            description_parts.append(f"Visual: {', '.join(labels)}")
        if scene.ocr_text:
            description_parts.append(f"On-screen text: {scene.ocr_text}")
        if not description_parts:
            description_parts.append("Scene change detected")

        source_refs = [f"scene_{scene.start_s:.2f}"]
        if scene.keyframe_path:
            source_refs.append(f"keyframe:{scene.keyframe_path}")
        if media_id:
            source_refs = [f"{media_id}:{ref}" for ref in source_refs]

        events.append(AtomicEvent(
            time_start=scene.start_s,
            time_end=scene.end_s,
            visual_entities=labels,
            text_evidence=" | ".join(description_parts),
            event_type=EventType.SCENE_CHANGE if scene.scene_score > 0 else EventType.OBSERVATION,
            confidence=min(1.0, scene.scene_score / 0.5) if scene.scene_score > 0 else 0.5,
            source_refs=source_refs,
            metadata={
                "scene_score": scene.scene_score,
                "motion_score": scene.motion_score,
                "sharpness": scene.sharpness_score,
                "ocr_text": scene.ocr_text,
            },
        ))

    return events


def merge_events(
    speech_events: list[AtomicEvent],
    scene_events: list[AtomicEvent],
) -> list[AtomicEvent]:
    """Merge speech and scene events into a unified timeline.

    Events are sorted by start time. Overlapping speech and scene events
    are cross-referenced but not merged to preserve evidence separation.
    """
    all_events = speech_events + scene_events
    all_events.sort(key=lambda e: (e.time_start, e.time_end))

    # Cross-reference overlapping events
    for i, evt in enumerate(all_events):
        for j, other in enumerate(all_events):
            if i == j:
                continue
            # Check temporal overlap
            if evt.time_start <= other.time_end and evt.time_end >= other.time_start:
                if other.event_id not in evt.source_refs:
                    evt.source_refs.append(f"xref:{other.event_id}")

    return all_events
