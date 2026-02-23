import os

import requests


BASE_URL = os.environ.get("VECTORSTORE_BASE_URL", "http://127.0.0.1:5050").rstrip("/")


def test_health_ok():
    r = requests.get(f"{BASE_URL}/health", timeout=10)
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


def test_list_collections_has_expected_shape():
    r = requests.get(f"{BASE_URL}/api/collections?include_stats=true", timeout=30)
    assert r.status_code == 200
    payload = r.json()
    assert "collections" in payload
    assert isinstance(payload["collections"], list)
    assert len(payload["collections"]) > 0

    first = payload["collections"][0]
    assert "name" in first
    assert "raw_name" in first
    assert isinstance(first.get("fields", []), list)
    if first.get("fields"):
        assert "dtype" in first["fields"][0]


def test_collection_detail_works_for_first_collection():
    cols = requests.get(f"{BASE_URL}/api/collections?include_stats=false", timeout=30).json()["collections"]
    name = cols[0]["name"]
    r = requests.get(f"{BASE_URL}/api/collections/{name}", timeout=30)
    assert r.status_code == 200
    detail = r.json()
    assert detail["name"] == name
    assert isinstance(detail["fields"], list)
    assert isinstance(detail["num_entities"], int)


def test_global_search_endpoint_responds():
    r = requests.post(
        f"{BASE_URL}/api/search/global",
        json={
            "query": "turn on the lights",
            "mode": "hybrid",
            "limit": 5,
            "nprobe": 8,
            "metric_type": "L2",
            "hybrid_fusion": "weighted",
            "hybrid_dense_weight": 0.65,
            "hybrid_sparse_weight": 0.35,
            "hybrid_rrf_k": 60,
        },
        timeout=60,
    )
    assert r.status_code == 200
    payload = r.json()
    assert "results" in payload
    assert isinstance(payload["results"], list)
    if payload["results"]:
        first = payload["results"][0]
        assert "collection" in first
        assert "distance" in first

