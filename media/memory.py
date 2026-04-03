"""L4: Contextual memory layer - build compressed working memory from recaps.

Creates a structured memory object that captures the essence of processed media
in a form optimized for downstream document generation and search.
"""

from __future__ import annotations

import logging
from collections import Counter
from typing import Optional

from media.models import ContextualMemory, LocalRecap

logger = logging.getLogger("archivist.media.memory")

# ── Prompts for LLM-based memory construction ───────────────────────────

MEMORY_SYSTEM_PROMPT = """You are building a compressed contextual memory from a series of local recaps of media content.

This memory is NOT a summary - it is structured working memory optimized for:
1. Answering questions about the content
2. Generating task-specific documents (reports, minutes, narratives)
3. Identifying what matters and what needs follow-up

Rules:
- Distinguish facts from inferences
- Preserve uncertainty and contradictions - they are valuable signals
- Track open loops (things mentioned but not resolved)
- Note risk/safety issues prominently
- Cross-reference evidence across recaps
- Adapt structure to the content type (meeting, incident, narrative, etc.)"""

MEMORY_USER_PROMPT_TEMPLATE = """Build a contextual memory from these {recap_count} recaps spanning {duration:.0f} seconds.

## Recaps (chronological)
{recaps_text}

## Produce structured memory with these fields:
- **Main actors**: Who appears and what role do they play?
- **Timeline anchors**: Key moments that structure the narrative (with timestamps)
- **Locations**: Where things happen
- **Open loops**: Things mentioned but unresolved
- **Inferred themes**: What is this content really about?
- **Risk/safety issues**: Anything concerning or requiring attention
- **Contradictions**: Conflicting information or inconsistencies
- **Notable evidence**: Specific quotes, frames, or data points worth preserving
- **Final takeaways**: The most important things to remember

Be concise but thorough. This memory will be used to generate documents later."""


# ── Memory Construction ─────────────────────────────────────────────────


def build_memory_prompt(recaps: list[LocalRecap], media_id: str = "") -> tuple[str, str]:
    """Build prompts for LLM-based memory construction.

    Returns (system_prompt, user_prompt).
    """
    recaps_text = _format_recaps_for_prompt(recaps)
    duration = (recaps[-1].time_end - recaps[0].time_start) if recaps else 0.0

    user_prompt = MEMORY_USER_PROMPT_TEMPLATE.format(
        recap_count=len(recaps),
        duration=duration,
        recaps_text=recaps_text,
    )

    return MEMORY_SYSTEM_PROMPT, user_prompt


def _format_recaps_for_prompt(recaps: list[LocalRecap]) -> str:
    """Format recaps into text for LLM consumption."""
    parts = []
    for i, recap in enumerate(recaps, 1):
        header = f"### Recap {i} [{recap.time_start:.1f}s - {recap.time_end:.1f}s] ({recap.group_type})"
        parts.append(header)
        parts.append(recap.recap_text)
        if recap.salient_entities:
            parts.append(f"Entities: {', '.join(recap.salient_entities)}")
        if recap.unresolved_questions:
            parts.append(f"Open questions: {'; '.join(recap.unresolved_questions)}")
        parts.append("")
    return "\n".join(parts).strip()


def build_memory_from_recaps(
    recaps: list[LocalRecap],
    media_id: str = "",
) -> ContextualMemory:
    """Build contextual memory from local recaps using heuristic extraction.

    For LLM-enhanced memory, use build_memory_prompt() to get prompts,
    send to LLM, and parse the structured response.
    """
    if not recaps:
        return ContextualMemory(media_id=media_id)

    # Aggregate entities across all recaps
    entity_counts: Counter = Counter()
    all_questions = []
    all_causal = []

    for recap in recaps:
        for entity in recap.salient_entities:
            entity_counts[entity] += 1
        all_questions.extend(recap.unresolved_questions)
        all_causal.extend(recap.causal_links)

    # Main actors: entities appearing in multiple recaps
    main_actors = [entity for entity, count in entity_counts.most_common(20) if count >= 2]
    if not main_actors:
        main_actors = [entity for entity, _ in entity_counts.most_common(5)]

    # Timeline anchors: first and last recap, plus any with significant events
    anchors = []
    if recaps:
        anchors.append({
            "time": recaps[0].time_start,
            "label": "Start",
            "recap_id": recaps[0].recap_id,
        })
        if len(recaps) > 2:
            mid = recaps[len(recaps) // 2]
            anchors.append({
                "time": mid.time_start,
                "label": "Midpoint",
                "recap_id": mid.recap_id,
            })
        anchors.append({
            "time": recaps[-1].time_end,
            "label": "End",
            "recap_id": recaps[-1].recap_id,
        })

    # Detect themes from recurring entity patterns
    themes = []
    for entity, count in entity_counts.most_common(10):
        if count >= max(2, len(recaps) // 4):
            themes.append(entity)

    return ContextualMemory(
        media_id=media_id,
        main_actors=main_actors,
        timeline_anchors=anchors,
        locations=[],
        open_loops=all_questions[:20],
        inferred_themes=themes,
        risk_safety_issues=[],
        contradictions=[],
        notable_evidence=[],
        final_takeaways=[],
        recap_ids=[r.recap_id for r in recaps],
    )
