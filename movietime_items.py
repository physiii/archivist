from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from hashlib import sha256
from typing import Any
from uuid import uuid4

from pymilvus import (
    AnnSearchRequest,
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    RRFRanker,
    WeightedRanker,
    connections,
    utility,
)
try:
    from pymilvus import Function, FunctionType
except Exception:  # pragma: no cover
    Function = None  # type: ignore
    FunctionType = None  # type: ignore

from utils import (
    INDEX_TYPE,
    LOCAL_EMBEDDING_DIM,
    LOCAL_EMBEDDING_MODEL,
    METRIC_TYPE,
    NLIST,
    embed_text_to_vector,
    validate_embeddings,
)

MOVIETIME_COLLECTION_DEFAULT = "documents_movietime_library"
MAX_QUERY_LIMIT = 4096
EMBEDDING_BATCH_SIZE = 16
EMBEDDING_TEXT_MAX_CHARS = 12000


def _alias(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


def _raw_collection_name(name: str | None) -> str:
    base = str(name or "").strip() or "movietime_library"
    return base if base.startswith("documents_") else f"documents_{base}"


def _ensure_collection_schema(alias: str, collection_name: str) -> Collection:
    required = {
        "id",
        "vector",
        "text",
        "sparse",
        "hash",
        "source_id",
        "item_id",
        "kind",
        "chunk_tag",
        "title",
        "canonical_title",
        "year",
        "genres",
        "parental_rating",
        "rating",
        "runtime",
        "tags",
        "updated_at",
        "embedding_model",
        "creation_date",
    }

    if utility.has_collection(collection_name, using=alias):
        coll = Collection(collection_name, using=alias)
        names = {f.name for f in coll.schema.fields}
        vector_dim = 0
        text_has_analyzer = False
        for f in coll.schema.fields:
            if f.name == "vector":
                vector_dim = int(getattr(f, "params", {}).get("dim", 0) or 0)
            if f.name == "text":
                params = getattr(f, "params", {}) or {}
                text_has_analyzer = bool(getattr(f, "enable_analyzer", False) or params.get("enable_analyzer"))
        if required.issubset(names) and vector_dim == LOCAL_EMBEDDING_DIM and text_has_analyzer:
            return coll
        logging.warning(
            "Dropping collection %s due to schema mismatch (required=%s present=%s dim=%s analyzer=%s).",
            collection_name,
            sorted(required),
            sorted(names),
            vector_dim,
            text_has_analyzer,
        )
        coll.drop()

    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=LOCAL_EMBEDDING_DIM),
        FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535, enable_analyzer=True),
        FieldSchema(name="sparse", dtype=DataType.SPARSE_FLOAT_VECTOR),
        FieldSchema(name="hash", dtype=DataType.VARCHAR, max_length=64),
        FieldSchema(name="source_id", dtype=DataType.VARCHAR, max_length=256),
        FieldSchema(name="item_id", dtype=DataType.INT64),
        FieldSchema(name="kind", dtype=DataType.VARCHAR, max_length=16),
        FieldSchema(name="chunk_tag", dtype=DataType.VARCHAR, max_length=64),
        FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=512),
        FieldSchema(name="canonical_title", dtype=DataType.VARCHAR, max_length=512),
        FieldSchema(name="year", dtype=DataType.INT64),
        FieldSchema(name="genres", dtype=DataType.VARCHAR, max_length=512),
        FieldSchema(name="parental_rating", dtype=DataType.VARCHAR, max_length=32),
        FieldSchema(name="rating", dtype=DataType.FLOAT),
        FieldSchema(name="runtime", dtype=DataType.INT64),
        FieldSchema(name="tags", dtype=DataType.VARCHAR, max_length=4096),
        FieldSchema(name="updated_at", dtype=DataType.INT64),
        FieldSchema(name="embedding_model", dtype=DataType.VARCHAR, max_length=64),
        FieldSchema(name="creation_date", dtype=DataType.INT64),
    ]
    functions = []
    if Function is not None and FunctionType is not None:
        functions = [
            Function(
                name="bm25_fn",
                function_type=FunctionType.BM25,
                input_field_names=["text"],
                output_field_names=["sparse"],
            )
        ]
    schema = CollectionSchema(
        fields=fields,
        description="MovieTime item chunks",
        functions=functions,
    )
    coll = Collection(collection_name, schema=schema, using=alias)

    try:
        coll.create_index(
            field_name="vector",
            index_params={"index_type": INDEX_TYPE, "metric_type": METRIC_TYPE, "params": {"nlist": NLIST}},
            timeout=10,
        )
    except Exception as exc:
        logging.warning("Dense index create warning for %s: %s", collection_name, exc)

    try:
        coll.create_index(
            field_name="sparse",
            index_params={"index_type": "SPARSE_INVERTED_INDEX", "metric_type": "BM25", "params": {}},
            timeout=10,
        )
    except Exception as exc:
        logging.warning("Sparse index create warning for %s: %s", collection_name, exc)

    return coll


