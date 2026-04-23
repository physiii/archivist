"""L5: Document composer - generate task-specific output from contextual memory.

Chooses structure based on content type and generates the appropriate document
format: chronological report, meeting minutes, incident report, narrative, etc.
"""

from __future__ import annotations

import logging
import re
import time
from typing import Optional

from media.models import (
    AtomicEvent,
    ComposedDocument,
    ContextualMemory,
    EventType,
    LocalRecap,
    OutputFormat,
)
from media.text_cleanup import distill_statement, extract_inline_topic_terms, extract_topic_phrases, is_weak_topic_phrase, strip_summary_boilerplate

logger = logging.getLogger("archivist.media.composer")

# ── Format-specific prompts ─────────────────────────────────────────────

COMPOSER_SYSTEM_PROMPT = """You are a document composer that generates structured documents from media analysis results.

Core principles:
1. Every claim must trace back to evidence (timestamps, quotes, visual observations)
2. Distinguish facts from inferences - always label inferences
3. Preserve uncertainty markers - "possibly", "appears to", "unclear whether"
4. Structure should serve the content, not the other way around
5. Include source references for verifiability
6. Adapt detail level to significance - more detail for critical moments
7. Never fabricate details not present in the evidence
8. The document must contain two clearly distinct layers:
   - a compressed contextual account for fast orientation
   - a walkthrough for chronological inspection
9. Never repeat the walkthrough verbatim inside the context sections
10. The context sections should read like a compressed document brief, not a replay of segment-by-segment chronology"""

FORMAT_PROMPTS = {
    OutputFormat.CHRONOLOGICAL: "Emphasize operational flow, what changed over time, and precise chronology.",
    OutputFormat.MEETING_MINUTES: "Emphasize decisions, follow-up work, current status, and unresolved questions.",
    OutputFormat.INCIDENT_REPORT: "Emphasize impact, likely causes, risks, and what still requires investigation.",
    OutputFormat.NARRATIVE: "Emphasize the setup, turning points, and current state without losing evidence anchors.",
    OutputFormat.EXECUTIVE_BRIEF: "Emphasize the bottom line quickly and keep the contextual account tight.",
    OutputFormat.THEMATIC: "Emphasize recurring themes, cross-cutting patterns, and what they imply.",
    OutputFormat.HYBRID: "Balance high-level context with enough chronology to preserve auditability.",
}


# ── Format Selection ────────────────────────────────────────────────────


def select_output_format(memory: ContextualMemory, events: list[AtomicEvent]) -> OutputFormat:
    """Automatically select the best output format based on content analysis.

    Uses heuristics based on content characteristics:
    - Multiple speakers + decision events -> meeting minutes
    - Risk/safety issues -> incident report
    - Short duration + few events -> executive brief
    - Lots of visual events -> hybrid
    - Default -> chronological
    """
    if not events:
        return OutputFormat.EXECUTIVE_BRIEF

    has_decisions = any(e.event_type.value == "decision" for e in events)
    has_questions = any(e.event_type.value == "question" for e in events)
    has_multiple_speakers = len(set(
        speaker for e in events for speaker in e.speakers
    )) > 1
    has_multiple_participants = has_multiple_speakers or len(memory.main_actors) > 1

    has_risk = bool(memory.risk_safety_issues)
    has_visual = any(e.visual_entities for e in events)
    duration = events[-1].time_end - events[0].time_start if events else 0

    # Meeting: multiple speakers + decisions/questions
    if has_multiple_participants and (has_decisions or has_questions):
        return OutputFormat.MEETING_MINUTES

    # Incident: risk/safety issues present
    if has_risk:
        return OutputFormat.INCIDENT_REPORT

    # Brief: short content
    if duration < 120 and len(events) < 10:
        return OutputFormat.EXECUTIVE_BRIEF

    # Hybrid: visual + audio content
    if has_visual and has_multiple_participants:
        return OutputFormat.HYBRID

    # Default: chronological
    return OutputFormat.CHRONOLOGICAL


