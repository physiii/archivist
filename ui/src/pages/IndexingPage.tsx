import { useEffect, useMemo, useState } from "react";

import { WorkspaceEmpty, WorkspacePage, WorkspacePanel } from "../components/Workspace";
import {
  addIndexingTarget,
  deleteIndexingTarget,
  getIndexingOverview,
  getIndexingRunLogs,
  scanIndexingTarget,
  startIndexing,
  startIndexingTarget,
  stopIndexing,
  updateBackupSchedule,
  updateIndexingTarget,
} from "../lib/api";
import type { IndexingLogResponse, IndexingOverview, IndexingTarget } from "../types";

function formatDateTime(value?: string | null) {
  return value ? new Date(value).toLocaleString() : "Never";
}

function formatDuration(seconds?: number | null) {
  if (typeof seconds !== "number" || Number.isNaN(seconds)) return "Unknown";
  if (seconds < 60) return `${seconds.toFixed(0)}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${Math.floor(seconds % 60)}s`;
  return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
}

export default function IndexingPage() {
  const [overview, setOverview] = useState<IndexingOverview | null>(null);
  const [logs, setLogs] = useState<IndexingLogResponse | null>(null);
  const [selectedRun, setSelectedRun] = useState<string | null>(null);
  const [selectedTargetId, setSelectedTargetId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [working, setWorking] = useState(false);
  const [scheduleEnabled, setScheduleEnabled] = useState(true);
  const [scheduleTime, setScheduleTime] = useState("02:00");
  const [newTargetPath, setNewTargetPath] = useState("/media/mass/recording");
  const [newTargetRecursive, setNewTargetRecursive] = useState(true);

  async function refresh() {
    try {
      const data = await getIndexingOverview();
      setOverview(data);
      setScheduleEnabled(data.schedule.enabled);
      setScheduleTime(data.schedule.time_of_day);
      setSelectedRun((current) => {
        if (current && data.recent_runs.some((run) => run.run_id === current)) return current;
        return data.recent_runs[0]?.run_id ?? null;
      });
      setSelectedTargetId((current) => {
        if (current && data.targets.some((target) => target.id === current)) return current;
        return data.targets[0]?.id ?? null;
      });
      setError(null);
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

  async function onSaveSchedule() {
    setWorking(true);
    try {
      await updateBackupSchedule(scheduleEnabled, scheduleTime);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update schedule.");
    } finally {
      setWorking(false);
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
      setNewTargetPath("");
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

  const targetHealthMap = useMemo(() => {
    const map = new Map<string, IndexingOverview["target_health"][number]>();
    if (!overview) return map;
    for (const item of overview.target_health) {
      map.set(item.id, item);
    }
    return map;
  }, [overview]);

  const selectedTarget = overview?.targets.find((target) => target.id === selectedTargetId) ?? null;
  const selectedTargetHealth = selectedTarget ? targetHealthMap.get(selectedTarget.id) ?? null : null;
  const selectedRunSummary = overview?.recent_runs.find((run) => run.run_id === selectedRun) ?? null;
  const totalFiles = useMemo(
    () => overview?.targets.reduce((sum, target) => sum + (target.transcript_files ?? 0), 0) ?? 0,
    [overview],
  );

  return (
    <WorkspacePage
      eyebrow="Operations"
      title="Indexing"
      subtitle="Track target readiness, launch ad hoc indexing runs, and keep the current run plus recent history in a single coordinated view."
      actions={
        overview?.status.running ? (
          <button disabled={working} onClick={() => void onStop()}>
            Stop indexing
          </button>
        ) : (
          <button disabled={working} onClick={() => void onStart()}>
            Start indexing
          </button>
        )
      }
      stats={[
        {
          label: "Pipeline state",
          value: overview?.status.running ? "Running" : "Idle",
          meta: overview?.status.active_step || overview?.status.progress_line || "Awaiting work",
          tone: overview?.status.running ? "accent" : "default",
        },
        { label: "Targets", value: overview?.targets.length ?? "—", meta: `${totalFiles.toLocaleString()} indexable files` },
        {
          label: "Next run",
          value: overview?.schedule.next_run_at ? new Date(overview.schedule.next_run_at).toLocaleDateString() : "Disabled",
          meta: overview?.schedule.next_run_at ? new Date(overview.schedule.next_run_at).toLocaleTimeString() : "Scheduler off",
        },
      ]}
    >
      {error ? <div className="error-banner">{error}</div> : null}

      <div className="workspace-grid workspace-grid--two">
        <WorkspacePanel
          title="Indexing targets"
          description="Transcripts (.vtt, .srt) and documents (.pdf, .docx) are indexed directly. Audio, video, and image files are routed to the Media pipeline for rich processing."
        >
          <div className="inline-form compact">
            <input
              value={newTargetPath}
              onChange={(event) => setNewTargetPath(event.target.value)}
              placeholder="Add target path"
            />
            <label className="toggle-chip">
              <input
                type="checkbox"
                checked={newTargetRecursive}
                onChange={(event) => setNewTargetRecursive(event.target.checked)}
              />
              Recursive
            </label>
            <button disabled={working || !newTargetPath.trim()} onClick={() => void onAddTarget()}>
              Add target
            </button>
          </div>

          {!overview ? (
            <WorkspaceEmpty title="Loading targets" description="Waiting for indexing overview." />
          ) : overview.targets.length === 0 ? (
            <WorkspaceEmpty title="No targets configured" description="Add a target path to start indexing." />
          ) : (
            <div className="record-list" role="list" aria-label="Indexing targets">
              {overview.targets.map((target) => {
                const health = targetHealthMap.get(target.id);
                return (
                  <button
                    key={target.id}
                    type="button"
                    className={`record-row ${selectedTargetId === target.id ? "active" : ""}`}
                    onClick={() => setSelectedTargetId(target.id)}
                  >
                    <div className="record-row-head">
                      <div className="record-row-title-group">
                        <strong className="record-row-title" title={target.path}>
                          {target.path}
                        </strong>
                        <span className={`workspace-chip ${target.enabled ? "workspace-chip--success" : ""}`}>
                          {target.enabled ? "Enabled" : "Disabled"}
                        </span>
                      </div>
                      <span className={`workspace-chip ${health?.ready ? "workspace-chip--success" : "workspace-chip--warning"}`}>
                        {health?.ready ? "Ready" : "Needs review"}
                      </span>
                    </div>
                    <span className="record-row-subtitle">
                      {target.recursive ? "Recursive" : "Single folder"} · {target.transcript_files.toLocaleString()} files
                      {health?.excluded_child_targets?.length
                        ? ` · excludes ${health.excluded_child_targets.length} nested target${
                            health.excluded_child_targets.length === 1 ? "" : "s"
                          }`
                        : ""}
                    </span>
                    <span className="record-row-preview">
                      Last scan {formatDateTime(target.last_scanned_at)}
                      {target.last_error ? ` · ${target.last_error}` : ""}
                    </span>
                  </button>
                );
              })}
            </div>
          )}
        </WorkspacePanel>

        <WorkspacePanel
          title="Target inspector"
          description="Actions live here so the list stays clean and stays readable when the number of targets grows."
          actions={
            selectedTarget ? (
              <div className="workspace-inline-actions">
                <button className="tiny-button" disabled={working} onClick={() => void onScan(selectedTarget)}>
                  Scan
                </button>
                <button
                  className="tiny-button"
                  disabled={working || overview?.status.running || !selectedTargetHealth?.ready}
                  onClick={() => void onIndexTarget(selectedTarget)}
                >
                  Index
                </button>
                <button className="tiny-button" disabled={working} onClick={() => void onToggle(selectedTarget)}>
                  {selectedTarget.enabled ? "Disable" : "Enable"}
                </button>
                <button className="icon-danger-button" disabled={working} onClick={() => void onDelete(selectedTarget)}>
                  Delete
                </button>
              </div>
            ) : null
          }
        >
          {selectedTarget && selectedTargetHealth ? (
            <>
              <dl className="detail-list">
                <div>
                  <dt>Resolved path</dt>
                  <dd className="mono" title={selectedTargetHealth.resolved_path}>
                    {selectedTargetHealth.resolved_path}
                  </dd>
                </div>
                <div>
                  <dt>Readiness</dt>
                  <dd>{selectedTargetHealth.ready ? "Ready" : "Issue detected"}</dd>
                </div>
                <div>
                  <dt>Files</dt>
                  <dd>{selectedTarget.transcript_files.toLocaleString()}</dd>
                </div>
                <div>
                  <dt>Last scan</dt>
                  <dd>{formatDateTime(selectedTarget.last_scanned_at)}</dd>
                </div>
                <div>
                  <dt>Last index</dt>
                  <dd>{formatDateTime(selectedTarget.last_indexed_at)}</dd>
                </div>
                <div>
                  <dt>Fallback mode</dt>
                  <dd>{selectedTargetHealth.used_host_fallback ? "Host path fallback used" : "Direct storage path"}</dd>
                </div>
                <div>
                  <dt>Nested target exclusions</dt>
                  <dd>
                    {selectedTargetHealth.excluded_child_targets?.length
                      ? `${selectedTargetHealth.excluded_child_targets.length} configured child target${
                          selectedTargetHealth.excluded_child_targets.length === 1 ? "" : "s"
                        }`
                      : "None"}
                  </dd>
                </div>
              </dl>
              {selectedTargetHealth.excluded_child_targets?.length ? (
                <div className="inline-warning">
                  This target excludes nested targets during scans and full indexing runs:{" "}
                  {selectedTargetHealth.excluded_child_targets.join(", ")}
                </div>
              ) : null}
              {selectedTarget.last_error ? <div className="inline-warning">Last error: {selectedTarget.last_error}</div> : null}
              <p className="inspector-copy">
                {selectedTargetHealth.exists && selectedTargetHealth.readable
                  ? "The target is visible to the service and can be scanned or indexed from this panel."
                  : "The target is currently missing or unreadable. Fix storage access before starting a run."}
              </p>
            </>
          ) : (
            <WorkspaceEmpty title="No target selected" description="Choose a target row to inspect it and run actions from this panel." />
          )}
        </WorkspacePanel>
      </div>

      <div className="workspace-grid workspace-grid--two">
        <WorkspacePanel
          title="Scheduler and run state"
          description="Scheduler edits and current progress are grouped together because they affect the same operational decision."
        >
          {overview ? (
            <>
              <div className="inline-form">
                <label className="toggle-chip">
                  <input
                    type="checkbox"
                    checked={scheduleEnabled}
                    onChange={(event) => setScheduleEnabled(event.target.checked)}
                  />
                  Scheduler enabled
                </label>
                <input type="time" value={scheduleTime} onChange={(event) => setScheduleTime(event.target.value)} />
                <button disabled={working} onClick={() => void onSaveSchedule()}>
                  Save schedule
                </button>
              </div>
              <dl className="detail-list">
                <div>
                  <dt>Next trigger</dt>
                  <dd>{formatDateTime(overview.schedule.next_run_at)}</dd>
                </div>
                <div>
                  <dt>Last trigger</dt>
                  <dd>{formatDateTime(overview.schedule.last_triggered_at)}</dd>
                </div>
                <div>
                  <dt>Progress</dt>
                  <dd>
                    {overview.status.progress_current ?? 0}/{overview.status.progress_total ?? 0}
                  </dd>
                </div>
                <div>
                  <dt>Current file</dt>
                  <dd className="mono" title={overview.status.current_path || ""}>
                    {overview.status.current_path || "No active file"}
                  </dd>
                </div>
                <div>
                  <dt>Elapsed</dt>
                  <dd>{formatDuration(overview.status.elapsed_seconds)}</dd>
                </div>
                <div>
                  <dt>ETA</dt>
                  <dd>{formatDuration(overview.status.eta_seconds)}</dd>
                </div>
              </dl>
              <div className="progress-meter" aria-label="Indexing progress">
                <div
                  className="progress-meter-fill"
                  style={{
                    width: `${
                      overview.status.progress_total
                        ? Math.min(100, ((overview.status.progress_current ?? 0) / overview.status.progress_total) * 100)
                        : 0
                    }%`,
                  }}
                />
              </div>
              <p className="inspector-copy">{overview.status.progress_line || "No active progress line."}</p>
            </>
          ) : (
            <WorkspaceEmpty title="Loading scheduler" description="Waiting for indexing overview." />
          )}
        </WorkspacePanel>

        <WorkspacePanel
          title="Recent runs"
          description="Run history is selection-based so the log pane below can stay anchored to the chosen run."
        >
          {!overview || overview.recent_runs.length === 0 ? (
            <WorkspaceEmpty title="No runs recorded" description="Run history appears here after indexing jobs complete or start." />
          ) : (
            <div className="record-list" role="list" aria-label="Recent indexing runs">
              {overview.recent_runs.map((run) => (
                <button
                  key={run.run_id}
                  type="button"
                  className={`record-row ${selectedRun === run.run_id ? "active" : ""}`}
                  onClick={() => setSelectedRun(run.run_id)}
                >
                  <div className="record-row-head">
                    <div className="record-row-title-group">
                      <strong className="record-row-title mono">{run.run_id}</strong>
                      <span className="workspace-chip">{run.status ?? "unknown"}</span>
                    </div>
                    <span className="record-row-meta">{formatDateTime(run.started_at)}</span>
                  </div>
                  <span className="record-row-subtitle">
                    Files {run.files_indexed ?? 0}/{run.files_total ?? 0} · Chunks {run.chunks_indexed ?? 0}/{run.chunks_total ?? 0}
                  </span>
                  <span className="record-row-preview">{run.last_line ?? "No summary line available."}</span>
                </button>
              ))}
            </div>
          )}
        </WorkspacePanel>
      </div>

      <div className="workspace-grid workspace-grid--two">
        <WorkspacePanel
          title="Run inspector"
          description="Structured run metadata stays separate from raw logs so the operational summary is readable at a glance."
        >
          {selectedRunSummary ? (
            <>
              <dl className="detail-list">
                <div>
                  <dt>Run id</dt>
                  <dd className="mono">{selectedRunSummary.run_id}</dd>
                </div>
                <div>
                  <dt>Status</dt>
                  <dd>{logs?.summary?.status ?? selectedRunSummary.status ?? "unknown"}</dd>
                </div>
                <div>
                  <dt>Files</dt>
                  <dd>
                    {logs?.summary?.files_indexed ?? selectedRunSummary.files_indexed ?? 0}/{logs?.summary?.files_total ?? selectedRunSummary.files_total ?? 0}
                  </dd>
                </div>
                <div>
                  <dt>Chunks</dt>
                  <dd>
                    {logs?.summary?.chunks_indexed ?? selectedRunSummary.chunks_indexed ?? 0}/{logs?.summary?.chunks_total ?? selectedRunSummary.chunks_total ?? 0}
                  </dd>
                </div>
                <div>
                  <dt>Started</dt>
                  <dd>{formatDateTime(logs?.summary?.started_at ?? selectedRunSummary.started_at)}</dd>
                </div>
                <div>
                  <dt>Finished</dt>
                  <dd>{formatDateTime(logs?.summary?.finished_at)}</dd>
                </div>
              </dl>
              {logs?.summary?.errors && logs.summary.errors.length > 0 ? (
                <div className="storage-errors">
                  {logs.summary.errors.map((entry, index) => (
                    <p key={`${entry}-${index}`}>{entry}</p>
                  ))}
                </div>
              ) : (
                <p className="inspector-copy">{selectedRunSummary.last_line ?? "No summary line available for this run."}</p>
              )}
            </>
          ) : (
            <WorkspaceEmpty title="No run selected" description="Choose a run to inspect the summary and logs." />
          )}
        </WorkspacePanel>

        <WorkspacePanel
          title="Run logs"
          description="Raw logs remain accessible, but they no longer dominate the page when you are just scanning status."
        >
          <div className="backup-log-grid">
            <div>
              <h3 className="subpanel-title">Main log</h3>
              <pre className="terminal">{logs?.main_log_tail || "No log content."}</pre>
            </div>
            <div>
              <h3 className="subpanel-title">Debug log</h3>
              <pre className="terminal">{logs?.debug_log_tail || "No log content."}</pre>
            </div>
          </div>
        </WorkspacePanel>
      </div>
    </WorkspacePage>
  );
}
