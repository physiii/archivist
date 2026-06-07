# main.py
from flask import Flask, request, jsonify, send_from_directory, Response
from load import load_to_vectorstore, load_text_to_vectorstore, clear_vectorstore_collection
from search import CollectionLoadError, search_vectorstore
import argparse
import base64
import copy
import json
import logging
import traceback
import math
import re
import subprocess
import threading
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from hashlib import sha256
from html import unescape as html_unescape
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
from zoneinfo import ZoneInfo
try:
    import numpy as np
except Exception:
    np = None
from pymilvus import connections, utility, Collection, DataType
from uuid import uuid4
import os
import sys
from werkzeug.exceptions import HTTPException
from utils import LOCAL_EMBEDDING_MODEL, LOCAL_EMBEDDING_DIM, embed_text_to_vector, validate_embeddings
from xml.etree import ElementTree as ET

from backups_service import (
    BACKUP_ROOT,
    add_backup_target,
    delete_backup_target,
    get_backup_overview,
    get_run_logs,
    list_backup_files,
    list_backup_targets,
    start_backup,
    start_scheduler_best_effort,
    start_target_backup,
    stop_backup,
    update_backup_target,
    update_schedule,
)
from embedding_health import check_embedding_service
from indexing_service import (
    GOOGLE_ARCHIVE_CONTENT_VERSION,
    add_indexing_target,
    delete_indexing_target,
    get_indexing_overview,
    get_indexing_run_logs,
    index_google_archive_content,
    list_indexing_targets,
    scan_indexing_target,
    start_indexing,
    start_scheduler_best_effort as start_indexing_scheduler_best_effort,
    start_target_indexing,
    stop_indexing,
    update_indexing_target,
)
from movietime_items import search_movietime_items, upsert_movietime_items
from chat_store import (
    add_message,
    create_session as create_chat_session,
    delete_session as delete_chat_session,
    get_session_messages,
    init_db as init_chat_db,
    list_sessions,
    update_session_title,
)
import notifications
import transcription_service
import tts_service
from agent_integration import (
    agent_session_key,
    agents_repo_root,
    build_agent_system_message,
    console_agent_id,
    decode_session_ref,
    default_web_session_key,
    encode_session_ref,
    host_workspace,
    inspect_agent_runtime,
    load_agent_messages_from_transcript,
    load_agent_sessions_for_agents,
    load_mcp_resources_for_status,
    load_mcp_tools_for_status,
    load_shared_skills,
    load_team_agents,
    registered_agent_ids,
    resolve_agent_chat_model,
    resolve_agent_executor_token,
    resolve_agent_executor_url,
    resolve_agent_session_file,
    session_kind,
    visible_agent_ids,
)

app = Flask(__name__)
_LOG_LEVEL_NAME = str(os.getenv("ARCHIVIST_LOG_LEVEL", "INFO")).strip().upper() or "INFO"
_LOG_LEVEL = getattr(logging, _LOG_LEVEL_NAME, logging.INFO)
logging.basicConfig(level=_LOG_LEVEL)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)
logging.getLogger("googleapiclient.discovery").setLevel(logging.WARNING)
init_chat_db()


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


_WEB_BACKGROUND_TASKS_ENABLED = _env_flag("ARCHIVIST_ENABLE_WEB_BACKGROUND_TASKS", default=True)
try:
    GLOBAL_SEARCH_COLLECTION_LOAD_TIMEOUT = max(1.0, float(os.getenv("GLOBAL_SEARCH_COLLECTION_LOAD_TIMEOUT", "5")))
except (TypeError, ValueError):
    GLOBAL_SEARCH_COLLECTION_LOAD_TIMEOUT = 5.0

if _WEB_BACKGROUND_TASKS_ENABLED:
    # Start backup/indexing schedulers once (best-effort; use file locks).
    start_scheduler_best_effort()
    start_indexing_scheduler_best_effort()
else:
    logging.info("Archivist web background tasks disabled: skipping backup and indexing schedulers")

# Google import scheduler is started at module tail (after its function is defined).

# Initialize transcription service (non-blocking, will log if GPU unavailable)
try:
    transcription_service.init_transcription_model()
except Exception as e:
    logging.warning("Transcription service init failed: %s", e)

