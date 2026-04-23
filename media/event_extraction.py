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
from media.text_cleanup import (
    clean_question,
    distill_statement,
    extract_inline_topic_terms,
    is_noise_phrase,
    normalize_whitespace,
    split_sentences,
    strip_leading_filler,
)

logger = logging.getLogger("archivist.media.events")

MAX_EVENT_DURATION_S = max(15.0, float(os.getenv("MEDIA_MAX_EVENT_DURATION_S", "90")))
MAX_EVENT_SEGMENTS = max(3, int(os.getenv("MEDIA_MAX_EVENT_SEGMENTS", "40")))
MAX_EVENT_WORDS = max(40, int(os.getenv("MEDIA_MAX_EVENT_WORDS", "220")))

ENTITY_STOP_WORDS = {
    "a", "actually", "again", "all", "also", "amazing", "and", "another", "any", "anything",
    "appreciate", "along", "are", "asset", "basically", "because", "best", "better", "brief", "but", "bye", "can", "chatgpt",
    "classification", "classifier", "cool", "course", "data", "december", "demo",
    "correct", "cause", "document", "documents", "done", "does", "easy", "energy", "even", "exactly", "extraction", "first",
    "forget", "get", "going", "great", "guys", "have", "hello", "here", "hey", "hopefully",
    "how", "however", "i", "idea", "if", "immediately", "in", "it", "january", "jump",
    "just", "kind", "last", "let", "like", "look", "makes", "manual", "maybe", "meeting",
    "more", "mosfet", "my", "next", "no", "not", "now",
    "okay", "our", "over", "pay", "pay stub", "pay stubs", "pdf", "please", "product", "prompt",
    "prompts", "quality", "really", "right", "same", "second", "see", "since", "slack", "snacks",
    "so", "sorry", "sounds", "summary", "sure", "system", "talk", "thank", "thanks", "that", "the", "then", "there",
    "these", "things", "this", "those", "transcript", "true", "unable", "up", "use", "vector", "well", "what",
    "when", "where", "which", "who", "why", "with", "worked", "workflow", "yeah", "yep", "yes", "you", "your",
    "was", "were", "would",
}


def _source_ref(media_id: str, base_ref: str) -> str:
    return f"{media_id}:{base_ref}" if media_id else base_ref


def _segment_source_ref(media_id: str, segment: SpeechSegment) -> str:
    return _source_ref(media_id, f"speech_{segment.start_s:.2f}")


def _aggregate_word_timestamps(group: list[SpeechSegment]) -> list[dict]:
    words: list[dict] = []
    for segment in group:
        for word in segment.word_timestamps or []:
            if not isinstance(word, dict):
                continue
            words.append({
                "start": word.get("start"),
                "end": word.get("end"),
                "word": word.get("word") or word.get("text"),
                "confidence": word.get("confidence"),
                "speaker": segment.speaker,
            })
    return words


def _salient_sentences(text: str, limit: int = 2) -> list[str]:
    sentences: list[str] = []
    for sentence in split_sentences(text):
        candidate = strip_leading_filler(sentence).strip(" ,.;:-")
        if not candidate or is_noise_phrase(candidate):
            continue
        sentences.append(candidate)
        if len(sentences) >= limit:
            break
    if sentences:
        return sentences
    fallback = distill_statement(text, limit=180)
    if fallback and not is_noise_phrase(fallback):
        return [fallback]
    return []


