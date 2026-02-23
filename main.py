# main.py
from flask import Flask, request, jsonify, send_from_directory
from load import load_to_vectorstore, load_text_to_vectorstore, clear_vectorstore_collection
from search import search_vectorstore
import argparse
import logging
import traceback
from pymilvus import connections, utility, Collection, DataType
from uuid import uuid4
import os
from werkzeug.exceptions import HTTPException

from backups_service import (
    BACKUP_ROOT,
    add_backup_target,
    delete_backup_target,
    get_backup_overview,
    get_run_logs,
    list_backup_targets,
    start_backup,
    start_scheduler_best_effort,
    stop_backup,
    update_backup_target,
    update_schedule,
)

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
        "nprobe": _as_int(payload.get("nprobe")),
        "hybrid_fusion": payload.get("hybrid_fusion"),
        "hybrid_dense_weight": _as_float(payload.get("hybrid_dense_weight")),
        "hybrid_sparse_weight": _as_float(payload.get("hybrid_sparse_weight")),
        "hybrid_rrf_k": _as_int(payload.get("hybrid_rrf_k")),
    }

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
    raw_name = name if name.startswith("documents_") else f"documents_{name}"
    alias = _milvus_alias("collection")
    try:
        _milvus_connect(alias)
        if not utility.has_collection(raw_name, using=alias):
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

    merged.sort(key=lambda item: item.get("distance", float("inf")))
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
    result = load_text_to_vectorstore(
        text,
        collection_name=name,
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
    raw_name = name if name.startswith("documents_") else f"documents_{name}"
    alias = _milvus_alias("drop")
    try:
        _milvus_connect(alias)
        if not utility.has_collection(raw_name, using=alias):
            return jsonify({"message": "Already absent", "raw_name": raw_name}), 200
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
        return jsonify({"error": str(e)}), 409

@app.route("/api/backups/stop", methods=["POST"])
def api_backup_stop():
    try:
        return jsonify(stop_backup())
    except Exception as e:
        return jsonify({"error": str(e)}), 409

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

@app.route("/api/backups/files/<name>", methods=["GET"])
def api_backup_file(name: str):
    # Only allow serving files from backup root.
    return send_from_directory(str(BACKUP_ROOT), name, as_attachment=True)

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
                        collection_name_formatted = f"documents_{collection_name}" if collection_name else "documents_local_model"
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
                "error": "An unexpected error occurred",
                "details": str(e),
                "traceback": traceback.format_exc() if data.get('debug', False) else None
            }), 500

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

# UI static serving (built by Dockerfile into ./ui_dist).
UI_DIST_DIR = os.path.join(os.path.dirname(__file__), "ui_dist")
if os.path.isdir(UI_DIST_DIR):
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def _ui_static(path: str):
        candidate = os.path.join(UI_DIST_DIR, path)
        if path and os.path.isfile(candidate):
            return send_from_directory(UI_DIST_DIR, path)
        return send_from_directory(UI_DIST_DIR, "index.html")

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
