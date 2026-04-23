# Media Processing Pipeline Design

**Archivist** | Media Intelligence Subsystem

---

## 1. Overview

The media processing pipeline transforms raw audio, video, and image files into structured, searchable knowledge. It operates as a **seven-stage hierarchical pipeline**: evidence through composition (L0-L5), vectorstore projection (L6), and a final subject-line inference stage (L7) that creates a one-sentence description for the file.

The design rule is: **compress aggressively, never lose provenance**. Chronology and raw evidence remain canonical. Higher layers are derived views that point back to timestamps, frames, OCR spans, transcript timing, and stored artifacts.

Every intermediate output preserves full provenance back to source evidence. Each layer is independently testable and replaceable, but the persisted outputs are split into two tiers:

- `public bundle`: the clean sidecar and pipeline JSON attached back to the media file
- `trace bundle`: the low-level internal evidence used for troubleshooting

```
Raw Media File
    |
    v
  [L0] Evidence Registration ---- MediaAsset (hash, modality, codec)
    |
    v
  [--] Transcription ------------ Whisper segments (word-level timestamps)
    |
    v
  [L1] Filtering & Detection ---- SceneSegments, SpeechSegments, word timing, OCR, keyframes
    |
    v
  [L2] Atomic Event Extraction --- Typed AtomicEvents with evidence refs
    |
    v
  [L3] Local Recap Building ------ Step-by-step event ledger windows
    |
    v
  [L4] Contextual Memory --------- Compressed contextual account
    |
    v
  [L5] Document Composition ------ Presentation-specific document view
    |
    v
  [L6] Vectorstore Projection ---- Multi-granularity Milvus chunks
    |
    v
  [L7] Subject Inference --------- One-sentence archival subject line
```

---

## 2. Supported Media Formats

| Category | Extensions |
|----------|-----------|
| Audio    | `.mp3` `.wav` `.m4a` `.flac` `.ogg` `.opus` `.wma` `.aac` `.webm` |
| Video    | `.mp4` `.mkv` `.avi` `.mov` `.webm` `.flv` `.wmv` `.ts` `.m4v` |
| Image    | `.jpg` `.jpeg` `.png` `.gif` `.bmp` `.tiff` `.webp` `.svg` |

Modality is auto-detected by file extension at registration time.

---

## 3. Pipeline Layers

### L0: Evidence Store

**Module:** `media/evidence_store.py`

Registers raw media files, computes SHA-256 hashes for deduplication, and extracts technical metadata via `ffprobe`.

- `register_asset(path, metadata)` -- creates a `MediaAsset` record
- `_detect_modality(path)` -- extension-based modality classification
- `_probe_media(path)` -- extracts duration, sample rate, bitrate, resolution, codec, FPS
- `save_artifact(artifact)` -- persists a single raw-trace `DerivedArtifact`
- `save_artifact_bundle(media_id, artifacts)` -- persists the full technical trace bundle
- `get_artifacts(media_id, kind, scope)` -- retrieves either the clean public artifact package or the technical trace

**Storage layout:**

```
/data/media_store/
  assets.json                          # Asset index
  artifacts/{media_id}/{artifact_id}.json  # Per-layer artifacts
```

### L1: Filtering

**Module:** `media/filtering.py`

Detects scenes, extracts speech segments, and scores visual quality. Content is **tagged, never deleted** -- salience tags allow downstream layers to make their own filtering decisions.

**Video filtering:**
- `detect_scene_changes(asset, threshold=0.3)` -- FFprobe scene detection, returns `SceneSegment` objects with motion/sharpness scores, keyframe paths, OCR text, and visual labels
- `extract_keyframes(asset, output_dir, max_frames, interval_s)` -- I-frame or fixed-interval extraction via FFmpeg
- `compute_sharpness(image_path)` -- Laplacian variance via OpenCV (>100 = sharp)
- `score_frame_uniqueness(frames, threshold=0.95)` -- histogram-based duplicate detection

**Audio filtering:**
- `detect_speech_segments(asset, transcript_segments)` -- converts transcript output to `SpeechSegment` objects, tags filler words (`um`, `uh`, `like`, `you know`) with `SalienceTag.FILLER`, marks low-confidence segments
- `filter_speech_segments(segments, min_confidence=0.3)` -- confidence filtering, boilerplate detection for repeated phrases

**Output:** `FilterResult` objects carrying keep/reject flags with reason codes, plus full `SceneSegment` and `SpeechSegment` lists.

### L2: Atomic Event Extraction

**Module:** `media/event_extraction.py`