def _escape_expr(value: str) -> str:
    return str(value).replace("\\", "\\\\").replace('"', '\\"')


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _to_tags(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, str):
        val = raw.strip()
        if not val:
            return []
        try:
            decoded = json.loads(val)
            if isinstance(decoded, list):
                return _to_tags(decoded)
        except Exception:
            pass
        return [val.lower()]
    if isinstance(raw, list):
        out: list[str] = []
        for item in raw:
            token = str(item or "").strip().lower()
            if token:
                out.append(token)
        return sorted(set(out))
    return [str(raw).strip().lower()]


def _build_hash(source_id: str, chunk_tag: str, text: str) -> str:
    payload = f"{source_id}|{chunk_tag}|{text}"
    return sha256(payload.encode("utf-8")).hexdigest()


def _normalized_record(record: dict[str, Any], now_ts: int) -> dict[str, Any]:
    source_id = str(record.get("source_id") or "").strip()
    text = str(record.get("text") or "").strip()
    if not source_id or not text:
        raise ValueError("record.source_id and record.text are required")
    chunk_tag = str(record.get("chunk_tag") or "full").strip().lower()[:64]
    tags_list = _to_tags(record.get("tags"))
    tags_json = json.dumps(tags_list)
    title = str(record.get("title") or "")[:512]
    canonical_title = str(record.get("canonical_title") or "")[:512]
    return {
        "source_id": source_id[:256],
        "item_id": _to_int(record.get("item_id"), 0),
        "kind": str(record.get("kind") or "movie").strip().lower()[:16],
        "chunk_tag": chunk_tag,
        "title": title,
        "canonical_title": canonical_title,
        "year": _to_int(record.get("year"), 0),
        "genres": str(record.get("genres") or "")[:512],
        "parental_rating": str(record.get("parental_rating") or "")[:32],
        "rating": _to_float(record.get("rating"), 0.0),
        "runtime": _to_int(record.get("runtime"), 0),
        "tags": tags_json[:4096],
        "updated_at": _to_int(record.get("updated_at"), now_ts),
        "text": text[:65000],
        "hash": str(record.get("hash") or _build_hash(source_id, chunk_tag, text))[:64],
        "embedding_model": str(record.get("embedding_model") or LOCAL_EMBEDDING_MODEL)[:64],
        "creation_date": _to_int(record.get("creation_date"), now_ts),
    }


