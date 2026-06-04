# Media Pipeline Repair Plan

## Goal

Make Archivist media processing reliable for long audio/video files by:

- running the Whisper transcription path inside Archivist
- keeping an optional remote fallback available only when explicitly configured
- producing a single consolidated artifact JSON per media asset instead of dozens of per-artifact files
- embedding portable results back into media files, especially MKV, so transcripts and artifact bundles travel with the source file
- verifying the full path end to end against `/media/mass/recording/screens/office/obs/2025-01-08_15-58-11.mkv`

## Current Problems

1. Archivist must be the production transcription service so other apps can point at `/api/transcribe`.
2. Older apps and docs referenced the standalone TranscribeServer on port `8123`; active callers should now target Archivist.
3. The media pipeline reads the entire source media file into memory before transcription, which is wrong for large MKV recordings.
4. Artifact persistence is fragmented across many JSON files, while the UI and inspection workflow need a single canonical bundle.
5. The current artifact set is incomplete:
   - transcript artifacts may be missing entirely
   - speech segments are not persisted as artifacts
   - video keyframes are implemented but not wired into the pipeline
6. Metadata injection only writes a few summary tags. It does not embed:
   - subtitle/transcript streams
   - the consolidated artifact bundle
7. Duplicate asset registrations exist for the same file hash and path variants, which makes the page misleading.

## Target Behavior

For one processed media asset, Archivist should produce:

- one canonical pipeline JSON file containing:
  - asset metadata
  - layer summaries
  - all artifacts for all layers
  - prompts and processing metadata
  - embedding / injection status
- one transcript sidecar when needed for interoperability
- embedded MKV subtitle track carrying the transcript
- embedded MKV attachment carrying the canonical artifact JSON
- summary metadata tags written back into the media file

The API should expose the canonical pipeline JSON as the source of truth.

## Implementation Plan

### 1. Transcription

- Default `transcription_service.py` to local-first faster-whisper inside Archivist.
- Keep remote transcription support as an explicit fallback for emergencies.
- Preserve TranscribeServer-compatible request and response shapes for existing clients.
- Add a media-file transcription helper that extracts audio from the source file first instead of reading the whole video into memory.

### 2. Dependencies and Runtime

- Install `faster-whisper` and `ffmpeg-python` in Archivist.
- Pin `numpy<2` to match the transcription service runtime.
- Add transcription service environment variables to `docker-compose.yml`.

### 3. Artifact Model

- Switch artifact persistence to a single consolidated JSON bundle per media asset.
- Keep backward-compatible reads for legacy per-artifact files.
- Persist transcript, speech-segment, scene, event, recap, memory, and document artifacts into that bundle.

### 4. Filtering and Video Artifacts

- Wire keyframe extraction into the video path.
- Use scaled analysis for scene detection and keyframe extraction where possible so large OBS recordings are tractable.
- Persist scene and keyframe references into the canonical artifact bundle.

### 5. Metadata Injection

- Generate transcript sidecar VTT from transcript segments.
- Embed transcript/subtitle track into MKV and MP4 using the existing `transcribe.py` behavior as reference.
- Attach the canonical artifact JSON into MKV as an attachment stream.
- Preserve summary tags for quick inspection in generic media tools.

### 6. API and UI Contract

- Make `/api/media/pipeline/<media_id>` return the canonical file including artifacts.
- Make `/api/media/artifacts/<media_id>` read from the canonical bundle.
- Keep existing endpoints but remove dependency on per-artifact files.
- Preserve path visibility and artifact counts for future UI cleanup.

### 7. Tests and Verification

- Add unit tests for:
  - remote transcription fallback behavior
  - consolidated artifact storage and retrieval
  - transcript/VTT generation
  - metadata injection command building
- Rebuild and restart the Archivist container.
- Run the pipeline on `/media/mass/recording/screens/office/obs/2025-01-08_15-58-11.mkv`.
- Verify:
  - transcription exists
  - canonical JSON exists
  - artifacts exist across layers
  - MKV contains embedded subtitle stream
  - MKV contains attached artifact JSON
  - API returns the new bundle cleanly

## Verification Commands

These are the commands the implementation must satisfy before close-out:

```bash
pytest tests/test_transcription_service.py tests/test_media_pipeline.py
docker compose build archivist
docker compose up -d archivist
curl -sf http://127.0.0.1:5050/api/transcribe/status
curl -sf http://127.0.0.1:5050/api/media/process -H 'Content-Type: application/json' -d '{"path":"/media/mass/recording/screens/office/obs/2025-01-08_15-58-11.mkv"}'
curl -sf http://127.0.0.1:5050/api/media/assets
curl -sf http://127.0.0.1:5050/api/media/pipeline/<media_id>
ffprobe -v error -show_streams -show_format /media/mass/recording/screens/office/obs/2025-01-08_15-58-11.mkv
```

## Notes

- Archivist is the production transcription endpoint at `/api/transcribe`, with `POST /` retained for legacy TranscribeServer-style clients.
- Apps that previously targeted port `8123` should target Archivist instead.
