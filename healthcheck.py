#!/usr/bin/env python3
"""Docker healthcheck for the archivist container.

Probes the local /healthz endpoint and reports the container UNHEALTHY when the
GPU/CUDA-backed pipeline is broken — the failure mode that previously wedged
transcription silently (no CPU fallback, nothing restarting the container).

Exit 0 (healthy) / exit 1 (unhealthy). Referenced from docker-compose.yml.

Design notes:
- Uses /healthz, NOT /health: /healthz reports only this container's CUDA +
  transcription state and is fast, so the check does not flap on external-
  dependency latency (Milvus/embeddings/Google live probes in /health can exceed
  the timeout even when this container is perfectly healthy).
- Recovery itself is handled by gpu_watchdog (it restarts the container on a
  sustained healthy->lost CUDA transition). This check is the observability half:
  it makes `docker ps` actually show health, which was missing (Health=none).
"""
import json
import os
import sys
import urllib.request

URL = os.getenv("ARCHIVIST_HEALTHCHECK_URL", "http://127.0.0.1:5050/healthz")
TIMEOUT = float(os.getenv("ARCHIVIST_HEALTHCHECK_TIMEOUT_S", "10"))


def main() -> int:
    try:
        with urllib.request.urlopen(URL, timeout=TIMEOUT) as resp:
            payload = json.load(resp)
            code = resp.getcode()
    except urllib.error.HTTPError as exc:  # /healthz returns 503 when unhealthy
        try:
            detail = exc.read().decode("utf-8", "replace")[:200]
        except Exception:
            detail = ""
        print(f"unhealthy: HTTP {exc.code} {detail}")
        return 1
    except Exception as exc:  # server down / wedged / not yet up
        print(f"unhealthy: /healthz request failed: {exc}")
        return 1

    if code == 200 and payload.get("status") == "ok":
        print(f"healthy: gpu={payload.get('gpu')} transcription_device={payload.get('transcription_device')}")
        return 0
    print(f"unhealthy: {json.dumps(payload)[:300]}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
