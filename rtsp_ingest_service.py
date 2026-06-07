"""RTSP ingest service for archivist's unified media pipeline.

Per-source worker (one thread per source, daemon=True) that:
  - opens the source's RTSP URL via PyAV
  - demuxes audio and (for cameras) video packets
  - writes passthrough MP4 segments (~60s, rotating on keyframe), no re-encode
  - feeds decoded audio PCM to streaming_transcription_service
  - publishes source.health and segment.written events to Redis

Invariants:
  - The video WRITE path must never call packet.decode(). Segments are pure
    passthrough so they're cheap and preserve original quality. Enforced by
    tests/test_ingest_no_decode.py.
"""

from __future__ import annotations

import json
import logging
import math
import os
import random
import re
import audioop
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

import events_bus
import source_quality
import sources_config
from sources_config import Source

logger = logging.getLogger("archivist.rtsp")

OPEN_TIMEOUT_S = int(os.getenv("RTSP_OPEN_TIMEOUT_S", "10"))
PKT_RECV_TIMEOUT_S = int(os.getenv("RTSP_RECV_TIMEOUT_S", "30"))

SEGMENTS_ROOT = Path(os.getenv("ARCHIVIST_SEGMENTS_ROOT", "/data/media_store/segments"))
SEGMENT_TARGET_S = float(os.getenv("ARCHIVIST_SEGMENT_TARGET_S", "60"))
SEGMENT_MAX_S = float(os.getenv("ARCHIVIST_SEGMENT_MAX_S", "120"))  # hard cap if no keyframe arrives
AUDIO_HEALTH_INTERVAL_S = float(os.getenv("ARCHIVIST_AUDIO_HEALTH_INTERVAL_S", "5"))
AUDIO_LOW_RMS_DBFS = float(os.getenv("ARCHIVIST_AUDIO_LOW_RMS_DBFS", "-70"))
CAPTURE_MIN_MEDIA_RATIO = float(os.getenv("ARCHIVIST_CAPTURE_MIN_MEDIA_RATIO", "0.80"))
CAPTURE_MIN_VIDEO_PACKETS_PER_S = float(os.getenv("ARCHIVIST_CAPTURE_MIN_VIDEO_PACKETS_PER_S", "8.0"))
CAMERA_KEYFRAME_VISION_ENABLED = (
    os.getenv("ARCHIVIST_CAMERA_KEYFRAME_VISION_ENABLED") or "false"
).strip().lower() in ("1", "true", "yes", "on")
CAMERA_AUDIO_TRANSCRIPTION_ENABLED = (
    os.getenv("ARCHIVIST_CAMERA_AUDIO_TRANSCRIPTION_ENABLED") or "false"
).strip().lower() in ("1", "true", "yes", "on")
CAMERA_RECORD_AUDIO_ENABLED = (
    os.getenv("ARCHIVIST_CAMERA_RECORD_AUDIO_ENABLED") or "false"
).strip().lower() in ("1", "true", "yes", "on")
CAMERA_MOTION_ENABLED = (
    os.getenv("ARCHIVIST_CAMERA_MOTION_ENABLED") or "false"
).strip().lower() in ("1", "true", "yes", "on")
CAMERA_MOTION_MAX_FPS = float(os.getenv("ARCHIVIST_CAMERA_MOTION_MAX_FPS", "2.0"))
SEGMENT_WRITER_ENABLED = (os.getenv("ARCHIVIST_SEGMENT_WRITER_ENABLED") or "true").strip().lower() in (
    "1", "true", "yes", "on"
)

_FORMAT_EXTENSIONS = {"mp4": ".mp4", "mpegts": ".ts", "matroska": ".mkv"}
_FORMAT_OPTIONS = {
    "mp4": {
        "movflags": "+frag_keyframe+empty_moov+default_base_moof",
        "avoid_negative_ts": "make_zero",
    },
    "mpegts": {
        # resend_headers inlines SPS/PPS before each keyframe so segments are self-contained;
        # system_b keeps the PAT/PMT tables regenerated per-segment.
        "mpegts_flags": "+resend_headers+system_b",
    },
    "matroska": {},
}

_workers: dict[str, "_Worker"] = {}
_stop_event = threading.Event()
_start_lock = threading.Lock()
_RTSP_URL_RE = re.compile(r"rtsp://[^\s'\"<>]+")


