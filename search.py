# search.py
import os
import sys
import re
import logging
from collections import Counter
from pathlib import Path
from datetime import datetime
from pymilvus import connections, Collection, utility, AnnSearchRequest, WeightedRanker, RRFRanker
import traceback
from uuid import uuid4

from utils import (
    DEFAULT_EMBEDDING_MODEL, EMBEDDING_DIMENSIONS, LOCAL_EMBEDDING_MODEL, LOCAL_EMBEDDING_DIM,
    embed_text_to_vector, validate_embeddings
)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Constants Configuration
BATCH_SIZE = 10
NPROBE = 16
MAX_QUERY_LIMIT = 16384
LEGACY_PATH_PREFIX_ALIASES = {
    "/mass": "/media/mass",
}
TRANSCRIPT_PATH_SUFFIX_RE = re.compile(r"(?i)(?:\.ts)?\.(vtt|srt|tsv|txt)$")


def _indexing_alias_pairs() -> list[tuple[str, str]]:
    raw = os.environ.get("INDEXING_PATH_ALIASES", "/media/mass=/media/mass;/home/andy/nas_mass=/home/andy/nas_mass")
    pairs: list[tuple[str, str]] = []
    for pair in raw.split(";"):
        pair = pair.strip()
        if not pair or "=" not in pair:
            continue
        host_prefix, container_prefix = pair.split("=", 1)
        host_prefix = host_prefix.strip().rstrip("/")
        container_prefix = container_prefix.strip().rstrip("/")
        if host_prefix and container_prefix:
            pairs.append((host_prefix, container_prefix))
    return pairs


def _to_display_path(path: str) -> str:
    clean = str(path or "").strip()
    for host_prefix, container_prefix in _indexing_alias_pairs():
        if clean == container_prefix or clean.startswith(container_prefix + "/"):
            return host_prefix + clean[len(container_prefix) :]
    return clean


def _canonicalize_path_key(path: str) -> str:
    clean = str(Path(str(path or "")).as_posix()).strip()
    for legacy_prefix, canonical_prefix in LEGACY_PATH_PREFIX_ALIASES.items():
        if clean == legacy_prefix or clean.startswith(legacy_prefix + "/"):
            clean = canonical_prefix + clean[len(legacy_prefix) :]
            break
    return _to_display_path(clean)


def _transcript_source_group(item: dict) -> str:
    source_id = _canonicalize_path_key(str(item.get("source_id") or item.get("path") or ""))
    if not source_id:
        return ""
    return TRANSCRIPT_PATH_SUFFIX_RE.sub("", source_id)