# ── Document Composition ────────────────────────────────────────────────


def build_compose_prompt(
    memory: ContextualMemory,
    recaps: list[LocalRecap],
    events: list[AtomicEvent],
    output_format: Optional[OutputFormat] = None,
) -> tuple[str, str]:
    """Build prompts for LLM-based document composition.

    Returns (system_prompt, user_prompt).
    """
    if output_format is None:
        output_format = select_output_format(memory, events)

    format_instruction = FORMAT_PROMPTS.get(output_format, FORMAT_PROMPTS[OutputFormat.CHRONOLOGICAL])

    user_parts = [
        f"## Output Format Preference\n{output_format.value.replace('_', ' ')}",
        f"## Format Emphasis\n{format_instruction}",
        "",
        "## Contextual Memory",
        _format_memory(memory),
        "",
        "## Local Recaps (chronological)",
    ]

    for i, recap in enumerate(recaps, 1):
        user_parts.append(f"\n### Segment {i} [{recap.time_start:.1f}s - {recap.time_end:.1f}s]")
        user_parts.append(recap.recap_text)

    user_parts.append("\n## Instructions")
    user_parts.append("Generate a user-facing document with these exact section headings:")
    user_parts.append("1. ## Context Overview")
    user_parts.append("2. ## Key Topics")
    user_parts.append("3. ## Decisions and Follow-Ups (omit only if there are truly none)")
    user_parts.append("4. ## Walkthrough")
    user_parts.append("The Context Overview and Key Topics sections must be highly compressed and synthesize meaning.")
    user_parts.append("The Walkthrough section must stay chronological and inspectable.")
    user_parts.append("Chronology is the canonical truth; presentation order is a document-layer choice built on top of that truth.")
    user_parts.append("Never paste the same text into both the context and walkthrough sections.")
    user_parts.append("Every claim should reference specific evidence (timestamps, quotes, recap IDs, or visible observations).")
    user_parts.append("Keep interpretations separate from facts and tie them to evidence when included.")
    user_parts.append("Prefer evidence anchors from the provided memory and recap refs when summarizing.")
    user_parts.append("Do not include title metadata, duration metadata, or other boilerplate inside the section bodies unless it matters.")

    return COMPOSER_SYSTEM_PROMPT, "\n".join(user_parts)


def _format_memory(memory: ContextualMemory) -> str:
    """Format memory for prompt inclusion."""
    parts = []
    if memory.context_overview:
        parts.append(f"**Context overview**: {memory.context_overview}")
    if memory.main_actors:
        parts.append(f"**Main actors**: {', '.join(memory.main_actors)}")
    if memory.timeline_anchors:
        anchor_strs = [f"{a['label']} ({a['time']:.1f}s)" for a in memory.timeline_anchors]
        parts.append(f"**Timeline**: {' -> '.join(anchor_strs)}")
    if memory.inferred_themes:
        parts.append(f"**Themes**: {', '.join(memory.inferred_themes)}")
    if memory.open_loops:
        parts.append(f"**Open questions**: {'; '.join(memory.open_loops[:5])}")
    if memory.risk_safety_issues:
        parts.append(f"**Risk/safety**: {'; '.join(memory.risk_safety_issues)}")
    if memory.contradictions:
        parts.append(f"**Contradictions**: {'; '.join(memory.contradictions)}")
    if memory.interpretive_notes:
        rendered_notes = [
            f"{note.get('label', '')} (conf={note.get('confidence', 0):.2f})"
            for note in memory.interpretive_notes[:4]
            if isinstance(note, dict) and note.get("label")
        ]
        if rendered_notes:
            parts.append(f"**Interpretive notes**: {'; '.join(rendered_notes)}")
    if memory.final_takeaways:
        parts.append("**Takeaways**:")
        takeaway_items = memory.evidence_map.get("final_takeaways", [])[:4]
        if takeaway_items:
            for item in takeaway_items:
                if not isinstance(item, dict):
                    continue
                refs = ", ".join(str(ref) for ref in item.get("source_refs", [])[:3])
                text = str(item.get("text") or "").strip()
                if text:
                    parts.append(f"- {text}{f' [{refs}]' if refs else ''}")
        else:
            parts.extend(f"- {item}" for item in memory.final_takeaways[:4])
    if memory.notable_evidence:
        parts.append("**Notable evidence**:")
        evidence_items = memory.evidence_map.get("notable_evidence", [])[:4]
        if evidence_items:
            for item in evidence_items:
                if not isinstance(item, dict):
                    continue
                refs = ", ".join(str(ref) for ref in item.get("source_refs", [])[:3])
                text = str(item.get("text") or "").strip()
                if text:
                    parts.append(f"- {text}{f' [{refs}]' if refs else ''}")
        else:
            parts.extend(f"- {item}" for item in memory.notable_evidence[:4])
    return "\n".join(parts) if parts else "(No structured memory available)"


