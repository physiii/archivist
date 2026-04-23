import { useEffect, useState } from "react";

interface HealthComponent {
  status: string;
  error?: string;
  hours_since?: number;
  stale?: number;
  broken?: number;
  current?: number;
  latest?: string;
  last_imported_at?: string;
}

interface HealthResponse {
  status: "healthy" | "degraded" | "unhealthy";
  components: Record<string, HealthComponent>;
}

function formatWarning(name: string, component: HealthComponent): string | null {
  if (component.status === "ok") return null;

  switch (name) {
    case "google_import":
      if (component.status === "stale") {
        const hours = component.hours_since != null ? `${component.hours_since}h` : "unknown time";
        return `Google import is ${hours} old`;
      }
      if (component.status === "no_data") return "No Google data imported yet";
      return `Google import error: ${component.error ?? "unknown"}`;

    case "media_pipeline":
      if (component.stale || component.broken) {
        const parts: string[] = [];
        if (component.stale) parts.push(`${component.stale} stale`);
        if (component.broken) parts.push(`${component.broken} broken`);
        return `Media pipeline: ${parts.join(", ")} results`;
      }
      return `Media pipeline: ${component.error ?? "degraded"}`;

    case "milvus":
      return `Milvus: ${component.error ?? "unreachable"}`;

    case "backups":
      if (component.status === "stale") {
        return `Last backup is ${component.hours_since ?? "?"}h old`;
      }
      if (component.status === "no_data") return "No backups found";
      return `Backup error: ${component.error ?? "unknown"}`;

    default:
      return `${name}: ${component.status}`;
  }
}

export default function HealthBanner() {
  const [health, setHealth] = useState<HealthResponse | null>(null);

  useEffect(() => {
    let active = true;
    async function poll() {
      try {
        const res = await fetch("/health");
        if (res.ok && active) {
          setHealth(await res.json() as HealthResponse);
        }
      } catch {
        // Silently ignore fetch errors -- banner just won't show
      }
    }
    void poll();
    const interval = setInterval(() => void poll(), 30_000);
    return () => { active = false; clearInterval(interval); };
  }, []);

  if (!health || health.status === "healthy") return null;

  const warnings: string[] = [];
  for (const [name, component] of Object.entries(health.components)) {
    const msg = formatWarning(name, component);
    if (msg) warnings.push(msg);
  }

  if (warnings.length === 0) return null;

  const hasError = Object.values(health.components).some(
    (c) => c.status === "error",
  );

  return (
    <div className={hasError ? "health-banner health-banner--error" : "health-banner health-banner--warning"}>
      <span className="health-banner-icon">{hasError ? "\u26A0" : "\u25CF"}</span>
      <span className="health-banner-text">{warnings.join(" \u00B7 ")}</span>
    </div>
  );
}