def _speech_event_metadata(group: list[SpeechSegment], combined_text: str, media_id: str) -> dict:
    normalized_text = normalize_whitespace(combined_text)
    topic_terms = extract_inline_topic_terms(combined_text, limit=6)
    summary_text = " ".join(_salient_sentences(combined_text, limit=2)).strip()
    brief_text = distill_statement(summary_text or combined_text, limit=180)
    word_timestamps = _aggregate_word_timestamps(group)
    speaker_turns = [
        {
            "speaker": segment.speaker,
            "start_s": segment.start_s,
            "end_s": segment.end_s,
            "source_ref": _segment_source_ref(media_id, segment),
        }
        for segment in group
    ]
    evidence_refs = [
        {
            "kind": "speech_segment",
            "start_s": segment.start_s,
            "end_s": segment.end_s,
            "speaker": segment.speaker,
            "source_ref": _segment_source_ref(media_id, segment),
            "word_timestamps_available": bool(segment.word_timestamps),
        }
        for segment in group
    ]
    return {
        "entities": _extract_entities(combined_text),
        "brief": brief_text,
        "summary_text": summary_text,
        "topic_terms": topic_terms,
        "question_text": clean_question(combined_text),
        "word_count": len(normalized_text.split()),
        "segment_count": len(group),
        "raw_text": combined_text,
        "cleaned_text": normalized_text,
        "transcript_span": {
            "start_s": group[0].start_s,
            "end_s": group[-1].end_s,
        },
        "speaker_turns": speaker_turns,
        "word_timestamps": word_timestamps,
        "evidence_refs": evidence_refs,
    }


def _scene_event_metadata(scene: SceneSegment, media_id: str) -> dict:
    frame_ref = _source_ref(media_id, f"keyframe:{scene.keyframe_path}") if scene.keyframe_path else ""
    ocr_lines = [line.strip() for line in str(scene.ocr_text or "").splitlines() if line.strip()]
    evidence_refs = [
        {
            "kind": "scene_segment",
            "start_s": scene.start_s,
            "end_s": scene.end_s,
            "source_ref": _source_ref(media_id, f"scene_{scene.start_s:.2f}"),
        }
    ]
    if frame_ref:
        evidence_refs.append({
            "kind": "keyframe",
            "start_s": scene.start_s,
            "end_s": scene.end_s,
            "source_ref": frame_ref,
        })
    visual_summary = ", ".join(scene.labels) if scene.labels else ""
    if ocr_lines:
        visual_summary = f"{visual_summary} | OCR: {' '.join(ocr_lines)}".strip(" |")
    return {
        "scene_score": scene.scene_score,
        "motion_score": scene.motion_score,
        "sharpness": scene.sharpness_score,
        "ocr_text": scene.ocr_text,
        "ocr_lines": ocr_lines,
        "visual_summary": visual_summary or "Scene change detected",
        "representative_frame_refs": [frame_ref] if frame_ref else [],
        "evidence_refs": evidence_refs,
    }