@dataclass
class _Worker:
    source: Source
    thread: threading.Thread
    state: str = "idle"
    last_error: Optional[str] = None
    segments_written: int = 0


def _publish_health(src_id: str, state: str, error: Optional[str] = None, **fields) -> None:
    payload = {"state": state}
    payload.update({k: v for k, v in fields.items() if v is not None})
    if error:
        payload["error"] = _safe_error(error)[:500]
    events_bus.publish("source.health", src_id, payload)


def _redact_sensitive(value: object) -> str:
    return _RTSP_URL_RE.sub("rtsp://[redacted]", str(value))


def _safe_error(value: object) -> str:
    return _redact_sensitive(value)[:500]


def _dbfs(amplitude: float, *, full_scale: float = 32768.0) -> float:
    if amplitude <= 0:
        return -120.0
    return max(-120.0, 20.0 * math.log10(float(amplitude) / float(full_scale)))


def _audio_level_stats(pcm: bytes) -> dict:
    """Return compact int16 PCM audio level stats for source health."""
    if not pcm:
        return {
            "audio_samples": 0,
            "audio_rms": 0.0,
            "audio_peak": 0.0,
            "audio_rms_dbfs": -120.0,
            "audio_peak_dbfs": -120.0,
        }
    usable = pcm[: len(pcm) - (len(pcm) % 2)]
    if not usable:
        return {
            "audio_samples": 0,
            "audio_rms": 0.0,
            "audio_peak": 0.0,
            "audio_rms_dbfs": -120.0,
            "audio_peak_dbfs": -120.0,
        }
    try:
        rms = float(audioop.rms(usable, 2))
        peak = float(audioop.max(usable, 2))
    except Exception:
        rms = 0.0
        peak = 0.0
    return {
        "audio_samples": len(usable) // 2,
        "audio_rms": round(rms / 32768.0, 6),
        "audio_peak": round(peak / 32768.0, 6),
        "audio_rms_dbfs": round(_dbfs(rms), 1),
        "audio_peak_dbfs": round(_dbfs(peak), 1),
    }


def _audio_health_payload(source: Source, pcm: bytes, stream_ts: Optional[float]) -> dict:
    stats = _audio_level_stats(pcm)
    quality = source_quality.snapshot(source.id)
    rms_dbfs = float(stats.get("audio_rms_dbfs", -120.0))
    stats.update(
        {
            "role": "audio",
            "kind": source.kind,
            "location": source.location,
            "audio_state": "low_signal" if rms_dbfs < AUDIO_LOW_RMS_DBFS else "ok",
            "voice_activity": rms_dbfs >= AUDIO_LOW_RMS_DBFS,
            "low_rms_threshold_dbfs": AUDIO_LOW_RMS_DBFS,
            "audio_stream_ts": stream_ts,
            "source_quality": quality,
            "vad_profile": quality.get("vad_profile"),
        }
    )
    return stats


def _should_start_detect_stream(source: Source) -> bool:
    return bool(CAMERA_MOTION_ENABLED and source.kind == "camera" and source.video_sub_url)


def _motion_frame_interval_s(source: Source) -> float:
    fps_values = [float(v) for v in (CAMERA_MOTION_MAX_FPS, getattr(source.detect, "fps", 0)) if float(v) > 0]
    if not fps_values:
        return 0.0
    return 1.0 / min(fps_values)


def _main_stream_url(source: Source) -> Optional[str]:
    if source.kind == "camera":
        return source.video_main_url or source.audio_url
    return source.audio_url or source.video_main_url


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _segment_dir(source_id: str, now: datetime) -> Path:
    return SEGMENTS_ROOT / source_id / now.strftime("%Y-%m-%d")


def _segment_paths(source_id: str, now: datetime, ext: str = ".mp4") -> tuple[Path, Path]:
    base = _segment_dir(source_id, now) / now.strftime("%H%M%S")
    return base.with_suffix(ext), base.with_suffix(".json")