def _is_informative_result_text(text: str) -> bool:
    cleaned = " ".join(str(text or "").split()).strip()
    if not cleaned:
        return False
    if not re.search(r"[A-Za-z0-9]", cleaned):
        return False
    tokens = [tok.lower() for tok in re.findall(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?", cleaned)]
    if len(tokens) < 3:
        return False
    unique = set(tokens)
    if len(tokens) >= 4 and len(unique) == 1:
        return False
    short_dominance = Counter(tokens).most_common(1)[0][1] / float(len(tokens))
    if len(tokens) <= 5 and short_dominance >= 0.5 and len(unique) <= 3:
        return False
    if len(tokens) >= 5 and len(unique) < 3:
        return False
    if len(tokens) >= 8:
        unique_ratio = len(unique) / float(len(tokens))
        if unique_ratio < 0.35:
            return False
    most_common_count = Counter(tokens).most_common(1)[0][1]
    if len(tokens) >= 6 and (most_common_count / float(len(tokens))) >= 0.5 and len(unique) <= 4:
        return False
    return True


def _prefers_lower_distance(mode_norm: str, anns_field: str, metric_type: str) -> bool:
    if mode_norm == "hybrid":
        return False
    if anns_field == "sparse":
        return False
    metric = str(metric_type or "COSINE").strip().upper()
    return metric in {"L2", "COSINE"}


def _is_better(candidate_distance: float, current_distance: float, prefers_lower: bool) -> bool:
    if prefers_lower:
        return candidate_distance < current_distance
    return candidate_distance > current_distance


def _metric_fallback_from_error(error: Exception, active_metric: str) -> str | None:
    message = str(error or "")
    match = re.search(r"expected=([A-Za-z0-9_]+)\]\[actual=([A-Za-z0-9_]+)", message)
    if match:
        expected = match.group(1).upper()
        actual = match.group(2).upper()
        if expected and actual == active_metric.upper() and expected != actual:
            return expected
    if "metric type not match" in message.lower() and active_metric.upper() != "L2":
        return "L2"
    return None


def _is_embedding_failure(error: Exception) -> bool:
    message = str(error or "").lower()
    return any(
        marker in message
        for marker in [
            "embedding request failed",
            "failed to generate valid query vector",
            "/v1/embeddings",
            "/embed",
            "tei backend error",
            "cuda_error_launch_failed",
        ]
    )


def _dedupe_repeated_chunks(results: list[dict], prefers_lower: bool = True) -> list[dict]:
    deduped: dict[tuple[str, str], dict] = {}
    passthrough: list[dict] = []
    for item in results:
        source_group = _transcript_source_group(item)
        text_norm = " ".join(str(item.get("text") or "").split()).lower()
        if not source_group or not text_norm:
            # Collections like command templates often don't carry source/path metadata.
            # Keep those rows; only apply repeated-chunk dedupe when a stable source key exists.
            passthrough.append(item)
            continue
        key = (source_group, text_norm)
        current = deduped.get(key)
        item_distance = float(item.get("distance", 1e18 if prefers_lower else -1e18))
        current_distance = float(current.get("distance", 1e18 if prefers_lower else -1e18)) if current is not None else None
        if current is None or _is_better(item_distance, current_distance, prefers_lower):
            deduped[key] = item
    if not passthrough and len(deduped) == len(results):
        return results
    out = list(deduped.values()) + passthrough
    out.sort(key=lambda item: float(item.get("distance", 1e18 if prefers_lower else -1e18)), reverse=not prefers_lower)
    return out


def _dedupe_transcript_copies(results: list[dict], prefers_lower: bool = True) -> list[dict]:
    deduped: dict[tuple[str, int, int, int, str], dict] = {}
    passthrough: list[dict] = []
    for item in results:
        filehash = str(item.get("filehash") or "").strip()
        text_norm = " ".join(str(item.get("text") or "").split()).lower()
        try:
            start_ms = int(item.get("t_start_ms"))
            end_ms = int(item.get("t_end_ms"))
            level = int(item.get("level"))
        except (TypeError, ValueError):
            passthrough.append(item)
            continue
        if not filehash or not text_norm:
            passthrough.append(item)
            continue
        key = (filehash, start_ms, end_ms, level, text_norm)
        current = deduped.get(key)
        item_distance = float(item.get("distance", 1e18 if prefers_lower else -1e18))
        current_distance = float(current.get("distance", 1e18 if prefers_lower else -1e18)) if current is not None else None
        if current is None or _is_better(item_distance, current_distance, prefers_lower):
            deduped[key] = item
    if not passthrough and len(deduped) == len(results):
        return results
    out = list(deduped.values()) + passthrough
    out.sort(key=lambda item: float(item.get("distance", 1e18 if prefers_lower else -1e18)), reverse=not prefers_lower)
    return out

def search_vectorstore(
    query,
    limit=10,
    path_filter="",
    unique=False,
    collection_name=None,
    ip_address="localhost",
    embedding_host="localhost",
    embedding_port=None,
    mode="dense",
    metric_type=None,
    max_distance=None,
    nprobe=None,
    hybrid_fusion=None,
    hybrid_dense_weight=None,
    hybrid_sparse_weight=None,
    hybrid_rrf_k=None,
):
    start_time = datetime.now()
    logging.info(f"Starting search_vectorstore: query='{query}', collection={collection_name}, ip={ip_address}, mode={mode}")
    alias = f"search_{uuid4().hex}"
    
    try:
        logging.info(f"Connecting to Milvus at {ip_address}...")
        connections.connect(alias, host=ip_address, port='19530')
        logging.info("Connected to Milvus successfully")

        # Resolve collection name with compatibility for both prefixed and raw names.
        if collection_name:
            clean_name = str(collection_name).strip()
            candidates = [clean_name]
            if clean_name.startswith("documents_"):
                logical_name = clean_name.removeprefix("documents_")
                if logical_name:
                    candidates.append(logical_name)
            else:
                candidates.append(f"documents_{clean_name}")
            chosen = None
            for candidate in candidates:
                if utility.has_collection(candidate, using=alias):
                    chosen = candidate
                    break
            collection_name = chosen or candidates[-1]
        else:
            collection_name = f"documents_{DEFAULT_EMBEDDING_MODEL.replace('-', '_')}"
        logging.info(f"Using collection: {collection_name}")

        # Check if collection exists
        if not utility.has_collection(collection_name, using=alias):
            raise RuntimeError(f"Collection {collection_name} does not exist.")

        # Open the collection
        collection = Collection(name=collection_name, using=alias)
        collection.load()
        logging.info(f"Collection loaded with {collection.num_entities} entities")
        collection_vector_dim = None
        try:
            for field in collection.schema.fields:
                if getattr(field, "name", "") == "vector":
                    collection_vector_dim = int(getattr(field, "params", {}).get("dim", 0) or 0)
                    break
        except Exception:
            collection_vector_dim = None

        # Determine search mode and required data format.
        mode_norm = str(mode or "dense").strip().lower()
        field_names = {f.name for f in collection.schema.fields}
        use_bm25 = mode_norm in {"bm25", "sparse"} and ("sparse" in field_names)
        use_hybrid = mode_norm in {"hybrid"} and ("sparse" in field_names) and ("vector" in field_names)
        vector_index_metric = None
        try:
            for index in (collection.indexes or []):
                if getattr(index, "field_name", "") != "vector":
                    continue
                params = getattr(index, "params", {}) or {}
                metric = params.get("metric_type")
                if metric:
                    vector_index_metric = str(metric).strip().upper()
                    break
        except Exception:
            vector_index_metric = None

        # Build output_fields: path exists only in file-loaded schema, not text-loaded
        output_fields = ["text", "hash", "embedding_model", "creation_date"]
        if "path" in field_names:
            output_fields.append("path")
        for optional_field in [
            "filehash",
            "tags",
            "chunk_duration_s",
            "level",
            "t_start_ms",
            "t_end_ms",
            "source_id",
            "parent_id",
            "doc_type",
            "source_type",
            "topic_label",
            "language",
        ]:
            if optional_field in field_names:
                output_fields.append(optional_field)

        # Build filter expression (used by hybrid and dense/bm25)
        expr = None
        if path_filter and "path" in field_names:
            expr = f'path == "{path_filter}"'
            logging.info(f"Using filter expression: {expr}")
        elif path_filter:
            logging.warning("Ignoring path_filter because collection has no 'path' field.")

        effective_metric_type = str(metric_type or os.environ.get("VECTORSTORE_METRIC_TYPE", "COSINE")).strip().upper()
        if not use_bm25 and vector_index_metric and effective_metric_type != vector_index_metric:
            logging.warning(
                "Requested metric '%s' differs from vector index metric '%s'; using '%s' for search.",
                effective_metric_type,
                vector_index_metric,
                vector_index_metric,
            )
            effective_metric_type = vector_index_metric
        effective_nprobe = int(nprobe if nprobe is not None else os.environ.get("VECTORSTORE_NPROBE", NPROBE))

        active_metric_type = effective_metric_type
        if use_hybrid:
            logging.info("Using HYBRID search (dense + BM25 sparse).")

            # Dense vector query via local embedding server
            model = LOCAL_EMBEDDING_MODEL
            dim = collection_vector_dim or LOCAL_EMBEDDING_DIM
            try:
                query_vectors = embed_text_to_vector(
                    [query],
                    model,
                    is_local=True,
                    ip_address=ip_address,
                    embedding_host=embedding_host,
                    embedding_port=embedding_port,
                )
                validated_query_vectors = validate_embeddings(query_vectors, dim)
                if not validated_query_vectors or validated_query_vectors[0] is None:
                    raise RuntimeError("Failed to generate valid query vector for hybrid search.")
            except Exception as e:
                if _is_embedding_failure(e):
                    logging.warning(
                        "Hybrid search embedding failed for collection '%s'; falling back to BM25 sparse search. Error: %s",
                        collection_name,
                        e,
                    )
                    use_hybrid = False
                    use_bm25 = "sparse" in field_names
                else:
                    raise

            if use_hybrid:
                # Default: weighted fusion (tunable via env)
                dense_w = (
                    float(hybrid_dense_weight)
                    if hybrid_dense_weight is not None
                    else float(os.environ.get("VECTORSTORE_HYBRID_DENSE_WEIGHT", "0.65"))
                )
                sparse_w = (
                    float(hybrid_sparse_weight)
                    if hybrid_sparse_weight is not None
                    else float(os.environ.get("VECTORSTORE_HYBRID_SPARSE_WEIGHT", "0.35"))
                )
                fusion = str(hybrid_fusion or os.environ.get("VECTORSTORE_HYBRID_FUSION", "weighted")).strip().lower()
                if fusion == "rrf":
                    k = int(hybrid_rrf_k if hybrid_rrf_k is not None else os.environ.get("VECTORSTORE_HYBRID_RRF_K", "60"))
                    rerank = RRFRanker(k=k)
                else:
                    rerank = WeightedRanker(dense_w, sparse_w)

                results = None
                while True:
                    try:
                        dense_req = AnnSearchRequest(
                            data=[validated_query_vectors[0]],
                            anns_field="vector",
                            param={"metric_type": active_metric_type, "params": {"nprobe": effective_nprobe}},
                            limit=min(max(limit, 10) * 4, MAX_QUERY_LIMIT),
                            expr=expr,
                        )
                        sparse_req = AnnSearchRequest(
                            data=[str(query)],
                            anns_field="sparse",
                            param={"metric_type": "BM25", "params": {}},
                            limit=min(max(limit, 10) * 4, MAX_QUERY_LIMIT),
                            expr=expr,
                        )
                        results = collection.hybrid_search(
                            reqs=[dense_req, sparse_req],
                            rerank=rerank,
                            limit=min(limit, MAX_QUERY_LIMIT),
                            output_fields=output_fields,
                        )
                        break
                    except Exception as e:
                        fallback_metric = _metric_fallback_from_error(e, active_metric_type)
                        if not fallback_metric:
                            raise
                        logging.warning(
                            "Hybrid search metric '%s' rejected by index; retrying with '%s'.",
                            active_metric_type,
                            fallback_metric,
                        )
                        active_metric_type = fallback_metric

                out = []
                # hybrid_search returns a list of Hits for each query vector; we have exactly one query.
                for hit in (results[0] if results else []):
                    out.append({
                        "id": hit.id,
                        "text": hit.get('text') or '',
                        "hash": hit.get('hash') or '',
                        "embedding_model": hit.get('embedding_model') or '',
                        "distance": hit.distance,
                        "creation_date": datetime.fromtimestamp(int(hit.get('creation_date') or 0)).isoformat(),
                        "filehash": hit.get("filehash") or "",
                        "path": _to_display_path(hit.get('path') or ''),
                        "tags": hit.get("tags"),
                        "chunk_duration_s": hit.get("chunk_duration_s"),
                        "level": hit.get("level"),
                        "t_start_ms": hit.get("t_start_ms"),
                        "t_end_ms": hit.get("t_end_ms"),
                        "source_id": _to_display_path(hit.get("source_id") or ""),
                        "parent_id": hit.get("parent_id"),
                        "doc_type": hit.get("doc_type"),
                        "source_type": hit.get("source_type"),
                        "topic_label": hit.get("topic_label"),
                        "language": hit.get("language"),
                    })
                prefers_lower = _prefers_lower_distance(mode_norm="hybrid", anns_field="vector", metric_type=effective_metric_type)
                # Deduplicate occasional hybrid duplicates by id, keeping best score.
                deduped_by_id = {}
                for item in out:
                    key = str(item.get("id"))
                    current = deduped_by_id.get(key)
                    item_distance = float(item.get("distance", 1e18 if prefers_lower else -1e18))
                    current_distance = float(current.get("distance", 1e18 if prefers_lower else -1e18)) if current is not None else None
                    if current is None or _is_better(item_distance, current_distance, prefers_lower):
                        deduped_by_id[key] = item
                out = list(deduped_by_id.values())
                out.sort(key=lambda item: float(item.get("distance", 1e18 if prefers_lower else -1e18)), reverse=not prefers_lower)
                out = [item for item in out if _is_informative_result_text(item.get("text", ""))]
                out = _dedupe_transcript_copies(out, prefers_lower=prefers_lower)
                out = _dedupe_repeated_chunks(out, prefers_lower=prefers_lower)

                # Handle unique results if requested
                if unique and out:
                    seen_hashes = set()
                    unique_results = []
                    for result in out:
                        if result['hash'] not in seen_hashes:
                            seen_hashes.add(result['hash'])
                            unique_results.append(result)
                    out = unique_results

                return out

        if use_bm25:
            logging.info("Using BM25 sparse search.")
            search_data = [str(query)]
            anns_field = "sparse"
            search_param = {"metric_type": "BM25", "params": {}}
        else:
            # Dense vector search (local embeddings server)
            model = LOCAL_EMBEDDING_MODEL
            dim = collection_vector_dim or LOCAL_EMBEDDING_DIM
            logging.info(f"Using embedding model: {model}")

            # Get embedding for the query
            logging.info("Generating embedding for query...")
            try:
                query_vectors = embed_text_to_vector(
                    [query],
                    model,
                    is_local=True,
                    ip_address=ip_address,
                    embedding_host=embedding_host,
                    embedding_port=embedding_port,
                )
                logging.info("Embedding generated successfully")

                # Validate embedding
                logging.info("Validating query embedding...")
                validated_query_vectors = validate_embeddings(query_vectors, dim)
                if not validated_query_vectors or validated_query_vectors[0] is None:
                    raise RuntimeError("Failed to generate valid query vector.")
                logging.info("Query embedding validated successfully")

                search_data = [validated_query_vectors[0]]
                anns_field = "vector"
                search_param = {"metric_type": active_metric_type, "params": {"nprobe": effective_nprobe}}
            except Exception as e:
                if not ("sparse" in field_names and _is_embedding_failure(e)):
                    raise
                logging.warning(
                    "Dense search embedding failed for collection '%s'; falling back to BM25 sparse search. Error: %s",
                    collection_name,
                    e,
                )
                search_data = [str(query)]
                anns_field = "sparse"
                search_param = {"metric_type": "BM25", "params": {}}

        # Perform search
        logging.info(f"Searching with limit={limit}...")
        search_params = {
            "data": search_data,
            "anns_field": anns_field,
            "param": search_param,
            "limit": min(limit, MAX_QUERY_LIMIT),
            "output_fields": output_fields,
            "expr": expr
        }

        search_start = datetime.now()
        while True:
            try:
                search_results = collection.search(**search_params)
                break
            except Exception as e:
                if anns_field != "vector":
                    raise
                current_metric = str(search_params.get("param", {}).get("metric_type", effective_metric_type)).upper()
                fallback_metric = _metric_fallback_from_error(e, current_metric)
                if not fallback_metric:
                    raise
                logging.warning(
                    "Dense search metric '%s' rejected by index; retrying with '%s'.",
                    current_metric,
                    fallback_metric,
                )
                search_params["param"] = {"metric_type": fallback_metric, "params": {"nprobe": effective_nprobe}}
                active_metric_type = fallback_metric
        search_time = datetime.now() - search_start
        logging.info(f"Search completed in {search_time.total_seconds():.2f}s")
        logging.info(f"Number of results returned: {len(search_results)}")

        # Process results
        results = []
        for hits in search_results:
            for hit in hits:
                results.append({
                    "id": hit.id,
                    "text": hit.get('text') or '',
                    "hash": hit.get('hash') or '',
                    "embedding_model": hit.get('embedding_model') or '',
                    "distance": hit.distance,
                    "creation_date": datetime.fromtimestamp(int(hit.get('creation_date') or 0)).isoformat(),
                    "filehash": hit.get("filehash") or "",
                    "path": _to_display_path(hit.get('path') or ''),
                    "tags": hit.get("tags"),
                    "chunk_duration_s": hit.get("chunk_duration_s"),
                    "level": hit.get("level"),
                    "t_start_ms": hit.get("t_start_ms"),
                    "t_end_ms": hit.get("t_end_ms"),
                    "source_id": _to_display_path(hit.get("source_id") or ""),
                    "parent_id": hit.get("parent_id"),
                    "doc_type": hit.get("doc_type"),
                    "source_type": hit.get("source_type"),
                    "topic_label": hit.get("topic_label"),
                    "language": hit.get("language"),
                })

        prefers_lower = _prefers_lower_distance(mode_norm=mode_norm, anns_field=anns_field, metric_type=active_metric_type if anns_field == "vector" else "BM25")
        deduped_by_id = {}
        for item in results:
            key = str(item.get("id"))
            current = deduped_by_id.get(key)
            item_distance = float(item.get("distance", 1e18 if prefers_lower else -1e18))
            current_distance = float(current.get("distance", 1e18 if prefers_lower else -1e18)) if current is not None else None
            if current is None or _is_better(item_distance, current_distance, prefers_lower):
                deduped_by_id[key] = item
        results = list(deduped_by_id.values())
        results.sort(key=lambda item: float(item.get("distance", 1e18 if prefers_lower else -1e18)), reverse=not prefers_lower)
        results = [item for item in results if _is_informative_result_text(item.get("text", ""))]
        results = _dedupe_transcript_copies(results, prefers_lower=prefers_lower)
        results = _dedupe_repeated_chunks(results, prefers_lower=prefers_lower)

        if max_distance is not None and anns_field == "vector" and active_metric_type in {"L2", "COSINE"}:
            results = [result for result in results if result.get("distance") is not None and result["distance"] <= float(max_distance)]

        # Handle unique results if requested
        if unique and results:
            logging.info(f"Filtering for unique results. Before: {len(results)}")
            seen_hashes = set()
            unique_results = []
            for result in results:
                if result['hash'] not in seen_hashes:
                    seen_hashes.add(result['hash'])
                    unique_results.append(result)
            results = unique_results
            logging.info(f"After unique filtering: {len(results)}")

        return results
    except Exception as e:
        logging.error(f"An error occurred during search: {str(e)}")
        logging.error(traceback.format_exc())
        raise
    finally:
        try:
            connections.disconnect(alias)
            logging.info("Disconnected from Milvus")
        except:
            pass
        end_time = datetime.now()
        logging.info(f"Search operation completed in {end_time - start_time}.")

if __name__ == "__main__":
    # Example usage: python search.py "your query" [collection_name]
    query = sys.argv[1] if len(sys.argv) > 1 else "I want a drink"
    collection_name = sys.argv[2] if len(sys.argv) > 2 else "amygdala"
    results = search_vectorstore(query, limit=5, collection_name=collection_name)

    if results:
        print(f"Found {len(results)} results:")
        for result in results:
            print(f"Text: {result['text']}")
            print(f"Distance: {result['distance']}")
            if result.get('path'):
                print(f"Path: {result['path']}")
            print(f"Embedding Model: {result['embedding_model']}")
            print(f"Creation Date: {result['creation_date']}")
            print("---")
    else:
        print("No results found.")
