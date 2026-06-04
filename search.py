# search.py
import os
import sys
import re
import logging
import threading
from collections import Counter
from pathlib import Path
from datetime import datetime
from pymilvus import connections, Collection, utility, AnnSearchRequest, WeightedRanker, RRFRanker
try:
    from pymilvus.client.types import LoadState
except Exception:  # pragma: no cover - older pymilvus compatibility
    LoadState = None  # type: ignore
import traceback
from uuid import uuid4


# ── Shared Milvus connection pool ──────────────────────────────────
# Reuse connections per host:port instead of creating one per request.
_milvus_pool_lock = threading.Lock()
_milvus_pool: dict[str, str] = {}  # "host:port" → alias
_milvus_pool_refcount: dict[str, int] = {}  # alias → active users

# ── Collection existence cache (avoids repeated has_collection RPCs) ──
_collection_exists_cache: dict[str, set] = {}  # alias → set of known names
_collection_exists_cache_ts: dict[str, float] = {}  # alias → last refresh time
_COLLECTION_CACHE_TTL = 30.0
_milvus_pool_verified_at: dict[str, float] = {}  # alias → last-verified timestamp
_MILVUS_POOL_VERIFY_INTERVAL = 30.0  # seconds between liveness checks
try:
    MILVUS_CONNECT_TIMEOUT = float(os.environ.get("MILVUS_CONNECT_TIMEOUT", "3"))
except (TypeError, ValueError):
    MILVUS_CONNECT_TIMEOUT = 3.0
try:
    MILVUS_LOAD_TIMEOUT = float(os.environ.get("MILVUS_LOAD_TIMEOUT", "60"))
except (TypeError, ValueError):
    MILVUS_LOAD_TIMEOUT = 60.0
RELEASE_COLLECTION_AFTER_SEARCH = (
    os.environ.get("VECTORSTORE_RELEASE_AFTER_SEARCH", "0").strip().lower()
    in {"1", "true", "yes", "on"}
)


def _get_milvus_connection(host: str, port: str = "19530") -> str:
    """Return a reusable Milvus connection alias for the given host."""
    import time as _time
    key = f"{host}:{port}"
    with _milvus_pool_lock:
        alias = _milvus_pool.get(key)
        if alias:
            last_verified = _milvus_pool_verified_at.get(alias, 0)
            if (_time.time() - last_verified) < _MILVUS_POOL_VERIFY_INTERVAL:
                _milvus_pool_refcount[alias] = _milvus_pool_refcount.get(alias, 0) + 1
                return alias
            try:
                utility.list_collections(using=alias, timeout=MILVUS_CONNECT_TIMEOUT)
                _milvus_pool_verified_at[alias] = _time.time()
                _milvus_pool_refcount[alias] = _milvus_pool_refcount.get(alias, 0) + 1
                return alias
            except Exception:
                try:
                    connections.disconnect(alias)
                except Exception:
                    pass
                del _milvus_pool[key]
                _milvus_pool_refcount.pop(alias, None)
                _milvus_pool_verified_at.pop(alias, None)

        alias = f"pool_{key.replace('.', '_').replace(':', '_')}"
        connections.connect(alias, host=host, port=port, timeout=MILVUS_CONNECT_TIMEOUT)
        _milvus_pool[key] = alias
        _milvus_pool_refcount[alias] = 1
        _milvus_pool_verified_at[alias] = _time.time()
        return alias


def _has_collection_cached(name: str, alias: str) -> bool:
    """Check collection existence with a short-lived cache to avoid per-search RPCs."""
    import time as _time
    now = _time.time()
    last = _collection_exists_cache_ts.get(alias, 0)
    if (now - last) >= _COLLECTION_CACHE_TTL or alias not in _collection_exists_cache:
        try:
            names = set(utility.list_collections(using=alias, timeout=MILVUS_CONNECT_TIMEOUT))
            _collection_exists_cache[alias] = names
            _collection_exists_cache_ts[alias] = now
        except Exception:
            return utility.has_collection(name, using=alias, timeout=MILVUS_CONNECT_TIMEOUT)
    if name in _collection_exists_cache.get(alias, set()):
        return True
    # Cache miss: the cached set may be stale (a collection created after the last
    # refresh, within the TTL window). Confirm with an authoritative check before
    # reporting absence so freshly-created collections are not falsely "missing".
    try:
        exists = utility.has_collection(name, using=alias, timeout=MILVUS_CONNECT_TIMEOUT)
    except Exception:
        return False
    if exists:
        _collection_exists_cache.setdefault(alias, set()).add(name)
    return exists


