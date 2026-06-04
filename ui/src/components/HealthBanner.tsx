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
  model?: string;
  endpoint?: string;
  vector_dim?: number;
  expected_dim?: number;
  latency_ms?: number;
  http_status?: number;
  device?: string;
  device_index?: number | null;
  local_model?: string;
  compute_type?: string;
  gpu_available?: boolean;
  gpu_device_count?: number;
  gpu_device_names?: string[];
  nvidia_visible_devices?: string;
  available?: boolean;
  severity?: string;
  sources?: Record<string, { status: string; last_event_age_s?: number | null; error?: string | null }>;
  channels?: Record<string, boolean>;
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

    case "embeddings":
      if (component.status === "ok") return null;
      return `EMBEDDINGS DOWN: ${component.error ?? "local-default smoke test failed"} Dense search, hybrid search, indexing, media recall, and agent retrieval are degraded.`;

    case "transcription":
      if (component.status === "ok") return null;
      if (component.status === "cpu_fallback") {
        const model = component.local_model || component.model || "whisper";
        const visible = component.nvidia_visible_devices ?? "?";
        return `TRANSCRIPTION ON CPU: ${model} fell back to CPU (NVIDIA_VISIBLE_DEVICES=${visible}, cuda_devices=${component.gpu_device_count ?? 0}). Realtime transcription will be orders of magnitude slower. Fix GPU wiring immediately.`;
      }
      return `TRANSCRIPTION DOWN: ${component.error ?? "whisper model failed to load"} No audio will be transcribed.`;

    case "backups":
      if (component.status === "stale") {
        return `Last backup is ${component.hours_since ?? "?"}h old`;
      }
      if (component.status === "no_data") return "No backups found";
      return `Backup error: ${component.error ?? "unknown"}`;

    case "source_ingest": {
      if (component.status === "ok") return null;
      const bad: string[] = [];
      for (const [id, info] of Object.entries(component.sources ?? {})) {
        if (info.status === "down" || info.status === "stale" || info.status === "unknown") {
          const age = info.last_event_age_s != null ? ` (${Math.round(info.last_event_age_s)}s silent)` : "";
          bad.push(`${id}:${info.status}${age}`);
        }
      }
      if (bad.length === 0) return null;
      return `Camera/mic ingest degraded: ${bad.join(", ")}`;
    }

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
