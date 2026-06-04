# Archivist Unified Media Pipeline — Cutover Sign-off

**Branch:** `feature/unified-media-pipeline-phase1`
**Date:** 2026-04-26
**State:** Phases 1–6 + tiered storage shipped, awaiting your walkthrough before Frigate is fully removed.

This doc is a hand-held checklist. Run the commands, compare to the expected
output, tick each box when it looks right. Anything that fails or looks off,
flag and we'll fix before flipping retention to real deletions or removing
Frigate entirely.

---

## 0. What's running

```
container                 role
─────────────────────   ──────────────────────────────────────────────
archivist               RTSP ingest + transcription + YOLO + CLIP + archive + retention
archivist-redis         event bus (archivist:v1:*)
twin_app                voice assistant — reads transcripts from Redis
frigate-stale-*         still running, recording DISABLED, detection/UI only
```

Storage tiers:
```
local SSD (sonic):  /data/media_store/segments/<cam>/<date>/       # 48h hot cache
                    /data/media_store/keyframes/<cam>/<date>/
NAS (megamind):     /media/mass/recording/<cam>/<date>/            # up to 30d continuous,
                                                                    # then 365d event-only
```

`archive_service` moves local→NAS every 5 min after the 48 h local hold expires.
`retention_service` GCs the NAS per source policy (continuous window then event-only).

---

## 1. Run the smoke test

```bash
bash /home/andy/archivist/tests/smoke_pipeline.sh
```

Expected: `19 PASS, 0 FAIL`. Warnings are acceptable if they match:
- `archivist errors last 2m count=<small>` — cap ≤ 20 after the keyframe-tap fix
- `mux errors last 2m` — expected on `front_door` (4K), known issue below

**If FAIL count > 0, stop here and report.**

---

## 2. Per-capability walkthrough

### 2a. All 7 sources up

```bash
curl -s http://127.0.0.1:5050/api/media/sources/status \
  | python3 -c "import sys, json; [print(f\"{s['id']:12s} {s['state']}\") for s in json.load(sys.stdin)['rtsp']]"
```

Expected:
```
office       up
kids         up
backyard     up
hallway      up
front_door   up
floodlight   up
office_mic   up
```

### 2b. Audio transcription — speak into the office mic

1. Speak a short phrase near the Focusrite mic, e.g. *"archivist test, phase six sign-off"*.
2. Watch transcripts land in Redis:
   ```bash
   docker exec archivist-redis redis-cli XREVRANGE archivist:v1:transcript.final + - COUNT 3
   ```
3. Confirm `source` is `office_mic` or `office` and `text` matches what you said (small.en may transcribe imperfectly on noisy rooms).

Expected wall-clock latency (measured): speech end → transcript event **p50 ~150 ms**, plus the 400 ms VAD hangover = **≈ 550 ms end-to-end**.

### 2c. Twin is routing Redis transcripts

1. Check that twin's consumer group is keeping up:
   ```bash
   docker exec archivist-redis redis-cli XINFO GROUPS archivist:v1:transcript.final
   ```
   Expected: `name=twin, lag=0, pending=0`.

2. Watch twin's live log as you speak:
   ```bash
   docker logs -f twin_app 2>&1 | grep redis_transcripts
   ```
   You should see `redis→pipeline: source=office loc=office text=...` lines as you talk.

3. Issue a real voice command twin knows (e.g. "hey computer, what time is it") and confirm it responds.

### 2d. Segments on disk

```bash
docker exec archivist sh -c 'for cam in office kids backyard hallway front_door floodlight office_mic; do
  latest=$(ls -t /data/media_store/segments/$cam/$(date -u +%Y-%m-%d)/*.mp4 /data/media_store/segments/$cam/$(date -u +%Y-%m-%d)/*.ts 2>/dev/null | head -1);
  dur=$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$latest" 2>/dev/null);
  echo "$cam   dur=${dur:-ERR}s   $(basename "$latest")";
done'
```