def _event_brief(event: AtomicEvent, limit: int = 180) -> str:
    question_text = str(event.metadata.get("question_text") or "").strip()
    if event.event_type == EventType.QUESTION and question_text:
        return question_text
    return str(event.metadata.get("brief") or distill_statement(event.text_evidence, limit=limit))


def _recap_summary_line(recap: LocalRecap) -> str:
    def _fallback_from_refs() -> str:
        for ref in recap.summary_refs:
            if not isinstance(ref, dict):
                continue
            candidate = strip_summary_boilerplate(str(ref.get("summary") or "")).strip()
            if candidate and not is_weak_topic_phrase(candidate):
                return candidate
            for term in extract_inline_topic_terms(str(ref.get("summary") or ""), limit=3):
                if not is_weak_topic_phrase(term):
                    return f"Discussion of {term}."
        for entry in recap.ledger_entries:
            if not isinstance(entry, dict):
                continue
            candidate = strip_summary_boilerplate(str(entry.get("summary") or "")).strip()
            if candidate and not is_weak_topic_phrase(candidate):
                return candidate
            terms = extract_inline_topic_terms(str(entry.get("summary") or ""), limit=3)
            if terms:
                return f"Discussion of {', '.join(terms[:3])}."
        return ""

    for line in recap.recap_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("Window summary:"):
            candidate = strip_summary_boilerplate(stripped.removeprefix("Window summary:").strip()) or stripped.removeprefix("Window summary:").strip()
            if candidate and not is_weak_topic_phrase(candidate):
                return candidate
            fallback = _fallback_from_refs()
            if fallback:
                return fallback
        if stripped.startswith("Summary:"):
            candidate = strip_summary_boilerplate(stripped.removeprefix("Summary:").strip()) or stripped.removeprefix("Summary:").strip()
            if candidate and not is_weak_topic_phrase(candidate):
                return candidate
            fallback = _fallback_from_refs()
            if fallback:
                return fallback
    candidate = strip_summary_boilerplate(distill_statement(recap.recap_text, limit=180)) or distill_statement(recap.recap_text, limit=180)
    if candidate and not is_weak_topic_phrase(candidate):
        return candidate
    fallback = _fallback_from_refs()
    if fallback:
        return fallback
    terms = extract_inline_topic_terms(recap.recap_text, limit=3)
    if terms:
        return f"Discussion of {', '.join(terms[:3])}."
    return candidate


def _dedupe_items(values: list[str], limit: int = 10) -> list[str]:
    seen: set[str] = set()
    items: list[str] = []
    for value in values:
        clean = " ".join(str(value or "").split()).strip()
        if not clean:
            continue
        key = clean.lower().strip(" ?!.,;:-")
        if key in seen:
            continue
        seen.add(key)
        items.append(clean)
        if len(items) >= limit:
            break
    return items


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


