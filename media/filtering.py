"""L1: Filtering layer - scene detection, VAD, blur/sharpness scoring, deduplication.

Filters low-value content early while preserving raw references.
Marks content with salience tags rather than permanently deleting it.
"""

from __future__ import annotations

import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

import numpy as np

from media.models import (
    DerivedArtifact,
    FilterResult,
    MediaAsset,
    Modality,
    SalienceTag,
    SceneSegment,
    SpeechSegment,
)

logger = logging.getLogger("archivist.media.filtering")

SCENE_MAX_WIDTH = max(0, int(os.getenv("MEDIA_SCENE_MAX_WIDTH", "960")))
SCENE_SAMPLE_FPS = max(0.1, float(os.getenv("MEDIA_SCENE_SAMPLE_FPS", "1")))
SCENE_ANALYSIS_MAX_PIXELS = max(1, int(os.getenv("MEDIA_SCENE_ANALYSIS_MAX_PIXELS", "12000000")))
KEYFRAME_MAX_WIDTH = max(0, int(os.getenv("MEDIA_KEYFRAME_MAX_WIDTH", "1920")))
DEFAULT_KEYFRAME_INTERVAL_S = max(1.0, float(os.getenv("MEDIA_KEYFRAME_INTERVAL_S", "60")))
MAX_KEYFRAMES_PER_ASSET = max(1, int(os.getenv("MEDIA_MAX_KEYFRAMES_PER_ASSET", "120")))
LARGE_VIDEO_KEYFRAME_INTERVAL_S = max(1.0, float(os.getenv("MEDIA_LARGE_VIDEO_KEYFRAME_INTERVAL_S", "300")))
LARGE_VIDEO_MAX_KEYFRAMES = max(1, int(os.getenv("MEDIA_LARGE_VIDEO_MAX_KEYFRAMES", "16")))

# Batch video decode (scene detection, keyframes) runs at low CPU/IO priority so
# it yields to real-time RTSP transcription. Computed once at import.
import shutil as _shutil
def _lowpri_prefix() -> list[str]:
    pre: list[str] = []
    if os.getenv("MEDIA_BATCH_LOWPRI", "1").strip().lower() in {"1", "true", "yes", "on"}:
        if _shutil.which("nice"):
            pre += ["nice", "-n", "19"]
        if _shutil.which("ionice"):
            pre += ["ionice", "-c", "3"]
    return pre
LOWPRI_PREFIX = _lowpri_prefix()

# ── Video Filtering ─────────────────────────────────────────────────────


def detect_scene_changes(asset: MediaAsset, threshold: float = 0.3) -> list[SceneSegment]:
    """Detect scene changes in a video using ffmpeg's scene detection.

    Uses ffmpeg's select filter to find frames where the scene change score
    exceeds the threshold, then prints their timestamps.
    Returns a list of scene segments with boundaries and scores.
    """
    if asset.modality not in (Modality.VIDEO,):
        return []
    if not Path(asset.path).exists():
        return []
    pixel_count = max(0, int(asset.width)) * max(0, int(asset.height))
    if pixel_count and pixel_count > SCENE_ANALYSIS_MAX_PIXELS:
        logger.info(
            "Skipping scene detection for %s due to large frame size (%dx%d)",
            asset.filename,
            asset.width,
            asset.height,
        )
        return []

    try:
        vf_filters = []
        if SCENE_SAMPLE_FPS > 0:
            vf_filters.append(f"fps={SCENE_SAMPLE_FPS:g}")
        if SCENE_MAX_WIDTH > 0:
            vf_filters.append(f"scale='min(iw,{SCENE_MAX_WIDTH})':-2")
        vf_filters.append(f"select='gt(scene,{threshold})'")
        vf_filters.append("showinfo")
        # Use ffmpeg (not ffprobe) with the select filter to detect scene changes.
        # -f null - discards the output; showinfo prints pts_time for each selected frame.
        result = subprocess.run(
            [
                *LOWPRI_PREFIX, "ffmpeg", "-hide_banner", "-loglevel", "info", "-i", asset.path,
                "-an", "-sn", "-dn",
                "-vf", ",".join(vf_filters),
                "-vsync", "vfr",
                "-f", "null", "-",
            ],
            capture_output=True, text=True,
            timeout=max(300, int(asset.duration_s * 0.5)),
        )
        # ffmpeg writes filter output to stderr
        output = result.stderr or ""

        timestamps = []
        for line in output.split("\n"):
            # showinfo lines look like: [Parsed_showinfo...] n:0 pts:12345 pts_time:1.234 ...
            if "pts_time:" not in line:
                continue
            try:
                pts_part = line.split("pts_time:")[1]
                pts_val = pts_part.strip().split()[0].rstrip(",")
                timestamps.append(float(pts_val))
            except (ValueError, IndexError):
                continue

        if not timestamps and result.returncode != 0:
            logger.warning("Scene detection returned no scenes for %s (exit code %d)", asset.filename, result.returncode)

        # Build segments from scene change timestamps
        segments = []
        all_times = [0.0] + timestamps + [asset.duration_s]
        for i in range(len(all_times) - 1):
            if all_times[i + 1] <= all_times[i]:
                continue
            segments.append(SceneSegment(
                start_s=all_times[i],
                end_s=all_times[i + 1],
                scene_score=threshold if i > 0 else 0.0,
            ))
        return segments

    except subprocess.TimeoutExpired:
        logger.warning("Scene detection timed out for %s", asset.filename)
        return []
    except FileNotFoundError:
        logger.warning("ffmpeg not found for scene detection")
        return []
    except Exception as e:
        logger.warning("Scene detection error for %s: %s", asset.filename, e)
        return []