Expected: each camera shows a ~58–61 s segment.
Known exception: **`front_door` `.ts` segments report duration but fail strict H.264 decode** — bytes are on disk, playback needs a transcode pass. See §5.

### 2e. Motion detection is firing

```bash
docker exec archivist-redis redis-cli XLEN archivist:v1:detection.motion
```
Expected: large and growing (tens of thousands — MOG2 is sensitive).

Sample one:
```bash
docker exec archivist-redis redis-cli XREVRANGE archivist:v1:detection.motion + - COUNT 1
```

### 2f. YOLO is detecting tracked classes

```bash
docker exec archivist-redis redis-cli XLEN archivist:v1:detection.object
```
Expected: grows any time a `person / car / truck` is in a main-stream keyframe. Most indoor cams will sit near zero on a quiet day — that's correct.

Walk in front of the front_door or floodlight and watch it increment.

### 2g. Semantic search over keyframes

```bash
curl -s "http://127.0.0.1:5050/api/media/search?q=a%20car&k=5" | python3 -m json.tool
curl -s "http://127.0.0.1:5050/api/media/search?q=empty%20room&k=5" | python3 -m json.tool
```

Expected: `a car` ranks outdoor cameras (floodlight/backyard) high, `empty room` ranks indoor rooms (kids/hallway/office) high.

Pull up a thumbnail from a hit:
```bash
curl -so /tmp/hit.jpg "http://127.0.0.1:5050/api/media/keyframe?path=<keyframe_path from hit>"
xdg-open /tmp/hit.jpg
```

### 2h. Retention is in dry-run

```bash
curl -s http://127.0.0.1:5050/api/media/sources/status \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['retention'])"
```

Expected: `alive=True, dry_run=True, min_age_hours=48`. No segments have been deleted yet — the dry-run logs decisions only.

Trigger an explicit pass:
```bash
curl -s -X POST -H 'Content-Type: application/json' \
  -d '{"dry_run": true, "limit": 2000}' \
  http://127.0.0.1:5050/api/media/retention/run | python3 -m json.tool
```
Expected: `deleted=0` (all segments younger than 48 h right now), `reasons.young` equals `scanned`.

### 2i. Frigate is NOT recording any more

```bash
# ffmpeg worker count inside Frigate — should be 13, down from 19
docker top frigate-stale-20260423-1749 2>/dev/null | grep -c ffmpeg
# Frigate still healthy
docker ps --format '{{.Names}} | {{.Status}}' | grep -i frigate
# Recordings dir growth — should be flat after today
du -sh ~/automation/frigate/media/frigate/recordings 2>/dev/null
```

Expected: 13 ffmpeg workers (detection-only), status `healthy`, recordings directory stops growing (you can check again in an hour).

### 2j. GPU healthy, not oversubscribed

```bash
nvidia-smi --query-gpu=index,memory.used,memory.total,utilization.gpu --format=csv
```

Expected GPU 0: ~12 GB used / 24 GB total, ≤ 20 % steady-state utilization. Includes faster-whisper, CLIP, XTTS-v2, Immich ML, and the Qwen3-Embedding-4B TEI backend — all on the single remaining 4090 after GPU1 dropped off the bus on 2026-04-24 (Xid 79).

---

## 3. Known issues carried forward

| # | Issue | Impact | Plan |
|---|---|---|---|
| 1 | `front_door` 4K `.ts` segments fail strict H.264 decode ("non-existing PPS 0") | Files on disk but unplayable in standard players; bytes intact | Follow-up: per-source ffmpeg subprocess OR `h264_mp4toannexb` path |
| 2 | Pre-Phase-3 sidecars have empty labels | Will become retention-delete candidates at 48 h — **expected and desired** | Monitor first real retention pass |
| 3 | `detection.object` count low in quiet rooms | Not a bug — no tracked objects in frame | — |
| 4 | Twin routing → TTS first-byte not programmatically measured | Archivist/transport leg is p50 ≈ 550 ms; TTS leg depends on command type | Measure by stopwatch on a real command |