def _memory_refs(memory: ContextualMemory, key: str, limit: int = 12) -> list[str]:
    refs: list[str] = []
    for item in memory.evidence_map.get(key, [])[:8]:
        if not isinstance(item, dict):
            continue
        refs.extend(str(ref) for ref in item.get("source_refs", []) or [])
        for nested in item.get("summary_refs", []) or []:
            if isinstance(nested, dict):
                refs.extend(str(ref) for ref in nested.get("source_refs", []) or [])
                event_id = str(nested.get("event_id") or "").strip()
                if event_id:
                    refs.append(event_id)
        event_id = str(item.get("event_id") or "").strip()
        if event_id:
            refs.append(event_id)
        recap_id = str(item.get("recap_id") or "").strip()
        if recap_id:
            refs.append(recap_id)
    return _dedupe_refs(refs, limit=limit)


def _event_refs(events: list[AtomicEvent], limit: int = 12) -> list[str]:
    refs: list[str] = []
    for event in events:
        refs.append(event.event_id)
        refs.extend(event.source_refs)
    return _dedupe_refs(refs, limit=limit)


def _extract_action_item(event: AtomicEvent) -> str:
    if event.metadata.get("brief"):
        return str(event.metadata["brief"])
    text = event.text_evidence or ""
    match = re.search(
        r"\b(i(?:'ll| will)|we(?:'ll| will)|let me|we need to|i need to|i can|we can|start|check|look into|follow up)\b(.+)",
        text,
        re.IGNORECASE,
    )
    if match:
        action = f"{match.group(1)}{match.group(2)}"
        return distill_statement(action, limit=180)
    return distill_statement(text, limit=180)


def _is_followup_event(event: AtomicEvent) -> bool:
    text = str(event.metadata.get("brief") or event.text_evidence or "")
    return bool(re.search(
        r"\b(i(?:'ll| will)|we(?:'ll| will)|we need to|i need to|follow up|look into|dig into|check|review|share|send|reach out|fix|update|document)\b",
        text,
        re.IGNORECASE,
    ))


def _format_people(values: list[str], limit: int = 4) -> str:
    people = values[:limit]
    if not people:
        return ""
    if len(people) == 1:
        return people[0]
    if len(people) == 2:
        return f"{people[0]} and {people[1]}"
    return f"{', '.join(people[:-1])}, and {people[-1]}"


def _window_events(recap: LocalRecap, events: list[AtomicEvent]) -> list[AtomicEvent]:
    return [
        event
        for event in events
        if event.time_start >= recap.time_start - 0.05 and event.time_end <= recap.time_end + 0.05
    ]


def _recap_salience(recap: LocalRecap, events: list[AtomicEvent]) -> int:
    score = 0
    for event in _window_events(recap, events):
        if event.event_type == EventType.DECISION:
            score += 4
        elif event.event_type == EventType.ACTION:
            score += 3
        elif event.event_type == EventType.QUESTION:
            score += 2
        else:
            score += 1
    return score


def _salient_recap_bullets(recaps: list[LocalRecap], events: list[AtomicEvent], limit: int = 4) -> list[str]:
    ranked = sorted(recaps, key=lambda recap: (-_recap_salience(recap, events), recap.time_start))
    selected: list[LocalRecap] = []
    seen: set[str] = set()
    for recap in ranked:
        summary = _recap_summary_line(recap)
        key = summary.lower().strip(" ?!.,;:-")
        if not summary or key in seen:
            continue
        seen.add(key)
        selected.append(recap)
        if len(selected) >= limit:
            break
    selected.sort(key=lambda recap: recap.time_start)
    return [f"- [{recap.time_start:.1f}s - {recap.time_end:.1f}s] {_recap_summary_line(recap)}" for recap in selected]