def _release_milvus_connection(alias: str):
    """Decrement refcount for a pooled connection (kept alive for reuse)."""
    with _milvus_pool_lock:
        count = _milvus_pool_refcount.get(alias, 1) - 1
        if count <= 0:
            _milvus_pool_refcount.pop(alias, None)
        else:
            _milvus_pool_refcount[alias] = count

from utils import (
    DEFAULT_EMBEDDING_MODEL, EMBEDDING_DIMENSIONS, LOCAL_EMBEDDING_MODEL, LOCAL_EMBEDDING_DIM,
    embed_text_to_vector, validate_embeddings
)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Constants Configuration
BATCH_SIZE = 10
NPROBE = 16
MAX_QUERY_LIMIT = 16384
LEGACY_PATH_PREFIX_ALIASES = {
    "/mass": "/media/mass",
}
TRANSCRIPT_PATH_SUFFIX_RE = re.compile(r"(?i)(?:\.ts)?\.(vtt|srt|tsv|txt|log)$")
TRANSCRIPT_CONTEXT_EXPANSION_ENABLED = (
    os.environ.get("VECTORSTORE_TRANSCRIPT_CONTEXT_EXPANSION", "1").strip().lower()
    not in {"0", "false", "no", "off"}
)
try:
    TRANSCRIPT_CONTEXT_EXPAND_MAX_HITS = max(1, int(os.environ.get("VECTORSTORE_TRANSCRIPT_CONTEXT_EXPAND_MAX_HITS", "12")))
except (TypeError, ValueError):
    TRANSCRIPT_CONTEXT_EXPAND_MAX_HITS = 12
try:
    TRANSCRIPT_CONTEXT_TARGET_DURATION_S = max(
        60,
        int(os.environ.get("VECTORSTORE_TRANSCRIPT_CONTEXT_TARGET_DURATION_S", "3600")),
    )
except (TypeError, ValueError):
    TRANSCRIPT_CONTEXT_TARGET_DURATION_S = 3600


class CollectionLoadError(RuntimeError):
    """Raised when Milvus cannot make a collection searchable quickly."""


def _load_state_label(collection_name: str, alias: str) -> str:
    try:
        state = utility.load_state(collection_name, using=alias, timeout=1)
    except Exception:
        return "unknown"
    try:
        if LoadState is not None and state == LoadState.Loaded:
            return "loaded"
        if LoadState is not None and state == LoadState.Loading:
            return "loading"
        if LoadState is not None and state == LoadState.NotLoad:
            return "not_loaded"
    except Exception:
        pass
    return str(state).split(".")[-1].lower()


def _ensure_collection_loaded(
    collection: Collection,
    collection_name: str,
    alias: str,
    *,
    timeout: float,
    load_if_unloaded: bool,
) -> str:
    state = _load_state_label(collection_name, alias)
    if state == "loaded":
        return state
    if not load_if_unloaded:
        raise CollectionLoadError(
            f"Collection {collection_name} is {state}; skipping cold load for this search."
        )
    try:
        collection.load(timeout=timeout)
        utility.wait_for_loading_complete(collection_name, using=alias, timeout=timeout)
    except Exception as exc:
        next_state = _load_state_label(collection_name, alias)
        raise CollectionLoadError(
            f"Collection {collection_name} could not be loaded within {timeout:.1f}s "
            f"(state={next_state}). Milvus may be memory constrained or still loading segments: {exc}"
        ) from exc
    return _load_state_label(collection_name, alias)


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


def _escape_milvus_string(value: str) -> str:
    return str(value or "").replace("\\", "\\\\").replace('"', '\\"')