# Allow the UI to be served from a different dev origin (Vite preview/dev).
@app.after_request
def _add_cors_headers(response):
    response.headers.setdefault("Access-Control-Allow-Origin", "*")
    response.headers.setdefault("Access-Control-Allow-Headers", "Content-Type, Authorization")
    response.headers.setdefault("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
    return response

@app.route("/api/<path:_path>", methods=["OPTIONS"])
def _api_options(_path: str):
    return ("", 204)

@app.route("/vectorstore", methods=["OPTIONS"])
def _vectorstore_options():
    return ("", 204)

# Get service host values from environment variables
MILVUS_HOST = os.environ.get('MILVUS_HOST', 'localhost')
try:
    MILVUS_CONNECT_TIMEOUT = float(os.environ.get("MILVUS_CONNECT_TIMEOUT", "3"))
except (TypeError, ValueError):
    MILVUS_CONNECT_TIMEOUT = 3.0
try:
    MILVUS_LOAD_TIMEOUT = float(os.environ.get("MILVUS_LOAD_TIMEOUT", "60"))
except (TypeError, ValueError):
    MILVUS_LOAD_TIMEOUT = 60.0
EMBEDDING_HOST = os.environ.get('EMBEDDING_HOST', 'localhost')
EMBEDDING_PORT = int(os.environ.get('EMBEDDING_PORT', '8000'))
_STATUS_CACHE_LOCK = threading.Lock()
_STATUS_CACHE: dict[str, tuple[float, dict]] = {}


_STATUS_CACHE_REFRESHING: set = set()


def _cached_status_payload(key: str, ttl_seconds: float, builder):
    now = time.time()
    with _STATUS_CACHE_LOCK:
        cached = _STATUS_CACHE.get(key)
        if cached and (now - cached[0]) <= ttl_seconds:
            return copy.deepcopy(cached[1])
    # If we have stale data, return it immediately and refresh in background
    if cached and key not in _STATUS_CACHE_REFRESHING:
        _STATUS_CACHE_REFRESHING.add(key)
        def _refresh():
            try:
                payload = builder()
                with _STATUS_CACHE_LOCK:
                    _STATUS_CACHE[key] = (time.time(), copy.deepcopy(payload))
            finally:
                _STATUS_CACHE_REFRESHING.discard(key)
        threading.Thread(target=_refresh, daemon=True).start()
        return copy.deepcopy(cached[1])
    # No cached data at all — must block
    payload = builder()
    with _STATUS_CACHE_LOCK:
        _STATUS_CACHE[key] = (time.time(), copy.deepcopy(payload))
    _STATUS_CACHE_REFRESHING.discard(key)
    return payload

@app.route('/healthz', methods=['GET'])
def healthz():
    """Fast liveness + CUDA/transcription check for the container healthcheck.

    Deliberately avoids the heavy subsystem probes in /health (Milvus, embeddings,
    Google) so the docker healthcheck reflects THIS container's GPU/transcription
    health and server liveness — not external-dependency latency. Returns 200 when
    healthy, 503 when CUDA is lost or transcription has fallen back to CPU.
    """
    out: dict = {"status": "ok"}
    try:
        import gpu_watchdog
        gs = gpu_watchdog.status()
        out["gpu"] = gs.get("state", "unknown")
        if gs.get("state") == "lost":
            out["status"] = "unhealthy"
            out["gpu_error"] = gs.get("last_error")
    except Exception as exc:
        out["gpu"] = "error"
        out["gpu_probe_error"] = str(exc)[:200]
    try:
        t = transcription_service.get_status()
        dev = str(t.get("device") or "")
        out["transcription_device"] = dev or None
        out["transcription_available"] = bool(t.get("available"))
        # Only fail on a confirmed CPU fallback (available but not on CUDA); a
        # not-yet-loaded model at idle startup must NOT mark the container down.
        if bool(t.get("available")) and dev and dev != "cuda":
            out["status"] = "unhealthy"
            out["transcription"] = "cpu_fallback"
    except Exception as exc:
        out["transcription"] = "error"
        out["transcription_error"] = str(exc)[:200]
    return jsonify(out), (200 if out["status"] == "ok" else 503)


@app.route('/health', methods=['GET'])
def health_check():
    def _build_health_payload() -> dict:
        components: dict[str, dict] = {}
        overall = "healthy"

        try:
            alias = _milvus_alias("health")
            _milvus_connect(alias)
            connections.disconnect(alias)
            components["milvus"] = {"status": "ok"}
        except Exception as exc:
            components["milvus"] = {"status": "error", "error": str(exc)[:200]}
            overall = "degraded"

        try:
            embedding_status = _cached_status_payload(
                "embedding_service",
                30,
                lambda: check_embedding_service(
                    host=EMBEDDING_HOST,
                    port=EMBEDDING_PORT,
                    model=LOCAL_EMBEDDING_MODEL,
                ),
            )
            components["embeddings"] = embedding_status
            if embedding_status.get("status") != "ok":
                overall = "unhealthy"
        except Exception as exc:
            components["embeddings"] = {
                "status": "error",
                "severity": "error",
                "model": LOCAL_EMBEDDING_MODEL,
                "error": str(exc)[:200],
            }
            overall = "unhealthy"

        try:
            summary = _google_archive_summary()
            last_imported = str(summary.get("lastImportedAt") or "").strip()
            if last_imported:
                dt = datetime.fromisoformat(last_imported)
                hours = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
                stale = hours > 4
                components["google_import"] = {
                    "status": "stale" if stale else "ok",
                    "severity": "warning" if stale else "ok",
                    "hours_since": round(hours, 1),
                    "last_imported_at": last_imported,
                }
            else:
                components["google_import"] = {"status": "no_data", "severity": "warning"}
        except Exception as exc:
            components["google_import"] = {"status": "error", "severity": "warning", "error": str(exc)[:200]}

        try:
            from media.pipeline import pipeline_compat_status
            compat = pipeline_compat_status()
            stale_count = compat.get("stale", 0)
            broken_count = compat.get("broken", 0)
            if broken_count > 0:
                components["media_pipeline"] = {
                    "status": "broken",
                    "severity": "warning",
                    "stale": stale_count,
                    "broken": broken_count,
                    "current": compat.get("current", 0),
                }
            elif stale_count > 0:
                components["media_pipeline"] = {
                    "status": "stale",
                    "severity": "warning",
                    "stale": stale_count,
                    "broken": broken_count,
                    "current": compat.get("current", 0),
                }
            else:
                components["media_pipeline"] = {"status": "ok", "severity": "ok", "current": compat.get("current", 0), "broken": broken_count}
        except Exception as exc:
            components["media_pipeline"] = {"status": "error", "severity": "warning", "error": str(exc)[:200]}

        try:
            t_status = transcription_service.get_status()
            t_device = str(t_status.get("device") or "not_loaded")
            t_available = bool(t_status.get("available"))
            gpu = t_status.get("gpu") or {}
            entry: dict = {
                "device": t_device,
                "device_index": t_status.get("device_index"),
                "model": t_status.get("model"),
                "local_model": t_status.get("local_model"),
                "compute_type": t_status.get("local_compute_type") or t_status.get("compute_type"),
                "provider": t_status.get("provider"),
                "available": t_available,
                "gpu_available": bool(gpu.get("available")),
                "gpu_device_count": gpu.get("device_count"),
                "gpu_device_names": gpu.get("device_names"),
                "nvidia_visible_devices": gpu.get("nvidia_visible_devices"),
                "error": t_status.get("error") or (t_status.get("backends", {}).get("local", {}).get("error")),
            }
            if not t_available:
                entry["status"] = "error"
                entry["severity"] = "error"
                overall = "unhealthy"
            elif t_device != "cuda":
                entry["status"] = "cpu_fallback"
                entry["severity"] = "error"
                overall = "unhealthy"
            else:
                entry["status"] = "ok"
                entry["severity"] = "ok"
            components["transcription"] = entry
        except Exception as exc:
            components["transcription"] = {
                "status": "error",
                "severity": "error",
                "error": str(exc)[:200],
            }
            overall = "unhealthy"

        try:
            backup_files = list_backup_files()
            if backup_files:
                latest = backup_files[0]
                modified = str(latest.get("modified_at") or "").strip()
                if modified:
                    dt = datetime.fromisoformat(modified)
                    hours = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
                    stale = hours > 26
                    components["backups"] = {
                        "status": "stale" if stale else "ok",
                        "severity": "warning" if stale else "ok",
                        "hours_since": round(hours, 1),
                        "latest": latest.get("name"),
                    }
                else:
                    components["backups"] = {"status": "ok", "severity": "ok", "count": len(backup_files)}
            else:
                components["backups"] = {"status": "no_data", "severity": "warning"}
        except Exception as exc:
            components["backups"] = {"status": "error", "severity": "warning", "error": str(exc)[:200]}

        try:
            import health_monitor
            hs = health_monitor.status()
            worst = "ok"
            for info in hs.get("sources", {}).values():
                if info["status"] == "down":
                    worst = "error"; break
                if info["status"] in ("stale", "unknown") and worst != "error":
                    worst = "warning"
            components["source_ingest"] = {
                "status": worst,
                "severity": worst,
                "sources": hs.get("sources", {}),
                "channels": hs.get("channels", {}),
            }
            if worst == "error":
                overall = "unhealthy"
        except Exception as exc:
            components["source_ingest"] = {"status": "error", "severity": "warning", "error": str(exc)[:200]}

        try:
            import gpu_watchdog
            gs = gpu_watchdog.status()
            gpu_state = gs.get("state", "unknown")
            if gpu_state == "lost":
                components["gpu"] = {
                    "status": "lost",
                    "severity": "error",
                    "error": gs.get("last_error"),
                    "lost_since_ts": gs.get("lost_since_ts"),
                    "loss_count": gs.get("loss_count"),
                    "device_name": gs.get("device_name"),
                }
                overall = "unhealthy"
            elif gpu_state == "ok":
                components["gpu"] = {
                    "status": "ok",
                    "severity": "ok",
                    "device_name": gs.get("device_name"),
                }
            else:
                components["gpu"] = {"status": "unknown", "severity": "warning"}
        except Exception as exc:
            components["gpu"] = {"status": "error", "severity": "warning", "error": str(exc)[:200]}

        return {"status": overall, "components": components}

    payload = _cached_status_payload("health", 60, _build_health_payload)
    return jsonify(payload), 200


@app.route("/api/notifications/test", methods=["POST"])
def api_notifications_test():
    """Fire a test alert through all configured notification channels."""
    body = request.get_json(force=True, silent=True) or {}
    title = str(body.get("title") or "Archivist test alert").strip()
    message = str(body.get("message") or "This is a test notification from Archivist.").strip()
    severity = str(body.get("severity") or "info").strip()
    result = notifications.send_all(title, message, severity)
    return jsonify({
        "ok": True,
        "channels": result,
        "configured": notifications.channels_configured(),
    })


@app.route("/api/embeddings/health", methods=["GET"])
def api_embeddings_health():
    payload = check_embedding_service(
        host=request.args.get("host") or EMBEDDING_HOST,
        port=request.args.get("port") or EMBEDDING_PORT,
        model=request.args.get("model") or LOCAL_EMBEDDING_MODEL,
    )
    status_code = 200 if payload.get("status") == "ok" else 503
    return jsonify(payload), status_code

def _milvus_alias(prefix: str = "api") -> str:
    return f"{prefix}_{uuid4().hex}"

def _milvus_connect(alias: str, host: str | None = None) -> None:
    connections.connect(
        alias,
        host=host or MILVUS_HOST,
        port="19530",
        timeout=MILVUS_CONNECT_TIMEOUT,
    )

def _milvus_disconnect(alias: str) -> None:
    try:
        connections.disconnect(alias)
    except Exception:
        pass


def _start_vectorstore_preload() -> None:
    raw = os.getenv("VECTORSTORE_PRELOAD_COLLECTIONS", "")
    requested = [item.strip() for item in raw.split(",") if item.strip()]
    if not requested:
        return

    def _worker() -> None:
        alias = _milvus_alias("preload")
        try:
            _milvus_connect(alias)
            for requested_name in requested:
                candidates = [requested_name]
                if requested_name.startswith("documents_"):
                    logical = requested_name.removeprefix("documents_")
                    if logical:
                        candidates.append(logical)
                else:
                    candidates.append(f"documents_{requested_name}")
                raw_name = next(
                    (
                        candidate
                        for candidate in candidates
                        if utility.has_collection(candidate, using=alias, timeout=MILVUS_CONNECT_TIMEOUT)
                    ),
                    None,
                )
                if not raw_name:
                    app.logger.warning("Vectorstore preload skipped missing collection %s", requested_name)
                    continue
                try:
                    if _milvus_load_state_label(raw_name, alias) == "loaded":
                        app.logger.info("Vectorstore preload found %s already loaded", raw_name)
                        continue
                    coll = Collection(name=raw_name, using=alias)
                    started = time.time()
                    coll.load(timeout=MILVUS_LOAD_TIMEOUT)
                    utility.wait_for_loading_complete(raw_name, using=alias, timeout=MILVUS_LOAD_TIMEOUT)
                    app.logger.info("Vectorstore preloaded %s in %.1fs", raw_name, time.time() - started)
                except Exception as exc:
                    app.logger.warning("Vectorstore preload failed for %s: %s", raw_name, exc)
        finally:
            _milvus_disconnect(alias)

    threading.Thread(target=_worker, name="vectorstore-preload", daemon=True).start()

def _logical_collection_name(raw: str) -> str:
    return raw.removeprefix("documents_") if raw.startswith("documents_") else raw


def _resolve_collection_raw_name(name: str, alias: str) -> str | None:
    clean = str(name or "").strip()
    if not clean:
        return None
    candidates = [clean]
    if clean.startswith("documents_"):
        logical = clean.removeprefix("documents_")
        if logical:
            candidates.append(logical)
    else:
        candidates.append(f"documents_{clean}")
    seen: set[str] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        try:
            if utility.has_collection(candidate, using=alias, timeout=MILVUS_CONNECT_TIMEOUT):
                return candidate
        except Exception:
            continue
    return None

def _dtype_name(value) -> str:
    try:
        raw = int(value)
        return DataType(raw).name
    except Exception:
        try:
            return str(getattr(value, "name"))
        except Exception:
            return str(value)

def _as_int(value, default=None):
    if value is None:
        return default
    try:
        return int(value)
    except Exception:
        return default

def _as_float(value, default=None):
    if value is None:
        return default
    try:
        return float(value)
    except Exception:
        return default

def _build_search_options(payload: dict):
    return {
        "metric_type": payload.get("metric_type"),
        "max_distance": _as_float(payload.get("max_distance")),
        "nprobe": _as_int(payload.get("nprobe")),
        "hybrid_fusion": payload.get("hybrid_fusion"),
        "hybrid_dense_weight": _as_float(payload.get("hybrid_dense_weight")),
        "hybrid_sparse_weight": _as_float(payload.get("hybrid_sparse_weight")),
        "hybrid_rrf_k": _as_int(payload.get("hybrid_rrf_k")),
    }


def _prefers_lower_distance_for_response(mode: str, metric_type: str | None) -> bool:
    mode_norm = str(mode or "dense").strip().lower()
    if mode_norm in {"hybrid", "bm25", "sparse"}:
        return False
    metric = str(metric_type or "COSINE").strip().upper()
    return metric in {"L2", "COSINE"}

def _vector_dim_from_collection(collection: Collection) -> int | None:
    try:
        for field in collection.schema.fields:
            if getattr(field, "name", "") == "vector":
                params = getattr(field, "params", {}) or {}
                dim = _as_int(params.get("dim"))
                if dim and dim > 0:
                    return dim
    except Exception:
        pass
    return None

def _vector_index_metric_from_collection(collection: Collection) -> str | None:
    try:
        for index in (collection.indexes or []):
            if getattr(index, "field_name", "") != "vector":
                continue
            params = getattr(index, "params", {}) or {}
            metric = params.get("metric_type")
            if metric:
                return str(metric).strip().upper()
    except Exception:
        pass
    return None

def _milvus_load_state_label(collection_name: str, alias: str) -> str:
    try:
        state = utility.load_state(collection_name, using=alias, timeout=1)
    except Exception:
        return "unknown"
    return str(state).split(".")[-1].lower()

_start_vectorstore_preload()

def _vector_norm(values: list[float]) -> float:
    return math.sqrt(sum(v * v for v in values))

def _cosine_similarity(a: list[float], b: list[float]) -> float | None:
    if not a or not b or len(a) != len(b):
        return None
    denom = _vector_norm(a) * _vector_norm(b)
    if denom <= 0:
        return None
    return max(-1.0, min(1.0, sum(x * y for x, y in zip(a, b)) / denom))

def _l2_distance(a: list[float], b: list[float]) -> float | None:
    if not a or not b or len(a) != len(b):
        return None
    return math.sqrt(sum((x - y) * (x - y) for x, y in zip(a, b)))

def _metric_distance(metric_type: str, vector: list[float], query_vector: list[float], cosine_sim: float | None) -> float | None:
    metric = str(metric_type or "COSINE").strip().upper()
    if metric == "L2":
        return _l2_distance(vector, query_vector)
    if metric == "COSINE":
        if cosine_sim is None:
            cosine_sim = _cosine_similarity(vector, query_vector)
        return None if cosine_sim is None else max(0.0, 1.0 - cosine_sim)
    return None

def _sample_vector_dimensions(values: list[float], target_dim: int) -> list[float]:
    if not values:
        return values
    if len(values) <= target_dim:
        return [float(v) for v in values]
    if target_dim <= 1:
        return [float(values[0])]
    out = []
    last = len(values) - 1
    for i in range(target_dim):
        src_idx = int(round((i / (target_dim - 1)) * last))
        out.append(float(values[src_idx]))
    return out


def _normalize_matrix_rows(matrix):
    if np is None or matrix.size == 0:
        return matrix
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms = np.maximum(norms, 1e-9)
    return matrix / norms

def _normalize_vector_row(vector):
    if np is None:
        return vector
    norm = float(np.linalg.norm(vector))
    if norm <= 1e-9:
        return vector
    return vector / norm

def _append_orthonormal_axis(existing_axes: list, candidate, axis_count: int) -> bool:
    if np is None:
        return False
    if candidate is None or candidate.size == 0:
        return False
    axis = candidate.astype(np.float32, copy=True)
    for prev in existing_axes:
        axis = axis - float(np.dot(axis, prev)) * prev
    norm = float(np.linalg.norm(axis))
    if norm <= 1e-7:
        return False
    existing_axes.append(axis / norm)
    return len(existing_axes) >= axis_count

def _project_embedding_preview(
    vectors: list[list[float]],
    preview_dim_target: int,
    query_vector: list[float] | None = None,
    metric_type: str | None = None,
):
    if not vectors:
        return {
            "vectors": [],
            "query_vector": _sample_vector_dimensions(query_vector or [], preview_dim_target) if query_vector else None,
            "axis_labels": [f"Axis {idx + 1}" for idx in range(preview_dim_target)],
            "method": "sampled_dimensions",
        }

    if np is None:
        return {
            "vectors": [_sample_vector_dimensions(vector, preview_dim_target) for vector in vectors],
            "query_vector": _sample_vector_dimensions(query_vector or [], preview_dim_target) if query_vector else None,
            "axis_labels": [f"Axis {idx + 1}" for idx in range(preview_dim_target)],
            "method": "sampled_dimensions",
        }

    matrix = np.asarray(vectors, dtype=np.float32)
    query = np.asarray(query_vector, dtype=np.float32) if query_vector is not None else None
    metric = str(metric_type or "COSINE").strip().upper()
    if metric in {"COSINE", "IP"}:
        matrix = _normalize_matrix_rows(matrix)
        if query is not None:
            query = _normalize_vector_row(query)

    fit_origin = matrix.mean(axis=0, keepdims=True)
    centered = matrix - fit_origin
    query_centered = (query - fit_origin[0]) if query is not None else None

    fit_matrix = centered
    max_fit_rows = 192
    if centered.shape[0] > max_fit_rows:
        fit_indices = np.linspace(0, centered.shape[0] - 1, num=max_fit_rows, dtype=np.int32)
        fit_matrix = centered[fit_indices]

    axes = []
    axis_labels: list[str] = []
    method = "query_origin_global_pca" if query is not None else "pca"

    if fit_matrix.shape[0] > 0 and fit_matrix.shape[1] > 0:
        try:
            _, _, vh = np.linalg.svd(fit_matrix, full_matrices=False)
            for candidate in vh:
                done = _append_orthonormal_axis(axes, candidate, preview_dim_target)
                if len(axis_labels) < len(axes):
                    axis_labels.append(f"Semantic PC {len(axis_labels) + 1}")
                if done:
                    break
        except Exception:
            pass

    if len(axes) < preview_dim_target:
        basis = np.eye(matrix.shape[1], dtype=np.float32)
        for candidate in basis:
            done = _append_orthonormal_axis(axes, candidate, preview_dim_target)
            if len(axis_labels) < len(axes):
                axis_labels.append(f"Axis {len(axis_labels) + 1}")
            if done:
                break

    axis_matrix = np.stack(axes[:preview_dim_target], axis=1).astype(np.float32, copy=False)
    projected = centered @ axis_matrix
    query_projected = (query_centered @ axis_matrix) if query_centered is not None else None
    if query_projected is not None:
        projected = projected - query_projected
        query_projected = np.zeros(preview_dim_target, dtype=np.float32)

    scale_source = projected
    scales = np.percentile(np.abs(scale_source), 90, axis=0)
    scales = np.maximum(scales, 1e-6)
    projected = projected / scales
    if query_projected is not None:
        query_projected = query_projected / scales

    return {
        "vectors": projected.astype(np.float32).tolist(),
        "query_vector": query_projected.astype(np.float32).tolist() if query_projected is not None else None,
        "axis_labels": axis_labels[:preview_dim_target],
        "method": method,
    }

def _pick_first_value(row: dict, keys: list[str]):
    for key in keys:
        if key in row and row.get(key) not in (None, ""):
            return row.get(key)
    return None

@app.route("/api/collections", methods=["GET"])
def api_list_collections():
    include_stats = str(request.args.get("include_stats", "false")).strip().lower() in {"1", "true", "yes"}
    alias = _milvus_alias("collections")
    try:
        _milvus_connect(alias)
        names = utility.list_collections(using=alias, timeout=MILVUS_CONNECT_TIMEOUT)
        out = []
        for raw_name in sorted(names):
            item = {"name": _logical_collection_name(raw_name), "raw_name": raw_name}
            if include_stats:
                try:
                    coll = Collection(name=raw_name, using=alias)
                    fields = []
                    vector_dim = None
                    has_sparse = False
                    for f in coll.schema.fields:
                        params = getattr(f, "params", {}) or {}
                        if f.name == "vector":
                            vector_dim = params.get("dim")
                        if f.name == "sparse":
                            has_sparse = True
                        fields.append(
                            {
                                "name": f.name,
                                "dtype": _dtype_name(getattr(f, "dtype", "")),
                                "params": params,
                                "is_primary": bool(getattr(f, "is_primary", False)),
                                "auto_id": bool(getattr(f, "auto_id", False)),
                            }
                        )
                    indexes = []
                    try:
                        for ix in (coll.indexes or []):
                            ix_params = getattr(ix, "params", {}) or {}
                            indexes.append(
                                {
                                    "field": getattr(ix, "field_name", None),
                                    "index_type": ix_params.get("index_type"),
                                    "metric_type": ix_params.get("metric_type"),
                                    "params": ix_params.get("params") if isinstance(ix_params.get("params"), dict) else ix_params,
                                }
                            )
                    except Exception:
                        pass
                    item.update(
                        {
                            "num_entities": int(getattr(coll, "num_entities", 0) or 0),
                            "fields": fields,
                            "indexes": indexes,
                            "has_sparse": has_sparse,
                            "vector_dim": vector_dim,
                        }
                    )
                except Exception as e:
                    item["stats_error"] = str(e)
            out.append(item)
        return jsonify({"collections": out})
    finally:
        _milvus_disconnect(alias)

@app.route("/api/collections/<name>", methods=["GET"])
def api_get_collection(name: str):
    alias = _milvus_alias("collection")
    try:
        _milvus_connect(alias)
        raw_name = _resolve_collection_raw_name(name, alias)
        if not raw_name:
            return jsonify({"error": "Not found"}), 404
        coll = Collection(name=raw_name, using=alias)
        fields = []
        for f in coll.schema.fields:
            fields.append(
                {
                    "name": f.name,
                    "dtype": _dtype_name(getattr(f, "dtype", "")),
                    "params": getattr(f, "params", {}) or {},
                    "is_primary": bool(getattr(f, "is_primary", False)),
                    "auto_id": bool(getattr(f, "auto_id", False)),
                }
            )
        return jsonify(
            {
                "name": _logical_collection_name(raw_name),
                "raw_name": raw_name,
                "num_entities": int(getattr(coll, "num_entities", 0) or 0),
                "fields": fields,
            }
        )
    finally:
        _milvus_disconnect(alias)

@app.route("/api/collections/<name>/search", methods=["POST"])
def api_search_collection(name: str):
    payload = request.json or {}
    query = payload.get("query")
    if not query:
        return jsonify({"error": "No query provided"}), 400
    limit = int(payload.get("limit", 10))
    mode = payload.get("mode", "dense")
    embedding_model = payload.get("model")
    unique = bool(payload.get("unique", False))
    path_filter = payload.get("path", "")
    ip_address = payload.get("ip_address", MILVUS_HOST)
    embedding_host = payload.get("embedding_host", EMBEDDING_HOST)
    embedding_port = payload.get("embedding_port", EMBEDDING_PORT)
    search_options = _build_search_options(payload)
    try:
        results = search_vectorstore(
            query,
            limit=limit,
            path_filter=path_filter,
            unique=unique,
            mode=mode,
            collection_name=name,
            embedding_model=embedding_model,
            ip_address=ip_address,
            embedding_host=embedding_host,
            embedding_port=embedding_port,
            **search_options,
        )
        return jsonify({"results": results})
    except CollectionLoadError as e:
        return jsonify({"error": "Collection unavailable", "details": str(e)}), 503
    except Exception as e:
        app.logger.exception("Collection search failed for '%s'", name)
        return jsonify({"error": "Search failed", "details": str(e)}), 502

@app.route("/api/collections/<name>/embeddings-preview", methods=["GET"])
def api_collection_embeddings_preview(name: str):
    alias = _milvus_alias("embeddings_preview")
    coll = None
    limit = max(10, min(_as_int(request.args.get("limit"), 1000) or 1000, 10000))
    offset = max(0, _as_int(request.args.get("offset"), 0) or 0)
    query = (request.args.get("query") or "").strip()
    metric_type = str(request.args.get("metric_type") or "").strip().upper()
    preview_dim_target = _as_int(request.args.get("preview_dim"), 3) or 3
    preview_dim_target = max(3, min(preview_dim_target, 12))
    embedding_host = request.args.get("embedding_host", EMBEDDING_HOST)
    embedding_port = _as_int(request.args.get("embedding_port"), EMBEDDING_PORT) or EMBEDDING_PORT

    try:
        _milvus_connect(alias)
        raw_name = _resolve_collection_raw_name(name, alias)
        if not raw_name:
            return jsonify({"error": "Not found"}), 404

        coll = Collection(name=raw_name, using=alias)
        # Milvus may unload collections during heavy ingest; ensure it's loaded before query.
        if _milvus_load_state_label(raw_name, alias) != "loaded":
            try:
                coll.load(timeout=MILVUS_LOAD_TIMEOUT)
                utility.wait_for_loading_complete(raw_name, using=alias, timeout=MILVUS_LOAD_TIMEOUT)
            except Exception as exc:
                state = _milvus_load_state_label(raw_name, alias)
                return jsonify(
                    {
                        "error": "Collection unavailable",
                        "details": (
                            f"Collection {raw_name} could not be loaded for embeddings preview "
                            f"(state={state}). Milvus may be memory constrained: {exc}"
                        ),
                    }
                ), 503
        vector_dim = _vector_dim_from_collection(coll)
        vector_index_metric = _vector_index_metric_from_collection(coll)
        effective_metric_type = metric_type or vector_index_metric or "COSINE"
        field_names = {f.name for f in coll.schema.fields}
        if "vector" not in field_names:
            return jsonify({"error": "Collection does not contain a 'vector' field"}), 422

        output_fields = []
        for field in coll.schema.fields:
            field_name = getattr(field, "name", "")
            if not field_name or field_name in {"id", "vector", "sparse"}:
                continue
            output_fields.append(field_name)
        output_fields.insert(0, "vector")

        query_error = None
        query_point = None
        query_vector_full = None
        if query:
            try:
                query_vectors = embed_text_to_vector(
                    [query],
                    LOCAL_EMBEDDING_MODEL,
                    is_local=True,
                    embedding_host=embedding_host,
                    embedding_port=embedding_port,
                )
                expected_dim = vector_dim or 0
                validated = validate_embeddings(query_vectors, expected_dim)
                query_vector_full = validated[0] if validated else None
                if query_vector_full is None:
                    query_error = "Could not generate a query embedding with matching dimensions."
            except Exception as e:
                query_error = f"Query embedding failed: {str(e)}"

        started = time.time()
        rows = []
        seen_row_ids: set[str] = set()

        def _append_preview_row(row: dict) -> None:
            row_id = str(row.get("id"))
            if not row_id or row_id in seen_row_ids:
                return
            seen_row_ids.add(row_id)
            rows.append(row)

        if query_vector_full is not None:
            try:
                neighbor_limit = min(max(limit // 3, 200), max(limit - 50, 1))
                search_rows = coll.search(
                    data=[[float(v) for v in query_vector_full]],
                    anns_field="vector",
                    param={"metric_type": effective_metric_type, "params": {"nprobe": 16}},
                    limit=min(max(offset + neighbor_limit, neighbor_limit), 10000),
                    output_fields=output_fields,
                )
                for hits in search_rows or []:
                    for hit in hits:
                        row = {"id": hit.id}
                        for field_name in output_fields:
                            row[field_name] = hit.get(field_name)
                        _append_preview_row(row)
            except Exception as e:
                app.logger.exception("Query-centered embeddings preview search failed for %s", raw_name)
                query_error = f"Preview neighborhood search failed: {str(e)}"
                rows = []
                seen_row_ids.clear()

        context_target = max(offset + limit, limit)
        if len(rows) < context_target:
            iterator = None
            context_pool = []
            try:
                iterator = coll.query_iterator(
                    batch_size=min(128, max(16, limit)),
                    limit=min(max(context_target * 3, context_target), 6000),
                    expr="id >= 0",
                    output_fields=output_fields,
                    timeout=25,
                )
                while len(context_pool) < min(max(context_target * 3, context_target), 6000):
                    batch_rows = iterator.next()
                    if not batch_rows:
                        break
                    context_pool.extend(batch_rows)
            finally:
                if iterator is not None:
                    try:
                        iterator.close()
                    except Exception:
                        pass

            if query_vector_full is None:
                candidate_rows = context_pool
            else:
                # Blend query-nearest rows with a stable background sample so searched views
                # still make sense relative to the default plot context the user saw first.
                step = max(1, len(context_pool) // max(context_target - len(rows), 1))
                candidate_rows = context_pool[::step]
                if len(candidate_rows) < (context_target - len(rows)):
                    candidate_rows = context_pool

            for row in candidate_rows:
                _append_preview_row(row)
                if len(rows) >= context_target:
                    break

        if offset > 0:
            rows = rows[offset : offset + limit]
        else:
            rows = rows[:limit]

        points = []
        full_vectors: list[list[float]] = []

        for row in rows:
            row_vector = row.get("vector")
            if not isinstance(row_vector, list) or not row_vector:
                continue
            full_vector = [float(v) for v in row_vector]
            text_raw = row.get("text") or row.get("snippet") or ""
            text = str(text_raw)[:180]
            metadata = {
                key: value
                for key, value in row.items()
                if key not in {"id", "vector", "sparse", "text", "snippet", "hash", "path", "embedding_model", "creation_date"}
            }
            label_value = _pick_first_value(row, ["label", "labels", "class", "category", "topic"])
            cluster_value = _pick_first_value(row, ["cluster", "cluster_id", "cluster_label", "topic_cluster"])
            density_value = _as_float(_pick_first_value(row, ["density", "density_score"]))
            outlier_value = _as_float(_pick_first_value(row, ["outlier", "outlier_score", "anomaly_score"]))
            point = {
                "id": row.get("id"),
                "vector": [],
                "text": text,
                "embedding_model": row.get("embedding_model") or "",
                "creation_date": row.get("creation_date"),
                "hash": row.get("hash") or "",
                "path": row.get("path") or "",
                "tags": row.get("tags"),
                "label": label_value,
                "cluster": cluster_value,
                "density": density_value,
                "outlier_score": outlier_value,
                "metadata": metadata,
                "magnitude": None,
                "full_magnitude": _vector_norm(full_vector),
                "similarity": None,
                "query_distance": None,
            }
            points.append(point)
            full_vectors.append(full_vector)

        if query_vector_full is not None:
            query_point = {
                "vector": [],
                "magnitude": None,
                "label": "query",
                "text": query,
                "distance": 0.0,
            }
            for idx, point in enumerate(points):
                similarity = _cosine_similarity(full_vectors[idx], query_vector_full)
                point["similarity"] = similarity
                point["query_distance"] = _metric_distance(effective_metric_type, full_vectors[idx], query_vector_full, similarity)

        projection = _project_embedding_preview(
            vectors=full_vectors,
            preview_dim_target=preview_dim_target,
            query_vector=[float(v) for v in query_vector_full] if query_vector_full is not None else None,
            metric_type=effective_metric_type,
        )

        projected_vectors = projection.get("vectors") or []
        for idx, point in enumerate(points):
            vector = projected_vectors[idx] if idx < len(projected_vectors) else [0.0] * preview_dim_target
            point["vector"] = [float(v) for v in vector]
            point["magnitude"] = _vector_norm(point["vector"])

        projected_query_vector = projection.get("query_vector")
        if query_point is not None:
            query_point["vector"] = [float(v) for v in (projected_query_vector or [0.0] * preview_dim_target)]
            query_point["magnitude"] = _vector_norm(query_point["vector"])

        preview_vector_dim = len(points[0]["vector"]) if points and isinstance(points[0].get("vector"), list) else (vector_dim or 0)

        return jsonify(
            {
                "collection": _logical_collection_name(raw_name),
                "raw_name": raw_name,
                "vector_dim": preview_vector_dim,
                "points": points,
                "query_point": query_point,
                "query": query,
                "query_error": query_error,
                "meta": {
                    "limit": limit,
                    "offset": offset,
                    "returned": len(points),
                    "has_similarity": bool(query and not query_error),
                    "preview_dim": preview_vector_dim,
                    "metric_type": effective_metric_type,
                    "projection_method": projection.get("method"),
                    "axis_labels": projection.get("axis_labels") or [],
                },
            }
        )
        
    finally:
        elapsed_ms = int((time.time() - started) * 1000) if 'started' in locals() else None
        if elapsed_ms is not None:
            app.logger.info("Embeddings preview for %s completed in %sms", raw_name, elapsed_ms)
        if coll is not None:
            if _env_flag("VECTORSTORE_RELEASE_AFTER_PREVIEW", default=False):
                try:
                    coll.release()
                    app.logger.info("Released embeddings preview collection %s", raw_name)
                except Exception as release_error:
                    app.logger.warning("Failed to release embeddings preview collection %s: %s", raw_name, release_error)
        _milvus_disconnect(alias)

@app.route("/api/search/global", methods=["POST"])
def api_search_global():
    payload = request.json or {}
    query = payload.get("query")
    if not query:
        return jsonify({"error": "No query provided"}), 400
    limit = int(payload.get("limit", 20))
    per_collection_limit = int(payload.get("per_collection_limit", max(limit, 20)))
    mode = payload.get("mode", "dense")
    unique = bool(payload.get("unique", False))
    path_filter = payload.get("path", "")
    embedding_model = payload.get("model")
    ip_address = payload.get("ip_address", MILVUS_HOST)
    embedding_host = payload.get("embedding_host", EMBEDDING_HOST)
    embedding_port = payload.get("embedding_port", EMBEDDING_PORT)
    search_options = _build_search_options(payload)
    try:
        collection_load_timeout = max(
            1.0,
            float(payload.get("collection_load_timeout", GLOBAL_SEARCH_COLLECTION_LOAD_TIMEOUT)),
        )
    except (TypeError, ValueError):
        collection_load_timeout = GLOBAL_SEARCH_COLLECTION_LOAD_TIMEOUT
    search_options["load_if_unloaded"] = bool(payload.get("load_unloaded_collections", False))

    alias = _milvus_alias("global_search")
    merged = []
    try:
        _milvus_connect(alias, host=ip_address)
        collection_names = utility.list_collections(using=alias, timeout=MILVUS_CONNECT_TIMEOUT)
    finally:
        _milvus_disconnect(alias)

    # Embed query ONCE and reuse the vector across all collections
    precomputed_vector = None
    mode_norm = str(mode or "dense").strip().lower()
    if mode_norm in ("dense", "hybrid"):
        try:
            model = str(embedding_model or LOCAL_EMBEDDING_MODEL)
            vectors = embed_text_to_vector(
                [query], model, is_local=True,
                ip_address=ip_address, embedding_host=embedding_host, embedding_port=embedding_port,
            )
            validated = validate_embeddings(vectors, LOCAL_EMBEDDING_DIM)
            if validated and validated[0] is not None:
                precomputed_vector = validated[0]
        except Exception:
            app.logger.warning("Global search: failed to pre-compute embedding, will embed per-collection")

    skipped_collections = []
    for raw_name in sorted(collection_names):
        logical_name = _logical_collection_name(raw_name)
        try:
            hits = search_vectorstore(
                query,
                limit=per_collection_limit,
                path_filter=path_filter,
                unique=unique,
                mode=mode,
                collection_name=logical_name,
                embedding_model=embedding_model,
                ip_address=ip_address,
                embedding_host=embedding_host,
                embedding_port=embedding_port,
                load_timeout=collection_load_timeout,
                query_vector=precomputed_vector,
                **search_options,
            )
            for h in hits:
                h["collection"] = logical_name
                h["collection_raw"] = raw_name
                merged.append(h)
        except CollectionLoadError as exc:
            skipped_collections.append({"collection": logical_name, "reason": str(exc)})
            app.logger.info("Global search skipped collection '%s': %s", logical_name, exc)
        except Exception:
            app.logger.exception("Global search failed for collection '%s'", logical_name)

    prefers_lower = _prefers_lower_distance_for_response(mode=mode, metric_type=search_options.get("metric_type"))
    merged.sort(
        key=lambda item: (
            item.get("distance", float("inf"))
            if prefers_lower
            else item.get("ranking_score", item.get("distance", float("-inf")))
        ),
        reverse=not prefers_lower,
    )
    return jsonify({"results": merged[:limit], "total_candidates": len(merged), "skipped_collections": skipped_collections})

@app.route("/api/collections/<name>/insert-text", methods=["POST"])
def api_insert_text(name: str):
    payload = request.json or {}
    text = payload.get("text")
    if not text:
        return jsonify({"error": "No text provided"}), 400
    embedding_model = payload.get("model")
    ip_address = payload.get("ip_address", MILVUS_HOST)
    embedding_host = payload.get("embedding_host", EMBEDDING_HOST)
    embedding_port = payload.get("embedding_port", EMBEDDING_PORT)
    line_by_line = bool(payload.get("line_by_line", False))
    chunk_size = int(payload.get("chunk_size", 1000))
    overlap = int(payload.get("overlap", 0))
    alias = _milvus_alias("insert_resolve")
    resolved_name = name
    try:
        _milvus_connect(alias)
        resolved_raw = _resolve_collection_raw_name(name, alias)
        if resolved_raw:
            resolved_name = _logical_collection_name(resolved_raw)
    finally:
        _milvus_disconnect(alias)

    result = load_text_to_vectorstore(
        text,
        collection_name=resolved_name,
        embedding_model=embedding_model,
        ip_address=ip_address,
        embedding_host=embedding_host,
        embedding_port=embedding_port,
        line_by_line=line_by_line,
        chunk_size=chunk_size,
        overlap=overlap,
        flush=True,
    )
    if isinstance(result, dict) and result.get("error"):
        return jsonify(result), 500
    return jsonify({"message": "Inserted", "details": result})

@app.route("/api/collections/<name>/drop", methods=["POST"])
def api_drop_collection(name: str):
    alias = _milvus_alias("drop")
    try:
        _milvus_connect(alias)
        raw_name = _resolve_collection_raw_name(name, alias)
        if not raw_name:
            fallback_raw = name if str(name).startswith("documents_") else f"documents_{name}"
            return jsonify({"message": "Already absent", "raw_name": fallback_raw}), 200
        Collection(name=raw_name, using=alias).drop()
        return jsonify({"message": "Dropped", "raw_name": raw_name}), 200
    finally:
        _milvus_disconnect(alias)

@app.route("/api/backups/overview", methods=["GET"])
def api_backup_overview():
    return jsonify(get_backup_overview())

@app.route("/api/backups/start", methods=["POST"])
def api_backup_start():
    try:
        return jsonify(start_backup())
    except Exception as e:
        message = str(e)
        if "already running" in message.lower():
            payload = get_backup_overview()
            payload["warning"] = message
            return jsonify(payload), 200
        return jsonify({"error": message}), 409

@app.route("/api/backups/stop", methods=["POST"])
def api_backup_stop():
    try:
        return jsonify(stop_backup())
    except Exception as e:
        message = str(e)
        if "no running backup process" in message.lower():
            payload = get_backup_overview()
            payload["warning"] = message
            return jsonify(payload), 200
        return jsonify({"error": message}), 409

@app.route("/api/backups/runs/<run_id>/logs", methods=["GET"])
def api_backup_logs(run_id: str):
    tail = request.args.get("tail", "180")
    try:
        tail_lines = max(20, min(1000, int(tail)))
    except Exception:
        tail_lines = 180
    try:
        return jsonify(get_run_logs(run_id=run_id, tail_lines=tail_lines))
    except FileNotFoundError:
        return jsonify({"error": "Run not found"}), 404

@app.route("/api/backups/schedule", methods=["POST"])
def api_backup_schedule():
    payload = request.json or {}
    enabled = bool(payload.get("enabled", True))
    time_of_day = str(payload.get("time_of_day", "02:00"))
    try:
        return jsonify(update_schedule(enabled=enabled, time_of_day=time_of_day))
    except Exception as e:
        return jsonify({"error": str(e)}), 422

@app.route("/api/backups/targets", methods=["GET"])
def api_backup_targets():
    return jsonify({"targets": list_backup_targets()})

@app.route("/api/backups/targets", methods=["POST"])
def api_backup_targets_add():
    payload = request.json or {}
    try:
        target = add_backup_target(
            profile=str(payload.get("profile") or "default"),
            source=str(payload.get("source") or ""),
            destination=str(payload.get("destination") or ""),
            enabled=bool(payload.get("enabled", True)),
        )
        return jsonify(target), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 422

@app.route("/api/backups/targets/<target_id>", methods=["PUT"])
def api_backup_targets_update(target_id: str):
    payload = request.json or {}
    try:
        target = update_backup_target(target_id, payload)
        return jsonify(target)
    except FileNotFoundError:
        return jsonify({"error": "Target not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 422

@app.route("/api/backups/targets/<target_id>", methods=["DELETE"])
def api_backup_targets_delete(target_id: str):
    try:
        delete_backup_target(target_id)
        return jsonify({"message": "Deleted"})
    except FileNotFoundError:
        return jsonify({"error": "Target not found"}), 404

@app.route("/api/backups/targets/<target_id>/backup", methods=["POST"])
def api_backup_target_run(target_id: str):
    try:
        return jsonify(start_target_backup(target_id))
    except FileNotFoundError:
        return jsonify({"error": "Target not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 409

@app.route("/api/backups/files/<name>", methods=["GET"])
def api_backup_file(name: str):
    # Only allow serving files from backup root.
    return send_from_directory(str(BACKUP_ROOT), name, as_attachment=True)

@app.route("/api/indexing/overview", methods=["GET"])
def api_indexing_overview():
    return jsonify(get_indexing_overview())

@app.route("/api/indexing/start", methods=["POST"])
def api_indexing_start():
    # Accept empty-body POSTs from UI buttons that do not send JSON.
    payload = request.get_json(silent=True) or {}
    target_ids = payload.get("target_ids")
    embedding_host = payload.get("embedding_host", EMBEDDING_HOST)
    embedding_port = payload.get("embedding_port", EMBEDDING_PORT)
    ip_address = payload.get("ip_address", MILVUS_HOST)
    try:
        return jsonify(
            start_indexing(
                target_ids=target_ids,
                embedding_host=embedding_host,
                embedding_port=int(embedding_port),
                ip_address=ip_address,
            )
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 409

@app.route("/api/indexing/stop", methods=["POST"])
def api_indexing_stop():
    try:
        return jsonify(stop_indexing())
    except Exception as e:
        return jsonify({"error": str(e)}), 409

@app.route("/api/indexing/runs/<run_id>/logs", methods=["GET"])
def api_indexing_logs(run_id: str):
    tail = request.args.get("tail", "180")
    try:
        tail_lines = max(20, min(1000, int(tail)))
    except Exception:
        tail_lines = 180
    try:
        return jsonify(get_indexing_run_logs(run_id=run_id, tail_lines=tail_lines))
    except FileNotFoundError:
        return jsonify({"error": "Run not found"}), 404

@app.route("/api/indexing/targets", methods=["GET"])
def api_indexing_targets():
    return jsonify({"targets": list_indexing_targets()})

@app.route("/api/indexing/targets", methods=["POST"])
def api_indexing_targets_add():
    payload = request.json or {}
    try:
        target = add_indexing_target(
            path=str(payload.get("path") or ""),
            enabled=bool(payload.get("enabled", True)),
            recursive=bool(payload.get("recursive", True)),
        )
        return jsonify(target), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 422

@app.route("/api/indexing/targets/<target_id>", methods=["PUT"])
def api_indexing_targets_update(target_id: str):
    payload = request.json or {}
    try:
        target = update_indexing_target(target_id, payload)
        return jsonify(target)
    except FileNotFoundError:
        return jsonify({"error": "Target not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 422

@app.route("/api/indexing/targets/<target_id>", methods=["DELETE"])
def api_indexing_targets_delete(target_id: str):
    try:
        delete_indexing_target(target_id)
        return jsonify({"message": "Deleted"})
    except FileNotFoundError:
        return jsonify({"error": "Target not found"}), 404

@app.route("/api/indexing/targets/<target_id>/scan", methods=["POST"])
def api_indexing_target_scan(target_id: str):
    try:
        return jsonify(scan_indexing_target(target_id))
    except FileNotFoundError:
        return jsonify({"error": "Target not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 422

@app.route("/api/indexing/targets/<target_id>/index", methods=["POST"])
def api_indexing_target_index(target_id: str):
    payload = request.json or {}
    embedding_host = payload.get("embedding_host", EMBEDDING_HOST)
    embedding_port = payload.get("embedding_port", EMBEDDING_PORT)
    ip_address = payload.get("ip_address", MILVUS_HOST)
    try:
        return jsonify(
            start_target_indexing(
                target_id=target_id,
                embedding_host=embedding_host,
                embedding_port=int(embedding_port),
                ip_address=ip_address,
            )
        )
    except FileNotFoundError:
        return jsonify({"error": "Target not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 409


@app.route("/api/transcribe", methods=["POST"])
def transcribe_endpoint():
    """Transcription endpoint - drop-in replacement for TranscribeServer."""
    if not transcription_service.is_available():
        transcription_service.init_transcription_model()
    if not transcription_service.is_available():
        return jsonify({"error": "Transcription service not available", "status": transcription_service.get_status()}), 503

    if "file" not in request.files:
        return jsonify({"error": "No file provided. Send multipart/form-data with field 'file'."}), 400

    uploaded = request.files["file"]
    data = uploaded.read()
    if not data:
        return jsonify({"error": "Empty file"}), 400

    initial_prompt = request.args.get("initial_prompt")
    no_speech_threshold = request.args.get("no_speech_threshold", type=float)
    vad_filter = request.args.get("vad_filter", "true").lower() in ("true", "1", "yes")
    allow_fallback = request.args.get("allow_fallback", "true").lower() in ("true", "1", "yes")
    detailed = request.args.get("detailed", "false").lower() in ("true", "1", "yes")
    word_timestamps = request.args.get("word_timestamps", "false").lower() in ("true", "1", "yes")

    try:
        transcription, meta, segments = transcription_service.transcribe_audio_bytes(
            data,
            content_type=uploaded.content_type or "",
            filename=uploaded.filename or "",
            initial_prompt=initial_prompt,
            no_speech_threshold=no_speech_threshold,
            vad_filter=vad_filter,
            allow_fallback=allow_fallback,
            word_timestamps=word_timestamps,
        )
        return jsonify(transcription_service.build_transcribe_response(
            transcription, meta, segments, detailed=detailed, word_timestamps=word_timestamps
        ))
    except Exception as e:
        logging.exception("Transcription failed")
        return jsonify({"error": str(e)}), 500


@app.route("/api/transcribe/status", methods=["GET"])
def transcribe_status():
    return jsonify(transcription_service.get_status())


@app.route("/transcribe", methods=["POST"])
def transcribe_compat_endpoint():
    """Backward-compatible endpoint matching TranscribeServer's POST / contract."""
    return transcribe_endpoint()


@app.route("/", methods=["POST"])
def transcribe_root_compat_endpoint():
    """Legacy TranscribeServer clients POST to the service root."""
    return transcribe_endpoint()


@app.route("/api/movietime/items/upsert", methods=["POST"])
def api_movietime_items_upsert():
    payload = request.json or {}
    records = payload.get("records")
    if not isinstance(records, list) or not records:
        return jsonify({"error": "records (non-empty list) is required"}), 400

    collection = payload.get("collection") or "movietime_library"
    delete_first = bool(payload.get("delete_first", True))
    ip_address = payload.get("ip_address", MILVUS_HOST)
    embedding_host = payload.get("embedding_host", EMBEDDING_HOST)
    embedding_port = payload.get("embedding_port", EMBEDDING_PORT)
    try:
        result = upsert_movietime_items(
            records=records,
            collection_name=collection,
            delete_first=delete_first,
            ip_address=ip_address,
            embedding_host=embedding_host,
            embedding_port=embedding_port,
        )
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 422
    except Exception as e:
        app.logger.exception("MovieTime upsert failed")
        return jsonify({"error": "MovieTime upsert failed", "details": str(e)}), 500


@app.route("/api/movietime/items/search", methods=["POST"])
def api_movietime_items_search():
    payload = request.json or {}
    query = str(payload.get("query") or "").strip()
    if not query:
        return jsonify({"error": "query is required"}), 400

    collection = payload.get("collection") or "movietime_library"
    limit = int(payload.get("limit", 24))
    mode = payload.get("mode", "hybrid")
    filters = payload.get("filters")
    tag_boosts = payload.get("tagBoosts")
    ip_address = payload.get("ip_address", MILVUS_HOST)
    embedding_host = payload.get("embedding_host", EMBEDDING_HOST)
    embedding_port = payload.get("embedding_port", EMBEDDING_PORT)
    try:
        results = search_movietime_items(
            query=query,
            collection_name=collection,
            limit=limit,
            mode=mode,
            filters=filters if isinstance(filters, dict) else None,
            tag_boosts=tag_boosts if isinstance(tag_boosts, dict) else None,
            ip_address=ip_address,
            embedding_host=embedding_host,
            embedding_port=embedding_port,
        )
        return jsonify({"results": results})
    except Exception as e:
        app.logger.exception("MovieTime search failed")
        return jsonify({"error": "MovieTime search failed", "details": str(e)}), 500


@app.route('/vectorstore', methods=['GET', 'POST'])
def handle_vectorstore_request():
    if request.method == 'GET':
        return jsonify({"message": "Vectorstore is running. Use POST for operations."}), 200

    data = request.json
    operation_type = data.get('type')

    logging.info(f"Received request: {data}")

    # Special diagnostic endpoint for Milvus health check
    if operation_type == 'milvus_check':
        ip_address = data.get('ip_address', MILVUS_HOST)
        try:
            # Try connecting to Milvus directly
            connections.connect(
                "default",
                host=ip_address,
                port='19530',
                timeout=MILVUS_CONNECT_TIMEOUT,
            )
            status = connections.get_connection_addr("default")
            is_connected = connections.has_connection("default")
            
            # Get list of collections to verify Milvus is operational
            collections = []
            if is_connected:
                collections = utility.list_collections(timeout=MILVUS_CONNECT_TIMEOUT)
            
            result = {
                "status": "connected" if is_connected else "error",
                "connection_details": status,
                "collections": collections
            }
            
            connections.disconnect("default")
            return jsonify(result)
        except Exception as e:
            logging.error(f"Milvus connection check failed: {str(e)}")
            logging.error(traceback.format_exc())
            return jsonify({
                "status": "error", 
                "error": str(e),
                "traceback": traceback.format_exc()
            })

    if operation_type == 'load':
        if 'text' in data:
            text = data.get('text')
            collection_name = data.get('collection')
            embedding_model = data.get('model')
            # Use environment variable for IP address if not provided
            ip_address = data.get('ip_address', MILVUS_HOST)
            # Use environment variable for embedding host
            embedding_host = data.get('embedding_host', EMBEDDING_HOST)
            embedding_port = data.get('embedding_port', EMBEDDING_PORT)
            line_by_line = data.get('line_by_line', False)
            chunk_size = data.get('chunk_size', 1000)
            overlap = data.get('overlap', 0)
            debug = data.get('debug', False)

            try:
                result = load_text_to_vectorstore(
                    text,
                    collection_name=collection_name,
                    embedding_model=embedding_model,
                    ip_address=ip_address,
                    embedding_host=embedding_host,
                    embedding_port=embedding_port,
                    line_by_line=line_by_line,
                    chunk_size=chunk_size,
                    overlap=overlap
                )
                
                if isinstance(result, dict) and result.get("error"):
                    error_payload = {
                        "error": result.get("error"),
                        "details": result.get("details"),
                    }
                    if debug and result.get("traceback"):
                        error_payload["traceback"] = result["traceback"]
                    return jsonify(error_payload), 500

                # For debug requests, add detailed diagnostics
                if debug:
                    debug_alias = f"debug_{uuid4().hex}"
                    try:
                        connections.connect(
                            debug_alias,
                            host=ip_address,
                            port='19530',
                            timeout=MILVUS_CONNECT_TIMEOUT,
                        )
                        default_collection_suffix = LOCAL_EMBEDDING_MODEL.replace("-", "_")
                        collection_name_formatted = (
                            f"documents_{collection_name}" if collection_name else f"documents_{default_collection_suffix}"
                        )
                        collection_exists = utility.has_collection(
                            collection_name_formatted,
                            using=debug_alias,
                            timeout=MILVUS_CONNECT_TIMEOUT,
                        )
                        entity_count = 0
                        
                        if collection_exists:
                            from pymilvus import Collection
                            collection = Collection(collection_name_formatted, using=debug_alias)
                            entity_count = collection.num_entities
                        
                        debug_info = {
                            "collection_exists": collection_exists,
                            "entity_count": entity_count,
                            "collection_name": collection_name_formatted
                        }
                    finally:
                        connections.disconnect(debug_alias)
                    
                    return jsonify({"message": "Text loaded successfully", "details": result, "debug": debug_info})
                
                return jsonify({"message": "Text loaded successfully", "details": result})
            except Exception as e:
                logging.error(f"Load operation failed: {str(e)}")
                logging.error(traceback.format_exc())
                return jsonify({
                    "error": "An unexpected error occurred", 
                    "details": str(e),
                    "traceback": traceback.format_exc() if debug else None
                }), 500
        elif 'path' in data:
            args = argparse.Namespace(**data)
            
            # Set default IP address to environment variable if not provided
            if not hasattr(args, 'ip_address') or not args.ip_address:
                args.ip_address = MILVUS_HOST
            
            # Set default embedding host to environment variable if not provided
            if not hasattr(args, 'embedding_host') or not args.embedding_host:
                args.embedding_host = EMBEDDING_HOST
            if not hasattr(args, 'embedding_port') or not getattr(args, 'embedding_port', None):
                args.embedding_port = EMBEDDING_PORT
                
            load_to_vectorstore(args)
            return jsonify({"message": "Documents loaded successfully"})
        else:
            return jsonify({"error": "No text or path provided for loading"}), 400

    elif operation_type == 'search':
        query = data.get('query')
        if not query:
            return jsonify({"error": "No query provided for searching"}), 400

        # Extract additional search parameters
        limit = data.get('limit', 10)
        path_filter = data.get('path', "")
        unique = data.get('unique', False)
        mode = data.get('mode', 'dense')
        collection_name = data.get('collection')
        embedding_model = data.get('model')
        ip_address = data.get('ip_address', MILVUS_HOST)
        embedding_host = data.get('embedding_host', EMBEDDING_HOST)
        embedding_port = data.get('embedding_port', EMBEDDING_PORT)
        search_options = _build_search_options(data)

        try:
            results = search_vectorstore(
                query,
                limit=limit,
                path_filter=path_filter,
                unique=unique,
                mode=mode,
                collection_name=collection_name,
                embedding_model=embedding_model,
                ip_address=ip_address,
                embedding_host=embedding_host,
                embedding_port=embedding_port,
                **search_options,
            )
            return jsonify({"results": results})
        except Exception as e:
            logging.error(f"Search operation failed: {str(e)}")
            logging.error(traceback.format_exc())
            return jsonify({
                "error": "Search failed",
                "details": str(e),
                "traceback": traceback.format_exc() if data.get('debug', False) else None
            }), 502

    elif operation_type == 'clear':
        collection_name = data.get('collection')
        if not collection_name:
            return jsonify({"error": "No collection name provided for clearing"}), 400

        try:
            clear_vectorstore_collection(collection_name, ip_address=data.get('ip_address', MILVUS_HOST))
            return jsonify({"message": f"Collection '{collection_name}' cleared successfully"})
        except Exception as e:
            logging.error(f"Clear operation failed: {str(e)}")
            logging.error(traceback.format_exc())
            return jsonify({
                "error": "An unexpected error occurred during clear operation",
                "details": str(e),
                "traceback": traceback.format_exc() if data.get('debug', False) else None
            }), 500

    else:
        return jsonify({"error": "Invalid operation type"}), 400

# UI static serving.
# Prefer `./ui/dist` for the actively developed frontend build,
# and fall back to legacy `./ui_dist` only if needed.
_UI_DIR_CANDIDATES = [
    os.path.join(os.path.dirname(__file__), "ui", "dist"),
    os.path.join(os.path.dirname(__file__), "ui_dist"),
]
UI_DIST_DIR = next((path for path in _UI_DIR_CANDIDATES if os.path.isdir(path)), _UI_DIR_CANDIDATES[-1])
if os.path.isdir(UI_DIST_DIR):
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def _ui_static(path: str):
        candidate = os.path.join(UI_DIST_DIR, path)
        if path and os.path.isfile(candidate):
            return send_from_directory(UI_DIST_DIR, path)
        # Never cache HTML shell. If the browser caches an old `index.html` that
        # references a previous hashed bundle, refreshes can "break" the app.
        resp = send_from_directory(UI_DIST_DIR, "index.html")
        resp.headers["Cache-Control"] = "no-store, max-age=0"
        resp.headers["Pragma"] = "no-cache"
        return resp

@app.errorhandler(HTTPException)
def handle_http_exception(e: HTTPException):
    return jsonify({"error": e.name, "details": e.description}), e.code

@app.errorhandler(Exception)
def handle_exception(e: Exception):
    app.logger.error(f"Unhandled exception: {str(e)}")
    app.logger.error(traceback.format_exc())
    return jsonify({"error": "An unexpected error occurred"}), 500

## ── Chat endpoint (agent executor proxy) ────────────────────────────
import re as _re

_AGENT_CHAT_SESSIONS: dict[str, list[dict]] = {}
_AGENT_SESSION_META: dict[str, dict[str, object]] = {}
_AGENT_STOP_REQUESTS: set[str] = set()
_SYSTEM_FLAGS: dict[str, bool] = {
    "system_enabled": True,
    "speech_input_enabled": True,
}
_TEST_PROFILE_SPECS: dict[str, dict[str, object]] = {}
_TEST_PROFILES = [
    {"id": str(spec["id"]), "label": str(spec["label"])}
    for spec in _TEST_PROFILE_SPECS.values()
]
_TEST_REPORTS_ROOT = Path(
    os.getenv(
        "ARCHIVIST_TEST_REPORTS_DIR",
        str((Path(__file__).resolve().parent / ".artifacts" / "test-reports").resolve()),
    )
).expanduser()
_TEST_TASK_LOCK = threading.Lock()
_TEST_ACTIVE_PROCESS_LOCK = threading.Lock()
_TEST_ACTIVE_PROCESS: subprocess.Popen | None = None
_TEST_TASK_STATE: dict[str, object] = {
    "running": False,
    "profile": "focus-priorities",
    "run_id": "",
    "trigger": "manual",
    "started_at": "",
    "finished_at": None,
    "returncode": None,
    "progress_percent": None,
    "progress_line": None,
    "cancel_requested": False,
    "tail": [],
}
_TEST_AUTOMATION_LOCK = threading.Lock()
_TEST_AUTOMATION_STATE: dict[str, object] = {
    "last_auto_requested_at": None,
    "last_auto_profile": "",
    "last_auto_reason": "",
    "last_auto_run_id": "",
}


def _test_task_snapshot() -> dict[str, object]:
    with _TEST_TASK_LOCK:
        return dict(_TEST_TASK_STATE)


def _update_test_task(**updates: object) -> None:
    with _TEST_TASK_LOCK:
        _TEST_TASK_STATE.update(updates)


def _append_test_task_tail(line: str) -> None:
    clean = str(line or "").rstrip()
    if not clean:
        return
    with _TEST_TASK_LOCK:
        tail = list(_TEST_TASK_STATE.get("tail") or [])
        tail.append(clean)
        _TEST_TASK_STATE["tail"] = tail[-200:]
        _TEST_TASK_STATE["progress_line"] = clean


def _test_cancel_requested() -> bool:
    with _TEST_TASK_LOCK:
        return bool(_TEST_TASK_STATE.get("cancel_requested"))


def _set_active_test_process(process: subprocess.Popen | None) -> None:
    global _TEST_ACTIVE_PROCESS
    with _TEST_ACTIVE_PROCESS_LOCK:
        _TEST_ACTIVE_PROCESS = process


def _active_test_process() -> subprocess.Popen | None:
    with _TEST_ACTIVE_PROCESS_LOCK:
        return _TEST_ACTIVE_PROCESS


def _test_automation_snapshot() -> dict[str, object]:
    with _TEST_AUTOMATION_LOCK:
        return dict(_TEST_AUTOMATION_STATE)


def _update_test_automation_state(**updates: object) -> None:
    with _TEST_AUTOMATION_LOCK:
        _TEST_AUTOMATION_STATE.update(updates)


def _test_percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(float(value) for value in values)
    if len(ordered) == 1:
        return ordered[0]
    position = max(0.0, min(1.0, percentile)) * (len(ordered) - 1)
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def _test_result_category(name: str) -> str:
    text = str(name or "").strip()
    if not text:
        return "misc"
    node = text.split("::", 1)[0].replace("\\", "/")
    stem = Path(node).stem or node
    return stem or "misc"


def _test_result_name(case: ET.Element) -> str:
    file_name = str(case.attrib.get("file") or "").strip()
    classname = str(case.attrib.get("classname") or "").strip().replace(".", "/")
    test_name = str(case.attrib.get("name") or "unnamed").strip() or "unnamed"
    base = file_name or classname or "pytest"
    return f"{base}::{test_name}"


def _trim_oneline(value: str | None, max_chars: int = 180) -> str:
    clean = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(clean) <= max_chars:
        return clean
    clipped = clean[: max(1, max_chars - 1)].rsplit(" ", 1)[0].strip()
    return f"{clipped or clean[: max(1, max_chars - 1)]}…"


def _test_failure_reason(case: ET.Element) -> str:
    for tag in ("failure", "error"):
        node = case.find(tag)
        if node is None:
            continue
        message = str(node.attrib.get("message") or "").strip()
        if message:
            return _trim_oneline(message.replace("\n", " "), 160)
        text = str(node.text or "").strip()
        if text:
            return _trim_oneline(text.splitlines()[0], 160)
    return "Unknown failure"


def _build_test_report_from_results(
    *,
    profile_id: str,
    run_id: str,
    timestamp_iso: str,
    results: list[dict],
    failure_analysis: dict[str, list[str]],
) -> dict:
    total = len(results)
    passed = sum(1 for result in results if str(result.get("status") or "") == "passed")
    failed = sum(1 for result in results if str(result.get("status") or "") == "failed")
    durations = [float(result.get("duration_s") or 0.0) for result in results]
    category_breakdown: dict[str, dict] = {}
    grouped: dict[str, list[dict]] = defaultdict(list)
    for result in results:
        grouped[_test_result_category(str(result.get("name") or ""))].append(result)
    for category, items in grouped.items():
        category_durations = [float(item.get("duration_s") or 0.0) for item in items]
        category_failures = [str(item.get("name") or "") for item in items if str(item.get("status") or "") == "failed"]
        category_passed = sum(1 for item in items if str(item.get("status") or "") == "passed")
        category_failed = sum(1 for item in items if str(item.get("status") or "") == "failed")
        category_total = len(items)
        category_breakdown[category] = {
            "total": category_total,
            "passed": category_passed,
            "failed": category_failed,
            "pass_rate": round((category_passed / category_total) * 100, 1) if category_total else 0.0,
            "p50_s": round(_test_percentile(category_durations, 0.50), 3),
            "p95_s": round(_test_percentile(category_durations, 0.95), 3),
            "failures": category_failures[:20],
        }
    slowest = sorted(
        (
            {"name": str(result.get("name") or ""), "duration_s": float(result.get("duration_s") or 0.0)}
            for result in results
        ),
        key=lambda item: item["duration_s"],
        reverse=True,
    )[:10]
    return {
        "summary": {
            "run_id": run_id,
            "timestamp": timestamp_iso,
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": round((passed / total) * 100, 1) if total else 0.0,
            "total_duration_s": round(sum(durations), 3),
            "profile": profile_id,
        },
        "test_duration_metrics": {
            "p50_s": round(_test_percentile(durations, 0.50), 3),
            "p95_s": round(_test_percentile(durations, 0.95), 3),
            "slowest_tests": slowest,
        },
        "category_breakdown": category_breakdown,
        "failure_analysis": dict(failure_analysis),
        "performance_metrics": [],
        "results": results,
    }


def _fallback_test_report(profile_id: str, run_id: str, timestamp_iso: str, tail: list[str]) -> dict:
    failure_line = next((line for line in reversed(tail) if line.strip()), "pytest did not produce a structured report.")
    result_name = f"{profile_id}::runner"
    return _build_test_report_from_results(
        profile_id=profile_id,
        run_id=run_id,
        timestamp_iso=timestamp_iso,
        results=[
            {
                "name": result_name,
                "status": "failed",
                "duration_s": 0.0,
                "timestamp": timestamp_iso,
            }
        ],
        failure_analysis={failure_line: [result_name]},
    )


def _parse_junit_test_report(xml_path: Path, profile_id: str, run_id: str, timestamp_iso: str, tail: list[str]) -> dict:
    try:
        root = ET.parse(xml_path).getroot()
    except Exception:
        logging.exception("failed to parse junit xml from %s", xml_path)
        return _fallback_test_report(profile_id, run_id, timestamp_iso, tail)

    results: list[dict] = []
    failure_analysis: dict[str, list[str]] = defaultdict(list)
    for case in root.iter("testcase"):
        name = _test_result_name(case)
        duration_s = float(case.attrib.get("time") or 0.0)
        if case.find("failure") is not None or case.find("error") is not None:
            status = "failed"
            failure_analysis[_test_failure_reason(case)].append(name)
        elif case.find("skipped") is not None:
            status = "skipped"
        else:
            status = "passed"
        results.append(
            {
                "name": name,
                "status": status,
                "duration_s": duration_s,
                "timestamp": timestamp_iso,
            }
        )

    if not results:
        return _fallback_test_report(profile_id, run_id, timestamp_iso, tail)
    return _build_test_report_from_results(
        profile_id=profile_id,
        run_id=run_id,
        timestamp_iso=timestamp_iso,
        results=results,
        failure_analysis=dict(failure_analysis),
    )


def _combine_test_reports(profile_id: str, run_id: str, reports: list[dict]) -> dict:
    if not reports:
        return _fallback_test_report(profile_id, run_id, datetime.now(timezone.utc).isoformat(), [])
    if len(reports) == 1:
        report = copy.deepcopy(reports[0])
        report.setdefault("summary", {})["profile"] = profile_id
        return report
    timestamp_iso = datetime.now(timezone.utc).isoformat()
    results: list[dict] = []
    failure_analysis: dict[str, list[str]] = defaultdict(list)
    for report in reports:
        results.extend(list(report.get("results") or []))
        for reason, names in dict(report.get("failure_analysis") or {}).items():
            failure_analysis[str(reason)].extend(str(name) for name in list(names or []))
    return _build_test_report_from_results(
        profile_id=profile_id,
        run_id=run_id,
        timestamp_iso=timestamp_iso,
        results=results,
        failure_analysis=dict(failure_analysis),
    )


def _save_test_report(profile_id: str, run_id: str, report: dict) -> Path:
    _TEST_REPORTS_ROOT.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = _TEST_REPORTS_ROOT / f"{timestamp}_{profile_id}_{run_id}.json"
    path.write_text(json.dumps({"profile_id": profile_id, "report": report}, indent=2), encoding="utf-8")
    return path


def _load_test_report_records(limit: int | None = None) -> list[dict]:
    if not _TEST_REPORTS_ROOT.is_dir():
        return []
    records: list[dict] = []
    for path in sorted(_TEST_REPORTS_ROOT.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            logging.exception("failed to read test report %s", path)
            continue
        report = payload.get("report") if isinstance(payload, dict) else None
        profile_id = str(payload.get("profile_id") or "").strip() if isinstance(payload, dict) else ""
        if not isinstance(report, dict) or not profile_id:
            continue
        records.append(
            {
                "file": path.name,
                "profile_id": profile_id,
                "report": report,
                "report_mtime_iso": datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(),
            }
        )
        if limit is not None and len(records) >= limit:
            break
    return records


def _latest_test_report_record(profile_id: str) -> dict | None:
    profile_key = str(profile_id or "").strip().lower()
    if not profile_key:
        return None
    for record in _load_test_report_records():
        if str(record.get("profile_id") or "").strip().lower() == profile_key:
            return record
    return None


def _latest_test_reports_payload() -> dict[str, dict]:
    latest: dict[str, dict] = {}
    records = _load_test_report_records()
    for record in records:
        profile_id = str(record.get("profile_id") or "")
        if profile_id and profile_id not in latest:
            latest[profile_id] = {
                "ok": True,
                "report": record.get("report"),
                "report_mtime_iso": record.get("report_mtime_iso"),
            }
    if "all" not in latest and records:
        latest["all"] = {
            "ok": True,
            "report": records[0].get("report"),
            "report_mtime_iso": records[0].get("report_mtime_iso"),
        }
    return latest


def _summarize_test_report(profile_id: str, report: dict | None) -> str:
    if not isinstance(report, dict):
        return "No test report is available yet."
    summary = dict(report.get("summary") or {})
    total = int(summary.get("total_tests") or 0)
    passed = int(summary.get("passed") or 0)
    failed = int(summary.get("failed") or 0)
    pass_rate = float(summary.get("pass_rate") or 0.0)
    lines = [
        f"{profile_id}: {passed}/{total} passed ({pass_rate:.1f}%).",
        f"Failures: {failed}. Total duration: {float(summary.get('total_duration_s') or 0.0):.2f}s.",
    ]
    category_breakdown = dict(report.get("category_breakdown") or {})
    if category_breakdown:
        strongest = sorted(
            category_breakdown.items(),
            key=lambda item: (int(item[1].get("failed") or 0), str(item[0])),
            reverse=True,
        )
        top_category, info = strongest[0]
        lines.append(
            f"Highest-risk category: {top_category} ({int(info.get('failed') or 0)} failed of {int(info.get('total') or 0)})."
        )
    failure_analysis = dict(report.get("failure_analysis") or {})
    if failure_analysis:
        reason, names = next(iter(failure_analysis.items()))
        example = ", ".join(list(names or [])[:2])
        lines.append(f"Top failure signal: {reason}. Example tests: {example}.")
    else:
        lines.append("No failures detected.")
    return "\n".join(lines)


def _test_parse_iso_datetime(value: object) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _test_profile_specs_for_request(requested_profile: str) -> tuple[list[dict[str, object]], str | None]:
    profile_key = str(requested_profile or "all").strip().lower() or "all"
    if profile_key == "all":
        return list(_TEST_PROFILE_SPECS.values()), None
    spec = _TEST_PROFILE_SPECS.get(profile_key)
    if spec is None:
        return [], f"Unknown test profile: {profile_key}"
    return [spec], None


def _start_test_run(requested_profile: str, *, trigger: str = "manual") -> tuple[dict[str, object], int]:
    profile_key = str(requested_profile or "all").strip().lower() or "all"
    if _test_task_snapshot().get("running"):
        return {"error": "An Archivist test run is already active."}, 409
    specs, error = _test_profile_specs_for_request(profile_key)
    if error is not None:
        return {"error": error}, 404

    run_id = uuid4().hex[:12]
    _update_test_task(
        running=True,
        profile=profile_key,
        run_id=run_id,
        trigger=str(trigger or "manual"),
        started_at=datetime.now(timezone.utc).isoformat(),
        finished_at=None,
        returncode=None,
        progress_percent=None,
        progress_line="Starting pytest run...",
        cancel_requested=False,
        tail=[],
    )
    worker = threading.Thread(
        target=_run_test_job,
        args=(profile_key, specs, run_id),
        daemon=True,
        name=f"tests-{profile_key}",
    )
    worker.start()
    return {"ok": True, "profile": profile_key, "run_id": run_id, "trigger": str(trigger or "manual")}, 200


def _test_result_names_with_failures(report: dict | None) -> list[str]:
    if not isinstance(report, dict):
        return []
    failures = []
    for result in list(report.get("results") or []):
        if str(result.get("status") or "") != "failed":
            continue
        failures.append(str(result.get("name") or ""))
    return failures


def _run_single_test_profile(spec: dict[str, object], requested_profile: str, run_id: str) -> tuple[int, dict]:
    profile_id = str(spec.get("id") or requested_profile or "tests")
    pytest_args = [str(arg) for arg in list(spec.get("pytest_args") or [])]
    timestamp_iso = datetime.now(timezone.utc).isoformat()
    _TEST_REPORTS_ROOT.mkdir(parents=True, exist_ok=True)
    xml_path = _TEST_REPORTS_ROOT / f"{run_id}_{profile_id}.xml"
    cmd = [sys.executable, "-m", "pytest", *pytest_args, "--junitxml", str(xml_path), "-q"]
    _append_test_task_tail(f"$ {' '.join(cmd)}")
    process = subprocess.Popen(
        cmd,
        cwd=host_workspace(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env={**os.environ, "PYTHONUNBUFFERED": "1"},
    )
    _set_active_test_process(process)
    profile_tail: list[str] = []
    try:
        assert process.stdout is not None
        for line in process.stdout:
            clean = line.rstrip()
            if clean:
                prefixed = f"[{profile_id}] {clean}"
                profile_tail.append(prefixed)
                _append_test_task_tail(prefixed)
            if _test_cancel_requested() and process.poll() is None:
                process.terminate()
        returncode = process.wait()
    finally:
        _set_active_test_process(None)
    report = _parse_junit_test_report(xml_path, profile_id, run_id, timestamp_iso, profile_tail)
    return returncode, report


def _run_test_job(requested_profile: str, specs: list[dict[str, object]], run_id: str) -> None:
    reports: list[dict] = []
    return_codes: list[int] = []
    try:
        for spec in specs:
            if _test_cancel_requested():
                _append_test_task_tail("Cancellation requested. Stopping test run.")
                break
            returncode, report = _run_single_test_profile(spec, requested_profile, run_id)
            reports.append(report)
            return_codes.append(returncode)
            if returncode != 0:
                _append_test_task_tail(f"[{spec.get('id')}] exit code {returncode}")
        effective_profile = requested_profile if requested_profile != "all" else "all"
        combined = _combine_test_reports(effective_profile, run_id, reports)
        _save_test_report(effective_profile, run_id, combined)
        finished_at = datetime.now(timezone.utc).isoformat()
        cancelled = _test_cancel_requested()
        final_code = 130 if cancelled else (0 if all(code == 0 for code in return_codes or [0]) else 1)
        _update_test_task(
            running=False,
            finished_at=finished_at,
            returncode=final_code,
            progress_percent=100,
            progress_line="Cancelled" if cancelled else "Completed",
        )
    except Exception as exc:
        logging.exception("test runner job failed")
        _append_test_task_tail(f"Runner error: {exc}")
        _update_test_task(
            running=False,
            finished_at=datetime.now(timezone.utc).isoformat(),
            returncode=1,
            progress_percent=100,
            progress_line=f"Runner error: {exc}",
        )


_CHAT_SYSTEM_MESSAGE = """You are Archivist's built-in chat assistant. You run inside a self-hosted document search and vector database management app.

## What you know about
- Document collections (transcripts, PDFs, text files indexed in Milvus vector DB)
- Search: dense (semantic), BM25 (keyword), and hybrid search across collections
- 3D embeddings visualization
- Backup management: scheduled backups, logs, targets
- Indexing: document indexing pipelines, status, logs

## UI Navigation
Append ACTION line to navigate the user: ACTION:{"type":"navigate","payload":{"path":"/collections"}}

Available pages:
- /collections -- All collections (main view, search across all)
- /collections/COLLECTION_NAME -- Collection detail with search
- /backup -- Backup management (schedules, logs, targets)
- /indexing -- Indexing management (pipelines, status)

Examples:
- "show collections" -> answer + ACTION:{"type":"navigate","payload":{"path":"/collections"}}
- "search for meetings" -> answer + ACTION:{"type":"navigate","payload":{"path":"/collections"}}
- "backup status" -> answer + ACTION:{"type":"navigate","payload":{"path":"/backup"}}
- "indexing status" -> answer + ACTION:{"type":"navigate","payload":{"path":"/indexing"}}

## Rules
1. ALWAYS respond to every message
2. Keep responses concise and helpful
3. Keep responses under 200 words unless showing search results
"""


def _extract_chat_action(text):
    match = _re.search(r"ACTION:(\{[^}]+\})", text)
    if not match:
        return None
    try:
        import json as _json
        parsed = _json.loads(match.group(1))
        if parsed.get("type") and parsed.get("payload"):
            return parsed
    except (ValueError, KeyError):
        pass
    return None


def _session_title_from_messages(messages: list[dict]) -> str:
    for message in messages:
        if message.get("role") == "user":
            text = str(message.get("text") or message.get("content") or "").strip()
            if text:
                return text[:80]
    return "Untitled"


def _session_screen_context(payload: dict) -> str:
    context = payload.get("context") or {}
    parts: list[str] = []
    page = str(context.get("page") or "").strip()
    description = str(context.get("description") or "").strip()
    screen = str(context.get("screen") or "").strip()
    if page:
        parts.append(f"- User is viewing page: {page}")
    if description:
        parts.append(f"- View description: {description}")
    if screen:
        parts.append(f"- Visible UI context:\n{screen}")
    if not parts:
        return ""
    return "\n\n## Current UI context\n" + "\n".join(parts)


def _local_agent_sessions() -> list[dict]:
    sessions: list[dict] = []
    for session_id, messages in _AGENT_CHAT_SESSIONS.items():
        agent_id, session_key = decode_session_ref(session_id)
        first = messages[0] if messages else {}
        last = messages[-1] if messages else {}
        meta = dict(_AGENT_SESSION_META.get(session_id) or {})
        sessions.append(
            {
                "id": session_id,
                "agentId": agent_id,
                "sessionKey": session_key,
                "source": "local",
                "status": "active",
                "createdAt": int(first.get("ts") or 0),
                "updatedAt": int(last.get("ts") or first.get("ts") or 0),
                "messageCount": len(messages),
                "lastMessage": str(last.get("text") or last.get("content") or "")[:120],
                "title": _session_title_from_messages(messages),
                "kind": session_kind(session_key),
                "surface": str(meta.get("surface") or "").strip() or None,
                "historyScope": str(meta.get("historyScope") or "").strip() or None,
            }
        )
    return sessions


def _merged_agent_sessions() -> list[dict]:
    sessions_by_id = {session["id"]: session for session in _local_agent_sessions()}
    for session in load_agent_sessions_for_agents(visible_agent_ids()):
        sessions_by_id[session["id"]] = session
    sessions = list(sessions_by_id.values())
    sessions.sort(key=lambda item: item.get("updatedAt", 0), reverse=True)
    return sessions


def _load_agent_session(session_id: str) -> dict | None:
    agent_id, session_key = decode_session_ref(session_id)
    local = _AGENT_CHAT_SESSIONS.get(session_id)
    if local is not None:
        meta = dict(_AGENT_SESSION_META.get(session_id) or {})
        return {
            "id": session_id,
            "agentId": agent_id,
            "sessionKey": session_key,
            "source": "local",
            "surface": str(meta.get("surface") or "").strip() or None,
            "historyScope": str(meta.get("historyScope") or "").strip() or None,
            "messages": [
                {
                    "role": str(message.get("role") or ""),
                    "text": str(message.get("text") or message.get("content") or ""),
                    "ts": int(message.get("ts") or 0),
                    "toolName": message.get("toolName"),
                }
                for message in local
            ],
        }
    for session in load_agent_sessions_for_agents([agent_id]):
        if session.get("id") != session_id:
            continue
        session_file = resolve_agent_session_file(session.get("sessionFile"))
        if not session_file:
            return None
        return {
            "id": session_id,
            "agentId": agent_id,
            "sessionKey": session_key,
            "source": "agents",
            "messages": load_agent_messages_from_transcript(session_file),
        }
    return None


def _agent_runtime_snapshot() -> dict:
    runtime = inspect_agent_runtime()
    runtime["registered_agents"] = registered_agent_ids()
    runtime["visible_agent_ids"] = visible_agent_ids()
    runtime["host_workspace"] = host_workspace()
    return runtime


def _service_probes() -> list[dict]:
    probes: list[dict] = []
    runtime = _agent_runtime_snapshot()
    probes.append(
        {
            "name": "Agent Knowledge Base",
            "ok": bool(runtime.get("available")),
            "status": 200 if runtime.get("available") else 503,
            "target": str(agents_repo_root()),
            "latency_ms": None,
            "detail": f"{runtime.get('agents_count', 0)} agents, {runtime.get('skills_count', 0)} skills, {runtime.get('mcp_server_count', 0)} MCP entries",
        }
    )
    try:
        backup = get_backup_overview()
        probes.append(
            {
                "name": "Backup Service",
                "ok": True,
                "status": 200,
                "target": "internal",
                "latency_ms": None,
                "detail": "running" if backup.get("status", {}).get("running") else "idle",
            }
        )
    except Exception:
        probes.append({"name": "Backup Service", "ok": False, "status": 500, "target": "internal", "latency_ms": None})
    try:
        indexing = get_indexing_overview()
        probes.append(
            {
                "name": "Indexing Service",
                "ok": True,
                "status": 200,
                "target": "internal",
                "latency_ms": None,
                "detail": "running" if indexing.get("status", {}).get("running") else "idle",
            }
        )
    except Exception:
        probes.append({"name": "Indexing Service", "ok": False, "status": 500, "target": "internal", "latency_ms": None})
    try:
        from media.pipeline import get_active_jobs
        jobs = get_active_jobs()
        probes.append(
            {
                "name": "Media Pipeline",
                "ok": True,
                "status": 200,
                "target": "internal",
                "latency_ms": None,
                "detail": f"{len(jobs)} active jobs" if jobs else "idle",
            }
        )
    except Exception:
        probes.append({"name": "Media Pipeline", "ok": False, "status": 500, "target": "internal", "latency_ms": None})
    return probes


@app.route("/api/media/process", methods=["POST"])
def media_process():
    """Process a media file through the hierarchical pipeline.

    Runs the pipeline in a background thread so the HTTP request returns
    immediately. Progress can be tracked via GET /api/media/jobs.
    """
    import threading
    from media.pipeline import process_media_file
    body = request.get_json(force=True, silent=True) or {}
    path = (body.get("path") or "").strip()
    if not path:
        return jsonify({"error": "path is required"}), 400
    if not os.path.isfile(path):
        return jsonify({"error": f"File not found: {path}"}), 404
    output_format = body.get("format")
    try:
        from media.models import OutputFormat
        fmt = OutputFormat(output_format) if output_format else None
    except (ValueError, KeyError):
        fmt = None
    force_reprocess = bool(body.get("force") or body.get("force_reprocess") or body.get("reprocess"))

    def _run():
        try:
            process_media_file(path, output_format=fmt, force_reprocess=force_reprocess)
        except Exception:
            logging.exception("Media processing failed for %s", path)

    thread = threading.Thread(target=_run, daemon=True, name=f"media-process-{os.path.basename(path)}")
    thread.start()
    return jsonify({"status": "started", "path": path})


@app.route("/api/media/jobs", methods=["GET"])
def media_jobs():
    """Get active/recent media processing jobs."""
    from media.pipeline import get_active_jobs
    return jsonify({"jobs": get_active_jobs()})


@app.route("/api/media/assets", methods=["GET"])
def media_assets():
    """List all registered media assets with pipeline currency status."""
    from media.evidence_store import list_assets
    from media.pipeline import get_pipeline_result, MEDIA_PIPELINE_COMPAT_VERSION
    assets = list_assets()
    try:
        enrich_limit = max(0, min(200, int(request.args.get("enrich_limit", "50"))))
    except (TypeError, ValueError):
        enrich_limit = 50
    enriched = []
    for index, asset_dict in enumerate(assets):
        media_id = asset_dict.get("media_id", "")
        result = get_pipeline_result(media_id) if media_id and index < enrich_limit else None
        pipeline_current = False
        pipeline_version = None
        subject_line = None
        if result and isinstance(result, dict):
            stamp = result.get("archivist_pipeline")
            if isinstance(stamp, dict):
                pipeline_version = str(stamp.get("pipeline_compat_version") or "").strip() or None
                pipeline_current = pipeline_version == MEDIA_PIPELINE_COMPAT_VERSION
            # Extract subject line for catalog display
            for artifact in (result.get("artifacts") or []):
                if isinstance(artifact, dict) and artifact.get("kind") == "subject_line":
                    subject_line = str(artifact.get("content") or "").strip() or None
                    break
            if not subject_line:
                subject_line = str(result.get("subject_line") or "").strip() or None
        asset_dict["pipeline_current"] = pipeline_current
        asset_dict["pipeline_version"] = pipeline_version
        asset_dict["subject_line"] = subject_line
        asset_dict["has_result"] = result is not None
        enriched.append(asset_dict)
    return jsonify({"assets": enriched})


@app.route("/api/media/assets/<media_id>", methods=["GET"])
def media_asset_detail(media_id):
    """Get details for a specific media asset."""
    from media.evidence_store import get_asset, get_artifacts
    asset = get_asset(media_id)
    if not asset:
        return jsonify({"error": "Asset not found"}), 404
    artifacts = get_artifacts(media_id)
    return jsonify({
        "asset": {
            "media_id": asset.media_id,
            "path": asset.path,
            "filename": asset.filename,
            "modality": asset.modality.value,
            "duration_s": asset.duration_s,
            "file_hash": asset.file_hash,
            "file_size_bytes": asset.file_size_bytes,
            "created_at": asset.created_at,
            "indexed_at": asset.indexed_at,
            "metadata": asset.metadata,
        },
        "artifacts": [
            {"artifact_id": a.artifact_id, "kind": a.kind, "start_s": a.start_s, "end_s": a.end_s, "confidence": a.confidence}
            for a in artifacts
        ],
    })


@app.route("/api/media/pipeline/<media_id>", methods=["GET"])
def media_pipeline_result(media_id):
    """Get the full pipeline result for a processed media asset."""
    from media.pipeline import get_pipeline_result
    result = get_pipeline_result(media_id)
    if not result:
        return jsonify({"error": "No pipeline result found"}), 404
    return jsonify(result)


@app.route("/api/media/pipeline/compat-status", methods=["GET"])
def media_pipeline_compat_status():
    """Return counts of current vs stale vs broken pipeline results."""
    from media.pipeline import pipeline_compat_status
    return jsonify(pipeline_compat_status())


@app.route("/api/media/pipeline/migrate", methods=["POST"])
def media_pipeline_migrate():
    """Stamp existing valid pipeline results with the current compat version."""
    from media.pipeline import migrate_pipeline_compat_version
    payload = request.json if request.is_json else {}
    dry_run = payload.get("dry_run", False)
    verify_sources = payload.get("verify_sources", False)
    try:
        result = migrate_pipeline_compat_version(dry_run=dry_run, verify_sources=verify_sources)
        return jsonify(result)
    except Exception as exc:
        logging.exception("pipeline compat migration failed")
        return jsonify({"error": str(exc)}), 500


@app.route("/api/media/artifacts/<media_id>", methods=["GET"])
def media_artifacts(media_id):
    """Get all artifacts for a media asset, optionally filtered by kind."""
    from media.evidence_store import get_artifacts
    kind = request.args.get("kind")
    scope = request.args.get("scope", "public")
    artifacts = get_artifacts(media_id, kind=kind, scope=scope)
    return jsonify({
        "artifacts": [
            {
                "artifact_id": a.artifact_id,
                "kind": a.kind,
                "start_s": a.start_s,
                "end_s": a.end_s,
                "content": a.content,
                "confidence": a.confidence,
                "metadata": a.metadata,
                "source_refs": a.source_refs,
            }
            for a in artifacts
        ],
    })


# ── Chat session endpoints ─────────────────────────────────────────────

@app.route("/api/chat/sessions", methods=["GET"])
def get_chat_sessions():
    try:
        sessions = []
        for item in list_sessions():
            raw_id = str(item.get("id") or "")
            if not raw_id:
                continue
            sessions.append(
                {
                    "session_key": f"main:web:{raw_id}@{console_agent_id()}",
                    "title": item.get("title") or item.get("last_message") or "Untitled",
                    "created_at": item.get("updated_at"),
                    "message_count": item.get("message_count", 0),
                    "source": "local",
                }
            )
        agent_sessions = [
            {
                "session_key": session["id"],
                "title": session.get("title") or "Untitled",
                "created_at": session.get("updatedAt"),
                "message_count": session.get("messageCount", 0),
                "source": "agents",
                "kind": session.get("kind"),
            }
            for session in load_agent_sessions_for_agents(visible_agent_ids())
        ]
        return jsonify({"sessions": sessions, "agent_sessions": agent_sessions})
    except Exception as e:
        return jsonify({"sessions": [], "agent_sessions": [], "error": str(e)}), 200


@app.route("/api/chat/sessions", methods=["POST"])
def create_new_chat_session():
    body = request.get_json(force=True, silent=True) or {}
    title = (body.get("title") or "").strip()
    try:
        session = create_chat_session(title)
        return jsonify(session), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/chat/sessions/<session_id>/messages", methods=["GET"])
def get_chat_messages(session_id):
    try:
        if session_id.startswith("agent:"):
            session = _load_agent_session(session_id)
            if session:
                return jsonify({"messages": [{"role": m["role"], "content": m.get("text", "")} for m in session["messages"]]})
        if session_id.startswith("main:web:") and "@" in session_id:
            raw_id = session_id.split("main:web:", 1)[1].rsplit("@", 1)[0]
            msgs = get_session_messages(raw_id)
            return jsonify({"messages": msgs})
        msgs = get_session_messages(session_id)
        return jsonify({"messages": msgs})
    except Exception as e:
        return jsonify({"messages": [], "error": str(e)}), 200


@app.route("/api/chat/sessions/<session_id>", methods=["DELETE"])
def remove_chat_session(session_id):
    try:
        raw_id = session_id
        if session_id.startswith("main:web:") and "@" in session_id:
            raw_id = session_id.split("main:web:", 1)[1].rsplit("@", 1)[0]
        delete_chat_session(raw_id)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/chat", methods=["POST"])
def chat_endpoint():
    import json as _json

    body = request.get_json(force=True, silent=True) or {}
    message = (body.get("message") or "").strip()
    if not message:
        return jsonify({"reply": "Please provide a message."}), 400

    executor_token = resolve_agent_executor_token()
    executor_url = resolve_agent_executor_url()
    agent_id = console_agent_id()
    executor_model = resolve_agent_chat_model(agent_id)

    if not executor_token or not executor_url:
        return jsonify({"reply": "Agent executor is not configured. Set ARCHIVIST_AGENT_EXECUTOR_URL and ARCHIVIST_AGENT_EXECUTOR_TOKEN."}), 500

    stream = body.get("stream", True)
    session_id = body.get("session_id")
    session_key = body.get("session_key") or (
        f"main:web:{session_id}@{console_agent_id()}" if session_id else default_web_session_key(console_agent_id())
    )
    executor_session_ref = agent_session_key(agent_id, session_key)

    # Persist user message and load history
    if session_id:
        add_message(session_id, "user", message)
        history = get_session_messages(session_id)
        # Auto-title on first user message
        if sum(1 for m in history if m["role"] == "user") == 1:
            update_session_title(session_id, message[:80])
        # Build messages from DB history (last 20)
        recent = history[-20:]
        messages_payload = [{"role": "system", "content": _CHAT_SYSTEM_MESSAGE}]
        messages_payload += [{"role": m["role"], "content": m["content"]} for m in recent]
    else:
        messages_payload = [
            {"role": "system", "content": _CHAT_SYSTEM_MESSAGE},
            {"role": "user", "content": message},
        ]

    if stream:
        import requests as _requests

        def generate():
            try:
                resp = _requests.post(
                    f"{executor_url}/v1/chat/completions",
                    json={
                        "model": executor_model,
                        "stream": True,
                        "messages": messages_payload,
                        "user": executor_session_ref,
                    },
                    headers={
                        "Authorization": f"Bearer {executor_token}",
                        "Content-Type": "application/json",
                        "x-agent-id": agent_id,
                        "x-agent-scopes": "operator.write",
                        "x-agent-session-key": executor_session_ref,
                    },
                    stream=True,
                    timeout=180,
                )

                full_text = ""
                for line in resp.iter_lines(decode_unicode=True):
                    if not line or not line.startswith("data: "):
                        continue
                    payload = line[6:].strip()
                    if payload == "[DONE]":
                        # Persist assistant response
                        if session_id and full_text.strip():
                            add_message(session_id, "assistant", full_text.strip())
                        action = _extract_chat_action(full_text)
                        if action:
                            yield f"data: {_json.dumps({'action': action})}\n\n"
                        yield "data: [DONE]\n\n"
                        return
                    try:
                        parsed = _json.loads(payload)
                        delta = parsed.get("choices", [{}])[0].get("delta", {}).get("content")
                        if delta:
                            full_text += delta
                            yield f"data: {_json.dumps({'delta': delta})}\n\n"
                    except (ValueError, IndexError, KeyError):
                        pass

                # Persist assistant response (stream ended without [DONE])
                if session_id and full_text.strip():
                    add_message(session_id, "assistant", full_text.strip())
                action = _extract_chat_action(full_text)
                if action:
                    yield f"data: {_json.dumps({'action': action})}\n\n"
                yield "data: [DONE]\n\n"

            except Exception as e:
                yield f"data: {_json.dumps({'delta': f'Error: {str(e)}'})}\n\n"
                yield "data: [DONE]\n\n"

        from flask import Response
        return Response(generate(), mimetype="text/event-stream")

    else:
        import requests as _requests
        try:
            resp = _requests.post(
                f"{executor_url}/v1/chat/completions",
                json={
                    "model": executor_model,
                    "stream": False,
                    "messages": messages_payload,
                    "user": executor_session_ref,
                },
                headers={
                    "Authorization": f"Bearer {executor_token}",
                    "Content-Type": "application/json",
                    "x-agent-id": agent_id,
                    "x-agent-scopes": "operator.write",
                    "x-agent-session-key": executor_session_ref,
                },
                timeout=180,
            )
            data = resp.json()
            reply = data.get("choices", [{}])[0].get("message", {}).get("content", "No response.")
            # Persist assistant response
            if session_id and reply.strip():
                add_message(session_id, "assistant", reply.strip())
            action = _extract_chat_action(reply)
            clean_reply = _re.sub(r"ACTION:\{[^}]*\}", "", reply).strip()
            result = {"reply": clean_reply}
            if action:
                result["action"] = action
            return jsonify(result)
        except Exception as e:
            return jsonify({"reply": f"Failed to reach AI backend: {str(e)}"}), 500


@app.route("/api/status", methods=["GET"])
def app_status():
    runtime = _agent_runtime_snapshot()
    tasks = {
        "backup": {"running": False},
        "indexing": {"running": False},
        "media": {"running": False},
        "tests": {"running": bool(_test_task_snapshot().get("running"))},
    }
    try:
        backup = get_backup_overview()
        tasks["backup"]["running"] = bool(backup.get("status", {}).get("running"))
    except Exception:
        pass
    try:
        indexing = get_indexing_overview()
        tasks["indexing"]["running"] = bool(indexing.get("status", {}).get("running"))
    except Exception:
        pass
    try:
        from media.pipeline import get_active_jobs
        tasks["media"]["running"] = bool(get_active_jobs())
    except Exception:
        pass
    return jsonify(
        {
            "flags": dict(_SYSTEM_FLAGS),
            "integrations": {"probes": _service_probes()},
            "mcp": {"tools": load_mcp_tools_for_status()},
            "mcp_resources": {"resources": load_mcp_resources_for_status()},
            "recent_tool_calls": [],
            "tasks": tasks,
            "repairs": {"agent_runtime": runtime},
        }
    )


@app.route("/api/flags", methods=["POST"])
def update_flags():
    body = request.get_json(force=True, silent=True) or {}
    flags = body.get("flags") if isinstance(body.get("flags"), dict) else {}
    if "system_enabled" in flags:
        _SYSTEM_FLAGS["system_enabled"] = bool(flags.get("system_enabled"))
    if "speech_input_enabled" in flags:
        _SYSTEM_FLAGS["speech_input_enabled"] = bool(flags.get("speech_input_enabled"))
    if not _SYSTEM_FLAGS["system_enabled"]:
        _SYSTEM_FLAGS["speech_input_enabled"] = False
    return jsonify({"ok": True, "flags": dict(_SYSTEM_FLAGS)})


@app.route("/api/agent/config", methods=["GET"])
def agent_config():
    runtime = _agent_runtime_snapshot()
    return jsonify(
        {
            "consoleAgentId": console_agent_id(),
            "visibleAgentIds": visible_agent_ids(),
            "executorUrl": resolve_agent_executor_url(),
            "executorTokenConfigured": bool(resolve_agent_executor_token()),
            "workspacePath": host_workspace(),
            "agentsRoot": str(agents_repo_root()),
            "registeredAgents": runtime.get("registered_agents", []),
            "teamAgents": load_team_agents(),
            "sharedSkills": load_shared_skills(),
            "mcpServers": [tool.get("server") for tool in load_mcp_tools_for_status()],
            "runtime": runtime,
        }
    )


@app.route("/api/agents/fleet", methods=["GET"])
def agent_fleet():
    runtime = _agent_runtime_snapshot()
    sessions = load_agent_sessions_for_agents(visible_agent_ids())
    verification: dict[str, object] = {}
    tickets = [dict(ticket) for ticket in list(verification.get("tickets") or []) if isinstance(ticket, dict)]
    sessions_by_agent: dict[str, list[dict]] = {}
    for session in sessions:
        sessions_by_agent.setdefault(str(session.get("agentId") or ""), []).append(session)
    registered = set(runtime.get("registered_agents") or [])
    roster: list[tuple[int, str, dict[str, object]]] = []
    for manifest in load_team_agents():
        ui = manifest.get("ui") if isinstance(manifest.get("ui"), dict) else {}
        if ui.get("show") is False:
            continue
        sort_key_raw = ui.get("sort_key")
        try:
            sort_key = int(sort_key_raw)
        except (TypeError, ValueError):
            sort_key = 9999
        lane_id = str(manifest.get("fleet_lane") or manifest.get("fleetLane") or "system").strip().lower() or "system"
        roster.append((sort_key, lane_id, manifest))
    roster.sort(key=lambda item: (0 if item[1] == "system" else 1, item[1], item[0], str(item[2].get("agent_id") or "")))
    agents = []
    lanes: dict[str, dict[str, object]] = {}
    for sort_key, lane_id, manifest in roster:
        agent_id = str(manifest.get("agent_id") or "")
        agent_sessions = sessions_by_agent.get(agent_id, [])
        agent_tickets = [ticket for ticket in tickets if str(ticket.get("authority") or "") == agent_id]
        activity = [
            {
                "timestamp": session.get("updatedAt", 0),
                "action": "session",
                "detail": session.get("title") or session.get("sessionKey") or "Session",
            }
            for session in agent_sessions[:3]
        ]
        if agent_id in set(verification.get("owner_agents") or []):
            latest = dict(verification.get("latest") or {})
            status = str(verification.get("status") or "unknown")
            activity.insert(
                0,
                {
                    "timestamp": str(latest.get("timestamp") or datetime.now(timezone.utc).isoformat()),
                    "action": "verification",
                    "detail": f"focus-priorities {status}",
                },
            )
        critical_count = sum(1 for ticket in agent_tickets if str(ticket.get("severity") or "").lower() == "critical")
        high_count = sum(1 for ticket in agent_tickets if str(ticket.get("severity") or "").lower() == "high")
        open_count = sum(1 for ticket in agent_tickets if str(ticket.get("status") or "").lower() == "open")
        agents.append(
            {
                "id": agent_id,
                "name": manifest.get("name") or agent_id,
                "description": manifest.get("summary") or "",
                "status": "active" if agent_id in registered else "missing",
                "role": manifest.get("role") or "",
                "summary": manifest.get("summary") or "",
                "workspace": manifest.get("_path"),
                "registered": agent_id in registered,
                "group_label": (manifest.get("ui") or {}).get("badge"),
                "lane": lane_id,
                "sort_key": sort_key,
                "chat_enabled": agent_id in registered,
                "stats": {
                    "critical": critical_count,
                    "high": high_count,
                    "open": open_count if agent_id in registered else max(open_count, 1),
                    "fixed": 0,
                },
                "findings": [
                    {
                        "ticket_id": str(ticket.get("ticket_id") or ""),
                        "title": str(ticket.get("title") or ticket.get("summary") or ""),
                        "category": str(ticket.get("category") or "verification"),
                        "severity": str(ticket.get("severity") or "default"),
                        "status": str(ticket.get("status") or "open"),
                        "created_at": str(ticket.get("created_at") or ""),
                    }
                    for ticket in agent_tickets
                ],
                "recent_activity": activity,
                "activity": activity,
                "tickets": agent_tickets,
            }
        )
        lane = lanes.setdefault(
            lane_id,
            {
                "id": lane_id,
                "label": "System" if lane_id == "system" else ("Specialist" if lane_id == "specialist" else lane_id.replace("-", " ").replace("_", " ").title()),
                "description": (
                    "System agents are the durable control plane for Archivist."
                    if lane_id == "system"
                    else "Specialist agents own focused runtime or domain lanes."
                ),
                "agents": [],
            },
        )
        lane_agents = lane.setdefault("agents", [])
        if isinstance(lane_agents, list):
            lane_agents.append(agents[-1])
    for lane in lanes.values():
        lane_agents = lane.get("agents")
        if isinstance(lane_agents, list):
            lane_agents.sort(key=lambda agent: (int(agent.get("sort_key") or 9999), str(agent.get("name") or agent.get("id") or "")))
            for agent in lane_agents:
                if isinstance(agent, dict):
                    agent.pop("sort_key", None)
    for agent in agents:
        agent.pop("sort_key", None)
    lane_list = list(lanes.values())
    lane_list.sort(key=lambda lane: 0 if str(lane.get("id") or "") == "system" else 1)
    return jsonify(
        {
            "fleet_summary": {
                "active_agents": sum(1 for agent in agents if agent["status"] == "active"),
                "total_findings": 0,
                "open_findings": sum(agent["stats"]["open"] for agent in agents),
                "critical_findings": 0 if runtime.get("available") else 1,
            },
            "agents": agents,
            "lanes": lane_list,
        }
    )


@app.route("/api/automations/status", methods=["GET"])
def automations_status():
    runtime = _agent_runtime_snapshot()
    task = _test_task_snapshot()
    experiments_current = None
    if task.get("running") and str(task.get("trigger") or "").startswith("auto:"):
        experiments_current = f"Auto-running {task.get('profile')}"
    completed = []
    auto_state = _test_automation_snapshot()
    if auto_state.get("last_auto_run_id"):
        completed.append(
            f"{auto_state.get('last_auto_profile') or 'focus-priorities'} ({auto_state.get('last_auto_reason') or 'scheduled'})"
        )
    return jsonify(
        {
            "ok": bool(runtime.get("available")),
            "tickets_open": 0,
            "tickets": [],
            "agents": {
                "available": bool(runtime.get("available")),
                "binary": runtime.get("binary"),
                "model": runtime.get("model"),
                "version": runtime.get("version"),
                "skills_count": runtime.get("skills_count"),
                "mcp_server_count": runtime.get("mcp_server_count"),
            },
            "experiments": {"completed": completed, "current": experiments_current},
            "repair_runs": [],
            "verification": {},
        }
    )


@app.route("/api/tests/profiles", methods=["GET"])
def tests_profiles():
    return jsonify({"profiles": list(_TEST_PROFILES)})


@app.route("/api/tests/status", methods=["GET"])
def tests_status():
    return jsonify({"tasks": {"tests": _test_task_snapshot()}})


@app.route("/api/tests/run", methods=["POST"])
def tests_run():
    body = request.get_json(force=True, silent=True) or {}
    response, status_code = _start_test_run(str(body.get("profile") or "all"), trigger="manual")
    return jsonify(response), status_code


@app.route("/api/tests/cancel", methods=["POST"])
def tests_cancel():
    if not _test_task_snapshot().get("running"):
        return jsonify({"error": "No Archivist test run is currently active."}), 409
    _update_test_task(cancel_requested=True, progress_line="Cancellation requested...")
    process = _active_test_process()
    if process is not None and process.poll() is None:
        try:
            process.terminate()
        except Exception:
            logging.exception("failed to terminate active pytest process")
    return jsonify({"ok": True})


@app.route("/api/tests/summarize", methods=["POST"])
def tests_summarize():
    body = request.get_json(force=True, silent=True) or {}
    profile_id = str(body.get("profile") or "all").strip().lower() or "all"
    latest = _latest_test_reports_payload()
    entry = latest.get(profile_id)
    if entry is None and profile_id == "all":
        records = _load_test_report_records(limit=1)
        entry = {
            "ok": True,
            "report": records[0]["report"],
            "report_mtime_iso": records[0]["report_mtime_iso"],
        } if records else None
    return jsonify({"ok": True, "summary": _summarize_test_report(profile_id, entry.get("report") if entry else None)})


@app.route("/api/test-reports/latest", methods=["GET"])
def latest_test_reports():
    return jsonify({"reports": _latest_test_reports_payload()})


@app.route("/api/test-reports/history", methods=["GET"])
def test_report_history():
    try:
        limit = max(1, min(int(request.args.get("limit", "180")), 500))
    except ValueError:
        limit = 180
    records = _load_test_report_records(limit=limit)
    history = [
        {
            "file": record["file"],
            "summary": dict(record["report"].get("summary") or {}),
            "profile_id": record["profile_id"],
            "report_mtime_iso": record["report_mtime_iso"],
        }
        for record in records
    ]
    return jsonify({"reports": history})


@app.route("/api/test-report/by-file", methods=["GET"])
def test_report_by_file():
    file_name = Path(str(request.args.get("file") or "").strip()).name
    if not file_name:
        return jsonify({"error": "file is required"}), 400
    for record in _load_test_report_records():
        if record["file"] == file_name:
            return jsonify(
                {
                    "ok": True,
                    "report": record["report"],
                    "file": record["file"],
                    "profile_id": record["profile_id"],
                }
            )
    return jsonify({"error": "Test report not found."}), 404


@app.route("/api/agent/sessions", methods=["GET"])
def agent_sessions():
    return jsonify(_merged_agent_sessions())


@app.route("/api/agent/sessions/<path:session_id>", methods=["GET"])
def agent_session(session_id: str):
    decoded = _load_agent_session(session_id)
    if not decoded:
        return jsonify({"error": "session not found"}), 404
    return jsonify(decoded)


@app.route("/api/agent/stop/<path:session_id>", methods=["POST"])
def agent_stop(session_id: str):
    _AGENT_STOP_REQUESTS.add(session_id)
    return jsonify({"ok": True})


@app.route("/api/agent/chat", methods=["POST"])
def agent_chat():
    import requests as _requests

    body = request.get_json(force=True, silent=True) or {}
    message = (body.get("message") or "").strip()
    if not message:
        return jsonify({"error": "empty message"}), 400

    incoming_session_id = (body.get("sessionId") or "").strip()
    surface = str(body.get("surface") or "").strip().lower()
    history_scope = str(body.get("historyScope") or "").strip().lower()
    agent_id, session_key = decode_session_ref(incoming_session_id)
    if not incoming_session_id:
        session_key = default_web_session_key(agent_id)
    session_id = encode_session_ref(agent_id, session_key)
    executor_session_ref = agent_session_key(agent_id, session_key)
    _AGENT_SESSION_META.setdefault(session_id, {})
    if surface:
        _AGENT_SESSION_META[session_id]["surface"] = surface
    if history_scope:
        _AGENT_SESSION_META[session_id]["historyScope"] = history_scope

    screen_context = _session_screen_context(body)
    system_message = build_agent_system_message(agent_id, screen_context)
    _AGENT_CHAT_SESSIONS.setdefault(session_id, []).append(
        {"role": "user", "text": message, "ts": int(time.time() * 1000)}
    )

    executor_url = resolve_agent_executor_url()
    executor_token = resolve_agent_executor_token()
    model = resolve_agent_chat_model(agent_id)

    def generate():
        full_text = ""
        yield f"event: session_start\ndata: {json.dumps({'id': session_id})}\n\n"
        if not executor_token or not executor_url:
            yield f"event: error\ndata: {json.dumps({'message': 'Agent executor is not configured. Set ARCHIVIST_AGENT_EXECUTOR_URL and ARCHIVIST_AGENT_EXECUTOR_TOKEN.'})}\n\n"
            yield "event: done\ndata: {}\n\n"
            return
        try:
            response = _requests.post(
                f"{executor_url}/v1/chat/completions",
                json={
                    "model": model,
                    "stream": True,
                    "messages": [
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": message},
                    ],
                    "user": executor_session_ref,
                },
                headers={
                    "Authorization": f"Bearer {executor_token}",
                    "Content-Type": "application/json",
                    "x-agent-id": agent_id,
                    "x-agent-session-key": executor_session_ref,
                    "x-agent-message-channel": "archivist-console",
                    "x-agent-scopes": "operator.write",
                },
                stream=True,
                timeout=180,
            )
            if response.status_code >= 400:
                yield f"event: error\ndata: {json.dumps({'message': f'Agent executor returned HTTP {response.status_code}'})}\n\n"
                yield "event: done\ndata: {}\n\n"
                return
            for line in response.iter_lines(decode_unicode=True):
                if session_id in _AGENT_STOP_REQUESTS:
                    _AGENT_STOP_REQUESTS.discard(session_id)
                    yield f"event: system\ndata: {json.dumps({'text': 'Stopped'})}\n\n"
                    break
                if not line or not line.startswith("data: "):
                    continue
                payload = line[6:].strip()
                if payload == "[DONE]":
                    break
                try:
                    parsed = json.loads(payload)
                except Exception:
                    continue
                delta = parsed.get("choices", [{}])[0].get("delta", {})
                chunk = delta.get("content")
                if chunk:
                    full_text += chunk
                    yield f"event: text\ndata: {json.dumps({'text': chunk})}\n\n"
                tool_calls = delta.get("tool_calls") or []
                for tool_call in tool_calls:
                    fn = tool_call.get("function") or {}
                    if fn.get("name"):
                        args = fn.get("arguments")
                        try:
                            parsed_args = json.loads(args) if isinstance(args, str) and args.strip() else args
                        except Exception:
                            parsed_args = args
                        yield f"event: tool_use\ndata: {json.dumps({'name': fn.get('name'), 'input': parsed_args})}\n\n"
        except Exception as exc:
            yield f"event: error\ndata: {json.dumps({'message': str(exc)})}\n\n"

        if full_text.strip():
            _AGENT_CHAT_SESSIONS.setdefault(session_id, []).append(
                {"role": "assistant", "text": full_text.strip(), "ts": int(time.time() * 1000)}
            )
            yield f"event: result\ndata: {json.dumps({'text': full_text.strip()})}\n\n"
        yield "event: done\ndata: {}\n\n"

    return Response(generate(), mimetype="text/event-stream")


## ── MCP / Google Integration Status ────────────────────────────────────────
#
# We check Google API connectivity for Gmail, Calendar, and Drive by looking
# for OAuth2 credentials on disk (token.json or ~/.config/archivist/google_token.json)
# and making a lightweight API call to each service.

_GOOGLE_TOKEN_PATHS = [
    os.path.join(os.path.dirname(__file__), "google_token.json"),
    os.path.expanduser("~/.config/archivist/google_token.json"),
    os.path.expanduser("~/.credentials/google_token.json"),
]

_GOOGLE_ACCOUNT_TOKEN_DIRS = [
    os.getenv("ARCHIVIST_GOOGLE_TOKENS_DIR", "").strip(),
    os.path.expanduser("~/.config/archivist/google-accounts"),
    os.path.expanduser("~/.credentials/archivist/google-accounts"),
]

_GOOGLE_CLIENT_SECRET_PATHS = [
    os.path.join(os.path.dirname(__file__), "client_secret.json"),
    os.path.join(os.path.dirname(__file__), "credentials.json"),
    os.path.expanduser("~/.config/archivist/client_secret.json"),
]

_GOOGLE_AUTH_PENDING: dict[str, dict] = {}
_GOOGLE_AUTH_MAX_AGE_S = 1800

_GOOGLE_SERVICE_CATALOG = [
    {
        "key": "gmail",
        "id": "gmail",
        "name": "Gmail",
        "description": "Email archive & search",
        "scopes": [
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.send",
        ],
        "checker": "_check_gmail",
        "aliases": ["gmail"],
        "enabled_by_default": True,
    },
    {
        "key": "calendar",
        "id": "google-calendar",
        "name": "Google Calendar",
        "description": "Calendar events & scheduling",
        "scopes": ["https://www.googleapis.com/auth/calendar.readonly"],
        "checker": "_check_calendar",
        "aliases": ["calendar", "google-calendar", "google_calendar"],
        "enabled_by_default": True,
    },
    {
        "key": "drive",
        "id": "google-drive",
        "name": "Google Drive",
        "description": "Document & file archive",
        "scopes": ["https://www.googleapis.com/auth/drive.readonly"],
        "checker": "_check_drive",
        "aliases": ["drive", "google-drive", "google_drive"],
        "enabled_by_default": True,
    },
    {
        "key": "chat",
        "id": "google-chat",
        "name": "Google Chat",
        "description": "Chat spaces & message archive",
        "scopes": [
            "https://www.googleapis.com/auth/chat.spaces.readonly",
            "https://www.googleapis.com/auth/chat.messages.readonly",
        ],
        "checker": "_check_google_chat",
        "aliases": ["chat", "google-chat", "google_chat"],
        "enabled_by_default": False,
    },
]

_GOOGLE_DEFAULT_SERVICE_KEYS = [
    str(definition.get("key"))
    for definition in _GOOGLE_SERVICE_CATALOG
    if definition.get("enabled_by_default")
]

_GOOGLE_SERVICE_KEY_ALIASES: dict[str, str] = {}
for _google_definition in _GOOGLE_SERVICE_CATALOG:
    _canonical_key = str(_google_definition.get("key") or "").strip().lower()
    for _alias in _google_definition.get("aliases", []) or []:
        _normalized_alias = str(_alias or "").strip().lower().replace("_", "-")
        if _normalized_alias:
            _GOOGLE_SERVICE_KEY_ALIASES[_normalized_alias] = _canonical_key
    if _canonical_key:
        _GOOGLE_SERVICE_KEY_ALIASES[_canonical_key] = _canonical_key
        _service_id = str(_google_definition.get("id") or "").strip().lower().replace("_", "-")
        if _service_id:
            _GOOGLE_SERVICE_KEY_ALIASES[_service_id] = _canonical_key


def _parse_google_config_list(raw: str | None) -> list[str]:
    text = str(raw or "").strip()
    if not text:
        return []
    return [item for item in re.split(r"[\s,;]+", text) if item]


def _google_enabled_service_keys() -> list[str]:
    configured = _parse_google_config_list(os.getenv("ARCHIVIST_GOOGLE_SERVICES", ""))
    if not configured:
        return list(_GOOGLE_DEFAULT_SERVICE_KEYS)

    enabled: list[str] = []
    seen: set[str] = set()
    unknown: list[str] = []
    for raw_key in configured:
        normalized = str(raw_key or "").strip().lower().replace("_", "-")
        canonical = _GOOGLE_SERVICE_KEY_ALIASES.get(normalized)
        if not canonical:
            unknown.append(raw_key)
            continue
        if canonical in seen:
            continue
        seen.add(canonical)
        enabled.append(canonical)

    if unknown:
        logging.warning("Ignoring unknown Google service keys: %s", ", ".join(sorted(set(unknown))))

    return enabled or list(_GOOGLE_DEFAULT_SERVICE_KEYS)


def _google_enabled_service_definitions() -> list[dict]:
    enabled = set(_google_enabled_service_keys())
    return [
        definition
        for definition in _GOOGLE_SERVICE_CATALOG
        if str(definition.get("key")) in enabled
    ]


def _google_enabled_service_summaries() -> list[dict]:
    return [
        {
            "key": definition["key"],
            "id": definition["id"],
            "name": definition["name"],
            "description": definition["description"],
            "scopes": list(definition.get("scopes") or []),
        }
        for definition in _google_enabled_service_definitions()
    ]


def _google_extra_scopes() -> list[str]:
    return _parse_google_config_list(os.getenv("ARCHIVIST_GOOGLE_EXTRA_SCOPES", ""))


def _google_requested_scopes() -> list[str]:
    scopes: list[str] = []
    seen: set[str] = set()
    for definition in _google_enabled_service_definitions():
        for scope in definition.get("scopes", []) or []:
            clean = str(scope or "").strip()
            if not clean or clean in seen:
                continue
            seen.add(clean)
            scopes.append(clean)
    for scope in _google_extra_scopes():
        clean = str(scope or "").strip()
        if not clean or clean in seen:
            continue
        seen.add(clean)
        scopes.append(clean)
    return scopes


def _google_service_result(definition: dict, *, connected: bool = False, status: str = "unknown",
                           error: str | None = None, account: str | None = None) -> dict:
    result = {
        "id": definition["id"],
        "name": definition["name"],
        "description": definition["description"],
        "connected": connected,
        "status": status,
        "error": error,
    }
    if account:
        result["account"] = account
    return result

def _find_file(candidates: list[str]) -> str | None:
    for p in candidates:
        if os.path.isfile(p):
            return p
    return None


def _google_token_dir_candidates() -> list[Path]:
    out: list[Path] = []
    seen: set[str] = set()
    for raw in _GOOGLE_ACCOUNT_TOKEN_DIRS:
        clean = str(raw or "").strip()
        if not clean:
            continue
        path = Path(os.path.expanduser(clean))
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        out.append(path)
    return out


def _google_token_file_candidates() -> list[Path]:
    out: list[Path] = []
    seen: set[str] = set()

    for raw in _GOOGLE_TOKEN_PATHS:
        path = Path(os.path.expanduser(raw))
        key = str(path)
        if key in seen or not path.is_file():
            continue
        seen.add(key)
        out.append(path)

    for token_dir in _google_token_dir_candidates():
        if not token_dir.is_dir():
            continue
        for path in sorted(token_dir.glob("*.json")):
            key = str(path)
            if key in seen or not path.is_file():
                continue
            seen.add(key)
            out.append(path)

    return out


def _google_legacy_token_paths() -> set[str]:
    return {str(Path(os.path.expanduser(raw))) for raw in _GOOGLE_TOKEN_PATHS}


def _is_legacy_google_token_path(path: Path) -> bool:
    return str(path) in _google_legacy_token_paths()


def _google_account_slug(value: str | None) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[^a-z0-9._-]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text or f"google-account-{int(time.time())}"


def _preferred_google_token_dir() -> Path:
    return _google_token_dir_candidates()[0]


def _google_account_token_path(account_hint: str | None) -> Path:
    return _preferred_google_token_dir() / f"{_google_account_slug(account_hint)}.json"


def _cleanup_google_auth_pending(now_ts: float | None = None) -> None:
    cutoff = float(now_ts or time.time()) - _GOOGLE_AUTH_MAX_AGE_S
    expired = [state for state, payload in _GOOGLE_AUTH_PENDING.items() if float(payload.get("created_at") or 0) < cutoff]
    for state in expired:
        _GOOGLE_AUTH_PENDING.pop(state, None)


def _google_callback_url() -> str:
    host_url = str(request.host_url or "").strip() or "http://localhost:5050/"
    parts = urlsplit(host_url)
    scheme = "http"
    hostname = os.getenv("ARCHIVIST_GOOGLE_OAUTH_CALLBACK_HOST", "127.0.0.1").strip() or "127.0.0.1"
    netloc = hostname
    if parts.port:
        default_port = 80
        if parts.port != default_port:
            netloc = f"{hostname}:{parts.port}"
    return urlunsplit((scheme, netloc, "/api/integrations/oauth/google/callback", "", ""))


def _google_oauth_result_page(message: str, success: bool) -> str:
    safe_message = json.dumps(str(message))
    tone = "#22c55e" if success else "#ef4444"
    title = "Google Authorization Complete" if success else "Google Authorization Failed"
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{title}</title>
    <style>
      body {{
        margin: 0;
        font-family: Arial, sans-serif;
        background: #0b1220;
        color: #e5eefc;
        display: grid;
        min-height: 100vh;
        place-items: center;
      }}
      main {{
        width: min(92vw, 520px);
        background: rgba(15, 23, 42, 0.94);
        border: 1px solid rgba(148, 163, 184, 0.2);
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 20px 50px rgba(2, 6, 23, 0.45);
      }}
      h1 {{
        margin: 0 0 10px;
        font-size: 1.2rem;
      }}
      p {{
        margin: 0;
        line-height: 1.5;
        color: #cbd5e1;
      }}
      .status {{
        display: inline-block;
        margin-bottom: 12px;
        padding: 6px 10px;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 700;
        background: rgba(255, 255, 255, 0.08);
        color: {tone};
      }}
    </style>
  </head>
  <body>
    <main>
      <div class="status">{title}</div>
      <h1>{title}</h1>
      <p id="message"></p>
    </main>
    <script>
      const message = {safe_message};
      document.getElementById("message").textContent = message;
      if (window.opener && window.location.origin) {{
        window.opener.postMessage({{
          type: "archivist-google-oauth-complete",
          success: {str(success).lower()},
          message,
        }}, window.location.origin);
      }}
    </script>
  </body>
</html>"""


def _service_status_summary(services: list[dict]) -> dict:
    connected = sum(1 for service in services if service.get("connected"))
    total = len(services)
    return {
        "connected": connected > 0,
        "fully_connected": total > 0 and connected == total,
        "connected_services": connected,
        "service_count": total,
    }


def _make_no_creds(definition: dict, error: str) -> dict:
    return _google_service_result(definition, status="needs_auth", error=error)


def _empty_google_service_results(error: str) -> list[dict]:
    return [_make_no_creds(definition, error) for definition in _google_enabled_service_definitions()]


def _normalize_google_account(token_path: Path, services: list[dict], load_error: str | None = None) -> dict:
    account_email = next((str(service.get("account") or "").strip() for service in services if service.get("account")), "")
    label = account_email or token_path.stem or "Google account"
    service_summary = _service_status_summary(services)
    return {
        "id": _google_account_slug(account_email or token_path.stem),
        "label": label,
        "account": account_email or None,
        "token_path": str(token_path),
        "legacy": _is_legacy_google_token_path(token_path),
        "load_error": load_error,
        "services": services,
        **service_summary,
    }


def _flatten_google_integrations(accounts: list[dict]) -> list[dict]:
    items: list[dict] = []
    for account in accounts:
        account_label = str(account.get("account") or account.get("label") or "").strip() or None
        account_id = str(account.get("id") or "").strip() or None
        for service in account.get("services", []) or []:
            row = dict(service)
            row["key"] = f"{service.get('id')}:{account_id or account_label or len(items)}"
            if account_label:
                row["account"] = account_label
            if account_id:
                row["account_id"] = account_id
            items.append(row)
    items.sort(key=lambda item: (str(item.get("account") or ""), str(item.get("id") or "")))
    return items


def _aggregate_google_services(accounts: list[dict]) -> list[dict]:
    aggregate: dict[str, dict] = {}
    for account in accounts:
        for service in account.get("services", []) or []:
            service_id = str(service.get("id") or "").strip()
            if not service_id:
                continue
            current = aggregate.get(service_id)
            candidate = {
                "id": service_id,
                "name": service.get("name"),
                "status": service.get("status"),
                "connected": bool(service.get("connected")),
                "error": service.get("error"),
            }
            if current is None:
                aggregate[service_id] = candidate
                continue
            if candidate["connected"] and not current.get("connected"):
                aggregate[service_id] = candidate
            elif current.get("status") != "connected" and candidate.get("status") == "needs_auth":
                aggregate[service_id] = candidate
    ordered_ids = [str(definition.get("id")) for definition in _google_enabled_service_definitions()]
    return [aggregate[service_id] for service_id in ordered_ids if service_id in aggregate]


def _google_summary(accounts: list[dict]) -> dict:
    token_paths = _google_token_file_candidates()
    connected_accounts = sum(1 for account in accounts if account.get("connected"))
    fully_connected_accounts = sum(1 for account in accounts if account.get("fully_connected"))
    return {
        "connected": connected_accounts > 0,
        "configured": bool(_find_file(_GOOGLE_CLIENT_SECRET_PATHS) or token_paths),
        "accountCount": len(accounts),
        "connectedAccountCount": connected_accounts,
        "fullyConnectedAccountCount": fully_connected_accounts,
        "accounts": accounts,
        "services": _aggregate_google_services(accounts),
        "enabledServices": _google_enabled_service_summaries(),
        "requestedScopes": _google_requested_scopes(),
        "tokenPaths": [str(path) for path in token_paths],
        "clientSecretPath": _find_file(_GOOGLE_CLIENT_SECRET_PATHS),
    }


def _load_google_creds(token_path: str | Path | None = None):
    """Load cached OAuth2 credentials, refreshing if needed. Returns (creds, error, token_path)."""
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
    except ImportError:
        return None, "google-auth not installed (pip install google-auth google-auth-oauthlib google-api-python-client)", None

    resolved_token_path = Path(token_path).expanduser() if token_path else None
    if resolved_token_path is None:
        first = _find_file(_GOOGLE_TOKEN_PATHS)
        resolved_token_path = Path(first).expanduser() if first else None
    if resolved_token_path is None or not resolved_token_path.is_file():
        return None, "no_token", None

    requested_scopes = _google_requested_scopes()

    try:
        creds = Credentials.from_authorized_user_file(str(resolved_token_path), requested_scopes)
    except Exception as e:
        return None, f"Invalid token file: {e}", str(resolved_token_path)

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            # Write back the refreshed token
            with open(resolved_token_path, "w") as f:
                f.write(creds.to_json())
        except Exception as e:
            return None, f"Token refresh failed: {e}", str(resolved_token_path)

    if not creds or not creds.valid:
        return None, "Token expired or invalid — re-authorize", str(resolved_token_path)

    return creds, None, str(resolved_token_path)


def _check_gmail(creds) -> dict:
    definition = next(defn for defn in _GOOGLE_SERVICE_CATALOG if defn["id"] == "gmail")
    result = _google_service_result(definition)
    try:
        from googleapiclient.discovery import build
        svc = build("gmail", "v1", credentials=creds, cache_discovery=False)
        profile = svc.users().getProfile(userId="me").execute()
        result["connected"] = True
        result["status"] = "connected"
        result["account"] = profile.get("emailAddress")
    except Exception as e:
        msg = str(e)
        if "403" in msg or "insufficient" in msg.lower() or "scope" in msg.lower():
            result["status"] = "needs_auth"
            result["error"] = "Gmail scope not granted — re-authorize with gmail.readonly"
        else:
            result["status"] = "error"
            result["error"] = msg[:200]
    return result


def _check_calendar(creds) -> dict:
    definition = next(defn for defn in _GOOGLE_SERVICE_CATALOG if defn["id"] == "google-calendar")
    result = _google_service_result(definition)
    try:
        from googleapiclient.discovery import build
        svc = build("calendar", "v3", credentials=creds, cache_discovery=False)
        svc.calendarList().list(maxResults=1).execute()
        result["connected"] = True
        result["status"] = "connected"
    except Exception as e:
        msg = str(e)
        if "403" in msg or "insufficient" in msg.lower() or "scope" in msg.lower():
            result["status"] = "needs_auth"
            result["error"] = "Calendar scope not granted — re-authorize with calendar.readonly"
        else:
            result["status"] = "error"
            result["error"] = msg[:200]
    return result


def _check_drive(creds) -> dict:
    definition = next(defn for defn in _GOOGLE_SERVICE_CATALOG if defn["id"] == "google-drive")
    result = _google_service_result(definition)
    try:
        from googleapiclient.discovery import build
        svc = build("drive", "v3", credentials=creds, cache_discovery=False)
        svc.about().get(fields="user").execute()
        result["connected"] = True
        result["status"] = "connected"
    except Exception as e:
        msg = str(e)
        if "403" in msg or "insufficient" in msg.lower() or "scope" in msg.lower():
            result["status"] = "needs_auth"
            result["error"] = "Drive scope not granted — re-authorize with drive.readonly"
        else:
            result["status"] = "error"
            result["error"] = msg[:200]
    return result


def _check_google_chat(creds) -> dict:
    definition = next(defn for defn in _GOOGLE_SERVICE_CATALOG if defn["id"] == "google-chat")
    result = _google_service_result(definition)
    try:
        from googleapiclient.discovery import build
        svc = build("chat", "v1", credentials=creds, cache_discovery=False)
        svc.spaces().list(pageSize=1).execute()
        result["connected"] = True
        result["status"] = "connected"
    except Exception as e:
        msg = str(e)
        if "403" in msg or "insufficient" in msg.lower() or "scope" in msg.lower():
            result["status"] = "needs_auth"
            result["error"] = "Google Chat scope not granted — re-authorize with chat.spaces.readonly and chat.messages.readonly"
        else:
            result["status"] = "error"
            result["error"] = msg[:200]
    return result


def _discover_google_account_email(creds) -> str | None:
    result = _check_gmail(creds)
    account = str(result.get("account") or "").strip()
    return account or None


def _collect_google_accounts() -> list[dict]:
    accounts_by_key: dict[str, dict] = {}
    for token_path in _google_token_file_candidates():
        creds, error, _ = _load_google_creds(token_path)
        if creds is None:
            account = _normalize_google_account(token_path, _empty_google_service_results(str(error or "Unknown error")), str(error or "Unknown error"))
        else:
            services: list[dict] = []
            for definition in _google_enabled_service_definitions():
                checker_name = str(definition.get("checker") or "").strip()
                checker = globals().get(checker_name)
                if not callable(checker):
                    services.append(_google_service_result(definition, status="error", error=f"{definition['name']} checker unavailable"))
                    continue
                services.append(checker(creds))
            account = _normalize_google_account(token_path, services)

        dedupe_key = str(account.get("account") or "").strip().lower() or f"path:{token_path}"
        existing = accounts_by_key.get(dedupe_key)
        if existing is None:
            accounts_by_key[dedupe_key] = account
            continue
        if existing.get("legacy") and not account.get("legacy"):
            accounts_by_key[dedupe_key] = account

    accounts = list(accounts_by_key.values())
    accounts.sort(key=lambda item: (str(item.get("account") or item.get("label") or "").lower(), str(item.get("token_path") or "")))
    return accounts


_GOOGLE_ARCHIVE_ROOT = Path(os.getenv("ARCHIVIST_GOOGLE_ARCHIVE_DIR", "~/.config/archivist/google-archive")).expanduser()
_GOOGLE_JOURNAL_SOURCES = [
    {
        "key": "calendar",
        "label": "Google Calendar",
        "shortLabel": "Calendar",
        "cadence": "Schedule pressure",
        "contribution": "Meetings, appointments, recurring obligations, locations",
        "detail": "Calendar events establish the shape of each day and make meeting pressure visible instead of inferred.",
        "chipClass": "workspace-chip--accent",
        "accent": "#90b6ff",
    },
    {
        "key": "email",
        "label": "Gmail",
        "shortLabel": "Email",
        "cadence": "Inbox pressure",
        "contribution": "Subjects, senders, timing, reply load, async obligations",
        "detail": "Email gives the journal its async obligation trail: what arrived, who it came from, and how crowded the day became.",
        "chipClass": "workspace-chip--warning",
        "accent": "#f2b36d",
    },
    {
        "key": "drive",
        "label": "Google Drive",
        "shortLabel": "Drive",
        "cadence": "Document churn",
        "contribution": "Files, folders, ownership, modified timestamps, shared workspaces",
        "detail": "Drive metadata shows when files moved, changed, or accumulated around a day, even when the document body was not exported.",
        "chipClass": "",
        "accent": "#7cc7ff",
    },
    {
        "key": "chat",
        "label": "Google Chat",
        "shortLabel": "Chat",
        "cadence": "Conversation flow",
        "contribution": "Spaces, message senders, message text, threads, team conversation load",
        "detail": "Chat history captures the conversational side of work that never shows up in calendar or email.",
        "chipClass": "",
        "accent": "#f8a86a",
    },
    {
        "key": "git",
        "label": "Git Repos",
        "shortLabel": "Git",
        "cadence": "Code commits",
        "contribution": "Commits, repos, authors, development activity across all tracked projects",
        "detail": "Git commit history across local repositories shows what was actually built, fixed, or shipped each day.",
        "chipClass": "workspace-chip--success",
        "accent": "#7ad4a0",
    },
    {
        "key": "media",
        "label": "Media Pipeline",
        "shortLabel": "Media",
        "cadence": "Processed recordings",
        "contribution": "Transcribed and summarized screen recordings, meetings, and audio files",
        "detail": "Media pipeline completions show what recordings were processed into searchable transcripts and summaries.",
        "chipClass": "",
        "accent": "#c4a0f2",
    },
    {
        "key": "github",
        "label": "GitHub",
        "shortLabel": "GitHub",
        "cadence": "PRs, issues, reviews",
        "contribution": "Pull requests, issues, code reviews, and releases across GitHub repositories",
        "detail": "GitHub activity shows collaboration beyond local commits: PRs opened, issues filed, reviews given, and releases shipped.",
        "chipClass": "",
        "accent": "#f0f0f0",
    },
]
_GOOGLE_IMPORT_LOCK = threading.Lock()
_GOOGLE_IMPORT_STATE = {
    "running": False,
    "message": None,
    "startedAt": None,
    "finishedAt": None,
    "accounts": [],
}
_GOOGLE_IMPORT_SCHEDULER_STOP = threading.Event()
_GOOGLE_IMPORT_INTERVAL_HOURS = float(os.getenv("ARCHIVIST_GOOGLE_IMPORT_INTERVAL_HOURS", "2").strip() or "2")
try:
    _GOOGLE_CALENDAR_INCREMENTAL_LOOKBACK_DAYS = max(1, int(os.getenv("ARCHIVIST_GOOGLE_CALENDAR_INCREMENTAL_LOOKBACK_DAYS", "45")))
except (TypeError, ValueError):
    _GOOGLE_CALENDAR_INCREMENTAL_LOOKBACK_DAYS = 45


def _google_archive_root() -> Path:
    _GOOGLE_ARCHIVE_ROOT.mkdir(parents=True, exist_ok=True)
    return _GOOGLE_ARCHIVE_ROOT


def _google_archive_account_dir(account: str | None) -> Path:
    return _google_archive_root() / _google_account_slug(account)


def _google_archive_summary_path() -> Path:
    return _google_archive_root() / "summary.json"


def _google_archive_journal_path() -> Path:
    return _google_archive_root() / "journal_overview.json"


def _google_archive_index_status_path() -> Path:
    return _google_archive_root() / "index_status.json"


def _google_archive_manifest_snapshots() -> list[dict]:
    root = _google_archive_root()
    if not root.exists():
        return []
    manifests: list[dict] = []
    for account_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        manifest_path = account_dir / "manifest.json"
        if not manifest_path.is_file():
            continue
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(payload, dict):
            continue
        manifests.append(
            {
                "account": str(payload.get("account") or account_dir.name).strip(),
                "imported_at": str(payload.get("imported_at") or "").strip(),
                "gmailMessages": int(payload.get("gmailMessages") or 0),
                "calendarEvents": int(payload.get("calendarEvents") or 0),
                "driveFiles": int(payload.get("driveFiles") or 0),
                "chatMessages": int(payload.get("chatMessages") or 0),
                "dayCount": int(payload.get("dayCount") or 0),
            }
        )
    return manifests


def _google_archive_fingerprint(manifests: list[dict] | None = None) -> str:
    snapshot = manifests if manifests is not None else _google_archive_manifest_snapshots()
    payload = {
        "archiveVersion": GOOGLE_ARCHIVE_CONTENT_VERSION,
        "embeddingModel": LOCAL_EMBEDDING_MODEL,
        "accounts": sorted(
            snapshot,
            key=lambda item: (str(item.get("account") or ""), str(item.get("imported_at") or "")),
        ),
    }
    return sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def _load_google_archive_index_status() -> dict:
    path = _google_archive_index_status_path()
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_google_archive_index_status(payload: dict) -> None:
    path = _google_archive_index_status_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _google_archive_needs_index_sync() -> tuple[bool, str]:
    manifests = _google_archive_manifest_snapshots()
    if not manifests:
        return False, "archive-empty"
    fingerprint = _google_archive_fingerprint(manifests)
    status = _load_google_archive_index_status()
    if not status:
        return True, "missing-status"
    if str(status.get("archiveFingerprint") or "").strip() != fingerprint:
        return True, "archive-changed"
    if str(status.get("archiveVersion") or "").strip() != GOOGLE_ARCHIVE_CONTENT_VERSION:
        return True, "content-version-changed"
    if str(status.get("embeddingModel") or "").strip() != LOCAL_EMBEDDING_MODEL:
        return True, "embedding-model-changed"
    if str(status.get("status") or "").strip() != "synced":
        return True, str(status.get("status") or "unsynced")
    return False, "synced"


def _load_persisted_google_journal_overview() -> dict | None:
    path = _google_archive_journal_path()
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    if int(payload.get("journalVersion") or 0) != _GOOGLE_JOURNAL_OVERVIEW_VERSION:
        return None
    if str(payload.get("archiveFingerprint") or "").strip() != _google_archive_fingerprint():
        return None
    return payload


def _google_display_tz():
    tz_name = str(os.getenv("ARCHIVIST_DISPLAY_TIMEZONE") or os.getenv("TZ") or "America/Chicago").strip() or "America/Chicago"
    try:
        return ZoneInfo(tz_name)
    except Exception:
        return timezone.utc


def _jsonl_write(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False))
            handle.write("\n")


def _jsonl_read(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    out: list[dict] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for raw in handle:
            line = raw.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except Exception:
                continue
            if isinstance(item, dict):
                out.append(item)
    return out


def _google_api_build(service_name: str, version: str, creds):
    from googleapiclient.discovery import build
    return build(service_name, version, credentials=creds, cache_discovery=False)


def _google_strip_html(value: str) -> str:
    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", str(value or ""))
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = html_unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _google_b64decode(data: str | None) -> str:
    if not data:
        return ""
    padded = str(data) + "=" * ((4 - (len(str(data)) % 4)) % 4)
    try:
        raw = base64.urlsafe_b64decode(padded.encode("utf-8"))
    except Exception:
        return ""
    return raw.decode("utf-8", errors="replace")


def _google_gmail_headers(payload: dict) -> dict[str, str]:
    out: dict[str, str] = {}
    for header in payload.get("headers", []) or []:
        name = str(header.get("name") or "").strip().lower()
        value = str(header.get("value") or "").strip()
        if name and value and name not in out:
            out[name] = value
    return out


def _google_gmail_text(payload: dict) -> str:
    plain_parts: list[str] = []
    html_parts: list[str] = []

    def walk(part: dict) -> None:
        mime_type = str(part.get("mimeType") or "").lower()
        body = part.get("body") or {}
        data = _google_b64decode(body.get("data"))
        if data:
            if mime_type.startswith("text/plain"):
                plain_parts.append(data)
            elif mime_type.startswith("text/html"):
                html_parts.append(data)
        for child in part.get("parts", []) or []:
            if isinstance(child, dict):
                walk(child)

    walk(payload or {})
    if plain_parts:
        return re.sub(r"\s+", " ", "\n\n".join(plain_parts)).strip()
    if html_parts:
        return _google_strip_html("\n\n".join(html_parts))
    body = (payload or {}).get("body") or {}
    return _google_b64decode(body.get("data"))


def _google_parse_datetime(raw_value: str | None):
    text = str(raw_value or "").strip()
    if not text:
        return None
    try:
        dt = parsedate_to_datetime(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _google_datetime_from_ms(raw_ms) -> datetime | None:
    try:
        value = int(raw_ms)
    except Exception:
        return None
    return datetime.fromtimestamp(value / 1000.0, tz=timezone.utc)


def _google_local_day(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.astimezone(_google_display_tz()).date().isoformat()


def _google_parse_iso_datetime(raw_value: str | None) -> datetime | None:
    text = str(raw_value or "").strip()
    if not text:
        return None
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _google_since_datetime(since_date: str | None) -> datetime | None:
    text = str(since_date or "").strip()
    if not text:
        return None
    parsed = _google_parse_iso_datetime(text)
    if parsed is not None:
        return parsed
    for fmt in ("%Y/%m/%d", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=timezone.utc)
        except Exception:
            continue
    return None


def _google_account_record_url(service: str, record_id: str, calendar_id: str | None = None) -> str | None:
    record = str(record_id or "").strip()
    if not record:
        return None
    if service == "gmail":
        return f"https://mail.google.com/mail/u/0/#all/{record}"
    if service == "calendar" and calendar_id:
        return f"https://calendar.google.com/calendar/u/0/r?cid={calendar_id}"
    if service == "drive":
        return f"https://drive.google.com/open?id={record}"
    return None


def _fetch_google_gmail_records(account_email: str, creds, state: dict | None = None, since_date: str | None = None) -> list[dict]:
    service = _google_api_build("gmail", "v1", creds)
    records: list[dict] = []
    page_token = None
    fetched = 0
    query = f"after:{since_date}" if since_date else None
    while True:
        kwargs: dict = dict(userId="me", includeSpamTrash=False, maxResults=500, pageToken=page_token)
        if query:
            kwargs["q"] = query
        response = service.users().messages().list(**kwargs).execute()
        for item in response.get("messages", []) or []:
            message = service.users().messages().get(userId="me", id=item["id"], format="full").execute()
            payload = message.get("payload") or {}
            headers = _google_gmail_headers(payload)
            dt = _google_datetime_from_ms(message.get("internalDate")) or _google_parse_datetime(headers.get("date"))
            body_text = _google_gmail_text(payload)
            snippet = str(message.get("snippet") or "").strip()
            if snippet and body_text and snippet in body_text:
                body_excerpt = body_text[:20000]
            elif body_text:
                body_excerpt = body_text[:20000]
            else:
                body_excerpt = snippet[:20000]
            record = {
                "service": "gmail",
                "account": account_email,
                "id": str(message.get("id") or ""),
                "thread_id": str(message.get("threadId") or ""),
                "labels": list(message.get("labelIds") or []),
                "subject": headers.get("subject") or "(no subject)",
                "from": headers.get("from") or "",
                "to": headers.get("to") or "",
                "cc": headers.get("cc") or "",
                "date": dt.isoformat() if dt else None,
                "day": _google_local_day(dt),
                "snippet": snippet,
                "body": body_excerpt,
                "url": _google_account_record_url("gmail", str(message.get("id") or "")),
            }
            records.append(record)
            fetched += 1
            if state is not None and fetched % 25 == 0:
                state["message"] = f"Imported {fetched} Gmail messages from {account_email}."
        page_token = response.get("nextPageToken")
        if not page_token:
            break
    return records


def _google_calendar_event_day(event: dict) -> str | None:
    start = event.get("start") or {}
    raw_dt = start.get("dateTime") or start.get("date")
    if not raw_dt:
        return None
    try:
        if "T" in str(raw_dt):
            dt = datetime.fromisoformat(str(raw_dt).replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return _google_local_day(dt)
        return str(raw_dt)
    except Exception:
        return None


def _fetch_google_calendar_records(account_email: str, creds, state: dict | None = None, since_date: str | None = None) -> list[dict]:
    service = _google_api_build("calendar", "v3", creds)
    calendars: list[dict] = []
    page_token = None
    while True:
        response = service.calendarList().list(pageToken=page_token, maxResults=250).execute()
        calendars.extend(response.get("items", []) or [])
        page_token = response.get("nextPageToken")
        if not page_token:
            break

    now_utc = datetime.now(timezone.utc)
    if since_date:
        # since_date may be YYYY/MM/DD (from Gmail query) — convert to RFC 3339
        cal_date = since_date.replace("/", "-")
        time_min = f"{cal_date}T00:00:00Z"
    else:
        time_min = datetime(2000, 1, 1, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
    time_max = (now_utc + timedelta(days=366)).isoformat().replace("+00:00", "Z")
    records: list[dict] = []
    fetched = 0

    for calendar in calendars:
        calendar_id = str(calendar.get("id") or "").strip()
        if not calendar_id:
            continue
        event_token = None
        try:
          while True:
            response = service.events().list(
                calendarId=calendar_id,
                singleEvents=True,
                showDeleted=False,
                orderBy="startTime",
                timeMin=time_min,
                timeMax=time_max,
                maxResults=2500,
                pageToken=event_token,
            ).execute()
            for event in response.get("items", []) or []:
                start = event.get("start") or {}
                end = event.get("end") or {}
                record = {
                    "service": "calendar",
                    "account": account_email,
                    "calendar_id": calendar_id,
                    "calendar_summary": str(calendar.get("summary") or calendar.get("id") or "").strip(),
                    "id": str(event.get("id") or ""),
                    "status": str(event.get("status") or ""),
                    "summary": str(event.get("summary") or "(untitled event)").strip(),
                    "description": str(event.get("description") or "").strip()[:20000],
                    "location": str(event.get("location") or "").strip(),
                    "start": start.get("dateTime") or start.get("date"),
                    "end": end.get("dateTime") or end.get("date"),
                    "all_day": bool(start.get("date") and not start.get("dateTime")),
                    "day": _google_calendar_event_day(event),
                    "attendees": [str(item.get("email") or item.get("displayName") or "").strip() for item in (event.get("attendees") or []) if str(item.get("email") or item.get("displayName") or "").strip()],
                    "url": str(event.get("htmlLink") or _google_account_record_url("calendar", str(event.get("id") or ""), calendar_id) or ""),
                }
                records.append(record)
                fetched += 1
                if state is not None and fetched % 25 == 0:
                    state["message"] = f"Imported {fetched} calendar events from {account_email}."
            event_token = response.get("nextPageToken")
            if not event_token:
                break
        except Exception as cal_err:
            logging.warning("Skipping calendar %s: %s", calendar_id, cal_err)
            continue

    return records


def _fetch_google_drive_records(account_email: str, creds, state: dict | None = None, since_date: str | None = None) -> list[dict]:
    service = _google_api_build("drive", "v3", creds)
    records: list[dict] = []
    page_token = None
    fetched = 0
    filters = ["trashed = false"]
    since_dt = _google_since_datetime(since_date)
    if since_dt is not None:
        filters.append(f"modifiedTime > '{since_dt.isoformat().replace('+00:00', 'Z')}'")
    query = " and ".join(filters)
    while True:
        response = service.files().list(
            pageSize=1000,
            pageToken=page_token,
            q=query,
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
            fields=(
                "nextPageToken, files("
                "id, name, mimeType, description, createdTime, modifiedTime, "
                "owners(displayName,emailAddress), size, webViewLink, starred, shared, trashed, parents"
                ")"
            ),
        ).execute()
        for item in response.get("files", []) or []:
            modified = _google_parse_iso_datetime(item.get("modifiedTime"))
            created = _google_parse_iso_datetime(item.get("createdTime"))
            dt = modified or created
            owners = []
            for owner in item.get("owners", []) or []:
                owner_text = str(owner.get("emailAddress") or owner.get("displayName") or "").strip()
                if owner_text:
                    owners.append(owner_text)
            records.append(
                {
                    "service": "drive",
                    "account": account_email,
                    "id": str(item.get("id") or ""),
                    "name": str(item.get("name") or "(untitled file)").strip(),
                    "mime_type": str(item.get("mimeType") or "").strip(),
                    "description": str(item.get("description") or "").strip()[:20000],
                    "created_time": created.isoformat() if created else None,
                    "modified_time": modified.isoformat() if modified else None,
                    "day": _google_local_day(dt),
                    "owners": owners,
                    "size": int(item.get("size") or 0) if str(item.get("size") or "").isdigit() else 0,
                    "starred": bool(item.get("starred")),
                    "shared": bool(item.get("shared")),
                    "trashed": bool(item.get("trashed")),
                    "parent_ids": [str(parent).strip() for parent in (item.get("parents") or []) if str(parent).strip()],
                    "url": str(item.get("webViewLink") or _google_account_record_url("drive", str(item.get("id") or "")) or ""),
                }
            )
            fetched += 1
            if state is not None and fetched % 50 == 0:
                state["message"] = f"Imported {fetched} Drive files from {account_email}."
        page_token = response.get("nextPageToken")
        if not page_token:
            break
    return records


def _google_chat_message_text(message: dict) -> str:
    text = str(message.get("text") or "").strip()
    if text:
        return text[:20000]
    fallback_parts: list[str] = []
    for attachment in message.get("attachment") or []:
        title = str(attachment.get("name") or attachment.get("contentName") or "").strip()
        if title:
            fallback_parts.append(title)
    for annotation in message.get("annotations") or []:
        chip = str(annotation.get("displayName") or "").strip()
        if chip:
            fallback_parts.append(chip)
    return "\n".join(fallback_parts)[:20000]


def _fetch_google_chat_records(account_email: str, creds, state: dict | None = None, since_date: str | None = None) -> list[dict]:
    service = _google_api_build("chat", "v1", creds)
    records: list[dict] = []
    spaces_token = None
    fetched = 0
    since_dt = _google_since_datetime(since_date)
    while True:
        response = service.spaces().list(pageSize=200, pageToken=spaces_token).execute()
        for space in response.get("spaces", []) or []:
            space_name = str(space.get("name") or "").strip()
            if not space_name:
                continue
            messages_token = None
            while True:
                messages_response = service.spaces().messages().list(parent=space_name, pageSize=1000, pageToken=messages_token).execute()
                for message in messages_response.get("messages", []) or []:
                    created = _google_parse_iso_datetime(message.get("createTime"))
                    if since_dt is not None and created is not None and created < since_dt:
                        continue
                    sender = ""
                    sender_payload = message.get("sender") or {}
                    if isinstance(sender_payload, dict):
                        display_name = str(sender_payload.get("displayName") or "").strip()
                        sender_name = str(sender_payload.get("name") or "").strip()
                        sender = display_name or sender_name
                    records.append(
                        {
                            "service": "chat",
                            "account": account_email,
                            "id": str(message.get("name") or ""),
                            "space_name": space_name,
                            "space_display_name": str(space.get("displayName") or space.get("name") or "").strip(),
                            "space_type": str(space.get("spaceType") or "").strip(),
                            "sender": sender,
                            "create_time": created.isoformat() if created else None,
                            "day": _google_local_day(created),
                            "thread_name": str((message.get("thread") or {}).get("name") or "").strip(),
                            "text": _google_chat_message_text(message),
                            "url": "",
                        }
                    )
                    fetched += 1
                    if state is not None and fetched % 50 == 0:
                        state["message"] = f"Imported {fetched} Chat messages from {account_email}."
                messages_token = messages_response.get("nextPageToken")
                if not messages_token:
                    break
        spaces_token = response.get("nextPageToken")
        if not spaces_token:
            break
    return records


def _google_archive_manifest_for_account(
    account_email: str,
    gmail_records: list[dict],
    calendar_records: list[dict],
    drive_records: list[dict],
    chat_records: list[dict],
) -> dict:
    touched_days = {
        str(record.get("day") or "").strip()
        for record in gmail_records + calendar_records + drive_records + chat_records
        if str(record.get("day") or "").strip()
    }
    calendars = {str(record.get("calendar_id") or "").strip() for record in calendar_records if str(record.get("calendar_id") or "").strip()}
    chat_spaces = {str(record.get("space_name") or "").strip() for record in chat_records if str(record.get("space_name") or "").strip()}
    return {
        "account": account_email,
        "imported_at": datetime.now(timezone.utc).isoformat(),
        "gmailMessages": len(gmail_records),
        "calendarEvents": len(calendar_records),
        "driveFiles": len(drive_records),
        "chatMessages": len(chat_records),
        "calendarCount": len(calendars),
        "chatSpaceCount": len(chat_spaces),
        "dayCount": len(touched_days),
    }


def _google_archive_record_key(record: dict) -> str:
    service = str(record.get("service") or "").strip().lower()
    record_id = str(record.get("id") or "").strip()
    account = str(record.get("account") or "").strip().lower()
    if service == "calendar":
        calendar_id = str(record.get("calendar_id") or "").strip().lower()
        return f"{service}:{account}:{calendar_id}:{record_id}"
    if service == "chat":
        space_name = str(record.get("space_name") or "").strip().lower()
        return f"{service}:{account}:{space_name}:{record_id}"
    return f"{service}:{account}:{record_id}"


def _merge_google_archive_records(existing: list[dict], incoming: list[dict]) -> list[dict]:
    records_by_key = {_google_archive_record_key(record): record for record in existing if _google_archive_record_key(record)}
    for record in incoming:
        key = _google_archive_record_key(record)
        if key:
            records_by_key[key] = record
    merged = list(records_by_key.values())
    merged.sort(key=lambda item: (str(item.get("day") or ""), str(item.get("id") or "")))
    return merged


def _write_google_account_archive(
    account_email: str,
    gmail_records: list[dict],
    calendar_records: list[dict],
    drive_records: list[dict],
    chat_records: list[dict],
    *,
    merge: bool = False,
) -> dict:
    account_dir = _google_archive_account_dir(account_email)
    account_dir.mkdir(parents=True, exist_ok=True)

    if merge:
        # Merge new records into existing JSONL, deduplicating by record id.
        existing_gmail = _jsonl_read(account_dir / "gmail_messages.jsonl")
        existing_calendar = _jsonl_read(account_dir / "calendar_events.jsonl")
        existing_drive = _jsonl_read(account_dir / "drive_files.jsonl")
        existing_chat = _jsonl_read(account_dir / "chat_messages.jsonl")
        gmail_records = _merge_google_archive_records(existing_gmail, gmail_records)
        calendar_records = _merge_google_archive_records(existing_calendar, calendar_records)
        drive_records = _merge_google_archive_records(existing_drive, drive_records)
        chat_records = _merge_google_archive_records(existing_chat, chat_records)

    _jsonl_write(account_dir / "gmail_messages.jsonl", gmail_records)
    _jsonl_write(account_dir / "calendar_events.jsonl", calendar_records)
    _jsonl_write(account_dir / "drive_files.jsonl", drive_records)
    _jsonl_write(account_dir / "chat_messages.jsonl", chat_records)
    manifest = _google_archive_manifest_for_account(account_email, gmail_records, calendar_records, drive_records, chat_records)
    (account_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


_GOOGLE_JOURNAL_OVERVIEW_VERSION = 25
_GOOGLE_JOURNAL_ROUTINE_CALENDAR_PATTERNS = [
    re.compile(r"^week \d+ of \d{4}$", re.IGNORECASE),
    re.compile(r"^(recycle and )?trash pickup$", re.IGNORECASE),
    re.compile(r"^grass$", re.IGNORECASE),
    re.compile(r"^jonas pickup$", re.IGNORECASE),
    re.compile(r"^\(untitled event\)$", re.IGNORECASE),
]
_GOOGLE_JOURNAL_THEME_RULES = [
    {
        "key": "engineering",
        "title": "Engineering push",
        "summary": "engineering work",
        "keywords": [
            "feat",
            "fix",
            "refactor",
            "deploy",
            "deployment",
            "docker",
            "release",
            "plugin",
            "api",
            "mcp",
            "indexing",
            "build",
            "infra",
            "lambda",
            "integration test",
            "test coverage",
            "auth flow",
            "reauth",
            "dashboard",
            "vector store",
        ],
    },
    {
        "key": "research",
        "title": "Research and ideas",
        "summary": "research, media, and idea work",
        "keywords": [
            "podcast",
            "video",
            "film",
            "sci-fi",
            "movie",
            "story",
            "narrative",
            "colony",
            "mission",
            "media",
            "recording",
            "transcript",
            "photo",
            "picture",
            "image",
            "screenshot",
            "camera",
            "drone",
            "ukraine",
            "startup",
            "funding",
            "patent",
            "valuation",
            "science",
            "robotics",
            "ai",
            "model",
            "recommendation",
            "misalignment",
            "personalization",
            "trust mechanism",
            "music",
            "jazz",
            "guitar",
            "chord",
            "harmony",
            "voicing",
            "practice",
            "theory",
            "coltrane",
            "hartman",
            "movie",
            "writing review",
            "learning",
            "project hail mary",
        ],
    },
    {
        "key": "hiring",
        "title": "Interviews and hiring",
        "summary": "interview and hiring work",
        "keywords": [
            "interview",
            "recruit",
            "candidate",
            "resume",
            "application",
            "job",
            "engineer",
            "principal architect",
            "lead engineer",
            "hm interview",
        ],
    },
    {
        "key": "finance",
        "title": "Paperwork and finance",
        "summary": "paperwork and finance",
        "keywords": [
            "invoice",
            "statement",
            "paystub",
            "bank",
            "credit card",
            "bill",
            "payment",
            "payroll",
            "tax",
            "legal agreement",
            "receipt",
            "application completion",
        ],
    },
    {
        "key": "security",
        "title": "Security and ops",
        "summary": "security and operational follow-up",
        "keywords": [
            "security",
            "token",
            "credential",
            "maintenance",
            "incident",
            "outage",
            "alert",
            "access",
            "password",
            "meter",
        ],
    },
    {
        "key": "planning",
        "title": "Planning and coordination",
        "summary": "planning and coordination",
        "keywords": [
            "planning",
            "sync",
            "standup",
            "review",
            "1:1",
            "kickoff",
            "roadmap",
            "team",
            "agenda",
            "notes",
            "journal",
        ],
    },
    {
        "key": "household",
        "title": "Household logistics",
        "summary": "household logistics",
        "keywords": [
            "trash",
            "recycle",
            "pickup",
            "grass",
            "plumb",
            "technician",
            "shipped",
            "delivery",
            "coffee",
            "repair",
            "energy efficiency",
            "air conditioner",
            "ac",
            "lights",
            "lighting",
            "smart-home",
            "smart home",
            "office air conditioner",
            "hygiene",
            "shower",
        ],
    },
    {
        "key": "health",
        "title": "Health and appointments",
        "summary": "health and appointment work",
        "keywords": [
            "therapy",
            "doctor",
            "medical",
            "dentist",
            "appointment",
            "health",
        ],
    },
    {
        "key": "family",
        "title": "Family logistics",
        "summary": "family logistics",
        "keywords": [
            "jonas",
            "school",
            "family",
            "kids",
            "pickup",
        ],
    },
    {
        "key": "travel",
        "title": "Travel logistics",
        "summary": "travel coordination",
        "keywords": [
            "flight",
            "hotel",
            "trip",
            "travel",
            "itinerary",
            "booking",
        ],
    },
    {
        "key": "communications",
        "title": "Inbox and coordination",
        "summary": "inbox triage and coordination",
        "keywords": [
            "follow up",
            "fwd:",
            "re:",
            "digest",
            "update",
            "confirmation",
            "next steps",
        ],
    },
]
_GOOGLE_JOURNAL_THEME_INDEX = {rule["key"]: rule for rule in _GOOGLE_JOURNAL_THEME_RULES}
_GOOGLE_JOURNAL_SOURCE_SAMPLE_WEIGHTS = {
    "calendar": 2.4,
    "email": 1.4,
    "drive": 1.9,
    "chat": 1.4,
    "git": 2.2,
    "media": 4.2,
    "github": 1.4,
}
_GOOGLE_JOURNAL_LOW_SIGNAL_MEDIA_PATTERNS = [
    re.compile(r"^(brief recording captures|visual scene transitions dominate|repeated voice commands|voice commands toggle|untranscribable speech|the clip shows|audio captures)\b", re.IGNORECASE),
]
_GOOGLE_JOURNAL_LOW_SIGNAL_MEDIA_CONTEXT_PATTERNS = [
    re.compile(r"\bminimal activity\b", re.IGNORECASE),
    re.compile(r"\blow-content capture\b", re.IGNORECASE),
    re.compile(r"\bno substantive (conversation|content)\b", re.IGNORECASE),
    re.compile(r"\bno structured activity\b", re.IGNORECASE),
    re.compile(r"\bno explicit decisions\b", re.IGNORECASE),
    re.compile(r"\bverbal content unrecoverable\b", re.IGNORECASE),
    re.compile(r"\bno transcription available\b", re.IGNORECASE),
    re.compile(r"\bspeech (?:is )?detected .* not transcribed\b", re.IGNORECASE),
    re.compile(r"\boverwhelmingly visual\b", re.IGNORECASE),
    re.compile(r"\bmostly static environment\b", re.IGNORECASE),
    re.compile(r"\bscene (?:change|changes|transition|transitions|state|states)\b", re.IGNORECASE),
    re.compile(r"\bchange detected\b", re.IGNORECASE),
    re.compile(r"\bmonitoring capture\b", re.IGNORECASE),
    re.compile(r"\bstatic[- ]camera\b", re.IGNORECASE),
    re.compile(r"\bvoice commands?\b", re.IGNORECASE),
    re.compile(r"\brepeated voice commands?\b", re.IGNORECASE),
    re.compile(r"\blighting control\b", re.IGNORECASE),
    re.compile(r"\buntranscribable speech\b", re.IGNORECASE),
    re.compile(r"\bsingle utterance\b", re.IGNORECASE),
    re.compile(r"\bno surrounding dialogue\b", re.IGNORECASE),
    re.compile(r"\bbrief interpersonal exchange\b", re.IGNORECASE),
    re.compile(r"\bunrecoverable speech\b", re.IGNORECASE),
    re.compile(r"\btranscription unavailable\b", re.IGNORECASE),
    re.compile(r"\bminimal recoverable audio\b", re.IGNORECASE),
]
_GOOGLE_JOURNAL_LOW_SIGNAL_EMAIL_PATTERNS = [
    re.compile(r"^(shipped\b|big .*savings|your order|delivery update|sale|promo|promotion|welcome to)\b", re.IGNORECASE),
    re.compile(r"^(skip the flight|are you happy to hear from us|limited time|last chance|deal alert)\b", re.IGNORECASE),
    re.compile(r"^(security alert|your .*security report|your .*token .*expire|your dependabot alerts|e-statement)\b", re.IGNORECASE),
]
_GOOGLE_JOURNAL_GIT_SUBJECT_PREFIX_RE = re.compile(
    r"^(feat|fix|chore|docs|refactor|test|tests|build|ci|perf|style)(\([^)]+\))?!?:\s*",
    re.IGNORECASE,
)
_GOOGLE_JOURNAL_MEDIA_REFERENCE_RE = re.compile(r"\[[^\]]+\]")


def _google_archive_is_routine_calendar_item(value: str | None) -> bool:
    text = str(value or "").strip()
    if not text:
        return False
    return any(pattern.match(text) for pattern in _GOOGLE_JOURNAL_ROUTINE_CALENDAR_PATTERNS)


def _google_archive_humanize_ref(value: str | None) -> str:
    text = str(value or "").strip().strip("/")
    if not text:
        return ""
    parts = [part for part in text.split("/") if part]
    if parts and parts[0].lower() in {"feat", "feature", "fix", "bugfix", "chore", "docs", "refactor", "test", "tests", "release", "hotfix"}:
        parts = parts[1:]
    text = " ".join(parts) if parts else text
    text = re.sub(r"\b[A-Z]{2,}-\d+\b", " ", text)
    text = text.replace("_", " ").replace("/", " ").replace("-", " ")
    text = re.sub(r"\be2e\b", "end to end", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip(" \t\r\n-–—:;,.")
    return text


def _google_archive_clean_markdown_text(value: str | None) -> str:
    text = html_unescape(str(value or ""))
    if not text.strip():
        return ""
    text = _GOOGLE_JOURNAL_MEDIA_REFERENCE_RE.sub("", text)
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[-*]\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" \t\r\n-–—:;,.")


def _google_archive_markdown_section(text: str | None, heading: str) -> str:
    source = str(text or "")
    if not source.strip():
        return ""
    pattern = re.compile(
        rf"(?ims)^\s*#+\s*{re.escape(heading)}\s*(.*?)(?=^\s*#+\s|\Z)"
    )
    match = pattern.search(source)
    if not match:
        return ""
    return _google_archive_clean_markdown_text(match.group(1))


def _google_archive_first_sentence(value: str | None, *, max_chars: int = 220) -> str:
    text = _google_archive_clean_markdown_text(value)
    if not text:
        return ""
    parts = re.split(r"(?<=[.!?])\s+", text)
    sentence = next((part.strip() for part in parts if part.strip()), text)
    return _google_archive_trim_text(sentence, max_chars=max_chars)


def _google_archive_media_memory_payload(artifacts: list[dict]) -> dict:
    for artifact in artifacts:
        if str(artifact.get("kind") or "").strip() != "memory":
            continue
        try:
            payload = json.loads(str(artifact.get("content") or ""))
        except Exception:
            continue
        if isinstance(payload, dict):
            return payload
    return {}


def _google_archive_media_context_overview(artifacts: list[dict], document_payload: dict | None = None) -> str:
    memory_payload = _google_archive_media_memory_payload(artifacts)
    memory_overview = _google_archive_clean_markdown_text(memory_payload.get("context_overview"))
    if memory_overview:
        return memory_overview

    document_text = ""
    if isinstance(document_payload, dict):
        document_text = str(document_payload.get("full_text") or "")
    if not document_text:
        for artifact in artifacts:
            if str(artifact.get("kind") or "").strip() == "document":
                document_text = str(artifact.get("content") or "")
                if document_text:
                    break
    if not document_text:
        return ""

    for heading in ("Context Overview", "Meeting Summary"):
        section = _google_archive_markdown_section(document_text, heading)
        if section:
            return _google_archive_first_sentence(section, max_chars=260)
    return _google_archive_first_sentence(document_text, max_chars=260)


def _google_archive_media_key_topics(artifacts: list[dict], document_payload: dict | None = None) -> list[str]:
    document_text = ""
    if isinstance(document_payload, dict):
        document_text = str(document_payload.get("full_text") or "")
    if not document_text:
        for artifact in artifacts:
            if str(artifact.get("kind") or "").strip() == "document":
                document_text = str(artifact.get("content") or "")
                if document_text:
                    break
    if not document_text:
        return []

    match = re.search(r"(?ims)^\s*#+\s*Key Topics\s*(.*?)(?=^\s*#+\s|\Z)", document_text)
    if not match:
        return []
    section = str(match.group(1) or "")

    topics: list[str] = []
    seen: set[str] = set()
    for raw_line in section.splitlines():
        if not raw_line.strip():
            continue
        if raw_line.lstrip().startswith(("-", "*")):
            raw_line = raw_line.lstrip()[1:].strip()
        cleaned = _google_archive_clean_markdown_text(raw_line)
        cleaned = re.sub(r"^\[[^\]]+\]\s*", "", cleaned).strip()
        cleaned = re.sub(r"^\d+(\.\d+)?s?\s*[–-]\s*\d+(\.\d+)?s?\s*", "", cleaned).strip()
        cleaned = re.sub(r"^[A-Za-z ]+:\s*", "", cleaned).strip()
        cleaned = _google_archive_trim_text(cleaned, max_chars=140)
        lowered = cleaned.lower()
        if not cleaned or lowered in seen:
            continue
        if _google_archive_media_topic_is_low_signal(cleaned):
            continue
        seen.add(lowered)
        topics.append(cleaned)
        if len(topics) >= 3:
            break
    return topics


def _google_archive_media_has_low_signal_context(*values: str) -> bool:
    return any(
        pattern.search(str(value or ""))
        for value in values
        if str(value or "").strip()
        for pattern in _GOOGLE_JOURNAL_LOW_SIGNAL_MEDIA_CONTEXT_PATTERNS
    )


def _google_archive_media_topic_is_low_signal(value: str | None) -> bool:
    text = _google_archive_clean_markdown_text(value)
    return bool(text) and _google_archive_media_has_low_signal_context(text)


def _google_archive_clean_topic_text(source: str, value: str | None) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip(" \t\r\n-–—:;,.")
    if not text:
        return ""
    if source == "email":
        while True:
            updated = re.sub(r"^(re|fw|fwd)\s*:\s*", "", text, flags=re.IGNORECASE).strip()
            if updated == text:
                break
            text = updated
        text = re.sub(r"^(message replied|new message|you have a new message)\s*:\s*", "", text, flags=re.IGNORECASE).strip()
        text = re.sub(r"^\[[^\]]+\]\s*", "", text).strip()
    elif source == "drive":
        path_obj = Path(text)
        if path_obj.suffix and len(path_obj.suffix) <= 6:
            text = path_obj.stem
        text = text.replace("_", " ")
    elif source in {"git", "github"}:
        text = re.sub(r"^\d+\s+commits?:\s*", "", text, flags=re.IGNORECASE).strip()
        text = re.sub(r"^Review on:\s*", "", text, flags=re.IGNORECASE).strip()
        match = re.match(r"^(Created|Deleted)\s+(branch|tag):\s*(.+)$", text, flags=re.IGNORECASE)
        if match:
            humanized = _google_archive_humanize_ref(match.group(3))
            return humanized
        text = _GOOGLE_JOURNAL_GIT_SUBJECT_PREFIX_RE.sub("", text).strip()
        if re.fullmatch(r"(push|create|created|delete|deleted|pr|review)", text, flags=re.IGNORECASE):
            return ""
    elif source == "calendar" and _google_archive_is_routine_calendar_item(text):
        lowered = text.lower()
        if re.match(r"^week \d+ of \d{4}$", lowered, re.IGNORECASE):
            return "the weekly calendar marker"
        if lowered == "(untitled event)":
            return "an untitled calendar hold"
    text = re.sub(r"\s+", " ", text).strip(" \t\r\n-–—:;,.")
    return text


def _google_archive_is_low_signal_topic(source: str, raw_text: str, cleaned_text: str) -> bool:
    if not cleaned_text:
        return True
    if source == "calendar" and _google_archive_is_routine_calendar_item(raw_text):
        return True
    if source == "media":
        return any(pattern.match(raw_text) for pattern in _GOOGLE_JOURNAL_LOW_SIGNAL_MEDIA_PATTERNS)
    if source == "email":
        return any(pattern.match(raw_text) for pattern in _GOOGLE_JOURNAL_LOW_SIGNAL_EMAIL_PATTERNS)
    return False


def _google_archive_trim_text(value: str | None, max_chars: int = 56, *, ellipsis: bool = True) -> str:
    clean = re.sub(r"\s+", " ", str(value or "")).strip(" \t\r\n-–—:;,.")
    if not clean:
        return ""
    if max_chars <= 0:
        return clean
    if len(clean) <= max_chars:
        return clean
    reserve = 1 if ellipsis else 0
    clipped = clean[: max(1, max_chars - reserve)].rsplit(" ", 1)[0].strip(" \t\r\n-–—:;,.")
    clipped = clipped or clean[: max(1, max_chars - reserve)].rstrip(" \t\r\n-–—:;,.")
    return f"{clipped}…" if ellipsis else clipped


# ---------------------------------------------------------------------------
# Git activity collector for journal enrichment
# ---------------------------------------------------------------------------

_ARCHIVIST_GIT_REPO_DIRS = [
    p.strip() for p in os.getenv("ARCHIVIST_GIT_REPO_DIRS", "").split(":") if p.strip()
]


def _media_day_from_iso_value(raw_value: str | None) -> str | None:
    text = str(raw_value or "").strip()
    if not text:
        return None
    parsed = _google_parse_iso_datetime(text)
    if parsed is not None:
        return _google_local_day(parsed)
    try:
        dt = datetime.fromisoformat(text)
    except Exception:
        return None
    if dt.tzinfo is None:
        return dt.date().isoformat()
    return _google_local_day(dt)


def _media_day_from_epoch_value(raw_value) -> str | None:
    try:
        value = float(raw_value)
    except (TypeError, ValueError):
        return None
    if value <= 0:
        return None
    try:
        return datetime.fromtimestamp(value, tz=timezone.utc).astimezone(_google_display_tz()).date().isoformat()
    except Exception:
        return None


def _media_datetime_from_path_value(raw_value: str | None) -> str | None:
    text = str(raw_value or "").strip()
    if not text:
        return None
    match = re.search(
        r"(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})[T_\- ](?P<hour>\d{2})[:-](?P<minute>\d{2})([:-](?P<second>\d{2}))?",
        text,
    )
    if not match:
        match = re.search(
            r"(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})[T_\- ](?P<hour>\d{2})(?P<minute>\d{2})(?P<second>\d{2})?",
            text,
        )
    if not match:
        return None
    try:
        second = int(match.groupdict().get("second") or 0)
        return datetime(
            int(match.group("year")),
            int(match.group("month")),
            int(match.group("day")),
            int(match.group("hour")),
            int(match.group("minute")),
            second,
            tzinfo=_google_display_tz(),
        ).isoformat()
    except Exception:
        return None


def _media_result_recorded_time(data: dict, result_file: Path) -> str | None:
    asset = data.get("asset") if isinstance(data.get("asset"), dict) else {}
    stamp = data.get("archivist_pipeline") if isinstance(data.get("archivist_pipeline"), dict) else {}
    asset_metadata = asset.get("metadata") if isinstance(asset.get("metadata"), dict) else {}

    for raw_value in (
        asset.get("recorded_at"),
        asset_metadata.get("recorded_at"),
        stamp.get("source_recorded_at"),
    ):
        parsed = _google_parse_iso_datetime(str(raw_value or ""))
        if parsed is not None:
            return parsed.isoformat()

    for raw_path in (
        stamp.get("source_path"),
        asset.get("path"),
        asset.get("filename"),
        result_file.name,
    ):
        parsed = _media_datetime_from_path_value(str(raw_path or ""))
        if parsed:
            return parsed
    return None


def _media_result_day(data: dict, result_file: Path) -> tuple[str | None, str]:
    from media.evidence_store import infer_recorded_day_from_path

    asset = data.get("asset") if isinstance(data.get("asset"), dict) else {}
    stamp = data.get("archivist_pipeline") if isinstance(data.get("archivist_pipeline"), dict) else {}
    asset_metadata = asset.get("metadata") if isinstance(asset.get("metadata"), dict) else {}

    for raw_day in (
        asset.get("recorded_day"),
        asset_metadata.get("recorded_day"),
        stamp.get("source_recorded_day"),
    ):
        clean = str(raw_day or "").strip()
        if clean:
            return clean, "recorded_day"

    for raw_value in (
        asset.get("recorded_at"),
        asset_metadata.get("recorded_at"),
        stamp.get("source_recorded_at"),
    ):
        day = _media_day_from_iso_value(raw_value)
        if day:
            return day, "recorded_at"

    for raw_path in (
        stamp.get("source_path"),
        asset.get("path"),
        asset.get("filename"),
        result_file.name,
    ):
        day = infer_recorded_day_from_path(str(raw_path or "").strip())
        if day:
            return day, "source_filename"

    for raw_value in (
        asset.get("created_at"),
        asset_metadata.get("created_at"),
        stamp.get("generated_at"),
    ):
        day = _media_day_from_epoch_value(raw_value)
        if day:
            return day, "fallback_epoch"

    try:
        return datetime.fromtimestamp(result_file.stat().st_mtime, tz=timezone.utc).astimezone(_google_display_tz()).date().isoformat(), "result_mtime"
    except Exception:
        return None, "missing"


def _media_result_artifacts(data: dict, media_id: str) -> list[dict]:
    artifacts = [artifact for artifact in (data.get("artifacts") or []) if isinstance(artifact, dict)]
    if artifacts:
        return artifacts

    try:
        from media.evidence_store import get_artifacts

        fallback = []
        for artifact in get_artifacts(media_id):
            fallback.append(
                {
                    "kind": artifact.kind,
                    "content": artifact.content,
                    "metadata": artifact.metadata or {},
                }
            )
        return fallback
    except Exception:
        return []


def _media_result_subject_line(data: dict, artifacts: list[dict]) -> str:
    for artifact in artifacts:
        if str(artifact.get("kind") or "").strip() != "subject_line":
            continue
        text = str(artifact.get("content") or "").strip()
        if text:
            return text
    return str(data.get("subject_line") or "").strip()


def _media_result_journal_item(data: dict, result_file: Path, day_source: str) -> dict:
    media_id = str(data.get("media_id") or result_file.stem).strip() or result_file.stem
    artifacts = _media_result_artifacts(data, media_id)
    subject_line = _media_result_subject_line(data, artifacts)
    document_payload = data.get("document") if isinstance(data.get("document"), dict) else None
    context_overview = _google_archive_media_context_overview(artifacts, document_payload)
    key_topics = _google_archive_media_key_topics(artifacts, document_payload)

    cleaned_subject = _google_archive_clean_topic_text("media", subject_line)
    subject_low_signal = _google_archive_is_low_signal_topic("media", subject_line, cleaned_subject)
    subject_structural_low_signal = subject_low_signal or _google_archive_media_topic_is_low_signal(cleaned_subject)
    context_low_signal = _google_archive_media_has_low_signal_context(context_overview, *key_topics)
    if subject_structural_low_signal and context_low_signal:
        key_topics = []

    subject = cleaned_subject
    if (not subject or subject_low_signal) and key_topics:
        subject = key_topics[0]
    if not subject and context_overview:
        subject = _google_archive_first_sentence(context_overview, max_chars=140)

    theme_text_parts = [subject_line, context_overview, *key_topics]
    theme_text = _google_archive_trim_text(" ".join(part for part in theme_text_parts if part), max_chars=720)
    low_signal = bool((subject_structural_low_signal or not subject) and context_low_signal and not key_topics)

    weight_multiplier = 1.0
    if context_overview:
        weight_multiplier += 0.55
    if key_topics:
        weight_multiplier += min(0.65, 0.22 * len(key_topics))
    if low_signal:
        weight_multiplier *= 0.35
    elif subject_structural_low_signal and context_low_signal:
        weight_multiplier *= 0.6

    stamp = data.get("archivist_pipeline") if isinstance(data.get("archivist_pipeline"), dict) else {}
    asset = data.get("asset") if isinstance(data.get("asset"), dict) else {}
    source_path = str((stamp or {}).get("source_path") or asset.get("path") or "").strip()
    fallback_subject = Path(source_path).name if source_path else media_id

    return {
        "media_id": media_id,
        "subject": subject or fallback_subject,
        "context": _google_archive_trim_text(context_overview, max_chars=900, ellipsis=False),
        "topics": key_topics[:3],
        "theme_text": theme_text or subject or fallback_subject,
        "source": Path(source_path).name if source_path else "",
        "day_source": day_source,
        "recorded_time": _media_result_recorded_time(data, result_file),
        "weight_multiplier": round(weight_multiplier, 2),
        "low_signal": low_signal,
    }


def _persist_google_archive_views() -> dict:
    """Summarize the imported Google archive from per-account manifests.

    Replaces the former journal-overview engine. The System panel card and the
    health check only need aggregate counts + lastImportedAt, which live in each
    account's manifest.json; dayCount is the set of distinct days across the
    archived Google records.
    """
    root = _google_archive_root()
    account_count = 0
    gmail_total = calendar_total = drive_total = chat_total = 0
    latest_import: str | None = None
    days: set[str] = set()
    if root.is_dir():
        for account_dir in sorted(p for p in root.iterdir() if p.is_dir()):
            manifest_path = account_dir / "manifest.json"
            if not manifest_path.is_file():
                continue
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if not isinstance(manifest, dict):
                continue
            account_count += 1
            gmail_total += int(manifest.get("gmailMessages") or 0)
            calendar_total += int(manifest.get("calendarEvents") or 0)
            drive_total += int(manifest.get("driveFiles") or 0)
            chat_total += int(manifest.get("chatMessages") or 0)
            imported_at = str(manifest.get("imported_at") or "").strip()
            if imported_at and (latest_import is None or imported_at > latest_import):
                latest_import = imported_at
            for fname in ("gmail_messages.jsonl", "calendar_events.jsonl", "drive_files.jsonl", "chat_messages.jsonl"):
                for record in _jsonl_read(account_dir / fname):
                    day = str(record.get("day") or "").strip()
                    if day:
                        days.add(day)
    summary = {
        "available": account_count > 0,
        "accountCount": account_count,
        "gmailMessages": gmail_total,
        "calendarEvents": calendar_total,
        "driveFiles": drive_total,
        "chatMessages": chat_total,
        "dayCount": len(days),
        "lastImportedAt": latest_import,
    }
    try:
        _google_archive_summary_path().write_text(json.dumps(summary, indent=2), encoding="utf-8")
    except Exception:
        logging.debug("failed to persist google archive summary", exc_info=True)
    return summary


def _google_archive_summary() -> dict:
    summary_path = _google_archive_summary_path()
    if summary_path.is_file():
        try:
            payload = json.loads(summary_path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                return payload
        except Exception:
            pass
    return {
        "available": False,
        "accountCount": 0,
        "gmailMessages": 0,
        "calendarEvents": 0,
        "driveFiles": 0,
        "chatMessages": 0,
        "dayCount": 0,
        "lastImportedAt": None,
    }


def _google_import_status_public() -> dict:
    with _GOOGLE_IMPORT_LOCK:
        return {
            "running": bool(_GOOGLE_IMPORT_STATE.get("running")),
            "message": _GOOGLE_IMPORT_STATE.get("message"),
            "startedAt": _GOOGLE_IMPORT_STATE.get("startedAt"),
            "finishedAt": _GOOGLE_IMPORT_STATE.get("finishedAt"),
            "accounts": list(_GOOGLE_IMPORT_STATE.get("accounts") or []),
        }


def _google_archive_service_path(account_email: str, service: str) -> Path:
    filename_map = {
        "gmail": "gmail_messages.jsonl",
        "calendar": "calendar_events.jsonl",
        "drive": "drive_files.jsonl",
        "chat": "chat_messages.jsonl",
    }
    return _google_archive_account_dir(account_email) / filename_map[service]


def _google_service_since_date(account_email: str, service: str, *, incremental: bool) -> str | None:
    if not incremental:
        return None
    service_path = _google_archive_service_path(account_email, service)
    if not service_path.is_file():
        return None
    if service == "calendar":
        # Calendar APIs filter by event start time, not update time. Re-query a
        # recent window so missed or newly-added meetings inside the current
        # focus period are merged instead of permanently skipped.
        current_day = datetime.now(_google_display_tz()).date()
        return (current_day - timedelta(days=_GOOGLE_CALENDAR_INCREMENTAL_LOOKBACK_DAYS)).strftime("%Y/%m/%d")
    manifest_path = _google_archive_account_dir(account_email) / "manifest.json"
    if not manifest_path.is_file():
        return None
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    imported_at = str(manifest.get("imported_at") or "").strip()
    if not imported_at:
        return None
    dt = _google_parse_iso_datetime(imported_at)
    if dt is None:
        return None
    return (dt - timedelta(days=1)).strftime("%Y/%m/%d")


def _run_google_archive_index_sync(active_services: list[str]) -> tuple[dict, dict]:
    summary = _persist_google_archive_views()
    archive_fingerprint = _google_archive_fingerprint()
    started_at = datetime.now(timezone.utc).isoformat()
    embedding_status = check_embedding_service(
        host=EMBEDDING_HOST,
        port=EMBEDDING_PORT,
        model=LOCAL_EMBEDDING_MODEL,
    )
    if embedding_status.get("status") != "ok":
        error = str(embedding_status.get("error") or "embedding service unavailable")
        _write_google_archive_index_status(
            {
                "status": "skipped",
                "reason": "embeddings_unavailable",
                "startedAt": started_at,
                "finishedAt": datetime.now(timezone.utc).isoformat(),
                "archiveFingerprint": archive_fingerprint,
                "archiveVersion": GOOGLE_ARCHIVE_CONTENT_VERSION,
                "embeddingModel": LOCAL_EMBEDDING_MODEL,
                "services": active_services,
                "summary": {
                    "records_seen": 0,
                    "records_indexed": 0,
                    "chunks_inserted": 0,
                    "errors": [error],
                },
            }
        )
        return summary, {"records_seen": 0, "records_indexed": 0, "chunks_inserted": 0, "errors": [error]}

    _write_google_archive_index_status(
        {
            "status": "indexing",
            "startedAt": started_at,
            "archiveFingerprint": archive_fingerprint,
            "archiveVersion": GOOGLE_ARCHIVE_CONTENT_VERSION,
            "embeddingModel": LOCAL_EMBEDDING_MODEL,
            "services": active_services,
        }
    )

    index_summary = {"records_seen": 0, "records_indexed": 0, "chunks_inserted": 0, "errors": []}
    try:
        with _GOOGLE_IMPORT_LOCK:
            _GOOGLE_IMPORT_STATE["message"] = "Indexing archived Google history into the vector store."
        index_summary = index_google_archive_content(
            _google_archive_root(),
            services=set(active_services),
            embedding_host=EMBEDDING_HOST,
            embedding_port=EMBEDDING_PORT,
            ip_address=MILVUS_HOST,
        )
    except Exception as index_exc:
        logging.exception("google archive indexing failed")
        index_summary = {"records_seen": 0, "records_indexed": 0, "chunks_inserted": 0, "errors": [str(index_exc)]}

    status_value = "synced" if not index_summary.get("errors") else "failed"
    _write_google_archive_index_status(
        {
            "status": status_value,
            "startedAt": started_at,
            "finishedAt": datetime.now(timezone.utc).isoformat(),
            "archiveFingerprint": archive_fingerprint,
            "archiveVersion": GOOGLE_ARCHIVE_CONTENT_VERSION,
            "embeddingModel": LOCAL_EMBEDDING_MODEL,
            "services": active_services,
            "summary": {
                "records_seen": int(index_summary.get("records_seen") or 0),
                "records_indexed": int(index_summary.get("records_indexed") or 0),
                "chunks_inserted": int(index_summary.get("chunks_inserted") or 0),
                "errors": list(index_summary.get("errors") or []),
            },
        }
    )
    return summary, index_summary


def _run_google_import_job(
    services: list[str] | None = None,
    *,
    incremental: bool = False,
    reindex_only: bool = False,
) -> None:
    active_services = [service for service in (services or _google_enabled_service_keys()) if service in {"gmail", "calendar", "drive", "chat"}]
    try:
        imported_accounts: list[dict] = []
        if not reindex_only:
            accounts = _collect_google_accounts()
            for account in accounts:
                account_email = str(account.get("account") or account.get("label") or "").strip()
                token_path = account.get("token_path")
                if not account_email or not token_path:
                    continue
                with _GOOGLE_IMPORT_LOCK:
                    mode_label = "incremental" if incremental else "full"
                    _GOOGLE_IMPORT_STATE["message"] = f"Loading Google history for {account_email} ({mode_label})."
                creds, error, _ = _load_google_creds(token_path)
                if creds is None:
                    imported_accounts.append({"account": account_email, "error": str(error or "Unable to load credentials")})
                    continue

                gmail_records: list[dict] = []
                calendar_records: list[dict] = []
                drive_records: list[dict] = []
                chat_records: list[dict] = []
                service_errors: list[str] = []
                if "gmail" in active_services:
                    gmail_since = _google_service_since_date(account_email, "gmail", incremental=incremental)
                    try:
                        gmail_records = _fetch_google_gmail_records(account_email, creds, _GOOGLE_IMPORT_STATE, since_date=gmail_since)
                    except Exception as exc:
                        service_errors.append(f"gmail: {exc}")
                if "calendar" in active_services:
                    calendar_since = _google_service_since_date(account_email, "calendar", incremental=incremental)
                    try:
                        calendar_records = _fetch_google_calendar_records(account_email, creds, _GOOGLE_IMPORT_STATE, since_date=calendar_since)
                    except Exception as exc:
                        service_errors.append(f"calendar: {exc}")
                if "drive" in active_services:
                    drive_since = _google_service_since_date(account_email, "drive", incremental=incremental)
                    try:
                        drive_records = _fetch_google_drive_records(account_email, creds, _GOOGLE_IMPORT_STATE, since_date=drive_since)
                    except Exception as exc:
                        service_errors.append(f"drive: {exc}")
                if "chat" in active_services:
                    chat_since = _google_service_since_date(account_email, "chat", incremental=incremental)
                    try:
                        chat_records = _fetch_google_chat_records(account_email, creds, _GOOGLE_IMPORT_STATE, since_date=chat_since)
                    except Exception as exc:
                        service_errors.append(f"chat: {exc}")

                manifest = _write_google_account_archive(
                    account_email,
                    gmail_records,
                    calendar_records,
                    drive_records,
                    chat_records,
                    merge=incremental,
                )
                imported_accounts.append(
                    {
                        "account": account_email,
                        "gmailMessages": int(manifest.get("gmailMessages") or 0),
                        "calendarEvents": int(manifest.get("calendarEvents") or 0),
                        "driveFiles": int(manifest.get("driveFiles") or 0),
                        "chatMessages": int(manifest.get("chatMessages") or 0),
                        "dayCount": int(manifest.get("dayCount") or 0),
                        "errors": service_errors,
                    }
                )

        summary, index_summary = _run_google_archive_index_sync(active_services)
        mode_prefix = "Google archive reindex finished" if reindex_only else "Google import finished"
        with _GOOGLE_IMPORT_LOCK:
            _GOOGLE_IMPORT_STATE.update(
                {
                    "running": False,
                    "message": (
                        f"{mode_prefix} — {summary.get('gmailMessages', 0)} emails, "
                        f"{summary.get('calendarEvents', 0)} calendar events, {summary.get('driveFiles', 0)} drive files, "
                        f"{summary.get('chatMessages', 0)} chat messages, {summary.get('dayCount', 0)} journal day(s), "
                        f"{index_summary.get('records_indexed', 0)} indexed records / {index_summary.get('chunks_inserted', 0)} chunks."
                    ),
                    "finishedAt": datetime.now(timezone.utc).isoformat(),
                    "accounts": imported_accounts,
                }
            )
    except Exception as exc:
        logging.exception("google import failed")
        with _GOOGLE_IMPORT_LOCK:
            _GOOGLE_IMPORT_STATE.update(
                {
                    "running": False,
                    "message": f"Google import failed: {exc}",
                    "finishedAt": datetime.now(timezone.utc).isoformat(),
                }
            )


def _start_google_import(
    services: list[str] | None = None,
    *,
    incremental: bool = False,
    reindex_only: bool = False,
) -> dict:
    with _GOOGLE_IMPORT_LOCK:
        if _GOOGLE_IMPORT_STATE.get("running"):
            return {
                "running": bool(_GOOGLE_IMPORT_STATE.get("running")),
                "message": _GOOGLE_IMPORT_STATE.get("message"),
                "startedAt": _GOOGLE_IMPORT_STATE.get("startedAt"),
                "finishedAt": _GOOGLE_IMPORT_STATE.get("finishedAt"),
                "accounts": list(_GOOGLE_IMPORT_STATE.get("accounts") or []),
            }
        _GOOGLE_IMPORT_STATE.update(
            {
                "running": True,
                "message": (
                    "Starting Google archive reindex."
                    if reindex_only
                    else f"Starting Google history import ({'incremental' if incremental else 'full'})."
                ),
                "startedAt": datetime.now(timezone.utc).isoformat(),
                "finishedAt": None,
                "accounts": [],
            }
        )
    worker = threading.Thread(
        target=_run_google_import_job,
        args=(services,),
        kwargs={"incremental": incremental, "reindex_only": reindex_only},
        daemon=True,
    )
    worker.start()
    return _google_import_status_public()


# ---------------------------------------------------------------------------
# Google import scheduler -- runs incremental imports on a timer
# ---------------------------------------------------------------------------

def _google_import_scheduler_thread() -> None:
    interval_seconds = max(300, _GOOGLE_IMPORT_INTERVAL_HOURS * 3600)
    logging.info("Google import scheduler started (interval=%.1f hours)", _GOOGLE_IMPORT_INTERVAL_HOURS)
    while not _GOOGLE_IMPORT_SCHEDULER_STOP.is_set():
        try:
            summary = _google_archive_summary()
            last_imported = str(summary.get("lastImportedAt") or "").strip()
            needs_import = True
            if last_imported:
                try:
                    dt = datetime.fromisoformat(last_imported)
                    hours_since = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
                    needs_import = hours_since >= _GOOGLE_IMPORT_INTERVAL_HOURS
                except Exception:
                    pass

            try:
                accounts = _collect_google_accounts()
                if accounts:
                    if needs_import:
                        logging.info("Google import scheduler: starting incremental import")
                        _start_google_import(incremental=True)
                    else:
                        needs_index_sync, reason = _google_archive_needs_index_sync()
                        if needs_index_sync:
                            logging.info("Google import scheduler: starting archive reindex (%s)", reason)
                            _start_google_import(reindex_only=True)
                else:
                    logging.debug("Google import scheduler: no accounts configured, skipping")
            except Exception:
                logging.exception("Google import scheduler: error checking accounts")
        except Exception:
            logging.exception("Google import scheduler: unexpected error")
        _GOOGLE_IMPORT_SCHEDULER_STOP.wait(min(interval_seconds, 300))


def start_google_import_scheduler_best_effort() -> None:
    """Start the Google import scheduler as a daemon thread."""
    try:
        thread = threading.Thread(target=_google_import_scheduler_thread, daemon=True, name="google-import-scheduler")
        thread.start()
    except Exception:
        logging.exception("Failed to start Google import scheduler")


@app.route("/api/integrations/status", methods=["GET"])
def integrations_status():
    """Check Google API connectivity for Gmail, Calendar, and Drive across all connected accounts."""
    def _build_integrations_payload() -> dict:
        accounts = _collect_google_accounts()
        google = _google_summary(accounts)
        google["archive"] = _google_archive_summary()
        google["import"] = _google_import_status_public()

        if not accounts:
            msg = "No Google OAuth tokens found — run authorization flow"
            results = _empty_google_service_results(msg)
        else:
            results = _flatten_google_integrations(accounts)

        github_status: dict = {"connected": False, "error": "GITHUB_TOKEN not set"}
        try:
            from github_service import check_github_token
            github_status = check_github_token()
        except Exception as exc:
            github_status = {"connected": False, "error": str(exc)[:200]}

        if github_status.get("connected"):
            results.append({
                "id": "github",
                "name": "GitHub",
                "description": f"Authenticated as {github_status.get('login', 'unknown')}",
                "connected": True,
                "status": "connected",
                "account": github_status.get("login"),
            })

        return {
            "integrations": results,
            "google": google,
            "github": github_status,
            "token_path": (google.get("tokenPaths") or [None])[0],
            "token_paths": google.get("tokenPaths", []),
            "client_secret_path": google.get("clientSecretPath"),
        }

    return jsonify(_cached_status_payload("integrations_status", 20, _build_integrations_payload))


@app.route("/api/integrations/authorize", methods=["POST"])
def integrations_authorize():
    """Start OAuth2 authorization flow for Google services.

    Requires a client_secret.json / credentials.json file to exist.
    Returns a Google authorization URL that completes via the Archivist web app.
    """
    try:
        from google_auth_oauthlib.flow import Flow
    except ImportError:
        return jsonify({"error": "google-auth-oauthlib not installed"}), 500

    client_secret = _find_file(_GOOGLE_CLIENT_SECRET_PATHS)
    if not client_secret:
        return jsonify({
            "error": "No client_secret.json found",
            "hint": "Download OAuth client credentials from Google Cloud Console and place at "
                    + os.path.join(os.path.dirname(__file__), "client_secret.json"),
            "search_paths": _GOOGLE_CLIENT_SECRET_PATHS,
        }), 400

    body = request.get_json(force=True, silent=True) or {}
    label_hint = str(body.get("label") or body.get("account") or "").strip()
    requested_scopes = _google_requested_scopes()
    enabled_services = _google_enabled_service_summaries()

    try:
        _cleanup_google_auth_pending()
        flow = Flow.from_client_secrets_file(client_secret, scopes=requested_scopes)
        flow.redirect_uri = _google_callback_url()
        auth_url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="false",
            prompt="consent select_account",
        )
        _GOOGLE_AUTH_PENDING[state] = {
            "created_at": time.time(),
            "label_hint": label_hint,
            "client_secret": client_secret,
            "redirect_uri": flow.redirect_uri,
            "code_verifier": getattr(flow, "code_verifier", None),
            "scopes": requested_scopes,
            "services": enabled_services,
        }
        return jsonify(
            {
                "ok": True,
                "pending": True,
                "auth_url": auth_url,
                "redirect_uri": flow.redirect_uri,
                "requested_scopes": requested_scopes,
                "services": enabled_services,
                "message": "Continue authorization in the Google window. Re-authorize after enabling new Google services or scopes.",
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/google/import", methods=["POST"])
def api_google_import():
    body = request.get_json(force=True, silent=True) or {}
    services = body.get("services")
    service_list = None
    if isinstance(services, list):
        service_list = []
        seen: set[str] = set()
        for item in services:
            normalized = str(item or "").strip().lower().replace("_", "-")
            canonical = _GOOGLE_SERVICE_KEY_ALIASES.get(normalized, normalized)
            if canonical in seen:
                continue
            seen.add(canonical)
            service_list.append(canonical)
    incremental = bool(body.get("incremental", False))
    reindex_only = bool(body.get("reindex_only", False))
    state = _start_google_import(service_list, incremental=incremental, reindex_only=reindex_only)
    archive = _google_archive_summary()
    return jsonify({"ok": True, "import": state, "archive": archive, "message": state.get("message")})


@app.route("/api/google/import/status", methods=["GET"])
def api_google_import_status():
    needs_index_sync, reason = _google_archive_needs_index_sync()
    return jsonify(
        {
            "import": _google_import_status_public(),
            "archive": _google_archive_summary(),
            "index": _load_google_archive_index_status(),
            "needs_index_sync": needs_index_sync,
            "index_sync_reason": reason,
        }
    )


@app.route("/api/google/import/schedule", methods=["GET"])
def api_google_import_schedule():
    """Return the current import scheduler configuration."""
    summary = _google_archive_summary()
    last_imported = str(summary.get("lastImportedAt") or "").strip()
    hours_since = None
    if last_imported:
        try:
            dt = datetime.fromisoformat(last_imported)
            hours_since = round((datetime.now(timezone.utc) - dt).total_seconds() / 3600, 1)
        except Exception:
            pass
    return jsonify({
        "interval_hours": _GOOGLE_IMPORT_INTERVAL_HOURS,
        "last_imported_at": last_imported or None,
        "hours_since_import": hours_since,
        "import_running": _google_import_status_public().get("running", False),
        "index_status": _load_google_archive_index_status(),
        "needs_index_sync": _google_archive_needs_index_sync()[0],
    })


@app.route("/api/github/status", methods=["GET"])
def api_github_status():
    """Return GitHub token status, rate limit info, and expiration."""
    try:
        from github_service import check_github_token
        return jsonify(check_github_token())
    except Exception as exc:
        return jsonify({"connected": False, "error": str(exc)[:200]})


_github_sync_state: dict = {"running": False, "last_run": None, "items_fetched": 0, "items_indexed": 0, "chunks_inserted": 0, "error": None}


@app.route("/api/github/sync", methods=["POST"])
def api_github_sync():
    """Trigger a background GitHub content sync into the vector store."""
    if _github_sync_state["running"]:
        return jsonify({"ok": False, "error": "Sync already running", **_github_sync_state})

    def _run_sync():
        _github_sync_state["running"] = True
        _github_sync_state["error"] = None
        try:
            from indexing_service import index_github_content
            result = index_github_content(
                embedding_host=EMBEDDING_HOST,
                embedding_port=EMBEDDING_PORT,
                ip_address=MILVUS_HOST,
            )
            _github_sync_state["items_fetched"] = result.get("items_fetched", 0)
            _github_sync_state["items_indexed"] = result.get("items_indexed", 0)
            _github_sync_state["chunks_inserted"] = result.get("chunks_inserted", 0)
            _github_sync_state["last_run"] = datetime.now(timezone.utc).isoformat()
            if result.get("errors"):
                _github_sync_state["error"] = "; ".join(result["errors"][:3])
            logging.info(
                "GitHub sync complete: %d items fetched, %d indexed, %d chunks",
                result.get("items_fetched", 0),
                result.get("items_indexed", 0),
                result.get("chunks_inserted", 0),
            )
        except Exception as exc:
            logging.exception("GitHub sync failed")
            _github_sync_state["error"] = str(exc)[:200]
        finally:
            _github_sync_state["running"] = False

    threading.Thread(target=_run_sync, daemon=True, name="github-sync").start()
    return jsonify({"ok": True, "message": "GitHub sync started"})


@app.route("/api/github/activity", methods=["GET"])
def api_github_activity():
    """Return recent GitHub activity for the authenticated user."""
    try:
        from github_service import collect_github_activity_for_days
        days_param = request.args.get("days", "90")
        try:
            since_days = int(days_param)
        except ValueError:
            since_days = 90
        activity = collect_github_activity_for_days(since_days=since_days)
        total = sum(len(v) for v in activity.values())
        return jsonify({"ok": True, "days": len(activity), "total_events": total, "activity": activity})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)[:200]})


@app.route("/api/integrations/oauth/google/callback", methods=["GET"])
def integrations_authorize_callback():
    try:
        from google_auth_oauthlib.flow import Flow
    except ImportError:
        return Response(_google_oauth_result_page("google-auth-oauthlib not installed", False), status=500, mimetype="text/html")

    state = str(request.args.get("state") or "").strip()
    if not state:
        return Response(_google_oauth_result_page("Missing OAuth state.", False), status=400, mimetype="text/html")

    _cleanup_google_auth_pending()
    pending = _GOOGLE_AUTH_PENDING.get(state)
    if not pending:
        return Response(_google_oauth_result_page("Authorization request expired or was not found. Start again from Archivist.", False), status=400, mimetype="text/html")

    error = str(request.args.get("error") or "").strip()
    if error:
        _GOOGLE_AUTH_PENDING.pop(state, None)
        return Response(_google_oauth_result_page(f"Google returned an error: {error}", False), status=400, mimetype="text/html")

    try:
        os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")
        requested_scopes = list(pending.get("scopes") or _google_requested_scopes())
        flow = Flow.from_client_secrets_file(
            str(pending.get("client_secret")),
            scopes=requested_scopes,
            state=state,
        )
        flow.redirect_uri = str(pending.get("redirect_uri") or "")
        if pending.get("code_verifier"):
            flow.code_verifier = str(pending.get("code_verifier"))
        flow.fetch_token(authorization_response=request.url)
        creds = flow.credentials
        account_email = _discover_google_account_email(creds) or str(pending.get("label_hint") or "").strip() or "Google account"
        token_path = _google_account_token_path(account_email)
        token_path.parent.mkdir(parents=True, exist_ok=True)
        with open(token_path, "w") as f:
            f.write(creds.to_json())
        _GOOGLE_AUTH_PENDING.pop(state, None)
        return Response(
            _google_oauth_result_page(f"Authorization successful — connected {account_email}. You can close this window.", True),
            mimetype="text/html",
        )
    except Exception as e:
        _GOOGLE_AUTH_PENDING.pop(state, None)
        return Response(_google_oauth_result_page(f"Authorization failed: {e}", False), status=500, mimetype="text/html")


# Pre-warm journal cache in a background thread so the first request is fast.
# Uses a low-priority approach: sleeps briefly first to let gunicorn start accepting.
def _periodic_github_sync():
    """Periodically sync GitHub content in the background (every 2 hours).

    Fetches activity for the journal cache and indexes content into the vector store.
    """
    import time as _time
    _time.sleep(30)  # let server settle before first sync
    while True:
        try:
            from github_service import GITHUB_TOKEN as _gh_tok, collect_github_activity_for_days
            if _gh_tok:
                logging.info("Periodic GitHub activity sync starting...")
                collect_github_activity_for_days()
                # Also index content into vector store
                try:
                    from indexing_service import index_github_content
                    result = index_github_content(
                        embedding_host=EMBEDDING_HOST,
                        embedding_port=EMBEDDING_PORT,
                        ip_address=MILVUS_HOST,
                    )
                    logging.info(
                        "Periodic GitHub indexing: %d fetched, %d indexed, %d chunks",
                        result.get("items_fetched", 0),
                        result.get("items_indexed", 0),
                        result.get("chunks_inserted", 0),
                    )
                except Exception:
                    logging.exception("Periodic GitHub vector indexing failed (non-fatal)")
                logging.info("Periodic GitHub sync complete")
        except Exception:
            logging.exception("Periodic GitHub sync failed (non-fatal)")
        _time.sleep(7200)  # 2 hours


try:
    tts_service.start()
except Exception:
    logging.exception("TTS service startup failed (non-fatal)")

if _WEB_BACKGROUND_TASKS_ENABLED:
    # Start Google import scheduler (deferred to here since the function is defined above).
    try:
        start_google_import_scheduler_best_effort()
    except Exception:
        logging.exception("Google import scheduler startup failed")

    threading.Thread(target=_periodic_github_sync, daemon=True, name="github-periodic-sync").start()
else:
    logging.info(
        "Archivist web background tasks disabled: skipping Google import scheduler, focus sync scheduler, journal prewarm, and periodic GitHub sync"
    )


# ── Unified media pipeline (RTSP ingest + streaming transcription) ──────
# Audio+video ingest from enabled sources in config/sources.yml.
# Emits transcript.final + source.health events to Redis Streams.
try:
    import streaming_transcription_service
    import rtsp_ingest_service
    import vision_service
    import archive_service
    import retention_service
    streaming_transcription_service.start_all()
    try:
        vision_service.start()
    except Exception:
        logging.exception("vision_service startup failed (non-fatal)")
    rtsp_ingest_service.start_all()
    try:
        archive_service.start()
    except Exception:
        logging.exception("archive_service startup failed (non-fatal)")
    try:
        retention_service.start()
    except Exception:
        logging.exception("retention_service startup failed (non-fatal)")
    try:
        import health_monitor
        health_monitor.start()
    except Exception:
        logging.exception("health_monitor startup failed (non-fatal)")
    try:
        import gpu_watchdog
        gpu_watchdog.start()
    except Exception:
        logging.exception("gpu_watchdog startup failed (non-fatal)")
    logging.info("RTSP ingest + streaming transcription + vision + archive + retention + health + gpu_watchdog started")
except Exception:
    logging.exception("RTSP ingest startup failed (non-fatal)")


@app.route("/api/media/search", methods=["GET"])
def _media_semantic_search():
    q = (request.args.get("q") or "").strip()
    if not q:
        return jsonify({"error": "missing q"}), 400
    try:
        top_k = max(1, min(50, int(request.args.get("k", "10"))))
    except (TypeError, ValueError):
        top_k = 10
    sources_param = request.args.get("sources") or ""
    sources_filter = [s.strip() for s in sources_param.split(",") if s.strip()] or None
    try:
        import vision_service
        hits = vision_service.search_by_text(q, top_k=top_k, sources=sources_filter)
        return jsonify({"query": q, "k": top_k, "hits": hits})
    except Exception as exc:
        logging.exception("semantic search failed")
        return jsonify({"error": str(exc)}), 500


@app.route("/api/media/keyframe", methods=["GET"])
def _media_keyframe():
    path = request.args.get("path") or ""
    if not path:
        return jsonify({"error": "missing path"}), 400
    # Restrict to configured keyframe root for safety.
    import os.path as _op
    root = os.getenv("ARCHIVIST_KEYFRAMES_ROOT", "/data/media_store/keyframes")
    real = _op.realpath(path)
    if not real.startswith(_op.realpath(root)):
        return jsonify({"error": "path outside keyframes root"}), 403
    try:
        directory = _op.dirname(real)
        filename = _op.basename(real)
        return send_from_directory(directory, filename, mimetype="image/jpeg")
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/media/sources/status", methods=["GET"])
def _media_sources_status():
    try:
        import rtsp_ingest_service
        import streaming_transcription_service
        import motion_service
        import vision_service
        import archive_service
        import retention_service
        import health_monitor
        return jsonify({
            "configured": rtsp_ingest_service.configured_sources_status(),
            "rtsp": rtsp_ingest_service.status(),
            "streaming": streaming_transcription_service.status(),
            "motion": motion_service.status(),
            "vision": vision_service.status(),
            "archive": archive_service.status(),
            "retention": retention_service.status(),
            "health": health_monitor.status(),
        })
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/media/retention/run", methods=["POST"])
def _media_retention_run():
    """Trigger an immediate retention GC pass. Body: {dry_run: bool, limit: int}."""
    try:
        import retention_service
        body = request.get_json(silent=True) or {}
        dry = bool(body.get("dry_run", True))
        limit = int(body.get("limit", 500))
        summary = retention_service.run_gc_pass(dry_run=dry, limit=limit)
        return jsonify(summary)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/media/archive/run", methods=["POST"])
def _media_archive_run():
    """Trigger an immediate archive pass (local SSD → NAS).

    Body: {dry_run: bool, backfill: bool, limit: int}
    backfill=true ignores local_hold_hours (one-shot move of all local segments).
    """
    try:
        import archive_service
        body = request.get_json(silent=True) or {}
        dry = bool(body.get("dry_run", False))
        backfill = bool(body.get("backfill", False))
        limit = int(body.get("limit", 2000))
        summary = archive_service.run_archive_pass(backfill=backfill, dry_run=dry, limit=limit)
        return jsonify(summary)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/metrics", methods=["GET"])
def _prometheus_metrics():
    try:
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)
    except Exception as exc:
        return Response(f"# metrics unavailable: {exc}\n", mimetype="text/plain")


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5050)
