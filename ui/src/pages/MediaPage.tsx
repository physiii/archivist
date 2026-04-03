import { useCallback, useEffect, useState } from "react";

interface MediaAsset {
  media_id: string;
  path: string;
  filename: string;
  modality: string;
  duration_s: number;
  file_hash: string;
  file_size_bytes: number;
  created_at: number;
  indexed_at: number;
}

interface PipelineJob {
  job_id: string;
  media_id: string;
  status: string;
  current_layer: string;
  progress: number;
  started_at: number;
  finished_at: number;
  error: string;
  artifacts_count: number;
  events_count: number;
  recaps_count: number;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1073741824) return `${(bytes / 1048576).toFixed(1)} MB`;
  return `${(bytes / 1073741824).toFixed(2)} GB`;
}

function formatDuration(s: number): string {
  if (s < 60) return `${s.toFixed(0)}s`;
  if (s < 3600) return `${Math.floor(s / 60)}m ${Math.floor(s % 60)}s`;
  return `${Math.floor(s / 3600)}h ${Math.floor((s % 3600) / 60)}m`;
}

function relativeTime(ts: number): string {
  if (!ts) return "—";
  const diff = (Date.now() / 1000 - ts) | 0;
  if (diff < 60) return "just now";
  if (diff < 3600) return `${(diff / 60) | 0}m ago`;
  if (diff < 86400) return `${(diff / 3600) | 0}h ago`;
  return `${(diff / 86400) | 0}d ago`;
}

const LAYER_LABELS: Record<string, string> = {
  L0_evidence: "Registering asset",
  L1_filtering: "Filtering & scene detection",
  L2_events: "Extracting events",
  L3_recaps: "Building recaps",
  L4_memory: "Constructing memory",
  L5_compose: "Composing document",
};

