import hashlib
import json
import os
import random
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import requests


BASE_URL = os.environ.get("VECTORSTORE_BASE_URL", "http://127.0.0.1:5050").rstrip("/")


def _deterministic_embedding(text: str, dim: int = 1024) -> list[float]:
    h = hashlib.sha256(text.encode("utf-8")).digest()
    # Expand the hash into dim floats in [0, 1).
    out: list[float] = []
    seed = int.from_bytes(h[:8], "big", signed=False)
    rng = random.Random(seed)
    for _ in range(dim):
        out.append(rng.random())
    return out


class _EmbedHandler(BaseHTTPRequestHandler):
    def do_POST(self):  # noqa: N802 - stdlib handler API
        if self.path != "/embed_batch":
            self.send_response(404)
            self.end_headers()
            return
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8"))
        except Exception:
            payload = {}
        texts = payload.get("texts") or []
        embeddings = [_deterministic_embedding(str(t)) for t in texts]
        body = json.dumps({"embeddings": embeddings}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):  # noqa: D401 - keep quiet
        return


class FakeEmbeddingServer:
    def __init__(self):
        self.httpd: ThreadingHTTPServer | None = None
        self.thread: threading.Thread | None = None
        self.port: int | None = None

    def start(self):
        self.httpd = ThreadingHTTPServer(("0.0.0.0", 0), _EmbedHandler)
        self.port = int(self.httpd.server_address[1])
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        return self.port

    def stop(self):
        if self.httpd is not None:
            self.httpd.shutdown()


def _post(path: str, payload: dict, timeout: float = 120):
    r = requests.post(f"{BASE_URL}{path}", json=payload, timeout=timeout)
    try:
        body = r.json()
    except Exception:
        body = {"_raw": r.text}
    if r.status_code >= 400:
        raise RuntimeError(f"HTTP {r.status_code}: {body}")
    return body


def _poll_search(collection: str, token: str, embedding_port: int, mode: str, timeout_s: float = 45):
    deadline = time.time() + timeout_s
    last = None
    while time.time() < deadline:
        last = _post(
            f"/api/collections/{collection}/search",
            {
                "query": token,
                "limit": 5,
                "mode": mode,
                "embedding_host": "host.docker.internal",
                "embedding_port": embedding_port,
            },
            timeout=120,
        )
        results = last.get("results") or []
        if any(token in (r.get("text") or "") for r in results):
            return last
        time.sleep(1.0)
    raise AssertionError(f"Timed out waiting for {mode} search to find token. last={last}")


def test_insert_and_search_dense_bm25_hybrid():
    server = FakeEmbeddingServer()
    port = server.start()
    collection = f"pytest_{uuid.uuid4().hex[:10]}"
    try:
        token = f"uniqtoken_{uuid.uuid4().hex}"
        text = f"uuid: 00000000-0000-0000-0000-000000000000\nname: {token}\ndescription: hello vectorstore\n"

        _post(
            f"/api/collections/{collection}/insert-text",
            {
                "text": text,
                "model": "local_model",
                "chunk_size": 20000,
                "overlap": 0,
                "embedding_host": "host.docker.internal",
                "embedding_port": port,
            },
            timeout=120,
        )

        _poll_search(collection, token, port, mode="dense", timeout_s=60)
        _poll_search(collection, token, port, mode="bm25", timeout_s=60)
        _poll_search(collection, token, port, mode="hybrid", timeout_s=60)
    finally:
        try:
            _post(f"/api/collections/{collection}/drop", {}, timeout=60)
        except Exception:
            pass
        server.stop()