class _SegmentWriter:
    """Passthrough MP4 segment writer. No decode, no re-encode.

    The caller feeds input-side packets via feed_packet(). Rotation happens
    internally when a keyframe arrives past the target duration (cameras) or
    when the time cap is exceeded (mics without keyframes).
    """

    def __init__(
        self,
        source_id: str,
        video_in_stream,
        audio_in_stream,
        segment_format: str = "mp4",
        on_segment_closed: Optional[Callable[[], None]] = None,
    ) -> None:
        self._source_id = source_id
        self._video_in = video_in_stream
        self._audio_in = audio_in_stream
        self._segment_format = segment_format if segment_format in _FORMAT_EXTENSIONS else "mp4"
        self._container = None
        self._video_out = None
        self._audio_out = None
        self._path: Optional[Path] = None
        self._sidecar_path: Optional[Path] = None
        self._segment_start_wall: Optional[float] = None
        self._segment_start_dt: Optional[datetime] = None
        self._last_pts_s: Optional[float] = None
        self._bytes_muxed = 0
        self._on_segment_closed = on_segment_closed
        self._pts_base: dict[str, int] = {}
        self._last_mux_dts: dict[str, int] = {}
        self._packet_counts: dict[str, int] = {"video": 0, "audio": 0}
        self._stream_media_end_s: dict[str, float] = {}
        self._dropped_missing_timestamp_packets = 0
        self._dropped_nonmonotonic_packets = 0
        self._adjusted_nonmonotonic_packets = 0
        self._mux_error_count = 0

    @property
    def elapsed(self) -> float:
        if self._segment_start_wall is None:
            return 0.0
        return time.time() - self._segment_start_wall

    @staticmethod
    def _add_out_stream(container, in_stream):
        """Add a passthrough output stream matching the input. API differs by PyAV major."""
        add_from_template = getattr(container, "add_stream_from_template", None)
        if add_from_template is not None:
            return add_from_template(in_stream)
        # PyAV <= 11 path.
        return container.add_stream(template=in_stream)

    def _open_new(self) -> None:
        import av  # local import to keep test import paths easy

        now = _utc_now()
        ext = _FORMAT_EXTENSIONS.get(self._segment_format, ".mp4")
        seg_path, sidecar = _segment_paths(self._source_id, now, ext=ext)
        seg_path.parent.mkdir(parents=True, exist_ok=True)
        opts = dict(_FORMAT_OPTIONS.get(self._segment_format, {}))
        container = av.open(
            str(seg_path),
            "w",
            format=self._segment_format,
            options=opts,
        )
        v_out = self._add_out_stream(container, self._video_in) if self._video_in is not None else None
        a_out = self._add_out_stream(container, self._audio_in) if self._audio_in is not None else None
        self._container = container
        self._video_out = v_out
        self._audio_out = a_out
        self._path = seg_path
        self._sidecar_path = sidecar
        self._segment_start_wall = time.time()
        self._segment_start_dt = now
        self._last_pts_s = None
        self._bytes_muxed = 0
        self._pts_base = {}
        self._last_mux_dts = {}
        self._packet_counts = {"video": 0, "audio": 0}
        self._stream_media_end_s = {}
        self._dropped_missing_timestamp_packets = 0
        self._dropped_nonmonotonic_packets = 0
        self._adjusted_nonmonotonic_packets = 0
        self._mux_error_count = 0
        # MPEGTS needs SPS/PPS inlined before each keyframe or the stream is undecodable.
        # The dump_extra BSF was flaky for us; doing it manually is reliable.
        # Grab the video stream's codec extradata (Annex B for RTSP H.264) and prepend
        # it ourselves to each keyframe packet.
        self._video_extradata: Optional[bytes] = None
        self._video_bsf = None
        if self._segment_format == "mpegts" and self._video_in is not None and v_out is not None:
            try:
                ed = self._video_in.codec_context.extradata
                if ed:
                    self._video_extradata = bytes(ed)
            except Exception:
                self._video_extradata = None
        logger.info("segment open (%s): %s", self._segment_format, seg_path)

    def _close_current(self) -> None:
        if self._container is None:
            return
        try:
            self._container.close()
        except Exception:
            logger.exception("error closing segment %s", self._path)
        end_wall = time.time()
        path = self._path
        sidecar_path = self._sidecar_path
        start_dt = self._segment_start_dt
        start_wall = self._segment_start_wall or end_wall
        duration = end_wall - start_wall
        media_duration = max(self._stream_media_end_s.values(), default=0.0)
        media_ratio = (media_duration / duration) if duration > 0 else None
        video_duration = self._stream_media_end_s.get("video", 0.0)
        audio_duration = self._stream_media_end_s.get("audio", 0.0)
        video_ratio = (video_duration / duration) if duration > 0 else None
        audio_ratio = (audio_duration / duration) if duration > 0 else None
        video_packet_rate = (self._packet_counts.get("video", 0) / duration) if duration > 0 else 0.0
        size_bytes = 0
        if path is not None and path.exists():
            try:
                size_bytes = path.stat().st_size
            except OSError:
                pass
        if self._mux_error_count:
            capture_health = "mux_error"
        elif size_bytes <= 0 or sum(self._packet_counts.values()) == 0:
            capture_health = "empty"
        elif (
            self._video_in is not None
            and duration >= 5.0
            and (
                video_ratio is None
                or video_ratio < CAPTURE_MIN_MEDIA_RATIO
                or video_packet_rate < CAPTURE_MIN_VIDEO_PACKETS_PER_S
            )
        ):
            capture_health = "stalled"
        else:
            capture_health = "ok"
        # Gather motion + object events that fell inside this segment's wall-clock window.
        labels: list[str] = []
        motion_events: list[dict] = []
        object_events: list[dict] = []
        try:
            import motion_service
            motion_events = motion_service.events_between(self._source_id, start_wall, end_wall)
            if motion_events:
                labels.append("motion")
        except Exception:
            motion_events = []
        try:
            import vision_service
            object_events = vision_service.events_between(self._source_id, start_wall, end_wall)
            for cls in {e.get("class") for e in object_events if e.get("class")}:
                if cls and cls not in labels:
                    labels.append(cls)
        except Exception:
            object_events = []
        if sidecar_path is not None:
            try:
                sidecar = {
                    "segment_path": str(path),
                    "source": self._source_id,
                    "start_wall_ts": start_wall,
                    "end_wall_ts": end_wall,
                    "duration_s": round(duration, 3),
                    "media_duration_s": round(media_duration, 3),
                    "media_duration_ratio": round(media_ratio, 3) if media_ratio is not None else None,
                    "video_duration_s": round(video_duration, 3),
                    "video_duration_ratio": round(video_ratio, 3) if video_ratio is not None else None,
                    "video_packets_per_s": round(video_packet_rate, 3),
                    "audio_duration_s": round(audio_duration, 3),
                    "audio_duration_ratio": round(audio_ratio, 3) if audio_ratio is not None else None,
                    "capture_health": capture_health,
                    "bytes": size_bytes,
                    "packet_counts": dict(self._packet_counts),
                    "dropped_missing_timestamp_packets": self._dropped_missing_timestamp_packets,
                    "dropped_nonmonotonic_packets": self._dropped_nonmonotonic_packets,
                    "adjusted_nonmonotonic_packets": self._adjusted_nonmonotonic_packets,
                    "mux_errors": self._mux_error_count,
                    "labels": labels,
                    "detections": object_events,
                    "motion_events": motion_events,
                    "transcript_path": None,
                    "has_speech": False,
                    "clip_vector_ids": [],
                    "started_utc": start_dt.isoformat() if start_dt else None,
                }
                sidecar_path.write_text(json.dumps(sidecar, indent=2))
            except Exception:
                logger.exception("error writing sidecar %s", sidecar_path)
        # Reset
        self._container = None
        self._video_out = None
        self._audio_out = None
        # Publish segment.written event
        events_bus.publish(
            "segment.written",
            self._source_id,
            {
                "path": str(path) if path else None,
                "sidecar_path": str(sidecar_path) if sidecar_path else None,
                "start_wall_ts": start_wall,
                "end_wall_ts": end_wall,
                "duration_s": round(duration, 3),
                "media_duration_s": round(media_duration, 3),
                "video_duration_s": round(video_duration, 3),
                "video_packets_per_s": round(video_packet_rate, 3),
                "capture_health": capture_health,
                "bytes": size_bytes,
            },
        )
        if self._on_segment_closed is not None:
            try:
                self._on_segment_closed()
            except Exception:
                logger.exception("segment counter callback failed for %s", self._source_id)
        logger.info(
            "segment closed: %s (%.1fs wall, %.1fs media, %s, %d bytes)",
            path,
            duration,
            media_duration,
            capture_health,
            size_bytes,
        )
        if capture_health != "ok":
            logger.warning(
                "segment capture health %s for %s: wall=%.1fs media=%.1fs video=%.1fs video_rate=%.2f packets=%s mux_errors=%d dropped_missing_ts=%d dropped_dts=%d adjusted_dts=%d",
                capture_health,
                path,
                duration,
                media_duration,
                video_duration,
                video_packet_rate,
                self._packet_counts,
                self._mux_error_count,
                self._dropped_missing_timestamp_packets,
                self._dropped_nonmonotonic_packets,
                self._adjusted_nonmonotonic_packets,
            )
        self._path = None
        self._sidecar_path = None
        self._segment_start_wall = None
        self._segment_start_dt = None

    def _should_rotate(self, packet, is_video: bool) -> bool:
        if self._segment_start_wall is None:
            return False
        elapsed = self.elapsed
        if is_video:
            # Rotate on keyframe past target duration
            return elapsed >= SEGMENT_TARGET_S and bool(packet.is_keyframe)
        if self._video_in is not None:
            return False
        # Mic-only path: time-based rotation
        return elapsed >= SEGMENT_TARGET_S

    def _make_mux_packet(self, packet, target_stream, *, is_video: bool, data: Optional[bytes] = None):
        """Clone packet bytes and normalize timestamps for the current output segment."""
        import av as _av

        stream_key = "video" if is_video else "audio"
        src_dts = packet.dts if packet.dts is not None else packet.pts
        src_pts = packet.pts if packet.pts is not None else packet.dts
        if src_dts is None and src_pts is None:
            self._dropped_missing_timestamp_packets += 1
            return None
        ts = src_dts if src_dts is not None else src_pts
        if stream_key not in self._pts_base:
            self._pts_base[stream_key] = int(ts)
        base = self._pts_base[stream_key]
        out = _av.Packet(bytes(packet) if data is None else data)
        out.pts = int(src_pts - base) if src_pts is not None else None
        out.dts = int(src_dts - base) if src_dts is not None else None
        out.time_base = packet.time_base
        packet_duration = packet.duration or 0
        out.is_keyframe = bool(packet.is_keyframe)
        out.stream = target_stream

        if out.dts is not None:
            last_dts = self._last_mux_dts.get(stream_key)
            if last_dts is not None and out.dts <= last_dts:
                if is_video:
                    out.dts = last_dts + 1
                    if out.pts is None or out.pts < out.dts:
                        out.pts = out.dts
                    self._adjusted_nonmonotonic_packets += 1
                    if self._adjusted_nonmonotonic_packets <= 5 or self._adjusted_nonmonotonic_packets % 50 == 0:
                        logger.warning(
                            "adjusting non-monotonic %s packet for %s: dts=%s last=%s path=%s",
                            stream_key,
                            self._source_id,
                            out.dts,
                            last_dts,
                            self._path,
                        )
                else:
                    self._dropped_nonmonotonic_packets += 1
                    if self._dropped_nonmonotonic_packets <= 5 or self._dropped_nonmonotonic_packets % 50 == 0:
                        logger.warning(
                            "dropping non-monotonic %s packet for %s: dts=%s last=%s path=%s",
                            stream_key,
                            self._source_id,
                            out.dts,
                            last_dts,
                            self._path,
                        )
                    return None
            self._last_mux_dts[stream_key] = int(out.dts)

        ts_for_end = out.pts if out.pts is not None else out.dts
        if ts_for_end is not None:
            try:
                end_s = float((ts_for_end + packet_duration) * out.time_base)
                self._stream_media_end_s[stream_key] = max(
                    self._stream_media_end_s.get(stream_key, 0.0),
                    end_s,
                )
            except Exception:
                pass
        return out

    def feed_packet(self, packet, is_video: bool) -> None:
        if packet.dts is None and packet.pts is None:
            self._dropped_missing_timestamp_packets += 1
            return
        # For camera sources with video: always start segments on a keyframe.
        if self._container is None:
            if self._video_in is not None and is_video and not packet.is_keyframe:
                return  # wait for first keyframe before opening
            if self._video_in is not None and not is_video:
                return  # hold audio until first video keyframe opens the segment
            self._open_new()

        if self._should_rotate(packet, is_video):
            self._close_current()
            self._open_new()

        # Hard cap — if we exceeded SEGMENT_MAX_S without seeing a keyframe, force rotate.
        if self.elapsed >= SEGMENT_MAX_S:
            self._close_current()
            if self._video_in is not None and (not is_video or not packet.is_keyframe):
                return
            self._open_new()

        target_stream = self._video_out if is_video else self._audio_out
        if target_stream is None:
            return
        try:
            if is_video and self._video_extradata is not None and packet.is_keyframe:
                # Prepend extradata (Annex B SPS+PPS) to each keyframe so the MPEGTS
                # stream is self-contained and decoders don't fail on PPS reference.
                new_data = self._video_extradata + bytes(packet)
                new_pkt = self._make_mux_packet(packet, target_stream, is_video=is_video, data=new_data)
                if new_pkt is None:
                    return
                self._container.mux(new_pkt)
                self._bytes_muxed += new_pkt.size
            else:
                new_pkt = self._make_mux_packet(packet, target_stream, is_video=is_video)
                if new_pkt is None:
                    return
                self._container.mux(new_pkt)
                self._bytes_muxed += new_pkt.size
            self._packet_counts["video" if is_video else "audio"] += 1
        except Exception:
            self._mux_error_count += 1
            logger.exception("mux error on %s segment %s", self._source_id, self._path)
            # Best effort: close and reopen on next packet
            self._close_current()

    def close(self) -> None:
        self._close_current()


