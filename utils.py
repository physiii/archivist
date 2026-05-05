from __future__ import annotations

import os
import re
import logging
import threading
from hashlib import sha256
from pathlib import Path
from typing import Iterable

import requests
from requests.adapters import HTTPAdapter
from pymilvus import Collection, utility

DEFAULT_EMBEDDING_MODEL = os.getenv("DEFAULT_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
LOCAL_EMBEDDING_MODEL = os.getenv("LOCAL_EMBEDDING_MODEL", "local-default")
LOCAL_EMBEDDING_DIM = int(os.getenv("LOCAL_EMBEDDING_DIM", "2560"))

SNIPPET_LENGTH = int(os.getenv("SNIPPET_LENGTH", "65535"))
INDEX_TYPE = os.getenv("VECTORSTORE_INDEX_TYPE") or os.getenv("INDEX_TYPE", "IVF_FLAT")
METRIC_TYPE = os.getenv("METRIC_TYPE", "COSINE")
NLIST = int(os.getenv("VECTORSTORE_NLIST") or os.getenv("NLIST", "1024"))

EMBEDDING_DIMENSIONS: dict[str, int] = {
    DEFAULT_EMBEDDING_MODEL: LOCAL_EMBEDDING_DIM,
    LOCAL_EMBEDDING_MODEL: LOCAL_EMBEDDING_DIM,
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
}

_embed_session_local = threading.local()


def _embedding_session() -> requests.Session:
    session = getattr(_embed_session_local, "session", None)
    if session is None:
        session = requests.Session()
        adapter = HTTPAdapter(pool_connections=8, pool_maxsize=32, max_retries=0, pool_block=False)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        _embed_session_local.session = session
    return session


def _post_batch_embeddings(
    session: requests.Session,
    url: str,
    texts: list[str],
    model: str,
) -> list[list[float]] | None:
    payloads = [{"input": texts}]
    if model and str(model).strip() not in {LOCAL_EMBEDDING_MODEL, ""}:
        payloads.insert(0, {"input": texts, "model": model})
    for payload in payloads:
        try:
            response = session.post(url, json=payload, timeout=60)
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
    return None


def _post_single_embeddings(
    session: requests.Session,
    url: str,
    texts: list[str],
) -> list[list[float]] | None:
    out: list[list[float]] = []
    for text in texts:
        try:
            response = session.post(url, json={"text": text}, timeout=60)
            if response.status_code >= 300:
                return None
            body = response.json()
            embedding = body.get("embedding")
            if not isinstance(embedding, list):
                return None
            out.append([float(v) for v in embedding])
        except Exception:
            return None
    return out if len(out) == len(texts) else None

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
    session = _embedding_session()
    embed_url = f"http://{host}:{port}/embed"
    v1_url = f"http://{host}:{port}/v1/embeddings"

    if len(texts) > 1:
        batched = _post_batch_embeddings(session, v1_url, texts, model)
        if batched is not None:
            return batched

    singles = _post_single_embeddings(session, embed_url, texts)
    if singles is not None:
        return singles

    if len(texts) == 1:
        batched = _post_batch_embeddings(session, v1_url, texts, model)
        if batched is not None:
            return batched

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
