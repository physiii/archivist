import { useEffect, useMemo, useState } from "react";

import { WorkspaceEmpty, WorkspacePage, WorkspacePanel } from "../components/Workspace";
import {
  addBackupTarget,
  deleteBackupTarget,
  getBackupOverview,
  getBackupRunLogs,
  startBackupTarget,
  startBackup,
  stopBackup,
  toApiUrl,
  updateBackupSchedule,
  updateBackupTarget,
} from "../lib/api";
import type { BackupLogResponse, BackupOverview, BackupTarget } from "../types";

function formatBytes(value?: number | null) {
  if (typeof value !== "number" || Number.isNaN(value) || value < 0) return "Unknown";
  const units = ["B", "KB", "MB", "GB", "TB", "PB"];
  let amount = value;
  let index = 0;
  while (amount >= 1024 && index < units.length - 1) {
    amount /= 1024;
    index += 1;
  }
  return `${amount.toFixed(amount >= 10 || index === 0 ? 0 : 1)} ${units[index]}`;
}

function formatDateTime(value?: string | null) {
  return value ? new Date(value).toLocaleString() : "Never";
}

function sourceBadge(item: {
  exists: boolean;
  readable: boolean;
  mount_expected?: boolean;
  mount_ok?: boolean;
}) {
  if (!item.exists) return { label: "Missing", ok: false };
  if (!item.readable) return { label: "Unreadable", ok: false };
  if (item.mount_expected && item.mount_ok === false) return { label: "Not mounted", ok: false };
  return { label: "Ready", ok: true };
}

function destinationBadge(item: {
  exists: boolean;
  writable: boolean;
  mount_expected?: boolean;
  mount_ok?: boolean;
}) {
  if (!item.exists) return { label: "Missing", ok: false };
  if (!item.writable) return { label: "Not writable", ok: false };
  if (item.mount_expected && item.mount_ok === false) return { label: "Not mounted", ok: false };
  return { label: "Writable", ok: true };
}

function targetKey(target: { profile: string; source: string; destination: string }) {
  return `${target.profile}|${target.source}|${target.destination}`;
}