export default function MediaPage() {
  const [assets, setAssets] = useState<MediaAsset[]>([]);
  const [jobs, setJobs] = useState<PipelineJob[]>([]);
  const [processPath, setProcessPath] = useState("");
  const [working, setWorking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedAsset, setSelectedAsset] = useState<string | null>(null);
  const [pipelineResult, setPipelineResult] = useState<any>(null);

  const fetchData = useCallback(async () => {
    try {
      const [assetsRes, jobsRes] = await Promise.all([
        fetch("/api/media/assets"),
        fetch("/api/media/jobs"),
      ]);
      if (assetsRes.ok) {
        const data = await assetsRes.json();
        setAssets(data.assets || []);
      }
      if (jobsRes.ok) {
        const data = await jobsRes.json();
        setJobs(data.jobs || []);
      }
    } catch {}
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 4000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const submitProcess = async () => {
    if (!processPath.trim() || working) return;
    setWorking(true);
    setError(null);
    try {
      const res = await fetch("/api/media/process", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path: processPath.trim() }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error || `HTTP ${res.status}`);
      } else {
        setProcessPath("");
        fetchData();
      }
    } catch (e: any) {
      setError(e.message || "Failed");
    } finally {
      setWorking(false);
    }
  };

  const loadPipelineResult = async (mediaId: string) => {
    setSelectedAsset(mediaId);
    try {
      const res = await fetch(`/api/media/pipeline/${mediaId}`);
      if (res.ok) {
        setPipelineResult(await res.json());
      } else {
        setPipelineResult(null);
      }
    } catch {
      setPipelineResult(null);
    }
  };

  return (
    <div>
      <h2 style={{ margin: "0 0 16px" }}>Media Processing</h2>

      {error && <div className="error-banner">{error}</div>}

      {/* Process new file */}
      <div className="panel">
        <h3 style={{ margin: "0 0 10px", fontSize: "0.95rem" }}>Process Media File</h3>
        <div className="toolbar">
          <input
            type="text"
            placeholder="File path (e.g. /media/mass/recordings/meeting.mp4)"
            value={processPath}
            onChange={(e) => setProcessPath(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && submitProcess()}
            style={{ flex: 1 }}
          />
          <button onClick={submitProcess} disabled={working || !processPath.trim()}>
            {working ? "Processing..." : "Process"}
          </button>
        </div>
        <p className="muted" style={{ margin: "6px 0 0", fontSize: "0.8rem" }}>
          Runs the 6-layer pipeline: Evidence → Filter → Events → Recaps → Memory → Document
        </p>
      </div>

      {/* Active jobs */}
      {jobs.length > 0 && (
        <div className="panel">
          <h3 style={{ margin: "0 0 10px", fontSize: "0.95rem" }}>Pipeline Jobs</h3>
          <div className="target-health-list">
            {jobs.map((job) => (
              <div key={job.job_id} className="target-health-row">
                <div className="target-health-header">
                  <span className="mono" style={{ fontSize: "0.82rem" }}>{job.job_id}</span>
                  <span className={`health-badge ${job.status === "done" ? "ready" : job.status === "error" ? "issue" : ""}`}>
                    {job.status}
                  </span>
                </div>
                {job.current_layer && (
                  <div className="muted" style={{ fontSize: "0.82rem", marginTop: 4 }}>
                    {LAYER_LABELS[job.current_layer] || job.current_layer}
                  </div>
                )}
                {job.status !== "done" && job.status !== "error" && (
                  <div style={{ marginTop: 6, height: 4, borderRadius: 2, background: "rgba(216,227,255,0.08)", overflow: "hidden" }}>
                    <div style={{ height: "100%", width: `${(job.progress * 100).toFixed(0)}%`, background: "#3b82f6", borderRadius: 2, transition: "width 0.3s" }} />
                  </div>
                )}
                {job.error && <div className="muted" style={{ color: "#ffc8d0", fontSize: "0.8rem", marginTop: 4 }}>{job.error}</div>}
                <div className="target-health-meta" style={{ marginTop: 4 }}>
                  <span>{job.events_count} events</span>
                  <span>{job.recaps_count} recaps</span>
                  <span>{job.artifacts_count} artifacts</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Processed assets */}
      <div className="panel">
        <h3 style={{ margin: "0 0 10px", fontSize: "0.95rem" }}>
          Processed Media ({assets.length})
        </h3>
        {assets.length === 0 ? (
          <p className="muted" style={{ fontSize: "0.85rem" }}>No media files processed yet.</p>
        ) : (
          <div className="target-health-list">
            {assets.map((asset: any) => (
              <div
                key={asset.media_id}
                className={`snapshot-row clickable${selectedAsset === asset.media_id ? " active" : ""}`}
                onClick={() => loadPipelineResult(asset.media_id)}
              >
                <div className="target-health-header">
                  <div>
                    <strong style={{ fontSize: "0.88rem" }}>{asset.filename}</strong>
                    <span className="pill" style={{ marginLeft: 8 }}>{asset.modality}</span>
                  </div>
                  <span className="muted" style={{ fontSize: "0.78rem" }}>{relativeTime(asset.indexed_at)}</span>
                </div>
                <div className="target-health-meta" style={{ marginTop: 4 }}>
                  {asset.duration_s > 0 && <span>{formatDuration(asset.duration_s)}</span>}
                  <span>{formatBytes(asset.file_size_bytes)}</span>
                  <span className="mono muted" style={{ fontSize: "0.75rem" }}>{asset.media_id}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Pipeline result detail */}
      {selectedAsset && pipelineResult && (
        <div className="panel">
          <h3 style={{ margin: "0 0 10px", fontSize: "0.95rem" }}>
            Pipeline Result
            <button className="tiny-button" style={{ marginLeft: 8 }} onClick={() => { setSelectedAsset(null); setPipelineResult(null); }}>Close</button>
          </h3>

          {/* Layer summary */}
          {pipelineResult.layers && (
            <div className="backup-grid" style={{ marginBottom: 12 }}>
              {Object.entries(pipelineResult.layers).map(([layer, data]: [string, any]) => (
                <div key={layer} className="card">
                  <h4 style={{ margin: "0 0 6px", fontSize: "0.85rem" }}>{LAYER_LABELS[layer] || layer}</h4>
                  <div className="target-health-meta">
                    {Object.entries(data || {}).map(([k, v]) => (
                      <span key={k}>{k}: <strong>{String(v)}</strong></span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Composed document */}
          {pipelineResult.document && (
            <div>
              <h4 style={{ margin: "0 0 8px", fontSize: "0.88rem" }}>
                {pipelineResult.document.title}
                <span className="pill" style={{ marginLeft: 8 }}>{pipelineResult.document.format}</span>
              </h4>
              <pre className="terminal" style={{ maxHeight: 400 }}>
                {pipelineResult.document.full_text}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