def extract_keyframes(asset: MediaAsset, output_dir: str, max_frames: int = 100, interval_s: float = 0.0) -> list[str]:
    """Extract keyframes from video using ffmpeg.

    If interval_s > 0, samples every N seconds (fixed interval).
    Otherwise uses I-frame extraction (scene-based).
    Returns list of keyframe file paths.
    """
    if asset.modality != Modality.VIDEO:
        return []

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    if interval_s > 0:
        frames: list[str] = []
        timestamps = []
        current = 0.0
        duration = max(0.0, float(asset.duration_s or 0.0))
        while len(timestamps) < max_frames and current < duration:
            timestamps.append(current)
            current += interval_s
        if not timestamps:
            timestamps = [0.0]

        scale_filter = None
        if KEYFRAME_MAX_WIDTH > 0:
            scale_filter = f"scale='min(iw,{KEYFRAME_MAX_WIDTH})':-2"

        for idx, ts in enumerate(timestamps, start=1):
            frame_path = os.path.join(output_dir, f"keyframe_{idx:04d}.jpg")
            cmd = [
                *LOWPRI_PREFIX, "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-ss", f"{ts:.3f}",
                "-i", asset.path,
                "-an", "-sn", "-dn",
            ]
            if scale_filter:
                cmd.extend(["-vf", scale_filter])
            cmd.extend([
                "-frames:v", "1",
                "-q:v", "2",
                frame_path,
            ])
            try:
                result = subprocess.run(cmd, capture_output=True, timeout=60)
            except subprocess.TimeoutExpired:
                logger.warning("Keyframe seek extraction timed out for %s at %.2fs", asset.filename, ts)
                continue
            if result.returncode == 0 and Path(frame_path).exists() and Path(frame_path).stat().st_size > 0:
                frames.append(frame_path)
            else:
                try:
                    Path(frame_path).unlink(missing_ok=True)
                except Exception:
                    pass
        return frames

    vf_filters = []
    if KEYFRAME_MAX_WIDTH > 0:
        vf_filters.append(f"scale='min(iw,{KEYFRAME_MAX_WIDTH})':-2")
    if interval_s > 0:
        vf_filters.append(f"fps=1/{interval_s}")
    else:
        vf_filters.append("select='eq(pict_type\\,I)'")

    try:
        result = subprocess.run(
            [
                *LOWPRI_PREFIX, "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", asset.path,
                "-an", "-sn", "-dn",
                "-vf", ",".join(vf_filters),
                "-frames:v", str(max_frames),
                "-vsync", "vfr",
                "-q:v", "2",
                os.path.join(output_dir, "keyframe_%04d.jpg"),
            ],
            capture_output=True, timeout=180,
        )
        if result.returncode != 0:
            logger.warning("Keyframe extraction failed for %s", asset.filename)
            return []

        frames = sorted(Path(output_dir).glob("keyframe_*.jpg"))
        return [str(f) for f in frames[:max_frames]]

    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        logger.warning("Keyframe extraction error: %s", e)
        return []


def compute_sharpness(image_path: str) -> float:
    """Compute sharpness score using Laplacian variance (OpenCV).

    Higher values = sharper image. Blurry images score < 100 typically.
    Returns -1.0 if OpenCV is not available.
    """
    try:
        import cv2
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return -1.0
        return float(cv2.Laplacian(img, cv2.CV_64F).var())
    except ImportError:
        return -1.0
    except Exception:
        return -1.0