def _and_expr(*parts: str | None) -> str | None:
    clean = [str(part).strip() for part in parts if str(part or "").strip()]
    if not clean:
        return None
    if len(clean) == 1:
        return clean[0]
    return " and ".join(f"({part})" for part in clean)


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


def _result_from_row(row: dict, *, distance: float = 0.0, retrieval_mode: str | None = None) -> dict:
    raw_creation = row.get("creation_date") or 0
    if isinstance(raw_creation, str) and not raw_creation.isdigit():
        creation_date = raw_creation
    else:
        try:
            creation_date = datetime.fromtimestamp(int(raw_creation or 0)).isoformat()
        except Exception:
            creation_date = datetime.fromtimestamp(0).isoformat()
    result = {
        "id": row.get("id") or row.get("pk") or row.get("_id") or row.get("hash") or "",
        "text": row.get("text") or "",
        "hash": row.get("hash") or "",
        "embedding_model": row.get("embedding_model") or "",
        "distance": distance,
        "creation_date": creation_date,
        "filehash": row.get("filehash") or "",
        "path": _to_display_path(row.get("path") or ""),
        "tags": row.get("tags"),
        "chunk_duration_s": row.get("chunk_duration_s"),
        "level": row.get("level"),
        "t_start_ms": row.get("t_start_ms"),
        "t_end_ms": row.get("t_end_ms"),
        "source_id": _to_display_path(row.get("source_id") or ""),
        "parent_id": row.get("parent_id"),
        "doc_type": row.get("doc_type"),
        "source_type": row.get("source_type"),
        "topic_label": row.get("topic_label"),
        "language": row.get("language"),
    }
    if retrieval_mode:
        result["retrieval_mode"] = retrieval_mode
    return result


def _result_from_hit(hit) -> dict:
    return {
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
    }


_ANSWER_INTENT_RE = re.compile(
    r"\b(what|why|how|decid(?:e|ed|ing|ion)|answer|outcome|status|action|follow[- ]?up|risk|issue|changed|resolved|explain(?:ed|ing)?)\b",
    re.IGNORECASE,
)
_RERANK_STOPWORDS = {
    "about",
    "after",
    "again",
    "also",
    "and",
    "are",
    "because",
    "been",
    "before",
    "being",
    "but",
    "can",
    "could",
    "did",
    "does",
    "doing",
    "for",
    "from",
    "get",
    "got",
    "had",
    "has",
    "have",
    "how",
    "into",
    "just",
    "kind",
    "like",
    "more",
    "not",
    "now",
    "okay",
    "one",
    "our",
    "out",
    "right",
    "said",
    "see",
    "should",
    "some",
    "that",
    "the",
    "their",
    "them",
    "then",
    "there",
    "these",
    "they",
    "thing",
    "think",
    "this",
    "those",
    "through",
    "what",
    "when",
    "where",
    "which",
    "who",
    "with",
    "would",
    "yeah",
    "you",
    "your",
}
_LEXICAL_LOW_SIGNAL_TERMS = {
    "conversation",
    "different",
    "discussion",
    "long",
    "space",
    "talk",
    "talked",
    "talking",
    "thread",
}


def _rerank_terms(text: str) -> set[str]:
    return {
        token.lower()
        for token in re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", text or "")
        if token.lower() not in _RERANK_STOPWORDS
    }


def _query_wants_answer(query: str) -> bool:
    return bool(_ANSWER_INTENT_RE.search(query or ""))


def _is_transcript_result(item: dict) -> bool:
    doc_type = str(item.get("doc_type") or "").lower()
    source_type = str(item.get("source_type") or "").lower()
    path = str(item.get("path") or item.get("source_id") or "").lower()
    return (
        "transcript" in doc_type
        or "media_event" in doc_type
        or "subtitle" in doc_type
        or source_type in {"media", "transcript"}
        or (TRANSCRIPT_PATH_SUFFIX_RE.search(path) is not None and ("/media/" in path or "/recording/" in path))
    )


