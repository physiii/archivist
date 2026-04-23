"""L4: Contextual memory layer - build compressed working memory from recaps.

Creates a structured memory object that captures the essence of processed media
in a form optimized for downstream document generation and search.
"""

from __future__ import annotations

import logging
import re
from collections import Counter
from typing import Optional

from media.models import AtomicEvent, ContextualMemory, LocalRecap
from media.text_cleanup import (
    FILLER_WORDS,
    clean_question,
    distill_statement,
    extract_inline_topic_terms,
    extract_topic_phrases,
    is_generic_topic_phrase,
    is_weak_topic_phrase,
    strip_summary_boilerplate,
)

logger = logging.getLogger("archivist.media.memory")

MEMORY_ENTITY_STOP_TERMS = FILLER_WORDS | {
    "actually", "additional", "and", "are", "awesome", "blah", "but", "everybody",
    "control", "cursor", "database", "drive", "error", "file", "flash", "however",
    "fuck", "god", "good", "interesting", "never", "no", "none", "nope",
    "january", "february", "march", "april", "may", "june", "july", "august",
    "or", "otherwise", "proceed", "remember", "see", "september", "october", "november",
    "december", "obviously", "studio", "talk", "terminal", "the", "there", "they",
    "versus", "wait", "whereas", "window", "will", "yes",
}
MEMORY_NON_PERSON_TOKENS = {
    "app", "arm", "asic", "chip", "compiler", "control", "cursor", "database", "demo",
    "design", "document", "drive", "error", "file", "flash", "fpga", "host", "interface",
    "ip", "linux", "mac", "model", "network", "prototype", "server", "ssh", "studio",
    "terminal", "tunnel", "ui", "ux", "variant", "video", "vpn", "window", "workflow",
}

# ── Prompts for LLM-based memory construction ───────────────────────────

MEMORY_SYSTEM_PROMPT = """You are building a compressed contextual memory from a series of local recaps of media content.

This memory is NOT a walkthrough - it is a compressed contextual account optimized for:
1. Answering questions about the content
2. Generating task-specific documents (reports, minutes, narratives)
3. Identifying what matters and what needs follow-up

Rules:
- Distinguish facts from inferences
- Preserve uncertainty and contradictions - they are valuable signals
- Track open loops (things mentioned but not resolved)
- Note risk/safety issues prominently
- Cross-reference evidence across recaps
- Adapt structure to the content type (meeting, incident, narrative, etc.)
- Compress aggressively and avoid replaying the chronology
- Keep provenance whenever possible with timestamps, recap IDs, frame IDs, OCR spans, or other evidence anchors
- Separate factual record from interpretation
- Treat chronology as the canonical truth; this layer is a derived synthesis built on top of it
- Every high-level point should remain traceable back to recap IDs, event IDs, timestamps, or source refs"""