def score_frame_uniqueness(frames: list[str], threshold: float = 0.95) -> list[FilterResult]:
    """Score frames for uniqueness vs neighbors using histogram comparison.

    Marks near-duplicate frames with the DUPLICATE tag.
    """
    results = []
    try:
        import cv2
    except ImportError:
        return [FilterResult(artifact_id=f, keep=True, reason="cv2 unavailable") for f in frames]

    prev_hist = None
    for frame_path in frames:
        img = cv2.imread(frame_path)
        if img is None:
            results.append(FilterResult(artifact_id=frame_path, keep=False, reason="unreadable"))
            continue

        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist([hsv], [0, 1], None, [50, 60], [0, 180, 0, 256])
        cv2.normalize(hist, hist)

        if prev_hist is not None:
            similarity = cv2.compareHist(prev_hist, hist, cv2.HISTCMP_CORREL)
            if similarity > threshold:
                results.append(FilterResult(
                    artifact_id=frame_path, keep=False, score=1.0 - similarity,
                    reason="near-duplicate", tags=[SalienceTag.DUPLICATE],
                ))
                prev_hist = hist
                continue

        sharpness = compute_sharpness(frame_path)
        keep = sharpness > 50.0 or sharpness < 0  # Keep if sharp enough or if cv2 unavailable
        results.append(FilterResult(
            artifact_id=frame_path, keep=keep, score=min(1.0, sharpness / 500.0),
            reason="" if keep else "blurry",
        ))
        prev_hist = hist

    return results


# ── Audio Filtering ─────────────────────────────────────────────────────


def detect_speech_segments(asset: MediaAsset, transcript_segments: Optional[list] = None) -> list[SpeechSegment]:
    """Build speech segments from transcript data.

    If transcript_segments are provided (from faster-whisper), use those.
    Otherwise fall back to energy-based VAD using ffmpeg's silencedetect filter
    to identify non-silent regions as speech candidates.
    """
    segments = []

    if transcript_segments:
        for seg in transcript_segments:
            text = getattr(seg, "text", str(seg)) if not isinstance(seg, dict) else seg.get("text", "")
            start = getattr(seg, "start", 0.0) if not isinstance(seg, dict) else seg.get("start", 0.0)
            end = getattr(seg, "end", 0.0) if not isinstance(seg, dict) else seg.get("end", 0.0)
            no_speech = getattr(seg, "no_speech_prob", 0.0) if not isinstance(seg, dict) else seg.get("no_speech_prob", 0.0)

            tags = []
            if no_speech and no_speech > 0.5:
                tags.append(SalienceTag.LOW_CONFIDENCE)

            # Tag filler words (mark, don't delete)
            filler_words = {"um", "uh", "like", "you know", "i mean", "so", "well", "right"}
            text_lower = text.strip().lower()
            if text_lower in filler_words or (len(text_lower.split()) <= 2 and any(fw in text_lower for fw in filler_words)):
                tags.append(SalienceTag.FILLER)

            words = []
            if hasattr(seg, "words") and seg.words:
                words = [
                    {"start": w.start, "end": w.end, "word": w.word, "probability": getattr(w, "probability", None)}
                    for w in seg.words
                ]

            segments.append(SpeechSegment(
                start_s=float(start),
                end_s=float(end),
                text=text.strip(),
                confidence=1.0 - float(no_speech or 0.0),
                salience_tags=tags,
                word_timestamps=words,
            ))
        return segments

    # ── Fallback: energy-based VAD via ffmpeg silencedetect ─────────────
    # When no transcription is available, detect non-silent regions so
    # downstream layers still have speech timing information.
    if asset.modality not in (Modality.AUDIO, Modality.VIDEO):
        return segments

    if not Path(asset.path).exists():
        return segments

    try:
        result = subprocess.run(
            [
                *LOWPRI_PREFIX, "ffmpeg", "-hide_banner", "-loglevel", "info", "-i", asset.path,
                "-vn", "-sn", "-dn",
                "-map", "0:a:0?",
                "-af", "silencedetect=noise=-30dB:d=0.5",
                "-f", "null", "-",
            ],
            capture_output=True, text=True,
            timeout=max(300, int(asset.duration_s * 0.3)),
        )
        output = result.stderr or ""

        # Parse silence intervals from ffmpeg output:
        #   [silencedetect ...] silence_start: 1.234
        #   [silencedetect ...] silence_end: 5.678 | silence_duration: 4.444
        silence_starts = []
        silence_ends = []
        for line in output.split("\n"):
            if "silence_start:" in line:
                try:
                    val = line.split("silence_start:")[1].strip().split()[0]
                    silence_starts.append(float(val))
                except (ValueError, IndexError):
                    pass
            elif "silence_end:" in line:
                try:
                    val = line.split("silence_end:")[1].strip().split()[0]
                    silence_ends.append(float(val))
                except (ValueError, IndexError):
                    pass

        # Build speech regions as the inverse of silence regions
        duration = asset.duration_s or 0.0
        if not silence_starts and not silence_ends:
            # No silence detected -- entire file is speech
            if duration > 0:
                segments.append(SpeechSegment(
                    start_s=0.0,
                    end_s=duration,
                    text="[speech detected - transcription unavailable]",
                    confidence=0.5,
                    salience_tags=[SalienceTag.LOW_CONFIDENCE],
                ))
            return segments

        # Pair up silence intervals
        silence_intervals = list(zip(silence_starts, silence_ends[:len(silence_starts)]))

        # Speech is the gaps between silence
        speech_start = 0.0
        for s_start, s_end in silence_intervals:
            if s_start > speech_start + 0.5:
                segments.append(SpeechSegment(
                    start_s=speech_start,
                    end_s=s_start,
                    text="[speech detected - transcription unavailable]",
                    confidence=0.5,
                    salience_tags=[SalienceTag.LOW_CONFIDENCE],
                ))
            speech_start = s_end

        # Trailing speech after last silence
        if speech_start < duration - 0.5:
            segments.append(SpeechSegment(
                start_s=speech_start,
                end_s=duration,
                text="[speech detected - transcription unavailable]",
                confidence=0.5,
                salience_tags=[SalienceTag.LOW_CONFIDENCE],
            ))

        logger.info("VAD fallback: found %d speech regions for %s", len(segments), asset.filename)

    except subprocess.TimeoutExpired:
        logger.warning("VAD fallback timed out for %s", asset.filename)
    except FileNotFoundError:
        logger.warning("ffmpeg not found for VAD fallback")
    except Exception as e:
        logger.warning("VAD fallback error for %s: %s", asset.filename, e)

    return segments