def upsert_movietime_items(
    records: list[dict[str, Any]],
    collection_name: str | None = None,
    delete_first: bool = True,
    ip_address: str = "localhost",
    embedding_host: str = "localhost",
    embedding_port: int | None = None,
) -> dict[str, Any]:
    if not records:
        return {"inserted": 0, "deleted_source_ids": 0, "errors": []}

    alias = _alias("movietime_upsert")
    now_ts = int(datetime.now().timestamp())
    errors: list[str] = []

    normalized: list[dict[str, Any]] = []
    for idx, raw in enumerate(records):
        try:
            normalized.append(_normalized_record(dict(raw or {}), now_ts))
        except Exception as exc:
            errors.append(f"record[{idx}]: {exc}")

    if not normalized:
        return {"inserted": 0, "deleted_source_ids": 0, "errors": errors}

    raw_collection_name = _raw_collection_name(collection_name)
    try:
        connections.connect(alias, host=ip_address, port="19530")
        coll = _ensure_collection_schema(alias, raw_collection_name)
        try:
            coll.load()
        except Exception:
            pass

        source_ids = sorted({row["source_id"] for row in normalized})
        if delete_first and source_ids:
            for source_id in source_ids:
                try:
                    expr = f'source_id == "{_escape_expr(source_id)}"'
                    coll.delete(expr)
                except Exception as exc:
                    if "collection not loaded" not in str(exc).lower():
                        errors.append(f"delete source_id={source_id}: {exc}")

        rows: list[tuple[list[float], dict[str, Any]]] = []
        for i in range(0, len(normalized), EMBEDDING_BATCH_SIZE):
            batch = normalized[i : i + EMBEDDING_BATCH_SIZE]
            text_batch = [row["text"][:EMBEDDING_TEXT_MAX_CHARS] for row in batch]
            vectors = embed_text_to_vector(
                text_batch,
                LOCAL_EMBEDDING_MODEL,
                is_local=True,
                embedding_host=embedding_host,
                embedding_port=embedding_port,
            )
            validated = validate_embeddings(vectors, LOCAL_EMBEDDING_DIM)
            for vec, row in zip(validated, batch):
                if vec is None:
                    errors.append(f"embedding failed for source_id={row['source_id']} chunk={row['chunk_tag']}")
                    continue
                rows.append((vec, row))

        if not rows:
            return {"inserted": 0, "deleted_source_ids": len(source_ids), "errors": errors}

        fields = [
            "vector",
            "text",
            "hash",
            "source_id",
            "item_id",
            "kind",
            "chunk_tag",
            "title",
            "canonical_title",
            "year",
            "genres",
            "parental_rating",
            "rating",
            "runtime",
            "tags",
            "updated_at",
            "embedding_model",
            "creation_date",
        ]
        data = [
            [r[0] for r in rows],
            [r[1]["text"] for r in rows],
            [r[1]["hash"] for r in rows],
            [r[1]["source_id"] for r in rows],
            [r[1]["item_id"] for r in rows],
            [r[1]["kind"] for r in rows],
            [r[1]["chunk_tag"] for r in rows],
            [r[1]["title"] for r in rows],
            [r[1]["canonical_title"] for r in rows],
            [r[1]["year"] for r in rows],
            [r[1]["genres"] for r in rows],
            [r[1]["parental_rating"] for r in rows],
            [r[1]["rating"] for r in rows],
            [r[1]["runtime"] for r in rows],
            [r[1]["tags"] for r in rows],
            [r[1]["updated_at"] for r in rows],
            [r[1]["embedding_model"] for r in rows],
            [r[1]["creation_date"] for r in rows],
        ]
        coll.insert(data, fields=fields)

        return {
            "inserted": len(rows),
            "deleted_source_ids": len(source_ids),
            "collection": raw_collection_name.removeprefix("documents_"),
            "errors": errors,
        }
    finally:
        try:
            connections.disconnect(alias)
        except Exception:
            pass


def _tags_expr_clause(field_name: str, tags: list[str], op: str) -> str | None:
    if not tags:
        return None
    parts = [f'{field_name} like "%{_escape_expr(tag.lower())}%"' for tag in tags]
    if not parts:
        return None
    joiner = " and " if op == "all" else " or "
    return f"({joiner.join(parts)})"


