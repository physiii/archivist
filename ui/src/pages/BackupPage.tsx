import { useEffect, useMemo, useState } from "react";

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
  updateBackupTarget
} from "../lib/api";
import type { BackupLogResponse, BackupOverview, BackupTarget } from "../types";

function formatBytes(value?: number | null) {
  if (typeof value !== "number" || Number.isNaN(value) || value < 0) return "unknown";
  const units = ["B", "KB", "MB", "GB", "TB", "PB"];
  let amount = value;
  let idx = 0;
  while (amount >= 1024 && idx < units.length - 1) {
    amount /= 1024;
    idx += 1;
  }
  return `${amount.toFixed(amount >= 10 || idx === 0 ? 0 : 1)} ${units[idx]}`;
}

function sourceBadge(item: {
  exists: boolean;
  readable: boolean;
  mount_expected?: boolean;
  mount_ok?: boolean;
}): { label: string; ok: boolean } {
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
}): { label: string; ok: boolean } {
  if (!item.exists) return { label: "Missing", ok: false };
  if (!item.writable) return { label: "Not writable", ok: false };
  if (item.mount_expected && item.mount_ok === false) return { label: "Not mounted", ok: false };
  return { label: "Writable", ok: true };
}

export default function BackupPage() {
  const [overview, setOverview] = useState<BackupOverview | null>(null);
  const [logs, setLogs] = useState<BackupLogResponse | null>(null);
  const [selectedRun, setSelectedRun] = useState<string | null>(null);
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
      setError(null);
      if (!selectedRun && data.recent_runs.length > 0) {
        setSelectedRun(data.recent_runs[0].run_id);
      }
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
    } finally {
      setWorking(false);
    }
  }

  async function onStop() {
    setWorking(true);
    try {
      await stopBackup();
      await refresh();
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
        enabled: true
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

  const activeRun = useMemo(
    () => overview?.recent_runs.find((run) => run.run_id === selectedRun) ?? null,
    [overview?.recent_runs, selectedRun]
  );

  const targetIdByKey = useMemo(() => {
    const map = new Map<string, BackupTarget>();
    if (!overview) return map;
    for (const t of overview.target_mappings) {
      map.set(`${t.profile}|${t.source}|${t.destination}`, t);
    }
    return map;
  }, [overview]);

  return (
    <section className="backup-layout">
      {error && <div className="error-banner">{error}</div>}
      {!overview ? (
        <div className="muted">Loading backup status…</div>
      ) : (
        <>
          <div className="backup-header panel">
            <div>
              <h2>Backup</h2>
              <p className="muted">
                Schedule: {overview.timer_schedule ?? "unknown"} · Pool: {overview.backup_pool ?? "unknown"} · Bandwidth:{" "}
                {overview.rsync_bwlimit ?? "unknown"}
              </p>
              <div className="health-pill">
                <span className={`status-dot ${overview.storage_ready ? "success" : "warning"}`} />
                <span>{overview.storage_ready ? "Storage ready" : "Storage issues detected"}</span>
              </div>
            </div>
            <div className="inline-actions">
              {overview.status.running ? (
                <button disabled={working} onClick={() => void onStop()}>
                  Stop Backup
                </button>
              ) : (
                <button disabled={working} onClick={() => void onStart()}>
                  Start Backup
                </button>
              )}
            </div>
          </div>

          <div className="panel">
            <h3>Backup Scheduler</h3>
            <div className="schedule-form">
              <label className="schedule-toggle">
                <input type="checkbox" checked={scheduleEnabled} onChange={(event) => setScheduleEnabled(event.target.checked)} />
                Enabled
              </label>
              <label>
                Time (UTC)
                <input type="time" value={scheduleTime} onChange={(event) => setScheduleTime(event.target.value)} />
              </label>
              <button disabled={working} onClick={() => void onSaveSchedule()}>
                Save Schedule
              </button>
            </div>
            <p className="muted">
              Next run: {overview.schedule.next_run_at ? new Date(overview.schedule.next_run_at).toLocaleString() : "disabled"}
            </p>
            <p className="muted">
              Last trigger:{" "}
              {overview.schedule.last_triggered_at ? new Date(overview.schedule.last_triggered_at).toLocaleString() : "none"}
            </p>
          </div>

          <div className="panel">
            <p>
              <strong>State:</strong> {overview.status.running ? "Running" : "Idle"}
            </p>
            {overview.status.started_at && (
              <p>
                <strong>Started:</strong> {new Date(overview.status.started_at).toLocaleString()}
              </p>
            )}
            {overview.status.finished_at && (
              <p>
                <strong>Finished:</strong> {new Date(overview.status.finished_at).toLocaleString()}
              </p>
            )}
            {typeof overview.status.exit_code === "number" && (
              <p>
                <strong>Exit code:</strong> {overview.status.exit_code}
              </p>
            )}
            <p>
              <strong>Progress:</strong> {overview.status.progress_line ?? "No active progress line."}
            </p>
            {overview.status.progress_total ? (
              <p>
                <strong>Step Progress:</strong> {overview.status.progress_current ?? 0}/{overview.status.progress_total}{" "}
                {overview.status.active_step ? `· ${overview.status.active_step}` : ""}
              </p>
            ) : null}
          </div>

          <div className="backup-grid">
            <div className="panel">
              <h3>Backup Targets & Destinations</h3>
              <div className="target-health-list">
                {overview.target_health.map((target) => {
                  const linkedTarget = targetIdByKey.get(`${target.profile}|${target.source}|${target.destination}`);
                  return (
                    <div className="target-health-row" key={`${target.profile}:${target.source}`}>
                      <div className="target-health-header">
                        <strong>{target.source}</strong>
                        <div className="inline-actions">
                          <span className={target.ready ? "health-badge ready" : "health-badge issue"}>
                            {target.ready ? "Ready" : "Issue"}
                          </span>
                          {linkedTarget && (
                            <>
                              <button
                                className="tiny-button"
                                disabled={working || overview.status.running || !target.ready}
                                title={overview.status.running ? "A backup is already running." : "Run backup for this target only"}
                                onClick={() => void onBackupTarget(linkedTarget)}
                              >
                                Backup
                              </button>
                              <button className="tiny-button" onClick={() => void onToggleTarget(linkedTarget)}>
                                {linkedTarget.enabled ? "Disable" : "Enable"}
                              </button>
                              <button
                                className="icon-danger-button"
                                title="Remove target"
                                onClick={() => void onDeleteTarget(linkedTarget)}
                              >
                                ×
                              </button>
                            </>
                          )}
                        </div>
                      </div>
                      <p className="muted">{target.destination}</p>
                      <p className="muted">
                        Last backup: {target.last_backup_at ? new Date(target.last_backup_at).toLocaleString() : "Never"}
                      </p>
                      <div className="target-health-meta">
                        <span>
                          {target.source_exists && target.source_readable && (target.source_mount_ok ?? true)
                            ? "Source OK"
                            : "Source problem"}
                        </span>
                        <span>
                          {target.destination_exists && target.destination_writable && (target.destination_mount_ok ?? false)
                            ? "Destination writable"
                            : "Destination problem"}
                        </span>
                        <span>{target.destination_mount_ok ?? target.destination_separate_mount ? "Mounted" : "Not mounted"}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
              <details className="add-target-details">
                <summary>Add Target</summary>
                <div className="schedule-form" style={{ marginTop: 10 }}>
                  <label>
                    Profile
                    <input value={newTarget.profile} onChange={(event) => setNewTarget({ ...newTarget, profile: event.target.value })} />
                  </label>
                  <label>
                    Source
                    <input value={newTarget.source} onChange={(event) => setNewTarget({ ...newTarget, source: event.target.value })} />
                  </label>
                  <label>
                    Destination
                    <input
                      value={newTarget.destination}
                      onChange={(event) => setNewTarget({ ...newTarget, destination: event.target.value })}
                    />
                  </label>
                  <button disabled={working} onClick={() => void onAddTarget()}>
                    Add
                  </button>
                </div>
              </details>
            </div>

            <div className="panel">
              <h3>Storage Health & Capacity</h3>
              {overview.storage_diagnostics.filesystems.length > 0 && (
                <>
                  <h4>Disk usage (all mounts)</h4>
                  <div className="storage-df-table-wrap">
                    <table className="storage-df-table">
                      <thead>
                        <tr>
                          <th>Filesystem</th>
                          <th>Mount</th>
                          <th>Used</th>
                          <th>Total</th>
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
                            <td>{formatBytes(row.total_bytes)}</td>
                            <td>{formatBytes(row.free_bytes)}</td>
                            <td>{row.used_percent != null ? `${row.used_percent}%` : "—"}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              )}
              <div className="storage-health-grid">
                <div>
                  <h4>Sources</h4>
                  <div className="storage-list">
                    {overview.storage_diagnostics.sources.map((item) => (
                      <div key={`source-${item.path}`} className="storage-item">
                        <div className="storage-item-head">
                          <strong>{item.path}</strong>
                          {(() => {
                            const badge = sourceBadge(item);
                            return <span className={badge.ok ? "health-badge ready" : "health-badge issue"}>{badge.label}</span>;
                          })()}
                        </div>
                        <p className="muted">
                          Used {formatBytes(item.used_bytes)} / {formatBytes(item.total_bytes)} ({item.used_percent ?? "?"}%)
                        </p>
                        <p className="muted">Free: {formatBytes(item.free_bytes)}</p>
                        <p className="muted">Mount: {item.mount_point ?? "unknown"}</p>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <h4>Destinations</h4>
                  <div className="storage-list">
                    {overview.storage_diagnostics.destinations.map((item) => (
                      <div key={`dest-${item.path}`} className="storage-item">
                        <div className="storage-item-head">
                          <strong>{item.path}</strong>
                          {(() => {
                            const badge = destinationBadge(item);
                            return <span className={badge.ok ? "health-badge ready" : "health-badge issue"}>{badge.label}</span>;
                          })()}
                        </div>
                        <p className="muted">
                          Used {formatBytes(item.used_bytes)} / {formatBytes(item.total_bytes)} ({item.used_percent ?? "?"}%)
                        </p>
                        <p className="muted">Free: {formatBytes(item.free_bytes)}</p>
                        <p className="muted">Mount: {item.mount_point ?? "unknown"}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
              <div className="zfs-panel">
                <div className="storage-item-head">
                  <h4>ZFS Status</h4>
                  <span className={overview.storage_diagnostics.zfs.status_ok === false ? "health-badge issue" : "health-badge ready"}>
                    {overview.storage_diagnostics.zfs.status_ok === false ? "Issue" : "OK"}
                  </span>
                </div>
                <p className="muted">
                  Pool: {overview.storage_diagnostics.zfs.pool ?? "unknown"} · Health: {overview.storage_diagnostics.zfs.health ?? "unknown"}
                </p>
                <p className="muted">
                  ZFS used {formatBytes(overview.storage_diagnostics.zfs.used_bytes)} / available{" "}
                  {formatBytes(overview.storage_diagnostics.zfs.avail_bytes)}
                </p>
                {overview.storage_diagnostics.zfs.status_summary && <p className="muted">{overview.storage_diagnostics.zfs.status_summary}</p>}
                {overview.storage_diagnostics.zfs.command_error && <p className="muted">{overview.storage_diagnostics.zfs.command_error}</p>}
                {overview.storage_diagnostics.zfs.errors.length > 0 && (
                  <div className="storage-errors">
                    {overview.storage_diagnostics.zfs.errors.map((entry, idx) => (
                      <p key={`${entry}-${idx}`}>{entry}</p>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="panel">
            <h3>Recent Runs</h3>
            <div className="run-list">
              {overview.recent_runs.map((run) => (
                <button key={run.run_id} className={selectedRun === run.run_id ? "active" : ""} onClick={() => setSelectedRun(run.run_id)}>
                  <span>{run.run_id}</span>
                  <span className={`run-status-badge ${run.status ?? "unknown"}`}>{run.status ?? "unknown"}</span>
                  <span className="muted">
                    archive: {run.archive_ok === true ? "ok" : run.archive_ok === false ? "failed" : "unknown"} · sync failed:{" "}
                    {run.sync_failed ?? "?"}/{run.sync_total ?? "?"}
                  </span>
                  <span className="muted">{run.last_line ?? "No summary line."}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="panel">
            <h3>Run Outcome {activeRun ? `· ${activeRun.run_id}` : ""}</h3>
            {!logs?.summary ? (
              <p className="muted">No structured summary found for this run yet.</p>
            ) : (
              (() => {
                const syncResults = logs.summary?.sync_results ?? [];
                return (
              <div className="run-outcome-grid">
                <p>
                  <strong>Status:</strong> {logs.summary.status}
                </p>
                <p>
                  <strong>Archive:</strong>{" "}
                  {logs.summary.include_archive === false ? "Skipped (target-only run)" : logs.summary.archive_ok ? "OK" : "Failed"}{" "}
                  {logs.summary.archive_file ? `(${logs.summary.archive_file})` : ""}
                </p>
                <p>
                  <strong>Sync:</strong> {logs.summary.sync_ok}/{logs.summary.sync_total} OK, {logs.summary.sync_failed} failed
                </p>
                <p>
                  <strong>Snapshot:</strong> {logs.summary.snapshot_status ?? "skipped"}
                </p>
                {logs.summary.errors && logs.summary.errors.length > 0 && (
                  <div className="storage-errors">
                    {logs.summary.errors.map((entry, idx) => (
                      <p key={`${entry}-${idx}`}>{entry}</p>
                    ))}
                  </div>
                )}
                {syncResults.length > 0 && (
                  <div className="run-list">
                    {syncResults.map((item) => (
                      <div key={`${item.source}-${item.destination}`} className="snapshot-row">
                        <span>
                          {item.source} → {item.destination}
                        </span>
                        <span className={item.ok ? "health-badge ready" : "health-badge issue"}>
                          {item.ok ? "OK" : `exit ${item.exit_code}`}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
                );
              })()
            )}
          </div>

          <div className="panel">
            <h3>Snapshot History</h3>
            {overview.snapshots.length === 0 ? (
              <p className="muted">No snapshots parsed yet.</p>
            ) : (
              <div className="run-list">
                {overview.snapshots.map((snapshot) => (
                  <div key={`${snapshot.name}-${snapshot.timestamp}`} className="snapshot-row">
                    <span>{snapshot.name}</span>
                    <span className="muted">{snapshot.timestamp}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="panel">
            <h3>Backup Files</h3>
            {overview.backup_files.length === 0 ? (
              <p className="muted">No backups created yet.</p>
            ) : (
              <div className="run-list">
                {overview.backup_files.map((file) => (
                  <a key={file.name} href={toApiUrl(`/api/backups/files/${encodeURIComponent(file.name)}`)} className="snapshot-row">
                    <span className="mono">{file.name}</span>
                    <span className="muted">
                      {formatBytes(file.bytes)} · {new Date(file.modified_at).toLocaleString()}
                    </span>
                  </a>
                ))}
              </div>
            )}
          </div>

          <div className="panel">
            <h3>Run Logs {activeRun ? `· ${activeRun.run_id}` : ""}</h3>
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