---

## 4. Sign-off actions

When items 2a–2j are all ticked:

1. **Flip retention from dry-run to real** (frees disk, deletes label-less segments older than 48 h):
   ```bash
   # edit docker-compose.yml: RETENTION_DRY_RUN: "false"
   docker compose up -d archivist
   ```
   Watch:
   ```bash
   docker exec archivist-redis redis-cli XLEN archivist:v1:segment.deleted
   docker logs -f archivist 2>&1 | grep retention
   ```

2. **After 48 h of real retention without issues, fully decommission Frigate:**
   ```bash
   cd ~/automation/frigate
   docker compose stop
   docker compose rm -f
   ```
   (The `config.yml` already has `record.enabled: false` with a backup at `config.yml.bak.before-archivist-cutover` — reverting is a file copy + restart.)

3. **Commit the archivist branch**:
   ```bash
   cd /home/andy/archivist
   git status  # review what shipped
   git add config/ sources_config.py events_bus.py rtsp_ingest_service.py \
           streaming_transcription_service.py motion_service.py vision_service.py \
           retention_service.py tests/test_*.py tests/smoke_pipeline.sh \
           docker-compose.yml requirements.txt Dockerfile main.py docs/
   git commit -m "archivist: unified RTSP+transcription+vision+retention pipeline"
   ```

4. **Twin**: delete the legacy pull loop after a week of Redis-mode parity:
   ```bash
   cd /home/andy/twin
   # delete src/twin/audio/rtsp_audio.py and the process_rtsp_source loop in src/twin/main.py
   ```

---

## 5. Revert procedures (in case of problems)

**Bring back Frigate recording** (if archivist recordings turn out insufficient):
```bash
cp ~/automation/frigate/config/config.yml.bak.before-archivist-cutover \
   ~/automation/frigate/config/config.yml
docker restart frigate-stale-20260423-1749
```

**Turn off archivist RTSP ingest** (keeps archivist's other services alive):
```bash
# The ARCHIVIST_RTSP_INGEST_ENABLED flag was removed post-cutover — ingest is
# always on. To disable, comment out the worker startup block in main.py
# (search for "Unified media pipeline") and redeploy.
```

**Switch twin back to legacy pull loop**:
```bash
# edit twin/docker-compose.yml: TWIN_USE_REDIS_TRANSCRIPTS=false
cd ~/twin && docker compose up -d twin
```

---

## 6. Files you can trust ship in this cutover

*Core pipeline (new):*
- `config/sources.yml` — camera list, ported from Frigate
- `sources_config.py` — YAML loader, hot-reload
- `events_bus.py` — Redis Streams pub/sub
- `rtsp_ingest_service.py` — PyAV puller, segment writer, keyframe tap
- `streaming_transcription_service.py` — VAD-chunked whisper
- `motion_service.py` — MOG2 on detect sub-stream
- `vision_service.py` — YOLO + CLIP on keyframes, semantic search
- `retention_service.py` — label-driven GC

*Entry points:*
- `main.py` — boot wiring + new endpoints (`/api/media/*`, `/metrics`)

*Tests (all green, 271 passing):*
- `tests/test_events_bus.py`, `test_sources_config.py`, `test_streaming_vad.py`,
  `test_ingest_no_decode.py`, `test_motion_service.py`, `test_vision_service.py`,
  `test_retention_service.py`
- `tests/smoke_pipeline.sh` — end-to-end smoke

*Twin:*
- `twin/src/twin/ai/redis_transcripts.py` — async Redis consumer
- Wiring in `twin/src/twin/main.py` after `RoomCommandPipeline` init

---

Ping me after your walkthrough and tell me:
1. Anything that failed 2a–2j
2. Whether the latency feels right to you subjectively
3. Whether the front_door `.ts` playback issue blocks sign-off or can be a follow-up
4. Whether you want to flip retention to real deletes today or wait