def _topic_lines(memory: ContextualMemory, recaps: list[LocalRecap]) -> list[str]:
    topic_terms = memory.inferred_themes[:6] or extract_topic_phrases([recap.recap_text for recap in recaps], limit=6)
    topic_map = {
        str(item.get("label") or ""): item
        for item in memory.evidence_map.get("themes", [])
        if isinstance(item, dict) and item.get("label")
    }
    lines: list[str] = []
    for topic in topic_terms:
        if is_weak_topic_phrase(topic):
            continue
        anchor = ""
        themed_item = topic_map.get(topic)
        if themed_item and themed_item.get("time_ranges"):
            first_range = themed_item["time_ranges"][0]
            if isinstance(first_range, dict):
                anchor = f"[{float(first_range.get('start_s', 0.0)):.1f}s - {float(first_range.get('end_s', 0.0)):.1f}s] "
        else:
            lowered = topic.lower()
            for recap in recaps:
                if lowered in recap.recap_text.lower():
                    anchor = f"[{recap.time_start:.1f}s - {recap.time_end:.1f}s] "
                    break
        lines.append(f"- {anchor}{topic}")
    return _dedupe_items(lines, limit=6)


def _context_overview_content(
    memory: ContextualMemory,
    recaps: list[LocalRecap],
    events: list[AtomicEvent],
) -> str:
    themes = memory.inferred_themes[:4] or extract_topic_phrases([recap.recap_text for recap in recaps], limit=4)
    participants = _format_people(memory.main_actors)
    decisions = [event for event in events if event.event_type == EventType.DECISION]
    actions = [event for event in events if _is_followup_event(event)]
    sentences: list[str] = []
    if memory.context_overview:
        sentences.append(memory.context_overview)
    elif themes:
        sentences.append(f"The recording focuses on {', '.join(themes)}.")
    elif recaps:
        sentences.append(f"The recording centers on {_recap_summary_line(recaps[0]).rstrip('.')}.")
    if participants:
        sentences.append(f"The main participants are {participants}.")

    status_parts: list[str] = []
    if decisions:
        status_parts.append(f"{len(decisions)} decision{'s' if len(decisions) != 1 else ''}")
    if actions:
        status_parts.append(f"{len(actions)} follow-up item{'s' if len(actions) != 1 else ''}")
    if memory.open_loops:
        status_parts.append(f"{len(memory.open_loops)} open question{'s' if len(memory.open_loops) != 1 else ''}")
    if status_parts:
        sentences.append(f"The review yields {', '.join(status_parts)}.")

    bullets = _salient_recap_bullets(recaps, events, limit=4)
    parts = [" ".join(sentences).strip()] if sentences else []
    if bullets:
        parts.append("\n".join(bullets))
    return "\n\n".join(part for part in parts if part).strip()


def _decisions_followups_content(memory: ContextualMemory, events: list[AtomicEvent]) -> str:
    decision_items = _dedupe_items([
        f"- Decision [{event.time_start:.1f}s] {_event_brief(event)}"
        for event in events
        if event.event_type == EventType.DECISION
    ], limit=6)
    action_items = _dedupe_items([
        f"- Follow-up [{event.time_start:.1f}s] {_extract_action_item(event)}"
        for event in events
        if _is_followup_event(event)
    ], limit=6)
    open_questions = _dedupe_items([
        f"- Open question: {question}"
        for question in memory.open_loops
    ], limit=6)
    risk_items = _dedupe_items([f"- Risk: {risk}" for risk in memory.risk_safety_issues], limit=4)
    return "\n".join([*decision_items, *action_items, *open_questions, *risk_items]).strip()


def _walkthrough_content(recaps: list[LocalRecap]) -> str:
    lines: list[str] = []
    for recap in recaps:
        lines.append(f"### [{recap.time_start:.1f}s - {recap.time_end:.1f}s]")
        lines.append(_recap_summary_line(recap))
        key_points = [
            line.strip()
            for line in recap.recap_text.splitlines()
            if line.strip().startswith("- ")
        ][:5]
        if key_points:
            lines.append("")
            lines.extend(key_points)
        lines.append("")
    return "\n".join(lines).strip()