MEMORY_USER_PROMPT_TEMPLATE = """Build a contextual memory from these {recap_count} recaps spanning {duration:.0f} seconds.

## Recaps (chronological)
{recaps_text}

## Produce structured memory with these fields:
- **Context overview**: 2-4 sentences max; fast orientation, no chronological replay, with evidence anchors when possible
- **Main actors**: Who appears and what role do they play?
- **Timeline anchors**: Key moments that structure the narrative (with timestamps plus recap/event refs)
- **Locations**: Where things happen
- **Open loops**: Things mentioned but unresolved, with evidence refs
- **Inferred themes**: What is this content really about, with supporting recap/event refs
- **Risk/safety issues**: Anything concerning or requiring attention
- **Contradictions**: Conflicting information or inconsistencies
- **Notable evidence**: Specific quotes, frames, or data points worth preserving, each with evidence anchors
- **Final takeaways**: The most important things to remember, each with evidence anchors
- **Interpretive notes**: Optional derived interpretations kept separate from facts, each with confidence and evidence anchors

Be concise and selective. This memory is the compressed context layer that later documents will build on."""


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
        header = f"### Recap {i} / {recap.recap_id} [{recap.time_start:.1f}s - {recap.time_end:.1f}s] ({recap.group_type})"
        parts.append(header)
        if recap.window_summary:
            parts.append(f"Window summary: {recap.window_summary}")
        parts.append(recap.recap_text)
        if recap.salient_entities:
            parts.append(f"Entities: {', '.join(recap.salient_entities)}")
        if recap.unresolved_questions:
            parts.append(f"Open questions: {'; '.join(recap.unresolved_questions)}")
        if recap.summary_refs:
            rendered_refs = []
            for ref in recap.summary_refs[:4]:
                if not isinstance(ref, dict):
                    continue
                event_id = str(ref.get("event_id") or "").strip()
                time_start = ref.get("time_start")
                source_refs = ref.get("source_refs") or []
                anchor = f"{event_id}@{float(time_start):.1f}s" if event_id and isinstance(time_start, (int, float)) else event_id
                if anchor and source_refs:
                    rendered_refs.append(f"{anchor} -> {', '.join(str(item) for item in source_refs[:2])}")
                elif anchor:
                    rendered_refs.append(anchor)
            if rendered_refs:
                parts.append(f"Summary refs: {'; '.join(rendered_refs)}")
        parts.append("")
    return "\n".join(parts).strip()


def _normalize_memory_entity(entity: str) -> str:
    candidate = " ".join(str(entity or "").split()).strip(" ,.;:-")
    if len(candidate) <= 2 and not (candidate.isupper() and len(candidate) >= 2):
        return ""
    words = [word.strip(" ,.;:-").lower() for word in candidate.split() if word.strip(" ,.;:-")]
    if not words:
        return ""
    if len(words) == 1 and words[0] in MEMORY_ENTITY_STOP_TERMS:
        return ""
    if all(word in MEMORY_ENTITY_STOP_TERMS for word in words):
        return ""
    return candidate


def _is_person_like_entity(entity: str) -> bool:
    if entity.isupper():
        return False
    parts = entity.split()
    if not parts or len(parts) > 2:
        return False
    if len(parts) == 1 and parts[0].lower() in MEMORY_ENTITY_STOP_TERMS:
        return False
    if any(part.lower() in MEMORY_NON_PERSON_TOKENS for part in parts):
        return False
    if any(not part[:1].isupper() for part in parts):
        return False
    if any(part.lower() in MEMORY_ENTITY_STOP_TERMS for part in parts):
        return False
    return True


def _extract_vocative_names(events: list[AtomicEvent]) -> Counter:
    counts: Counter[str] = Counter()
    patterns = [
        re.compile(
            r"(?:^|[.!?]\s*)(?:hey|hi|hello|well|okay|ok|so|right|thanks|thank you)?\s*,?\s*([A-Za-z]{2,})(?=,\s*(?:can|could|would|will|did|do|please|let's|lets|thank|thanks))",
            re.IGNORECASE,
        ),
        re.compile(r"\bgood\s+(?:morning|afternoon|evening)\s+([A-Za-z]{2,})\b", re.IGNORECASE),
    ]
    for event in events:
        text = str(event.text_evidence or "")
        for pattern in patterns:
            for match in pattern.findall(text):
                normalized = _normalize_memory_entity(str(match).title())
                if normalized and _is_person_like_entity(normalized):
                    counts[normalized] += 1
    return counts


def _dedupe_text(values: list[str], limit: int = 20) -> list[str]:
    seen: set[str] = set()
    cleaned: list[str] = []
    for value in values:
        question = clean_question(value) or str(value or "").strip()
        key = question.lower().strip(" ?!.,;:-")
        if not key or key in seen:
            continue
        seen.add(key)
        cleaned.append(question)
        if len(cleaned) >= limit:
            break
    return cleaned