def _answer_intent_rank_score(item: dict, query_terms: set[str], prefers_lower: bool) -> float:
    raw_distance = float(item.get("distance", 1e18 if prefers_lower else -1e18))
    base_score = -raw_distance if prefers_lower else raw_distance
    if not query_terms or not _is_transcript_result(item):
        return base_score

    text = " ".join(str(item.get("text") or "").split()).strip()
    if not text:
        return base_score
    overlap = len(query_terms & _rerank_terms(text))
    if overlap <= 0:
        return base_score

    tags = str(item.get("tags") or "").lower()
    doc_type = str(item.get("doc_type") or "").lower()
    topic_label = str(item.get("topic_label") or "").lower()
    tag_blob = " ".join([tags, doc_type, topic_label])
    try:
        level = int(item.get("level") or 0)
    except (TypeError, ValueError):
        level = 0
    try:
        duration_s = float(item.get("chunk_duration_s") or 0.0)
    except (TypeError, ValueError):
        duration_s = 0.0

    boost = min(overlap, 6) * 2.5
    if any(marker in tag_blob for marker in ("event_decision", "event_action", "event_status", "decision", "action", "status")):
        boost += 80.0
    elif level >= 1 or duration_s >= 20.0 or len(text) >= 280:
        boost += 35.0

    short_question = text.endswith("?") and len(text.split()) <= 24
    if short_question:
        boost -= 55.0
    elif "?" in text[:240] and len(text) < 260 and level == 0:
        boost -= 20.0
    if level == 0 and duration_s <= 8.0 and len(text) < 180:
        boost -= 18.0
    return base_score + boost


def _rerank_answer_intent_results(results: list[dict], query: str, prefers_lower: bool) -> list[dict]:
    if not results or not _query_wants_answer(query):
        return results
    query_terms = _rerank_terms(query)
    if not query_terms:
        return results
    for item in results:
        item["ranking_score"] = _answer_intent_rank_score(item, query_terms, prefers_lower)
    results.sort(key=lambda item: float(item.get("ranking_score", 0.0)), reverse=True)
    return results


def _query_tokens_in_order(text: str) -> list[str]:
    tokens: list[str] = []
    seen: set[str] = set()
    for token in re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", text or ""):
        lower = token.lower()
        if lower in _RERANK_STOPWORDS or lower in seen:
            continue
        seen.add(lower)
        tokens.append(lower)
    return tokens


def _term_variants(token: str) -> list[str]:
    token = str(token or "").lower().strip()
    if not token:
        return []
    if token in {"bio", "biocomputing"}:
        variants = ["biological", "biology", "biocomputing"]
    else:
        variants = [token]
    if token in {"computing", "computation", "computational"}:
        variants.extend(["compute", "computational", "computation"])
    if token == "architecture":
        variants.append("architectural")
    if token.endswith("ing") and len(token) > 5:
        stem = token[:-3]
        variants.append(stem)
        variants.append(stem + "e")
    if token.endswith("ies") and len(token) > 5:
        variants.append(token[:-3] + "y")
    elif token.endswith("s") and len(token) > 4:
        variants.append(token[:-1])

    out: list[str] = []
    seen: set[str] = set()
    for variant in variants:
        clean = variant.strip().lower()
        if len(clean) < 3 or clean in seen:
            continue
        seen.add(clean)
        out.append(clean)
    return out


def _lexical_query_terms(query: str, *, max_terms: int = 12) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for token in _query_tokens_in_order(query):
        for variant in _term_variants(token):
            if variant in seen:
                continue
            seen.add(variant)
            out.append(variant)
            if len(out) >= max_terms:
                return out
    return out


def _lexical_query_groups(query: str, *, max_groups: int = 6) -> list[list[str]]:
    groups: list[list[str]] = []
    tokens = _query_tokens_in_order(query)
    high_signal = [token for token in tokens if token not in _LEXICAL_LOW_SIGNAL_TERMS]
    if len(high_signal) >= 2:
        tokens = high_signal
    for token in tokens:
        variants = _term_variants(token)
        if not variants:
            continue
        groups.append(variants[:4])
        if len(groups) >= max_groups:
            break
    return groups


def _variant_group_expr(variants: list[str]) -> str:
    return " or ".join(f'text like "%{_escape_milvus_string(term)}%"' for term in variants)


