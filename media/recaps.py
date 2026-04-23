"""L3: Local recap layer - build step-by-step accounts from atomic events.

Groups events into meaningful windows (scenes, conversation turns, chapters)
and generates plain-language recaps with entity tracking and causal links.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from media.models import AtomicEvent, EventType, LocalRecap
from media.text_cleanup import (
    clean_question,
    distill_statement,
    extract_inline_topic_terms,
    extract_topic_phrases,
    is_generic_topic_phrase,
    is_noise_phrase,
    is_weak_topic_phrase,
    lexical_tokens,
    strip_summary_boilerplate,
)

logger = logging.getLogger("archivist.media.recaps")


def _clip_text(text: str, limit: int = 220) -> str:
    clean = " ".join((text or "").split()).strip()
    if len(clean) <= limit:
        return clean
    clipped = clean[:limit].rsplit(" ", 1)[0].strip()
    return f"{clipped}..."


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        key = value.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        ordered.append(value.strip())
    return ordered


def _question_is_resolved_in_event(question: str, event_text: str) -> bool:
    question_key = question.strip().rstrip("?!.").lower()
    event_lower = event_text.lower()
    idx = event_lower.find(question_key)
    if idx == -1:
        return False
    remainder = event_lower[idx + len(question_key):].strip(" ?!.,;:-")
    if len(lexical_tokens(remainder)) < 8:
        return False
    answer_markers = (
        "yeah", "yep", "yes", "no", "that's", "that is", "it is", "it's",
        "we", "i", "there", "correct", "worked on", "i think", "we should",
    )
    return any(marker in remainder for marker in answer_markers)


def _extract_unresolved_question(event: AtomicEvent) -> str:
    question = str(event.metadata.get("question_text") or "").strip() or clean_question(event.text_evidence)
    if not question or is_noise_phrase(question):
        return ""
    tokens = lexical_tokens(question)
    if len(tokens) < 4:
        return ""
    status_check_prefixes = (
        "what's up", "whats up", "who was that", "any updates", "are those on",
        "anything else", "okay cool",
    )
    lowered = question.lower().strip()
    if any(lowered.startswith(prefix) for prefix in status_check_prefixes) and len(tokens) < 9:
        return ""
    if _question_is_resolved_in_event(question, event.text_evidence):
        return ""
    return question


def _question_followup_brief(event: AtomicEvent, question_text: str) -> str:
    lowered = question_text.lower().strip(" ?!.,;:-")
    status_check_prefixes = (
        "who was that",
        "what was that",
        "any updates",
    )
    if not any(lowered.startswith(prefix) for prefix in status_check_prefixes):
        return ""

    text = str(event.text_evidence or "")
    remainder = ""
    if "?" in text:
        remainder = text.rsplit("?", 1)[1].strip()
    if not remainder:
        return ""
    remainder = distill_statement(remainder, limit=180)
    if not remainder or is_noise_phrase(remainder):
        return ""
    return remainder


def _event_brief_for_ledger(event: AtomicEvent) -> str:
    question_text = str(event.metadata.get("question_text") or "").strip() or clean_question(event.text_evidence)
    if event.event_type == EventType.QUESTION and question_text and not is_noise_phrase(question_text):
        return _question_followup_brief(event, question_text) or question_text
    return str(event.metadata.get("brief") or distill_statement(event.text_evidence, limit=220) or _clip_text(event.text_evidence))


def _event_salience_score(event: AtomicEvent) -> int:
    score = 1
    if event.event_type == EventType.DECISION:
        score += 4
    elif event.event_type == EventType.ACTION:
        score += 3
    elif event.event_type == EventType.QUESTION:
        score += 2
    elif event.event_type == EventType.OBSERVATION:
        score += 1
    score += len(event.metadata.get("cross_modal_refs", []))
    if event.metadata.get("ocr_lines"):
        score += 1
    return score


def _format_topic_list(values: list[str]) -> str:
    if not values:
        return ""
    if len(values) == 1:
        return values[0]
    if len(values) == 2:
        return f"{values[0]} and {values[1]}"
    return f"{', '.join(values[:-1])}, and {values[-1]}"


def _dedupe_topic_terms(values: list[str], limit: int = 4) -> list[str]:
    seen: set[str] = set()
    cleaned: list[str] = []
    for value in values:
        candidate = strip_summary_boilerplate(str(value or "")).strip(" .")
        if not candidate or is_weak_topic_phrase(candidate):
            continue
        key = candidate.lower().strip(" ?!.,;:-")
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(candidate)
        if len(cleaned) >= limit:
            break
    return cleaned


def _has_followup_action(events: list[AtomicEvent]) -> bool:
    for event in events:
        if event.event_type != EventType.ACTION:
            continue
        text = str(event.metadata.get("brief") or event.text_evidence or "").lower()
        if re.search(r"\b(?:i(?:'ll| will)|we(?:'ll| will)|let me|follow up|check the|review the|look into|dig into)\b", text):
            return True
    return False


def _summary_from_topic_terms(topic_text: str, events: list[AtomicEvent]) -> str:
    dominant_types = {
        evt.event_type.value if hasattr(evt.event_type, "value") else str(evt.event_type)
        for evt in events
    }
    if {"decision", "question"} <= dominant_types:
        return f"Discussion of {topic_text}, including decisions and open questions."
    if "decision" in dominant_types and _has_followup_action(events):
        return f"Discussion of {topic_text}, including decisions and follow-up work."
    if "decision" in dominant_types:
        return f"Discussion of {topic_text}, with concrete decisions."
    if "question" in dominant_types:
        return f"Discussion of {topic_text}, with open questions."
    return f"Discussion of {topic_text}."


def _window_summary_from_events(events: list[AtomicEvent], all_entities: set[str]) -> str:
    ranked_events = sorted(events, key=lambda evt: (-_event_salience_score(evt), evt.time_start))
    briefs = [
        strip_summary_boilerplate(_event_brief_for_ledger(evt)).strip(" .")
        for evt in ranked_events
    ]
    briefs = [brief for brief in briefs if brief and not is_noise_phrase(brief) and not is_weak_topic_phrase(brief)]

    inline_terms: list[str] = []
    for evt in events:
        inline_terms.extend(str(term) for term in evt.metadata.get("topic_terms", []) or [])
        inline_terms.extend(extract_inline_topic_terms(str(evt.metadata.get("brief") or evt.text_evidence), limit=4))

    topic_terms = [
        term
        for term in extract_topic_phrases(
            [str(evt.metadata.get("brief") or evt.text_evidence) for evt in events],
            limit=4,
        )
        if term and not is_weak_topic_phrase(term) and not is_generic_topic_phrase(term)
    ]
    fallback_topic_entities = [
        entity
        for entity in sorted(all_entities)
        if entity and not is_weak_topic_phrase(entity) and not is_generic_topic_phrase(entity) and (entity.isupper() or len(entity.split()) > 1)
    ]

    topic_text = _format_topic_list(_dedupe_topic_terms([*topic_terms, *inline_terms, *fallback_topic_entities], limit=3))
    if topic_text:
        return _summary_from_topic_terms(topic_text, events)

    if briefs:
        lead = briefs[0].rstrip(".")
        if len(lead.split()) > 3 and not is_weak_topic_phrase(lead):
            return lead if lead.endswith(".") else f"{lead}."

    combined_lower = " ".join(str(evt.text_evidence or "") for evt in events).lower()
    if re.search(r"\b(good morning|hello|glad we got a chance to talk|background|bio version)\b", combined_lower):
        return "Introductions and background."
    return "Main developments in this window."


def _ledger_entry(event: AtomicEvent) -> dict:
    return {
        "event_id": event.event_id,
        "time_start": event.time_start,
        "time_end": event.time_end,
        "event_type": event.event_type.value if hasattr(event.event_type, "value") else str(event.event_type),
        "speakers": event.speakers,
        "summary": _event_brief_for_ledger(event),
        "source_refs": list(event.source_refs),
        "evidence_refs": list(event.metadata.get("evidence_refs", [])),
        "transcript_span": event.metadata.get("transcript_span"),
        "cross_modal_refs": list(event.metadata.get("cross_modal_refs", [])),
        "representative_frame_refs": list(event.metadata.get("representative_frame_refs", [])),
        "ocr_lines": list(event.metadata.get("ocr_lines", [])),
    }


def _summary_ref(event: AtomicEvent) -> dict:
    return {
        "event_id": event.event_id,
        "time_start": event.time_start,
        "time_end": event.time_end,
        "event_type": event.event_type.value if hasattr(event.event_type, "value") else str(event.event_type),
        "summary": _event_brief_for_ledger(event),
        "source_refs": list(event.source_refs),
        "evidence_refs": list(event.metadata.get("evidence_refs", [])),
    }

# ── Prompts for LLM-based recap generation ──────────────────────────────

RECAP_SYSTEM_PROMPT = """You are a precise evidence analyst creating an inspectable step-by-step event ledger from timestamped events.