def _recap_summary_text(recap: LocalRecap) -> str:
    for line in recap.recap_text.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("window summary:"):
            return stripped.split(":", 1)[1].strip()
        if stripped.lower().startswith("summary:"):
            return stripped.split(":", 1)[1].strip()
    return distill_statement(recap.recap_text, limit=180)


def _event_brief(event: AtomicEvent) -> str:
    if event.event_type.value == "question":
        question_text = str(event.metadata.get("question_text") or "").strip()
        if question_text:
            return clean_question(question_text)
    return str(event.metadata.get("brief") or distill_statement(event.text_evidence, limit=180))


def _dedupe_refs(values: list[str], limit: int = 12) -> list[str]:
    seen: set[str] = set()
    refs: list[str] = []
    for value in values:
        ref = str(value or "").strip()
        if not ref or ref in seen:
            continue
        seen.add(ref)
        refs.append(ref)
        if len(refs) >= limit:
            break
    return refs


def _recap_source_refs(recap: LocalRecap, limit: int = 12) -> list[str]:
    refs: list[str] = [recap.recap_id] if recap.recap_id else []
    refs.extend(recap.source_refs)
    for ref in recap.summary_refs:
        if not isinstance(ref, dict):
            continue
        refs.extend(str(item) for item in ref.get("source_refs", []) or [])
        event_id = str(ref.get("event_id") or "").strip()
        if event_id:
            refs.append(event_id)
    return _dedupe_refs(refs, limit=limit)


def _build_context_overview(
    themes: list[str],
    main_actors: list[str],
    open_loops: list[str],
    risk_safety_issues: list[str],
    takeaway_points: list[dict],
) -> str:
    sentences: list[str] = []
    if themes:
        sentences.append(f"The recording focuses on {', '.join(themes[:4])}.")
    elif takeaway_points:
        sentences.append(distill_statement(str(takeaway_points[0].get('text') or ""), limit=180))
    if main_actors:
        actors = ", ".join(main_actors[:3])
        sentences.append(f"Main participants include {actors}.")
    status_parts: list[str] = []
    if open_loops:
        status_parts.append(f"{len(open_loops)} open question{'s' if len(open_loops) != 1 else ''}")
    if risk_safety_issues:
        status_parts.append(f"{len(risk_safety_issues)} risk item{'s' if len(risk_safety_issues) != 1 else ''}")
    if status_parts:
        sentences.append(f"The current state leaves {', '.join(status_parts)}.")
    return " ".join(sentence.strip() for sentence in sentences if sentence.strip()).strip()


def _clean_theme_candidate(value: str) -> str:
    candidate = strip_summary_boilerplate(value).strip(" ,.;:-")
    if not candidate or is_generic_topic_phrase(candidate) or is_weak_topic_phrase(candidate):
        return ""
    return candidate


def _anchor_records(recaps: list[LocalRecap], anchors: list[dict]) -> list[dict]:
    if not recaps:
        return []
    recap_by_id = {recap.recap_id: recap for recap in recaps}
    records: list[dict] = []
    for anchor in anchors:
        recap = recap_by_id.get(str(anchor.get("recap_id") or ""))
        records.append({
            **anchor,
            "source_refs": _recap_source_refs(recap) if recap else [],
        })
    return records