def _lexical_query_expr(query: str, base_expr: str | None = None) -> str | None:
    groups = _lexical_query_groups(query)
    if not groups:
        return base_expr
    group_exprs = [_variant_group_expr(group) for group in groups]
    if len(group_exprs) == 1:
        term_expr = group_exprs[0]
    elif len(group_exprs) == 2:
        term_expr = f"({group_exprs[0]}) and ({group_exprs[1]})"
    else:
        pair_exprs: list[str] = []
        for left_idx, left in enumerate(group_exprs):
            for right in group_exprs[left_idx + 1 :]:
                pair_exprs.append(f"(({left}) and ({right}))")
        term_expr = " or ".join(pair_exprs)
    if not term_expr:
        return base_expr
    return _and_expr(base_expr, term_expr)


def _lexical_rank_score(item: dict, query: str) -> float:
    text = " ".join(str(item.get("text") or "").split()).strip()
    if not text:
        return 0.0
    text_lower = text.lower()
    groups = _lexical_query_groups(query, max_groups=8)
    score = 0.0
    for group in groups:
        if any(term in text_lower for term in group):
            score += 15.0
    query_norm = " ".join(str(query or "").lower().split())
    if query_norm and query_norm in text_lower:
        score += 35.0
    query_ordered_terms = _query_tokens_in_order(query)
    for left, right in zip(query_ordered_terms, query_ordered_terms[1:]):
        phrase = f"{left} {right}"
        if phrase in text_lower:
            score += 18.0
    try:
        level = int(item.get("level") or 0)
    except (TypeError, ValueError):
        level = 0
    try:
        duration_s = float(item.get("chunk_duration_s") or 0.0)
    except (TypeError, ValueError):
        duration_s = 0.0
    if _is_transcript_result(item):
        if level >= 2 or duration_s >= 1800:
            score += 8.0
        elif level >= 1 or duration_s >= 30:
            score += 3.0
    if len(text) >= 500:
        score += 2.0
    return score


def _is_sparse_text_search_data_error(error: Exception) -> bool:
    message = str(error or "").lower()
    return "search_data" in message and "illegal" in message


def _query_output_fields(output_fields: list[str]) -> list[str]:
    fields = list(output_fields)
    if "id" not in fields:
        fields.insert(0, "id")
    return fields


def _lexical_query_fallback(
    collection: Collection,
    query: str,
    *,
    output_fields: list[str],
    expr: str | None,
    limit: int,
) -> list[dict]:
    query_expr = _lexical_query_expr(query, expr)
    if not query_expr:
        return []
    candidate_limit = min(max(limit, 10) * 8, 512)
    rows = collection.query(
        expr=query_expr,
        output_fields=_query_output_fields(output_fields),
        limit=candidate_limit,
        timeout=10,
    )
    results: list[dict] = []
    for row in rows or []:
        item = _result_from_row(row, retrieval_mode="lexical_fallback")
        score = _lexical_rank_score(item, query)
        if score <= 0:
            continue
        item["distance"] = score
        item["ranking_score"] = score
        results.append(item)
    results.sort(key=lambda item: float(item.get("ranking_score", item.get("distance", 0.0))), reverse=True)
    return results


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


