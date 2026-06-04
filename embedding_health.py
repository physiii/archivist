from __future__ import annotations

import os
import time
from typing import Any

import requests


def _as_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def check_embedding_service(
    *,
    host: str | None = None,
    port: int | str | None = None,
    model: str | None = None,
    expected_dim: int | str | None = None,
    timeout_seconds: float | None = None,
) -> dict[str, Any]:
    host = str(host or os.getenv("EMBEDDING_HOST", "localhost"))
    port_int = _as_int(port or os.getenv("EMBEDDING_PORT", "8000"), 8000)
    model_name = str(model or os.getenv("LOCAL_EMBEDDING_MODEL", "local-default")).strip() or "local-default"
    expected = _as_int(expected_dim or os.getenv("LOCAL_EMBEDDING_DIM", "2560"), 2560)
    timeout = float(timeout_seconds or os.getenv("EMBEDDING_HEALTH_TIMEOUT_SECONDS", "8"))
    base_url = f"http://{host}:{port_int}"
    endpoint = f"{base_url}/v1/embeddings"
    started = time.perf_counter()

    payload = {
        "input": "archivist embedding health check",
        "model": model_name,
        "encoding_format": "float",
    }
    try:
        response = requests.post(endpoint, json=payload, timeout=timeout)
    except Exception as exc:
        return {
            "status": "error",
            "severity": "error",
            "model": model_name,
            "endpoint": endpoint,
            "expected_dim": expected,
            "error": f"Embedding service request failed: {exc}",
        }

    latency_ms = round((time.perf_counter() - started) * 1000)
    if response.status_code >= 300:
        detail = response.text[:500]
        return {
            "status": "error",
            "severity": "error",
            "model": model_name,
            "endpoint": endpoint,
            "http_status": response.status_code,
            "expected_dim": expected,
            "latency_ms": latency_ms,
            "error": f"Embedding smoke request returned HTTP {response.status_code}: {detail}",
        }

    try:
        body = response.json()
        data = body.get("data") if isinstance(body, dict) else None
        item = data[0] if isinstance(data, list) and data else None
        embedding = item.get("embedding") if isinstance(item, dict) else None
    except Exception as exc:
        return {
            "status": "error",
            "severity": "error",
            "model": model_name,
            "endpoint": endpoint,
            "expected_dim": expected,
            "latency_ms": latency_ms,
            "error": f"Embedding service returned invalid JSON: {exc}",
        }

    if not isinstance(embedding, list):
        return {
            "status": "error",
            "severity": "error",
            "model": model_name,
            "endpoint": endpoint,
            "expected_dim": expected,
            "latency_ms": latency_ms,
            "error": "Embedding response did not include a float vector.",
        }

    vector_dim = len(embedding)
    if vector_dim != expected:
        return {
            "status": "error",
            "severity": "error",
            "model": model_name,
            "endpoint": endpoint,
            "vector_dim": vector_dim,
            "expected_dim": expected,
            "latency_ms": latency_ms,
            "error": f"Embedding dimension mismatch: got {vector_dim}, expected {expected}.",
        }

    return {
        "status": "ok",
        "severity": "ok",
        "model": model_name,
        "endpoint": endpoint,
        "vector_dim": vector_dim,
        "expected_dim": expected,
        "latency_ms": latency_ms,
    }
