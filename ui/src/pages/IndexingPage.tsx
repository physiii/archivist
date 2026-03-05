import { useEffect, useMemo, useState } from "react";

import {
  addIndexingTarget,
  deleteIndexingTarget,
  getIndexingOverview,
  getIndexingRunLogs,
  scanIndexingTarget,
  startIndexing,
  startIndexingTarget,
  stopIndexing,
  updateIndexingTarget
} from "../lib/api";
import type { IndexingLogResponse, IndexingOverview, IndexingTarget } from "../types";

export default function IndexingPage() {
  const [overview, setOverview] = useState<IndexingOverview | null>(null);
  const [logs, setLogs] = useState<IndexingLogResponse | null>(null);
  const [selectedRun, setSelectedRun] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [working, setWorking] = useState(false);
  const [newTargetPath, setNewTargetPath] = useState("/media/mass/recording");
  const [newTargetRecursive, setNewTargetRecursive] = useState(true);

  async function refresh() {
    try {
      const data = await getIndexingOverview();
      setOverview(data);
      setError(null);
      if (!selectedRun && data.recent_runs.length > 0) {
        setSelectedRun(data.recent_runs[0].run_id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load indexing overview.");
    }
  }

  async function refreshLogs(runId: string) {
    try {
      const data = await getIndexingRunLogs(runId, 180);
      setLogs(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load indexing logs.");
    }
  }

  async function onStart() {
    setWorking(true);
    try {
      await startIndexing();
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start indexing.");
    } finally {
      setWorking(false);
    }
  }

  async function onStop() {
    setWorking(true);
    try {
      await stopIndexing();
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to stop indexing.");
    } finally {
      setWorking(false);
    }
  }

  async function onAddTarget() {
    const clean = newTargetPath.trim();
    if (!clean) return;
    setWorking(true);
    try {
      await addIndexingTarget({ path: clean, recursive: newTargetRecursive, enabled: true });
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add target.");
    } finally {
      setWorking(false);
    }
  }

  async function onScan(target: IndexingTarget) {
    setWorking(true);
    try {
      await scanIndexingTarget(target.id);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to scan target.");
    } finally {
      setWorking(false);
    }
  }

  async function onIndexTarget(target: IndexingTarget) {
    setWorking(true);
    try {
      await startIndexingTarget(target.id);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start target indexing.");
    } finally {
      setWorking(false);
    }
  }

  async function onToggle(target: IndexingTarget) {
    setWorking(true);
    try {
      await updateIndexingTarget(target.id, { enabled: !target.enabled });
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update target.");
    } finally {
      setWorking(false);
    }
  }

  async function onDelete(target: IndexingTarget) {
    if (!confirm(`Delete indexing target ${target.path}?`)) return;
    setWorking(true);
    try {
      await deleteIndexingTarget(target.id);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete target.");
    } finally {
      setWorking(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  useEffect(() => {
    const timer = setInterval(() => {
      void refresh();
      if (selectedRun) {
        void refreshLogs(selectedRun);
      }
    }, 4000);
    return () => clearInterval(timer);
  }, [selectedRun]);

  useEffect(() => {
    if (!selectedRun) return;
    void refreshLogs(selectedRun);
  }, [selectedRun]);

  const selectedHealth = useMemo(() => {
    if (!overview) return new Map<string, IndexingOverview["target_health"][number]>();
    return new Map(overview.target_health.map((item) => [item.id, item]));
  }, [overview]);

  return (
    <section className="backup-layout">
      {error && <div className="error-banner">{error}</div>}
      {!overview ? (
        <div className="muted">Loading indexing status…</div>
      ) : (
        <>
          <div className="backup-header panel">
            <div>
              <h2>Indexing</h2>
              <p className="muted">Transcript indexing for selected target folders.</p>
              <div className="health-pill">
                <span className={`status-dot ${overview.storage_ready ? "success" : "warning"}`} />
                <span>{overview.storage_ready ? "Targets look available" : "Targets need attention"}</span>
              </div>
            </div>
            <div className="inline-actions">
              {overview.status.running ? (
                <button disabled={working} onClick={() => void onStop()}>
                  Stop Indexing
                </button>
              ) : (
                <button disabled={working} onClick={() => void onStart()}>
                  Start Indexing
                </button>
              )}
            </div>
          </div>

          <div className="panel">
            <p>
              <strong>State:</strong> {overview.status.running ? "Running" : "Idle"}
            </p>
            <p>
              <strong>Progress:</strong> {overview.status.progress_current ?? 0}/{overview.status.progress_total ?? 0}
            </p>
            <p>
              <strong>Status line:</strong> {overview.status.progress_line ?? "No active progress line."}
            </p>
            <p className="muted">
              Files: {overview.status.files_done ?? 0}/{overview.status.files_total ?? 0} · Chunks: {overview.status.chunks_done ?? 0}/
              {overview.status.chunks_total ?? 0} · ETA:{" "}
              {typeof overview.status.eta_seconds === "number" ? `${overview.status.eta_seconds}s` : "unknown"}
            </p>
          </div>

          <div className="panel">
            <h3>Indexing Targets</h3>
            <div className="target-health-list">
              {overview.targets.map((target) => {
                const health = selectedHealth.get(target.id);
                return (
                  <div className="target-health-row" key={target.id}>
                    <div className="target-health-header">
                      <strong>{target.path}</strong>
                      <div className="inline-actions">
                        <span className={health?.ready ? "health-badge ready" : "health-badge issue"}>
                          {health?.ready ? "Ready" : "Issue"}
                        </span>
                        <button className="tiny-button" disabled={working} onClick={() => void onScan(target)}>
                          Scan
                        </button>
                        <button
                          className="tiny-button"
                          disabled={working || overview.status.running || !health?.ready}
                          onClick={() => void onIndexTarget(target)}
                        >
                          Index
                        </button>
                        <button className="tiny-button" disabled={working} onClick={() => void onToggle(target)}>
                          {target.enabled ? "Disable" : "Enable"}
                        </button>
                        <button className="icon-danger-button" disabled={working} onClick={() => void onDelete(target)}>
                          ×
                        </button>
                      </div>
                    </div>
                    <p className="muted">Resolved: {health?.resolved_path ?? target.path}</p>
                    <p className="muted">
                      Files: {target.transcript_files} · Recursive: {target.recursive ? "yes" : "no"} · Last scan:{" "}
                      {target.last_scanned_at ? new Date(target.last_scanned_at).toLocaleString() : "never"}
                    </p>
                    {target.last_error && <p className="muted">Last error: {target.last_error}</p>}
                  </div>
                );
              })}
            </div>
            <details className="add-target-details">
              <summary>Add Target</summary>
              <div className="schedule-form" style={{ marginTop: 10 }}>
                <label>
                  Path
                  <input value={newTargetPath} onChange={(event) => setNewTargetPath(event.target.value)} />
                </label>
                <label className="schedule-toggle">
                  <input
                    type="checkbox"
                    checked={newTargetRecursive}
                    onChange={(event) => setNewTargetRecursive(event.target.checked)}
                  />
                  Recursive
                </label>
                <button disabled={working} onClick={() => void onAddTarget()}>
                  Add
                </button>
              </div>
            </details>
          </div>

          <div className="panel">
            <h3>Recent Runs</h3>
            <div className="run-list">
              {overview.recent_runs.map((run) => (
                <button key={run.run_id} className={selectedRun === run.run_id ? "active" : ""} onClick={() => setSelectedRun(run.run_id)}>
                  <span>{run.run_id}</span>
                  <span className={`run-status-badge ${run.status ?? "unknown"}`}>{run.status ?? "unknown"}</span>
                  <span className="muted">
                    files {run.files_indexed ?? 0}/{run.files_total ?? 0} · chunks {run.chunks_indexed ?? 0}/{run.chunks_total ?? 0}
                  </span>
                  <span className="muted">{run.last_line ?? "No summary line."}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="panel">
            <h3>Run Logs {selectedRun ? `· ${selectedRun}` : ""}</h3>
            <div className="backup-log-grid">
              <div>
                <h4>Main</h4>
                <pre className="terminal">{logs?.main_log_tail || "No log content."}</pre>
              </div>
              <div>
                <h4>Debug</h4>
                <pre className="terminal">{logs?.debug_log_tail || "No log content."}</pre>
              </div>
            </div>
          </div>
        </>
      )}
    </section>
  );
}
