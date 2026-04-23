import { useCallback, useEffect, useState } from "react";
import type { McpIntegration } from "../types";
import { getIntegrationsStatus } from "../lib/api";

const GOOGLE_ICONS: Record<string, React.ReactNode> = {
  gmail: (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="4" width="20" height="16" rx="2" /><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7" />
    </svg>
  ),
  "google-calendar": (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="4" width="18" height="18" rx="2" /><line x1="16" y1="2" x2="16" y2="6" /><line x1="8" y1="2" x2="8" y2="6" /><line x1="3" y1="10" x2="21" y2="10" />
    </svg>
  ),
  "google-drive": (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2 2 19.5h20L12 2Z" /><path d="m2 19.5 5-8.5h14" /><path d="m21 19.5-5-8.5" />
    </svg>
  ),
};

function statusColor(status: McpIntegration["status"]): string {
  if (status === "connected") return "#22c55e";
  if (status === "needs_auth") return "#f59e0b";
  return "#ef4444";
}

function statusLabel(status: McpIntegration["status"]): string {
  switch (status) {
    case "connected": return "Connected";
    case "needs_auth": return "Needs auth";
    case "timeout": return "Timeout";
    case "not_installed": return "Not installed";
    case "no_response": return "No response";
    case "error": return "Error";
    default: return "Checking...";
  }
}

function normalizeIntegrations(payload: unknown): McpIntegration[] {
  if (Array.isArray(payload)) {
    return payload as McpIntegration[];
  }

  if (
    payload &&
    typeof payload === "object" &&
    "integrations" in payload &&
    Array.isArray((payload as { integrations?: unknown }).integrations)
  ) {
    return (payload as { integrations: McpIntegration[] }).integrations;
  }

  return [];
}

export default function IntegrationsStatus() {
  const [integrations, setIntegrations] = useState<McpIntegration[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const data = await getIntegrationsStatus();
      setIntegrations(normalizeIntegrations(data));
    } catch {
      setIntegrations([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
    const interval = setInterval(() => void refresh(), 30000);
    return () => clearInterval(interval);
  }, [refresh]);

  const allConnected = integrations.length > 0 && integrations.every(i => i.connected);
  const anyNeedsAuth = integrations.some(i => i.status === "needs_auth");

  return (
    <div className="integrations-status">
      <button
        className="integrations-header"
        onClick={() => setExpanded(e => !e)}
        title="Google integrations"
      >
        <span className="integrations-title">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 2a4 4 0 0 0-4 4c0 2 1.5 3.5 4 5 2.5-1.5 4-3 4-5a4 4 0 0 0-4-4Z" />
            <path d="M12 11v5" /><circle cx="12" cy="19" r="2" />
            <path d="M6 19h12" />
          </svg>
          Integrations
        </span>
        <span style={{ display: "flex", gap: 3, alignItems: "center" }}>
          {loading ? (
            <span className="muted" style={{ fontSize: "0.72rem" }}>...</span>
          ) : (
            integrations.map(i => (
              <span
                key={i.key ?? `${i.id}:${i.account ?? "default"}`}
                className="status-dot"
                style={{ background: statusColor(i.status), width: 7, height: 7 }}
                title={i.account ? `${i.account} · ${i.name}: ${statusLabel(i.status)}` : `${i.name}: ${statusLabel(i.status)}`}
              />
            ))
          )}
          <svg
            width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
            style={{ transform: expanded ? "rotate(180deg)" : "rotate(0)", transition: "transform 0.2s", marginLeft: 2 }}
          >
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </span>
      </button>

      {expanded && (
        <div className="integrations-list">
          {loading && <span className="muted" style={{ fontSize: "0.78rem", padding: "6px 0" }}>Checking Google accounts...</span>}
          {!loading && integrations.length === 0 && (
            <span className="muted" style={{ fontSize: "0.78rem" }}>No integrations configured</span>
          )}
          {integrations.map(i => (
            <div key={i.key ?? `${i.id}:${i.account ?? "default"}`} className="integration-row">
              <span className="integration-icon" style={{ color: statusColor(i.status) }}>
                {GOOGLE_ICONS[i.id] ?? null}
              </span>
              <span className="integration-info">
                <span className="integration-name">{i.name}</span>
                <span className="integration-desc muted">
                  {i.account ? `${i.account} · ${i.description}` : i.description}
                </span>
              </span>
              <span
                className="integration-dot"
                style={{ background: statusColor(i.status) }}
                title={i.account ? `${i.account}: ${i.error ?? statusLabel(i.status)}` : (i.error ?? statusLabel(i.status))}
              />
            </div>
          ))}
          {!loading && (
            <div className="integrations-summary">
              {allConnected ? (
                <span style={{ color: "#22c55e", fontSize: "0.75rem" }}>All connected</span>
              ) : anyNeedsAuth ? (
                <span style={{ color: "#f59e0b", fontSize: "0.75rem" }}>Grant account permissions to connect</span>
              ) : (
                <span style={{ color: "#ef4444", fontSize: "0.75rem" }}>Connection issues detected</span>
              )}
            </div>
          )}
          {!loading && (
            <button className="integrations-refresh" onClick={() => { setLoading(true); void refresh(); }}>
              Refresh
            </button>
          )}
        </div>
      )}
    </div>
  );
}