export default function BackupPage() {
  const [overview, setOverview] = useState<BackupOverview | null>(null);
  const [logs, setLogs] = useState<BackupLogResponse | null>(null);
  const [selectedRun, setSelectedRun] = useState<string | null>(null);
  const [selectedTargetKey, setSelectedTargetKey] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [working, setWorking] = useState(false);
  const [scheduleEnabled, setScheduleEnabled] = useState(true);
  const [scheduleTime, setScheduleTime] = useState("02:00");
  const [newTarget, setNewTarget] = useState({ profile: "nas", source: "", destination: "" });

  async function refresh() {
    try {
      const data = await getBackupOverview();
      setOverview(data);
      setScheduleEnabled(data.schedule.enabled);
      setScheduleTime(data.schedule.time_of_day);
      setSelectedRun((current) => {
        if (current && data.recent_runs.some((run) => run.run_id === current)) return current;
        return data.recent_runs[0]?.run_id ?? null;
      });
      setSelectedTargetKey((current) => {
        if (current && data.target_health.some((target) => targetKey(target) === current)) return current;
        return data.target_health[0] ? targetKey(data.target_health[0]) : null;
      });
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch backup status.");
    }
  }

  async function refreshLogs(runId: string) {
    try {
      const nextLogs = await getBackupRunLogs(runId, 180);
      setLogs(nextLogs);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch backup logs.");
    }
  }

  async function onStart() {
    setWorking(true);
    try {
      await startBackup();
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start backup.");
    } finally {
      setWorking(false);
    }
  }

  async function onStop() {
    setWorking(true);
    try {
      await stopBackup();
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to stop backup.");
    } finally {
      setWorking(false);
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

  async function onAddTarget() {
    if (!newTarget.source.trim() || !newTarget.destination.trim()) return;
    setWorking(true);
    try {
      await addBackupTarget({
        profile: newTarget.profile.trim() || "default",
        source: newTarget.source.trim(),
        destination: newTarget.destination.trim(),
        enabled: true,
      });
      setNewTarget({ profile: "nas", source: "", destination: "" });
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add target.");
    } finally {
      setWorking(false);
    }
  }

  async function onToggleTarget(target: BackupTarget) {
    setWorking(true);
    try {
      await updateBackupTarget(target.id, { enabled: !target.enabled });
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update target.");
    } finally {
      setWorking(false);
    }
  }

  async function onDeleteTarget(target: BackupTarget) {
    if (!confirm(`Delete target ${target.source} -> ${target.destination}?`)) return;
    setWorking(true);
    try {
      await deleteBackupTarget(target.id);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete target.");
    } finally {
      setWorking(false);
    }
  }

  async function onBackupTarget(target: BackupTarget) {
    setWorking(true);
    try {
      await startBackupTarget(target.id);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start target backup.");
    } finally {
      setWorking(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      void refresh();
      if (selectedRun) {
        void refreshLogs(selectedRun);
      }
    }, 4000);
    return () => clearInterval(interval);
  }, [selectedRun]);

  useEffect(() => {
    if (!selectedRun) return;
    void refreshLogs(selectedRun);
  }, [selectedRun]);

  const targetMap = useMemo(() => {
    const map = new Map<string, BackupTarget>();
    if (!overview) return map;
    for (const target of overview.target_mappings) {
      map.set(targetKey(target), target);
    }
    return map;
  }, [overview]);

  const selectedTargetHealth = overview?.target_health.find((target) => targetKey(target) === selectedTargetKey) ?? null;
  const selectedTarget = selectedTargetHealth ? targetMap.get(targetKey(selectedTargetHealth)) ?? null : null;
  const activeRun = overview?.recent_runs.find((run) => run.run_id === selectedRun) ?? null;
  const readyTargets = overview?.target_health.filter((target) => target.ready).length ?? 0;

  return (
    <WorkspacePage
      eyebrow="Operations"
      title="Backup"
      subtitle="Operate scheduled backups, inspect target readiness, and keep storage health plus run history in one cohesive operations view."
      actions={
        overview?.status.running ? (
          <button disabled={working} onClick={() => void onStop()}>
            Stop backup
          </button>
        ) : (
          <button disabled={working} onClick={() => void onStart()}>
            Start backup
          </button>
        )
      }
      stats={[
        {
          label: "Backup state",
          value: overview?.status.running ? "Running" : "Idle",
          meta: overview?.status.progress_line || overview?.status.active_step || "Awaiting work",
          tone: overview?.status.running ? "accent" : "default",
        },
        { label: "Targets", value: overview?.target_health.length ?? "—", meta: `${readyTargets} ready` },
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
          title="Backup targets"
          description="Targets stay condensed in the main list so the source and destination pair is easy to scan across many mappings."
        >
          <div className="inline-form compact">
            <input
              value={newTarget.profile}
              onChange={(event) => setNewTarget({ ...newTarget, profile: event.target.value })}
              placeholder="Profile"
            />
            <input
              value={newTarget.source}
              onChange={(event) => setNewTarget({ ...newTarget, source: event.target.value })}
              placeholder="Source path"
            />
            <input
              value={newTarget.destination}
              onChange={(event) => setNewTarget({ ...newTarget, destination: event.target.value })}
              placeholder="Destination path"
            />
            <button disabled={working || !newTarget.source.trim() || !newTarget.destination.trim()} onClick={() => void onAddTarget()}>
              Add target
            </button>
          </div>

          {!overview || overview.target_health.length === 0 ? (
            <WorkspaceEmpty title="No backup targets" description="Add a source and destination to configure backup coverage." />
          ) : (
            <div className="record-list" role="list" aria-label="Backup targets">
              {overview.target_health.map((target) => {
                const linkedTarget = targetMap.get(targetKey(target));
                return (
                  <button
                    key={targetKey(target)}
                    type="button"
                    className={`record-row ${selectedTargetKey === targetKey(target) ? "active" : ""}`}
                    onClick={() => setSelectedTargetKey(targetKey(target))}
                  >
                    <div className="record-row-head">
                      <div className="record-row-title-group">
                        <strong className="record-row-title" title={target.source}>
                          {target.source}
                        </strong>
                        <span className="workspace-chip">{target.profile}</span>
                      </div>
                      <span className={`workspace-chip ${target.ready ? "workspace-chip--success" : "workspace-chip--warning"}`}>
                        {target.ready ? "Ready" : "Issue"}
                      </span>
                    </div>
                    <span className="record-row-subtitle" title={target.destination}>
                      {target.destination}
                    </span>
                    <span className="record-row-preview">
                      {linkedTarget?.enabled ? "Enabled" : "Disabled"} · Last backup {formatDateTime(target.last_backup_at)}
                    </span>
                  </button>
                );
              })}
            </div>
          )}
        </WorkspacePanel>

        <WorkspacePanel
          title="Target inspector"
          description="Operational actions stay local to the selected mapping, which keeps the list readable and cuts accidental clicks."
          actions={
            selectedTarget ? (
              <div className="workspace-inline-actions">
                <button
                  className="tiny-button"
                  disabled={working || overview?.status.running || !selectedTargetHealth?.ready}
                  onClick={() => void onBackupTarget(selectedTarget)}
                >
                  Backup
                </button>
                <button className="tiny-button" disabled={working} onClick={() => void onToggleTarget(selectedTarget)}>
                  {selectedTarget.enabled ? "Disable" : "Enable"}
                </button>
                <button className="icon-danger-button" disabled={working} onClick={() => void onDeleteTarget(selectedTarget)}>
                  Delete
                </button>
              </div>
            ) : null
          }
        >
          {selectedTargetHealth ? (
            <>
              <dl className="detail-list">
                <div>
                  <dt>Profile</dt>
                  <dd>{selectedTargetHealth.profile}</dd>
                </div>
                <div>
                  <dt>Source</dt>
                  <dd className="mono" title={selectedTargetHealth.source}>
                    {selectedTargetHealth.source}
                  </dd>
                </div>
                <div>
                  <dt>Destination</dt>
                  <dd className="mono" title={selectedTargetHealth.destination}>
                    {selectedTargetHealth.destination}
                  </dd>
                </div>
                <div>
                  <dt>Last backup</dt>
                  <dd>{formatDateTime(selectedTargetHealth.last_backup_at)}</dd>
                </div>
                <div>
                  <dt>Source state</dt>
                  <dd>
                    {
                      sourceBadge({
                        exists: selectedTargetHealth.source_exists,
                        readable: selectedTargetHealth.source_readable,
                        mount_ok: selectedTargetHealth.source_mount_ok,
                      }).label
                    }
                  </dd>
                </div>
                <div>
                  <dt>Destination state</dt>
                  <dd>
                    {
                      destinationBadge({
                        exists: selectedTargetHealth.destination_exists,
                        writable: selectedTargetHealth.destination_writable,
                        mount_ok: selectedTargetHealth.destination_mount_ok,
                      }).label
                    }
                  </dd>
                </div>
              </dl>
              <div className="workspace-chip-row">
                <span className={`workspace-chip ${selectedTargetHealth.source_exists && selectedTargetHealth.source_readable ? "workspace-chip--success" : "workspace-chip--warning"}`}>
                  Source {selectedTargetHealth.source_exists && selectedTargetHealth.source_readable ? "OK" : "Problem"}
                </span>
                <span className={`workspace-chip ${selectedTargetHealth.destination_exists && selectedTargetHealth.destination_writable ? "workspace-chip--success" : "workspace-chip--warning"}`}>
                  Destination {selectedTargetHealth.destination_exists && selectedTargetHealth.destination_writable ? "Writable" : "Problem"}
                </span>
                <span className="workspace-chip">
                  {selectedTargetHealth.destination_mount_ok ?? selectedTargetHealth.destination_separate_mount ? "Mounted" : "Not mounted"}
                </span>
              </div>
              <p className="inspector-copy">
                {selectedTargetHealth.ready
                  ? "This target pair is ready for backup. Use the action bar to run only this mapping or toggle its schedule participation."
                  : "Fix the storage issue before running this mapping. The readiness chips above show whether the problem is on the source or destination side."}
              </p>
            </>
          ) : (
            <WorkspaceEmpty title="No target selected" description="Select a backup mapping to inspect it and run actions from this panel." />
          )}
        </WorkspacePanel>
      </div>

      <div className="workspace-grid workspace-grid--two">
        <WorkspacePanel
          title="Scheduler and current run"
          description="Backup cadence and active progress belong together because they drive the same operational decisions."
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
                  <dt>Timer</dt>
                  <dd>{overview.timer_schedule ?? "Unknown"}</dd>
                </div>
                <div>
                  <dt>Pool</dt>
                  <dd>{overview.backup_pool ?? "Unknown"}</dd>
                </div>
                <div>
                  <dt>Archive cap</dt>
                  <dd>{overview.archive_bwlimit ?? "Unknown"}</dd>
                </div>
                <div>
                  <dt>Sync cap</dt>
                  <dd>{overview.rsync_bwlimit ?? "Unknown"}</dd>
                </div>
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
                  <dd>{overview.status.progress_line ?? "No active progress line."}</dd>
                </div>
              </dl>
              <div className="progress-meter" aria-label="Backup progress">
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
            </>
          ) : (
            <WorkspaceEmpty title="Loading backup schedule" description="Waiting for backup overview." />
          )}
        </WorkspacePanel>

        <WorkspacePanel
          title="Storage health"
          description="Capacity and mount readiness stay in one place so storage issues are obvious before you start a backup."
        >
          {overview ? (
            <>
              {overview.storage_diagnostics.filesystems.length > 0 ? (
                <div className="storage-df-table-wrap">
                  <table className="storage-df-table">
                    <thead>
                      <tr>
                        <th>Filesystem</th>
                        <th>Mount</th>
                        <th>Used</th>
                        <th>Free</th>
                        <th>Use%</th>
                      </tr>
                    </thead>
                    <tbody>
                      {overview.storage_diagnostics.filesystems.map((row) => (
                        <tr key={`${row.filesystem}-${row.mount_point}`}>
                          <td className="mono">{row.filesystem}</td>
                          <td className="mono">{row.mount_point}</td>
                          <td>{formatBytes(row.used_bytes)}</td>
                          <td>{formatBytes(row.free_bytes)}</td>
                          <td>{row.used_percent != null ? `${row.used_percent}%` : "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : null}
              <div className="storage-health-grid">
                <div className="workspace-stack">
                  <h3 className="subpanel-title">Sources</h3>
                  {overview.storage_diagnostics.sources.map((item) => {
                    const badge = sourceBadge(item);
                    return (
                      <div key={`source-${item.path}`} className="storage-item">
                        <div className="storage-item-head">
                          <strong>{item.path}</strong>
                          <span className={badge.ok ? "health-badge ready" : "health-badge issue"}>{badge.label}</span>
                        </div>
                        <p className="muted">Free {formatBytes(item.free_bytes)} · Used {item.used_percent ?? "?"}%</p>
                        <p className="muted">Mount {item.mount_point ?? "Unknown"}</p>
                      </div>
                    );
                  })}
                </div>
                <div className="workspace-stack">
                  <h3 className="subpanel-title">Destinations</h3>
                  {overview.storage_diagnostics.destinations.map((item) => {
                    const badge = destinationBadge(item);
                    return (
                      <div key={`destination-${item.path}`} className="storage-item">
                        <div className="storage-item-head">
                          <strong>{item.path}</strong>
                          <span className={badge.ok ? "health-badge ready" : "health-badge issue"}>{badge.label}</span>
                        </div>
                        <p className="muted">Free {formatBytes(item.free_bytes)} · Used {item.used_percent ?? "?"}%</p>
                        <p className="muted">Mount {item.mount_point ?? "Unknown"}</p>
                      </div>
                    );
                  })}
                </div>
              </div>
              <div className="zfs-panel">
                <div className="storage-item-head">
                  <h3 className="subpanel-title">ZFS</h3>
                  <span className={overview.storage_diagnostics.zfs.status_ok === false ? "health-badge issue" : "health-badge ready"}>
                    {overview.storage_diagnostics.zfs.status_ok === false ? "Issue" : "OK"}
                  </span>
                </div>
                <p className="muted">
                  {overview.storage_diagnostics.zfs.pool ??
                    (overview.storage_diagnostics.zfs.host ? `${overview.storage_diagnostics.zfs.host}:unknown` : "Unknown pool")}
                  {" · "}
                  {overview.storage_diagnostics.zfs.health ?? "Unknown health"}
                </p>
                <p className="muted">
                  Used {formatBytes(overview.storage_diagnostics.zfs.used_bytes)} · Available {formatBytes(overview.storage_diagnostics.zfs.avail_bytes)}
                </p>
                {overview.storage_diagnostics.zfs.status_summary ? <p className="muted">{overview.storage_diagnostics.zfs.status_summary}</p> : null}
                {overview.storage_diagnostics.zfs.command_error ? <div className="inline-warning">{overview.storage_diagnostics.zfs.command_error}</div> : null}
              </div>
            </>
          ) : (
            <WorkspaceEmpty title="Loading storage health" description="Waiting for diagnostics from the backup overview." />
          )}
        </WorkspacePanel>
      </div>

      <div className="workspace-grid workspace-grid--two">
        <WorkspacePanel
          title="Recent runs"
          description="History stays dense and clickable so you can jump between outcomes quickly."
        >
          {!overview || overview.recent_runs.length === 0 ? (
            <WorkspaceEmpty title="No backup runs recorded" description="Run history appears here after the service records executions." />
          ) : (
            <div className="record-list" role="list" aria-label="Recent backup runs">
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
                    Archive {run.archive_ok === true ? "OK" : run.archive_ok === false ? "Failed" : "Unknown"} · Sync failures {run.sync_failed ?? "?"}/{run.sync_total ?? "?"}
                  </span>
                  <span className="record-row-preview">{run.last_line ?? "No summary line available."}</span>
                </button>
              ))}
            </div>
          )}
        </WorkspacePanel>

        <WorkspacePanel
          title="Run outcome"
          description="Outcome summary and sync details stay separate from logs so the important state is readable immediately."
        >
          {activeRun ? (
            <>
              <dl className="detail-list">
                <div>
                  <dt>Run id</dt>
                  <dd className="mono">{activeRun.run_id}</dd>
                </div>
                <div>
                  <dt>Status</dt>
                  <dd>{logs?.summary?.status ?? activeRun.status ?? "unknown"}</dd>
                </div>
                <div>
                  <dt>Archive</dt>
                  <dd>
                    {logs?.summary?.include_archive === false ? "Skipped" : logs?.summary?.archive_ok ? "OK" : "Failed"}
                    {logs?.summary?.archive_file ? ` · ${logs.summary.archive_file}` : ""}
                  </dd>
                </div>
                <div>
                  <dt>Sync</dt>
                  <dd>
                    {logs?.summary?.sync_ok ?? "?"}/{logs?.summary?.sync_total ?? "?"} OK · {logs?.summary?.sync_failed ?? "?"} failed
                  </dd>
                </div>
                <div>
                  <dt>Snapshot</dt>
                  <dd>{logs?.summary?.snapshot_status ?? "Skipped"}</dd>
                </div>
              </dl>
              {logs?.summary?.errors && logs.summary.errors.length > 0 ? (
                <div className="storage-errors">
                  {logs.summary.errors.map((entry, index) => (
                    <p key={`${entry}-${index}`}>{entry}</p>
                  ))}
                </div>
              ) : null}
              {logs?.summary?.sync_results && logs.summary.sync_results.length > 0 ? (
                <div className="record-list compact">
                  {logs.summary.sync_results.map((item) => (
                    <div key={`${item.source}-${item.destination}`} className="record-row static">
                      <div className="record-row-head">
                        <strong className="record-row-title" title={`${item.source} -> ${item.destination}`}>
                          {item.source} → {item.destination}
                        </strong>
                        <span className={item.ok ? "health-badge ready" : "health-badge issue"}>
                          {item.ok ? "OK" : `exit ${item.exit_code}`}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : null}
            </>
          ) : (
            <WorkspaceEmpty title="No run selected" description="Choose a run to inspect the structured backup outcome." />
          )}
        </WorkspacePanel>
      </div>

      <div className="workspace-grid workspace-grid--two">
        <WorkspacePanel
          title="Snapshots and backup files"
          description="Outputs remain visible without dominating the main operations workflow."
        >
          {!overview ? (
            <WorkspaceEmpty title="Loading outputs" description="Waiting for backup overview." />
          ) : (
            <div className="workspace-grid workspace-grid--two-narrow">
              <div className="workspace-stack">
                <h3 className="subpanel-title">Snapshots</h3>
                {overview.snapshots.length === 0 ? (
                  <WorkspaceEmpty title="No snapshots parsed" description="Snapshot history will appear here when available." />
                ) : (
                  <div className="record-list compact">
                    {overview.snapshots.map((snapshot) => (
                      <div key={`${snapshot.name}-${snapshot.timestamp}`} className="record-row static">
                        <div className="record-row-head">
                          <strong className="record-row-title">{snapshot.name}</strong>
                          <span className="record-row-meta">{snapshot.timestamp}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              <div className="workspace-stack">
                <h3 className="subpanel-title">Backup files</h3>
                {overview.backup_files.length === 0 ? (
                  <WorkspaceEmpty title="No backup files yet" description="Created archives appear here." />
                ) : (
                  <div className="record-list compact">
                    {overview.backup_files.map((file) => (
                      <a
                        key={file.name}
                        href={toApiUrl(`/api/backups/files/${encodeURIComponent(file.name)}`)}
                        className="record-row static link-row"
                      >
                        <div className="record-row-head">
                          <strong className="record-row-title mono">{file.name}</strong>
                          <span className="record-row-meta">{formatBytes(file.bytes)}</span>
                        </div>
                        <span className="record-row-subtitle">{formatDateTime(file.modified_at)}</span>
                      </a>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </WorkspacePanel>

        <WorkspacePanel
          title="Run logs"
          description="Full log tails are still available for debugging, but they are contained to a single panel instead of taking over the page."
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