Converts filtered evidence into structured, typed events.

**Speech event extraction:**
- Groups nearby speech segments within a 5-second merge window
- Classifies event type via heuristics:
  - `QUESTION` -- regex patterns (`?`, question words)
  - `DECISION` -- keywords (`decided`, `agreed`, `approved`, `going to`, `plan to`)
  - `ACTION` -- keywords (`did`, `went`, `made`, `created`, `built`, `fixed`)
  - `OBSERVATION` -- keywords (`saw`, `noticed`, `found`, `appears`, `seems`)
  - `SPEECH` -- default
- Extracts named entities via capitalized multi-word sequence regex

**Scene event extraction:**
- Creates events from visual scene changes
- Combines visual labels and OCR text as evidence

**Merging:**
- `merge_events(speech_events, scene_events)` -- temporal merge with cross-references for overlapping events

**Event types (`EventType`):**

```
SPEECH  OBSERVATION  ACTION  DECISION  QUESTION
SCENE_CHANGE  SILENCE  NOISE  OCR_TEXT  UNKNOWN
```

**Salience tags (`SalienceTag`):**

```
FILLER  UNCERTAINTY  INTERRUPTION  EMPHASIS  DECISION
ACTION_ITEM  CONTRADICTION  REFERENCE  LOW_CONFIDENCE
BOILERPLATE  DUPLICATE
```

**Output:** `AtomicEvent` objects carrying timestamps, speakers, visual entities, text evidence, confidence, source references, and provenance-rich metadata. Current metadata includes:

- raw text and cleaned text
- transcript span timing
- speaker turns
- word timestamps when available
- OCR text and OCR lines for visual events
- representative frame references
- cross-modal overlap references
- evidence refs back to speech segments, scene spans, and keyframes

### L3: Local Recaps

**Module:** `media/recaps.py`

Groups events into meaningful windows and generates inspectable step-by-step ledgers.

**Grouping strategies:**
1. `group_events_by_time_window(events, window_s=60.0)` -- fixed 60-second windows (default)
2. `group_events_by_scene(events, scene_boundaries)` -- scene-boundary alignment
3. `group_events_by_gap(events, max_gap_s=10.0)` -- silence-gap separation

**Recap generation:**
- Collects salient entities across the event group
- Extracts unresolved questions (question-type events)
- Detects causal links (cross-references between events)
- Builds a mechanical recap if no LLM text is provided
- `build_recap_prompt(events)` generates system + user prompts for optional LLM enhancement

**Output:** `LocalRecap` objects carrying group type, time range, recap text, a structured `window_summary`, salient entities, unresolved questions, emotional tone, causal links, event IDs, summary-level refs, ledger entries, and source references.

### L4: Contextual Memory

**Module:** `media/memory.py`

Compresses recaps into a contextual account that stays distinct from the walkthrough.

**Aggregation logic:**
- **Main actors:** entities appearing in 2+ recaps (top 20)
- **Timeline anchors:** start, midpoint, and end markers
- **Open loops:** unresolved questions collected from recaps
- **Inferred themes:** recurring entities across recaps
- **Locations, risk/safety issues, contradictions:** initialized for LLM enhancement
- **Notable evidence, final takeaways:** compact high-value memory traces
- **Interpretive notes:** optional derived interpretations stored separately from factual evidence

`build_memory_prompt(recaps)` generates prompts for LLM-enhanced memory construction.

**Output:** `ContextualMemory` object containing a compressed `context_overview`, main actors, timeline anchors, locations, open loops, inferred themes, risk/safety issues, contradictions, notable evidence, final takeaways, interpretive notes, an `evidence_map`, and recap IDs.

### L5: Document Composition

**Module:** `media/composer.py`

Generates task-specific output documents from the event ledger and compressed memory, not directly from the raw transcript.

**Format auto-selection (`select_output_format`):**
- Multiple speakers + decisions/questions --> `MEETING_MINUTES`
- Risk/safety issues present --> `INCIDENT_REPORT`
- Short duration (<2 min) or few events (<10) --> `EXECUTIVE_BRIEF`
- Visual + audio content with multiple speakers --> `HYBRID`
- Default --> `CHRONOLOGICAL`

**Available formats (`OutputFormat`):**

| Format | Description |
|--------|-------------|
| `CHRONOLOGICAL` | Detailed timeline with timestamps |
| `THEMATIC` | Grouped by identified themes |
| `NARRATIVE` | Story-like account of events |
| `HYBRID` | Executive summary + timeline + themes |
| `MEETING_MINUTES` | Meeting-specific structure with decisions, action items |
| `INCIDENT_REPORT` | Investigation-oriented structure |
| `EXECUTIVE_BRIEF` | High-level summary for busy stakeholders |