Rules:
1. Preserve chronological order within each group
2. Reference specific timestamps when citing evidence
3. Distinguish observed facts from inferences - label inferences explicitly
4. Note speakers by name/label when available
5. Flag contradictions, uncertainties, or gaps in the record
6. Keep language neutral and factual
7. Mark emotional tone only when clearly evidenced (tone of voice, word choice)
8. Note unresolved questions that downstream analysis should investigate
9. Preserve filler, hesitation, and uncertainty markers only when they change meaning or confidence
10. Cross-reference visual and audio evidence when both exist
11. This layer is the near-complete walkthrough source, not the high-level contextual summary
12. Prefer atomic ledger entries over polished narrative prose
13. Keep provenance-rich cues when available: timestamps, speakers, OCR, frame references, transcript token timing"""

RECAP_USER_PROMPT_TEMPLATE = """Create a detailed step-by-step event ledger for this segment.

## Context
Group type: {group_type}
Time range: {time_start:.1f}s - {time_end:.1f}s
Event count: {event_count}

## Events (chronological)
{events_text}

## Instructions
Produce a structured recap with:
- **Window summary**: 1 sentence that names the main topic of the span
- **Event ledger**: Chronological bullets with timestamps, concise evidence-grounded descriptions, and event/source refs when available
- **Key entities**: People, places, objects, concepts mentioned
- **Unresolved questions**: Anything unclear, contradictory, or requiring follow-up
- **Emotional tone**: Only if clearly evidenced (otherwise state "neutral/unclear")
- **Causal links**: Any cause-effect relationships observed