def _classify_event_type(text: str) -> EventType:
    """Classify the type of event from its text content.

    Uses keyword heuristics. A proper implementation would use an LLM
    for nuanced classification.
    """
    clean = normalize_whitespace(text)
    salient_sentences = _salient_sentences(clean, limit=2)
    lead_text = " ".join(salient_sentences).strip() or clean
    lower = lead_text.lower()
    sentences = [segment.lower() for segment in salient_sentences] if salient_sentences else [lower]
    first_sentence = sentences[0] if sentences else lower

    if is_noise_phrase(lead_text):
        return EventType.SPEECH
    if re.search(r"\b(check one two|can you hear me|hear me right|come in muted)\b", lower):
        return EventType.SPEECH

    if clean_question(lead_text):
        if "?" in first_sentence or re.match(r"^(who|what|when|where|why|how|is|are|do|does|did|can|could|would|should|will)\b", first_sentence):
            return EventType.QUESTION

    decision_patterns = [
        r"\bdecid(?:e|ed|ing)\b",
        r"\bagree(?:d|ing)?\b",
        r"\bapproved?\b",
        r"\blet's\b",
        r"\bplan is to\b",
        r"\bwe should\b",
    ]
    if any(re.search(pattern, lower) for pattern in decision_patterns):
        return EventType.DECISION

    action_patterns = [
        r"\b(?:i|we|he|she|they)\s+(?:went|made|created|built|fixed|moved|deployed|pushed|started|stopped|checked|reviewed)\b",
        r"\b(?:i|we)\s+(?:check|review|look into|dig into|fix|build|deploy|push|move|start|stop|share|send|reach out|follow up|update|document)\b",
        r"\b(?:i(?:'ll| will)|we(?:'ll| will)|we need to|i need to)\b",
        r"\bfollow up\b",
    ]
    if any(re.search(pattern, lower) for pattern in action_patterns):
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
    entities: list[str] = []
    normalized = normalize_whitespace(text)
    for acronym in re.findall(r"\b[A-Z]{2,6}\b", normalized):
        if acronym.lower() not in ENTITY_STOP_WORDS and acronym not in entities:
            entities.append(acronym)

    for match in re.finditer(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b", normalized):
        original_candidate = match.group(1).strip()
        candidate = original_candidate
        parts = candidate.split()
        trimmed_leading = False
        while parts and parts[0].lower() in ENTITY_STOP_WORDS:
            parts = parts[1:]
            trimmed_leading = True
        while parts and parts[-1].lower() in ENTITY_STOP_WORDS:
            parts = parts[:-1]
        if not parts:
            continue
        candidate = " ".join(parts).strip()
        lower = candidate.lower()
        if lower in ENTITY_STOP_WORDS:
            continue
        if any(part.lower() in ENTITY_STOP_WORDS for part in candidate.split()) and len(candidate.split()) == 1:
            continue
        if len(candidate) <= 2:
            continue
        left_context = normalized[:match.start()].rstrip()
        right_context = normalized[match.end():].lstrip()
        sentence_start = not left_context or left_context.endswith((".", "?", "!", ":"))
        if sentence_start and len(candidate.split()) == 1 and not trimmed_leading:
            next_word = right_context.split(" ", 1)[0].strip(" ,.;:!?-").lower()
            sentence_start_verbs = {"said", "asked", "joined", "met", "reviewed", "walked", "shared", "confirmed"}
            if not right_context.startswith((",", ":")) and next_word not in sentence_start_verbs:
                continue
        if candidate not in entities:
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

        source_refs = [_segment_source_ref(media_id, seg) for seg in group]

        event = AtomicEvent(
            time_start=group[0].start_s,
            time_end=group[-1].end_s,
            speakers=speakers,
            text_evidence=combined_text,
            event_type=_classify_event_type(combined_text),
            confidence=avg_confidence,
            source_refs=source_refs,
            salience_tags=list(set(all_tags)),
            metadata=_speech_event_metadata(group, combined_text, media_id),
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

        source_refs = [_source_ref(media_id, f"scene_{scene.start_s:.2f}")]
        if scene.keyframe_path:
            source_refs.append(_source_ref(media_id, f"keyframe:{scene.keyframe_path}"))

        events.append(AtomicEvent(
            time_start=scene.start_s,
            time_end=scene.end_s,
            visual_entities=labels,
            text_evidence=" | ".join(description_parts),
            event_type=EventType.SCENE_CHANGE if scene.scene_score > 0 else EventType.OBSERVATION,
            confidence=min(1.0, scene.scene_score / 0.5) if scene.scene_score > 0 else 0.5,
            source_refs=source_refs,
            metadata=_scene_event_metadata(scene, media_id),
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

    # Cross-reference overlapping events while preserving each modality's
    # evidence separately. The overlap links act as lightweight cross-modal
    # windows for downstream retrieval and summarization.
    for i, evt in enumerate(all_events):
        for j, other in enumerate(all_events):
            if i == j:
                continue
            # Check temporal overlap
            if evt.time_start <= other.time_end and evt.time_end >= other.time_start:
                if other.event_id not in evt.source_refs:
                    evt.source_refs.append(f"xref:{other.event_id}")
                evt.metadata.setdefault("cross_modal_refs", [])
                if other.event_id not in evt.metadata["cross_modal_refs"]:
                    evt.metadata["cross_modal_refs"].append(other.event_id)

    return all_events