`compose_document()` accepts optional LLM-composed text and falls back to mechanical composition. Final output is parsed into markdown sections with explicit section kinds so compressed context and walkthrough remain separate.

**Output:** `ComposedDocument` carrying format, title, sections (heading + content pairs), full markdown text, memory ID, source references, and generation timestamp.

### L6: Vectorstore Projection

**Handled in:** `media/pipeline.py`

Indexes processed media into Milvus using the same collection schema as document transcripts (`documents_transcripts`).

**Multi-level chunking strategy:**

| Level | Chunk Type | Granularity |
|-------|-----------|-------------|
| 0 | Utterance | Individual speech segments -- fine-grained retrieval |
| 1 | Event | Atomic events with speaker context |
| 2 | Recap | 60-second window summaries -- topic-level search |
| 3 | Document | Full composed output -- high-level queries |

Each chunk receives a deterministic ID (SHA-256 of content), is tagged by type (`media_transcript`, `media_event`, `media_recap`, `media_document`), and carries timing metadata (`t_start_ms`, `t_end_ms`, `chunk_duration_s`).

Previous chunks for a media ID are deleted before re-indexing via `source_id == "media:{media_id}"`.

### L7: Subject Inference

**Handled in:** `media/pipeline.py`

Builds a single-sentence subject line from the full artifact bundle after document composition and vectorstore projection.

- Uses representative artifacts across document, memory, recap, event, and transcript layers
- Calls the configured OpenClaw-compatible chat endpoint when available
- Falls back to a deterministic heuristic sentence when the gateway is unavailable
- Persists the result as:
  - top-level `subject_line` in the pipeline result
  - a `subject_line` derived artifact in the clean public artifact bundle
  - embedded media title metadata, with the composed document title retained as description metadata when different

---

## 3.5 Artifact Packaging

The pipeline produces many intermediate objects, but they are not all equal.

### Public bundle

Written to:

- `/data/media_pipeline/{media_id}.json`
- `{media_path}.json`
- embedded back into the source media file as `archivist_media_pipeline.json`

This bundle is intentionally small and human-readable. It contains only:

- `subject_line`
- `memory`
- `document`
- `transcript`

### Trace bundle

Written to:

- `/data/media_store/artifacts/{media_id}.json`

This bundle keeps low-level pipeline evidence such as:

- `speech_segment`
- `scene`
- `keyframe`
- `event`
- `recap`

The UI should only load this bundle when the operator explicitly opens the technical raw-trace view.

---

## 4. Pipeline Execution

### Entry Point

```python
process_media_file(
    path: str,
    output_format: OutputFormat | None = None,
    recap_window_s: float = 60.0,
    metadata: dict | None = None
) -> dict
```

### Execution Sequence

| Step | Layer | Job Status | Progress | Operation |
|------|-------|-----------|----------|-----------|
| 1 | L0 | `deriving` | 0.10 | Register asset, compute hash |
| 2 | -- | `deriving` | 0.20 | Transcribe audio/video via Whisper |
| 3 | L1 | `filtering` | 0.30 | Detect scenes, extract speech segments |
| 4 | L2 | `extracting` | 0.50 | Extract and merge speech + scene events |
| 5 | L3 | `recapping` | 0.70 | Build time-windowed recaps |
| 6 | L4 | `memorizing` | 0.85 | Aggregate contextual memory |
| 7 | L5 | `composing` | 0.95 | Compose task-specific document |
| 8 | -- | `indexing` | 0.96 | Save all layer artifacts to disk |
| 9 | L6 | `indexing` | 0.96 | Insert multi-level chunks into Milvus |
| 10 | L7 | `summarizing` | 0.98 | Generate one-sentence subject line from the artifact bundle |
| 11 | -- | `done` | 1.00 | Persist full pipeline result and embed sidecars/metadata |

### Job Tracking

Each pipeline execution creates a `PipelineJob` tracked in a thread-safe global dictionary:

- **Statuses:** `pending` -> `deriving` -> `filtering` -> `extracting` -> `recapping` -> `composing` -> `indexing` -> `summarizing` -> `done` | `error`
- **Counters:** events, recaps, artifacts produced per layer
- **Timing:** start time, elapsed duration
- **Errors:** captured and stored on the job object without halting artifact persistence

### Artifact Persistence

