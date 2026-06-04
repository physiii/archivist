import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { WorkspaceEmpty, WorkspacePage, WorkspacePanel } from "../components/Workspace";
import type { MediaAsset, MediaPipelineJob } from "../types";
import {
  formatAgeSec,
  formatBytes,
  formatDuration,
  jobPhaseLabel,
  relativeTime,
} from "./mediaShared";

interface SourceHealth {
  status: string;
  last_event_age_s: number | null;
  last_health_state?: string;
  error: string | null;
}

interface RtspSource {
  id: string;
  state: string;
  segments_written: number;
  kind: "camera" | "mic";
  location: string;
  last_error: string | null;
}

interface StreamingSource {
  source: string;
  submitted: number;
  dropped: number;
  qsize: number;
  alive: boolean;
}

interface MotionSource {
  source: string;
  events_published: number;
  frames_seen: number;
}

interface VisionSource {
  source: string;
  detections: number;
  embeddings: number;
  frames_seen: number;
}

interface SourcesStatus {
  rtsp: RtspSource[];
  streaming: StreamingSource[];
  motion: MotionSource[];
  vision: (VisionSource | { clip_available?: boolean; yolo_available?: boolean })[];
  archive: { alive: boolean; enabled: boolean; last_pass?: { scanned: number; moved: number } };
  retention: { alive: boolean; enabled: boolean };
}

interface TranscribeStatus {
  available: boolean;
  model: string;
  device: string;
  compute_type: string;
}

interface CompatStatus {
  current: number;
  stale: number;
  broken: number;
  total: number;
}

interface IngestSource {
  id: string;
  kind: "camera" | "mic";
  location: string;
  state: "up" | "down" | "stale" | "unknown";
  lastEventAge: number | null;
  segmentsWritten: number;
  transcriptionsSubmitted: number;
  dropped: number;
  queueSize: number;
  streamAlive: boolean;
  lastError: string | null;
  motionEvents: number | null;
  visionDetections: number | null;
}

