"""Media processing pipeline orchestrator.

Coordinates the 6-layer processing of media files:
L0 -> L1 -> L2 -> L3 -> L4 -> L5

Supports both synchronous single-file processing and watched-folder
background processing for incoming media.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from pathlib import Path
from typing import Optional

from media.evidence_store import (
    ALL_MEDIA_EXTS,
    register_asset,
    _load_assets_index,
)
from media.event_extraction import (
    extract_events_from_scenes,
    extract_events_from_speech,
    merge_events,
)
from media.filtering import (
    filter_asset,
)
from media.memory import build_memory_from_recaps, build_memory_prompt
from media.models import (
    ComposedDocument,
    ContextualMemory,
    DerivedArtifact,
    LocalRecap,
    MediaAsset,
    Modality,
    OutputFormat,
    PipelineJob,
)
from media.recaps import build_recap_from_events, build_recaps, group_events_by_time_window
from media.composer import build_compose_prompt, compose_document, select_output_format

logger = logging.getLogger("archivist.media.pipeline")

PIPELINE_STORE_DIR = Path(os.getenv("MEDIA_PIPELINE_DIR", "/data/media_pipeline"))
WATCH_INTERVAL_S = int(os.getenv("MEDIA_WATCH_INTERVAL_S", "30"))
OPENCLAW_GATEWAY_URL = os.getenv("OPENCLAW_GATEWAY_URL", "http://127.0.0.1:18789").rstrip("/")
OPENCLAW_GATEWAY_TOKEN = os.getenv("OPENCLAW_GATEWAY_TOKEN", "").strip()
OPENCLAW_CHAT_MODEL = os.getenv("OPENCLAW_CHAT_MODEL", "openclaw/default").strip()
SUBJECT_MAX_WORDS = max(8, int(os.getenv("MEDIA_SUBJECT_MAX_WORDS", "24")))
SUBJECT_MAX_CONTEXT_ARTIFACTS = max(6, int(os.getenv("MEDIA_SUBJECT_MAX_CONTEXT_ARTIFACTS", "12")))
SUBJECT_MAX_PREVIEW_CHARS = max(80, int(os.getenv("MEDIA_SUBJECT_MAX_PREVIEW_CHARS", "220")))
SUBJECT_STOP_TERMS = {
    "additional", "are", "awesome", "blah", "everybody", "fuck", "god", "never",
    "no", "none", "nope", "obviously", "okay", "so", "they", "versus", "wait",
    "whereas", "yep", "yes",
}

# ── Active job tracking ─────────────────────────────────────────────────

_active_jobs: dict[str, PipelineJob] = {}
_jobs_lock = threading.Lock()
_watcher_thread: Optional[threading.Thread] = None
_watcher_stop = threading.Event()
_watch_dirs: list[str] = []


def get_active_jobs() -> list[dict]:
    """Get all active/recent pipeline jobs."""
    with _jobs_lock:
        return [
            {
                "job_id": j.job_id,
                "media_id": j.media_id,
                "status": j.status,
                "current_layer": j.current_layer,
                "progress": j.progress,
                "started_at": j.started_at,
                "finished_at": j.finished_at,
                "error": j.error,
                "artifacts_count": j.artifacts_count,
                "events_count": j.events_count,
                "recaps_count": j.recaps_count,
            }
            for j in _active_jobs.values()
        ]


def _update_job(job: PipelineJob, **kwargs):
    for key, value in kwargs.items():
        setattr(job, key, value)


def _pipeline_sidecar_path(asset_path: str | Path) -> Path:
    return Path(asset_path).with_suffix(".json")


def _write_pipeline_sidecar(asset: MediaAsset, result: dict) -> Optional[Path]:
    sidecar_path = _pipeline_sidecar_path(asset.path)
    try:
        serializable = json.loads(json.dumps(result, default=str))
        sidecar_path.write_text(json.dumps(serializable, indent=2), encoding="utf-8")
        return sidecar_path
    except OSError as exc:
        logger.warning("Failed to write pipeline sidecar for %s: %s", asset.filename, exc)
        return None


def _media_output_complete(media_id: str) -> bool:
    return bool(media_id) and (PIPELINE_STORE_DIR / f"{media_id}.json").exists()


def _asset_record_complete(asset_data: dict) -> bool:
    path = str(asset_data.get("path") or "")
    media_id = str(asset_data.get("media_id") or "")
    return bool(path) and Path(path).exists() and _media_output_complete(media_id)


def _clip_subject_text(text: str, limit: int = SUBJECT_MAX_PREVIEW_CHARS) -> str:
    clean = " ".join(str(text or "").split()).strip()
    if len(clean) <= limit:
        return clean
    clipped = clean[:limit].rsplit(" ", 1)[0].strip()
    return f"{clipped}..."


def _subject_artifact_priority(kind: str) -> int:
    priority = {
        "document": 0,
        "memory": 1,
        "recap": 2,
        "event": 3,
        "transcript": 4,
        "scene": 5,
        "speech_segment": 6,
        "keyframe": 7,
    }
    return priority.get(kind, 99)


def _join_subject_terms(values: list[str], limit: int = 3) -> str:
    cleaned = _clean_subject_terms(values, limit=limit)
    if not cleaned:
        return ""
    if len(cleaned) == 1:
        return cleaned[0]
    if len(cleaned) == 2:
        return f"{cleaned[0]} and {cleaned[1]}"
    return f"{', '.join(cleaned[:-1])}, and {cleaned[-1]}"


def _clean_subject_terms(values: list[str], limit: Optional[int] = None) -> list[str]:
    cleaned: list[str] = []
    for value in values:
        term = _clip_subject_text(value, limit=80).strip(" ,.;:-")
        if not term or term.lower() in SUBJECT_STOP_TERMS:
            continue
        if term not in cleaned:
            cleaned.append(term)
        if limit is not None and len(cleaned) >= limit:
            break
    return cleaned


def _infer_subject_activity(artifacts: list[DerivedArtifact], document: Optional[ComposedDocument]) -> str:
    event_type_counts: dict[str, int] = {}
    for artifact in artifacts:
        if artifact.kind != "event":
            continue
        label = str(artifact.metadata.get("event_type") or "").strip().lower()
        if label:
            event_type_counts[label] = event_type_counts.get(label, 0) + 1

    if event_type_counts.get("decision") and event_type_counts.get("question"):
        return "discuss decisions and open questions"
    if event_type_counts.get("decision"):
        return "work through decisions"
    if event_type_counts.get("question"):
        return "work through open questions"
    if event_type_counts.get("action"):
        return "review ongoing actions"
    if document and document.format == OutputFormat.MEETING_MINUTES:
        return "discuss the main topics"
    if document and document.format == OutputFormat.INCIDENT_REPORT:
        return "document an incident"
    if document and document.format == OutputFormat.EXECUTIVE_BRIEF:
        return "capture the main points"
    return "capture the main activity"


def _build_subject_line_fallback(
    asset: MediaAsset,
    artifacts: list[DerivedArtifact],
    memory: ContextualMemory,
    document: Optional[ComposedDocument],
) -> str:
    participants = _join_subject_terms(memory.main_actors, limit=3)
    themes = _join_subject_terms(memory.inferred_themes, limit=2)

    entities: list[str] = []
    for artifact in artifacts:
        if artifact.kind == "event":
            source_entities = artifact.metadata.get("entities", []) or []
        elif artifact.kind == "recap":
            source_entities = artifact.metadata.get("salient_entities", []) or []
        else:
            source_entities = []
        for entity in source_entities:
            entity_text = str(entity or "").strip()
            if entity_text and entity_text not in entities:
                entities.append(entity_text)
        if len(entities) >= 3:
            break
    entity_text = _join_subject_terms(entities, limit=2)

    activity = _infer_subject_activity(artifacts, document)
    format_phrase = "recorded file"
    if document and document.format == OutputFormat.MEETING_MINUTES:
        format_phrase = "recorded meeting"
    elif document and document.format == OutputFormat.INCIDENT_REPORT:
        format_phrase = "recorded incident review"
    elif document and document.format == OutputFormat.EXECUTIVE_BRIEF:
        format_phrase = "recorded briefing"

    if participants and themes:
        return f"{participants} {activity} around {themes}."
    if participants:
        return f"{participants} {activity} in a {format_phrase}."
    if themes:
        return f"This {asset.modality.value} file {activity} around {themes}."
    if entity_text:
        return f"This {asset.modality.value} file {activity} involving {entity_text}."
    if document and document.title:
        title_text = _clip_subject_text(document.title, limit=100).strip(" .")
        return f"This {asset.modality.value} file documents {title_text.lower()}."
    return f"This {asset.modality.value} file {activity}."


def _normalize_subject_line(text: str, fallback: str) -> str:
    clean = str(text or "").strip()
    clean = clean.replace("\r", " ")
    clean = clean.splitlines()[0].strip() if clean else ""
    clean = clean.removeprefix("Subject:").removeprefix("subject:").strip()
    clean = clean.strip("`\"' ")
    if not clean:
        clean = fallback
    clean = " ".join(clean.split()).strip()

    split = clean.replace("!", ".").replace("?", ".")
    first_sentence = split.split(".", 1)[0].strip()
    clean = first_sentence or clean

    words = clean.split()
    if len(words) > SUBJECT_MAX_WORDS:
        clean = " ".join(words[:SUBJECT_MAX_WORDS]).rstrip(" ,;:-")

    if clean and clean[-1] not in ".!?":
        clean = f"{clean}."
    return clean or fallback


def build_subject_line_prompt(
    asset: MediaAsset,
    artifacts: list[DerivedArtifact],
    memory: ContextualMemory,
    document: Optional[ComposedDocument],
) -> tuple[str, str, list[str]]:
    kind_counts: dict[str, int] = {}
    for artifact in artifacts:
        kind_counts[artifact.kind] = kind_counts.get(artifact.kind, 0) + 1

    selected = sorted(
        artifacts,
        key=lambda artifact: (_subject_artifact_priority(artifact.kind), artifact.start_s, artifact.end_s),
    )[:SUBJECT_MAX_CONTEXT_ARTIFACTS]

    context_lines = []
    source_refs: list[str] = []
    for artifact in selected:
        preview = _clip_subject_text(artifact.content)
        if artifact.kind == "event":
            event_type = str(artifact.metadata.get("event_type") or "event")
            preview = f"{event_type}: {preview}"
        elif artifact.kind == "recap":
            preview = f"window {artifact.start_s:.0f}-{artifact.end_s:.0f}s: {preview}"
        elif artifact.kind == "memory":
            preview = (
                f"actors={', '.join(memory.main_actors[:5]) or 'none'}; "
                f"themes={', '.join(memory.inferred_themes[:5]) or 'none'}"
            )
        elif artifact.kind == "document":
            preview = _clip_subject_text(document.full_text if document else artifact.content)
        context_lines.append(f"- [{artifact.kind}] {preview}")
        source_refs.append(artifact.artifact_id)

    summary_lines = [
        f"Filename: {asset.filename}",
        f"Modality: {asset.modality.value}",
        f"Duration seconds: {asset.duration_s:.1f}",
        f"Document format: {document.format.value if document and hasattr(document.format, 'value') else ''}",
        f"Document title: {document.title if document else ''}",
        f"Main actors: {', '.join(memory.main_actors[:6]) or 'none'}",
        f"Themes: {', '.join(memory.inferred_themes[:6]) or 'none'}",
        f"Open loops: {len(memory.open_loops)}",
        "Artifact counts: " + ", ".join(f"{kind}={count}" for kind, count in sorted(kind_counts.items())),
        "Representative artifacts:",
        *(context_lines or ["- [none] no artifact context available"]),
        "",
        f"Write one factual sentence only, under {SUBJECT_MAX_WORDS} words, describing what this file is about.",
    ]
    system_prompt = (
        "You create concise archival subject lines for processed media files. "
        "Return exactly one sentence with no markdown, no quotes, no file IDs, and no speaker labels."
    )
    return system_prompt, "\n".join(summary_lines), source_refs


def _generate_subject_line(
    asset: MediaAsset,
    artifacts: list[DerivedArtifact],
    memory: ContextualMemory,
    document: Optional[ComposedDocument],
) -> tuple[str, dict]:
    fallback = _build_subject_line_fallback(asset, artifacts, memory, document)
    system_prompt, user_prompt, source_refs = build_subject_line_prompt(asset, artifacts, memory, document)
    details = {
        "generator": "heuristic",
        "model": None,
        "source_artifact_count": len(artifacts),
        "context_artifact_refs": source_refs,
        "error": None,
    }

    if not OPENCLAW_GATEWAY_TOKEN:
        return _normalize_subject_line(fallback, fallback), details | {"reason": "gateway_unconfigured"}

    try:
        import requests

        response = requests.post(
            f"{OPENCLAW_GATEWAY_URL}/v1/chat/completions",
            json={
                "model": OPENCLAW_CHAT_MODEL,
                "stream": False,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "user": f"media-subject:{asset.media_id}",
            },
            headers={
                "Authorization": f"Bearer {OPENCLAW_GATEWAY_TOKEN}",
                "Content-Type": "application/json",
                "x-openclaw-session-key": f"media-subject:{asset.media_id}",
            },
            timeout=90,
        )
        response.raise_for_status()
        payload = response.json()
        content = payload.get("choices", [{}])[0].get("message", {}).get("content", "")
        subject_line = _normalize_subject_line(content, fallback)
        return subject_line, details | {"generator": "openclaw", "model": OPENCLAW_CHAT_MODEL}
    except Exception as exc:
        logger.warning("Subject line inference failed for %s: %s", asset.filename, exc)
        return _normalize_subject_line(fallback, fallback), details | {
            "reason": "gateway_error",
            "error": str(exc),
            "model": OPENCLAW_CHAT_MODEL,
        }


# ── Pipeline Execution ──────────────────────────────────────────────────


def process_media_file(
    path: str,
    output_format: Optional[OutputFormat] = None,
    recap_window_s: float = 60.0,
    metadata: Optional[dict] = None,
) -> dict:
    """Process a single media file through the full pipeline.

    Returns a dict with results from each layer.

    Args:
        path: Path to the media file.
        output_format: Desired output format. Auto-detected if None.
        recap_window_s: Time window for grouping events into recaps.
        metadata: Optional metadata to attach to the asset.
    """
    job = PipelineJob(started_at=time.time())
    with _jobs_lock:
        _active_jobs[job.job_id] = job

    result: dict = {"job_id": job.job_id, "layers": {}}

    try:
        # ── L0: Register asset ──────────────────────────────────────
        _update_job(job, status="deriving", current_layer="L0_evidence", progress=0.1)
        asset = register_asset(path, metadata=metadata)
        job.media_id = asset.media_id
        result["media_id"] = asset.media_id
        result["asset"] = {
            "path": asset.path,
            "filename": asset.filename,
            "modality": asset.modality.value,
            "duration_s": asset.duration_s,
            "file_hash": asset.file_hash,
        }

        # ── Derive transcription for audio/video ────────────────────
        transcript_payload = None
        transcript_segments = None
        if asset.modality in (Modality.AUDIO, Modality.VIDEO):
            transcript_payload = _derive_transcript(asset, job)
            transcript_segments = transcript_payload.get("segments") if transcript_payload else None
        if transcript_payload:
            result["transcript"] = {
                "text": transcript_payload.get("text", ""),
                "meta": transcript_payload.get("meta", {}),
                "segment_count": len(transcript_segments or []),
            }

        # ── L1: Filter ──────────────────────────────────────────────
        _update_job(job, status="filtering", current_layer="L1_filtering", progress=0.3)
        filter_results = filter_asset(asset, transcript_segments=transcript_segments)
        result["layers"]["L1_filtering"] = {
            "scene_count": len(filter_results.get("scenes", [])),
            "speech_segment_count": len(filter_results.get("speech_segments", [])),
            "keyframe_count": len(filter_results.get("keyframes", [])),
        }

        # ── L2: Extract events ──────────────────────────────────────
        _update_job(job, status="extracting", current_layer="L2_events", progress=0.5)
        speech_events = extract_events_from_speech(
            filter_results.get("speech_segments", []),
            media_id=asset.media_id,
        )
        scene_events = extract_events_from_scenes(
            filter_results.get("scenes", []),
            media_id=asset.media_id,
        )
        all_events = merge_events(speech_events, scene_events)
        job.events_count = len(all_events)
        result["layers"]["L2_events"] = {
            "total_events": len(all_events),
            "speech_events": len(speech_events),
            "scene_events": len(scene_events),
        }

        # ── L3: Build recaps ───────────────────────────────────────
        _update_job(job, status="recapping", current_layer="L3_recaps", progress=0.7)
        recaps = build_recaps(all_events, window_s=recap_window_s)
        job.recaps_count = len(recaps)
        result["layers"]["L3_recaps"] = {
            "recap_count": len(recaps),
        }

        # ── L4: Build memory ───────────────────────────────────────
        _update_job(job, status="memorizing", current_layer="L4_memory", progress=0.85)
        memory = build_memory_from_recaps(recaps, media_id=asset.media_id)
        result["layers"]["L4_memory"] = {
            "main_actors": memory.main_actors,
            "themes": memory.inferred_themes,
            "open_loops_count": len(memory.open_loops),
        }

        # ── L5: Compose document ───────────────────────────────────
        _update_job(job, status="composing", current_layer="L5_compose", progress=0.95)
        if output_format is None:
            output_format = select_output_format(memory, all_events)

        document = compose_document(memory, recaps, all_events, output_format=output_format)
        result["layers"]["L5_compose"] = {
            "format": document.format.value,
            "title": document.title,
            "section_count": len(document.sections),
            "text_length": len(document.full_text),
        }
        result["document"] = {
            "format": document.format.value,
            "title": document.title,
            "full_text": document.full_text,
            "sections": document.sections,
        }

        # ── Build and persist canonical artifact bundle ────────────
        artifacts = _build_layer_artifacts(
            asset,
            transcript_payload,
            filter_results,
            all_events,
            recaps,
            memory,
            document,
            job,
        )
        result["artifacts"] = [_artifact_to_dict(artifact) for artifact in artifacts]
        result["artifact_count"] = len(result["artifacts"])

        # ── L6: Vectorstore projection ─────────────────────────────
        # Insert transcript chunks into Milvus for hybrid search.
        # This makes the transcribed media searchable via the same
        # collections/search infrastructure as manually-indexed files.
        _update_job(job, status="indexing", current_layer="L6_vectorstore", progress=0.96)
        vectorstore_result = _insert_into_vectorstore(asset, filter_results, all_events, recaps, memory, document)
        result["layers"]["L6_vectorstore"] = vectorstore_result

        # Store prompts for optional LLM enhancement
        result["prompts"] = {}
        if recaps:
            from media.recaps import build_recap_prompt
            sys_p, user_p = build_recap_prompt(all_events[:20])
            result["prompts"]["recap_sample"] = {"system": sys_p, "user": user_p}

        if recaps:
            mem_sys, mem_user = build_memory_prompt(recaps, media_id=asset.media_id)
            result["prompts"]["memory"] = {"system": mem_sys, "user": mem_user}

        comp_sys, comp_user = build_compose_prompt(memory, recaps, all_events, output_format)
        result["prompts"]["compose"] = {"system": comp_sys, "user": comp_user}

        # ── Final subject line inference ───────────────────────────
        _update_job(job, status="summarizing", current_layer="L7_subject_line", progress=0.98)
        subject_sys, subject_user, _ = build_subject_line_prompt(asset, artifacts, memory, document)
        result["prompts"]["subject_line"] = {"system": subject_sys, "user": subject_user}
        subject_line, subject_details = _generate_subject_line(asset, artifacts, memory, document)
        result["subject_line"] = subject_line
        result["document"]["subject_line"] = subject_line
        result["layers"]["L7_subject_line"] = {
            "subject_line": subject_line,
            **subject_details,
        }
        artifacts.append(DerivedArtifact(
            media_id=asset.media_id,
            kind="subject_line",
            start_s=0.0,
            end_s=asset.duration_s,
            content=subject_line,
            confidence=1.0 if subject_details.get("generator") == "openclaw" else 0.7,
            metadata={
                "layer": "L7",
                "generator": subject_details.get("generator"),
                "model": subject_details.get("model"),
                "source_artifact_count": subject_details.get("source_artifact_count"),
            },
            source_refs=subject_details.get("context_artifact_refs", []),
        ))
        artifacts.sort(key=lambda artifact: (artifact.start_s, artifact.end_s, artifact.kind, artifact.artifact_id))
        result["artifacts"] = [_artifact_to_dict(artifact) for artifact in artifacts]
        result["artifact_count"] = len(result["artifacts"])
        job.artifacts_count = len(artifacts)

        # Persist the canonical result before embedding it into the media file.
        result_path = _save_pipeline_result(asset.media_id, result)
        result["artifact_bundle_path"] = str(result_path)
        sidecar_path = _write_pipeline_sidecar(asset, result)
        if sidecar_path is not None:
            result["artifact_bundle_sidecar_path"] = str(sidecar_path)

        # ── Inject metadata into source file ───────────────────────
        result["injection"] = _inject_metadata_into_file(
            asset,
            memory,
            document,
            transcript_payload=transcript_payload,
            result_path=sidecar_path or result_path,
            subject_line=result.get("subject_line"),
        )
        _save_pipeline_result(asset.media_id, result)
        if sidecar_path is not None:
            _write_pipeline_sidecar(asset, result)

        # ── Done ───────────────────────────────────────────────────
        _update_job(job, status="done", current_layer="", progress=1.0, finished_at=time.time())

        logger.info(
            "Pipeline complete for %s: %d events, %d recaps, format=%s",
            asset.filename, len(all_events), len(recaps), output_format.value,
        )

    except Exception as e:
        _update_job(job, status="error", error=str(e), finished_at=time.time())
        result["error"] = str(e)
        logger.exception("Pipeline failed for %s", path)

    return result


def _artifact_to_dict(artifact: DerivedArtifact) -> dict:
    return {
        "artifact_id": artifact.artifact_id,
        "media_id": artifact.media_id,
        "kind": artifact.kind,
        "start_s": artifact.start_s,
        "end_s": artifact.end_s,
        "content": artifact.content,
        "confidence": artifact.confidence,
        "metadata": artifact.metadata,
        "source_refs": artifact.source_refs,
    }


def _derive_transcript(asset: MediaAsset, job: PipelineJob) -> Optional[dict]:
    """Derive a transcript from audio/video using the configured transcription backend."""
    try:
        import transcription_service
        if not transcription_service.is_available():
            transcription_service.init_transcription_model()
        if not transcription_service.is_available():
            logger.info("Transcription service not available, skipping transcript derivation")
            return None

        transcription, meta, segments = transcription_service.transcribe_media_file(
            asset.path,
            filename=asset.filename,
            word_timestamps=True,
        )
        return {"text": transcription, "meta": meta, "segments": segments}

    except ImportError:
        logger.info("transcription_service not available")
        return None
    except Exception as e:
        logger.warning("Transcript derivation failed for %s: %s", asset.filename, e)
        return None


def _build_layer_artifacts(
    asset: MediaAsset,
    transcript_payload: Optional[dict],
    filter_results: dict,
    events: list,
    recaps: list,
    memory,
    document,
    job: PipelineJob,
) -> list[DerivedArtifact]:
    """Build a single canonical artifact bundle for every pipeline layer."""
    import json as _json

    artifacts: list[DerivedArtifact] = []

    transcript_segments = transcript_payload.get("segments", []) if transcript_payload else []
    transcript_text = transcript_payload.get("text", "") if transcript_payload else ""
    transcript_meta = transcript_payload.get("meta", {}) if transcript_payload else {}
    if transcript_text:
        artifacts.append(DerivedArtifact(
            media_id=asset.media_id,
            kind="transcript",
            start_s=0.0,
            end_s=asset.duration_s,
            content=transcript_text,
            confidence=transcript_meta.get("lang_p", 1.0),
            metadata={"layer": "T", **transcript_meta},
        ))

    for idx, segment in enumerate(filter_results.get("speech_segments", [])):
        artifacts.append(DerivedArtifact(
            media_id=asset.media_id,
            kind="speech_segment",
            start_s=segment.start_s,
            end_s=segment.end_s,
            content=segment.text,
            confidence=segment.confidence,
            metadata={
                "layer": "L1",
                "speaker": segment.speaker,
                "salience_tags": [
                    tag.value if hasattr(tag, "value") else str(tag)
                    for tag in segment.salience_tags
                ],
                "word_timestamps": segment.word_timestamps,
                "segment_index": idx,
                "transcript_segment_count": len(transcript_segments),
            },
            source_refs=[f"speech_{segment.start_s:.2f}"],
        ))

    # ── L1: Scene segments ──────────────────────────────────────────
    for scene in filter_results.get("scenes", []):
        artifacts.append(DerivedArtifact(
            media_id=asset.media_id,
            kind="scene",
            start_s=scene.start_s,
            end_s=scene.end_s,
            content=_json.dumps({
                "scene_score": scene.scene_score,
                "motion_score": scene.motion_score,
                "sharpness_score": scene.sharpness_score,
                "keyframe_path": scene.keyframe_path,
                "ocr_text": scene.ocr_text,
                "labels": scene.labels,
            }),
            confidence=min(1.0, scene.scene_score / 0.5) if scene.scene_score > 0 else 0.5,
            metadata={"layer": "L1"},
        ))

    for idx, keyframe_path in enumerate(filter_results.get("keyframes", [])):
        keyframe_start = float(idx)
        keyframe_end = float(idx)
        if idx < len(filter_results.get("scenes", [])):
            keyframe_start = filter_results["scenes"][idx].start_s
            keyframe_end = filter_results["scenes"][idx].end_s
        artifacts.append(DerivedArtifact(
            media_id=asset.media_id,
            kind="keyframe",
            start_s=keyframe_start,
            end_s=keyframe_end,
            content="",
            confidence=1.0,
            metadata={"layer": "L1", "path": keyframe_path, "index": idx},
            source_refs=[f"keyframe:{keyframe_path}"],
        ))

    # ── L2: Atomic events ───────────────────────────────────────────
    for evt in events:
        artifacts.append(DerivedArtifact(
            media_id=asset.media_id,
            kind="event",
            start_s=evt.time_start,
            end_s=evt.time_end,
            content=evt.text_evidence,
            confidence=evt.confidence,
            metadata={
                "layer": "L2",
                "event_id": evt.event_id,
                "event_type": evt.event_type.value if hasattr(evt.event_type, 'value') else str(evt.event_type),
                "speakers": evt.speakers,
                "visual_entities": evt.visual_entities,
                "salience_tags": [t.value if hasattr(t, 'value') else str(t) for t in evt.salience_tags],
                "entities": evt.metadata.get("entities", []),
            },
            source_refs=evt.source_refs,
        ))

    # ── L3: Recaps ──────────────────────────────────────────────────
    for recap in recaps:
        artifacts.append(DerivedArtifact(
            media_id=asset.media_id,
            kind="recap",
            start_s=recap.time_start,
            end_s=recap.time_end,
            content=recap.recap_text,
            confidence=1.0,
            metadata={
                "layer": "L3",
                "recap_id": recap.recap_id,
                "group_type": recap.group_type,
                "salient_entities": recap.salient_entities,
                "unresolved_questions": recap.unresolved_questions,
                "emotional_tone": recap.emotional_tone,
                "causal_links": recap.causal_links,
                "event_ids": recap.event_ids,
            },
            source_refs=recap.source_refs,
        ))

    # ── L4: Contextual memory ───────────────────────────────────────
    artifacts.append(DerivedArtifact(
        media_id=asset.media_id,
        kind="memory",
        start_s=0.0,
        end_s=asset.duration_s,
        content=_json.dumps({
            "memory_id": memory.memory_id,
            "main_actors": memory.main_actors,
            "timeline_anchors": memory.timeline_anchors,
            "locations": memory.locations,
            "open_loops": memory.open_loops,
            "inferred_themes": memory.inferred_themes,
            "risk_safety_issues": memory.risk_safety_issues,
            "contradictions": memory.contradictions,
            "notable_evidence": memory.notable_evidence,
            "final_takeaways": memory.final_takeaways,
            "recap_ids": memory.recap_ids,
        }),
        confidence=1.0,
        metadata={"layer": "L4", "memory_id": memory.memory_id},
    ))

    # ── L5: Composed document ───────────────────────────────────────
    artifacts.append(DerivedArtifact(
        media_id=asset.media_id,
        kind="document",
        start_s=0.0,
        end_s=asset.duration_s,
        content=document.full_text,
        confidence=1.0,
        metadata={
            "layer": "L5",
            "document_id": document.document_id,
            "format": document.format.value if hasattr(document.format, 'value') else str(document.format),
            "title": document.title,
            "section_count": len(document.sections),
            "memory_id": document.memory_id,
        },
        source_refs=document.source_refs,
    ))

    artifacts.sort(key=lambda artifact: (artifact.start_s, artifact.end_s, artifact.kind, artifact.artifact_id))
    job.artifacts_count = len(artifacts)

    logger.info(
        "Saved %d artifacts for %s (scenes=%d, events=%d, recaps=%d, memory=1, doc=1)",
        job.artifacts_count, asset.filename,
        len(filter_results.get("scenes", [])), len(events), len(recaps),
    )
    return artifacts


def _format_vtt_timestamp(seconds: float) -> str:
    total_ms = max(0, int(round(seconds * 1000)))
    hours = total_ms // 3_600_000
    minutes = (total_ms % 3_600_000) // 60_000
    secs = (total_ms % 60_000) // 1000
    millis = total_ms % 1000
    return f"{hours:02}:{minutes:02}:{secs:02}.{millis:03}"


def _write_transcript_sidecar(asset: MediaAsset, transcript_payload: Optional[dict]) -> Optional[Path]:
    if not transcript_payload:
        return None
    segments = transcript_payload.get("segments") or []
    if not segments:
        return None

    vtt_path = Path(asset.path).with_suffix(".vtt")
    meta = transcript_payload.get("meta", {})
    lines = [
        "WEBVTT",
        "",
        "NOTE",
        f"Source: {asset.path}",
        f"Language: {meta.get('lang', 'en')}",
        "",
    ]
    for segment in segments:
        if isinstance(segment, dict):
            start_s = float(segment.get("start", 0.0) or 0.0)
            end_s = float(segment.get("end", start_s) or start_s)
            text = (segment.get("text") or "").strip()
        else:
            start_s = float(getattr(segment, "start", 0.0) or 0.0)
            end_s = float(getattr(segment, "end", start_s) or start_s)
            text = str(getattr(segment, "text", "") or "").strip()
        if not text:
            continue
        lines.extend([
            f"{_format_vtt_timestamp(start_s)} --> {_format_vtt_timestamp(end_s)}",
            text,
            "",
        ])
    if len(lines) <= 6:
        return None
    vtt_path.write_text("\n".join(lines), encoding="utf-8")
    return vtt_path


def _existing_transcript_sidecar(asset: MediaAsset) -> Optional[Path]:
    vtt_path = Path(asset.path).with_suffix(".vtt")
    if vtt_path.exists() and vtt_path.stat().st_size > 0:
        return vtt_path
    return None


def _count_ffprobe_streams(path: Path, stream_selector: str) -> int:
    import subprocess

    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet",
                "-print_format", "json",
                "-show_streams",
                "-select_streams", stream_selector,
                str(path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return 0
        payload = json.loads(result.stdout or "{}")
        return len(payload.get("streams", []))
    except Exception:
        return 0


def _probe_streams(path: Path) -> list[dict]:
    import subprocess

    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet",
                "-print_format", "json",
                "-show_streams",
                str(path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return []
        payload = json.loads(result.stdout or "{}")
        return payload.get("streams", [])
    except Exception:
        return []


def _find_archivist_embedded_streams(path: Path) -> tuple[list[int], list[int]]:
    subtitle_indexes: list[int] = []
    attachment_indexes: list[int] = []

    for stream in _probe_streams(path):
        try:
            stream_index = int(stream.get("index"))
        except (TypeError, ValueError):
            continue
        tags = stream.get("tags") or {}
        codec_type = stream.get("codec_type")
        if codec_type == "subtitle" and tags.get("title") == "Archivist Transcript":
            subtitle_indexes.append(stream_index)
        if codec_type == "attachment" and tags.get("filename") == "archivist_media_pipeline.json":
            attachment_indexes.append(stream_index)

    return subtitle_indexes, attachment_indexes


def _inject_metadata_into_file(
    asset: MediaAsset,
    memory,
    document,
    transcript_payload: Optional[dict] = None,
    result_path: Optional[Path] = None,
    subject_line: Optional[str] = None,
) -> dict:
    """Inject transcript, artifact bundle, and summary metadata back into the source file."""
    import subprocess

    info = {
        "status": "skipped",
        "transcript_sidecar_path": None,
        "transcript_stream_embedded": False,
        "artifact_bundle_attached": False,
        "summary_tags_written": False,
        "error": None,
    }

    if asset.modality not in (Modality.AUDIO, Modality.VIDEO):
        return info

    src = Path(asset.path)
    if not src.exists():
        info["error"] = f"source file missing: {src}"
        logger.warning("Cannot inject metadata - %s", info["error"])
        return info

    transcript_sidecar = _write_transcript_sidecar(asset, transcript_payload)
    if transcript_sidecar is None:
        transcript_sidecar = _existing_transcript_sidecar(asset)
    if transcript_sidecar:
        info["transcript_sidecar_path"] = str(transcript_sidecar)

    metadata_args = []
    title_text = str(subject_line or (document.title if document else "") or "").strip()
    if title_text:
        metadata_args.extend(["-metadata", f"title={title_text}"])
    if document and document.title and document.title != title_text:
        metadata_args.extend(["-metadata", f"description={document.title}"])

    description_parts = []
    if memory.inferred_themes:
        description_parts.append(f"Themes: {', '.join(memory.inferred_themes)}")
    cleaned_participants = _clean_subject_terms(memory.main_actors, limit=8)
    if cleaned_participants:
        description_parts.append(f"Participants: {', '.join(cleaned_participants)}")
    if memory.open_loops:
        description_parts.append(f"Open questions: {len(memory.open_loops)}")
    if result_path:
        description_parts.append(f"Archivist bundle: {result_path.name}")
    if description_parts:
        metadata_args.extend(["-metadata", f"comment={' | '.join(description_parts)}"])

    if cleaned_participants:
        metadata_args.extend(["-metadata", f"artist={', '.join(cleaned_participants[:5])}"])

    if document and document.format:
        fmt_label = document.format.value if hasattr(document.format, "value") else str(document.format)
        metadata_args.extend(["-metadata", f"genre={fmt_label}"])

    suffix = src.suffix.lower()
    embed_transcript_stream = transcript_sidecar is not None and suffix in {".mkv", ".mp4"}
    attach_artifact_bundle = result_path is not None and suffix == ".mkv"

    if not metadata_args and not embed_transcript_stream and not attach_artifact_bundle:
        return info

    tmp_path = src.with_name(f"{src.stem}.archivist_tmp{src.suffix}")
    try:
        cmd = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-i", str(src),
        ]
        existing_archivist_subtitles, existing_archivist_attachments = _find_archivist_embedded_streams(src)
        subtitle_stream_index = None
        if embed_transcript_stream and transcript_sidecar is not None:
            subtitle_stream_index = max(
                0,
                _count_ffprobe_streams(src, "s") - len(existing_archivist_subtitles),
            )
            cmd.extend(["-i", str(transcript_sidecar)])

        cmd.extend(["-map", "0"])
        if embed_transcript_stream:
            for stream_index in existing_archivist_subtitles:
                cmd.extend(["-map", f"-0:{stream_index}"])
        if attach_artifact_bundle:
            for stream_index in existing_archivist_attachments:
                cmd.extend(["-map", f"-0:{stream_index}"])
        if embed_transcript_stream:
            cmd.extend(["-map", "1:0"])

        if suffix == ".mp4":
            cmd.extend(["-c:v", "copy", "-c:a", "copy"])
            if embed_transcript_stream:
                cmd.extend(["-c:s", "mov_text"])
            else:
                cmd.extend(["-c", "copy"])
        else:
            cmd.extend(["-c", "copy"])

        cmd.extend(["-map_metadata", "0"])
        cmd.extend(metadata_args)

        if embed_transcript_stream and subtitle_stream_index is not None:
            cmd.extend([
                f"-metadata:s:s:{subtitle_stream_index}", "language=eng",
                f"-metadata:s:s:{subtitle_stream_index}", "title=Archivist Transcript",
            ])

        if attach_artifact_bundle and result_path is not None:
            attachment_index = max(
                0,
                _count_ffprobe_streams(src, "t") - len(existing_archivist_attachments),
            )
            cmd.extend([
                "-attach", str(result_path),
                f"-metadata:s:t:{attachment_index}", "mimetype=application/json",
                f"-metadata:s:t:{attachment_index}", "filename=archivist_media_pipeline.json",
            ])

        cmd.append(str(tmp_path))
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=max(300, int(src.stat().st_size / (8 * 1024 * 1024))),
        )
        if result.returncode == 0 and tmp_path.exists() and tmp_path.stat().st_size > 0:
            tmp_path.replace(src)
            info["status"] = "embedded"
            info["summary_tags_written"] = bool(metadata_args)
            info["transcript_stream_embedded"] = embed_transcript_stream
            info["artifact_bundle_attached"] = attach_artifact_bundle
            logger.info("Injected metadata into %s", asset.filename)
            return info

        stderr = (result.stderr or b"").decode("utf-8", errors="ignore")
        info["status"] = "error"
        info["error"] = stderr[:500]
        logger.warning("Metadata injection failed for %s: %s", asset.filename, stderr[:200])
    except Exception as e:
        info["status"] = "error"
        info["error"] = str(e)
        logger.warning("Metadata injection error for %s: %s", asset.filename, e)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()
    return info


def _insert_into_vectorstore(
    asset: MediaAsset,
    filter_results: dict,
    events: list,
    recaps: list,
    memory,
    document,
) -> dict:
    """L6: Insert processed media into Milvus vectorstore.

    Converts the pipeline output into TranscriptChunk objects that slot
    into the existing indexing infrastructure. Uses the same collection
    schema (documents_transcripts) so media transcripts are searchable
    alongside manually-indexed transcript files.

    Creates chunks at multiple levels per the QA retrieval research:
    - Utterance-level (speech segments) for fine-grained answer retrieval
    - Event-level (atomic events) for contextual search
    - Recap-level (60s windows) for broader topic search
    - Document-level (full composed output) for high-level queries

    The hybrid retrieval (dense + BM25 sparse) in the existing search
    infrastructure handles both semantic and keyword matching automatically.
    """
    stats = {"chunks_created": 0, "chunks_inserted": 0, "collection": "", "error": None}

    try:
        from transcripts.chunking import TranscriptChunk
        from hashlib import sha256
        import os

        speech_segments = filter_results.get("speech_segments", [])
        if not speech_segments and not events:
            stats["error"] = "No speech segments or events to index"
            return stats

        source_id = f"media:{asset.media_id}"
        display_path = asset.path
        filehash = asset.file_hash or ""

        chunks: list[TranscriptChunk] = []

        # ── Utterance-level chunks (from speech segments) ───────────
        # These are the fine-grained chunks for answer retrieval.
        # Per QA research: short answer-bearing passages rank better
        # when they're stored as their own chunks rather than buried
        # in large windows.
        for seg in speech_segments:
            text = seg.text.strip()
            if not text or len(text.split()) < 3:
                continue
            chunk_seed = f"{source_id}|0|{int(seg.start_s * 1000)}|{int((seg.end_s - seg.start_s))}|{text[:100]}"
            chunk_id = sha256(chunk_seed.encode()).hexdigest()[:24]
            chunks.append(TranscriptChunk(
                chunk_id=chunk_id,
                source_id=source_id,
                path=display_path,
                text=text,
                t_start_ms=int(seg.start_s * 1000),
                t_end_ms=int(seg.end_s * 1000),
                chunk_duration_s=max(1, int(seg.end_s - seg.start_s)),
                level=0,
                parent_id=None,
                doc_type="media_transcript",
                source_type="media",
                topic_label=None,
                language=None,
                tag="utterance",
            ))

        # ── Event-level chunks (merged speech windows) ──────────────
        # Per QA research: contextual chunk embeddings improve retrieval.
        # Events carry more context than raw utterances.
        for evt in events:
            text = evt.text_evidence.strip()
            if not text or len(text.split()) < 5:
                continue
            chunk_seed = f"{source_id}|1|{int(evt.time_start * 1000)}|{int(evt.time_end - evt.time_start)}|event"
            chunk_id = sha256(chunk_seed.encode()).hexdigest()[:24]
            # Add speaker context to improve retrieval
            context_prefix = ""
            if evt.speakers:
                context_prefix = f"[{', '.join(evt.speakers)}] "
            chunks.append(TranscriptChunk(
                chunk_id=chunk_id,
                source_id=source_id,
                path=display_path,
                text=f"{context_prefix}{text}",
                t_start_ms=int(evt.time_start * 1000),
                t_end_ms=int(evt.time_end * 1000),
                chunk_duration_s=max(1, int(evt.time_end - evt.time_start)),
                level=1,
                parent_id=None,
                doc_type="media_event",
                source_type="media",
                topic_label=evt.event_type.value if hasattr(evt.event_type, 'value') else str(evt.event_type),
                language=None,
                tag=f"event_{evt.event_type.value}" if hasattr(evt.event_type, 'value') else "event",
            ))

        # ── Recap-level chunks (60s window summaries) ───────────────
        # These provide topic-level search coverage.
        for recap in recaps:
            text = recap.recap_text.strip()
            if not text or len(text.split()) < 8:
                continue
            chunk_seed = f"{source_id}|2|{int(recap.time_start * 1000)}|60|recap"
            chunk_id = sha256(chunk_seed.encode()).hexdigest()[:24]
            chunks.append(TranscriptChunk(
                chunk_id=chunk_id,
                source_id=source_id,
                path=display_path,
                text=text,
                t_start_ms=int(recap.time_start * 1000),
                t_end_ms=int(recap.time_end * 1000),
                chunk_duration_s=max(1, int(recap.time_end - recap.time_start)),
                level=2,
                parent_id=None,
                doc_type="media_recap",
                source_type="media",
                topic_label=recap.group_type,
                language=None,
                tag="recap",
            ))

        # ── Document-level chunk (composed output) ──────────────────
        # This gives the high-level summary for broad queries.
        if document and document.full_text and len(document.full_text.split()) >= 10:
            chunk_seed = f"{source_id}|3|0|{int(asset.duration_s)}|doc"
            chunk_id = sha256(chunk_seed.encode()).hexdigest()[:24]
            chunks.append(TranscriptChunk(
                chunk_id=chunk_id,
                source_id=source_id,
                path=display_path,
                text=document.full_text[:65000],
                t_start_ms=0,
                t_end_ms=int(asset.duration_s * 1000),
                chunk_duration_s=max(1, int(asset.duration_s)),
                level=3,
                parent_id=None,
                doc_type="media_document",
                source_type="media",
                topic_label=document.format.value if hasattr(document.format, 'value') else str(document.format),
                language=None,
                tag="doc_chunk",
            ))

        stats["chunks_created"] = len(chunks)

        if not chunks:
            stats["error"] = "No chunks generated from pipeline output"
            return stats

        # ── Insert into Milvus via existing indexing infrastructure ──
        from indexing_service import (
            _ensure_chunk_collection,
            _insert_chunks,
            TRANSCRIPT_COLLECTION,
        )

        embedding_host = os.getenv("EMBEDDING_HOST", "localhost")
        embedding_port = int(os.getenv("EMBEDDING_PORT", "8000"))
        alias = f"media_{asset.media_id[:8]}"

        collection = _ensure_chunk_collection(
            TRANSCRIPT_COLLECTION,
            description="Documents and transcripts",
            alias=alias,
            ip_address=os.getenv("MILVUS_HOST", "localhost"),
        )
        try:
            collection.load()
        except Exception:
            pass

        # Delete any previous chunks for this media asset
        try:
            delete_expr = f'source_id == "media:{asset.media_id}"'
            collection.delete(delete_expr)
        except Exception:
            pass

        inserted = _insert_chunks(
            collection=collection,
            chunks=chunks,
            filehash=filehash,
            embedding_host=embedding_host,
            embedding_port=embedding_port,
        )
        stats["chunks_inserted"] = inserted
        stats["collection"] = TRANSCRIPT_COLLECTION

        from pymilvus import connections
        try:
            connections.disconnect(alias)
        except Exception:
            pass

        logger.info(
            "Vectorstore: inserted %d/%d chunks for %s into %s",
            inserted, len(chunks), asset.filename, TRANSCRIPT_COLLECTION,
        )

    except Exception as e:
        stats["error"] = str(e)
        logger.warning("Vectorstore insertion failed for %s: %s", asset.media_id, e)

    return stats


def _save_pipeline_result(media_id: str, result: dict):
    """Persist pipeline results to disk."""
    PIPELINE_STORE_DIR.mkdir(parents=True, exist_ok=True)
    result_file = PIPELINE_STORE_DIR / f"{media_id}.json"
    # Convert non-serializable objects
    serializable = json.loads(json.dumps(result, default=str))
    result_file.write_text(json.dumps(serializable, indent=2), encoding="utf-8")
    return result_file


def get_pipeline_result(media_id: str) -> Optional[dict]:
    """Load a stored pipeline result."""
    result_file = PIPELINE_STORE_DIR / f"{media_id}.json"
    if not result_file.exists():
        return None
    try:
        return json.loads(result_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


# ── Folder Watcher ──────────────────────────────────────────────────────


def start_watcher(directories: list[str]):
    """Start watching directories for new media files."""
    global _watcher_thread, _watch_dirs
    _watch_dirs = [d for d in directories if Path(d).is_dir()]
    if not _watch_dirs:
        logger.warning("No valid watch directories provided")
        return

    if _watcher_thread and _watcher_thread.is_alive():
        stop_watcher()

    _watcher_stop.clear()
    _watcher_thread = threading.Thread(target=_watcher_loop, daemon=True, name="media-watcher")
    _watcher_thread.start()
    logger.info("Media watcher started for %d directories", len(_watch_dirs))


def stop_watcher():
    """Stop the folder watcher."""
    _watcher_stop.set()
    if _watcher_thread and _watcher_thread.is_alive():
        _watcher_thread.join(timeout=10)
    logger.info("Media watcher stopped")


def _watcher_loop():
    """Background loop that checks watch directories for new media files."""
    processed_hashes: set[str] = set()

    # Load already-processed hashes
    index = _load_assets_index()
    for asset_data in index.values():
        if asset_data.get("file_hash") and _asset_record_complete(asset_data):
            processed_hashes.add(asset_data["file_hash"])

    while not _watcher_stop.is_set():
        for directory in _watch_dirs:
            try:
                _scan_directory(directory, processed_hashes)
            except Exception as e:
                logger.error("Watcher error scanning %s: %s", directory, e)

        _watcher_stop.wait(timeout=WATCH_INTERVAL_S)


def _scan_directory(directory: str, processed_hashes: set[str]):
    """Scan a directory for new media files and process them."""
    from hashlib import sha256

    dir_path = Path(directory)
    index = _load_assets_index()
    complete_paths = {
        str(data.get("path") or ""): data
        for data in index.values()
        if _asset_record_complete(data)
    }
    for file_path in dir_path.rglob("*"):
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in ALL_MEDIA_EXTS:
            continue

        resolved_path = str(file_path.resolve())
        existing_complete = complete_paths.get(resolved_path)
        if existing_complete and existing_complete.get("file_hash"):
            processed_hashes.add(existing_complete["file_hash"])
            continue

        # Quick hash check to avoid reprocessing
        try:
            h = sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    h.update(chunk)
            file_hash = h.hexdigest()
        except OSError:
            continue

        if file_hash in processed_hashes:
            continue

        logger.info("New media file detected: %s", file_path.name)
        try:
            result = process_media_file(str(file_path))
            if not result.get("error"):
                processed_hashes.add(file_hash)
                complete_paths[resolved_path] = {
                    "path": resolved_path,
                    "media_id": result.get("media_id", ""),
                    "file_hash": file_hash,
                }
        except Exception as e:
            logger.error("Failed to process %s: %s", file_path.name, e)