def _audio_resampler():
    import av

    return av.audio.resampler.AudioResampler(format="s16", layout="mono", rate=16000)


def _run_source(source: Source, on_pcm) -> None:
    """Main-stream worker: opens the source's main RTSP URL, demuxes audio + (for cameras) video,
    writes passthrough MP4 segments, and feeds decoded audio PCM for transcription."""
    import av
    backoff = source.reconnect_min_s
    while not _stop_event.is_set():
        worker = _workers.get(source.id)
        if worker:
            worker.state = "connecting"
        _publish_health(source.id, "connecting")
        container = None
        writer: Optional[_SegmentWriter] = None
        try:
            url = _main_stream_url(source)
            if not url:
                logger.warning("source %s has no URL; skipping", source.id)
                _publish_health(source.id, "down", "no url")
                return
            container = av.open(
                url,
                options={
                    "rtsp_transport": source.rtsp_transport,
                    "stimeout": str(OPEN_TIMEOUT_S * 1_000_000),
                    "rw_timeout": str(PKT_RECV_TIMEOUT_S * 1_000_000),
                    # Mirror Frigate's ffmpeg input flags for robust RTSP handling.
                    "fflags": "+genpts+discardcorrupt",
                    "avoid_negative_ts": "make_zero",
                    "max_delay": "500000",
                },
                timeout=OPEN_TIMEOUT_S,
            )
            audio_streams = [s for s in container.streams if s.type == "audio"]
            video_streams = [s for s in container.streams if s.type == "video"]
            # Cameras use main-stream video; mics skip video entirely.
            vstream = video_streams[0] if (video_streams and source.kind == "camera") else None
            if source.kind == "camera" and not CAMERA_RECORD_AUDIO_ENABLED:
                astream = None
            else:
                astream = audio_streams[0] if audio_streams else None

            demux_streams = [s for s in (vstream, astream) if s is not None]
            if not demux_streams:
                raise RuntimeError(f"no usable streams on {url}")

            resampler = _audio_resampler() if astream is not None else None

            if SEGMENT_WRITER_ENABLED:
                def on_segment_closed(source_id: str = source.id) -> None:
                    if current_worker := _workers.get(source_id):
                        current_worker.segments_written += 1

                # Mic: audio-only MP4. Camera: video-first, audio only when explicitly enabled.
                writer = _SegmentWriter(
                    source.id,
                    video_in_stream=vstream,
                    audio_in_stream=astream,
                    segment_format=source.segment_format,
                    on_segment_closed=on_segment_closed,
                )

            if worker:
                worker.state = "up"
            _publish_health(source.id, "up")
            backoff = source.reconnect_min_s
            last_audio_health_publish = 0.0

            for packet in container.demux(*demux_streams):
                if _stop_event.is_set():
                    break
                is_video = packet.stream.type == "video"
                packet_wall_ts = time.time()
                # Record first. The writer clones packets, so the original packet remains
                # available for keyframe taps and audio decoding below.
                if writer is not None:
                    try:
                        writer.feed_packet(packet, is_video=is_video)
                    except Exception:
                        logger.exception("segment writer error on %s", source.id)
                # Non-keyframes are never decoded on the camera video path.
                tapped_frames = []
                if (
                    CAMERA_KEYFRAME_VISION_ENABLED
                    and is_video
                    and packet.is_keyframe
                    and source.kind == "camera"
                ):
                    try:
                        for frame in packet.decode():
                            try:
                                tapped_frames.append(frame.to_ndarray(format="bgr24"))
                            except Exception:
                                pass
                    except Exception:
                        # Decode failures are non-fatal; the mux path still runs below.
                        pass
                # Feed decoded keyframes to the vision service.
                if tapped_frames:
                    try:
                        import vision_service
                        seg_path = str(writer._path) if writer is not None and writer._path is not None else None
                        for arr in tapped_frames:
                            vision_service.enqueue_frame(
                                source,
                                arr,
                                wall_ts=packet_wall_ts,
                                segment_path=seg_path,
                            )
                    except Exception:
                        logger.exception("vision dispatch error on %s", source.id)
                if (
                    not is_video
                    and astream is not None
                    and on_pcm is not None
                    and (source.kind != "camera" or CAMERA_AUDIO_TRANSCRIPTION_ENABLED)
                ):
                    # Decode audio only (video non-keyframes are never decoded).
                    if packet.dts is None and packet.pts is None:
                        continue
                    try:
                        for frame in packet.decode():
                            for out_frame in resampler.resample(frame):
                                pcm = bytes(out_frame.planes[0])
                                stream_ts = (
                                    float(out_frame.pts * out_frame.time_base)
                                    if out_frame.pts is not None
                                    else None
                                )
                                on_pcm(source.id, pcm, stream_ts)
                                now = time.time()
                                if now - last_audio_health_publish >= AUDIO_HEALTH_INTERVAL_S:
                                    _publish_health(
                                        source.id,
                                        "up",
                                        **_audio_health_payload(source, pcm, stream_ts),
                                    )
                                    last_audio_health_publish = now
                    except Exception:
                        logger.exception("audio decode error on %s", source.id)
        except Exception as exc:
            safe_error = _safe_error(exc)
            logger.warning("source %s error: %s", source.id, safe_error)
            if worker := _workers.get(source.id):
                worker.state = "reconnecting"
                worker.last_error = safe_error
            _publish_health(source.id, "reconnecting", safe_error)
        finally:
            try:
                if writer is not None:
                    writer.close()
            except Exception:
                pass
            try:
                if container is not None:
                    container.close()
            except Exception:
                pass
        if _stop_event.is_set():
            break
        sleep_s = min(source.reconnect_max_s, backoff) * (0.75 + random.random() * 0.5)
        logger.info("source %s backing off %.1fs", source.id, sleep_s)
        if _stop_event.wait(sleep_s):
            break
        backoff = min(source.reconnect_max_s, backoff * 2)
    _publish_health(source.id, "down")


