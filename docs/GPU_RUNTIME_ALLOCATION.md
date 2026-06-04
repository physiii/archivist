# GPU Runtime Allocation

Host `sonic` runs a single RTX 4090 (24 GB). The second 4090 that used to host
the embedding backend dropped off the PCIe bus on 2026-04-24 (Xid 79, hardware)
and is no longer in the machine. Every GPU workload now shares `cuda:0`.

## Steady-state budget (24 GB)

| Host GPU | Workload | Container | Approx VRAM |
| --- | --- | --- | --- |
| 0 | Qwen/Qwen3-Embedding-4B (TEI, fp16) | `embed-tei-qwen3-4b-1` | ~8.3 GB |
| 0 | faster-whisper `medium.en` (float16) | `archivist` | ~1.5 GB |
| 0 | CLIP ViT-B-32 | `archivist` | ~0.5 GB |
| 0 | XTTS-v2 streaming helper (`tts-env`) | host process | ~3.1 GB |
| 0 | Immich ML (ONNX CLIP + face detection) | `immich_machine_learning` | ~2 GB |
| 0 | Frigate decode + ffmpeg NVENC | `frigate` | transient ~0.3 GB |
| 0 | _headroom_ | — | ~9 GB |

Confirm with:

```bash
nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv
nvidia-smi --query-gpu=memory.used,memory.free --format=csv
```

Expect total `memory.used` under 14 GB at idle. Transient spikes during
concurrent transcoding + transcription + TTS can add another 3–4 GB.

## Controls

- **Archivist** (`docker-compose.yml`): `ARCHIVIST_GPU_ID=0`, `TRANSCRIBE_GPU_ID=0`,
  `CLIP_GPU_ID=0`, `TTS_DEVICE_TYPE=cuda`. `LOCAL_EMBEDDING_DIM=2560` and
  `LOCAL_EMBEDDING_MODEL=local-default` must match whatever the embed gateway
  is serving, or collection search will silently fall back to BM25-only.
- **Embed gateway** (`/home/andy/embed/.env`): `EMBED_GPU_ID=0`,
  `EMBED_NVIDIA_VISIBLE_DEVICES=0`. The TEI service id is `tei-qwen3-4b`;
  change `--model-id` in `docker-compose.yml` to swap models, and keep
  `models.yaml` in sync so the gateway advertises the right dimension.
- **Immich ML** (`/home/andy/automation/immich/immich-app/.env`):
  `IMMICH_ML_GPU_ID=0`.
- **Frigate** (`/home/andy/automation/docker-compose.yml`):
  `FRIGATE_GPU_ID=0`, `FRIGATE_NVIDIA_VISIBLE_DEVICES=0`.

## Verification after container restarts

```bash
# GPU inventory
nvidia-smi --query-gpu=index,name,memory.total,memory.used,utilization.gpu --format=csv,noheader,nounits

# Embedding backend
curl -fsS http://localhost:8000/healthz
curl -sS http://localhost:8000/v1/embeddings -H 'content-type: application/json' \
  -d '{"input":"ping","model":"local-default"}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('dim=',len(d['data'][0]['embedding']))"
# expect: dim= 2560

# Archivist
curl -fsS http://localhost:5050/api/transcribe/status

# Immich ML
docker logs --tail 5 immich_machine_learning | grep -i ready
```

## If something OOMs

The embedding backend is the biggest single consumer. To reclaim memory for an
oversized transcoding or training burst, stop TEI rather than starving the
others:

```bash
docker compose -f /home/andy/embed/docker-compose.yml stop tei-qwen3-4b
# ... run the transient heavy job ...
docker compose -f /home/andy/embed/docker-compose.yml start tei-qwen3-4b
```

Archivist search will degrade to BM25-only while TEI is down, but ingest still
succeeds (new chunks queue for later dense embedding).

## Historical note

Prior to 2026-04-24 this host ran dual 4090s with a GPU0/GPU1 split.
`Qwen3-Embedding-8B` (INT8 via bitsandbytes) was pinned to GPU1 and
produced 4096-dim vectors. After GPU1 left the bus we switched the backend
to `Qwen3-Embedding-4B` on HF Text Embeddings Inference (fp16, dim 2560)
and re-embedded every `documents_*` Milvus collection. See
`scripts/migrate_embeddings_to_qwen4b.py`. Old 4096-dim collections were
renamed with the `_v1_qwen8b_4096` suffix and are kept read-only as a
safety net; drop them once you're confident about retrieval quality on
the new model.