export default function MediaPage() {
  const navigate = useNavigate();

  const [assets, setAssets] = useState<MediaAsset[]>([]);
  const [jobs, setJobs] = useState<MediaPipelineJob[]>([]);
  const [processPath, setProcessPath] = useState("");
  const [assetQuery, setAssetQuery] = useState("");
  const [working, setWorking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [compatStatus, setCompatStatus] = useState<CompatStatus | null>(null);
  const [sourceHealth, setSourceHealth] = useState<Record<string, SourceHealth> | null>(null);
  const [sourcesStatus, setSourcesStatus] = useState<SourcesStatus | null>(null);
  const [transcribeStatus, setTranscribeStatus] = useState<TranscribeStatus | null>(null);
  const [migrating, setMigrating] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [assetsRes, jobsRes, compatRes, healthRes, sourcesRes, transcribeRes] = await Promise.all([
        fetch("/api/media/assets"),
        fetch("/api/media/jobs"),
        fetch("/api/media/pipeline/compat-status"),
        fetch("/health"),
        fetch("/api/media/sources/status"),
        fetch("/api/transcribe/status"),
      ]);
      if (assetsRes.ok) {
        const data = (await assetsRes.json()) as { assets?: MediaAsset[] };
        setAssets(data.assets ?? []);
      }
      if (jobsRes.ok) {
        const data = (await jobsRes.json()) as { jobs?: MediaPipelineJob[] };
        setJobs(data.jobs ?? []);
      }
      if (compatRes.ok) {
        setCompatStatus(await compatRes.json() as CompatStatus);
      }
      if (healthRes.ok) {
        const health = (await healthRes.json()) as { components?: { source_ingest?: { sources?: Record<string, SourceHealth> } } };
        setSourceHealth(health.components?.source_ingest?.sources ?? null);
      }
      if (sourcesRes.ok) {
        setSourcesStatus(await sourcesRes.json() as SourcesStatus);
      }
      if (transcribeRes.ok) {
        setTranscribeStatus(await transcribeRes.json() as TranscribeStatus);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to refresh media status.");
    }
  }, []);

  useEffect(() => {
    void fetchData();
    const interval = setInterval(() => {
      void fetchData();
    }, 4000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const ingestSources = useMemo<IngestSource[]>(() => {
    if (!sourcesStatus) return [];
    const healthMap = sourceHealth ?? {};
    const streamMap = new Map(sourcesStatus.streaming.map(s => [s.source, s]));
    const motionMap = new Map(
      sourcesStatus.motion.map(s => [s.source, s])
    );
    const visionSources = sourcesStatus.vision.filter(
      (v): v is VisionSource => "source" in v
    );
    const visionMap = new Map(visionSources.map(s => [s.source, s]));

    return sourcesStatus.rtsp.map(rtsp => {
      const health = healthMap[rtsp.id];
      const stream = streamMap.get(rtsp.id);
      const motion = motionMap.get(rtsp.id);
      const vision = visionMap.get(rtsp.id);

      let state: "up" | "down" | "stale" | "unknown" = "unknown";
      if (health) {
        if (health.status === "healthy" || health.last_health_state === "up") state = "up";
        else if (health.status === "stale") state = "stale";
        else if (health.status === "down") state = "down";
      } else if (rtsp.state === "up") state = "up";
      else if (rtsp.state === "down") state = "down";

      return {
        id: rtsp.id,
        kind: rtsp.kind,
        location: rtsp.location,
        state,
        lastEventAge: health?.last_event_age_s ?? null,
        segmentsWritten: rtsp.segments_written,
        transcriptionsSubmitted: stream?.submitted ?? 0,
        dropped: stream?.dropped ?? 0,
        queueSize: stream?.qsize ?? 0,
        streamAlive: stream?.alive ?? false,
        lastError: rtsp.last_error ?? health?.error ?? null,
        motionEvents: motion?.events_published ?? null,
        visionDetections: vision?.detections ?? null,
      };
    });
  }, [sourcesStatus, sourceHealth]);

  const jobsByMediaId = useMemo(() => {
    const map = new Map<string, MediaPipelineJob>();
    for (const job of jobs) {
      const existing = map.get(job.media_id);
      if (!existing || existing.started_at < job.started_at) {
        map.set(job.media_id, job);
      }
    }
    return map;
  }, [jobs]);

  const sortedJobs = useMemo(
    () => [...jobs].sort((left, right) => Math.max(right.finished_at, right.started_at) - Math.max(left.finished_at, left.started_at)),
    [jobs],
  );
  const activeJobs = useMemo(
    () => sortedJobs.filter((job) => job.status !== "done" && job.status !== "error"),
    [sortedJobs],
  );
  const recentJobs = useMemo(
    () => sortedJobs.filter((job) => job.status === "done" || job.status === "error").slice(0, 3),
    [sortedJobs],
  );

  const filteredAssets = useMemo(() => {
    const query = assetQuery.trim().toLowerCase();
    const sorted = [...assets].sort((left, right) => right.indexed_at - left.indexed_at);
    if (!query) return sorted;
    return sorted.filter((asset) => {
      const haystack = `${asset.filename} ${asset.path} ${asset.media_id}`.toLowerCase();
      return haystack.includes(query);
    });
  }, [assetQuery, assets]);

  const totalDurationHours = useMemo(
    () => (assets.reduce((sum, asset) => sum + (asset.duration_s || 0), 0) / 3600).toFixed(1),
    [assets],
  );

  const totalMotionEvents = useMemo(
    () => sourcesStatus?.motion.reduce((sum, m) => sum + m.events_published, 0) ?? 0,
    [sourcesStatus],
  );

  const totalVisionDetections = useMemo(() => {
    if (!sourcesStatus) return 0;
    return sourcesStatus.vision
      .filter((v): v is VisionSource => "source" in v)
      .reduce((sum, v) => sum + v.detections, 0);
  }, [sourcesStatus]);

  const totalVisionEmbeddings = useMemo(() => {
    if (!sourcesStatus) return 0;
    return sourcesStatus.vision
      .filter((v): v is VisionSource => "source" in v)
      .reduce((sum, v) => sum + v.embeddings, 0);
  }, [sourcesStatus]);

  async function submitProcess() {
    if (!processPath.trim() || working) return;
    setWorking(true);
    setError(null);
    setNotice(null);
    try {
      const response = await fetch("/api/media/process", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path: processPath.trim() }),
      });
      const data = (await response.json()) as { error?: string };
      if (!response.ok) {
        setError(data.error || `HTTP ${response.status}`);
      } else {
        setProcessPath("");
        await fetchData();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start media processing.");
    } finally {
      setWorking(false);
    }
  }

  const healthyCount = ingestSources.filter(s => s.state === "up").length;

  return (
    <WorkspacePage
      eyebrow="Media Operations"
      title="Live Ingest & Processing"
      subtitle="RTSP camera and microphone pipeline status, processing queue, and processed file catalog."
      actions={
        <button onClick={() => void fetchData()}>
          Refresh
        </button>
      }
      stats={[
        {
          label: "Sources",
          value: ingestSources.length || "—",
          meta: `${healthyCount} healthy`,
          tone: ingestSources.length > 0 && healthyCount < ingestSources.length ? "warning" : "success",
        },
        {
          label: "Pipeline",
          value: compatStatus ? `${compatStatus.current.toLocaleString()}` : "—",
          meta: compatStatus?.broken ? `${compatStatus.broken} broken` : "All current",
          tone: compatStatus?.broken ? "warning" : "default",
        },
        {
          label: "Transcription",
          value: transcribeStatus?.available ? "Active" : "Offline",
          meta: transcribeStatus ? `${transcribeStatus.model} / ${transcribeStatus.device}` : "—",
          tone: transcribeStatus?.available ? "success" : "warning",
        },
      ]}
    >
      {error ? <div className="error-banner">{error}</div> : null}
      {notice ? <div className="notice-banner">{notice}</div> : null}

      <WorkspacePanel
        title="Live ingest"
        description={ingestSources.length > 0 ? `${healthyCount}/${ingestSources.length} sources streaming` : undefined}
      >
        {ingestSources.length === 0 ? (
          <WorkspaceEmpty title="Loading sources..." description="Waiting for ingest status data." />
        ) : (
          <div className="workspace-grid workspace-grid--two">
            {ingestSources.map(source => (
              <div key={source.id} className="record-row static">
                <div className="record-row-head">
                  <div className="record-row-title-group">
                    <strong className="record-row-title">
                      {source.kind === "mic" ? "[MIC]" : "[CAM]"} {source.id.replace(/_/g, " ")}
                    </strong>
                    <span className={`workspace-chip ${
                      source.state === "up" ? "workspace-chip--success" :
                      source.state === "stale" ? "workspace-chip--warning" :
                      source.state === "down" ? "workspace-chip--warning" :
                      ""
                    }`}>
                      {source.state}
                    </span>
                    <span className="workspace-chip">{source.kind}</span>
                  </div>
                  <span className="record-row-meta">
                    {formatAgeSec(source.lastEventAge)}
                  </span>
                </div>
                <span className="record-row-subtitle">
                  {source.segmentsWritten.toLocaleString()} segments · {source.transcriptionsSubmitted.toLocaleString()} transcriptions
                  {source.dropped > 0 ? ` · ${source.dropped} dropped` : ""}
                  {source.queueSize > 0 ? ` · queue: ${source.queueSize}` : ""}
                </span>
                {source.motionEvents != null && (
                  <span className="record-row-preview">
                    {source.motionEvents.toLocaleString()} motion events
                    {source.visionDetections != null ? ` · ${source.visionDetections} detections` : ""}
                  </span>
                )}
                {source.lastError ? (
                  <span className="record-row-preview" style={{ color: "var(--text-warning, #ffd2a0)" }}>
                    {source.lastError}
                  </span>
                ) : null}
              </div>
            ))}
          </div>
        )}
      </WorkspacePanel>

      <WorkspacePanel title="System overview">
        <dl className="detail-list detail-list--inline">
          <div>
            <dt>Transcription</dt>
            <dd>{transcribeStatus ? `${transcribeStatus.model} · ${transcribeStatus.device} · ${transcribeStatus.compute_type}` : "—"}</dd>
          </div>
          <div>
            <dt>Pipeline</dt>
            <dd>
              {compatStatus ? `${compatStatus.current.toLocaleString()} current` : "—"}
              {compatStatus && compatStatus.stale > 0 ? ` · ${compatStatus.stale} stale` : ""}
              {compatStatus && compatStatus.broken > 0 ? ` · ${compatStatus.broken} broken` : ""}
              {compatStatus && (compatStatus.stale > 0 || compatStatus.broken > 0) ? (
                <>
                  {" "}
                  <button
                    className="tiny-button"
                    disabled={migrating}
                    onClick={async () => {
                      setMigrating(true);
                      try {
                        const res = await fetch("/api/media/pipeline/migrate", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({}) });
                        if (res.ok) {
                          const result = await res.json() as { migrated: number };
                          setNotice(`Migrated ${result.migrated} pipeline results.`);
                          await fetchData();
                        } else {
                          const data = await res.json() as { error?: string };
                          setError(data.error ?? "Migration failed");
                        }
                      } catch (err) {
                        setError(err instanceof Error ? err.message : "Migration failed");
                      } finally {
                        setMigrating(false);
                      }
                    }}
                  >
                    {migrating ? "Migrating..." : "Migrate"}
                  </button>
                </>
              ) : null}
            </dd>
          </div>
          <div>
            <dt>Archive</dt>
            <dd>{sourcesStatus?.archive ? `${sourcesStatus.archive.alive ? "Active" : "Stopped"} · ${sourcesStatus.archive.last_pass?.scanned?.toLocaleString() ?? 0} scanned` : "—"}</dd>
          </div>
          <div>
            <dt>Motion</dt>
            <dd>{totalMotionEvents.toLocaleString()} events</dd>
          </div>
          <div>
            <dt>Vision</dt>
            <dd>{totalVisionDetections} detections · {totalVisionEmbeddings.toLocaleString()} embeddings</dd>
          </div>
          <div>
            <dt>Retention</dt>
            <dd>{sourcesStatus?.retention ? (sourcesStatus.retention.alive ? "Active" : "Stopped") : "—"}</dd>
          </div>
        </dl>
      </WorkspacePanel>

      <div className="workspace-grid workspace-grid--two">
        <WorkspacePanel
          title="Processing queue"
          description={`${activeJobs.length} active · ${assets.length} assets (${totalDurationHours}h)`}
        >
          <div className="inline-form compact" style={{ marginBottom: "var(--sp-4)" }}>
            <input
              value={processPath}
              onChange={(event) => setProcessPath(event.target.value)}
              placeholder="Process a specific media file path"
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  void submitProcess();
                }
              }}
            />
            <button onClick={() => void submitProcess()} disabled={working || !processPath.trim()}>
              {working ? "Processing..." : "Process"}
            </button>
          </div>

          {activeJobs.length === 0 ? (
            <WorkspaceEmpty title="No active jobs" description="The queue is clear." />
          ) : (
            <div className="record-list" role="list" aria-label="Active media jobs">
              {activeJobs.map((job) => (
                <button
                  key={job.job_id}
                  type="button"
                  className="record-row"
                  onClick={() => navigate(`/media/${job.media_id}`)}
                >
                  <div className="record-row-head">
                    <div className="record-row-title-group">
                      <strong className="record-row-title mono">{job.job_id}</strong>
                      <span className={`workspace-chip ${job.status === "error" ? "workspace-chip--warning" : "workspace-chip--accent"}`}>
                        {job.status}
                      </span>
                    </div>
                    <span className="record-row-meta">{relativeTime(job.started_at)}</span>
                  </div>
                  <span className="record-row-subtitle">{jobPhaseLabel(job)}</span>
                  <div className="progress-meter compact" aria-label={`Progress for ${job.job_id}`}>
                    <div className="progress-meter-fill" style={{ width: `${Math.max(0, Math.min(100, job.progress * 100))}%` }} />
                  </div>
                </button>
              ))}
            </div>
          )}

          {recentJobs.length > 0 ? (
            <div className="workspace-stack">
              <h3 className="subpanel-title">Recent completions</h3>
              <div className="record-list compact" role="list" aria-label="Recent media jobs">
                {recentJobs.map((job) => (
                  <button
                    key={job.job_id}
                    type="button"
                    className="record-row"
                    onClick={() => navigate(`/media/${job.media_id}`)}
                  >
                    <div className="record-row-head">
                      <div className="record-row-title-group">
                        <strong className="record-row-title mono">{job.job_id}</strong>
                        <span className={`workspace-chip ${job.status === "done" ? "workspace-chip--success" : "workspace-chip--warning"}`}>
                          {job.status === "done" ? "ready" : job.status}
                        </span>
                      </div>
                      <span className="record-row-meta">{relativeTime(job.finished_at || job.started_at)}</span>
                    </div>
                    <span className="record-row-subtitle">{jobPhaseLabel(job)}</span>
                  </button>
                ))}
              </div>
            </div>
          ) : null}
        </WorkspacePanel>

        <WorkspacePanel
          title="Processed files"
          description={`${filteredAssets.length} of ${assets.length} shown`}
        >
          <div className="inline-form compact">
            <input
              value={assetQuery}
              onChange={(event) => setAssetQuery(event.target.value)}
              placeholder="Filter by filename, path, or media id"
            />
          </div>
          {filteredAssets.length === 0 ? (
            <WorkspaceEmpty title="No assets found" description="Adjust the filter or process a media file." />
          ) : (
            <div className="record-list" role="list" aria-label="Processed media assets">
              {filteredAssets.slice(0, 20).map((asset) => {
                const job = jobsByMediaId.get(asset.media_id);
                const isReady = job?.status === "done";
                return (
                  <button
                    key={asset.media_id}
                    type="button"
                    className="record-row"
                    onClick={() => navigate(`/media/${asset.media_id}`)}
                  >
                    <div className="record-row-head">
                      <div className="record-row-title-group">
                        <strong className="record-row-title" title={asset.filename}>
                          {asset.subject_line ?? asset.filename}
                        </strong>
                        <span className="workspace-chip">{asset.modality}</span>
                        {asset.pipeline_current ? (
                          <span className="workspace-chip workspace-chip--success">current</span>
                        ) : asset.has_result ? (
                          <span className="workspace-chip workspace-chip--warning">stale</span>
                        ) : null}
                        {job ? (
                          <span className={`workspace-chip ${isReady ? "workspace-chip--success" : job.status === "error" ? "workspace-chip--warning" : "workspace-chip--accent"}`}>
                            {isReady ? "ready" : job.status}
                          </span>
                        ) : null}
                      </div>
                      <span className="record-row-meta">{relativeTime(asset.indexed_at)}</span>
                    </div>
                    <span className="record-row-subtitle mono" title={asset.path}>
                      {asset.subject_line ? asset.filename : asset.path}
                    </span>
                    <span className="record-row-preview">
                      {asset.duration_s > 0 ? `${formatDuration(asset.duration_s)} · ` : ""}
                      {formatBytes(asset.file_size_bytes)}
                      {asset.codec ? ` · ${asset.codec}` : ""}
                    </span>
                  </button>
                );
              })}
            </div>
          )}
        </WorkspacePanel>
      </div>
    </WorkspacePage>
  );
}
