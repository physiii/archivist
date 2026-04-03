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
    get_artifacts,
    register_asset,
    save_artifact,
)
from media.event_extraction import (
    extract_events_from_scenes,
    extract_events_from_speech,
    merge_events,
)
from media.filtering import (
    detect_scene_changes,
    detect_speech_segments,
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
            "filename": asset.filename,
            "modality": asset.modality.value,
            "duration_s": asset.duration_s,
            "file_hash": asset.file_hash,
        }

        # ── Derive transcription for audio/video ────────────────────
        transcript_segments = None
        if asset.modality in (Modality.AUDIO, Modality.VIDEO):
            transcript_segments = _derive_transcript(asset, job)

        # ── L1: Filter ──────────────────────────────────────────────
        _update_job(job, status="filtering", current_layer="L1_filtering", progress=0.3)
        filter_results = filter_asset(asset, transcript_segments=transcript_segments)
        result["layers"]["L1_filtering"] = {
            "scene_count": len(filter_results.get("scenes", [])),
            "speech_segment_count": len(filter_results.get("speech_segments", [])),
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

        # ── Done ───────────────────────────────────────────────────
        _update_job(job, status="done", current_layer="", progress=1.0, finished_at=time.time())

        # Persist pipeline result
        _save_pipeline_result(asset.media_id, result)

        logger.info(
            "Pipeline complete for %s: %d events, %d recaps, format=%s",
            asset.filename, len(all_events), len(recaps), output_format.value,
        )

    except Exception as e:
        _update_job(job, status="error", error=str(e), finished_at=time.time())
        result["error"] = str(e)
        logger.exception("Pipeline failed for %s", path)

    return result


def _derive_transcript(asset: MediaAsset, job: PipelineJob) -> Optional[list]:
    """Derive a transcript from audio/video using the transcription service."""
    try:
        import transcription_service
        if not transcription_service.is_available():
            logger.info("Transcription service not available, skipping transcript derivation")
            return None

        with open(asset.path, "rb") as f:
            data = f.read()

        content_type = "audio/wav" if asset.path.endswith(".wav") else ""
        transcription, meta, segments = transcription_service.transcribe_audio_bytes(
            data,
            content_type=content_type,
            filename=asset.filename,
        )

        if transcription:
            # Save transcript as artifact
            artifact = DerivedArtifact(
                media_id=asset.media_id,
                kind="transcript",
                start_s=0.0,
                end_s=asset.duration_s,
                content=transcription,
                confidence=meta.get("lang_p", 1.0),
                metadata=meta,
            )
            save_artifact(artifact)
            job.artifacts_count += 1

        return segments

    except ImportError:
        logger.info("transcription_service not available")
        return None
    except Exception as e:
        logger.warning("Transcript derivation failed for %s: %s", asset.filename, e)
        return None


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
    from media.evidence_store import _load_assets_index
    processed_hashes: set[str] = set()

    # Load already-processed hashes
    index = _load_assets_index()
    for asset_data in index.values():
        if asset_data.get("file_hash"):
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
    for file_path in dir_path.rglob("*"):
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in ALL_MEDIA_EXTS:
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
        processed_hashes.add(file_hash)

        try:
            process_media_file(str(file_path))
        except Exception as e:
            logger.error("Failed to process %s: %s", file_path.name, e)
