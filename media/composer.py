"""L5: Document composer - generate task-specific output from contextual memory.

Chooses structure based on content type and generates the appropriate document
format: chronological report, meeting minutes, incident report, narrative, etc.
"""

from __future__ import annotations

import logging
import time
from typing import Optional

from media.models import (
    AtomicEvent,
    ComposedDocument,
    ContextualMemory,
    LocalRecap,
    OutputFormat,
)

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
7. Never fabricate details not present in the evidence"""

FORMAT_PROMPTS = {
    OutputFormat.CHRONOLOGICAL: """Generate a chronological report.

Structure:
1. **Timeline Overview**: Key timestamps and what happened
2. **Detailed Chronology**: Step-by-step account with timestamps
3. **Participants**: Who was involved and their roles
4. **Evidence Notes**: Key quotes and observations with source references

Best for: incidents, surveillance, operations logs, procedure playback.""",

    OutputFormat.MEETING_MINUTES: """Generate meeting minutes.

Structure:
1. **Meeting Summary**: Date, participants, duration, key outcomes
2. **Agenda Items Discussed**: Organized by topic
3. **Decisions Made**: With context and who made them
4. **Action Items**: Owner, deadline if mentioned, description
5. **Open Questions**: Unresolved issues for follow-up
6. **Next Steps**: What happens after this meeting

Best for: meetings, calls, standups, reviews.""",

    OutputFormat.INCIDENT_REPORT: """Generate an incident report.

Structure:
1. **Incident Summary**: What happened, when, severity
2. **Timeline of Events**: Precise chronology with timestamps
3. **Affected Parties**: Who was involved or impacted
4. **Root Cause Analysis**: If determinable from evidence
5. **Evidence**: Key observations with source references
6. **Recommendations**: Based on findings
7. **Open Questions**: What still needs investigation

Best for: incidents, security events, operational issues.""",

    OutputFormat.NARRATIVE: """Generate a narrative summary.

Structure:
1. **Opening**: Set the scene - what, where, when
2. **Development**: How events unfolded, key turning points
3. **Resolution/Current State**: Where things stand
4. **Significance**: Why this matters, implications

Best for: storytelling, case studies, human-facing summaries.""",

    OutputFormat.EXECUTIVE_BRIEF: """Generate an executive brief.

Structure:
1. **Bottom Line**: The single most important takeaway (1-2 sentences)
2. **Key Findings**: 3-5 bullet points
3. **Risks/Concerns**: If any
4. **Recommended Actions**: If applicable
5. **Supporting Evidence**: Brief reference to key moments

Best for: busy stakeholders, quick decisions, status updates.""",

    OutputFormat.THEMATIC: """Generate a thematic analysis.

Structure:
1. **Key Themes**: Major topics identified, organized by theme
2. **Per-Theme Analysis**: Evidence and discussion for each theme
3. **Cross-cutting Observations**: Patterns across themes
4. **Conclusions**: What the themes tell us

Best for: interviews, long discussions, educational content.""",

    OutputFormat.HYBRID: """Generate a hybrid report.

Structure:
1. **Executive Summary**: 2-3 sentence overview
2. **Chronological Account**: Detailed timeline
3. **Thematic Analysis**: Key themes identified
4. **Evidence Appendix**: Notable quotes and observations with timestamps

Best for: comprehensive analysis, official records, detailed reviews.""",
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
        f"## Output Format\n{format_instruction}",
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
    user_parts.append("Generate the document following the specified format.")
    user_parts.append("Every claim should reference specific evidence (timestamps, quotes).")
    user_parts.append("Adapt detail level to the significance of each segment.")

    return COMPOSER_SYSTEM_PROMPT, "\n".join(user_parts)


def _format_memory(memory: ContextualMemory) -> str:
    """Format memory for prompt inclusion."""
    parts = []
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
    return "\n".join(parts) if parts else "(No structured memory available)"


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
        composed_text = _mechanical_compose(memory, recaps, events, output_format)

    # Build sections from the text
    sections = []
    current_section = {"heading": "Document", "content": ""}
    for line in composed_text.split("\n"):
        if line.startswith("# ") or line.startswith("## "):
            if current_section["content"].strip():
                sections.append(current_section)
            current_section = {"heading": line.lstrip("# ").strip(), "content": ""}
        else:
            current_section["content"] += line + "\n"
    if current_section["content"].strip():
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


def _mechanical_compose(
    memory: ContextualMemory,
    recaps: list[LocalRecap],
    events: list[AtomicEvent],
    output_format: OutputFormat,
) -> str:
    """Generate a mechanical document without LLM assistance.

    Useful as a fallback or for testing. Produces structured text
    from the available data.
    """
    parts = []

    # Title
    parts.append(f"# {output_format.value.replace('_', ' ').title()}")
    parts.append("")

    # Summary
    if memory.main_actors:
        parts.append(f"**Participants**: {', '.join(memory.main_actors)}")
    if recaps:
        duration = recaps[-1].time_end - recaps[0].time_start
        parts.append(f"**Duration**: {duration:.0f} seconds ({duration/60:.1f} minutes)")
    parts.append(f"**Events**: {len(events)} atomic events across {len(recaps)} segments")
    parts.append("")

    # Body
    if output_format == OutputFormat.CHRONOLOGICAL or output_format == OutputFormat.HYBRID:
        parts.append("## Chronological Account")
        for recap in recaps:
            parts.append(f"\n### [{recap.time_start:.1f}s - {recap.time_end:.1f}s]")
            parts.append(recap.recap_text)
        parts.append("")

    if output_format == OutputFormat.MEETING_MINUTES:
        parts.append("## Discussion")
        for recap in recaps:
            parts.append(f"\n### [{recap.time_start:.1f}s - {recap.time_end:.1f}s]")
            parts.append(recap.recap_text)
        if memory.open_loops:
            parts.append("\n## Open Questions")
            for q in memory.open_loops:
                parts.append(f"- {q}")
        parts.append("")

    if output_format == OutputFormat.EXECUTIVE_BRIEF:
        parts.append("## Key Points")
        for recap in recaps[:3]:
            first_line = recap.recap_text.split("\n")[0] if recap.recap_text else ""
            parts.append(f"- {first_line}")
        parts.append("")

    # Themes
    if memory.inferred_themes:
        parts.append("## Themes")
        for theme in memory.inferred_themes:
            parts.append(f"- {theme}")
        parts.append("")

    # Open items
    if memory.open_loops:
        parts.append("## Unresolved Questions")
        for q in memory.open_loops:
            parts.append(f"- {q}")

    return "\n".join(parts)