def filter_speech_segments(segments: list[SpeechSegment], min_confidence: float = 0.3) -> list[FilterResult]:
    """Filter speech segments by confidence and content quality.

    Does NOT delete segments - marks them with salience tags for downstream use.
    """
    results = []
    for seg in segments:
        tags = list(seg.salience_tags)
        keep = True
        reason = ""

        if seg.confidence < min_confidence:
            tags.append(SalienceTag.LOW_CONFIDENCE)
            keep = False
            reason = "low confidence"

        # Detect repeated phrases
        words = seg.text.lower().split()
        if len(words) >= 4:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio < 0.3:
                tags.append(SalienceTag.BOILERPLATE)

        results.append(FilterResult(
            artifact_id=f"speech_{seg.start_s:.2f}",
            keep=keep,
            score=seg.confidence,
            reason=reason,
            tags=tags,
        ))

    return results


# ── Combined Filtering ──────────────────────────────────────────────────


def filter_asset(asset: MediaAsset, transcript_segments: Optional[list] = None) -> dict:
    """Run all applicable filters on a media asset.

    Returns a summary of filtering results by type.
    """
    results: dict = {
        "media_id": asset.media_id,
        "modality": asset.modality.value,
        "scenes": [],
        "speech_segments": [],
        "speech_filters": [],
        "keyframe_filters": [],
        "keyframes": [],
    }

    if asset.modality == Modality.VIDEO:
        pixel_count = max(0, int(asset.width)) * max(0, int(asset.height))
        results["scenes"] = detect_scene_changes(asset)
        keyframe_dir = Path(os.getenv("MEDIA_PIPELINE_DIR", "/data/media_pipeline")) / "keyframes" / asset.media_id
        keyframe_interval_s = DEFAULT_KEYFRAME_INTERVAL_S
        if pixel_count and pixel_count > SCENE_ANALYSIS_MAX_PIXELS:
            keyframe_interval_s = max(keyframe_interval_s, LARGE_VIDEO_KEYFRAME_INTERVAL_S)
        estimated_interval_frames = max(1, int((asset.duration_s or 0.0) / keyframe_interval_s) + 1)
        max_frames = min(MAX_KEYFRAMES_PER_ASSET, max(1, len(results["scenes"]) or 1, estimated_interval_frames))
        if pixel_count and pixel_count > SCENE_ANALYSIS_MAX_PIXELS:
            max_frames = min(max_frames, LARGE_VIDEO_MAX_KEYFRAMES)
        keyframes = extract_keyframes(
            asset,
            str(keyframe_dir),
            max_frames=max_frames,
            interval_s=keyframe_interval_s,
        )
        results["keyframes"] = keyframes
        for idx, scene in enumerate(results["scenes"]):
            if idx < len(keyframes):
                scene.keyframe_path = keyframes[idx]

    if asset.modality in (Modality.AUDIO, Modality.VIDEO):
        speech_segs = detect_speech_segments(asset, transcript_segments)
        results["speech_segments"] = speech_segs
        results["speech_filters"] = filter_speech_segments(speech_segs)

    return results