def _run_detect_stream(source: Source) -> None:
    """Detect sub-stream worker: decode every video frame, feed to motion_service.

    Runs alongside _run_source as a second thread per camera. CPU-only; the frame
    rate (typically 10 fps on the sub-stream) is a natural throttle. Audio on the
    detect URL is ignored.
    """
    import av
    import motion_service

    url = source.video_sub_url
    if not url:
        logger.info("source %s has no detect sub-stream; skipping motion worker", source.id)
        return
    frame_interval_s = _motion_frame_interval_s(source)

    backoff = source.reconnect_min_s
    while not _stop_event.is_set():
        container = None
        events_bus.publish(
            "source.health", source.id, {"state": "connecting", "role": "detect"},
        )
        try:
            container = av.open(
                url,
                options={
                    "rtsp_transport": source.rtsp_transport,
                    "stimeout": str(OPEN_TIMEOUT_S * 1_000_000),
                    "rw_timeout": str(PKT_RECV_TIMEOUT_S * 1_000_000),
                    "fflags": "+genpts+discardcorrupt",
                    "max_delay": "500000",
                },
                timeout=OPEN_TIMEOUT_S,
            )
            video_streams = [s for s in container.streams if s.type == "video"]
            if not video_streams:
                raise RuntimeError(f"no video on detect sub-stream {url}")
            vstream = video_streams[0]
            events_bus.publish(
                "source.health", source.id, {"state": "up", "role": "detect"},
            )
            backoff = source.reconnect_min_s
            last_frame_wall = 0.0
            for packet in container.demux(vstream):
                if _stop_event.is_set():
                    break
                if packet.dts is None and packet.pts is None:
                    continue
                now = time.time()
                if frame_interval_s > 0 and (now - last_frame_wall) < frame_interval_s:
                    continue
                try:
                    for frame in packet.decode():
                        try:
                            arr = frame.to_ndarray(format="bgr24")
                        except Exception:
                            continue
                        try:
                            motion_service.process_frame(source, arr)
                        except Exception:
                            logger.exception("motion processing error on %s", source.id)
                        last_frame_wall = time.time()
                except Exception:
                    # Decode errors are non-fatal; skip packet
                    continue
        except Exception as exc:
            safe_error = _safe_error(exc)
            logger.warning("detect stream %s error: %s", source.id, safe_error)
            events_bus.publish(
                "source.health", source.id,
                {"state": "reconnecting", "role": "detect", "error": safe_error},
            )
        finally:
            try:
                if container is not None:
                    container.close()
            except Exception:
                pass
        if _stop_event.is_set():
            break
        sleep_s = min(source.reconnect_max_s, backoff) * (0.75 + random.random() * 0.5)
        logger.info("detect stream %s backing off %.1fs", source.id, sleep_s)
        if _stop_event.wait(sleep_s):
            break
        backoff = min(source.reconnect_max_s, backoff * 2)


