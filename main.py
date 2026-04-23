# main.py
from flask import Flask, request, jsonify, send_from_directory, Response
from load import load_to_vectorstore, load_text_to_vectorstore, clear_vectorstore_collection
from search import search_vectorstore
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
from utils import LOCAL_EMBEDDING_MODEL, embed_text_to_vector, validate_embeddings
from xml.etree import ElementTree as ET

from backups_service import (
    BACKUP_ROOT,
    add_backup_target,
    delete_backup_target,
    get_backup_overview,
    get_run_logs,
    list_backup_targets,
    start_backup,
    start_scheduler_best_effort,
    start_target_backup,
    stop_backup,
    update_backup_target,
    update_schedule,
)
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
import transcription_service
from agent_integration import (
    build_agent_system_message,
    console_agent_id,
    decode_session_ref,
    default_web_session_key,
    encode_session_ref,
    gateway_session_key,
    host_workspace,
    inspect_agent_runtime,
    load_openclaw_config,
    load_openclaw_messages_from_transcript,
    load_openclaw_sessions_for_agents,
    load_team_agents,
    registered_agent_ids,
    resolve_gateway_token,
    resolve_gateway_url,
    resolve_openclaw_session_file,
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


def _cached_status_payload(key: str, ttl_seconds: float, builder):
    now = time.time()
    with _STATUS_CACHE_LOCK:
        cached = _STATUS_CACHE.get(key)
        if cached and (now - cached[0]) <= ttl_seconds:
            return copy.deepcopy(cached[1])
    payload = builder()
    with _STATUS_CACHE_LOCK:
        _STATUS_CACHE[key] = (time.time(), copy.deepcopy(payload))
    return payload

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
            if stale_count > 0:
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
            backup_overview = get_backup_overview()
            backup_files = backup_overview.get("backup_files", [])
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

        return {"status": overall, "components": components}

    payload = _cached_status_payload("health", 15, _build_health_payload)
    return jsonify(payload), 200

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
        coll.load()
        utility.wait_for_loading_complete(raw_name, using=alias, timeout=MILVUS_LOAD_TIMEOUT)
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

    alias = _milvus_alias("global_search")
    merged = []
    try:
        _milvus_connect(alias, host=ip_address)
        collection_names = utility.list_collections(using=alias, timeout=MILVUS_CONNECT_TIMEOUT)
    finally:
        _milvus_disconnect(alias)

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
                **search_options,
            )
            for h in hits:
                h["collection"] = logical_name
                h["collection_raw"] = raw_name
                merged.append(h)
        except Exception:
            app.logger.exception("Global search failed for collection '%s'", logical_name)

    prefers_lower = _prefers_lower_distance_for_response(mode=mode, metric_type=search_options.get("metric_type"))
    merged.sort(
        key=lambda item: item.get("distance", float("inf") if prefers_lower else float("-inf")),
        reverse=not prefers_lower,
    )
    return jsonify({"results": merged[:limit], "total_candidates": len(merged)})

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

## ── Chat endpoint (OpenClaw proxy) ──────────────────────────────────
import re as _re

_OPENCLAW_URL = os.environ.get("OPENCLAW_GATEWAY_URL", "http://127.0.0.1:18789").rstrip("/")
_OPENCLAW_TOKEN = os.environ.get("OPENCLAW_GATEWAY_TOKEN", "").strip()

_AGENT_CHAT_SESSIONS: dict[str, list[dict]] = {}
_AGENT_SESSION_META: dict[str, dict[str, object]] = {}
_AGENT_STOP_REQUESTS: set[str] = set()
_SYSTEM_FLAGS: dict[str, bool] = {
    "system_enabled": True,
    "speech_input_enabled": True,
}
try:
    _FOCUS_MANUAL_PRIORITY_GATEWAY_TIMEOUT_S = max(
        0.1,
        float(os.getenv("ARCHIVIST_FOCUS_MANUAL_PRIORITY_GATEWAY_TIMEOUT_S", "2.0")),
    )
except (TypeError, ValueError):
    _FOCUS_MANUAL_PRIORITY_GATEWAY_TIMEOUT_S = 2.0
try:
    _FOCUS_PRIORITY_AUTO_VERIFY_MAX_AGE_MINUTES = max(
        15,
        int(os.getenv("ARCHIVIST_FOCUS_PRIORITY_AUTO_VERIFY_MAX_AGE_MINUTES", "360")),
    )
except (TypeError, ValueError):
    _FOCUS_PRIORITY_AUTO_VERIFY_MAX_AGE_MINUTES = 360
try:
    _FOCUS_PRIORITY_AUTO_VERIFY_MIN_INTERVAL_SECONDS = max(
        60,
        int(os.getenv("ARCHIVIST_FOCUS_PRIORITY_AUTO_VERIFY_MIN_INTERVAL_SECONDS", "1800")),
    )
except (TypeError, ValueError):
    _FOCUS_PRIORITY_AUTO_VERIFY_MIN_INTERVAL_SECONDS = 1800
_TEST_PROFILE_SPECS: dict[str, dict[str, object]] = {
    "focus-priorities": {
        "id": "focus-priorities",
        "label": "Focus Priority Evals",
        "pytest_args": ["tests/test_focus_priority_console_eval.py"],
        "owner_agents": ["archivist-verifier", "archivist-health"],
        "auto_run": True,
        "stale_after_minutes": _FOCUS_PRIORITY_AUTO_VERIFY_MAX_AGE_MINUTES,
    },
}
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


def _test_failure_reason(case: ET.Element) -> str:
    for tag in ("failure", "error"):
        node = case.find(tag)
        if node is None:
            continue
        message = str(node.attrib.get("message") or "").strip()
        if message:
            return _focus_trim(message.replace("\n", " "), 160)
        text = str(node.text or "").strip()
        if text:
            return _focus_trim(text.splitlines()[0], 160)
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


def _build_focus_priority_verification_snapshot(*, auto_schedule: bool) -> dict[str, object]:
    profile_id = "focus-priorities"
    spec = dict(_TEST_PROFILE_SPECS.get(profile_id) or {})
    latest = _latest_test_report_record(profile_id)
    latest_report = latest.get("report") if isinstance(latest, dict) else None
    summary = dict(latest_report.get("summary") or {}) if isinstance(latest_report, dict) else {}
    latest_ts = _test_parse_iso_datetime(summary.get("timestamp")) or _test_parse_iso_datetime(latest.get("report_mtime_iso") if isinstance(latest, dict) else None)
    stale_after_minutes = int(spec.get("stale_after_minutes") or _FOCUS_PRIORITY_AUTO_VERIFY_MAX_AGE_MINUTES)
    now_utc = datetime.now(timezone.utc)
    age_minutes = round((now_utc - latest_ts).total_seconds() / 60.0, 1) if latest_ts else None
    failed = int(summary.get("failed") or 0)
    failing_names = _test_result_names_with_failures(latest_report)
    performance_failures = [name for name in failing_names if "performance" in name.lower() or "timeout" in name.lower() or "non_blocking" in name.lower()]

    if latest is None:
        status = "missing"
    elif failed > 0:
        status = "failing"
    elif age_minutes is not None and age_minutes > stale_after_minutes:
        status = "stale"
    else:
        status = "ok"

    tickets: list[dict[str, object]] = []
    timestamp = latest_ts.isoformat() if latest_ts else now_utc.isoformat()
    if status == "missing":
        tickets.append(
            {
                "ticket_id": "focus-priorities-missing",
                "summary": "Focus priority evals have not produced a report yet.",
                "title": "Focus priority evals missing",
                "status": "open",
                "severity": "high",
                "authority": "archivist-verifier",
                "kind": "verification",
                "issue_code": "focus-priorities-missing",
                "category": "verification",
                "created_at": timestamp,
                "last_seen_at": now_utc.isoformat(),
                "details": {"profile": profile_id},
            }
        )
    if status == "stale":
        tickets.append(
            {
                "ticket_id": "focus-priorities-stale",
                "summary": f"Focus priority evals are stale ({age_minutes:.1f} minutes old).",
                "title": "Focus priority evals stale",
                "status": "open",
                "severity": "high",
                "authority": "archivist-verifier",
                "kind": "verification",
                "issue_code": "focus-priorities-stale",
                "category": "verification",
                "created_at": timestamp,
                "last_seen_at": now_utc.isoformat(),
                "details": {
                    "profile": profile_id,
                    "age_minutes": age_minutes,
                    "stale_after_minutes": stale_after_minutes,
                },
            }
        )
    if failed > 0:
        tickets.append(
            {
                "ticket_id": "focus-priorities-failing",
                "summary": f"Focus priority evals are failing ({failed} failed).",
                "title": "Focus priority evals failing",
                "status": "open",
                "severity": "critical",
                "authority": "archivist-verifier",
                "kind": "verification",
                "issue_code": "focus-priorities-failing",
                "category": "verification",
                "created_at": timestamp,
                "last_seen_at": now_utc.isoformat(),
                "details": {
                    "profile": profile_id,
                    "failed": failed,
                    "examples": failing_names[:5],
                },
            }
        )
    if performance_failures:
        tickets.append(
            {
                "ticket_id": "focus-priorities-performance",
                "summary": "Focus priority performance checks are failing.",
                "title": "Focus priority performance regression",
                "status": "open",
                "severity": "high",
                "authority": "archivist-health",
                "kind": "performance",
                "issue_code": "focus-priorities-performance",
                "category": "performance",
                "created_at": timestamp,
                "last_seen_at": now_utc.isoformat(),
                "details": {
                    "profile": profile_id,
                    "examples": performance_failures[:5],
                },
            }
        )

    auto_run = {"scheduled": False, "reason": None, "run_id": None}
    task = _test_task_snapshot()
    should_auto_run = bool(spec.get("auto_run")) and status in {"missing", "stale", "failing"} and not task.get("running")
    if auto_schedule and should_auto_run:
        auto_state = _test_automation_snapshot()
        last_auto_at = _test_parse_iso_datetime(auto_state.get("last_auto_requested_at"))
        interval_ok = (
            last_auto_at is None
            or (now_utc - last_auto_at).total_seconds() >= _FOCUS_PRIORITY_AUTO_VERIFY_MIN_INTERVAL_SECONDS
        )
        if interval_ok:
            reason = f"auto:{status}"
            response, status_code = _start_test_run(profile_id, trigger=reason)
            if status_code == 200:
                auto_run = {
                    "scheduled": True,
                    "reason": status,
                    "run_id": str(response.get("run_id") or ""),
                }
                _update_test_automation_state(
                    last_auto_requested_at=now_utc.isoformat(),
                    last_auto_profile=profile_id,
                    last_auto_reason=status,
                    last_auto_run_id=str(response.get("run_id") or ""),
                )
                task = _test_task_snapshot()

    latest_summary = None
    if isinstance(latest_report, dict):
        latest_summary = {
            "run_id": summary.get("run_id"),
            "timestamp": summary.get("timestamp"),
            "passed": int(summary.get("passed") or 0),
            "failed": int(summary.get("failed") or 0),
            "total_tests": int(summary.get("total_tests") or 0),
            "pass_rate": float(summary.get("pass_rate") or 0.0),
            "age_minutes": age_minutes,
        }
    return {
        "profile": profile_id,
        "label": str(spec.get("label") or profile_id),
        "status": status,
        "owner_agents": list(spec.get("owner_agents") or []),
        "stale_after_minutes": stale_after_minutes,
        "latest": latest_summary,
        "tickets": tickets,
        "auto_run": auto_run,
        "task": {
            "running": bool(task.get("running")),
            "trigger": str(task.get("trigger") or ""),
            "run_id": str(task.get("run_id") or ""),
        },
    }


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
    for session in load_openclaw_sessions_for_agents(visible_agent_ids()):
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
    for session in load_openclaw_sessions_for_agents([agent_id]):
        if session.get("id") != session_id:
            continue
        session_file = resolve_openclaw_session_file(session.get("sessionFile"))
        if not session_file:
            return None
        return {
            "id": session_id,
            "agentId": agent_id,
            "sessionKey": session_key,
            "source": "openclaw",
            "messages": load_openclaw_messages_from_transcript(session_file),
        }
    return None


def _agent_runtime_snapshot() -> dict:
    config, config_path = load_openclaw_config()
    runtime = inspect_agent_runtime()
    runtime["registered_agents"] = registered_agent_ids(config)
    runtime["visible_agent_ids"] = visible_agent_ids()
    runtime["host_workspace"] = host_workspace()
    runtime["config_path"] = runtime.get("config_path") or (str(config_path) if config_path else None)
    return runtime


