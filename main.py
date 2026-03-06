# main.py
from flask import Flask, request, jsonify, send_from_directory
from load import load_to_vectorstore, load_text_to_vectorstore, clear_vectorstore_collection
from search import search_vectorstore
import argparse
import logging
import traceback
import math
import time
try:
    import numpy as np
except Exception:
    np = None
from pymilvus import connections, utility, Collection, DataType
from uuid import uuid4
import os
from werkzeug.exceptions import HTTPException
from utils import LOCAL_EMBEDDING_MODEL, embed_text_to_vector, validate_embeddings

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
    add_indexing_target,
    delete_indexing_target,
    get_indexing_overview,
    get_indexing_run_logs,
    list_indexing_targets,
    scan_indexing_target,
    start_indexing,
    start_target_indexing,
    stop_indexing,
    update_indexing_target,
)
from movietime_items import search_movietime_items, upsert_movietime_items

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

# Start backup scheduler once (best-effort; uses a file lock).
start_scheduler_best_effort()

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
EMBEDDING_HOST = os.environ.get('EMBEDDING_HOST', 'localhost')
EMBEDDING_PORT = int(os.environ.get('EMBEDDING_PORT', '8000'))

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"}), 200

def _milvus_alias(prefix: str = "api") -> str:
    return f"{prefix}_{uuid4().hex}"

def _milvus_connect(alias: str, host: str | None = None) -> None:
    connections.connect(alias, host=host or MILVUS_HOST, port="19530")

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
            if utility.has_collection(candidate, using=alias):
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
    include_stats = str(request.args.get("include_stats", "true")).strip().lower() in {"1", "true", "yes"}
    alias = _milvus_alias("collections")
    try:
        _milvus_connect(alias)
        names = utility.list_collections(using=alias)
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
    ip_address = payload.get("ip_address", MILVUS_HOST)
    embedding_host = payload.get("embedding_host", EMBEDDING_HOST)
    embedding_port = payload.get("embedding_port", EMBEDDING_PORT)
    search_options = _build_search_options(payload)

    alias = _milvus_alias("global_search")
    merged = []
    try:
        _milvus_connect(alias, host=ip_address)
        collection_names = utility.list_collections(using=alias)
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
            connections.connect("default", host=ip_address, port='19530')
            status = connections.get_connection_addr("default")
            is_connected = connections.has_connection("default")
            
            # Get list of collections to verify Milvus is operational
            collections = []
            if is_connected:
                collections = utility.list_collections()
            
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
                        connections.connect(debug_alias, host=ip_address, port='19530')
                        default_collection_suffix = LOCAL_EMBEDDING_MODEL.replace("-", "_")
                        collection_name_formatted = (
                            f"documents_{collection_name}" if collection_name else f"documents_{default_collection_suffix}"
                        )
                        collection_exists = utility.has_collection(collection_name_formatted, using=debug_alias)
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5050)
