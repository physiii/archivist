import hashlib
import json
import os
import random
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import time

import requests


BASE_URL = os.environ.get("VECTORSTORE_BASE_URL", "http://127.0.0.1:5050").rstrip("/")


def _deterministic_embedding(text: str, dim: int = 4096) -> list[float]:
    h = hashlib.sha256(text.encode("utf-8")).digest()
    seed = int.from_bytes(h[:8], "big", signed=False)
    rng = random.Random(seed)
    return [rng.random() for _ in range(dim)]


class _EmbedHandler(BaseHTTPRequestHandler):
    def do_POST(self):  # noqa: N802
        if self.path not in {"/embed", "/v1/embeddings", "/embed_batch"}:
            self.send_response(404)
            self.end_headers()
            return
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8"))
        except Exception:
            payload = {}
        if self.path == "/embed":
            text = payload.get("text") or ""
            body = json.dumps({"embedding": _deterministic_embedding(str(text))}).encode("utf-8")
        else:
            texts = payload.get("texts") or payload.get("input") or []
            if isinstance(texts, str):
                texts = [texts]
            embeddings = [_deterministic_embedding(str(t)) for t in texts]
            if self.path == "/v1/embeddings":
                body = json.dumps(
                    {"data": [{"index": idx, "embedding": embedding} for idx, embedding in enumerate(embeddings)]}
                ).encode("utf-8")
            else:
                body = json.dumps({"embeddings": embeddings}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):  # noqa: D401, ARG002
        return


class FakeEmbeddingServer:
    def __init__(self):
        self.httpd: ThreadingHTTPServer | None = None
        self.thread: threading.Thread | None = None
        self.port: int | None = None

    def start(self) -> int:
        self.httpd = ThreadingHTTPServer(("0.0.0.0", 0), _EmbedHandler)
        self.port = int(self.httpd.server_address[1])
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        return self.port

    def stop(self) -> None:
        if self.httpd is not None:
            self.httpd.shutdown()


def _post(path: str, payload: dict, timeout: float = 90):
    response = requests.post(f"{BASE_URL}{path}", json=payload, timeout=timeout)
    try:
        body = response.json()
    except Exception:
        body = {"_raw": response.text}
    if response.status_code >= 400:
        raise RuntimeError(f"HTTP {response.status_code}: {body}")
    return body


def test_movietime_upsert_and_filtered_search():
    embed = FakeEmbeddingServer()
    port = embed.start()
    collection = f"movietime_test_{uuid.uuid4().hex[:10]}"
    try:
        upsert_payload = {
            "collection": collection,
            "delete_first": True,
            "embedding_host": "host.docker.internal",
            "embedding_port": port,
            "records": [
                {
                    "source_id": "movietime:item:1001",
                    "item_id": 1001,
                    "kind": "movie",
                    "chunk_tag": "summary",
                    "title": "The Wild Robot",
                    "canonical_title": "The Wild Robot",
                    "year": 2024,
                    "genres": "Animation, Family",
                    "parental_rating": "PG",
                    "rating": 7.9,
                    "runtime": 102,
                    "tags": ["kind:movie", "genre:animation", "genre:family"],
                    "updated_at": 1700000000,
                    "text": "A robot stranded in the wilderness learns to survive among animals.",
                },
                {
                    "source_id": "movietime:item:1002",
                    "item_id": 1002,
                    "kind": "movie",
                    "chunk_tag": "summary",
                    "title": "A Clockwork Orange",
                    "canonical_title": "A Clockwork Orange",
                    "year": 1971,
                    "genres": "Crime, Sci-Fi",
                    "parental_rating": "NC-17",
                    "rating": 8.2,
                    "runtime": 136,
                    "tags": ["kind:movie", "genre:crime", "genre:sci-fi"],
                    "updated_at": 1700000000,
                    "text": "In a dystopian future, delinquent youth undergoes aversion therapy.",
                },
            ],
        }
        upsert_result = _post("/api/movietime/items/upsert", upsert_payload, timeout=120)
        assert upsert_result.get("inserted", 0) >= 2

        results = []
        deadline = time.time() + 25
        while time.time() < deadline and not results:
            search_result = _post(
                "/api/movietime/items/search",
                {
                    "collection": collection,
                    "query": "robot wilderness family animation",
                    "limit": 10,
                    "mode": "dense",
                    "embedding_host": "host.docker.internal",
                    "embedding_port": port,
                    "filters": {"kind": "movie", "tagsAll": ["genre:animation"]},
                    "tagBoosts": {"genre:animation": 0.5},
                },
                timeout=120,
            )
            results = search_result.get("results") or []
            if results:
                break
            time.sleep(1)
        assert results
        assert results[0].get("item_id") == 1001
        assert all(r.get("kind") == "movie" for r in results)
    finally:
        try:
            _post(f"/api/collections/{collection}/drop", {}, timeout=60)
        except Exception:
            pass
        embed.stop()
