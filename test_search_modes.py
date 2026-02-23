import os
import time
import uuid
import requests


VECTORSTORE_URL = os.environ.get("VECTORSTORE_URL", "http://127.0.0.1:5050/vectorstore").strip()


def post(payload):
    r = requests.post(VECTORSTORE_URL, json=payload, timeout=120)
    try:
        body = r.json()
    except Exception:
        body = {"_raw": r.text}
    if r.status_code >= 400:
        raise RuntimeError(f"HTTP {r.status_code}: {body}")
    return body


def poll_search(payload, must_contain, timeout_s=30):
    deadline = time.time() + timeout_s
    last = None
    while time.time() < deadline:
        last = post(payload)
        results = last.get("results") or []
        if any(must_contain in (r.get("text") or "") for r in results):
            return last
        time.sleep(1.0)
    raise AssertionError(f"Timed out waiting for search to find '{must_contain}'. Last={last}")


def main():
    collection = f"needl_test_{uuid.uuid4().hex[:10]}"
    token = f"uniqtoken_{uuid.uuid4().hex}"
    text = f"uuid: 00000000-0000-0000-0000-000000000000\\nname: {token}\\ndescription: the quick brown fox jumps over the lazy dog\\n"

    # Load (dense embeddings path, uses local embedding server via the wrapper)
    post(
        {
            "type": "load",
            "collection": collection,
            "model": "local_model",
            "text": text,
            "chunk_size": 20000,
            "overlap": 0,
            "line_by_line": False,
            "debug": True,
        }
    )

    # Dense search should find it quickly (same exact token)
    poll_search(
        {
            "type": "search",
            "collection": collection,
            "query": token,
            "limit": 5,
            "mode": "dense",
        },
        must_contain=token,
        timeout_s=45,
    )
    print("PASS: dense search")

    # BM25 search should also find it
    poll_search(
        {
            "type": "search",
            "collection": collection,
            "query": token,
            "limit": 5,
            "mode": "bm25",
        },
        must_contain=token,
        timeout_s=45,
    )
    print("PASS: bm25 search")

    # Hybrid search should also find it
    poll_search(
        {
            "type": "search",
            "collection": collection,
            "query": token,
            "limit": 5,
            "mode": "hybrid",
        },
        must_contain=token,
        timeout_s=45,
    )
    print("PASS: hybrid search")

    print("ALL PASS")


if __name__ == "__main__":
    main()