def _int_value(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _query_benefits_from_transcript_context(query: str) -> bool:
    terms = _query_tokens_in_order(query)
    if not terms:
        return False
    if _query_wants_answer(query):
        return True
    if len(terms) <= 8:
        return True
    return bool(
        re.search(
            r"\b(conversation|discussion|discuss(?:ed|ing)?|talk(?:ed|ing)?|thread|transcript|meeting|call|long)\b",
            query or "",
            re.IGNORECASE,
        )
    )


def _should_expand_transcript_context(item: dict, query: str) -> bool:
    if not TRANSCRIPT_CONTEXT_EXPANSION_ENABLED:
        return False
    if not _is_transcript_result(item):
        return False
    if not _query_benefits_from_transcript_context(query):
        return False
    level = _int_value(item.get("level"), 0)
    duration_s = _int_value(item.get("chunk_duration_s"), 0)
    if level >= 2 or duration_s >= TRANSCRIPT_CONTEXT_TARGET_DURATION_S:
        return False
    return True


def _parent_context_expr(item: dict, base_expr: str | None) -> str | None:
    start_ms = _int_value(item.get("t_start_ms"), -1)
    if start_ms < 0:
        return None
    source_id = str(item.get("source_id") or "").strip()
    path = str(item.get("path") or "").strip()
    source_expr = None
    if source_id:
        source_expr = f'source_id == "{_escape_milvus_string(source_id)}"'
    elif path:
        source_expr = f'path == "{_escape_milvus_string(path)}"'
    if not source_expr:
        return None
    parent_expr = (
        f"{source_expr} and level == 2 and "
        f"t_start_ms <= {start_ms} and t_end_ms >= {start_ms}"
    )
    return _and_expr(base_expr, parent_expr)


def _select_parent_context(rows: list[dict], query: str) -> dict | None:
    if not rows:
        return None
    candidates = [_result_from_row(row) for row in rows]
    for item in candidates:
        lexical = _lexical_rank_score(item, query)
        duration_s = _int_value(item.get("chunk_duration_s"), 0)
        duration_fit = 1.0 / (1.0 + abs(duration_s - TRANSCRIPT_CONTEXT_TARGET_DURATION_S))
        item["_context_selection_score"] = lexical + duration_fit
    candidates.sort(key=lambda item: float(item.get("_context_selection_score", 0.0)), reverse=True)
    return candidates[0]


def _apply_parent_context(child: dict, parent: dict) -> dict:
    out = dict(child)
    matched_fields = {
        "matched_id": child.get("id"),
        "matched_text": child.get("text") or "",
        "matched_hash": child.get("hash") or "",
        "matched_level": child.get("level"),
        "matched_chunk_duration_s": child.get("chunk_duration_s"),
        "matched_t_start_ms": child.get("t_start_ms"),
        "matched_t_end_ms": child.get("t_end_ms"),
    }
    child_id = child.get("id")
    child_distance = child.get("distance")
    child_ranking_score = child.get("ranking_score")
    out.update(parent)
    out.update(matched_fields)
    out["id"] = child_id
    out["distance"] = child_distance
    if child_ranking_score is not None:
        out["ranking_score"] = child_ranking_score
    out["context_id"] = parent.get("id")
    out["context_expanded"] = True
    out["retrieval_context"] = "parent_transcript_window"
    return out


def _dedupe_expanded_context(results: list[dict], prefers_lower: bool) -> list[dict]:
    deduped: dict[tuple[str, int, int, int], dict] = {}
    passthrough: list[dict] = []
    for item in results:
        if not item.get("context_expanded"):
            passthrough.append(item)
            continue
        source_group = _transcript_source_group(item)
        start_ms = _int_value(item.get("t_start_ms"), -1)
        end_ms = _int_value(item.get("t_end_ms"), -1)
        level = _int_value(item.get("level"), -1)
        if not source_group or start_ms < 0 or end_ms < 0 or level < 0:
            passthrough.append(item)
            continue
        key = (source_group, start_ms, end_ms, level)
        current = deduped.get(key)
        item_distance = float(item.get("distance", 1e18 if prefers_lower else -1e18))
        current_distance = float(current.get("distance", 1e18 if prefers_lower else -1e18)) if current is not None else None
        if current is None or _is_better(item_distance, current_distance, prefers_lower):
            deduped[key] = item
    out = list(deduped.values()) + passthrough
    out.sort(key=lambda item: float(item.get("distance", 1e18 if prefers_lower else -1e18)), reverse=not prefers_lower)
    return out


def _expand_transcript_context_results(
    collection: Collection,
    results: list[dict],
    query: str,
    output_fields: list[str],
    expr: str | None,
    limit: int,
    prefers_lower: bool,
) -> list[dict]:
    if not results or not TRANSCRIPT_CONTEXT_EXPANSION_ENABLED:
        return results
    expanded: list[dict] = []
    expanded_count = 0
    max_expand = min(len(results), max(limit, TRANSCRIPT_CONTEXT_EXPAND_MAX_HITS))
    for idx, item in enumerate(results):
        if idx >= max_expand or not _should_expand_transcript_context(item, query):
            expanded.append(item)
            continue
        parent_expr = _parent_context_expr(item, expr)
        if not parent_expr:
            expanded.append(item)
            continue
        try:
            rows = collection.query(
                expr=parent_expr,
                output_fields=_query_output_fields(output_fields),
                limit=4,
                timeout=10,
            )
        except Exception as exc:
            logging.warning("Transcript context expansion failed for result %s: %s", item.get("id"), exc)
            expanded.append(item)
            continue
        parent = _select_parent_context(rows or [], query)
        if not parent:
            expanded.append(item)
            continue
        expanded.append(_apply_parent_context(item, parent))
        expanded_count += 1
    if expanded_count <= 0:
        return results
    return _dedupe_expanded_context(expanded, prefers_lower=prefers_lower)

def search_vectorstore(
    query,
    limit=10,
    path_filter="",
    unique=False,
    collection_name=None,
    embedding_model=None,
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
    load_timeout=None,
    load_if_unloaded=True,
    query_vector=None,
):
    start_time = datetime.now()
    logging.debug(f"search_vectorstore: query='{query[:40]}', collection={collection_name}, mode={mode}")
    try:
        limit = max(1, min(int(limit), MAX_QUERY_LIMIT))
    except (TypeError, ValueError):
        limit = 10
    alias = _get_milvus_connection(ip_address)
    collection = None

    try:


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
                if _has_collection_cached(candidate, alias):
                    chosen = candidate
                    break
            collection_name = chosen or candidates[-1]
        else:
            collection_name = f"documents_{DEFAULT_EMBEDDING_MODEL.replace('-', '_')}"

        if not _has_collection_cached(collection_name, alias):
            raise RuntimeError(f"Collection {collection_name} does not exist.")

        # Open the collection
        effective_load_timeout = MILVUS_LOAD_TIMEOUT
        if load_timeout is not None:
            try:
                effective_load_timeout = max(1.0, float(load_timeout))
            except (TypeError, ValueError):
                effective_load_timeout = MILVUS_LOAD_TIMEOUT
        collection = Collection(name=collection_name, using=alias)
        _ensure_collection_loaded(
            collection,
            collection_name,
            alias,
            timeout=effective_load_timeout,
            load_if_unloaded=bool(load_if_unloaded),
        )

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

            # Dense vector query — use pre-computed vector if available
            model = str(embedding_model or LOCAL_EMBEDDING_MODEL)
            dim = collection_vector_dim or LOCAL_EMBEDDING_DIM
            try:
                if query_vector is not None:
                    validated_query_vectors = [query_vector]
                else:
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

                candidate_limit = min(max(limit, 10) * 4, MAX_QUERY_LIMIT)
                results = None
                hybrid_dense_only_fallback = False
                while True:
                    try:
                        dense_req = AnnSearchRequest(
                            data=[validated_query_vectors[0]],
                            anns_field="vector",
                            param={"metric_type": active_metric_type, "params": {"nprobe": effective_nprobe}},
                            limit=candidate_limit,
                            expr=expr,
                        )
                        sparse_req = AnnSearchRequest(
                            data=[str(query)],
                            anns_field="sparse",
                            param={"metric_type": "BM25", "params": {}},
                            limit=candidate_limit,
                            expr=expr,
                        )
                        results = collection.hybrid_search(
                            reqs=[dense_req, sparse_req],
                            rerank=rerank,
                            limit=candidate_limit,
                            output_fields=output_fields,
                        )
                        break
                    except Exception as e:
                        if _is_sparse_text_search_data_error(e):
                            logging.warning(
                                "Hybrid sparse text search was rejected by the Milvus client; retrying dense-only search. Error: %s",
                                e,
                            )
                            results = collection.search(
                                data=[validated_query_vectors[0]],
                                anns_field="vector",
                                param={"metric_type": active_metric_type, "params": {"nprobe": effective_nprobe}},
                                limit=candidate_limit,
                                output_fields=output_fields,
                                expr=expr,
                            )
                            hybrid_dense_only_fallback = True
                            break
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
                    item = _result_from_hit(hit)
                    if hybrid_dense_only_fallback:
                        item["retrieval_mode"] = "dense_fallback"
                    out.append(item)
                prefers_lower = _prefers_lower_distance(
                    mode_norm="dense" if hybrid_dense_only_fallback else "hybrid",
                    anns_field="vector",
                    metric_type=effective_metric_type,
                )
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
                out = _rerank_answer_intent_results(out, query, prefers_lower=prefers_lower)
                out = _expand_transcript_context_results(
                    collection,
                    out,
                    query,
                    output_fields,
                    expr,
                    limit,
                    prefers_lower,
                )

                # Handle unique results if requested
                if unique and out:
                    seen_hashes = set()
                    unique_results = []
                    for result in out:
                        if result['hash'] not in seen_hashes:
                            seen_hashes.add(result['hash'])
                            unique_results.append(result)
                    out = unique_results

                return out[:limit]

        if use_bm25:
            logging.info("Using BM25 sparse search.")
            search_data = [str(query)]
            anns_field = "sparse"
            search_param = {"metric_type": "BM25", "params": {}}
        else:
            # Dense vector search — use pre-computed vector if available
            model = str(embedding_model or LOCAL_EMBEDDING_MODEL)
            dim = collection_vector_dim or LOCAL_EMBEDDING_DIM
            try:
                if query_vector is not None:
                    validated_query_vectors = [query_vector]
                else:
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
                    raise RuntimeError("Failed to generate valid query vector.")

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

        search_params = {
            "data": search_data,
            "anns_field": anns_field,
            "param": search_param,
            "limit": min(max(limit, 10) * 4, MAX_QUERY_LIMIT) if anns_field == "sparse" else limit,
            "output_fields": output_fields,
            "expr": expr
        }

        search_start = datetime.now()
        while True:
            try:
                search_results = collection.search(**search_params)
                break
            except Exception as e:
                if anns_field == "sparse" and _is_sparse_text_search_data_error(e):
                    logging.warning(
                        "BM25 sparse text search was rejected by the Milvus client; using lexical scalar fallback. Error: %s",
                        e,
                    )
                    results = _lexical_query_fallback(
                        collection,
                        query,
                        output_fields=output_fields,
                        expr=expr,
                        limit=limit,
                    )
                    prefers_lower = False
                    results = [item for item in results if _is_informative_result_text(item.get("text", ""))]
                    results = _dedupe_transcript_copies(results, prefers_lower=prefers_lower)
                    results = _dedupe_repeated_chunks(results, prefers_lower=prefers_lower)
                    results = _rerank_answer_intent_results(results, query, prefers_lower=prefers_lower)
                    results = _expand_transcript_context_results(
                        collection,
                        results,
                        query,
                        output_fields,
                        expr,
                        limit,
                        prefers_lower,
                    )
                    if unique and results:
                        seen_hashes = set()
                        unique_results = []
                        for result in results:
                            if result["hash"] not in seen_hashes:
                                seen_hashes.add(result["hash"])
                                unique_results.append(result)
                        results = unique_results
                    return results[:limit]
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
                results.append(_result_from_hit(hit))

        prefers_lower = _prefers_lower_distance(mode_norm=mode_norm, anns_field=anns_field, metric_type=active_metric_type if anns_field == "vector" else "IP")
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
        if anns_field == "sparse" or mode_norm == "hybrid":
            results = _rerank_answer_intent_results(results, query, prefers_lower=prefers_lower)

        if max_distance is not None and anns_field == "vector" and active_metric_type in {"L2", "COSINE"}:
            results = [result for result in results if result.get("distance") is not None and result["distance"] <= float(max_distance)]

        results = _expand_transcript_context_results(
            collection,
            results,
            query,
            output_fields,
            expr,
            limit,
            prefers_lower,
        )

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

        return results[:limit]
    except Exception as e:
        logging.error(f"An error occurred during search: {str(e)}")
        logging.error(traceback.format_exc())
        raise
    finally:
        if collection is not None and RELEASE_COLLECTION_AFTER_SEARCH:
            try:
                collection.release()
                logging.info(f"Released collection {collection_name}")
            except Exception as release_error:
                logging.warning(f"Failed to release collection {collection_name}: {release_error}")
        _release_milvus_connection(alias)
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