def _build_filter_expr(filters: dict[str, Any] | None) -> str | None:
    if not isinstance(filters, dict):
        return None
    clauses: list[str] = []

    kind = filters.get("kind")
    if isinstance(kind, list):
        vals = [str(x).strip().lower() for x in kind if str(x).strip()]
        if vals:
            in_list = ",".join([f'"{_escape_expr(v)}"' for v in sorted(set(vals))])
            clauses.append(f"kind in [{in_list}]")
    elif kind:
        val = str(kind).strip().lower()
        clauses.append(f'kind == "{_escape_expr(val)}"')

    year_min = filters.get("yearMin")
    if year_min is not None:
        clauses.append(f"year >= {_to_int(year_min)}")
    year_max = filters.get("yearMax")
    if year_max is not None:
        clauses.append(f"year <= {_to_int(year_max)}")

    rating_min = filters.get("ratingMin")
    if rating_min is not None:
        clauses.append(f"rating >= {_to_float(rating_min)}")

    parental = filters.get("parentalRatings")
    if isinstance(parental, list):
        vals = [str(x).strip().upper() for x in parental if str(x).strip()]
        if vals:
            in_list = ",".join([f'"{_escape_expr(v)}"' for v in sorted(set(vals))])
            clauses.append(f"parental_rating in [{in_list}]")

    tags_all = _to_tags(filters.get("tagsAll"))
    tags_any = _to_tags(filters.get("tagsAny"))
    all_clause = _tags_expr_clause("tags", tags_all, op="all")
    any_clause = _tags_expr_clause("tags", tags_any, op="any")
    if all_clause:
        clauses.append(all_clause)
    if any_clause:
        clauses.append(any_clause)

    return " and ".join(clauses) if clauses else None


def _tag_boost_for_result(tags_json: str, boosts: dict[str, Any] | None) -> float:
    if not boosts:
        return 0.0
    try:
        tags = _to_tags(json.loads(tags_json) if tags_json else [])
    except Exception:
        tags = _to_tags(tags_json)
    if not tags:
        return 0.0
    total = 0.0
    for tag in tags:
        if tag in boosts:
            total += _to_float(boosts.get(tag), 0.0)
    return total


