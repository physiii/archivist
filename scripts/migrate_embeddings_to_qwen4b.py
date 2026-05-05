#!/usr/bin/env python3
"""
Re-embed Milvus text collections from dim=4096 (Qwen3-Embedding-8B) to dim=2560
(Qwen3-Embedding-4B on TEI).

Run inside the archivist container so it shares the same Milvus + embed-gateway
network reachability as the live service:

    docker exec -it archivist python /app/scripts/migrate_embeddings_to_qwen4b.py [--dry-run]
    docker exec -it archivist python /app/scripts/migrate_embeddings_to_qwen4b.py --cutover

Two phases, gated by explicit flags so nothing destructive runs without intent:

  Phase 1 (default)  -- build `<name>_v2` at dim 2560, re-embed from each row's
                        primary text field, insert, build index. Idempotent via
                        a progress JSON; rerun to resume.

  Phase 2 (--cutover) -- for each migrated collection, rename old -> `<name>_v1_4096`
                        and `<name>_v2` -> original name. Atomic per-collection.

Constraints: one collection at a time, batch size tuned to avoid starving the
live search workload. Only collections whose vector field dim == 4096 are
touched; 1024/1536/512 collections (CLIP, legacy openai) are skipped.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

# Allow running from /app inside the container
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pymilvus import (  # type: ignore[import-not-found]
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    Function,
    FunctionType,
    connections,
    utility,
)

from utils import embed_text_to_vector

LOGGER = logging.getLogger("migrate_embeddings")
TARGET_DIM = 2560
SOURCE_DIM = 4096
V2_SUFFIX = "_v2_qwen4b"
ARCHIVE_SUFFIX = "_v1_qwen8b_4096"
DEFAULT_BATCH = 128
PROGRESS_PATH = Path(os.getenv("MIGRATION_PROGRESS_PATH", "/data/media_pipeline/embedding_migration.json"))

TEXT_FIELD_CANDIDATES = ("text", "snippet", "content", "body")


def connect() -> None:
    host = os.getenv("MILVUS_HOST", "host.docker.internal")
    port = os.getenv("MILVUS_PORT", "19530")
    connections.connect(alias="default", host=host, port=port)
    LOGGER.info("connected to milvus at %s:%s", host, port)


def load_progress() -> dict[str, Any]:
    if PROGRESS_PATH.exists():
        try:
            return json.loads(PROGRESS_PATH.read_text())
        except Exception as exc:
            LOGGER.warning("could not parse progress file %s: %s", PROGRESS_PATH, exc)
    return {}


def save_progress(state: dict[str, Any]) -> None:
    PROGRESS_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = PROGRESS_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2, sort_keys=True))
    tmp.replace(PROGRESS_PATH)


def list_4096_collections() -> list[tuple[str, int]]:
    """Return [(name, vector_field_dim), ...] for source collections at dim 4096.

    Skips anything already tagged _v2_qwen4b or _v1_qwen8b_4096.
    """
    names = utility.list_collections()
    out: list[tuple[str, int]] = []
    for name in sorted(names):
        if name.endswith(V2_SUFFIX) or name.endswith(ARCHIVE_SUFFIX):
            continue
        try:
            coll = Collection(name)
        except Exception as exc:
            LOGGER.warning("cannot open %s: %s", name, exc)
            continue
        vec_dim = _vector_dim(coll)
        if vec_dim == SOURCE_DIM:
            out.append((name, vec_dim))
    return out


def _vector_dim(coll: Collection) -> int | None:
    for field in coll.schema.fields:
        if field.dtype in (DataType.FLOAT_VECTOR, DataType.BINARY_VECTOR):
            try:
                return int(field.params.get("dim"))
            except Exception:
                return None
    return None


def _rebuild_schema_with_new_dim(src: Collection, new_dim: int) -> CollectionSchema:
    """Copy source schema but swap FLOAT_VECTOR dim to new_dim.

    Force auto_id=True on any primary INT64 field (archivist's convention;
    rows don't carry externally-referenced ids). This also lets inserts omit
    the primary key.
    """
    new_fields: list[FieldSchema] = []
    for field in src.schema.fields:
        if field.dtype == DataType.FLOAT_VECTOR:
            new_fields.append(
                FieldSchema(
                    name=field.name,
                    dtype=DataType.FLOAT_VECTOR,
                    dim=new_dim,
                    is_primary=field.is_primary,
                )
            )
            continue
        kwargs: dict[str, Any] = {
            "name": field.name,
            "dtype": field.dtype,
            "is_primary": field.is_primary,
        }
        if field.is_primary and field.dtype == DataType.INT64:
            kwargs["auto_id"] = True
        elif field.auto_id:
            kwargs["auto_id"] = True
        params = dict(field.params or {})
        for key in ("max_length", "max_capacity", "element_type"):
            if key in params:
                kwargs[key] = params[key]
        if field.dtype in (DataType.VARCHAR,) and "max_length" not in kwargs:
            kwargs["max_length"] = 65535
        if field.dtype == DataType.ARRAY and "element_type" not in kwargs:
            # conservative default
            kwargs["element_type"] = DataType.VARCHAR
            kwargs["max_length"] = 1024
        if field.dtype == DataType.VARCHAR and bool(params.get("enable_analyzer")):
            kwargs["enable_analyzer"] = True
        new_fields.append(FieldSchema(**kwargs))
    description = f"{src.description or src.name} (dim={new_dim})"

    # Copy any BM25 / transform Functions so SPARSE_FLOAT_VECTOR fields are
    # auto-populated from text on insert (matches archivist indexing_service
    # setup). pymilvus exposes these as dicts on schema.functions, so we
    # reconstruct Function objects from the stored metadata.
    rebuilt_functions: list[Function] = []
    for raw in getattr(src.schema, "functions", None) or []:
        raw_dict = raw if isinstance(raw, dict) else getattr(raw, "to_dict", lambda: {})()
        fn_type_value = raw_dict.get("type")
        if isinstance(fn_type_value, FunctionType):
            fn_type = fn_type_value
        else:
            try:
                fn_type = FunctionType(fn_type_value)
            except Exception:
                LOGGER.warning("%s: unknown function type %r; skipping", src.name, fn_type_value)
                continue
        rebuilt_functions.append(
            Function(
                name=raw_dict.get("name", "fn"),
                function_type=fn_type,
                input_field_names=raw_dict.get("input_field_names", []),
                output_field_names=raw_dict.get("output_field_names", []),
                description=raw_dict.get("description", "") or "",
                params=raw_dict.get("params", {}) or {},
            )
        )

    schema_kwargs: dict[str, Any] = {"fields": new_fields, "description": description}
    if rebuilt_functions:
        schema_kwargs["functions"] = rebuilt_functions
    return CollectionSchema(**schema_kwargs)


def _pick_text_field(coll: Collection) -> str | None:
    names = {f.name for f in coll.schema.fields}
    for candidate in TEXT_FIELD_CANDIDATES:
        if candidate in names:
            return candidate
    return None


def _pick_vector_field(coll: Collection) -> str:
    for field in coll.schema.fields:
        if field.dtype == DataType.FLOAT_VECTOR:
            return field.name
    raise RuntimeError(f"{coll.name} has no FLOAT_VECTOR field")


def _non_vector_output_fields(coll: Collection, vector_field: str) -> list[str]:
    out: list[str] = []
    for field in coll.schema.fields:
        if field.name == vector_field:
            continue
        # Sparse vectors from BM25 Functions are autogenerated; skip — Milvus will
        # regenerate them on insert when the Function is bound.
        if field.dtype == DataType.SPARSE_FLOAT_VECTOR:
            continue
        if field.is_primary and field.auto_id:
            continue
        out.append(field.name)
    return out


def _index_params(coll: Collection, vector_field: str) -> dict[str, Any]:
    """Find the existing vector index params so the new collection matches."""
    try:
        for index in coll.indexes:
            if index.field_name == vector_field:
                params = dict(index.params or {})
                metric = params.pop("metric_type", None) or params.get("metric_type")
                index_type = params.pop("index_type", None) or params.get("index_type", "IVF_SQ8")
                inner = params.get("params") if "params" in params else params
                return {
                    "index_type": index_type,
                    "metric_type": metric or os.getenv("METRIC_TYPE", "COSINE"),
                    "params": inner or {"nlist": int(os.getenv("VECTORSTORE_NLIST", "4096"))},
                }
    except Exception as exc:
        LOGGER.warning("could not read existing index on %s: %s", coll.name, exc)
    return {
        "index_type": os.getenv("VECTORSTORE_INDEX_TYPE", "IVF_SQ8"),
        "metric_type": os.getenv("METRIC_TYPE", "COSINE"),
        "params": {"nlist": int(os.getenv("VECTORSTORE_NLIST", "4096"))},
    }


def migrate_collection(name: str, *, dry_run: bool, batch_size: int, progress: dict[str, Any]) -> bool:
    src = Collection(name)
    src.load()
    vector_field = _pick_vector_field(src)
    text_field = _pick_text_field(src)
    if text_field is None:
        LOGGER.warning("%s has no recognized text field (%s); skipping",
                       name, ",".join(TEXT_FIELD_CANDIDATES))
        return False

    output_fields = _non_vector_output_fields(src, vector_field)
    if text_field not in output_fields:
        output_fields.append(text_field)

    target_name = f"{name}{V2_SUFFIX}"
    src_count = src.num_entities
    LOGGER.info("[%s] source rows=%d text_field=%s -> %s",
                name, src_count, text_field, target_name)

    if dry_run:
        return False

    if utility.has_collection(target_name):
        tgt = Collection(target_name)
        if tgt.num_entities >= src_count:
            LOGGER.info("[%s] target already has %d rows; skipping", name, tgt.num_entities)
            progress.setdefault("done", {})[name] = {"rows": tgt.num_entities}
            save_progress(progress)
            return True
    else:
        schema = _rebuild_schema_with_new_dim(src, TARGET_DIM)
        tgt = Collection(name=target_name, schema=schema)
        LOGGER.info("[%s] created target %s at dim=%d", name, target_name, TARGET_DIM)

    # Stream pk-ordered pages via query_iterator, re-embed, insert.
    pk_field = next((f.name for f in src.schema.fields if f.is_primary), "id")
    iterator = src.query_iterator(batch_size=batch_size,
                                  expr="",
                                  output_fields=output_fields + [pk_field])

    migrated = 0
    started = time.perf_counter()
    while True:
        rows = iterator.next()
        if not rows:
            break
        texts = [str(row.get(text_field) or "") for row in rows]
        # Skip entirely-empty rows (still insert placeholder? No: drop them — they
        # contribute nothing to retrieval and re-embedding '' is wasted GPU time.)
        keep_idx = [i for i, t in enumerate(texts) if t.strip()]
        if not keep_idx:
            continue
        texts_keep = [texts[i] for i in keep_idx]
        try:
            vectors = embed_text_to_vector(
                texts_keep,
                model=os.getenv("LOCAL_EMBEDDING_MODEL", "local-default"),
            )
        except Exception as exc:
            LOGGER.error("[%s] embed call failed at offset %d: %s", name, migrated, exc)
            raise

        if len(vectors) != len(texts_keep):
            LOGGER.error("[%s] embed returned %d vectors for %d texts",
                         name, len(vectors), len(texts_keep))
            raise RuntimeError("embed count mismatch")

        # Build an insert dict keyed by field name.
        payload: dict[str, list[Any]] = {vector_field: vectors}
        for field_name in output_fields:
            payload[field_name] = [rows[i].get(field_name) for i in keep_idx]

        tgt.insert([payload[f.name]
                    for f in tgt.schema.fields
                    if f.name in payload and not (f.is_primary and f.auto_id)],
                   fields=[f.name for f in tgt.schema.fields
                           if f.name in payload and not (f.is_primary and f.auto_id)])
        migrated += len(keep_idx)
        if migrated % (batch_size * 10) == 0:
            elapsed = time.perf_counter() - started
            rate = migrated / max(elapsed, 0.001)
            LOGGER.info("[%s] %d / %d rows (%.1f rows/s)", name, migrated, src_count, rate)
            progress.setdefault("in_progress", {})[name] = {"rows": migrated}
            save_progress(progress)

    iterator.close()
    try:
        tgt.flush()
    except Exception as exc:
        LOGGER.warning("[%s] flush failed: %s", name, exc)

    index_params = _index_params(src, vector_field)
    try:
        tgt.create_index(field_name=vector_field, index_params=index_params)
    except Exception as exc:
        LOGGER.warning("[%s] dense index failed: %s", name, exc)

    # BM25 Function outputs a SPARSE_FLOAT_VECTOR that also needs an index
    # before load() will succeed.
    for field in tgt.schema.fields:
        if field.dtype == DataType.SPARSE_FLOAT_VECTOR:
            try:
                tgt.create_index(
                    field_name=field.name,
                    index_params={
                        "index_type": "SPARSE_INVERTED_INDEX",
                        "metric_type": "BM25",
                        "params": {},
                    },
                )
            except Exception as exc:
                LOGGER.warning("[%s] sparse index (%s) failed: %s",
                               name, field.name, exc)

    try:
        tgt.load()
    except Exception as exc:
        LOGGER.warning("[%s] load failed: %s", name, exc)

    elapsed = time.perf_counter() - started
    LOGGER.info("[%s] done: migrated %d rows in %.1fs -> %s",
                name, migrated, elapsed, target_name)
    progress.setdefault("done", {})[name] = {
        "rows": migrated,
        "source_rows": src_count,
        "elapsed_s": round(elapsed, 1),
    }
    progress.get("in_progress", {}).pop(name, None)
    save_progress(progress)
    return True


def cutover(progress: dict[str, Any]) -> None:
    done = progress.get("done", {})
    if not done:
        LOGGER.error("no migrated collections in progress file; run re-embed first")
        sys.exit(2)
    for name in sorted(done.keys()):
        target = f"{name}{V2_SUFFIX}"
        archive = f"{name}{ARCHIVE_SUFFIX}"
        if not utility.has_collection(target):
            LOGGER.warning("[%s] target %s missing; skipping", name, target)
            continue
        if not utility.has_collection(name):
            LOGGER.warning("[%s] source missing; skipping rename", name)
            continue
        LOGGER.info("[%s] rename %s -> %s; %s -> %s",
                    name, name, archive, target, name)
        utility.rename_collection(name, archive)
        utility.rename_collection(target, name)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="list collections to migrate, do not build or insert")
    parser.add_argument("--cutover", action="store_true",
                        help="rename migrated collections into production names")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH)
    parser.add_argument("--only", action="append", default=[],
                        help="restrict to these collection names (repeatable)")
    args = parser.parse_args()

    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(message)s",
    )

    connect()
    progress = load_progress()

    if args.cutover:
        cutover(progress)
        return

    sources = list_4096_collections()
    if args.only:
        keep = set(args.only)
        sources = [(n, d) for n, d in sources if n in keep]

    LOGGER.info("found %d collections at dim=%d", len(sources), SOURCE_DIM)
    for name, dim in sources:
        LOGGER.info("  - %s (dim=%d)", name, dim)

    if args.dry_run:
        for name, _ in sources:
            migrate_collection(name, dry_run=True, batch_size=args.batch_size, progress=progress)
        return

    for name, _ in sources:
        try:
            migrate_collection(name, dry_run=False, batch_size=args.batch_size, progress=progress)
        except Exception as exc:
            LOGGER.exception("[%s] migration failed: %s", name, exc)
            continue


if __name__ == "__main__":
    main()