def build_memory_from_recaps(
    recaps: list[LocalRecap],
    media_id: str = "",
    events: Optional[list[AtomicEvent]] = None,
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
    speaker_counts: Counter[str] = Counter()
    actor_counts = _extract_vocative_names(events or [])
    event_entity_counts: Counter[str] = Counter()
    theme_source_texts: list[str] = []

    for recap in recaps:
        for entity in recap.salient_entities:
            normalized = _normalize_memory_entity(entity)
            if normalized:
                entity_counts[normalized] += 1
        all_questions.extend(recap.unresolved_questions)
        all_causal.extend(recap.causal_links)
        theme_source = _clean_theme_candidate(recap.window_summary or _recap_summary_text(recap))
        if theme_source:
            theme_source_texts.append(theme_source)

    for event in events or []:
        for speaker in event.speakers:
            normalized_speaker = _normalize_memory_entity(speaker)
            if normalized_speaker and _is_person_like_entity(normalized_speaker):
                speaker_counts[normalized_speaker] += 1
        for entity in event.metadata.get("entities", []):
            normalized = _normalize_memory_entity(entity)
            if normalized:
                event_entity_counts[normalized] += 1
        for term in event.metadata.get("topic_terms", []) or []:
            cleaned_term = _clean_theme_candidate(str(term or ""))
            if cleaned_term:
                theme_source_texts.append(cleaned_term)
        brief = _clean_theme_candidate(_event_brief(event))
        if brief:
            theme_source_texts.append(brief)
        for inline_term in extract_inline_topic_terms(str(event.text_evidence or ""), limit=4):
            cleaned_term = _clean_theme_candidate(inline_term)
            if cleaned_term:
                theme_source_texts.append(cleaned_term)

    actor_counts = Counter({
        entity: count
        for entity, count in actor_counts.items()
        if entity in event_entity_counts or count >= 2
    })

    combined_actor_counts = speaker_counts + actor_counts

    # Main actors: prefer explicit speakers and direct-address names, then
    # cautiously backfill from recurring person-like entities when the meeting
    # never names speakers aloud.
    main_actors = [entity for entity, count in combined_actor_counts.most_common(20) if count >= 1]
    if actor_counts and len(main_actors) < 3:
        recurring_people = [
            entity for entity, count in entity_counts.most_common(20)
            if count >= 2 and len(entity.split()) == 1 and _is_person_like_entity(entity) and entity not in main_actors
        ]
        for entity in recurring_people:
            if entity not in main_actors:
                main_actors.append(entity)
            if len(main_actors) >= 8:
                break
    if not main_actors and not events:
        main_actors = [entity for entity, count in entity_counts.most_common(20) if count >= 2 and _is_person_like_entity(entity)]

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

    # Detect themes from recap text and recurring non-actor entities.
    thematic_entities = [
        entity for entity, count in entity_counts.most_common(20)
        if count >= max(2, len(recaps) // 4) and entity not in main_actors and not _is_person_like_entity(entity)
    ]
    acronym_entities = [
        entity for entity, count in entity_counts.most_common(20)
        if entity.isupper() and len(entity) >= 2 and count >= 1 and entity not in main_actors
    ]
    themes = extract_topic_phrases(theme_source_texts, limit=6)
    for entity in thematic_entities:
        if entity not in themes and not is_generic_topic_phrase(entity) and not is_weak_topic_phrase(entity):
            themes.append(entity)
    for entity in acronym_entities:
        if entity not in themes and not is_generic_topic_phrase(entity) and not is_weak_topic_phrase(entity):
            themes.append(entity)
    cleaned_themes: list[str] = []
    for theme in themes:
        candidate = _clean_theme_candidate(theme)
        if not candidate or candidate in main_actors or candidate in cleaned_themes:
            continue
        cleaned_themes.append(candidate)
        if len(cleaned_themes) >= 6:
            break
    themes = cleaned_themes
    open_loops = _dedupe_text(all_questions, limit=20)
    takeaway_points: list[dict] = []
    takeaway_seen: set[str] = set()
    for recap in recaps:
        raw_text = recap.window_summary or _recap_summary_text(recap)
        text = strip_summary_boilerplate(raw_text).strip()
        if is_generic_topic_phrase(text) or is_weak_topic_phrase(text):
            text = ""
        if not text:
            if recap.summary_refs:
                text = str((recap.summary_refs[0] or {}).get("summary") or "").strip()
                if is_weak_topic_phrase(text):
                    text = ""
            if not text and recap.ledger_entries:
                text = str((recap.ledger_entries[0] or {}).get("summary") or "").strip()
                if is_weak_topic_phrase(text):
                    text = ""
        if not text and not is_generic_topic_phrase(raw_text):
            text = raw_text
        key = text.lower().strip(" ?!.,;:-")
        if not text or key in takeaway_seen:
            continue
        takeaway_seen.add(key)
        takeaway_points.append({
            "text": text,
            "recap_id": recap.recap_id,
            "time_start": recap.time_start,
            "time_end": recap.time_end,
            "source_refs": _recap_source_refs(recap),
            "summary_refs": recap.summary_refs[:4],
        })
        if len(takeaway_points) >= 6:
            break
    final_takeaways = [str(point.get("text") or "") for point in takeaway_points]

    notable_evidence_points: list[dict] = []
    evidence_seen: set[str] = set()
    for event in events or []:
        brief = _event_brief(event)
        if not brief or event.event_type.value not in {"decision", "action", "question", "observation"}:
            continue
        key = brief.lower().strip(" ?!.,;:-")
        if key in evidence_seen:
            continue
        evidence_seen.add(key)
        notable_evidence_points.append({
            "text": f"[{event.time_start:.1f}s] {brief}",
            "event_id": event.event_id,
            "event_type": event.event_type.value,
            "time_start": event.time_start,
            "time_end": event.time_end,
            "source_refs": _dedupe_refs(list(event.source_refs) + [event.event_id]),
            "evidence_refs": list(event.metadata.get("evidence_refs", [])),
            "transcript_span": event.metadata.get("transcript_span"),
            "representative_frame_refs": list(event.metadata.get("representative_frame_refs", [])),
        })
        if len(notable_evidence_points) >= 10:
            break
    notable_evidence = [str(point.get("text") or "") for point in notable_evidence_points]

    theme_points: list[dict] = []
    for theme in themes:
        matching_recaps = [
            recap
            for recap in recaps
            if theme.lower() in " ".join(
                [
                    recap.window_summary,
                    recap.recap_text,
                    " ".join(recap.salient_entities),
                ]
            ).lower()
        ]
        theme_points.append({
            "label": theme,
            "recap_ids": [recap.recap_id for recap in matching_recaps],
            "source_refs": _dedupe_refs([ref for recap in matching_recaps for ref in _recap_source_refs(recap)]),
            "time_ranges": [
                {"start_s": recap.time_start, "end_s": recap.time_end}
                for recap in matching_recaps[:6]
            ],
        })

    open_loop_points: list[dict] = []
    for question in open_loops:
        matching_recaps = [recap for recap in recaps if question in recap.unresolved_questions]
        open_loop_points.append({
            "text": question,
            "recap_ids": [recap.recap_id for recap in matching_recaps],
            "source_refs": _dedupe_refs([ref for recap in matching_recaps for ref in _recap_source_refs(recap)]),
            "time_ranges": [
                {"start_s": recap.time_start, "end_s": recap.time_end}
                for recap in matching_recaps[:6]
            ],
        })

    context_overview = _build_context_overview(
        themes=themes,
        main_actors=main_actors,
        open_loops=open_loops,
        risk_safety_issues=[],
        takeaway_points=takeaway_points,
    )
    anchor_records = _anchor_records(recaps, anchors)

    return ContextualMemory(
        media_id=media_id,
        context_overview=context_overview,
        main_actors=main_actors,
        timeline_anchors=anchor_records,
        locations=[],
        open_loops=open_loops,
        inferred_themes=themes,
        risk_safety_issues=[],
        contradictions=[],
        notable_evidence=notable_evidence,
        final_takeaways=final_takeaways,
        interpretive_notes=[],
        evidence_map={
            "final_takeaways": takeaway_points,
            "notable_evidence": notable_evidence_points,
            "themes": theme_points,
            "open_loops": open_loop_points,
            "timeline_anchors": anchor_records,
        },
        recap_ids=[r.recap_id for r in recaps],
    )