Adapt your detail level to the density and significance of the events.
For routine content, stay compact. For important moments, stay complete and inspectable.
Preserve evidence anchors in the ledger whenever the input provides them.
Do not turn this layer into a high-level summary of the whole recording."""


# ── Event Grouping ──────────────────────────────────────────────────────


def group_events_by_time_window(
    events: list[AtomicEvent],
    window_s: float = 60.0,
    min_events: int = 1,
) -> list[list[AtomicEvent]]:
    """Group events into fixed-duration time windows."""
    if not events:
        return []

    groups: list[list[AtomicEvent]] = []
    current: list[AtomicEvent] = []
    window_start = events[0].time_start

    for event in events:
        if event.time_start - window_start > window_s and current:
            if len(current) >= min_events:
                groups.append(current)
            current = []
            window_start = event.time_start
        current.append(event)

    if current and len(current) >= min_events:
        groups.append(current)

    return groups


def group_events_by_scene(
    events: list[AtomicEvent],
    scene_boundaries: Optional[list[float]] = None,
) -> list[list[AtomicEvent]]:
    """Group events by scene boundaries.

    If no scene boundaries provided, falls back to conversation-turn grouping.
    """
    if not events:
        return []

    if not scene_boundaries:
        # Fall back to gap-based grouping (> 10s silence = new group)
        return group_events_by_gap(events, max_gap_s=10.0)

    boundaries = sorted(set([0.0] + scene_boundaries))
    groups: list[list[AtomicEvent]] = [[] for _ in range(len(boundaries))]

    for event in events:
        # Find which scene this event belongs to
        scene_idx = 0
        for i, boundary in enumerate(boundaries):
            if event.time_start >= boundary:
                scene_idx = i
        if scene_idx < len(groups):
            groups[scene_idx].append(event)

    return [g for g in groups if g]


def group_events_by_gap(
    events: list[AtomicEvent],
    max_gap_s: float = 10.0,
) -> list[list[AtomicEvent]]:
    """Group events by gaps in the timeline."""
    if not events:
        return []

    groups: list[list[AtomicEvent]] = []
    current: list[AtomicEvent] = [events[0]]

    for event in events[1:]:
        gap = event.time_start - current[-1].time_end
        if gap > max_gap_s:
            groups.append(current)
            current = []
        current.append(event)

    if current:
        groups.append(current)

    return groups


# ── Recap Generation ────────────────────────────────────────────────────


def _format_events_for_prompt(events: list[AtomicEvent]) -> str:
    """Format events into a text block for LLM consumption."""
    lines = []
    for evt in events:
        timestamp = f"[{evt.time_start:.1f}s - {evt.time_end:.1f}s]"
        speakers_str = f" ({', '.join(evt.speakers)})" if evt.speakers else ""
        type_str = f" [{evt.event_type.value}]" if evt.event_type != EventType.UNKNOWN else ""
        confidence_str = f" (conf: {evt.confidence:.0%})" if evt.confidence < 0.8 else ""
        tags_str = ""
        if evt.salience_tags:
            tags_str = f" [tags: {', '.join(t.value for t in evt.salience_tags)}]"

        lines.append(f"{timestamp} {evt.event_id}{speakers_str}{type_str}{confidence_str}{tags_str}".strip())
        lines.append(f"  Text: {evt.text_evidence}")
        if evt.visual_entities:
            lines.append(f"  Visual: {', '.join(evt.visual_entities)}")
        transcript_span = evt.metadata.get("transcript_span")
        if isinstance(transcript_span, dict) and transcript_span.get("start_s") is not None:
            lines.append(
                "  Transcript span: "
                f"{float(transcript_span.get('start_s', 0.0)):.1f}s - {float(transcript_span.get('end_s', 0.0)):.1f}s"
            )
        if evt.metadata.get("ocr_lines"):
            lines.append(f"  OCR: {' | '.join(str(line) for line in evt.metadata.get('ocr_lines', [])[:4])}")
        evidence_refs = evt.metadata.get("evidence_refs", [])
        if evidence_refs:
            rendered_refs = []
            for ref in evidence_refs[:4]:
                if not isinstance(ref, dict):
                    continue
                ref_kind = str(ref.get("kind") or "evidence")
                source_ref = str(ref.get("source_ref") or "").strip()
                if source_ref:
                    rendered_refs.append(f"{ref_kind}:{source_ref}")
            if rendered_refs:
                lines.append(f"  Evidence refs: {', '.join(rendered_refs)}")
        lines.append("")

    return "\n".join(lines).strip()


def build_recap_prompt(events: list[AtomicEvent], group_type: str = "segment") -> tuple[str, str]:
    """Build the system and user prompts for recap generation.

    Returns (system_prompt, user_prompt) to be sent to an LLM.
    """
    events_text = _format_events_for_prompt(events)

    user_prompt = RECAP_USER_PROMPT_TEMPLATE.format(
        group_type=group_type,
        time_start=events[0].time_start if events else 0.0,
        time_end=events[-1].time_end if events else 0.0,
        event_count=len(events),
        events_text=events_text,
    )

    return RECAP_SYSTEM_PROMPT, user_prompt


def build_recap_from_events(
    events: list[AtomicEvent],
    group_type: str = "segment",
    recap_text: str = "",
) -> LocalRecap:
    """Build a LocalRecap from a group of events.

    If recap_text is provided (e.g. from LLM), uses it directly.
    Otherwise builds a mechanical recap from the events.
    """
    if not events:
        return LocalRecap(group_type=group_type)

    # Collect all entities
    all_entities = set()
    for evt in events:
        all_entities.update(evt.metadata.get("entities", []))
        all_entities.update(evt.visual_entities)

    # Build mechanical recap if no LLM text provided
    summary_text = ""
    if not recap_text:
        summary_text = _window_summary_from_events(events, all_entities)
        lines = [f"Window summary: {summary_text}", "", "Event ledger:"]
        preview_limit = 8
        for evt in events[:preview_limit]:
            timestamp = f"[{evt.time_start:.1f}s]"
            speakers = f" {', '.join(evt.speakers)}:" if evt.speakers else ""
            type_label = evt.event_type.value if hasattr(evt.event_type, "value") else str(evt.event_type)
            event_brief = _event_brief_for_ledger(evt)
            if not event_brief or is_noise_phrase(event_brief):
                continue
            lines.append(f"- {timestamp}{speakers} [{type_label}] {event_brief}")
        if len(events) > preview_limit:
            lines.append(f"- ... {len(events) - preview_limit} additional events in this window.")
        recap_text = "\n".join(lines)
    else:
        summary_text = ""
        for line in recap_text.splitlines():
            stripped = line.strip()
            if stripped.lower().startswith("window summary:"):
                summary_text = stripped.split(":", 1)[1].strip()
                break
        if not summary_text:
            summary_text = distill_statement(recap_text, limit=220)
        summary_text = strip_summary_boilerplate(summary_text) or summary_text

    ledger_entries = [
        entry
        for entry in (_ledger_entry(evt) for evt in events)
        if entry.get("summary")
    ]
    ranked_events = sorted(events, key=lambda evt: (-_event_salience_score(evt), evt.time_start))
    summary_refs = [_summary_ref(evt) for evt in ranked_events[:4]]

    # Detect questions in events
    questions = _dedupe_preserve_order([
        _extract_unresolved_question(evt)
        for evt in events
        if evt.event_type == EventType.QUESTION
    ])

    # Detect causal links (events referencing each other)
    causal = []
    for evt in events:
        xrefs = [ref for ref in evt.source_refs if ref.startswith("xref:")]
        if xrefs:
            causal.append(f"{evt.event_id} -> {', '.join(xrefs)}")

    return LocalRecap(
        group_type=group_type,
        time_start=events[0].time_start,
        time_end=events[-1].time_end,
        recap_text=recap_text,
        window_summary=summary_text,
        salient_entities=sorted(all_entities),
        unresolved_questions=questions,
        causal_links=causal,
        event_ids=[evt.event_id for evt in events],
        summary_refs=summary_refs,
        ledger_entries=ledger_entries,
        source_refs=[ref for evt in events for ref in evt.source_refs],
    )


def build_recaps(
    events: list[AtomicEvent],
    window_s: float = 60.0,
    group_type: str = "segment",
) -> list[LocalRecap]:
    """Build local recaps from events using time-window grouping.

    This is the default grouping strategy. For scene-based grouping,
    use group_events_by_scene + build_recap_from_events directly.
    """
    groups = group_events_by_time_window(events, window_s=window_s)
    return [build_recap_from_events(group, group_type=group_type) for group in groups]