def search_movietime_items(
    query: str,
    collection_name: str | None = None,
    limit: int = 24,
    mode: str = "hybrid",
    filters: dict[str, Any] | None = None,
    tag_boosts: dict[str, Any] | None = None,
    ip_address: str = "localhost",
    embedding_host: str = "localhost",
    embedding_port: int | None = None,
) -> list[dict[str, Any]]:
    clean_query = str(query or "").strip()
    if not clean_query:
        return []

    alias = _alias("movietime_search")
    out: list[dict[str, Any]] = []
    raw_collection_name = _raw_collection_name(collection_name)
    try:
        connections.connect(alias, host=ip_address, port="19530")
        if not utility.has_collection(raw_collection_name, using=alias):
            return []
        coll = Collection(raw_collection_name, using=alias)
        try:
            coll.load()
        except Exception:
            pass

        field_names = {f.name for f in coll.schema.fields}
        expr = _build_filter_expr(filters)
        output_fields = [
            "text",
            "hash",
            "source_id",
            "item_id",
            "kind",
            "chunk_tag",
            "title",
            "canonical_title",
            "year",
            "genres",
            "parental_rating",
            "rating",
            "runtime",
            "tags",
            "updated_at",
            "embedding_model",
            "creation_date",
        ]
        output_fields = [f for f in output_fields if f in field_names]

        mode_norm = str(mode or "hybrid").strip().lower()
        use_bm25 = mode_norm in {"bm25", "sparse"} and "sparse" in field_names
        use_hybrid = mode_norm == "hybrid" and "sparse" in field_names and "vector" in field_names
        topk = min(max(int(limit) * 6, 60), MAX_QUERY_LIMIT)

        if use_hybrid:
            query_vec = embed_text_to_vector(
                [clean_query],
                LOCAL_EMBEDDING_MODEL,
                is_local=True,
                embedding_host=embedding_host,
                embedding_port=embedding_port,
            )
            validated = validate_embeddings(query_vec, LOCAL_EMBEDDING_DIM)
            if not validated or validated[0] is None:
                return []
            dense_req = AnnSearchRequest(
                data=[validated[0]],
                anns_field="vector",
                param={"metric_type": str(METRIC_TYPE or "L2").upper(), "params": {"nprobe": 16}},
                limit=topk,
                expr=expr,
            )
            sparse_req = AnnSearchRequest(
                data=[clean_query],
                anns_field="sparse",
                param={"metric_type": "BM25", "params": {}},
                limit=topk,
                expr=expr,
            )
            dense_weight = float(os.environ.get("VECTORSTORE_HYBRID_DENSE_WEIGHT", "0.65"))
            sparse_weight = float(os.environ.get("VECTORSTORE_HYBRID_SPARSE_WEIGHT", "0.35"))
            fusion = str(os.environ.get("VECTORSTORE_HYBRID_FUSION", "weighted")).strip().lower()
            if fusion == "rrf":
                ranker = RRFRanker(k=int(os.environ.get("VECTORSTORE_HYBRID_RRF_K", "60")))
            else:
                ranker = WeightedRanker(dense_weight, sparse_weight)
            results = coll.hybrid_search(
                reqs=[dense_req, sparse_req],
                rerank=ranker,
                limit=topk,
                output_fields=output_fields,
            )
            hits = results[0] if results else []
        else:
            if use_bm25:
                search_data = [clean_query]
                anns_field = "sparse"
                params = {"metric_type": "BM25", "params": {}}
            else:
                query_vec = embed_text_to_vector(
                    [clean_query],
                    LOCAL_EMBEDDING_MODEL,
                    is_local=True,
                    embedding_host=embedding_host,
                    embedding_port=embedding_port,
                )
                validated = validate_embeddings(query_vec, LOCAL_EMBEDDING_DIM)
                if not validated or validated[0] is None:
                    return []
                search_data = [validated[0]]
                anns_field = "vector"
                params = {"metric_type": str(METRIC_TYPE or "L2").upper(), "params": {"nprobe": 16}}
            search_results = coll.search(
                data=search_data,
                anns_field=anns_field,
                param=params,
                limit=topk,
                output_fields=output_fields,
                expr=expr,
            )
            hits = search_results[0] if search_results else []

        by_source: dict[str, dict[str, Any]] = {}
        for hit in hits:
            source_id = str(hit.get("source_id") or "")
            if not source_id:
                continue
            distance = float(hit.distance if hit.distance is not None else 1e18)
            tags_json = str(hit.get("tags") or "[]")
            boost = _tag_boost_for_result(tags_json, tag_boosts)
            score = (-distance) + boost
            row = {
                "id": hit.id,
                "distance": distance,
                "score": score,
                "text": hit.get("text") or "",
                "hash": hit.get("hash") or "",
                "source_id": source_id,
                "item_id": _to_int(hit.get("item_id"), 0),
                "kind": (hit.get("kind") or ""),
                "chunk_tag": (hit.get("chunk_tag") or ""),
                "title": (hit.get("title") or ""),
                "canonical_title": (hit.get("canonical_title") or ""),
                "year": _to_int(hit.get("year"), 0),
                "genres": (hit.get("genres") or ""),
                "parental_rating": (hit.get("parental_rating") or ""),
                "rating": _to_float(hit.get("rating"), 0.0),
                "runtime": _to_int(hit.get("runtime"), 0),
                "tags": tags_json,
                "updated_at": _to_int(hit.get("updated_at"), 0),
                "embedding_model": (hit.get("embedding_model") or ""),
                "creation_date": _to_int(hit.get("creation_date"), 0),
            }
            prev = by_source.get(source_id)
            if prev is None or row["score"] > prev["score"]:
                by_source[source_id] = row

        out = sorted(by_source.values(), key=lambda item: float(item.get("score", -1e18)), reverse=True)[: max(1, int(limit))]
        return out
    finally:
        try:
            connections.disconnect(alias)
        except Exception:
            pass