def _section(heading: str, content: str, kind: str, source_refs: Optional[list[str]] = None) -> dict:
    section = {
        "heading": heading,
        "content": content.strip(),
        "kind": kind,
    }
    if source_refs:
        section["source_refs"] = source_refs
    return section


def _infer_section_kind(heading: str) -> str:
    return "walkthrough" if re.search(r"(walkthrough|discussion|timeline|chronology)", heading, re.IGNORECASE) else "context"


def _render_sections_markdown(title: str, sections: list[dict]) -> str:
    parts = [f"# {title}", ""]
    for section in sections:
        parts.append(f"## {section['heading']}")
        parts.append("")
        parts.append(str(section.get("content") or "").strip())
        parts.append("")
    return "\n".join(parts).strip()


def _mechanical_sections(
    memory: ContextualMemory,
    recaps: list[LocalRecap],
    events: list[AtomicEvent],
    output_format: OutputFormat,
) -> list[dict]:
    sections: list[dict] = []

    context_overview = _context_overview_content(memory, recaps, events)
    if context_overview:
        sections.append(_section(
            "Context Overview",
            context_overview,
            "context",
            source_refs=_memory_refs(memory, "final_takeaways") or [recap.recap_id for recap in recaps[:4]],
        ))

    topic_content = "\n".join(_topic_lines(memory, recaps)).strip()
    if topic_content:
        sections.append(_section(
            "Key Topics",
            topic_content,
            "context",
            source_refs=_memory_refs(memory, "themes") or [recap.recap_id for recap in recaps],
        ))

    decisions_followups = _decisions_followups_content(memory, events)
    if decisions_followups:
        sections.append(_section(
            "Decisions and Follow-Ups",
            decisions_followups,
            "context",
            source_refs=_event_refs([
                event
                for event in events
                if event.event_type in {EventType.DECISION, EventType.ACTION, EventType.QUESTION}
            ]) or [event.event_id for event in events],
        ))

    walkthrough = _walkthrough_content(recaps)
    if walkthrough:
        sections.append(_section(
            "Walkthrough",
            walkthrough,
            "walkthrough",
            source_refs=[recap.recap_id for recap in recaps],
        ))

    if not sections:
        sections.append(_section(
            "Context Overview",
            f"No derived content was available for this {output_format.value.replace('_', ' ')}.",
            "context",
        ))

    return sections


def compose_document(
    memory: ContextualMemory,
    recaps: list[LocalRecap],
    events: list[AtomicEvent],
    output_format: Optional[OutputFormat] = None,
    composed_text: str = "",
) -> ComposedDocument:
    """Compose a document from memory and recaps.

    If composed_text is provided (e.g. from LLM), uses it directly.
    Otherwise builds a mechanical document from the structured data.
    """
    if output_format is None:
        output_format = select_output_format(memory, events)

    if not composed_text:
        title = output_format.value.replace("_", " ").title()
        sections = _mechanical_sections(memory, recaps, events, output_format)
        composed_text = _render_sections_markdown(title, sections)
    else:
        sections = []
        current_section: Optional[dict] = None
        for line in composed_text.split("\n"):
            if line.startswith("# "):
                continue
            if line.startswith("## "):
                if current_section and str(current_section.get("content") or "").strip():
                    current_section["content"] = str(current_section["content"]).rstrip()
                    sections.append(current_section)
                heading = line.removeprefix("## ").strip()
                current_section = {"heading": heading, "content": "", "kind": _infer_section_kind(heading)}
                continue
            if current_section is None:
                continue
            current_section["content"] += line + "\n"
        if current_section and str(current_section.get("content") or "").strip():
            current_section["content"] = str(current_section["content"]).rstrip()
            sections.append(current_section)

    return ComposedDocument(
        media_id=memory.media_id,
        format=output_format,
        title=f"{output_format.value.replace('_', ' ').title()} - {memory.media_id}",
        sections=sections,
        full_text=composed_text,
        memory_id=memory.memory_id,
        source_refs=[r.recap_id for r in recaps],
        generated_at=time.time(),
    )
