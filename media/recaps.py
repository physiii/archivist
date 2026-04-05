"""L3: Local recap layer - build step-by-step accounts from atomic events.

Groups events into meaningful windows (scenes, conversation turns, chapters)
and generates plain-language recaps with entity tracking and causal links.
"""

from __future__ import annotations

import logging
from typing import Optional

from media.models import AtomicEvent, EventType, LocalRecap

logger = logging.getLogger("archivist.media.recaps")


def _clip_text(text: str, limit: int = 220) -> str:
    clean = " ".join((text or "").split()).strip()
    if len(clean) <= limit:
        return clean
    clipped = clean[:limit].rsplit(" ", 1)[0].strip()
    return f"{clipped}..."

# ── Prompts for LLM-based recap generation ──────────────────────────────

RECAP_SYSTEM_PROMPT = """You are a precise evidence analyst creating step-by-step accounts from timestamped events.

Rules:
1. Preserve chronological order within each group
2. Reference specific timestamps when citing evidence
3. Distinguish observed facts from inferences - label inferences explicitly
4. Note speakers by name/label when available
5. Flag contradictions, uncertainties, or gaps in the record
6. Keep language neutral and factual
7. Mark emotional tone only when clearly evidenced (tone of voice, word choice)
8. Note unresolved questions that downstream analysis should investigate
9. Preserve filler, hesitation, and uncertainty markers - they carry meaning about intent and confidence
10. Cross-reference visual and audio evidence when both exist"""

RECAP_USER_PROMPT_TEMPLATE = """Create a detailed step-by-step recap of this segment.

## Context
Group type: {group_type}
Time range: {time_start:.1f}s - {time_end:.1f}s
Event count: {event_count}

## Events (chronological)
{events_text}

## Instructions
Produce a structured recap with:
- **Summary**: 1-2 sentence overview of what happened
- **Step-by-step account**: Chronological walkthrough with timestamps
- **Key entities**: People, places, objects, concepts mentioned
- **Unresolved questions**: Anything unclear, contradictory, or requiring follow-up
- **Emotional tone**: Only if clearly evidenced (otherwise state "neutral/unclear")
- **Causal links**: Any cause-effect relationships observed

Adapt your detail level to the density and significance of the events.
For routine/low-salience content, be brief. For critical moments, be thorough."""


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

        lines.append(f"{timestamp}{speakers_str}{type_str}{confidence_str}{tags_str}")
        lines.append(f"  {evt.text_evidence}")
        if evt.visual_entities:
            lines.append(f"  Visual: {', '.join(evt.visual_entities)}")
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
    if not recap_text:
        event_type_counts: dict[str, int] = {}
        for evt in events:
            key = evt.event_type.value if hasattr(evt.event_type, "value") else str(evt.event_type)
            event_type_counts[key] = event_type_counts.get(key, 0) + 1

        dominant_types = ", ".join(
            f"{kind} x{count}"
            for kind, count in sorted(event_type_counts.items(), key=lambda item: (-item[1], item[0]))[:3]
        )
        summary_bits = [f"{len(events)} events"]
        if dominant_types:
            summary_bits.append(dominant_types)
        if all_entities:
            summary_bits.append(f"entities: {', '.join(sorted(all_entities)[:6])}")

        lines = [f"Summary: {' | '.join(summary_bits)}", "", "Timeline:"]
        preview_limit = 8
        for evt in events[:preview_limit]:
            timestamp = f"[{evt.time_start:.1f}s]"
            speakers = f" {', '.join(evt.speakers)}:" if evt.speakers else ""
            type_label = evt.event_type.value if hasattr(evt.event_type, "value") else str(evt.event_type)
            lines.append(f"{timestamp}{speakers} [{type_label}] {_clip_text(evt.text_evidence)}")
        if len(events) > preview_limit:
            lines.append(f"... {len(events) - preview_limit} additional events in this window.")
        recap_text = "\n".join(lines)

    # Detect questions in events
    questions = [
        evt.text_evidence for evt in events
        if evt.event_type == EventType.QUESTION
    ]

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
        salient_entities=sorted(all_entities),
        unresolved_questions=questions,
        causal_links=causal,
        event_ids=[evt.event_id for evt in events],
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
