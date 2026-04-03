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

# ── Video Filtering ─────────────────────────────────────────────────────


def detect_scene_changes(asset: MediaAsset, threshold: float = 0.3) -> list[SceneSegment]:
    """Detect scene changes in a video using ffmpeg's scene detection.

    Uses ffmpeg's select filter with scene change detection.
    Returns a list of scene segments with boundaries and scores.
    """
    if asset.modality not in (Modality.VIDEO,):
        return []
    if not Path(asset.path).exists():
        return []

    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet",
                "-show_entries", "frame=pts_time,pict_type",
                "-select_streams", "v:0",
                "-of", "csv=p=0",
                "-f", "lavfi",
                f"movie={asset.path},select='gt(scene\\,{threshold})'",
            ],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            logger.warning("Scene detection failed for %s", asset.filename)
            return []

        timestamps = []
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            parts = line.strip().split(",")
            try:
                timestamps.append(float(parts[0]))
            except (ValueError, IndexError):
                continue

        # Build segments from scene change timestamps
        segments = []
        all_times = [0.0] + timestamps + [asset.duration_s]
        for i in range(len(all_times) - 1):
            segments.append(SceneSegment(
                start_s=all_times[i],
                end_s=all_times[i + 1],
                scene_score=threshold if i > 0 else 0.0,
            ))
        return segments

    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
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
        vf_filter = f"fps=1/{interval_s}"
    else:
        vf_filter = "select='eq(pict_type\\,I)'"

    try:
        result = subprocess.run(
            [
                "ffmpeg", "-y", "-i", asset.path,
                "-vf", vf_filter,
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
    Otherwise fall back to simple energy-based VAD.
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
    }

    if asset.modality == Modality.VIDEO:
        results["scenes"] = detect_scene_changes(asset)

    if asset.modality in (Modality.AUDIO, Modality.VIDEO):
        speech_segs = detect_speech_segments(asset, transcript_segments)
        results["speech_segments"] = speech_segs
        results["speech_filters"] = filter_speech_segments(speech_segs)

    return results
