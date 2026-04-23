import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { WorkspaceEmpty, WorkspacePage, WorkspacePanel } from "../components/Workspace";
import type { MediaAsset, MediaPipelineJob } from "../types";
import {
  formatBytes,
  formatDuration,
  jobPhaseLabel,
  relativeTime,
} from "./mediaShared";

export default function MediaPage() {
  const navigate = useNavigate();

  const [assets, setAssets] = useState<MediaAsset[]>([]);
  const [jobs, setJobs] = useState<MediaPipelineJob[]>([]);
  const [processPath, setProcessPath] = useState("");
  const [assetQuery, setAssetQuery] = useState("");
  const [working, setWorking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [compatStatus, setCompatStatus] = useState<{ current: number; stale: number; broken: number; total: number } | null>(null);
  const [migrating, setMigrating] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [assetsRes, jobsRes, compatRes] = await Promise.all([
        fetch("/api/media/assets"),
        fetch("/api/media/jobs"),
        fetch("/api/media/pipeline/compat-status"),
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
        setCompatStatus(await compatRes.json() as { current: number; stale: number; broken: number; total: number });
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
    () => sortedJobs.filter((job) => job.status === "done" || job.status === "error").slice(0, 6),
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

  return (
    <WorkspacePage
      eyebrow="Media Operations"
      title="Media Processing"
      subtitle="Queue visibility, processed catalog, and file detail pages. Media files are discovered automatically by the indexing service."
      actions={
        <button onClick={() => void fetchData()}>
          Refresh
        </button>
      }
      stats={[
        { label: "Assets", value: assets.length, meta: `${totalDurationHours}h processed` },
        { label: "Queue", value: activeJobs.length, meta: `${recentJobs.length} recent completions` },
      ]}
    >
      {error ? <div className="error-banner">{error}</div> : null}
      {notice ? <div className="notice-banner">{notice}</div> : null}
      {compatStatus && (compatStatus.stale > 0 || compatStatus.broken > 0) ? (
        <div className="health-banner health-banner--warning">
          <span className="health-banner-icon">{"●"}</span>
          <span className="health-banner-text">
            Pipeline: {compatStatus.stale > 0 ? `${compatStatus.stale} stale` : ""}{compatStatus.stale > 0 && compatStatus.broken > 0 ? ", " : ""}{compatStatus.broken > 0 ? `${compatStatus.broken} broken` : ""} of {compatStatus.total} results.
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
                    setNotice(`Migrated ${result.migrated} pipeline results to current version.`);
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
              {migrating ? "Migrating..." : "Migrate all"}
            </button>
          </span>
        </div>
      ) : null}

      <div className="media-watch-callout">
        Media files in your indexing targets are automatically routed here for rich processing.{" "}
        <Link to="/indexing">Configure directories on the Indexing page.</Link>
        {" "}You can also process individual files below.
      </div>

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
          {working ? "Processing..." : "Process file"}
        </button>
      </div>

      <div className="workspace-grid workspace-grid--two">
        <WorkspacePanel
          title="Processing queue"
          description="Rows open the dedicated file page, so the catalog and the detail view no longer fight for space."
        >
          {activeJobs.length === 0 ? (
            <WorkspaceEmpty title="No active jobs" description="The queue is clear right now. Recent completions are listed below for quick review." />
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
                  <span className="record-row-preview">
                    {job.status === "error" ? job.error || "Pipeline failed" : `${Math.round(job.progress * 100)}% complete`}
                  </span>
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
                    <span className="record-row-preview">
                      {job.status === "done"
                        ? "Open the file page to review subject line, summary, walkthrough, and transcript."
                        : job.error || "Processing ended with an error."}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          ) : null}
        </WorkspacePanel>

        <WorkspacePanel
          title="Processed files"
          description="Selecting a file opens a dedicated detail page instead of expanding a second page underneath the catalog."
        >
          <div className="inline-form compact">
            <input
              value={assetQuery}
              onChange={(event) => setAssetQuery(event.target.value)}
              placeholder="Filter by filename, path, or media id"
            />
            <span className="workspace-inline-meta">{filteredAssets.length} visible</span>
          </div>
          {filteredAssets.length === 0 ? (
            <WorkspaceEmpty title="No assets found" description="Adjust the filter or process a media file to populate the catalog." />
          ) : (
            <div className="record-list" role="list" aria-label="Processed media assets">
              {filteredAssets.map((asset) => {
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
                        {asset.has_result && !asset.pipeline_current ? (
                          <span className="workspace-chip workspace-chip--warning">stale</span>
                        ) : asset.pipeline_current ? (
                          <span className="workspace-chip workspace-chip--success">current</span>
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
                      {job ? ` · ${jobPhaseLabel(job)}` : ""}
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