def start_all() -> dict[str, _Worker]:
    with _start_lock:
        if _workers:
            return _workers
        _stop_event.clear()
        import streaming_transcription_service as streaming

        def on_pcm(source_id: str, pcm_bytes: bytes, stream_ts: Optional[float]):
            streaming.enqueue_audio(source_id, pcm_bytes, stream_ts)

        for src in sources_config.enabled_sources():
            if src.kind not in ("camera", "mic"):
                logger.warning("unknown kind %r for source %s", src.kind, src.id)
                continue
            if not src.audio_url and not src.video_main_url:
                logger.warning("source %s has no URL; skipping", src.id)
                continue
            t = threading.Thread(
                target=_run_source,
                args=(src, on_pcm),
                daemon=True,
                name=f"rtsp-ingest-{src.id}",
            )
            worker = _Worker(source=src, thread=t)
            _workers[src.id] = worker
            t.start()
            logger.info("started rtsp ingest for %s (%s)", src.id, _redact_sensitive(_main_stream_url(src)))
            # Cameras also get a detect-substream worker for motion.
            if _should_start_detect_stream(src):
                dt = threading.Thread(
                    target=_run_detect_stream,
                    args=(src,),
                    daemon=True,
                    name=f"rtsp-detect-{src.id}",
                )
                dt.start()
                logger.info("started detect-stream worker for %s (%s)", src.id, _redact_sensitive(src.video_sub_url))
            elif src.kind == "camera" and src.video_sub_url:
                logger.info(
                    "motion detect stream disabled for %s (ARCHIVIST_CAMERA_MOTION_ENABLED=false)",
                    src.id,
                )
        return _workers


def stop_all(timeout: float = 5.0) -> None:
    _stop_event.set()
    deadline = time.time() + timeout
    for w in list(_workers.values()):
        remaining = max(0.0, deadline - time.time())
        w.thread.join(timeout=remaining)
    _workers.clear()


def status() -> list[dict]:
    return [
        {
            "id": w.source.id,
            "state": w.state,
            "last_error": w.last_error,
            "kind": w.source.kind,
            "location": w.source.location,
            "segments_written": w.segments_written,
        }
        for w in _workers.values()
    ]


def configured_sources_status() -> list[dict]:
    """Return the configured ingest inventory without exposing source URLs."""
    return [
        {
            "id": src.id,
            "enabled": src.enabled,
            "kind": src.kind,
            "location": src.location,
            "has_audio": bool(src.audio_url),
            "has_video_main": bool(src.video_main_url),
            "has_video_sub": bool(src.video_sub_url),
            "motion_enabled": bool(src.motion),
            "transcription_enabled": bool(src.transcription.enabled),
            "segment_format": src.segment_format,
        }
        for src in sources_config.enabled_sources()
    ]