def _service_probes() -> list[dict]:
    probes: list[dict] = []
    runtime = _agent_runtime_snapshot()
    probes.append(
        {
            "name": "OpenClaw Gateway",
            "ok": bool(runtime.get("available")),
            "status": 200 if runtime.get("available") else 503,
            "target": resolve_gateway_url(),
            "latency_ms": None,
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


def _focus_recording_lane_summary(root: Path = Path("/media/mass/recording"), max_dates: int = 12) -> list[dict]:
    if not root.is_dir():
        return []

    date_dirs = sorted(
        (
            path
            for path in root.iterdir()
            if path.is_dir() and re.fullmatch(r"\d{4}-\d{2}-\d{2}", path.name)
        ),
        key=lambda path: path.name,
        reverse=True,
    )[:max_dates]
    counts: dict[str, int] = {}
    latest_paths: dict[str, str] = {}

    for date_dir in date_dirs:
        for hour_dir in date_dir.iterdir():
            if not hour_dir.is_dir():
                continue
            for lane_dir in hour_dir.iterdir():
                if not lane_dir.is_dir():
                    continue
                lane_name = lane_dir.name
                counts[lane_name] = counts.get(lane_name, 0) + 1
                latest_paths.setdefault(lane_name, str(lane_dir))

    return [
        {
            "name": name,
            "count": count,
            "latest_path": latest_paths.get(name),
        }
        for name, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]


def _focus_collection_count() -> int:
    alias = _milvus_alias("focus_overview")
    try:
        _milvus_connect(alias)
        return len(utility.list_collections(using=alias, timeout=MILVUS_CONNECT_TIMEOUT))
    except Exception:
        return 0
    finally:
        _milvus_disconnect(alias)


def _humanize_focus_label(value: str) -> str:
    return str(value or "").replace("_", " ").replace("-", " ").strip().title()


def _focus_git_snapshot(repo_root: Path | None = None) -> dict:
    root = repo_root or Path(__file__).resolve().parent
    try:
        status_result = subprocess.run(
            ["git", "status", "--short"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        )
        branch_result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        )
        commit_result = subprocess.run(
            ["git", "log", "-1", "--pretty=%s"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        )
    except Exception:
        return {
            "available": False,
            "branch": "",
            "modified": 0,
            "untracked": 0,
            "dirty": 0,
            "last_commit": "",
        }

    modified = 0
    untracked = 0
    for raw_line in status_result.stdout.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("??"):
            untracked += 1
        else:
            modified += 1

    return {
        "available": True,
        "branch": branch_result.stdout.strip(),
        "modified": modified,
        "untracked": untracked,
        "dirty": modified + untracked,
        "last_commit": commit_result.stdout.strip(),
    }


def _parse_focus_md(focus_path: Path | None = None) -> dict:
    """Read a focus markdown file and extract structured priority, calendar, blocker, and team data."""
    focus_path = focus_path or (Path(__file__).resolve().parent / "FOCUS.md")
    if not focus_path.is_file():
        return {"available": False}

    text = focus_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    def _strip_md(s: str) -> str:
        return re.sub(r"\*{1,2}(.+?)\*{1,2}", r"\1", s).strip()

    result: dict = {
        "available": True,
        "week_title": "",
        "role_line": "",
        "reports_line": "",
        "context_block": "",
        "priorities": [],
        "calendar": [],
        "critical_path": [],
        "blockers": [],
        "direct_reports": [],
    }

    # Header: week title
    for line in lines:
        if line.startswith("# Focus"):
            result["week_title"] = line.lstrip("# ").strip()
            break

    # Role and reports lines (first few non-empty, non-heading lines)
    for line in lines[1:8]:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith(">"):
            continue
        if "AI Director" in stripped or "Andy Payne" in stripped:
            result["role_line"] = stripped
        if "Reports to" in stripped or "Direct reports" in stripped:
            result["reports_line"] = stripped

    # Context block (the > quoted section)
    context_lines: list[str] = []
    in_context = False
    for line in lines:
        if line.startswith("> "):
            in_context = True
            context_lines.append(line[2:].strip())
        elif in_context and line.startswith(">"):
            context_lines.append(line[1:].strip())
        elif in_context:
            break
    result["context_block"] = " ".join(context_lines)

    # Helper: parse a markdown table following a section heading pattern
    def _parse_md_table(heading_pattern: str) -> list[dict]:
        match = re.search(heading_pattern, text, re.IGNORECASE)
        if not match:
            return []
        section_text = text[match.end():]
        table_lines: list[str] = []
        in_table = False
        for tl in section_text.splitlines():
            stripped = tl.strip()
            if stripped.startswith("|") and stripped.endswith("|"):
                in_table = True
                table_lines.append(stripped)
            elif in_table:
                break
        if len(table_lines) < 3:
            return []
        headers = [_strip_md(cell) for cell in table_lines[0].split("|")[1:-1]]
        rows: list[dict] = []
        for row_line in table_lines[2:]:
            cells = [_strip_md(cell) for cell in row_line.split("|")[1:-1]]
            if len(cells) >= len(headers):
                row = {headers[i].lower().replace(" ", "_"): cells[i] for i in range(len(headers))}
                rows.append(row)
        return rows

    result["priorities"] = _parse_md_table(r"## This Week.*?Priority Order\s*\n")
    result["calendar"] = _parse_md_table(r"## Calendar\s*\n")
    result["blockers"] = _parse_md_table(r"## Blockers\s*\n")

    # Critical path: numbered bold items
    critical_match = re.search(r"## Critical Path\s*\n", text)
    if critical_match:
        critical_section = text[critical_match.end():]
        for cl in critical_section.splitlines():
            stripped = cl.strip()
            if re.match(r"^\d+\.\s+\*\*", stripped):
                title_match = re.search(r"\*\*(.+?)\*\*", stripped)
                if title_match:
                    result["critical_path"].append(title_match.group(1))
            elif stripped.startswith("## ") or stripped.startswith("---"):
                break

    # Direct reports: ### Name — Focus sections
    report_pattern = re.compile(r"###\s+(\w+)\s*\u2014\s*(.+?)$", re.MULTILINE)
    for rmatch in report_pattern.finditer(text):
        name = rmatch.group(1)
        focus_area = rmatch.group(2).strip()
        section_start = rmatch.end()
        next_section = re.search(r"\n#{2,3}\s", text[section_start:])
        section_end = section_start + next_section.start() if next_section else len(text)
        section = text[section_start:section_end]
        this_week_items: list[str] = []
        in_this_week = False
        for sl in section.splitlines():
            stripped = sl.strip()
            if "this week" in stripped.lower() and stripped.startswith("**"):
                in_this_week = True
                continue
            if in_this_week and stripped.startswith("- "):
                this_week_items.append(_strip_md(stripped[2:].strip()))
            elif in_this_week and stripped and not stripped.startswith("- "):
                break
        result["direct_reports"].append({"name": name, "focus": focus_area, "this_week": this_week_items})

    # Detail sections: ### N. Title under ## Details
    details_match = re.search(r"## Details\s*\n", text)
    result["details"] = {}
    if details_match:
        details_text = text[details_match.end():]
        detail_pattern = re.compile(r"^### (\d+)\.\s+(.+?)$", re.MULTILINE)
        detail_matches = list(detail_pattern.finditer(details_text))
        for i, dm in enumerate(detail_matches):
            num = dm.group(1)
            body_start = dm.end()
            body_end = detail_matches[i + 1].start() if i + 1 < len(detail_matches) else len(details_text)
            # Stop at the next ## section
            next_h2 = re.search(r"^## ", details_text[body_start:body_end], re.MULTILINE)
            if next_h2:
                body_end = body_start + next_h2.start()
            body = details_text[body_start:body_end].strip().rstrip("-").strip()
            result["details"][num] = body

    # Open Questions: bullet list under ## Open Questions
    oq_match = re.search(r"## Open Questions\s*\n", text)
    result["open_questions"] = []
    if oq_match:
        oq_text = text[oq_match.end():]
        for oq_line in oq_text.splitlines():
            stripped = oq_line.strip()
            if stripped.startswith("- "):
                result["open_questions"].append(_strip_md(stripped[2:].strip()))
            elif stripped.startswith("## ") or stripped.startswith("---"):
                break

    # Product Ideas: table under ## Product Ideas Pipeline
    result["product_ideas"] = _parse_md_table(r"## Product Ideas Pipeline\s*\n")

    return result


def _focus_overview_payload(focus_path: Path | None = None) -> dict:
    """Build a sections-based focus payload from a focus markdown file."""
    focus = _parse_focus_md(focus_path)
    if not focus.get("available"):
        return {
            "available": False,
            "week_title": "",
            "role_line": "",
            "context": "",
            "sections": [],
        }

    def _strip_md(s: str) -> str:
        return re.sub(r"\*{1,2}(.+?)\*{1,2}", r"\1", s).strip()

    priorities = focus.get("priorities", [])
    details = focus.get("details", {})
    calendar_rows = focus.get("calendar", [])
    blockers_rows = focus.get("blockers", [])
    critical_path = focus.get("critical_path", [])
    direct_reports = focus.get("direct_reports", [])
    open_questions = focus.get("open_questions", [])
    product_ideas = focus.get("product_ideas", [])

    # Attach detail_md to each priority by matching on the # column
    priority_items = []
    for p in priorities:
        num = p.get("#", "").strip()
        item = {
            "num": num,
            "title": _strip_md(p.get("what", "")),
            "owner": _strip_md(p.get("owner", "")),
            "status": _strip_md(p.get("status", "")),
            "next_action": _strip_md(p.get("next_action", "")),
            "detail_md": details.get(num, ""),
        }
        priority_items.append(item)

    sections = []

    if priority_items:
        sections.append({
            "id": "priorities",
            "title": "Priorities",
            "kind": "priority_table",
            "items": priority_items,
        })

    if calendar_rows:
        sections.append({
            "id": "calendar",
            "title": "Calendar",
            "kind": "table",
            "columns": ["day", "time", "event"],
            "items": calendar_rows,
        })

    if blockers_rows:
        sections.append({
            "id": "blockers",
            "title": f"Blockers ({len(blockers_rows)})",
            "kind": "table",
            "columns": ["blocker", "impact", "who_can_unblock"],
            "items": blockers_rows,
        })

    if critical_path:
        sections.append({
            "id": "critical_path",
            "title": "Critical Path",
            "kind": "list",
            "items": critical_path,
        })

    if direct_reports:
        sections.append({
            "id": "direct_reports",
            "title": "Direct Reports",
            "kind": "people",
            "items": [{"name": dr.get("name", ""), "focus": dr.get("focus", ""), "this_week": dr.get("this_week", [])} for dr in direct_reports],
        })

    if open_questions:
        sections.append({
            "id": "open_questions",
            "title": f"Open Questions ({len(open_questions)})",
            "kind": "list",
            "items": open_questions,
        })

    if product_ideas:
        sections.append({
            "id": "product_ideas",
            "title": "Product Ideas",
            "kind": "table",
            "columns": ["idea", "source", "status"],
            "items": product_ideas,
        })

    context = re.sub(r"\*{1,2}(.+?)\*{1,2}", r"\1", focus.get("context_block", "")).strip()

    # Add live GitHub activity section (open PRs, review requests)
    try:
        from github_service import get_github_focus_data, GITHUB_TOKEN as _gh_token
        if _gh_token:
            gh_data = get_github_focus_data(os.getenv("GITHUB_USERNAME", ""))
            gh_items = []
            for pr in gh_data.get("open_prs", []):
                gh_items.append({
                    "num": f"PR#{pr.get('number', '')}",
                    "title": pr.get("title", ""),
                    "owner": pr.get("repo", ""),
                    "status": "open",
                    "next_action": pr.get("url", ""),
                    "detail_md": "",
                })
            for pr in gh_data.get("review_requests", []):
                gh_items.append({
                    "num": "Review",
                    "title": pr.get("title", ""),
                    "owner": pr.get("repo", ""),
                    "status": "review requested",
                    "next_action": pr.get("url", ""),
                    "detail_md": "",
                })
            for issue in gh_data.get("assigned_issues", []):
                gh_items.append({
                    "num": f"#{issue.get('number', '')}",
                    "title": issue.get("title", ""),
                    "owner": issue.get("repo", ""),
                    "status": "assigned",
                    "next_action": issue.get("url", ""),
                    "detail_md": "",
                })
            if gh_items:
                sections.append({
                    "id": "github",
                    "title": f"GitHub ({len(gh_items)})",
                    "kind": "priority_table",
                    "items": gh_items,
                })
    except Exception:
        logging.exception("failed to add GitHub data to focus")

    return {
        "available": True,
        "week_title": focus.get("week_title", ""),
        "role_line": focus.get("role_line", ""),
        "context": context,
        "sections": sections,
    }


_FOCUS_SYNC_ROOT = Path(os.getenv("ARCHIVIST_FOCUS_STATE_DIR", "~/.config/archivist/focus")).expanduser()
_FOCUS_PERSONAL_SNAPSHOT_FILE = _FOCUS_SYNC_ROOT / "personal_focus.json"
_FOCUS_MANUAL_PRIORITIES_FILE = _FOCUS_SYNC_ROOT / "manual_priorities.json"
_FOCUS_SCHEDULE_STATE_FILE = _FOCUS_SYNC_ROOT / ".schedule.json"
_FOCUS_WORK_NOTES_ROOT = Path(os.getenv("ARCHIVIST_WORK_NOTES_ROOT", "/home/andy/vnotes")).expanduser()
_FOCUS_SYNC_TIME_OF_DAY = str(os.getenv("ARCHIVIST_FOCUS_SYNC_TIME", "05:30")).strip() or "05:30"
_FOCUS_SYNC_TIMEZONE = str(os.getenv("ARCHIVIST_FOCUS_SYNC_TIMEZONE", os.getenv("TZ", "America/Chicago"))).strip() or "America/Chicago"
try:
    _FOCUS_MAX_AGE_HOURS = float(os.getenv("ARCHIVIST_FOCUS_MAX_AGE_HOURS", "6"))
except (TypeError, ValueError):
    _FOCUS_MAX_AGE_HOURS = 6.0
try:
    _FOCUS_WORK_CALENDAR_WINDOW_DAYS = max(1, int(os.getenv("ARCHIVIST_FOCUS_WORK_CALENDAR_WINDOW_DAYS", "21")))
except (TypeError, ValueError):
    _FOCUS_WORK_CALENDAR_WINDOW_DAYS = 21
try:
    _FOCUS_MANUAL_PRIORITY_LIMIT = max(1, int(os.getenv("ARCHIVIST_FOCUS_MANUAL_PRIORITY_LIMIT", "8")))
except (TypeError, ValueError):
    _FOCUS_MANUAL_PRIORITY_LIMIT = 8
_FOCUS_PROMPT_VERSION = 1
_FOCUS_WEEK_DIR_RE = re.compile(r"^WEEK(\d+)$", re.IGNORECASE)
_FOCUS_WORK_TEXT_PATTERNS = [
    re.compile(
        r"\b(versant|caddy|prism|easylynx|easylinks|beta customer|twilio|github action|jira|confluence|"
        r"devops|ecs|lambda|dashboard|oauth|wax|garrett|tanmay|sharif|victor|jonathan|jason|sms confirmation|"
        r"production bugs?|tool-call middleware|interview packet|performance goals?)\b",
        re.IGNORECASE,
    ),
]
_FOCUS_PERSONAL_TEXT_PATTERNS = [
    re.compile(r"\b(jonas|family|household|trash|recycle|pickup|bank|statement|billing|project hail mary|doctor|health|travel)\b", re.IGNORECASE),
]
_FOCUS_WORK_ACCOUNT_HINTS = [
    item.strip().lower()
    for item in str(os.getenv("ARCHIVIST_FOCUS_WORK_ACCOUNT_HINTS", "pyfi.org,versant")).split(",")
    if item.strip()
]
_FOCUS_PERSONAL_SYNC_STATE: dict[str, object] = {
    "running": False,
    "message": "",
    "startedAt": None,
    "finishedAt": None,
    "error": None,
}
_FOCUS_PERSONAL_SYNC_LOCK = threading.Lock()
_FOCUS_MANUAL_PRIORITIES_LOCK = threading.Lock()
_FOCUS_SCHEDULE_LOCK = threading.Lock()
_FOCUS_SCHEDULE_STATE_LOADED = False
_FOCUS_SCHEDULE_LAST_TRIGGERED_AT: datetime | None = None


def _focus_sync_tz():
    try:
        return ZoneInfo(_FOCUS_SYNC_TIMEZONE)
    except Exception:
        return timezone.utc


def _focus_parse_hhmm(value: str) -> tuple[int, int]:
    match = re.fullmatch(r"([01]?\d|2[0-3]):([0-5]\d)", str(value or "").strip())
    if not match:
        raise ValueError("focus sync time must be HH:MM (24h).")
    return int(match.group(1)), int(match.group(2))


def _focus_before_daily_refresh(now_local: datetime | None = None) -> bool:
    current = now_local or datetime.now(_focus_sync_tz())
    hour, minute = _focus_parse_hhmm(_FOCUS_SYNC_TIME_OF_DAY)
    return (current.hour, current.minute) < (hour, minute)


def _focus_archive_mutation_active() -> bool:
    try:
        return bool(_google_import_status_public().get("running"))
    except Exception:
        return False


def _focus_next_run(now_local: datetime | None = None) -> datetime:
    current = now_local or datetime.now(_focus_sync_tz())
    hour, minute = _focus_parse_hhmm(_FOCUS_SYNC_TIME_OF_DAY)
    candidate = current.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if candidate <= current:
        candidate += timedelta(days=1)
    return candidate


def _focus_scheduled_slot_at_or_before(now_local: datetime) -> datetime:
    hour, minute = _focus_parse_hhmm(_FOCUS_SYNC_TIME_OF_DAY)
    return now_local.replace(hour=hour, minute=minute, second=0, microsecond=0)


def _focus_schedule_state() -> None:
    global _FOCUS_SCHEDULE_STATE_LOADED, _FOCUS_SCHEDULE_LAST_TRIGGERED_AT
    if _FOCUS_SCHEDULE_STATE_LOADED:
        return
    _FOCUS_SCHEDULE_STATE_LOADED = True
    _FOCUS_SCHEDULE_LAST_TRIGGERED_AT = None
    try:
        if not _FOCUS_SCHEDULE_STATE_FILE.is_file():
            return
        payload = json.loads(_FOCUS_SCHEDULE_STATE_FILE.read_text(encoding="utf-8"))
        raw = str(payload.get("last_triggered_at") or "").strip()
        if raw:
            _FOCUS_SCHEDULE_LAST_TRIGGERED_AT = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:
        _FOCUS_SCHEDULE_LAST_TRIGGERED_AT = None


def _focus_save_schedule_state() -> None:
    _FOCUS_SYNC_ROOT.mkdir(parents=True, exist_ok=True)
    payload = {
        "last_triggered_at": _FOCUS_SCHEDULE_LAST_TRIGGERED_AT.astimezone(timezone.utc).isoformat()
        if _FOCUS_SCHEDULE_LAST_TRIGGERED_AT is not None
        else None
    }
    _FOCUS_SCHEDULE_STATE_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _focus_schedule_payload(now_local: datetime | None = None) -> dict:
    _focus_schedule_state()
    current = now_local or datetime.now(_focus_sync_tz())
    next_run = _focus_next_run(current)
    last_triggered = _FOCUS_SCHEDULE_LAST_TRIGGERED_AT.astimezone(timezone.utc).isoformat() if _FOCUS_SCHEDULE_LAST_TRIGGERED_AT else None
    return {
        "enabled": True,
        "time_of_day": _FOCUS_SYNC_TIME_OF_DAY,
        "timezone": _FOCUS_SYNC_TIMEZONE,
        "next_run_at": next_run.astimezone(timezone.utc).isoformat(),
        "last_triggered_at": last_triggered,
    }


def _focus_json_hash(payload: object) -> str:
    return sha256(json.dumps(payload, sort_keys=True, ensure_ascii=True).encode("utf-8")).hexdigest()


def _focus_iso_from_timestamp(timestamp: float | int | None) -> str | None:
    try:
        value = float(timestamp)
    except (TypeError, ValueError):
        return None
    if value <= 0:
        return None
    return datetime.fromtimestamp(value, tz=timezone.utc).isoformat()


def _focus_file_meta(path: Path | None) -> dict | None:
    if path is None or not path.is_file():
        return None
    try:
        stat = path.stat()
    except OSError:
        return None
    return {
        "path": str(path),
        "mtime": round(float(stat.st_mtime), 3),
        "size": int(stat.st_size),
    }


def _focus_parse_datetime(value: str | None) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except Exception:
        return None


def _focus_manual_priority_day_label(value: datetime | None = None) -> str:
    current = (value or datetime.now(timezone.utc)).astimezone(_focus_sync_tz())
    return f"{current.strftime('%b')} {current.day}"


def _focus_guess_manual_priority_title(text: str) -> str:
    clean = re.sub(r"\s+", " ", str(text or "")).strip(" -")
    if not clean:
        return "Manual priority"
    first_line = re.split(r"[\n\r]+", clean, maxsplit=1)[0].strip()
    first_sentence = re.split(r"(?<=[.!?])\s+", first_line, maxsplit=1)[0].strip()
    candidate = first_sentence.rstrip(".!?").strip() or first_line or clean
    return _focus_trim(candidate, 110)


def _focus_manual_priority_sample(section: dict) -> str:
    kind = str(section.get("kind") or "").strip()
    items = section.get("items") if isinstance(section.get("items"), list) else []
    if not items:
        return ""
    first = items[0]
    if kind == "priority_table" and isinstance(first, dict):
        title = str(first.get("title") or "").strip()
        next_action = str(first.get("next_action") or "").strip()
        return _focus_trim(title or next_action, 120)
    if kind == "table" and isinstance(first, dict):
        for key in ("event", "title", "blocker", "idea", "when", "date"):
            value = str(first.get(key) or "").strip()
            if value:
                return _focus_trim(value, 120)
    if kind == "list":
        return _focus_trim(str(first or "").strip(), 120)
    if kind == "people" and isinstance(first, dict):
        return _focus_trim(str(first.get("name") or first.get("focus") or "").strip(), 120)
    return ""


def _focus_manual_priority_context_payload(lane_id: str) -> dict:
    lane_key = str(lane_id or "").strip().lower()
    if lane_key == "personal":
        source_context = _focus_personal_source_context()
        lane = _focus_personal_lane_for_response(source_context)
    else:
        lane = _build_work_focus_lane()
    sections = []
    for section in list(lane.get("sections") or [])[:4]:
        if not isinstance(section, dict):
            continue
        sections.append(
            {
                "id": str(section.get("id") or ""),
                "title": str(section.get("title") or ""),
                "sample": _focus_manual_priority_sample(section),
            }
        )
    return {
        "laneId": lane_key,
        "title": str(lane.get("title") or ""),
        "subtitle": str(lane.get("subtitle") or ""),
        "context": _focus_trim(str(lane.get("context") or ""), 360),
        "sections": sections,
    }


def _focus_manual_priority_gateway_json(*, lane_id: str, purpose: str, system_prompt: str, user_prompt: str) -> dict | None:
    result_holder: dict[str, object] = {"payload": None}

    def _worker() -> None:
        result_holder["payload"] = _focus_call_gateway_json(
            lane_id=lane_id,
            purpose=purpose,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            timeout=max(1, int(math.ceil(_FOCUS_MANUAL_PRIORITY_GATEWAY_TIMEOUT_S))),
        )

    started = time.perf_counter()
    worker = threading.Thread(
        target=_worker,
        daemon=True,
        name=f"focus-manual-gateway-{lane_id}",
    )
    worker.start()
    worker.join(_FOCUS_MANUAL_PRIORITY_GATEWAY_TIMEOUT_S)
    elapsed_ms = round((time.perf_counter() - started) * 1000.0, 1)
    if worker.is_alive():
        logging.warning(
            "focus manual priority gateway call timed out lane=%s purpose=%s elapsed_ms=%.1f budget_s=%.2f",
            lane_id,
            purpose,
            elapsed_ms,
            _FOCUS_MANUAL_PRIORITY_GATEWAY_TIMEOUT_S,
        )
        return None
    payload = result_holder.get("payload")
    logging.info(
        "focus manual priority gateway call completed lane=%s purpose=%s elapsed_ms=%.1f gateway_used=%s",
        lane_id,
        purpose,
        elapsed_ms,
        isinstance(payload, dict),
    )
    return payload if isinstance(payload, dict) else None


def _focus_structure_manual_priority_entry(lane_id: str, text: str, *, allow_gateway: bool = True) -> dict:
    clean = re.sub(r"\s+", " ", str(text or "")).strip()
    now_utc = datetime.now(timezone.utc)
    entry = {
        "id": uuid4().hex,
        "laneId": lane_id,
        "createdAt": now_utc.isoformat(),
        "title": _focus_guess_manual_priority_title(clean),
        "status": f"Added {_focus_manual_priority_day_label(now_utc)}",
        "next_action": _focus_trim(clean, 180) or "Review this priority.",
        "detail_md": clean,
    }
    payload = None
    if allow_gateway:
        context_payload = _focus_manual_priority_context_payload(lane_id)
        payload = _focus_manual_priority_gateway_json(
            lane_id=f"manual-{lane_id}",
            purpose=f"manual-priority-{entry['id'][:12]}",
            system_prompt=(
                "You convert a human-entered note into one structured focus priority. "
                "Return only valid JSON. Keep the user's intent intact. Do not invent facts, deadlines, or names."
            ),
            user_prompt=(
                "Convert this note into a focus priority that fits the lane context.\n"
                "Return JSON with this shape:\n"
                "{\n"
                '  "title": string,\n'
                '  "status": string,\n'
                '  "next_action": string,\n'
                '  "detail_md": string\n'
                "}\n"
                f"Lane context:\n{json.dumps(context_payload, indent=2)}\n\n"
                f"Human note:\n{clean}"
            ),
        )
    if isinstance(payload, dict):
        title = _focus_trim(str(payload.get("title") or "").strip(), 120)
        status = _focus_trim(str(payload.get("status") or "").strip(), 140)
        next_action = _focus_trim(str(payload.get("next_action") or "").strip(), 180)
        detail_md = str(payload.get("detail_md") or "").strip()
        if title:
            entry["title"] = title
        if status:
            entry["status"] = status
        if next_action:
            entry["next_action"] = next_action
        if detail_md:
            entry["detail_md"] = detail_md
    return entry


def _focus_normalize_manual_priority_store(payload: object) -> dict[str, list[dict]]:
    normalized: dict[str, list[dict]] = {"work": [], "personal": []}
    if not isinstance(payload, dict):
        return normalized
    for lane_id in normalized:
        raw_entries = payload.get(lane_id)
        if not isinstance(raw_entries, list):
            continue
        seen_ids: set[str] = set()
        for raw_entry in raw_entries:
            if not isinstance(raw_entry, dict):
                continue
            entry_id = str(raw_entry.get("id") or uuid4().hex).strip()
            if not entry_id or entry_id in seen_ids:
                continue
            created_at = str(raw_entry.get("createdAt") or raw_entry.get("created_at") or datetime.now(timezone.utc).isoformat()).strip()
            detail_md = str(raw_entry.get("detail_md") or raw_entry.get("detail") or raw_entry.get("text") or "").strip()
            next_action = _focus_trim(str(raw_entry.get("next_action") or raw_entry.get("nextAction") or "").strip(), 180)
            title = _focus_trim(str(raw_entry.get("title") or "").strip(), 120)
            if not (title or next_action or detail_md):
                continue
            parsed_created = _focus_parse_datetime(created_at)
            normalized[lane_id].append(
                {
                    "id": entry_id,
                    "laneId": lane_id,
                    "createdAt": created_at,
                    "title": title or _focus_guess_manual_priority_title(detail_md or next_action),
                    "status": _focus_trim(
                        str(raw_entry.get("status") or f"Added {_focus_manual_priority_day_label(parsed_created)}").strip(),
                        140,
                    ),
                    "next_action": next_action or _focus_trim(detail_md or title, 180) or "Review this priority.",
                    "detail_md": detail_md or next_action or title,
                }
            )
            seen_ids.add(entry_id)
            if len(normalized[lane_id]) >= _FOCUS_MANUAL_PRIORITY_LIMIT:
                break
    return normalized


def _load_focus_manual_priorities() -> dict[str, list[dict]]:
    with _FOCUS_MANUAL_PRIORITIES_LOCK:
        try:
            if not _FOCUS_MANUAL_PRIORITIES_FILE.is_file():
                return {"work": [], "personal": []}
            payload = json.loads(_FOCUS_MANUAL_PRIORITIES_FILE.read_text(encoding="utf-8"))
            return _focus_normalize_manual_priority_store(payload)
        except Exception:
            logging.exception("failed to load focus manual priorities")
            return {"work": [], "personal": []}


def _save_focus_manual_priorities(payload: dict[str, list[dict]]) -> None:
    normalized = _focus_normalize_manual_priority_store(payload)
    with _FOCUS_MANUAL_PRIORITIES_LOCK:
        _FOCUS_SYNC_ROOT.mkdir(parents=True, exist_ok=True)
        _FOCUS_MANUAL_PRIORITIES_FILE.write_text(json.dumps(normalized, indent=2), encoding="utf-8")


def _focus_manual_priority_model_payload(entries: list[dict]) -> list[dict]:
    payload: list[dict] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        payload.append(
            {
                "id": str(entry.get("id") or "").strip(),
                "title": _focus_trim(str(entry.get("title") or "").strip(), 120),
                "status": _focus_trim(str(entry.get("status") or "").strip(), 140),
                "next_action": _focus_trim(str(entry.get("next_action") or "").strip(), 180),
                "detail_md": str(entry.get("detail_md") or "").strip(),
            }
        )
    return payload


def _focus_manual_priority_entry_from_model(raw_entry: object, lane_id: str, existing_by_id: dict[str, dict], now_utc: datetime) -> dict | None:
    if not isinstance(raw_entry, dict):
        return None
    raw_id = str(raw_entry.get("id") or "").strip()
    existing = existing_by_id.get(raw_id) if raw_id else None
    existing_entry = existing if isinstance(existing, dict) else {}
    title = _focus_trim(str(raw_entry.get("title") or "").strip(), 120)
    status = _focus_trim(str(raw_entry.get("status") or "").strip(), 140)
    next_action = _focus_trim(str(raw_entry.get("next_action") or raw_entry.get("nextAction") or "").strip(), 180)
    detail_md = str(raw_entry.get("detail_md") or raw_entry.get("detail") or raw_entry.get("text") or "").strip()
    if not (title or next_action or detail_md or existing):
        return None
    seed = detail_md or next_action or title
    return {
        "id": str(existing_entry.get("id") or uuid4().hex),
        "laneId": lane_id,
        "createdAt": str(existing_entry.get("createdAt") or now_utc.isoformat()),
        "title": title or _focus_trim(str(existing_entry.get("title") or "").strip(), 120) or _focus_guess_manual_priority_title(seed),
        "status": status or _focus_trim(str(existing_entry.get("status") or "").strip(), 140) or f"Updated {_focus_manual_priority_day_label(now_utc)}",
        "next_action": next_action or _focus_trim(str(existing_entry.get("next_action") or "").strip(), 180) or _focus_trim(seed, 180) or "Review this priority.",
        "detail_md": detail_md or str(existing_entry.get("detail_md") or "").strip() or next_action or title,
    }


def _focus_apply_manual_priority_note(lane_id: str, text: str) -> dict:
    lane_key = str(lane_id or "").strip().lower()
    if lane_key not in {"work", "personal"}:
        raise ValueError("laneId must be 'work' or 'personal'.")
    clean = str(text or "").strip()
    if not clean:
        raise ValueError("text is required.")
    payload = _load_focus_manual_priorities()
    existing_entries = list(payload.get(lane_key) or [])
    now_utc = datetime.now(timezone.utc)
    context_payload = _focus_manual_priority_context_payload(lane_key)
    gateway_payload = _focus_manual_priority_gateway_json(
        lane_id=f"manual-{lane_key}",
        purpose=f"manual-priority-update-{sha256(clean.encode('utf-8')).hexdigest()[:12]}",
        system_prompt=(
            "You revise a lane's manual priority list from a human note. "
            "The manual list is the editable layer on top of archive-driven focus. "
            "You may add, remove, rewrite, merge, split, or reorder manual items. "
            "Do not invent facts, deadlines, or names that are not in the note or existing items. "
            "Return only valid JSON."
        ),
        user_prompt=(
            "Revise the manual priority list for this lane.\n"
            "Return JSON with this shape:\n"
            "{\n"
            '  "items": [\n'
            "    {\n"
            '      "id": string,\n'
            '      "title": string,\n'
            '      "status": string,\n'
            '      "next_action": string,\n'
            '      "detail_md": string\n'
            "    }\n"
            "  ]\n"
            "}\n"
            "Rules:\n"
            f"- Keep at most {_FOCUS_MANUAL_PRIORITY_LIMIT} items.\n"
            "- Preserve an item's id when it still exists after the revision.\n"
            "- Use an empty id for any new item.\n"
            "- If the note removes or resolves something, leave it out of the returned items.\n"
            "- If the note reorders priorities, return the items in that order.\n"
            "- Update only the manual list. The archive-driven lane context is reference-only.\n"
            "- If the note is exploratory and does not imply a concrete change, keep the list as-is.\n"
            f"Lane context:\n{json.dumps(context_payload, indent=2)}\n\n"
            f"Current manual priorities:\n{json.dumps(_focus_manual_priority_model_payload(existing_entries), indent=2)}\n\n"
            f"Human note:\n{clean}"
        ),
    )

    next_entries: list[dict] | None = None
    if isinstance(gateway_payload, dict) and isinstance(gateway_payload.get("items"), list):
        raw_items = list(gateway_payload.get("items") or [])
        existing_by_id = {
            str(entry.get("id") or "").strip(): entry
            for entry in existing_entries
            if isinstance(entry, dict) and str(entry.get("id") or "").strip()
        }
        next_entries = []
        seen_ids: set[str] = set()
        for raw_entry in raw_items:
            entry = _focus_manual_priority_entry_from_model(raw_entry, lane_key, existing_by_id, now_utc)
            if not entry:
                continue
            entry_id = str(entry.get("id") or "").strip()
            if not entry_id or entry_id in seen_ids:
                continue
            seen_ids.add(entry_id)
            next_entries.append(entry)
            if len(next_entries) >= _FOCUS_MANUAL_PRIORITY_LIMIT:
                break
        if raw_items and not next_entries:
            next_entries = None

    if next_entries is None:
        logging.info("focus manual priority note fell back to local entry lane=%s", lane_key)
        entry = _focus_structure_manual_priority_entry(lane_key, clean, allow_gateway=False)
        next_entries = [entry, *existing_entries][: _FOCUS_MANUAL_PRIORITY_LIMIT]

    payload[lane_key] = next_entries
    _save_focus_manual_priorities(payload)
    return {
        "laneId": lane_key,
        "entries": next_entries,
        "updatedAt": now_utc.isoformat(),
    }


def _delete_focus_manual_priority(entry_id: str) -> dict | None:
    target_id = str(entry_id or "").strip()
    if not target_id:
        return None
    payload = _load_focus_manual_priorities()
    removed = None
    for lane_id in ("work", "personal"):
        next_entries = []
        for entry in list(payload.get(lane_id) or []):
            if str(entry.get("id") or "") == target_id and removed is None:
                removed = entry
                continue
            next_entries.append(entry)
        payload[lane_id] = next_entries
    if removed is not None:
        _save_focus_manual_priorities(payload)
    return removed


def _focus_parse_iso_day(value: str | None):
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(f"{text[:10]}T00:00:00").date()
    except Exception:
        return None


def _focus_week_end_from_title(value: str | None):
    dates = []
    for raw in re.findall(r"\b20\d{2}-\d{2}-\d{2}\b", str(value or "")):
        parsed = _focus_parse_iso_day(raw)
        if parsed is not None:
            dates.append(parsed)
    return max(dates) if dates else None


def _focus_business_notes_stale(parsed: dict, *, fallback_source: bool) -> bool:
    if fallback_source:
        return True
    week_end = _focus_week_end_from_title(str(parsed.get("week_title") or ""))
    if week_end is None:
        return False
    today = datetime.now(_focus_sync_tz()).date()
    return week_end < (today - timedelta(days=1))


def _focus_account_is_work_like(value: str | None) -> bool:
    text = str(value or "").strip().lower()
    if not text:
        return False
    return any(hint in text for hint in _FOCUS_WORK_ACCOUNT_HINTS)


def _focus_format_calendar_when(record: dict) -> str:
    raw_start = str(record.get("start") or "").strip()
    day = str(record.get("day") or "").strip()
    if "T" in raw_start:
        try:
            dt = datetime.fromisoformat(raw_start.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            local_dt = dt.astimezone(_focus_sync_tz())
            return local_dt.strftime("%b %d, %I:%M %p").replace(" 0", " ")
        except Exception:
            pass
    return day or raw_start


def _focus_recent_work_calendar_events() -> list[dict]:
    root = _google_archive_root()
    if not root.is_dir():
        return []

    today = datetime.now(_focus_sync_tz()).date()
    window_start = today - timedelta(days=_FOCUS_WORK_CALENDAR_WINDOW_DAYS)
    window_end = today + timedelta(days=_FOCUS_WORK_CALENDAR_WINDOW_DAYS)
    events: list[dict] = []

    for account_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        for record in _jsonl_read(account_dir / "calendar_events.jsonl"):
            day = _focus_parse_iso_day(str(record.get("day") or ""))
            if day is None or not (window_start <= day <= window_end):
                continue
            summary = str(record.get("summary") or "").strip()
            if not summary or _google_archive_is_routine_calendar_item(summary):
                continue
            text_blob = " ".join(
                [
                    summary,
                    str(record.get("description") or ""),
                    str(record.get("calendar_summary") or ""),
                    str(record.get("account") or ""),
                    " ".join(str(item or "") for item in (record.get("attendees") or [])),
                ]
            )
            if not (_focus_text_is_work_like(text_blob) or _focus_account_is_work_like(str(record.get("account") or ""))):
                continue
            events.append(
                {
                    "date": day.isoformat(),
                    "start": str(record.get("start") or ""),
                    "when": _focus_format_calendar_when(record),
                    "event": _focus_trim(summary, 110),
                    "calendar": _focus_trim(str(record.get("calendar_summary") or record.get("account") or "Calendar"), 80),
                    "description": _focus_trim(str(record.get("description") or ""), 280),
                    "account": str(record.get("account") or ""),
                }
            )

    events.sort(key=lambda item: (str(item.get("date") or ""), str(item.get("start") or ""), str(item.get("event") or "")))
    return events


def _focus_recent_business_journal_items() -> list[dict]:
    try:
        overview = _build_google_journal_overview()
    except Exception:
        logging.debug("failed to load journal overview for focus business signals", exc_info=True)
        return []

    today = datetime.now(_focus_sync_tz()).date()
    window_start = today - timedelta(days=_FOCUS_WORK_CALENDAR_WINDOW_DAYS)
    window_end = today + timedelta(days=_FOCUS_WORK_CALENDAR_WINDOW_DAYS)
    source_rank = {"git": 0, "github": 1, "drive": 2, "email": 3, "media": 4, "chat": 5}
    items: list[dict] = []
    seen: set[str] = set()

    for day_payload in overview.get("days") or []:
        day = _focus_parse_iso_day(str(day_payload.get("date") or ""))
        if day is None or not (window_start <= day <= window_end):
            continue
        day_title = str(day_payload.get("title") or "").strip()
        if day == today:
            status = "Today"
        elif day > today:
            status = f"Upcoming {day.strftime('%b %-d')}"
        else:
            status = f"Recent {day.strftime('%b %-d')}"
        for group in day_payload.get("evidence") or []:
            source = str(group.get("key") or "").strip()
            for evidence in group.get("items") or []:
                title = str(evidence.get("title") or "").strip()
                detail = str(evidence.get("detail") or "").strip()
                kind = str(evidence.get("kind") or "").strip().lower()
                text_blob = " ".join([title, detail, day_title, source, kind])
                lowered = text_blob.lower()
                project_like = (
                    source in {"git", "github"}
                    or kind in {"code", "work"}
                    or _focus_text_is_work_like(text_blob)
                    or bool(
                        re.search(
                            r"\b(pr #\d+|pull request|github|portfolio|ascensus|candidate|recruiting|booking confirmation|ai leadership|data leadership)\b",
                            lowered,
                        )
                    )
                )
                if not project_like:
                    continue
                key = re.sub(r"\s+", " ", title.lower())
                if not key or key in seen:
                    continue
                seen.add(key)
                items.append(
                    {
                        "date": day.isoformat(),
                        "rank": source_rank.get(source, 9),
                        "title": _focus_trim(title, 120),
                        "status": status,
                        "next_action": "Review the underlying evidence and decide whether this changes the active business priority list.",
                        "detail": _focus_trim(
                            f"{source.upper()} signal from {day.isoformat()}: {detail or day_title}",
                            360,
                        ),
                    }
                )

    items.sort(key=lambda item: (abs((_focus_parse_iso_day(str(item.get("date") or "")) or today) - today).days, int(item.get("rank") or 9), str(item.get("title") or "")))
    return items[:8]


def _focus_business_archive_sections() -> tuple[list[dict], str]:
    events = _focus_recent_work_calendar_events()
    journal_items = _focus_recent_business_journal_items()
    if not events and not journal_items:
        return [], ""

    today = datetime.now(_focus_sync_tz()).date()

    def _event_priority_key(item: dict) -> tuple[int, int, str]:
        day = _focus_parse_iso_day(str(item.get("date") or "")) or today
        upcoming_rank = 0 if day >= today else 1
        return upcoming_rank, abs((day - today).days), str(item.get("start") or "")

    priority_items = []
    seen: set[str] = set()
    for item in journal_items:
        title = str(item.get("title") or "").strip()
        if not title:
            continue
        lowered = title.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        priority_items.append(
            _focus_priority_item(
                len(priority_items) + 1,
                title,
                str(item.get("status") or ""),
                str(item.get("next_action") or ""),
                str(item.get("detail") or ""),
            )
        )
        if len(priority_items) >= 5:
            break
    for item in sorted(events, key=_event_priority_key):
        if len(priority_items) >= 5:
            break
        event = str(item.get("event") or "").strip()
        if not event:
            continue
        lowered = event.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        day = _focus_parse_iso_day(str(item.get("date") or "")) or today
        if day == today:
            status = "Today"
        elif day > today:
            status = f"Upcoming {item.get('when')}"
        else:
            status = f"Recent {item.get('when')}"
        detail = str(item.get("description") or "").strip()
        priority_items.append(
            _focus_priority_item(
                len(priority_items) + 1,
                event,
                status,
                "Review the meeting context and update the business notes if it changes priorities.",
                detail,
            )
        )

    meeting_rows = [
        {
            "when": str(item.get("when") or ""),
            "event": str(item.get("event") or ""),
            "calendar": str(item.get("calendar") or ""),
        }
        for item in events[:12]
    ]
    sections = []
    if priority_items:
        sections.append({"id": "current_business_signals", "title": "Current Business Signals", "kind": "priority_table", "items": priority_items})
    if journal_items:
        sections.append(
            {
                "id": "recent_project_signals",
                "title": "Recent Project Signals",
                "kind": "table",
                "columns": ["date", "title", "status"],
                "items": [
                    {
                        "date": str(item.get("date") or ""),
                        "title": str(item.get("title") or ""),
                        "status": str(item.get("status") or ""),
                    }
                    for item in journal_items[:12]
                ],
            }
        )
    if meeting_rows:
        sections.append({"id": "recent_business_meetings", "title": "Recent/Upcoming Meetings", "kind": "table", "columns": ["when", "event", "calendar"], "items": meeting_rows})

    context_parts = []
    if journal_items:
        context_parts.append(f"{len(journal_items)} project/work signal(s)")
    if events:
        context_parts.append(f"{len(events)} business calendar event(s)")
    context = f"Google archive has {_google_archive_join_phrases(context_parts)} in the current focus window."
    return sections, context


def _focus_work_bundle() -> dict:
    root = _FOCUS_WORK_NOTES_ROOT
    candidates: list[tuple[float, int, Path]] = []
    if root.is_dir():
        for child in root.iterdir():
            if not child.is_dir():
                continue
            match = _FOCUS_WEEK_DIR_RE.fullmatch(child.name)
            if not match:
                continue
            focus_path = child / "FOCUS.md"
            if not focus_path.is_file():
                continue
            try:
                mtime = focus_path.stat().st_mtime
            except OSError:
                mtime = 0.0
            candidates.append((mtime, int(match.group(1)), child))

    if candidates:
        _, _, week_dir = sorted(candidates, key=lambda item: (-item[0], -item[1], str(item[2])))[0]
        focus_path = week_dir / "FOCUS.md"
        schedule_path = week_dir / "SCHEDULE.md"
        journal_path = root / "JOURNAL.md"
        return {
            "available": True,
            "label": week_dir.name,
            "root": str(root),
            "focus_path": focus_path,
            "schedule_path": schedule_path if schedule_path.is_file() else None,
            "journal_path": journal_path if journal_path.is_file() else None,
        }

    fallback_focus = Path(__file__).resolve().parent / "FOCUS.md"
    return {
        "available": fallback_focus.is_file(),
        "label": "repo",
        "root": str(fallback_focus.parent),
        "focus_path": fallback_focus if fallback_focus.is_file() else None,
        "schedule_path": None,
        "journal_path": None,
    }


def _build_work_focus_lane() -> dict:
    bundle = _focus_work_bundle()
    focus_path = bundle.get("focus_path")
    if not focus_path:
        archive_sections, archive_context = _focus_business_archive_sections()
        return {
            "id": "work",
            "title": "Business",
            "subtitle": "",
            "context": archive_context,
            "available": bool(archive_sections),
            "sourceLabel": "Business archive signals" if archive_sections else "Business notes",
            "sourcePath": None,
            "generatedAt": None,
            "sections": archive_sections,
            "sourceWarning": f"Business notes root {_FOCUS_WORK_NOTES_ROOT} was not found.",
        }

    parsed = _focus_overview_payload(Path(focus_path))
    source_files = [
        item
        for item in [
            _focus_file_meta(Path(focus_path)),
            _focus_file_meta(bundle.get("schedule_path")),
            _focus_file_meta(bundle.get("journal_path")),
        ]
        if item
    ]
    latest_source_at = None
    for item in source_files:
        mtime = item.get("mtime")
        if mtime is None:
            continue
        iso = _focus_iso_from_timestamp(float(mtime))
        if iso and (latest_source_at is None or iso > latest_source_at):
            latest_source_at = iso

    subtitle = str(parsed.get("role_line") or "").strip()
    if bundle.get("label") and bundle.get("label") != "repo":
        subtitle = f"{subtitle} · {bundle['label']}" if subtitle else str(bundle["label"])

    fallback_source = str(bundle.get("label") or "") == "repo"
    notes_stale = _focus_business_notes_stale(parsed, fallback_source=fallback_source)
    archive_sections, archive_context = _focus_business_archive_sections()
    notes_sections = list(parsed.get("sections") or [])
    if notes_stale:
        for section in notes_sections:
            if section.get("id") == "priorities":
                section["title"] = "Priorities (Notes)"
                break
    sections = [*archive_sections, *notes_sections] if notes_stale else [*notes_sections, *archive_sections]
    context_bits = []
    if archive_context and (notes_stale or not notes_sections):
        context_bits.append(archive_context)
    parsed_context = str(parsed.get("context") or "").strip()
    if parsed_context:
        context_bits.append(parsed_context)

    source_warning = None
    if fallback_source:
        source_warning = f"Business notes root {_FOCUS_WORK_NOTES_ROOT} was not found; showing repo fallback notes plus archive signals."
    elif notes_stale:
        source_warning = "Business notes appear older than the current focus window; archive signals are shown first."

    return {
        "id": "work",
        "title": "Business",
        "subtitle": subtitle,
        "context": " ".join(context_bits).strip(),
        "available": bool(parsed.get("available")) or bool(archive_sections),
        "sourceLabel": "Fallback business notes" if fallback_source else "Latest business notes",
        "sourcePath": str(focus_path),
        "generatedAt": latest_source_at,
        "sections": sections,
        "sourceFiles": source_files,
        "weekTitle": str(parsed.get("week_title") or "").strip(),
        "sourceWarning": source_warning,
    }


def _focus_text_is_work_like(value: str | None) -> bool:
    text = str(value or "").strip()
    if not text:
        return False
    return any(pattern.search(text) for pattern in _FOCUS_WORK_TEXT_PATTERNS)


def _focus_text_is_personal_like(value: str | None) -> bool:
    text = str(value or "").strip()
    if not text:
        return False
    return any(pattern.search(text) for pattern in _FOCUS_PERSONAL_TEXT_PATTERNS)


def _focus_trim(value: str | None, max_chars: int = 180) -> str:
    clean = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(clean) <= max_chars:
        return clean
    clipped = clean[: max(1, max_chars - 1)].rsplit(" ", 1)[0].strip()
    return f"{clipped or clean[: max(1, max_chars - 1)]}…"


def _focus_personal_source_context() -> dict:
    overview = _build_google_journal_overview()
    today = datetime.now(_focus_sync_tz()).date()
    window_start = today - timedelta(days=4)
    window_end = today + timedelta(days=7)

    selected_days: list[dict] = []
    for day in overview.get("days", []) or []:
        raw_date = str(day.get("date") or "").strip()
        if not raw_date:
            continue
        try:
            day_date = datetime.fromisoformat(f"{raw_date}T00:00:00").date()
        except Exception:
            continue
        if not (window_start <= day_date <= window_end):
            continue
        title = str(day.get("title") or "").strip()
        focus = str(day.get("focus") or "").strip()
        summary = str(day.get("summary") or "").strip()
        sections = [
            {
                "label": str(section.get("label") or "").strip(),
                "text": _focus_trim(str(section.get("text") or "").strip(), 200),
            }
            for section in (day.get("sections") or [])[:2]
            if str(section.get("text") or "").strip()
        ]
        signals = [
            {
                "key": str(signal.get("key") or "").strip(),
                "count": str(signal.get("count") or "").strip(),
                "note": _focus_trim(str(signal.get("note") or "").strip(), 120),
            }
            for signal in (day.get("signals") or [])[:4]
            if str(signal.get("count") or "").strip()
        ]
        text_blob = " ".join([title, focus, summary, *[item["text"] for item in sections], *[item["note"] for item in signals]])
        selected_days.append(
            {
                "date": raw_date,
                "title": title,
                "focus": focus,
                "summary": summary,
                "sections": sections,
                "signals": signals,
                "sources": list(day.get("sources") or []),
                "signalCount": int(day.get("signalCount") or 0),
                "work_like": _focus_text_is_work_like(text_blob),
                "personal_like": _focus_text_is_personal_like(text_blob),
            }
        )

    recent_days = [item for item in selected_days if item["date"] <= today.isoformat()]
    upcoming_days = [item for item in selected_days if item["date"] > today.isoformat()]
    context = {
        "today": today.isoformat(),
        "weekWindow": {
            "start": (today - timedelta(days=today.weekday())).isoformat(),
            "end": (today - timedelta(days=today.weekday()) + timedelta(days=6)).isoformat(),
        },
        "archiveFingerprint": str(overview.get("archiveFingerprint") or ""),
        "lastImportedAt": overview.get("lastImportedAt"),
        "generatedAt": overview.get("generatedAt"),
        "recentDays": recent_days,
        "upcomingDays": upcoming_days,
    }
    context["fingerprint"] = _focus_json_hash(
        {
            "prompt_version": _FOCUS_PROMPT_VERSION,
            "today": context["today"],
            "archiveFingerprint": context["archiveFingerprint"],
            "recentDays": recent_days,
            "upcomingDays": upcoming_days,
        }
    )
    return context


def _focus_strip_json_fences(text: str) -> str:
    clean = str(text or "").strip()
    if clean.startswith("```"):
        clean = re.sub(r"^```(?:json)?\s*", "", clean, flags=re.IGNORECASE)
        clean = re.sub(r"\s*```$", "", clean)
    return clean.strip()


def _focus_parse_json_blob(text: str) -> dict | None:
    clean = _focus_strip_json_fences(text)
    if not clean:
        return None
    candidates = [clean]
    start = clean.find("{")
    end = clean.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidates.append(clean[start : end + 1])
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except Exception:
            continue
        if isinstance(parsed, dict):
            return parsed
    return None


def _focus_call_gateway_json(*, lane_id: str, purpose: str, system_prompt: str, user_prompt: str, timeout: int = 90) -> dict | None:
    gateway_token = resolve_gateway_token()
    if not gateway_token:
        return None

    try:
        import requests as _requests

        agent_id = str(os.getenv("ARCHIVIST_FOCUS_SYNC_AGENT_ID", console_agent_id())).strip() or console_agent_id()
        response = _requests.post(
            f"{resolve_gateway_url()}/v1/chat/completions",
            json={
                "model": f"openclaw/{agent_id}",
                "stream": False,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "user": gateway_session_key(agent_id, f"focus:{lane_id}:{purpose}"),
            },
            headers={
                "Authorization": f"Bearer {gateway_token}",
                "Content-Type": "application/json",
                "x-openclaw-agent-id": agent_id,
                "x-openclaw-session-key": gateway_session_key(agent_id, f"focus:{lane_id}:{purpose}"),
            },
            timeout=timeout,
        )
        response.raise_for_status()
        payload = response.json()
        content = str(payload.get("choices", [{}])[0].get("message", {}).get("content", "") or "").strip()
        return _focus_parse_json_blob(content)
    except Exception:
        logging.exception("focus sync gateway call failed for %s", lane_id)
        return None


def _focus_priority_item(num: int, title: str, status: str, next_action: str, detail_md: str, owner: str = "Andy") -> dict:
    return {
        "num": str(num),
        "title": _focus_trim(title, 120),
        "owner": owner,
        "status": _focus_trim(status, 140),
        "next_action": _focus_trim(next_action, 160),
        "detail_md": detail_md.strip(),
    }


def _focus_manual_priority_items(lane_id: str) -> list[dict]:
    entries = list(_load_focus_manual_priorities().get(str(lane_id or "").strip().lower(), []) or [])
    items: list[dict] = []
    for index, entry in enumerate(entries, start=1):
        item = _focus_priority_item(
            index,
            str(entry.get("title") or ""),
            str(entry.get("status") or ""),
            str(entry.get("next_action") or ""),
            str(entry.get("detail_md") or ""),
            owner="Andy",
        )
        item["manualId"] = str(entry.get("id") or "")
        item["createdAt"] = str(entry.get("createdAt") or "")
        items.append(item)
    return items


def _focus_apply_manual_priorities(lane: dict) -> dict:
    lane_id = str((lane or {}).get("id") or "").strip().lower()
    if lane_id not in {"work", "personal"}:
        return lane
    manual_items = _focus_manual_priority_items(lane_id)
    if not manual_items:
        return lane
    sections = [copy.deepcopy(section) for section in list(lane.get("sections") or []) if isinstance(section, dict)]
    sections = [section for section in sections if str(section.get("id") or "") != "manual_priorities"]
    sections.insert(
        0,
        {
            "id": "manual_priorities",
            "title": "Manual Focus",
            "kind": "priority_table",
            "items": manual_items,
        },
    )
    lane["sections"] = sections
    lane["available"] = True
    lane["manualPriorityCount"] = len(manual_items)
    return lane


def _build_personal_focus_fallback_lane(source_context: dict) -> dict:
    today = str(source_context.get("today") or "")
    priority_items: list[dict] = []
    priority_candidates = [
        day
        for day in [*(source_context.get("upcomingDays") or []), *(source_context.get("recentDays") or [])]
        if not day.get("work_like")
    ]
    if not priority_candidates:
        priority_candidates = list(source_context.get("upcomingDays") or []) or list(source_context.get("recentDays") or [])

    seen_titles: set[str] = set()
    for day in priority_candidates:
        title = str(day.get("focus") or day.get("title") or "").strip()
        if not title:
            continue
        lowered = title.lower()
        if lowered in seen_titles:
            continue
        seen_titles.add(lowered)
        status = "Today" if day.get("date") == today else ("Upcoming" if day.get("date", "") > today else "Recent")
        next_action = str(day.get("summary") or "").strip()
        detail_bits = [next_action]
        for section in day.get("sections") or []:
            text = str(section.get("text") or "").strip()
            if text:
                detail_bits.append(text)
        priority_items.append(
            _focus_priority_item(
                len(priority_items) + 1,
                title,
                status,
                next_action or "Review the supporting signals for this day.",
                "\n\n".join(bit for bit in detail_bits if bit),
            )
        )
        if len(priority_items) >= 5:
            break

    upcoming_rows = []
    for day in (source_context.get("upcomingDays") or [])[:6]:
        upcoming_rows.append(
            {
                "when": str(day.get("date") or ""),
                "event": _focus_trim(str(day.get("title") or day.get("focus") or "").strip(), 80),
                "why": _focus_trim(str(day.get("summary") or "").strip(), 140),
            }
        )

    watchlist = []
    for day in (source_context.get("recentDays") or [])[:6]:
        summary = str(day.get("summary") or "").strip()
        if not summary or day.get("work_like"):
            continue
        watchlist.append(_focus_trim(summary, 140))
        if len(watchlist) >= 5:
            break

    context_lines = []
    if priority_items:
        context_lines.append(f"Personal focus is being inferred from {len(priority_items)} recent or upcoming personal signals.")
    if upcoming_rows:
        context_lines.append(f"There are {len(upcoming_rows)} upcoming calendar-backed personal items in the next week.")

    sections = []
    if priority_items:
        sections.append({"id": "priorities", "title": "Priorities", "kind": "priority_table", "items": priority_items})
    if upcoming_rows:
        sections.append({"id": "upcoming", "title": "Upcoming", "kind": "table", "columns": ["when", "event", "why"], "items": upcoming_rows})
    if watchlist:
        sections.append({"id": "watchlist", "title": "Watchlist", "kind": "list", "items": watchlist})

    return {
        "id": "personal",
        "title": "Personal",
        "subtitle": "Archive-driven personal focus",
        "context": " ".join(context_lines).strip(),
        "available": bool(sections),
        "sourceLabel": "Personal archive synthesis",
        "sourcePath": None,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "sections": sections,
    }


def _normalize_personal_focus_payload(payload: dict, source_context: dict) -> dict:
    priorities_raw = payload.get("priorities") if isinstance(payload.get("priorities"), list) else []
    priority_items: list[dict] = []
    for index, item in enumerate(priorities_raw[:5], start=1):
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()
        if not title:
            continue
        priority_items.append(
            _focus_priority_item(
                index,
                title,
                str(item.get("status") or "Active").strip() or "Active",
                str(item.get("next_action") or "Review the supporting evidence and decide the next move.").strip(),
                str(item.get("detail_md") or item.get("detail") or "").strip(),
                owner=str(item.get("owner") or "Andy").strip() or "Andy",
            )
        )

    upcoming_raw = payload.get("upcoming") if isinstance(payload.get("upcoming"), list) else []
    upcoming_rows: list[dict] = []
    for item in upcoming_raw[:6]:
        if not isinstance(item, dict):
            continue
        event = str(item.get("event") or "").strip()
        if not event:
            continue
        upcoming_rows.append(
            {
                "when": _focus_trim(str(item.get("when") or "").strip(), 48),
                "event": _focus_trim(event, 100),
                "why": _focus_trim(str(item.get("why") or "").strip(), 150),
            }
        )

    watchlist = [
        _focus_trim(str(item or "").strip(), 160)
        for item in (payload.get("watchlist") or [])
        if str(item or "").strip()
    ][:6] if isinstance(payload.get("watchlist"), list) else []

    blockers_raw = payload.get("blockers") if isinstance(payload.get("blockers"), list) else []
    blockers_rows: list[dict] = []
    for item in blockers_raw[:4]:
        if not isinstance(item, dict):
            continue
        blocker = str(item.get("blocker") or "").strip()
        if not blocker:
            continue
        blockers_rows.append(
            {
                "blocker": _focus_trim(blocker, 80),
                "impact": _focus_trim(str(item.get("impact") or "").strip(), 120),
                "who_can_unblock": _focus_trim(str(item.get("who_can_unblock") or "Andy").strip(), 60),
            }
        )

    sections = []
    if priority_items:
        sections.append({"id": "priorities", "title": "Priorities", "kind": "priority_table", "items": priority_items})
    if upcoming_rows:
        sections.append({"id": "upcoming", "title": "Upcoming", "kind": "table", "columns": ["when", "event", "why"], "items": upcoming_rows})
    if blockers_rows:
        sections.append({"id": "blockers", "title": "Blockers", "kind": "table", "columns": ["blocker", "impact", "who_can_unblock"], "items": blockers_rows})
    if watchlist:
        sections.append({"id": "watchlist", "title": "Watchlist", "kind": "list", "items": watchlist})

    context = _focus_trim(str(payload.get("context") or "").strip(), 420)
    lane = {
        "id": "personal",
        "title": "Personal",
        "subtitle": "Archive-driven personal focus",
        "context": context,
        "available": bool(sections),
        "sourceLabel": "Personal archive synthesis",
        "sourcePath": None,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "sections": sections,
        "sourceFingerprint": str(source_context.get("fingerprint") or ""),
    }
    if not lane["available"]:
        return _build_personal_focus_fallback_lane(source_context)
    return lane


def _build_personal_focus_lane(source_context: dict) -> dict:
    system_prompt = (
        "You generate a personal focus dashboard from concrete evidence. "
        "Return only valid JSON. Use natural language. Prefer obligations, plans, and meaningful themes over mechanisms. "
        "Ignore business, Versant, coding, GitHub, and engineering unless they clearly create personal obligations."
    )
    user_prompt = (
        "Create Andy's PERSONAL focus lane from the evidence below.\n"
        "Rules:\n"
        "- Do not repeat work priorities from the work notes lane.\n"
        "- Focus on household, family, finance/admin, health, travel, upcoming events, and personally meaningful study/research.\n"
        "- Keep priorities actionable and concise.\n"
        "- Return ONLY JSON with this shape:\n"
        "{\n"
        '  "context": string,\n'
        '  "priorities": [{"title": string, "status": string, "next_action": string, "detail_md": string, "owner": string}],\n'
        '  "upcoming": [{"when": string, "event": string, "why": string}],\n'
        '  "watchlist": [string],\n'
        '  "blockers": [{"blocker": string, "impact": string, "who_can_unblock": string}]\n'
        "}\n"
        "Evidence:\n"
        f"{json.dumps(source_context, indent=2)}"
    )
    payload = _focus_call_gateway_json(
        lane_id="personal",
        purpose=f"personal-{str(source_context.get('fingerprint') or '')[:12]}",
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        timeout=120,
    )
    if not payload:
        return _build_personal_focus_fallback_lane(source_context)
    return _normalize_personal_focus_payload(payload, source_context)


def _load_personal_focus_snapshot() -> dict | None:
    try:
        if not _FOCUS_PERSONAL_SNAPSHOT_FILE.is_file():
            return None
        payload = json.loads(_FOCUS_PERSONAL_SNAPSHOT_FILE.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else None
    except Exception:
        return None


def _save_personal_focus_snapshot(payload: dict) -> None:
    _FOCUS_SYNC_ROOT.mkdir(parents=True, exist_ok=True)
    _FOCUS_PERSONAL_SNAPSHOT_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _personal_focus_snapshot_stale(snapshot: dict | None, source_context: dict) -> bool:
    if not snapshot:
        return True
    raw_generated = str(snapshot.get("generatedAt") or "").strip()
    if not raw_generated:
        return True
    try:
        generated_dt = datetime.fromisoformat(raw_generated.replace("Z", "+00:00"))
    except Exception:
        return True
    now_utc = datetime.now(timezone.utc)
    hours_old = (now_utc - generated_dt.astimezone(timezone.utc)).total_seconds() / 3600
    if _focus_archive_mutation_active() and hours_old < 24:
        return False
    if hours_old >= _FOCUS_MAX_AGE_HOURS:
        return True
    fingerprint_changed = str(snapshot.get("sourceFingerprint") or "") != str(source_context.get("fingerprint") or "")
    if not fingerprint_changed:
        return False
    if _focus_archive_mutation_active():
        return False
    now_local = now_utc.astimezone(_focus_sync_tz())
    generated_local = generated_dt.astimezone(_focus_sync_tz())
    if _focus_before_daily_refresh(now_local) and generated_local.date() < now_local.date():
        return False
    return True


def _personal_focus_sync_status(source_context: dict, snapshot: dict | None) -> dict:
    schedule = _focus_schedule_payload()
    raw_generated = str((snapshot or {}).get("generatedAt") or "").strip()
    stale = _personal_focus_snapshot_stale(snapshot, source_context)
    with _FOCUS_PERSONAL_SYNC_LOCK:
        running = bool(_FOCUS_PERSONAL_SYNC_STATE.get("running"))
        message = str(_FOCUS_PERSONAL_SYNC_STATE.get("message") or "").strip()
        started_at = _FOCUS_PERSONAL_SYNC_STATE.get("startedAt")
        finished_at = _FOCUS_PERSONAL_SYNC_STATE.get("finishedAt")
        error = _FOCUS_PERSONAL_SYNC_STATE.get("error")
    return {
        "running": running,
        "message": message,
        "startedAt": started_at,
        "finishedAt": finished_at,
        "lastSuccessfulAt": raw_generated or None,
        "error": error,
        "stale": stale,
        "schedule": schedule,
    }


def _run_personal_focus_sync(*, force: bool = False, reason: str = "manual") -> None:
    with _FOCUS_PERSONAL_SYNC_LOCK:
        _FOCUS_PERSONAL_SYNC_STATE.update(
            {
                "running": True,
                "message": f"Refreshing personal focus ({reason}).",
                "startedAt": datetime.now(timezone.utc).isoformat(),
                "finishedAt": None,
                "error": None,
            }
        )
    try:
        source_context = _focus_personal_source_context()
        existing = _load_personal_focus_snapshot()
        if not force and not _personal_focus_snapshot_stale(existing, source_context):
            with _FOCUS_PERSONAL_SYNC_LOCK:
                _FOCUS_PERSONAL_SYNC_STATE.update(
                    {
                        "running": False,
                        "message": "Personal focus already up to date.",
                        "finishedAt": datetime.now(timezone.utc).isoformat(),
                        "error": None,
                    }
                )
            return

        lane = _build_personal_focus_lane(source_context)
        snapshot = {
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "reason": reason,
            "sourceFingerprint": str(source_context.get("fingerprint") or ""),
            "sourceContext": {
                "today": source_context.get("today"),
                "archiveFingerprint": source_context.get("archiveFingerprint"),
                "lastImportedAt": source_context.get("lastImportedAt"),
                "generatedAt": source_context.get("generatedAt"),
            },
            "lane": lane,
        }
        _save_personal_focus_snapshot(snapshot)
        with _FOCUS_PERSONAL_SYNC_LOCK:
            _FOCUS_PERSONAL_SYNC_STATE.update(
                {
                    "running": False,
                    "message": "Personal focus updated.",
                    "finishedAt": datetime.now(timezone.utc).isoformat(),
                    "error": None,
                }
            )
    except Exception as exc:
        logging.exception("personal focus sync failed")
        with _FOCUS_PERSONAL_SYNC_LOCK:
            _FOCUS_PERSONAL_SYNC_STATE.update(
                {
                    "running": False,
                    "message": "Personal focus sync failed.",
                    "finishedAt": datetime.now(timezone.utc).isoformat(),
                    "error": str(exc),
                }
            )


def _start_personal_focus_sync(*, force: bool = False, reason: str = "manual") -> bool:
    with _FOCUS_PERSONAL_SYNC_LOCK:
        if _FOCUS_PERSONAL_SYNC_STATE.get("running"):
            return False
    worker = threading.Thread(
        target=_run_personal_focus_sync,
        kwargs={"force": force, "reason": reason},
        daemon=True,
        name="focus-personal-sync",
    )
    worker.start()
    return True


def _focus_personal_lane_for_response(source_context: dict) -> dict:
    snapshot = _load_personal_focus_snapshot()
    if _personal_focus_snapshot_stale(snapshot, source_context):
        _start_personal_focus_sync(reason="stale")
    lane = copy.deepcopy((snapshot or {}).get("lane") or {})
    if not isinstance(lane, dict) or not lane:
        lane = _build_personal_focus_fallback_lane(source_context)
    lane.setdefault("id", "personal")
    lane.setdefault("title", "Personal")
    lane.setdefault("subtitle", "Archive-driven personal focus")
    lane.setdefault("sourceLabel", "Personal archive synthesis")
    lane.setdefault("generatedAt", (snapshot or {}).get("generatedAt"))
    return lane


def _focus_overview_response() -> dict:
    work_lane = _focus_apply_manual_priorities(_build_work_focus_lane())
    personal_source_context = _focus_personal_source_context()
    personal_lane = _focus_apply_manual_priorities(_focus_personal_lane_for_response(personal_source_context))
    snapshot = _load_personal_focus_snapshot()
    return {
        "available": bool(work_lane.get("available")) or bool(personal_lane.get("available")),
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "lanes": [work_lane, personal_lane],
        "sync": _personal_focus_sync_status(personal_source_context, snapshot),
    }


def _focus_sync_scheduler_thread() -> None:
    global _FOCUS_SCHEDULE_LAST_TRIGGERED_AT
    logging.info("Focus sync scheduler started (%s %s)", _FOCUS_SYNC_TIME_OF_DAY, _FOCUS_SYNC_TIMEZONE)
    while True:
        try:
            now_local = datetime.now(_focus_sync_tz())
            schedule = _focus_schedule_payload(now_local)
            _focus_schedule_state()
            slot = _focus_scheduled_slot_at_or_before(now_local)
            slot_utc = slot.astimezone(timezone.utc)
            with _FOCUS_SCHEDULE_LOCK:
                last_triggered = _FOCUS_SCHEDULE_LAST_TRIGGERED_AT
                if last_triggered is None or last_triggered < slot_utc:
                    current_utc = datetime.now(timezone.utc)
                    next_run_raw = str(schedule.get("next_run_at") or "").strip()
                    due = False
                    if next_run_raw:
                        try:
                            next_run_utc = datetime.fromisoformat(next_run_raw.replace("Z", "+00:00"))
                            due = next_run_utc.astimezone(timezone.utc) - current_utc <= timedelta(minutes=0)
                        except Exception:
                            due = False
                    if due or slot <= now_local:
                        _FOCUS_SCHEDULE_LAST_TRIGGERED_AT = current_utc
                        _focus_save_schedule_state()
                        _start_personal_focus_sync(force=True, reason="scheduled")
        except Exception:
            logging.exception("focus sync scheduler error")
        time.sleep(30)


def start_focus_sync_scheduler_best_effort() -> None:
    try:
        thread = threading.Thread(target=_focus_sync_scheduler_thread, daemon=True, name="focus-sync-scheduler")
        thread.start()
        _start_personal_focus_sync(reason="startup")
    except Exception:
        logging.exception("Failed to start focus sync scheduler")


# ── Media processing endpoints ─────────────────────────────────────────

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
    enriched = []
    for asset_dict in assets:
        media_id = asset_dict.get("media_id", "")
        result = get_pipeline_result(media_id) if media_id else None
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
    dry_run = request.json.get("dry_run", False) if request.is_json else False
    try:
        result = migrate_pipeline_compat_version(dry_run=dry_run)
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
        oc_sessions = [
            {
                "session_key": session["id"],
                "title": session.get("title") or "Untitled",
                "created_at": session.get("updatedAt"),
                "message_count": session.get("messageCount", 0),
                "source": "openclaw",
                "kind": session.get("kind"),
            }
            for session in load_openclaw_sessions_for_agents(visible_agent_ids())
        ]
        return jsonify({"sessions": sessions, "oc_sessions": oc_sessions})
    except Exception as e:
        return jsonify({"sessions": [], "oc_sessions": [], "error": str(e)}), 200


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

    gateway_token = resolve_gateway_token()
    gateway_url = resolve_gateway_url()
    agent_id = console_agent_id()
    gateway_model = f"openclaw/{agent_id}"

    if not gateway_token:
        return jsonify({"reply": "Chat backend not configured. Set OPENCLAW_GATEWAY_TOKEN."}), 500

    stream = body.get("stream", True)
    session_id = body.get("session_id")
    session_key = body.get("session_key") or (
        f"main:web:{session_id}@{console_agent_id()}" if session_id else default_web_session_key(console_agent_id())
    )
    gateway_session_ref = gateway_session_key(agent_id, session_key)

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
                    f"{gateway_url}/v1/chat/completions",
                    json={
                        "model": gateway_model,
                        "stream": True,
                        "messages": messages_payload,
                        "user": gateway_session_ref,
                    },
                    headers={
                        "Authorization": f"Bearer {gateway_token}",
                        "Content-Type": "application/json",
                        "x-openclaw-agent-id": agent_id,
                        "x-openclaw-scopes": "operator.write",
                        "x-openclaw-session-key": gateway_session_ref,
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
                f"{gateway_url}/v1/chat/completions",
                json={
                    "model": gateway_model,
                    "stream": False,
                    "messages": messages_payload,
                    "user": gateway_session_ref,
                },
                headers={
                    "Authorization": f"Bearer {gateway_token}",
                    "Content-Type": "application/json",
                    "x-openclaw-agent-id": agent_id,
                    "x-openclaw-scopes": "operator.write",
                    "x-openclaw-session-key": gateway_session_ref,
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
            "mcp": {"tools": []},
            "mcp_resources": {"resources": []},
            "recent_tool_calls": [],
            "tasks": tasks,
            "repairs": {"agent_runtime": runtime},
        }
    )


@app.route("/api/focus/overview", methods=["GET"])
def focus_overview():
    try:
        return jsonify(_focus_overview_response())
    except Exception as exc:
        logging.exception("focus overview failed")
        return jsonify({"error": f"Failed to build focus overview: {exc}"}), 500


@app.route("/api/focus/sync", methods=["POST"])
def focus_sync():
    body = request.get_json(force=True, silent=True) or {}
    force = bool(body.get("force"))
    reason = str(body.get("reason") or "manual").strip() or "manual"
    started = _start_personal_focus_sync(force=force, reason=reason)
    source_context = _focus_personal_source_context()
    snapshot = _load_personal_focus_snapshot()
    return jsonify(
        {
            "ok": True,
            "started": started,
            "sync": _personal_focus_sync_status(source_context, snapshot),
        }
    )


@app.route("/api/focus/manual-priorities", methods=["POST"])
def focus_add_manual_priority():
    body = request.get_json(force=True, silent=True) or {}
    lane_id = str(body.get("laneId") or "").strip().lower()
    text = str(body.get("text") or "").strip()
    if lane_id not in {"work", "personal"}:
        return jsonify({"error": "laneId must be 'work' or 'personal'."}), 400
    if not text:
        return jsonify({"error": "text is required."}), 400
    try:
        result = _focus_apply_manual_priority_note(lane_id, text)
        return jsonify({"ok": True, **result})
    except Exception as exc:
        logging.exception("focus manual priority update failed")
        return jsonify({"error": f"Failed to update manual priorities: {exc}"}), 500


@app.route("/api/focus/manual-priorities/<entry_id>", methods=["DELETE"])
def focus_delete_manual_priority(entry_id):
    removed = _delete_focus_manual_priority(entry_id)
    if removed is None:
        return jsonify({"error": "Manual priority not found."}), 404
    return jsonify({"ok": True, "removed": removed})


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
            "gatewayUrl": resolve_gateway_url(),
            "gatewayTokenConfigured": bool(resolve_gateway_token()),
            "workspacePath": host_workspace(),
            "registeredAgents": runtime.get("registered_agents", []),
            "teamAgents": load_team_agents(),
            "runtime": runtime,
        }
    )


@app.route("/api/agents/fleet", methods=["GET"])
def agent_fleet():
    runtime = _agent_runtime_snapshot()
    sessions = load_openclaw_sessions_for_agents(visible_agent_ids())
    verification = _build_focus_priority_verification_snapshot(auto_schedule=False)
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
    verification = _build_focus_priority_verification_snapshot(auto_schedule=True)
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
            "tickets_open": len(list(verification.get("tickets") or [])),
            "tickets": list(verification.get("tickets") or []),
            "openclaw": {
                "available": bool(runtime.get("available")),
                "binary": runtime.get("binary"),
                "model": runtime.get("model"),
                "version": runtime.get("version"),
            },
            "experiments": {"completed": completed, "current": experiments_current},
            "repair_runs": [],
            "verification": {"focus-priorities": verification},
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
    gateway_session_ref = gateway_session_key(agent_id, session_key)
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

    gateway_url = resolve_gateway_url()
    gateway_token = resolve_gateway_token()
    model = f"openclaw/{agent_id}"

    def generate():
        full_text = ""
        yield f"event: session_start\ndata: {json.dumps({'id': session_id})}\n\n"
        if not gateway_token:
            yield f"event: error\ndata: {json.dumps({'message': 'OpenClaw gateway token not configured'})}\n\n"
            yield "event: done\ndata: {}\n\n"
            return
        try:
            response = _requests.post(
                f"{gateway_url}/v1/chat/completions",
                json={
                    "model": model,
                    "stream": True,
                    "messages": [
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": message},
                    ],
                    "user": gateway_session_ref,
                },
                headers={
                    "Authorization": f"Bearer {gateway_token}",
                    "Content-Type": "application/json",
                    "x-openclaw-agent-id": agent_id,
                    "x-openclaw-session-key": gateway_session_ref,
                    "x-openclaw-message-channel": "archivist-console",
                    "x-openclaw-scopes": "operator.write",
                },
                stream=True,
                timeout=180,
            )
            if response.status_code >= 400:
                yield f"event: error\ndata: {json.dumps({'message': f'Gateway returned HTTP {response.status_code}'})}\n\n"
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
        "scopes": ["https://www.googleapis.com/auth/gmail.readonly"],
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


_GOOGLE_JOURNAL_OVERVIEW_VERSION = 21
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


def _google_archive_join_phrases(items: list[str]) -> str:
    clean = [str(item or "").strip() for item in items if str(item or "").strip()]
    if not clean:
        return ""
    if len(clean) == 1:
        return clean[0]
    if len(clean) == 2:
        return f"{clean[0]} and {clean[1]}"
    return f"{', '.join(clean[:-1])}, and {clean[-1]}"


def _google_archive_sentence_join(parts: list[str]) -> str:
    sentences: list[str] = []
    for raw in parts:
        text = re.sub(r"\s+", " ", str(raw or "")).strip()
        if not text:
            continue
        if text[-1] not in ".!?":
            text = f"{text}."
        sentences.append(text)
    return " ".join(sentences)


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


def _google_archive_abstract_topic_text(source: str, raw_text: str) -> str:
    cleaned = _google_archive_clean_topic_text(source, raw_text)
    lowered = cleaned.lower()
    if not cleaned:
        return ""
    if source == "email":
        if re.search(r"\border has been executed\b", lowered):
            return "brokerage order confirmations"
        if any(term in lowered for term in ("limited time", "last chance", "deal alert", "big savings", "promo")):
            return ""
        if any(term in lowered for term in ("opportunity", "candidate", "resume", "interview")) and any(
            term in lowered for term in ("ai", "ml", "data science", "engineer", "architect", "vp", "leader")
        ):
            return "AI and data leadership recruiting conversations"
        if any(term in lowered for term in ("security alert", "security report", "token", "password", "credential")):
            return "account security notices"
        if any(term in lowered for term in ("e-statement", "statement", "invoice", "receipt", "payment")):
            return "financial paperwork and receipts"
    if source == "drive":
        if "paystub" in lowered or "verification of benefits" in lowered:
            return "paystub and benefits paperwork"
        if lowered.startswith("portfolio "):
            return cleaned.replace("portfolio ", "portfolio document: ", 1)
    if source == "calendar" and lowered == "project hail mary":
        return "Project Hail Mary movie outing"
    if source == "media":
        cleaned = re.sub(r"^the recording focuses on\s*", "", cleaned, flags=re.IGNORECASE).strip(" :;,.")
        cleaned = re.sub(r"\brecording_\d{4}-\d{2}-\d{2}[_-]\d{2}-\d{2}-\d{2}\.\w+\b", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" \t\r\n-–—:;,.")
    return _google_archive_trim_text(cleaned, max_chars=180, ellipsis=False)


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


def _google_archive_topic_mentions(candidates: list[dict], *, limit: int = 4, include_low_signal: bool = False) -> list[dict]:
    mentions: list[dict] = []
    deferred_low_signal: list[dict] = []
    seen: set[str] = set()
    for candidate in candidates:
        source = str(candidate.get("source") or "").strip()
        raw_text = str(candidate.get("raw_text") or candidate.get("text") or "").strip()
        cleaned = _google_archive_clean_topic_text(source, raw_text)
        if not cleaned:
            continue
        low_signal = bool(candidate.get("low_signal")) or _google_archive_is_low_signal_topic(source, raw_text, cleaned)
        display_text = _google_archive_abstract_topic_text(source, raw_text)
        if not display_text and include_low_signal:
            display_text = cleaned
        if not display_text:
            continue
        normalized = display_text.lower()
        if normalized in seen:
            continue
        if low_signal and not include_low_signal:
            continue
        target = deferred_low_signal if low_signal else mentions
        target.append(
            {
                "source": source,
                "text": display_text,
                "low_signal": low_signal,
                "weight": float(candidate.get("weight") or 0.0),
            }
        )
        seen.add(normalized)
        if len(mentions) >= limit:
            break
    if include_low_signal and len(mentions) < limit:
        mentions.extend(deferred_low_signal[: max(0, limit - len(mentions))])
    if not mentions and not include_low_signal:
        return _google_archive_topic_mentions(candidates, limit=limit, include_low_signal=True)
    return mentions[:limit]


def _google_archive_candidate_theme_hits(candidate: dict, theme_key: str) -> int:
    if not theme_key:
        return 0
    rule = _GOOGLE_JOURNAL_THEME_INDEX.get(theme_key) or {}
    keywords = rule.get("keywords") or []
    normalized = str(candidate.get("normalized") or "")
    return sum(1 for keyword in keywords if keyword in normalized)


def _google_archive_rank_candidates_for_themes(candidates: list[dict], theme_keys: list[str]) -> list[dict]:
    primary_theme = theme_keys[0] if theme_keys else ""
    secondary_theme = theme_keys[1] if len(theme_keys) > 1 else ""
    return sorted(
        candidates,
        key=lambda candidate: (
            -_google_archive_candidate_theme_hits(candidate, primary_theme),
            -_google_archive_candidate_theme_hits(candidate, secondary_theme),
            -float(candidate.get("weight") or 0.0),
            str(candidate.get("text") or ""),
        ),
    )


def _google_archive_day_context(
    *,
    day: str,
    accounts: list[str],
    email_count: int,
    calendar_count: int,
    drive_count: int,
    chat_count: int,
    git_count: int,
    media_count: int,
    github_count: int,
    email_samples: list[str],
    calendar_samples: list[str],
    drive_samples: list[str],
    chat_samples: list[str],
    git_samples: list[str],
    media_samples: list[str | dict],
    github_samples: list[str],
) -> dict:
    relation = _google_archive_day_relation(day)
    account_phrase = _google_archive_account_phrase(accounts, relation)
    candidates = _google_archive_sample_candidates(
        calendar_samples=calendar_samples,
        email_samples=email_samples,
        drive_samples=drive_samples,
        chat_samples=chat_samples,
        git_samples=git_samples,
        media_samples=media_samples,
        github_samples=github_samples,
    )
    scores = _google_archive_theme_scores(
        candidates,
        email_count=email_count,
        calendar_count=calendar_count,
        drive_count=drive_count,
        chat_count=chat_count,
        git_count=git_count,
        media_count=media_count,
        github_count=github_count,
    )
    theme_keys = _google_archive_pick_day_themes(scores)
    ranked_candidates = _google_archive_rank_candidates_for_themes(candidates, theme_keys)
    primary_theme = _GOOGLE_JOURNAL_THEME_INDEX.get(theme_keys[0], {}) if theme_keys else {}
    secondary_theme = _GOOGLE_JOURNAL_THEME_INDEX.get(theme_keys[1], {}) if len(theme_keys) > 1 else {}
    notable_mentions = _google_archive_topic_mentions(ranked_candidates, limit=4)
    supporting_mentions = _google_archive_topic_mentions(ranked_candidates, limit=6, include_low_signal=True)
    notable_texts = [str(item.get("text") or "").strip() for item in notable_mentions if str(item.get("text") or "").strip()]
    supporting_texts: list[str] = []
    seen_supporting = {text.lower() for text in notable_texts}
    for item in supporting_mentions:
        text = str(item.get("text") or "").strip()
        if not text or text.lower() in seen_supporting:
            continue
        seen_supporting.add(text.lower())
        supporting_texts.append(text)
    routine_calendar_items: list[str] = []
    seen_routine: set[str] = set()
    for sample in calendar_samples:
        if not _google_archive_is_routine_calendar_item(sample):
            continue
        cleaned = _google_archive_clean_topic_text("calendar", sample)
        if not cleaned or cleaned.lower() in seen_routine:
            continue
        seen_routine.add(cleaned.lower())
        routine_calendar_items.append(cleaned)
    document_topics: list[str] = []
    seen_documents: set[str] = set()
    for sample in drive_samples[:4]:
        cleaned = _google_archive_clean_topic_text("drive", sample)
        if not cleaned or cleaned.lower() in seen_documents or cleaned.lower() in seen_supporting:
            continue
        seen_documents.add(cleaned.lower())
        document_topics.append(cleaned)
    return {
        "relation": relation,
        "account_phrase": account_phrase,
        "theme_keys": theme_keys,
        "primary_theme_key": str(primary_theme.get("key") or ""),
        "primary_theme_title": str(primary_theme.get("title") or "").strip(),
        "primary_theme_label": str(primary_theme.get("summary") or "").strip(),
        "secondary_theme_label": str(secondary_theme.get("summary") or "").strip(),
        "notable_topics": notable_texts,
        "supporting_topics": supporting_texts,
        "notable_mentions": notable_mentions,
        "supporting_mentions": supporting_mentions,
        "routine_calendar_items": routine_calendar_items,
        "document_topics": document_topics,
    }


def _google_archive_story_topic_text(value: str | None) -> str:
    text = _google_archive_clean_markdown_text(value)
    if not text:
        return ""
    lowered = text.lower()
    if "colony 7" in lowered and ("colony 5" in lowered or "rescue mission" in lowered):
        return "the Colony 7 quarantine and rescue narrative"
    if "recommendation systems" in lowered and ("misalignment" in lowered or "trust mechanism" in lowered):
        return "AI recommendation-system trust and misalignment questions"
    if any(term in lowered for term in ("chromatic harmony", "coltrane", "johnny hartman", "minor triads")):
        return "music-theory and jazz-practice study"
    if "two-step booking confirmation" in lowered:
        return "two-step booking-confirmation quality work"
    if lowered.startswith("portfolio document:"):
        tail = text.split(":", 1)[1].strip()
        return f"the {tail} portfolio document" if tail else "portfolio document work"
    if "project hail mary" in lowered:
        return "the Project Hail Mary movie outing"
    if "paystub" in lowered and "benefits" in lowered:
        return "paystub and benefits paperwork"
    if "paystub" in lowered:
        return "paystub paperwork"
    if "brokerage order" in lowered:
        return "brokerage order confirmations"
    if "14 days to deploy" in lowered and "inference era" in lowered:
        return "AI deployment reading"
    if lowered.startswith("bank "):
        return f"{text[5:].strip()} banking notices" if text[5:].strip() else "banking notices"
    if "financial paperwork" in lowered or "receipts" in lowered:
        return "financial paperwork and receipts"
    if "account security" in lowered:
        return "account security notices"
    return _google_archive_trim_text(text, max_chars=132, ellipsis=False)


def _google_archive_topic_is_life_or_admin(source: str, text: str) -> bool:
    lowered = text.lower()
    admin_terms = (
        "paystub",
        "benefits",
        "brokerage",
        "financial paperwork",
        "receipt",
        "invoice",
        "statement",
        "payment",
        "bank",
        "credit union",
        "security notice",
        "security alert",
        "password",
        "credential",
        "token",
        "movie outing",
        "doctor",
        "therapy",
        "dentist",
        "appointment",
        "trash",
        "recycle",
        "pickup",
        "grass",
        "delivery",
        "shipped",
        "flight",
        "hotel",
        "travel",
    )
    if any(term in lowered for term in admin_terms):
        return True
    if source == "calendar" and not _google_archive_topic_is_project(source, text):
        return True
    return False


def _google_archive_topic_is_project(source: str, text: str) -> bool:
    lowered = text.lower()
    project_terms = (
        "pr #",
        "pull request",
        "github",
        "commit",
        "quality",
        "booking confirmation",
        "portfolio document",
        "candidate",
        "recruiting",
        "interview",
        "resume",
        "ai and data",
        "leadership",
        "recommendation-system",
        "recommendation system",
        "misalignment",
        "colony",
        "harmony",
        "jazz",
        "practice",
        "research",
        "product",
        "infra",
        "launch planning",
        "sync",
    )
    if source in {"git", "github"}:
        return True
    if source in {"git", "github", "chat"} and "deploy" in lowered:
        return True
    if source == "media":
        return True
    if source == "drive" and "portfolio document" in lowered:
        return True
    return any(term in lowered for term in project_terms)


def _google_archive_topic_is_background(source: str, text: str) -> bool:
    lowered = text.lower()
    if source == "email" and "14 days to deploy" in lowered and "inference era" in lowered:
        return True
    if source == "email" and any(term in lowered for term in ("newsletter", "digest", "webinar", "limited time")):
        return True
    return False


def _google_archive_story_topics_overlap(a: str, b: str) -> bool:
    left = a.lower()
    right = b.lower()
    if left == right:
        return True
    if min(len(left), len(right)) >= 18 and (left in right or right in left):
        return True
    overlap_terms = (
        "paystub",
        "benefits",
        "brokerage",
        "portfolio",
        "project hail mary",
        "credit union",
        "security",
        "financial paperwork",
    )
    return any(term in left and term in right for term in overlap_terms)


def _google_archive_add_story_topic(target: list[str], text: str, seen: set[str]) -> None:
    display = _google_archive_story_topic_text(text)
    key = display.lower()
    if not display or key in seen:
        return
    if any(_google_archive_story_topics_overlap(display, existing) for existing in target):
        return
    seen.add(key)
    target.append(display)


def _google_archive_story_buckets(context: dict) -> dict[str, list[str]]:
    notable_mentions = [item for item in (context.get("notable_mentions") or []) if isinstance(item, dict)]
    supporting_mentions = [item for item in (context.get("supporting_mentions") or []) if isinstance(item, dict)]
    buckets = {"work": [], "life": [], "background": []}
    seen = {"work": set(), "life": set(), "background": set()}
    for item in [*notable_mentions, *supporting_mentions]:
        source = str(item.get("source") or "").strip()
        raw_text = str(item.get("text") or "").strip()
        if not raw_text:
            continue
        if bool(item.get("low_signal")):
            bucket_name = "background"
        elif _google_archive_topic_is_background(source, raw_text):
            bucket_name = "background"
        elif _google_archive_topic_is_life_or_admin(source, raw_text):
            bucket_name = "life"
        elif _google_archive_topic_is_project(source, raw_text):
            bucket_name = "work"
        elif source in {"drive", "chat"}:
            bucket_name = "work"
        else:
            bucket_name = "life"
        _google_archive_add_story_topic(buckets[bucket_name], raw_text, seen[bucket_name])

    for item in (context.get("document_topics") or []):
        text = str(item or "").strip()
        if not text:
            continue
        bucket_name = "life" if _google_archive_topic_is_life_or_admin("drive", text) else "work"
        _google_archive_add_story_topic(buckets[bucket_name], text, seen[bucket_name])

    for item in (context.get("routine_calendar_items") or []):
        _google_archive_add_story_topic(buckets["life"], str(item or ""), seen["life"])
    return buckets


def _google_archive_summary_lead(relation: str, primary: str, fallback_label: str) -> str:
    subject = primary or fallback_label or "current activity"
    if relation == "future":
        return f"The day is shaping up around {subject}"
    if relation == "present":
        return f"Today's clearest thread is {subject}"
    return f"The clearest thread was {subject}"


def _google_archive_day_verb(relation: str, present: str, past: str, future: str | None = None) -> str:
    if relation == "future":
        return future or present
    if relation == "present":
        return present
    return past


def _google_archive_day_story(context: dict, *, max_chars: int = 220) -> str:
    relation = str(context.get("relation") or "past")
    primary_theme_label = str(context.get("primary_theme_label") or "").strip()
    account_phrase = str(context.get("account_phrase") or "").strip()
    buckets = _google_archive_story_buckets(context)
    work_topics = buckets["work"]
    life_topics = buckets["life"]
    background_topics = buckets["background"]
    primary = work_topics[0] if work_topics else (life_topics[0] if life_topics else "")

    sentences = [_google_archive_summary_lead(relation, primary, primary_theme_label)]
    if work_topics:
        rest = work_topics[1:4]
        if rest:
            sentences.append(f"The work and project layer also shows {_google_archive_join_phrases(rest)}.")
    if life_topics:
        life_sentence_topics = life_topics[:3]
        prefix = "Separate life and logistics context"
        if not work_topics:
            life_sentence_topics = life_topics[1:4]
            prefix = "The life and logistics layer also"
        if life_sentence_topics:
            sentences.append(f"{prefix} includes {_google_archive_join_phrases(life_sentence_topics)}.")
    if background_topics and not (work_topics or life_topics):
        sentences.append(f"Background signals include {_google_archive_join_phrases(background_topics[:2])}.")
    if account_phrase:
        sentences.append(f"{account_phrase}.")

    story = _google_archive_sentence_join(sentences)
    if max_chars and max_chars > 0:
        return _google_archive_trim_text(story, max_chars=max_chars, ellipsis=False)
    return story


def _google_archive_day_sections(context: dict) -> list[dict]:
    sections: list[dict] = []
    buckets = _google_archive_story_buckets(context)
    relation = str(context.get("relation") or "past")
    work_topics = buckets["work"]
    life_topics = buckets["life"]
    background_topics = buckets["background"]
    account_phrase = str(context.get("account_phrase") or "").strip()

    what_parts: list[str] = []
    primary_theme_label = str(context.get("primary_theme_label") or "").strip()
    primary = work_topics[0] if work_topics else (life_topics[0] if life_topics else primary_theme_label)
    if primary:
        what_parts.append(f"The main through-line {_google_archive_day_verb(relation, 'is', 'was', 'is')} {primary}.")
    if work_topics and life_topics:
        life_tail = _google_archive_join_phrases(life_topics[:2])
        what_parts.append(
            f"Work and project signals {_google_archive_day_verb(relation, 'are', 'were', 'are')} distinct from the personal logistics around {life_tail}."
        )
    elif work_topics:
        what_parts.append(
            f"Most of the visible signal {_google_archive_day_verb(relation, 'sits', 'sat', 'sits')} in project, research, or creative work."
        )
    elif life_topics:
        what_parts.append(
            f"Most of the visible signal {_google_archive_day_verb(relation, 'sits', 'sat', 'sits')} in personal logistics, paperwork, or scheduled obligations."
        )
    if background_topics and not (work_topics or life_topics):
        what_parts.append(f"Lower-confidence background context includes {_google_archive_join_phrases(background_topics[:2])}.")
    if account_phrase:
        what_parts.append(f"{account_phrase}.")
    if what_parts:
        sections.append({"label": "What happened", "text": _google_archive_sentence_join(what_parts)})

    if work_topics:
        work_sentences = [
            f"On the work and project side, the strongest signal {_google_archive_day_verb(relation, 'is', 'was', 'is')} {work_topics[0]}."
        ]
        if len(work_topics) > 1:
            work_sentences.append(f"Related work includes {_google_archive_join_phrases(work_topics[1:4])}.")
        sections.append({"label": "Work and projects", "text": _google_archive_sentence_join(work_sentences)})

    life_sentences: list[str] = []
    if life_topics:
        life_sentences.append(
            f"The personal logistics layer {_google_archive_day_verb(relation, 'is', 'was', 'is')} {_google_archive_join_phrases(life_topics[:4])}."
        )
    if account_phrase:
        life_sentences.append(f"{account_phrase}.")
    if life_sentences:
        sections.append({"label": "Life and logistics", "text": _google_archive_sentence_join(life_sentences)})
    return sections


def _google_archive_score_clamp(value: float, *, minimum: float = 0.0, maximum: float = 100.0) -> int:
    return int(round(max(minimum, min(maximum, value))))


def _google_archive_score_keyword_hits(text: str, terms: tuple[str, ...]) -> int:
    lowered = text.lower()
    return sum(1 for term in terms if term in lowered)


def _google_archive_day_score(
    context: dict,
    *,
    email_count: int,
    calendar_count: int,
    drive_count: int,
    chat_count: int,
    git_count: int,
    media_count: int,
    github_count: int,
) -> dict:
    total_signals = email_count + calendar_count + drive_count + chat_count + git_count + media_count + github_count
    source_count = sum(1 for count in (email_count, calendar_count, drive_count, chat_count, git_count, media_count, github_count) if count > 0)
    theme_keys = {str(item or "").strip() for item in (context.get("theme_keys") or []) if str(item or "").strip()}
    buckets = _google_archive_story_buckets(context)
    work_topics = buckets.get("work") or []
    life_topics = buckets.get("life") or []
    background_topics = buckets.get("background") or []
    mentions = [item for item in [*(context.get("notable_mentions") or []), *(context.get("supporting_mentions") or [])] if isinstance(item, dict)]
    meaningful_mentions = [item for item in mentions if not item.get("low_signal")]
    meaningful_media = [item for item in meaningful_mentions if str(item.get("source") or "") == "media"]
    meaningful_work = [item for item in meaningful_mentions if str(item.get("source") or "") in {"git", "github", "drive", "chat", "media"}]
    topic_text = " ".join(
        str(item or "")
        for item in [
            *(context.get("notable_topics") or []),
            *(context.get("supporting_topics") or []),
            *(context.get("document_topics") or []),
            *work_topics,
            *life_topics,
            *background_topics,
        ]
    ).lower()

    wonder_hits = _google_archive_score_keyword_hits(
        topic_text,
        (
            "music",
            "jazz",
            "harmony",
            "movie",
            "project hail mary",
            "story",
            "narrative",
            "colony",
            "science",
            "research",
            "photo",
            "picture",
            "learning",
            "travel",
            "creative",
        ),
    )
    sadness_hits = _google_archive_score_keyword_hits(
        topic_text,
        (
            "sad",
            "grief",
            "loss",
            "death",
            "funeral",
            "therapy",
            "doctor",
            "medical",
            "hospital",
            "illness",
            "disease",
            "anxiety",
        ),
    )
    friction_hits = _google_archive_score_keyword_hits(
        topic_text,
        (
            "security",
            "password",
            "credential",
            "token",
            "paystub",
            "benefits",
            "bank",
            "brokerage",
            "invoice",
            "receipt",
            "statement",
            "bill",
            "tax",
            "repair",
            "failure",
            "error",
        ),
    )
    connection_hits = _google_archive_score_keyword_hits(
        topic_text,
        (
            "meeting",
            "sync",
            "interview",
            "recruit",
            "candidate",
            "family",
            "movie outing",
            "follow up",
            "coordination",
            "chat",
        ),
    )
    low_quality_hits = _google_archive_score_keyword_hits(
        topic_text,
        (
            "virtually no activity",
            "minimal activity",
            "undetermined",
            "untranscribed",
            "transcription failing",
            "transcription unavailable",
            "no substantive",
            "single spoken phrase",
            "scene transition",
            "scene transitions",
            "out of extra usage",
            "request rejected",
            "interface turning white",
            "no words were recoverable",
            "speech detections",
        ),
    )
    quality_penalty = min(28, low_quality_hits * 6 + len(background_topics) * 3)

    activity = _google_archive_score_clamp(8 + math.log1p(max(total_signals, 0)) * 9.5 + source_count * 3.5)
    momentum = _google_archive_score_clamp(
        6
        + min(git_count, 8) * 7
        + min(github_count, 8) * 5
        + min(drive_count, 5) * 2.6
        + min(len(meaningful_work), 5) * 4
        + ("engineering" in theme_keys) * 10
        - quality_penalty * 0.45
    )
    wonder = _google_archive_score_clamp(
        5
        + min(len(meaningful_media), 5) * 6
        + wonder_hits * 6.5
        + ("research" in theme_keys) * 8
        - quality_penalty * 0.8
    )
    friction = _google_archive_score_clamp(
        4
        + friction_hits * 8
        + ("finance" in theme_keys) * 10
        + ("security" in theme_keys) * 12
        + min(email_count, 30) * 0.35
        + min(len(life_topics), 5) * 2
    )
    sadness = _google_archive_score_clamp(2 + sadness_hits * 12 + ("health" in theme_keys) * 10 + max(0, friction - 68) * 0.25)
    connection = _google_archive_score_clamp(
        5
        + min(calendar_count, 8) * 5
        + min(chat_count, 6) * 4
        + min(email_count, 18) * 0.7
        + connection_hits * 7
        + ("hiring" in theme_keys) * 10
    )
    intensity = _google_archive_score_clamp(6 + activity * 0.5 + max(momentum, friction, connection, wonder) * 0.28 + source_count * 2)
    importance = _google_archive_score_clamp(
        7
        + momentum * 0.34
        + connection * 0.2
        + wonder * 0.12
        + min(len(work_topics), 5) * 5
        + min(github_count, 8) * 2.4
        + ("planning" in theme_keys) * 5
        + ("hiring" in theme_keys) * 8
        - quality_penalty * 0.35
    )
    excitement = _google_archive_score_clamp(5 + wonder * 0.32 + momentum * 0.24 + connection * 0.16 + intensity * 0.12 - quality_penalty * 0.22)
    overall = _google_archive_score_clamp(
        6
        + activity * 0.12
        + importance * 0.29
        + intensity * 0.18
        + excitement * 0.13
        + connection * 0.09
        + friction * 0.04
        + wonder * 0.08
        + momentum * 0.07
        - quality_penalty * 0.12
    )

    metrics = {
        "activity": activity,
        "importance": importance,
        "intensity": intensity,
        "excitement": excitement,
        "wonder": wonder,
        "sadness": sadness,
        "friction": friction,
        "connection": connection,
        "momentum": momentum,
    }
    dominant_metrics = sorted(metrics.items(), key=lambda item: (-item[1], item[0]))[:3]
    if sadness >= 54 or friction >= 70:
        mood = "Heavy"
    elif connection >= 60:
        mood = "Connected"
    elif wonder >= 62:
        mood = "Wonderful"
    elif excitement >= 58 or momentum >= 75 or importance >= 75:
        mood = "Charged"
    else:
        mood = "Steady"
    if overall >= 72:
        label = "Peak"
    elif overall >= 48:
        label = "Notable"
    elif overall >= 25:
        label = "Steady"
    else:
        label = "Quiet"
    return {
        "overall": overall,
        "rank": 0,
        "percentile": 0,
        "label": label,
        "mood": mood,
        "reasons": [name for name, value in dominant_metrics if value >= 24],
        "metrics": metrics,
    }


def _google_archive_apply_day_score_ranks(days: list[dict]) -> None:
    ranked = sorted(
        [day for day in days if isinstance(day.get("score"), dict)],
        key=lambda item: (-int((item.get("score") or {}).get("overall") or 0), str(item.get("date") or "")),
    )
    total = max(1, len(ranked))
    for index, day in enumerate(ranked, start=1):
        score = day.get("score") or {}
        score["rank"] = index
        score["percentile"] = _google_archive_score_clamp(100 - ((index - 1) / total * 100), minimum=1, maximum=100)
        day["score"] = score


def _google_archive_sample_candidates(
    *,
    calendar_samples: list[str],
    email_samples: list[str],
    drive_samples: list[str],
    chat_samples: list[str],
    git_samples: list[str],
    media_samples: list[str | dict],
    github_samples: list[str],
) -> list[dict]:
    sample_groups = {
        "calendar": calendar_samples,
        "email": email_samples,
        "drive": drive_samples,
        "chat": chat_samples,
        "git": git_samples,
        "media": media_samples,
        "github": github_samples,
    }
    candidates: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for source, samples in sample_groups.items():
        for index, raw_sample in enumerate(samples[:6]):
            text_value = raw_sample
            normalized_text = ""
            extra_weight = 1.0
            explicit_low_signal = False
            if isinstance(raw_sample, dict):
                text_value = raw_sample.get("text") or raw_sample.get("display") or ""
                normalized_text = str(
                    raw_sample.get("normalized")
                    or raw_sample.get("context")
                    or raw_sample.get("theme_text")
                    or text_value
                    or ""
                ).strip()
                try:
                    extra_weight = max(0.2, float(raw_sample.get("weight_multiplier") or 1.0))
                except (TypeError, ValueError):
                    extra_weight = 1.0
                explicit_low_signal = bool(raw_sample.get("low_signal"))
            text = _google_archive_trim_text(str(text_value or "").strip(), max_chars=180, ellipsis=False)
            if not text:
                continue
            key = (source, text.lower())
            if key in seen:
                continue
            seen.add(key)
            routine = source == "calendar" and _google_archive_is_routine_calendar_item(text)
            weight = _GOOGLE_JOURNAL_SOURCE_SAMPLE_WEIGHTS.get(source, 1.0)
            weight *= max(0.45, 1.0 - (index * 0.12))
            weight *= extra_weight
            if routine:
                weight *= 0.22
            if explicit_low_signal:
                weight *= 0.35
            candidates.append(
                {
                    "source": source,
                    "text": text,
                    "raw_text": str(text_value or "").strip(),
                    "normalized": _google_archive_trim_text(normalized_text or text, max_chars=720, ellipsis=False).lower(),
                    "routine": routine,
                    "weight": weight,
                    "low_signal": explicit_low_signal,
                }
            )
    candidates.sort(key=lambda item: (-float(item["weight"]), str(item["text"])))
    return candidates


def _google_archive_theme_scores(
    candidates: list[dict],
    *,
    email_count: int,
    calendar_count: int,
    drive_count: int,
    chat_count: int,
    git_count: int,
    media_count: int,
    github_count: int,
) -> dict[str, float]:
    scores: dict[str, float] = {}
    rich_media_candidates = 0
    for candidate in candidates:
        normalized = str(candidate.get("normalized") or "")
        weight = float(candidate.get("weight") or 0.0)
        source = str(candidate.get("source") or "").strip()
        raw_text = str(candidate.get("raw_text") or candidate.get("text") or "").strip()
        cleaned_text = _google_archive_clean_topic_text(source, raw_text)
        candidate_low_signal = bool(candidate.get("low_signal")) or _google_archive_is_low_signal_topic(source, raw_text, cleaned_text)
        if candidate_low_signal:
            weight *= 0.15
        if source == "media" and not candidate_low_signal and weight >= 2.4:
            rich_media_candidates += 1
            scores["research"] = scores.get("research", 0.0) + weight * 0.75
        if source in {"git", "github"} and not candidate_low_signal and cleaned_text:
            scores["engineering"] = scores.get("engineering", 0.0) + weight * 0.35
        for rule in _GOOGLE_JOURNAL_THEME_RULES:
            hits = sum(1 for keyword in rule["keywords"] if keyword in normalized)
            if hits:
                scores[rule["key"]] = scores.get(rule["key"], 0.0) + weight * (1.0 + ((hits - 1) * 0.35))

    non_routine_calendar = sum(
        1
        for candidate in candidates
        if candidate.get("source") == "calendar" and not candidate.get("routine")
    )
    routine_calendar = sum(
        1
        for candidate in candidates
        if candidate.get("source") == "calendar" and candidate.get("routine")
    )
    if git_count:
        scores["engineering"] = scores.get("engineering", 0.0) + min(8.0, 1.2 + math.log1p(git_count) * 1.45)
    if github_count:
        scores["engineering"] = scores.get("engineering", 0.0) + min(4.5, 0.35 + github_count * 0.35)
    if media_count:
        scores["research"] = scores.get("research", 0.0) + min(7.5, 0.8 + math.log1p(media_count) * 1.7)
    if rich_media_candidates:
        scores["research"] = scores.get("research", 0.0) + min(7.0, rich_media_candidates * 1.15)
    if drive_count:
        scores["finance"] = scores.get("finance", 0.0) + min(5.0, drive_count * 0.65)
    if email_count:
        scores["communications"] = scores.get("communications", 0.0) + min(5.0, math.log1p(email_count) * 0.95)
    if non_routine_calendar:
        scores["planning"] = scores.get("planning", 0.0) + min(6.0, non_routine_calendar * 1.2)
    elif calendar_count:
        scores["household"] = scores.get("household", 0.0) + min(4.0, max(routine_calendar, 1) * 0.9)
    if chat_count:
        scores["communications"] = scores.get("communications", 0.0) + min(4.0, math.log1p(chat_count))
    return scores


def _google_archive_pick_day_themes(scores: dict[str, float]) -> list[str]:
    ranked = sorted(
        ((key, value) for key, value in scores.items() if value > 0),
        key=lambda item: (-item[1], item[0]),
    )
    if not ranked:
        return []
    primary_key, primary_score = ranked[0]
    selected = [primary_key]
    if len(ranked) > 1:
        secondary_key, secondary_score = ranked[1]
        if secondary_key != primary_key and secondary_score >= max(1.8, primary_score * 0.5):
            selected.append(secondary_key)
    return selected


def _google_archive_theme_title(theme_keys: list[str]) -> str:
    if not theme_keys:
        return ""
    primary = _GOOGLE_JOURNAL_THEME_INDEX.get(theme_keys[0], {})
    if len(theme_keys) == 1:
        return str(primary.get("title") or "").strip()
    secondary = _GOOGLE_JOURNAL_THEME_INDEX.get(theme_keys[1], {})
    if primary.get("key") == "engineering" and secondary.get("key") == "research":
        return "Research and engineering"
    if primary.get("key") == "research" and secondary.get("key") in {"planning", "communications"}:
        return "Research and coordination"
    if primary.get("key") == "engineering" and secondary.get("key") in {"planning", "communications"}:
        return "Engineering and coordination"
    if primary.get("key") == "engineering" and secondary.get("key") == "security":
        return "Engineering and ops"
    if primary.get("key") == "finance" and secondary.get("key") == "household":
        return "Paperwork and household"
    if primary.get("key") == "finance" and secondary.get("key") == "communications":
        return "Paperwork and coordination"
    if primary.get("key") == "communications" and secondary.get("key") == "finance":
        return "Inbox and paperwork"
    primary_title = str(primary.get("title") or "").strip()
    secondary_title = str(secondary.get("title") or "").strip()
    secondary_tail = secondary_title.split(" and ", 1)[-1] if " and " in secondary_title else secondary_title.lower()
    if not secondary_tail:
        secondary_tail = secondary_title.lower()
    return f"{primary_title} and {secondary_tail}".strip()


def _google_archive_theme_summary_label(theme_keys: list[str]) -> str:
    if not theme_keys:
        return ""
    primary = _GOOGLE_JOURNAL_THEME_INDEX.get(theme_keys[0], {})
    if len(theme_keys) == 1:
        return str(primary.get("summary") or "").strip()
    secondary = _GOOGLE_JOURNAL_THEME_INDEX.get(theme_keys[1], {})
    secondary_summary = str(secondary.get("summary") or "").strip()
    if primary.get("key") == "engineering" and secondary.get("key") == "research":
        return "research-heavy engineering work"
    if primary.get("key") == "finance" and secondary.get("key") == "household":
        return "paperwork plus household logistics"
    if {primary.get("key"), secondary.get("key")} == {"finance", "communications"}:
        return "paperwork, finance, and inbox follow-up"
    return _google_archive_join_phrases(
        [str(primary.get("summary") or "").strip(), secondary_summary]
    )


def _google_archive_metric_story(
    *,
    relation: str,
    email_count: int,
    calendar_count: int,
    drive_count: int,
    chat_count: int,
    git_count: int,
    media_count: int,
    github_count: int,
) -> str:
    metric_candidates = [
        ("media", _google_archive_count_phrase(media_count, "media item"), media_count * 0.28),
        ("git", _google_archive_count_phrase(git_count, "commit"), git_count * 0.12),
        ("github", _google_archive_count_phrase(github_count, "GitHub event"), github_count * 1.6),
        ("email", _google_archive_count_phrase(email_count, "email"), email_count * 0.22),
        (
            "calendar",
            _google_archive_count_phrase(calendar_count, "scheduled event" if relation == "future" else "event"),
            calendar_count * 1.35,
        ),
        ("drive", _google_archive_count_phrase(drive_count, "Drive file"), drive_count * 1.4),
        ("chat", _google_archive_count_phrase(chat_count, "chat message"), chat_count * 0.2),
    ]
    ranked = [
        phrase
        for _, phrase, score in sorted(metric_candidates, key=lambda item: (-item[2], item[0]))
        if phrase and score > 0
    ][:3]
    return _google_archive_join_phrases(ranked)


def _google_archive_highlights(candidates: list[dict], relation: str, account_phrase: str) -> str:
    picked: list[str] = []
    for candidate in candidates[:3]:
        raw_text = str(candidate.get("text") or "").strip()
        if candidate.get("routine") and re.match(r"^week \d+ of \d{4}$", raw_text, re.IGNORECASE):
            raw_text = "the weekly calendar marker"
        elif candidate.get("routine") and raw_text.lower() == "(untitled event)":
            raw_text = "an untitled calendar hold"
        picked.append(_google_archive_trim_text(raw_text, max_chars=54))
    highlights = [highlight for highlight in picked if highlight]
    if not highlights:
        return account_phrase
    lead = "Key items include" if relation == "future" else "Key threads included"
    sentence = f"{lead} {_google_archive_join_phrases(highlights[:2])}."
    if account_phrase:
        sentence = f"{sentence[:-1]}; {account_phrase.lower()}."
    return sentence


def _google_archive_day_title(
    email_count: int,
    calendar_count: int,
    drive_count: int = 0,
    chat_count: int = 0,
    *,
    git_count: int = 0,
    media_count: int = 0,
    github_count: int = 0,
    email_samples: list[str] | None = None,
    calendar_samples: list[str] | None = None,
    drive_samples: list[str] | None = None,
    chat_samples: list[str] | None = None,
    git_samples: list[str] | None = None,
    media_samples: list[str | dict] | None = None,
    github_samples: list[str] | None = None,
) -> str:
    context = _google_archive_day_context(
        day=datetime.now(_google_display_tz()).date().isoformat(),
        accounts=[],
        email_count=email_count,
        calendar_count=calendar_count,
        drive_count=drive_count,
        chat_count=chat_count,
        git_count=git_count,
        media_count=media_count,
        github_count=github_count,
        email_samples=email_samples or [],
        calendar_samples=calendar_samples or [],
        drive_samples=drive_samples or [],
        chat_samples=chat_samples or [],
        git_samples=git_samples or [],
        media_samples=media_samples or [],
        github_samples=github_samples or [],
    )
    theme_keys = list(context.get("theme_keys") or [])
    title = _google_archive_theme_title(theme_keys)
    if title:
        return title
    if git_count or github_count:
        return "Engineering push"
    if media_count:
        return "Research and ideas"
    if drive_count and email_count:
        return "Paperwork and inbox"
    if calendar_count and email_count:
        return "Calendar and inbox"
    if calendar_count:
        return "Calendar-led day"
    if email_count:
        return "Inbox-led day"
    if drive_count or chat_count:
        return "Workspace activity"
    return "Quiet day"


def _google_archive_day_tone(email_count: int, calendar_count: int, drive_count: int = 0, chat_count: int = 0) -> str:
    if calendar_count >= 6 and email_count >= 20:
        return "Dense commitments"
    if calendar_count >= 6:
        return "Schedule-led"
    if email_count >= 20:
        return "Inbox-led"
    if drive_count >= 10:
        return "Document-led"
    if chat_count >= 20:
        return "Conversation-led"
    if calendar_count or email_count:
        return "Light obligations"
    if drive_count or chat_count:
        return "Workspace-led"
    return "Quiet"


def _google_archive_day_focus(
    email_samples: list[str],
    calendar_samples: list[str],
    drive_samples: list[str] | None = None,
    chat_samples: list[str] | None = None,
    *,
    day: str | None = None,
    accounts: list[str] | None = None,
    email_count: int = 0,
    calendar_count: int = 0,
    drive_count: int = 0,
    chat_count: int = 0,
    git_count: int = 0,
    media_count: int = 0,
    github_count: int = 0,
    git_samples: list[str] | None = None,
    media_samples: list[str | dict] | None = None,
    github_samples: list[str] | None = None,
) -> str:
    context = _google_archive_day_context(
        day=day or datetime.now(_google_display_tz()).date().isoformat(),
        accounts=accounts or [],
        email_count=email_count,
        calendar_count=calendar_count,
        drive_count=drive_count,
        chat_count=chat_count,
        git_count=git_count,
        media_count=media_count,
        github_count=github_count,
        email_samples=email_samples or [],
        calendar_samples=calendar_samples or [],
        drive_samples=drive_samples or [],
        chat_samples=chat_samples or [],
        git_samples=git_samples or [],
        media_samples=media_samples or [],
        github_samples=github_samples or [],
    )
    primary_theme_label = str(context.get("primary_theme_label") or "").strip()
    notable_topics = [str(item or "").strip() for item in (context.get("notable_topics") or []) if str(item or "").strip()]
    if primary_theme_label and notable_topics:
        return _google_archive_trim_text(f"{primary_theme_label.capitalize()} around {notable_topics[0]}", max_chars=96)
    if notable_topics:
        return _google_archive_trim_text(notable_topics[0], max_chars=96)
    if primary_theme_label:
        return _google_archive_trim_text(primary_theme_label.capitalize(), max_chars=96)
    return "Google history import"


def _google_archive_day_movement(
    calendar_locations: list[str],
    email_count: int,
    calendar_count: int,
    drive_count: int = 0,
    chat_count: int = 0,
) -> str:
    if calendar_locations:
        unique_locations = list(dict.fromkeys([location for location in calendar_locations if location]))
        if unique_locations:
            return f"Scheduled across {len(unique_locations)} location(s)"
    if calendar_count:
        return "Calendar-led day"
    if email_count:
        return "Inbox-led day"
    if drive_count:
        return "Document-led day"
    if chat_count:
        return "Conversation-led day"
    return "No Google activity"


def _google_archive_day_note(samples: list[str], fallback: str) -> str:
    picks = [sample for sample in samples if sample][:3]
    if not picks:
        return fallback
    return "; ".join(picks)


def _google_archive_format_record_time(value: str | None) -> str:
    parsed = _google_parse_iso_datetime(value)
    if parsed is None:
        return ""
    local = parsed.astimezone(_google_display_tz())
    text = local.strftime("%b %-d, %-I:%M %p")
    return text.replace("AM", "am").replace("PM", "pm")


def _google_archive_record_kind(source: str, text: str, record: dict | None = None) -> str:
    lowered = str(text or "").lower()
    mime = str((record or {}).get("mime_type") or "").lower()
    if source == "drive" and mime.startswith("image/"):
        return "photo"
    if any(term in lowered for term in ("receipt", "invoice", "order", "payment", "statement", "paystub", "w-2", "tax")):
        return "paperwork"
    if any(term in lowered for term in ("flight", "hotel", "booking", "trip", "travel", "itinerary")):
        return "travel"
    if any(term in lowered for term in ("token", "security", "password", "alert", "credential")):
        return "security"
    if any(term in lowered for term in ("interview", "position", "engineer", "candidate", "resume")):
        return "work"
    if source in {"git", "github"}:
        return "code"
    if source == "media":
        return "media"
    return source


def _google_archive_email_sort_key(record: dict) -> tuple[int, int, str]:
    subject = str(record.get("subject") or "").strip()
    cleaned = _google_archive_clean_topic_text("email", subject)
    kind = _google_archive_record_kind("email", cleaned or subject, record)
    low_signal = _google_archive_is_low_signal_topic("email", subject, cleaned)
    kind_order = {
        "work": 0,
        "paperwork": 1,
        "travel": 2,
        "security": 3,
        "email": 4,
    }.get(kind, 5)
    sender = str(record.get("from") or "").lower()
    automated = 1 if any(token in sender for token in ("noreply", "no-reply", "marketing", "reply.")) else 0
    return (1 if low_signal else 0, kind_order + automated, subject.lower())


def _google_archive_evidence_item(title: str, *, source: str, meta: str = "", detail: str = "", record: dict | None = None) -> dict:
    clean_title = _google_archive_trim_text(title, max_chars=180, ellipsis=False)
    return {
        "title": clean_title,
        "meta": _google_archive_trim_text(meta, max_chars=140, ellipsis=False),
        "detail": _google_archive_trim_text(detail, max_chars=700, ellipsis=False),
        "kind": _google_archive_record_kind(source, clean_title, record),
    }


def _google_archive_day_evidence(
    *,
    email_records: list[dict],
    event_records: list[dict],
    drive_records: list[dict],
    chat_records: list[dict],
    git_commits: list[dict],
    media_items: list[dict],
    github_items: list[dict],
) -> list[dict]:
    groups: list[dict] = []

    def add_group(key: str, count: int, items: list[dict]) -> None:
        clean_items = [item for item in items if item.get("title")]
        if not clean_items:
            return
        groups.append({"key": key, "count": count, "items": clean_items[:5]})

    calendar_items = []
    for record in event_records:
        summary = str(record.get("summary") or "").strip()
        if not summary:
            continue
        when = "all day" if record.get("all_day") else _google_archive_format_record_time(str(record.get("start") or ""))
        location = str(record.get("location") or "").strip()
        detail = f"Location: {location}" if location else ""
        calendar_items.append(_google_archive_evidence_item(summary, source="calendar", meta=when, detail=detail, record=record))
    add_group("calendar", len(event_records), calendar_items)

    email_items = []
    for record in sorted(email_records, key=_google_archive_email_sort_key):
        subject = str(record.get("subject") or "").strip()
        if not subject:
            continue
        if _google_archive_is_low_signal_topic("email", subject, _google_archive_clean_topic_text("email", subject)) and len(email_items) >= 2:
            continue
        sender = str(record.get("from") or "").strip()
        email_items.append(
            _google_archive_evidence_item(
                _google_archive_clean_topic_text("email", subject) or subject,
                source="email",
                meta=_google_archive_format_record_time(str(record.get("date") or "")),
                detail=sender,
                record=record,
            )
        )
    add_group("email", len(email_records), email_items)

    drive_items = []
    for record in drive_records:
        name = str(record.get("name") or "").strip()
        if not name:
            continue
        modified = _google_archive_format_record_time(str(record.get("modified_time") or record.get("created_time") or ""))
        mime = str(record.get("mime_type") or "").strip()
        drive_items.append(_google_archive_evidence_item(name, source="drive", meta=modified, detail=mime, record=record))
    add_group("drive", len(drive_records), drive_items)

    media_evidence = []
    for item in media_items:
        title = str(item.get("subject") or "").strip()
        if not title:
            continue
        source_name = str(item.get("source") or "").strip()
        detail_parts = [part for part in [str(item.get("context") or "").strip(), source_name] if part]
        recorded_time = _google_archive_format_record_time(str(item.get("recorded_time") or ""))
        media_evidence.append(
            _google_archive_evidence_item(
                title,
                source="media",
                meta=recorded_time or str(item.get("day_source") or ""),
                detail=" · ".join(detail_parts),
                record=item,
            )
        )
    add_group("media", len(media_items), media_evidence)

    git_items = [
        _google_archive_evidence_item(
            str(commit.get("subject") or ""),
            source="git",
            meta=str(commit.get("repo") or ""),
            detail=str(commit.get("hash") or ""),
            record=commit,
        )
        for commit in git_commits
    ]
    add_group("git", len(git_commits), git_items)

    github_evidence = [
        _google_archive_evidence_item(
            str(item.get("title") or ""),
            source="github",
            meta=str(item.get("repo") or ""),
            detail=str(item.get("type") or ""),
            record=item,
        )
        for item in github_items
    ]
    add_group("github", len(github_items), github_evidence)

    chat_items = [
        _google_archive_evidence_item(
            str(item.get("text") or ""),
            source="chat",
            meta=str(item.get("space_display_name") or item.get("space_name") or ""),
            detail=str(item.get("sender") or ""),
            record=item,
        )
        for item in chat_records
    ]
    add_group("chat", len(chat_records), chat_items)
    group_order = {"git": 0, "github": 1, "media": 2, "calendar": 3, "drive": 4, "email": 5, "chat": 6}
    groups.sort(key=lambda group: group_order.get(str(group.get("key") or ""), 99))
    return groups


def _google_archive_day_relation(day: str) -> str:
    try:
        target_day = datetime.fromisoformat(f"{day}T00:00:00").date()
    except Exception:
        return "past"
    today = datetime.now(_google_display_tz()).date()
    if target_day > today:
        return "future"
    if target_day < today:
        return "past"
    return "present"


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


def _google_archive_count_phrase(count: int, singular: str, plural: str | None = None, *, prefix: str | None = None) -> str:
    if count <= 0:
        return ""
    noun = singular if count == 1 else (plural or f"{singular}s")
    clean_prefix = str(prefix or "").strip()
    if clean_prefix:
        return f"{count} {clean_prefix} {noun}"
    return f"{count} {noun}"


def _google_archive_account_phrase(accounts: list[str], relation: str) -> str:
    account_count = len([account for account in accounts if str(account).strip()])
    if account_count <= 1:
        return ""
    if account_count == 2:
        return "Both accounts scheduled" if relation == "future" else "Both accounts active"
    return f"{account_count} accounts scheduled" if relation == "future" else f"{account_count} accounts active"


def _google_archive_day_summary(
    *,
    day: str,
    accounts: list[str],
    email_count: int,
    calendar_count: int,
    drive_count: int,
    chat_count: int,
    git_count: int,
    media_count: int,
    github_count: int,
    email_samples: list[str],
    calendar_samples: list[str],
    drive_samples: list[str],
    chat_samples: list[str],
    git_samples: list[str],
    media_samples: list[str | dict],
    github_samples: list[str],
) -> str:
    context = _google_archive_day_context(
        day=day,
        accounts=accounts,
        email_count=email_count,
        calendar_count=calendar_count,
        drive_count=drive_count,
        chat_count=chat_count,
        git_count=git_count,
        media_count=media_count,
        github_count=github_count,
        email_samples=email_samples,
        calendar_samples=calendar_samples,
        drive_samples=drive_samples,
        chat_samples=chat_samples,
        git_samples=git_samples,
        media_samples=media_samples,
        github_samples=github_samples,
    )
    return _google_archive_day_story(context, max_chars=0)


# ---------------------------------------------------------------------------
# Git activity collector for journal enrichment
# ---------------------------------------------------------------------------

_ARCHIVIST_GIT_REPO_DIRS = [
    p.strip() for p in os.getenv("ARCHIVIST_GIT_REPO_DIRS", "").split(":") if p.strip()
]


def _collect_git_activity_for_days() -> dict[str, list[dict]]:
    """Collect git commits grouped by day across configured repos."""
    activity: dict[str, list[dict]] = {}
    for repo_dir in _ARCHIVIST_GIT_REPO_DIRS:
        repo_path = Path(repo_dir)
        if not (repo_path / ".git").exists():
            continue
        repo_name = repo_path.name
        try:
            result = subprocess.run(
                ["git", "-c", f"safe.directory={repo_path}", "-C", str(repo_path),
                 "log", "--all",
                 "--pretty=format:%H|%s|%an|%aI"],
                capture_output=True, text=True, timeout=60,
            )
            if result.returncode != 0:
                continue
            for line in result.stdout.strip().split("\n"):
                if not line.strip():
                    continue
                parts = line.split("|", 3)
                if len(parts) < 4:
                    continue
                commit_hash, subject, author, date_iso = parts
                try:
                    dt = datetime.fromisoformat(date_iso)
                    day = dt.astimezone(_google_display_tz()).date().isoformat()
                except Exception:
                    continue
                activity.setdefault(day, []).append({
                    "repo": repo_name,
                    "hash": commit_hash[:8],
                    "subject": subject.strip(),
                    "author": author.strip(),
                })
        except Exception:
            continue
    return activity


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


def _collect_media_activity_for_days() -> dict[str, list[dict]]:
    """Collect media pipeline completions grouped by day."""
    from media.pipeline import PIPELINE_STORE_DIR
    activity: dict[str, list[dict]] = {}
    if not PIPELINE_STORE_DIR.is_dir():
        return activity
    for result_file in PIPELINE_STORE_DIR.glob("*.json"):
        try:
            data = json.loads(result_file.read_text(encoding="utf-8"))
            stamp = data.get("archivist_pipeline")
            if stamp is not None and not isinstance(stamp, dict):
                continue
            day, day_source = _media_result_day(data, result_file)
            if not day:
                continue
            activity.setdefault(day, []).append(_media_result_journal_item(data, result_file, day_source))
        except Exception:
            continue
    return activity


_journal_overview_cache: dict | None = None
_journal_overview_cache_time: float = 0.0
_journal_overview_building: bool = False
_journal_overview_cache_fingerprint: str | None = None


def _build_google_journal_overview() -> dict:
    global _journal_overview_cache, _journal_overview_cache_time, _journal_overview_building, _journal_overview_cache_fingerprint
    import time as _time
    now = _time.monotonic()
    current_fingerprint = _google_archive_fingerprint()
    persisted = _load_persisted_google_journal_overview()
    # Return cached result if fresh (within 120s)
    if (
        _journal_overview_cache is not None
        and (now - _journal_overview_cache_time) < 120
        and _journal_overview_cache_fingerprint == current_fingerprint
    ):
        cached_days = int(_journal_overview_cache.get("dayCount") or 0)
        persisted_days = int((persisted or {}).get("dayCount") or 0)
        if persisted is not None and persisted_days > cached_days:
            _journal_overview_cache = persisted
            _journal_overview_cache_time = _time.monotonic()
            _journal_overview_cache_fingerprint = str(persisted.get("archiveFingerprint") or current_fingerprint)
            return persisted
        return _journal_overview_cache
    # If another thread is already building, return stale cache or empty
    if _journal_overview_building:
        if persisted is not None:
            return persisted
        if _journal_overview_cache is not None:
            return _journal_overview_cache
        return {"available": False, "days": [], "sources": [], "dayCount": 0,
                "accountCount": 0, "gmailMessages": 0, "calendarEvents": 0, "driveFiles": 0, "chatMessages": 0}
    _journal_overview_building = True
    try:
        result = _build_google_journal_overview_uncached()
        _journal_overview_cache = result
        _journal_overview_cache_time = _time.monotonic()
        _journal_overview_cache_fingerprint = str(result.get("archiveFingerprint") or current_fingerprint)
        return result
    finally:
        _journal_overview_building = False


def _build_google_journal_overview_uncached() -> dict:
    persisted = _load_persisted_google_journal_overview()
    if persisted is not None:
        return persisted

    root = _google_archive_root()
    day_buckets: dict[str, dict] = {}
    account_manifests: list[dict] = []

    for account_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        manifest_path = account_dir / "manifest.json"
        if manifest_path.is_file():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                if isinstance(manifest, dict):
                    account_manifests.append(manifest)
            except Exception:
                pass
        for record in _jsonl_read(account_dir / "gmail_messages.jsonl"):
            day = str(record.get("day") or "").strip()
            if not day:
                continue
            bucket = day_buckets.setdefault(day, {"emails": [], "events": [], "drive_files": [], "chat_messages": [], "accounts": set(), "locations": []})
            bucket["emails"].append(record)
            bucket["accounts"].add(str(record.get("account") or "").strip())
        for record in _jsonl_read(account_dir / "calendar_events.jsonl"):
            day = str(record.get("day") or "").strip()
            if not day:
                continue
            bucket = day_buckets.setdefault(day, {"emails": [], "events": [], "drive_files": [], "chat_messages": [], "accounts": set(), "locations": []})
            bucket["events"].append(record)
            bucket["accounts"].add(str(record.get("account") or "").strip())
            location = str(record.get("location") or "").strip()
            if location:
                bucket["locations"].append(location)
        for record in _jsonl_read(account_dir / "drive_files.jsonl"):
            day = str(record.get("day") or "").strip()
            if not day:
                continue
            bucket = day_buckets.setdefault(day, {"emails": [], "events": [], "drive_files": [], "chat_messages": [], "accounts": set(), "locations": []})
            bucket["drive_files"].append(record)
            bucket["accounts"].add(str(record.get("account") or "").strip())
        for record in _jsonl_read(account_dir / "chat_messages.jsonl"):
            day = str(record.get("day") or "").strip()
            if not day:
                continue
            bucket = day_buckets.setdefault(day, {"emails": [], "events": [], "drive_files": [], "chat_messages": [], "accounts": set(), "locations": []})
            bucket["chat_messages"].append(record)
            bucket["accounts"].add(str(record.get("account") or "").strip())

    # Enrich with git activity across configured repos.
    try:
        git_activity = _collect_git_activity_for_days()
        for day, commits in git_activity.items():
            bucket = day_buckets.setdefault(day, {"emails": [], "events": [], "drive_files": [], "chat_messages": [], "accounts": set(), "locations": []})
            bucket.setdefault("git_commits", []).extend(commits)
    except Exception:
        logging.exception("failed to collect git activity for journal")

    # Enrich with media pipeline completions.
    try:
        media_activity = _collect_media_activity_for_days()
        for day, items in media_activity.items():
            bucket = day_buckets.setdefault(day, {"emails": [], "events": [], "drive_files": [], "chat_messages": [], "accounts": set(), "locations": []})
            bucket.setdefault("media_processed", []).extend(items)
    except Exception:
        logging.exception("failed to collect media activity for journal")

    # Enrich with GitHub activity (PRs, issues, reviews).
    try:
        from github_service import collect_github_activity_for_days
        github_activity = collect_github_activity_for_days()
        for day, items in github_activity.items():
            bucket = day_buckets.setdefault(day, {"emails": [], "events": [], "drive_files": [], "chat_messages": [], "accounts": set(), "locations": []})
            bucket.setdefault("github_activity", []).extend(items)
    except Exception:
        logging.exception("failed to collect GitHub activity for journal")

    days: list[dict] = []
    for day in sorted(day_buckets.keys(), reverse=True):
        bucket = day_buckets[day]
        email_records = bucket["emails"]
        event_records = bucket["events"]
        drive_records = bucket["drive_files"]
        chat_records = bucket["chat_messages"]
        git_commits = bucket.get("git_commits", [])
        media_items = bucket.get("media_processed", [])
        email_count = len(email_records)
        calendar_count = len(event_records)
        drive_count = len(drive_records)
        chat_count = len(chat_records)
        git_count = len(git_commits)
        media_count = len(media_items)
        github_items = bucket.get("github_activity", [])
        github_count = len(github_items)
        email_samples = [
            str(item.get("subject") or "").strip()
            for item in sorted(email_records, key=_google_archive_email_sort_key)
            if str(item.get("subject") or "").strip()
        ]
        calendar_samples = [str(item.get("summary") or "").strip() for item in event_records if str(item.get("summary") or "").strip()]
        drive_samples = [str(item.get("name") or "").strip() for item in drive_records if str(item.get("name") or "").strip()]
        chat_samples = [str(item.get("text") or "").strip() for item in chat_records if str(item.get("text") or "").strip()]
        git_samples = [str(item.get("subject") or "").strip() for item in git_commits if str(item.get("subject") or "").strip()]
        media_note_samples = [str(item.get("subject") or "").strip() for item in media_items if str(item.get("subject") or "").strip()]
        media_samples: list[dict] = []
        for item in media_items:
            subject = str(item.get("subject") or "").strip()
            context = str(item.get("context") or "").strip()
            theme_text = str(item.get("theme_text") or context or subject).strip()
            if not subject:
                continue
            media_samples.append(
                {
                    "text": subject,
                    "normalized": theme_text,
                    "weight_multiplier": item.get("weight_multiplier"),
                    "low_signal": item.get("low_signal"),
                }
            )
        github_samples = [str(item.get("title") or "").strip() for item in github_items if str(item.get("title") or "").strip()]
        accounts = sorted(account for account in bucket["accounts"] if account)
        sources = []
        day_context = _google_archive_day_context(
            day=day,
            accounts=accounts,
            email_count=email_count,
            calendar_count=calendar_count,
            drive_count=drive_count,
            chat_count=chat_count,
            git_count=git_count,
            media_count=media_count,
            github_count=github_count,
            email_samples=email_samples,
            calendar_samples=calendar_samples,
            drive_samples=drive_samples,
            chat_samples=chat_samples,
            git_samples=git_samples,
            media_samples=media_samples,
            github_samples=github_samples,
        )
        sections = _google_archive_day_sections(day_context)
        signals = []
        if calendar_count:
            sources.append("calendar")
            signals.append(
                {
                    "key": "calendar",
                    "count": f"{calendar_count} event(s)",
                    "note": _google_archive_day_note(calendar_samples, "Scheduled commitments were captured for this day."),
                }
            )
        if email_count:
            sources.append("email")
            signals.append(
                {
                    "key": "email",
                    "count": f"{email_count} message(s)",
                    "note": _google_archive_day_note(email_samples, "Inbox traffic is visible for this day."),
                }
            )
        if drive_count:
            sources.append("drive")
            signals.append(
                {
                    "key": "drive",
                    "count": f"{drive_count} file(s)",
                    "note": _google_archive_day_note(drive_samples, "Drive activity is visible for this day."),
                }
            )
        if chat_count:
            sources.append("chat")
            signals.append(
                {
                    "key": "chat",
                    "count": f"{chat_count} message(s)",
                    "note": _google_archive_day_note(chat_samples, "Chat traffic is visible for this day."),
                }
            )
        if git_count:
            sources.append("git")
            repos: dict[str, list[str]] = {}
            for commit in git_commits:
                repos.setdefault(commit.get("repo", "?"), []).append(commit.get("subject", ""))
            repo_summaries = [f"{repo} ({len(msgs)} commit{'s' if len(msgs) != 1 else ''})" for repo, msgs in repos.items()]
            signals.append(
                {
                    "key": "git",
                    "count": f"{git_count} commit(s)",
                    "note": f"Activity in {', '.join(repo_summaries[:3])}",
                }
            )
        if media_count:
            sources.append("media")
            media_subjects = [m.get("subject", "") for m in media_items[:5] if m.get("subject")]
            signals.append(
                {
                    "key": "media",
                    "count": f"{media_count} file(s)",
                    "note": _google_archive_day_note(media_note_samples or media_subjects, "Media processing activity"),
                }
            )
        if github_count:
            sources.append("github")
            by_type: dict[str, list[dict]] = {}
            for gh_item in github_items:
                by_type.setdefault(gh_item.get("type", "other"), []).append(gh_item)
            type_summaries = [f"{len(tlist)} {tname}" for tname, tlist in by_type.items()]
            signals.append(
                {
                    "key": "github",
                    "count": f"{github_count} event(s)",
                    "note": ", ".join(type_summaries[:3]),
                }
            )
        total_signals = email_count + calendar_count + drive_count + chat_count + git_count + media_count + github_count
        day_score = _google_archive_day_score(
            day_context,
            email_count=email_count,
            calendar_count=calendar_count,
            drive_count=drive_count,
            chat_count=chat_count,
            git_count=git_count,
            media_count=media_count,
            github_count=github_count,
        )
        days.append(
            {
                "id": day,
                "date": day,
                "title": _google_archive_day_title(
                    email_count,
                    calendar_count,
                    drive_count,
                    chat_count,
                    git_count=git_count,
                    media_count=media_count,
                    github_count=github_count,
                    email_samples=email_samples,
                    calendar_samples=calendar_samples,
                    drive_samples=drive_samples,
                    chat_samples=chat_samples,
                    git_samples=git_samples,
                    media_samples=media_samples,
                    github_samples=github_samples,
                ),
                "summary": _google_archive_day_summary(
                    day=day,
                    accounts=accounts,
                    email_count=email_count,
                    calendar_count=calendar_count,
                    drive_count=drive_count,
                    chat_count=chat_count,
                    git_count=git_count,
                    media_count=media_count,
                    github_count=github_count,
                    email_samples=email_samples,
                    calendar_samples=calendar_samples,
                    drive_samples=drive_samples,
                    chat_samples=chat_samples,
                    git_samples=git_samples,
                    media_samples=media_samples,
                    github_samples=github_samples,
                ),
                "tone": _google_archive_day_tone(email_count, calendar_count, drive_count, chat_count),
                "focus": _google_archive_day_focus(
                    email_samples,
                    calendar_samples,
                    drive_samples,
                    chat_samples,
                    day=day,
                    accounts=accounts,
                    email_count=email_count,
                    calendar_count=calendar_count,
                    drive_count=drive_count,
                    chat_count=chat_count,
                    git_count=git_count,
                    media_count=media_count,
                    github_count=github_count,
                    git_samples=git_samples,
                    media_samples=media_samples,
                    github_samples=github_samples,
                ),
                "movement": _google_archive_day_movement(bucket["locations"], email_count, calendar_count, drive_count, chat_count),
                "signalCount": total_signals,
                "sources": sources,
                "sections": sections,
                "signals": signals,
                "score": day_score,
                "evidence": _google_archive_day_evidence(
                    email_records=email_records,
                    event_records=event_records,
                    drive_records=drive_records,
                    chat_records=chat_records,
                    git_commits=git_commits,
                    media_items=media_items,
                    github_items=github_items,
                ),
                "closing": (
                    "This day is grounded in imported history and local activity."
                    if total_signals
                    else "No records landed on this day."
                ),
            }
        )

    _google_archive_apply_day_score_ranks(days)

    latest_import = None
    gmail_total = 0
    calendar_total = 0
    drive_total = 0
    chat_total = 0
    for manifest in account_manifests:
        gmail_total += int(manifest.get("gmailMessages") or 0)
        calendar_total += int(manifest.get("calendarEvents") or 0)
        drive_total += int(manifest.get("driveFiles") or 0)
        chat_total += int(manifest.get("chatMessages") or 0)
        imported_at = str(manifest.get("imported_at") or "").strip()
        if imported_at and (latest_import is None or imported_at > latest_import):
            latest_import = imported_at

    result = {
        "available": bool(days),
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "accountCount": len(account_manifests),
        "gmailMessages": gmail_total,
        "calendarEvents": calendar_total,
        "driveFiles": drive_total,
        "chatMessages": chat_total,
        "dayCount": len(days),
        "days": days,
        "sources": list(_GOOGLE_JOURNAL_SOURCES),
        "mode": "live" if days else "empty",
        "lastImportedAt": latest_import,
        "journalVersion": _GOOGLE_JOURNAL_OVERVIEW_VERSION,
        "archiveFingerprint": _google_archive_fingerprint(),
    }
    try:
        _google_archive_journal_path().write_text(json.dumps(result, indent=2), encoding="utf-8")
    except Exception:
        logging.debug("failed to persist journal overview cache", exc_info=True)
    return result


def _persist_google_archive_views() -> dict:
    overview = _build_google_journal_overview()
    summary = {
        "available": bool(overview.get("available")),
        "accountCount": int(overview.get("accountCount") or 0),
        "gmailMessages": int(overview.get("gmailMessages") or 0),
        "calendarEvents": int(overview.get("calendarEvents") or 0),
        "driveFiles": int(overview.get("driveFiles") or 0),
        "chatMessages": int(overview.get("chatMessages") or 0),
        "dayCount": int(overview.get("dayCount") or 0),
        "lastImportedAt": overview.get("lastImportedAt"),
    }
    _google_archive_summary_path().write_text(json.dumps(summary, indent=2), encoding="utf-8")
    _google_archive_journal_path().write_text(json.dumps(overview, indent=2), encoding="utf-8")
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


@app.route("/api/journal/overview", methods=["GET"])
def api_journal_overview():
    payload = _build_google_journal_overview()
    payload["import"] = _google_import_status_public()
    payload["archive"] = _google_archive_summary()

    # Staleness indicator so the UI can warn when imports are overdue.
    last_imported = str(payload.get("lastImportedAt") or "").strip()
    if last_imported:
        try:
            imported_dt = datetime.fromisoformat(last_imported)
            stale_hours = (datetime.now(timezone.utc) - imported_dt).total_seconds() / 3600
            payload["stale"] = stale_hours > 4
            payload["stale_hours"] = round(stale_hours, 1)
        except Exception:
            payload["stale"] = True
            payload["stale_hours"] = None
    else:
        payload["stale"] = True
        payload["stale_hours"] = None

    # Optional month filter: ?month=2026-04 returns only days in that month.
    # Without a month param, return only the most recent 60 days to keep the response small.
    month_param = request.args.get("month", "").strip()
    if month_param and payload.get("days"):
        prefix = month_param  # e.g. "2026-04"
        filtered = [d for d in payload["days"] if d["date"].startswith(prefix)]
        payload = {**payload, "days": filtered, "filteredDayCount": len(filtered)}
    elif payload.get("days"):
        payload = {**payload, "days": payload["days"][:60], "filteredDayCount": min(60, len(payload["days"]))}

    return jsonify(payload)


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
def _prewarm_journal_cache():
    import time as _time
    _time.sleep(5)  # let gunicorn finish binding
    try:
        logging.info("Pre-warming journal cache...")
        _build_google_journal_overview()
        logging.info("Journal cache ready (%d days)", _journal_overview_cache.get("dayCount", 0) if _journal_overview_cache else 0)
    except Exception:
        logging.exception("Journal cache pre-warm failed (non-fatal)")


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


if _WEB_BACKGROUND_TASKS_ENABLED:
    # Start Google import scheduler (deferred to here since the function is defined above).
    try:
        start_google_import_scheduler_best_effort()
    except Exception:
        logging.exception("Google import scheduler startup failed")

    try:
        start_focus_sync_scheduler_best_effort()
    except Exception:
        logging.exception("Focus sync scheduler startup failed")

    threading.Thread(target=_prewarm_journal_cache, daemon=True, name="journal-cache-warm").start()
    threading.Thread(target=_periodic_github_sync, daemon=True, name="github-periodic-sync").start()
else:
    logging.info(
        "Archivist web background tasks disabled: skipping Google import scheduler, focus sync scheduler, journal prewarm, and periodic GitHub sync"
    )


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5050)
