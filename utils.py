from __future__ import annotations

import os
import re
import logging
from hashlib import sha256
from pathlib import Path
from typing import Iterable

import requests
from pymilvus import Collection, utility

DEFAULT_EMBEDDING_MODEL = os.getenv("DEFAULT_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
LOCAL_EMBEDDING_MODEL = os.getenv("LOCAL_EMBEDDING_MODEL", "local-default")
LOCAL_EMBEDDING_DIM = int(os.getenv("LOCAL_EMBEDDING_DIM", "4096"))

SNIPPET_LENGTH = int(os.getenv("SNIPPET_LENGTH", "65535"))
INDEX_TYPE = os.getenv("INDEX_TYPE", "IVF_FLAT")
METRIC_TYPE = os.getenv("METRIC_TYPE", "COSINE")
NLIST = int(os.getenv("NLIST", "1024"))

EMBEDDING_DIMENSIONS: dict[str, int] = {
    DEFAULT_EMBEDDING_MODEL: LOCAL_EMBEDDING_DIM,
    LOCAL_EMBEDDING_MODEL: LOCAL_EMBEDDING_DIM,
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
}

def embed_text_to_vector(
    texts: list[str],
    model: str,
    is_local: bool = True,
    ip_address: str | None = None,
    embedding_host: str | None = None,
    embedding_port: int | str | None = None,
) -> list[list[float]]:
    if not texts:
        return []
    host = str(embedding_host or ip_address or os.getenv("EMBEDDING_HOST", "localhost"))
    port = int(embedding_port or os.getenv("EMBEDDING_PORT", "8000"))
    # First try per-text /embed endpoint expecting {"text": "..."}.
    embed_url = f"http://{host}:{port}/embed"
    out: list[list[float]] = []
    for text in texts:
        try:
            response = requests.post(embed_url, json={"text": text}, timeout=60)
            if response.status_code >= 300:
                out = []
                break
            body = response.json()
            embedding = body.get("embedding")
            if not isinstance(embedding, list):
                out = []
                break
            out.append([float(v) for v in embedding])
        except Exception:
            out = []
            break
    if len(out) == len(texts):
        return out

    # Fallback to OpenAI-compatible endpoint in batch mode.
    v1_url = f"http://{host}:{port}/v1/embeddings"
    v1_payloads = [{"input": texts}]
    # Most local embedding gateways reject unknown model labels; only pass
    # model when caller provided a non-default explicit model value.
    if model and str(model).strip() not in {LOCAL_EMBEDDING_MODEL, ""}:
        v1_payloads.insert(0, {"input": texts, "model": model})
    for payload in v1_payloads:
        try:
            response = requests.post(v1_url, json=payload, timeout=60)
            if response.status_code >= 300:
                continue
            body = response.json()
            data = body.get("data")
            if not isinstance(data, list):
                continue
            vectors: list[list[float]] = []
            for item in data:
                embedding = item.get("embedding") if isinstance(item, dict) else None
                if not isinstance(embedding, list):
                    vectors = []
                    break
                vectors.append([float(v) for v in embedding])
            if len(vectors) == len(texts):
                return vectors
        except Exception:
            continue

    message = (
        f"Embedding request failed for host={host} port={port}. "
        "Checked /v1/embeddings and /embed; no valid vector payload returned."
    )
    logging.error(message)
    raise RuntimeError(message)


def validate_embeddings(vectors: list[list[float]], embedding_dim: int) -> list[list[float] | None]:
    out: list[list[float] | None] = []
    for vector in vectors or []:
        if not isinstance(vector, list):
            out.append(None)
            continue
        if len(vector) < embedding_dim:
            out.append(None)
            continue
        if len(vector) > embedding_dim:
            out.append([float(v) for v in vector[:embedding_dim]])
            continue
        out.append([float(v) for v in vector])
    return out


def file_hash(path: str) -> str:
    digest = sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def get_creation_date(path: str) -> int:
    return int(Path(path).stat().st_mtime)


def count_files(root: str) -> int:
    count = 0
    for _, _, files in os.walk(root):
        count += len(files)
    return count


def load_files(root: str, recursive: bool = True) -> Iterable[tuple[str, str, int]]:
    if recursive:
        for dirpath, _, files in os.walk(root):
            for name in files:
                path = str(Path(dirpath) / name)
                try:
                    yield path, file_hash(path), get_creation_date(path)
                except Exception:
                    continue
        return
    for item in Path(root).iterdir():
        if item.is_file():
            path = str(item)
            try:
                yield path, file_hash(path), get_creation_date(path)
            except Exception:
                continue


def ensure_collection_exists(collection_name: str, schema) -> Collection:
    if utility.has_collection(collection_name):
        return Collection(name=collection_name)
    return Collection(name=collection_name, schema=schema)


def delete_old_entries(collection: Collection, path: str) -> None:
    escaped = path.replace("\\", "\\\\").replace('"', '\\"')
    expr = f'path == "{escaped}"'
    try:
        collection.delete(expr)
    except Exception:
        pass


def process_file(path: str) -> list[str]:
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []
    chunks = [part.strip() for part in re.split(r"\n\s*\n+", text) if part.strip()]
    return chunks if chunks else ([text.strip()] if text.strip() else [])


def extract_snippet(text: str) -> str:
    return str(text or "")[:SNIPPET_LENGTH]


def process_and_insert_lines(
    path: str,
    collection: Collection,
    embedding_model: str,
    embedding_dim: int,
    is_local: bool,
    embedding_host: str | None = None,
    embedding_port: int | str | None = None,
) -> None:
    try:
        lines = [line.strip() for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines() if line.strip()]
    except Exception:
        return
    if not lines:
        return
    vectors = validate_embeddings(
        embed_text_to_vector(lines, embedding_model, is_local=is_local, embedding_host=embedding_host, embedding_port=embedding_port),
        embedding_dim,
    )
    rows = [(line, vector) for line, vector in zip(lines, vectors) if vector is not None]
    if not rows:
        return
    fh = file_hash(path)
    created = get_creation_date(path)
    snippets = [extract_snippet(line) for line, _ in rows]
    vecs = [vector for _, vector in rows]
    fields = ["vector", "path", "snippet", "filehash", "embedding_model", "creation_date"]
    data = [
        vecs,
        [path] * len(rows),
        snippets,
        [fh] * len(rows),
        [embedding_model] * len(rows),
        [created] * len(rows),
    ]
    collection.insert(data, fields=fields)