`_save_layer_artifacts()` persists each layer's output as individual `DerivedArtifact` records:
- L1 scenes, L2 events, L3 recaps, L4 memory, L5 document
- Each artifact carries layer metadata, confidence scores, and source references
- Full pipeline result saved to `/data/media_pipeline/{media_id}.json`

### Metadata Injection

`_inject_metadata_into_file()` writes pipeline results back into source media file tags via FFmpeg:
- Fields: title, artist (participants), genre (themes), comment (open questions)
- Uses stream copy -- no re-encoding
- Supports MP4, MKV, MP3, M4A, FLAC, OGG, and related containers

---

## 5. Transcription Service

**Module:** `transcription_service.py`

Integrates **faster-whisper** directly into the archivist process.

| Setting | Environment Variable | Default |
|---------|---------------------|---------|
| Model | `TRANSCRIBE_MODEL` | `turbo` |
| Compute type | `TRANSCRIBE_COMPUTE_TYPE` | `float16` (GPU) / `int8` (CPU) |
| Beam size | `TRANSCRIBE_BEAM_SIZE` | `1` |
| Max concurrent | `TRANSCRIBE_MAX_CONCURRENT` | `2` |
| Normalization target | `TRANSCRIBE_TARGET_PEAK` | `0.10` |

- **Lazy loading:** model loaded on first transcription request, not at startup
- **GPU-first:** uses `cuda:0` by default, falls back to `cpu` with `int8`
- **Audio normalization:** peak detection and gain adjustment before transcription
- **Concurrency:** semaphore-limited to prevent GPU memory exhaustion
- **Output:** segments with start/end times and word-level timestamps

---

## 6. Folder Watcher

A background daemon thread monitors directories for new media files.

- **Scan interval:** configurable via `MEDIA_WATCH_INTERVAL_S` (default 30 seconds)
- **Deduplication:** tracks processed file hashes; skips already-processed files
- **Config persistence:** `/data/media_store/watcher_config.json`
- **Control:** started and stopped via API; runs as a daemon thread

---

## 7. REST API

### Processing

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/media/process` | Process a single media file. Body: `{ "path": "...", "format": "chronological" }` |

### Status and Assets

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/media/jobs` | List active and recent pipeline jobs |
| `GET` | `/api/media/assets` | List all registered media assets |
| `GET` | `/api/media/assets/<media_id>` | Asset details and artifact summary |
| `GET` | `/api/media/pipeline/<media_id>` | Full pipeline result |
| `GET` | `/api/media/artifacts/<media_id>` | All artifacts (optional `?kind=` filter) |

### Watcher Control

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/media/watcher` | Watcher status and configuration |
| `POST` | `/api/media/watcher` | Enable or disable the watcher |
| `POST` | `/api/media/watcher/directories` | Add a watch directory |
| `DELETE` | `/api/media/watcher/directories` | Remove a watch directory |

### Transcription

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/transcribe` | On-demand transcription (multipart or raw audio) |
| `GET` | `/api/transcription/status` | Check transcription service availability |

---

## 8. Search Integration

Media outputs are indexed into the same Milvus collection (`documents_transcripts`) used by the document indexing system. This enables unified hybrid search (dense embeddings + BM25 sparse vectors) across all content.

**Chunk metadata schema:**
- `source_id`: `"media:{media_id}"` -- used for filtering and re-indexing
- `source_type`: `"media"` (vs `"transcript"` for documents)
- `doc_type`: `media_transcript` | `media_event` | `media_recap` | `media_document`
- `path`: display file path
- `t_start_ms`, `t_end_ms`, `chunk_duration_s`: timing for playback alignment
- `level`: chunk granularity (0-3)
- `topic_label`: event type or format name
- `tag`: descriptive label for search filtering

---

## 9. Data Models

**Module:** `media/models.py`

| Model | Purpose |
|-------|---------|
| `MediaAsset` | Raw media file metadata (ID, path, modality, duration, codec, hash) |
| `DerivedArtifact` | Any layer output (kind, timing, content, confidence, source refs) |
| `SceneSegment` | L1 scene with scores, keyframe path, OCR, labels |
| `SpeechSegment` | L1 speech segment with word timestamps, salience tags |
| `FilterResult` | L1 keep/reject decision with reason code |
| `AtomicEvent` | L2 typed event with speakers, entities, confidence |
| `LocalRecap` | L3 time-windowed summary with causal links |
| `ContextualMemory` | L4 compressed memory (actors, themes, loops) |
| `ComposedDocument` | L5 final document with sections and format |
| `PipelineJob` | Job tracking (status, progress, counters, errors) |

