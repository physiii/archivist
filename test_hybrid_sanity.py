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


def search(collection, q, mode, limit=5):
    return post({"type": "search", "collection": collection, "query": q, "limit": limit, "mode": mode}).get("results") or []


def main():
    collection = f"needl_hybrid_{uuid.uuid4().hex[:10]}"

    # Three docs:
    # - doc_kw: exact keyword match for "airpods"
    # - doc_sem: semantic-ish variant without exact keyword (dense should help)
    # - doc_noise: unrelated but with one overlapping term
    token = uuid.uuid4().hex
    doc_kw = f"uuid: 11111111-1111-1111-1111-111111111111\nname: Apple AirPods Pro 2\nnotes: {token}\n"
    doc_sem = f"uuid: 22222222-2222-2222-2222-222222222222\nname: Apple wireless earbuds pro (2nd gen)\nnotes: {token}\n"
    doc_noise = f"uuid: 33333333-3333-3333-3333-333333333333\nname: Apple phone case\nnotes: {token}\n"
    post({"type": "load", "collection": collection, "model": "local_model", "text": doc_kw + "\n" + doc_sem + "\n" + doc_noise, "chunk_size": 20000})

    # Give Milvus a moment to index; the load path doesn't force flush by default.
    time.sleep(2.0)

    query = "airpods pro 2"
    dense = search(collection, query, "dense", limit=5)
    bm25 = search(collection, query, "bm25", limit=5)
    hybrid = search(collection, query, "hybrid", limit=5)

    def top_uuid(results):
        if not results:
            return ""
        txt = results[0].get("text") or ""
        for line in txt.splitlines():
            if line.lower().startswith("uuid:"):
                return line.split(":", 1)[1].strip()
        return ""

    print("Top dense:", top_uuid(dense))
    print("Top bm25:", top_uuid(bm25))
    print("Top hybrid:", top_uuid(hybrid))

    # Sanity expectation: keyword doc should be top-1 for bm25 and usually for hybrid.
    assert top_uuid(bm25) == "11111111-1111-1111-1111-111111111111"
    assert top_uuid(hybrid) in {"11111111-1111-1111-1111-111111111111", "22222222-2222-2222-2222-222222222222"}

    print("PASS: hybrid sanity")


if __name__ == "__main__":
    main()