---

## 10. UI

**Module:** `ui/src/pages/MediaPage.tsx`

The media processing page is divided into five sections:

1. **Folder Watcher Panel** -- toggle watcher on/off, manage watched directories, status indicator
2. **Process Media Panel** -- file path input, format selection, trigger processing
3. **Active Jobs Panel** -- live job list with status badges, progress bars, event/recap/artifact counts, elapsed time
4. **Processed Media List** -- clickable asset list showing filename, modality, duration, file size, codec, relative timestamp
5. **Pipeline Result Detail** -- tabbed view:
   - **Overview:** asset metadata + layer summary grid with counts
   - **Artifacts:** filterable list by kind, color-coded (transcript: blue, scene: purple, event: orange, recap: green, memory: pink, document: gold)
   - **Document:** full composed document rendered with sections

Real-time updates poll every 4 seconds. Pipeline results and artifacts are lazy-loaded on asset selection.

---

## 11. Error Handling

The pipeline follows a **graceful degradation** strategy:

- Transcription is optional -- logs a warning and continues if unavailable
- Scene detection falls back to an empty list if `ffprobe` fails
- OpenCV sharpness returns `-1.0` if unavailable (skips duplicate detection)
- FFmpeg metadata injection is non-fatal (catches errors, continues pipeline)
- Job exceptions are captured and stored on the job object
- Pipeline results are partially saved even on layer failure
- The watcher skips failed files and continues scanning

---

## 12. Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `MEDIA_STORE_DIR` | `/data/media_store` | Asset index and artifact storage |
| `MEDIA_PIPELINE_DIR` | `/data/media_pipeline` | Pipeline result cache |
| `MEDIA_WATCH_INTERVAL_S` | `30` | Watcher scan interval (seconds) |
| `TRANSCRIBE_MODEL` | `turbo` | Whisper model variant |
| `TRANSCRIBE_COMPUTE_TYPE` | `float16` | Inference precision |
| `TRANSCRIBE_BEAM_SIZE` | `1` | Beam search width |
| `TRANSCRIBE_MAX_CONCURRENT` | `2` | Max parallel transcriptions |
| `TRANSCRIBE_TARGET_PEAK` | `0.10` | Audio normalization target |
| `MILVUS_HOST` | `localhost` | Milvus vector DB host |
| `EMBEDDING_HOST` | `localhost` | Embedding service host |
| `EMBEDDING_PORT` | `8000` | Embedding service port |

**Hardcoded defaults (adjustable per call):**
- Recap time window: 60 seconds
- Speech merge window: 5 seconds
- Scene detection threshold: 0.3
- Scene gap grouping: 10 seconds
- Entity recurrence threshold: 2+ recaps

---

## 13. Design Principles

1. **Preservation over deletion.** Salience tags mark content for downstream decision-making. No layer deletes source evidence.
2. **Full provenance.** Every output traces back to source evidence via `source_refs`. Artifact chains are auditable from document sections down to individual utterances.
3. **Multi-granularity indexing.** Four chunk levels (utterance, event, recap, document) serve different query types within a single search infrastructure.
4. **Heuristic-first, LLM-optional.** Every layer produces useful output via mechanical heuristics. LLM enhancement is additive, not required.
5. **Idempotent processing.** File hashes prevent redundant re-processing. Vectorstore projection deletes previous chunks before re-indexing, and metadata injection replaces prior Archivist subtitle and bundle attachments before re-embedding.
6. **Non-destructive metadata.** FFmpeg metadata injection uses stream copy -- no re-encoding, no quality loss.
7. **Thread-safe concurrency.** Job tracking uses locks, transcription uses semaphores, the watcher runs as a stoppable daemon thread.

---

## 14. File Map

```
media/
  __init__.py
  models.py              # Data models and enumerations
  evidence_store.py      # L0 -- asset registration, artifact persistence
  filtering.py           # L1 -- scene detection, speech filtering
  event_extraction.py    # L2 -- typed event extraction and merging
  recaps.py              # L3 -- time-windowed recap generation
  memory.py              # L4 -- contextual memory aggregation
  composer.py            # L5 -- document composition
  pipeline.py            # Orchestrator, L6 vectorstore, L7 subject line, watcher, job tracking

transcription_service.py # Faster-whisper integration

main.py                  # REST API endpoints

ui/src/pages/MediaPage.tsx  # Media processing UI

tests/
  test_media_pipeline.py        # Pipeline and layer tests
  test_transcription_service.py # Transcription tests
```
