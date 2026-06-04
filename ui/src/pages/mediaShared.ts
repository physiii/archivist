import type {
  MediaArtifact,
  MediaDocumentSection,
  MediaPipelineJob,
  MediaPipelineResult,
} from "../types";

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1073741824) return `${(bytes / 1048576).toFixed(1)} MB`;
  return `${(bytes / 1073741824).toFixed(2)} GB`;
}

export function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds.toFixed(0)}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${Math.floor(seconds % 60)}s`;
  return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
}

export function relativeTime(timestampSeconds: number): string {
  if (!timestampSeconds) return "—";
  const diff = Math.max(0, Math.floor(Date.now() / 1000 - timestampSeconds));
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

export function formatAgeSec(seconds: number | null | undefined): string {
  if (seconds == null || !Number.isFinite(seconds)) return "—";
  if (seconds < 60) return `${Math.round(seconds)}s ago`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}

export function clip(text: string, limit: number) {
  return text.length > limit ? `${text.slice(0, limit)}…` : text;
}

export function formatRange(start: number, end: number) {
  const toClock = (value: number) => {
    const minutes = Math.floor(value / 60);
    const seconds = Math.floor(value % 60);
    return `${minutes}:${seconds.toString().padStart(2, "0")}`;
  };
  return `${toClock(start)} - ${toClock(end)}`;
}

export function summarizeValue(value: unknown) {
  if (value == null) return "—";
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  if (Array.isArray(value)) return `${value.length} item${value.length === 1 ? "" : "s"}`;
  return clip(JSON.stringify(value), 72);
}

export function humanizeLabel(value: string) {
  return value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

export function safeStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.filter((item): item is string => typeof item === "string" && item.trim().length > 0);
}

export function formatDocumentFormat(format?: string) {
  if (!format) return "Document";
  return humanizeLabel(format);
}

export function buildMarkdownFromSections(sections: MediaDocumentSection[]) {
  return sections
    .filter((section) => (section.content || "").trim())
    .map((section) => `## ${section.heading}\n\n${section.content?.trim()}`)
    .join("\n\n");
}

export function coerceMarkdownText(text: string) {
  const trimmed = text.trim();
  if (!trimmed) return "";
  if (/^#{1,6}\s/m.test(trimmed) || /```/.test(trimmed)) {
    return trimmed;
  }
  return trimmed
    .split(/\n{2,}/)
    .map((block) => block.trim())
    .filter(Boolean)
    .map((block) => {
      if (/^[-*]\s/m.test(block) || /^\d+\.\s/m.test(block) || /^>\s/m.test(block) || /^\|/.test(block)) {
        return block;
      }
      return block
        .split("\n")
        .map((line) => line.trimEnd())
        .join("  \n");
    })
    .join("\n\n");
}

export function stripMarkdownSyntax(text: string) {
  return text
    .replace(/^#{1,6}\s+/gm, "")
    .replace(/^\s*[-*+]\s+/gm, "")
    .replace(/^\s*\d+\.\s+/gm, "")
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, "$1")
    .replace(/!\[([^\]]*)\]\(([^)]+)\)/g, "$1")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/\*\*([^*]+)\*\*/g, "$1")
    .replace(/\*([^*]+)\*/g, "$1")
    .replace(/^>\s?/gm, "")
    .replace(/\|/g, " ")
    .replace(/\[(?:\d+(?:\.\d+)?s\s*-\s*\d+(?:\.\d+)?s|question|decision|action|speech|observation)\]/gi, "")
    .replace(/\s+/g, " ")
    .trim();
}

export function readablePreview(text: string, limit = 220) {
  if (!text.trim()) return "";
  const blocks = text
    .split(/\n{2,}/)
    .map((block) => stripMarkdownSyntax(block))
    .filter(Boolean);
  const preferred =
    blocks.find((block) => block.length > 24 && !/^meeting minutes$/i.test(block) && !/^discussion$/i.test(block)) ||
    blocks[0] ||
    "";
  return clip(preferred, limit);
}

export function subtitlePreview(text: string, limit = 220) {
  if (!text.trim()) return "";
  const spokenLines = text
    .replace(/\r\n/g, "\n")
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line && line !== "WEBVTT" && !line.startsWith("NOTE") && !/^\d+$/.test(line) && !/^\d{2}:\d{2}:\d{2}\.\d+\s+-->\s+\d{2}:\d{2}:\d{2}\.\d+/.test(line));
  return clip(spokenLines.join(" "), limit);
}

export function findSection(sections: MediaDocumentSection[], pattern: RegExp) {
  return (
    sections.find((section) => section.kind === "walkthrough") ??
    sections.find((section) => pattern.test(section.heading)) ??
    null
  );
}

export function transcriptFromResult(result: MediaPipelineResult | null, transcriptArtifact: MediaArtifact | null) {
  if (transcriptArtifact?.content) return transcriptArtifact.content;
  const transcriptPayload = result?.transcript;
  if (!transcriptPayload) return "";
  if (typeof transcriptPayload.text === "string" && transcriptPayload.text.trim()) {
    return transcriptPayload.text;
  }
  if (Array.isArray(transcriptPayload.segments)) {
    return transcriptPayload.segments
      .map((segment) => (typeof segment?.text === "string" ? segment.text.trim() : ""))
      .filter(Boolean)
      .join(" ");
  }
  return "";
}

export function jobPhaseLabel(job: MediaPipelineJob) {
  if (job.status === "done") return "Core outputs ready";
  if (job.status === "error") return job.error || "Pipeline failed";
  return LAYER_LABELS[job.current_layer] || job.current_layer || "Queued";
}

export function artifactKindSort(left: string, right: string) {
  const order = ["subject_line", "document", "transcript", "memory", "recap", "event", "speech_segment", "keyframe"];
  const leftIndex = order.indexOf(left);
  const rightIndex = order.indexOf(right);
  if (leftIndex === -1 && rightIndex === -1) return left.localeCompare(right);
  if (leftIndex === -1) return 1;
  if (rightIndex === -1) return -1;
  return leftIndex - rightIndex;
}

export const LAYER_LABELS: Record<string, string> = {
  L0_evidence: "Evidence",
  L1_filtering: "Filtering",
  L2_events: "Events",
  L3_recaps: "Recaps",
  L4_memory: "Context",
  L5_compose: "Walkthrough",
  L6_vectorstore: "Indexing",
  L7_subject_line: "Subject line",
};

export const KIND_COLORS: Record<string, string> = {
  transcript: "workspace-chip--accent",
  event: "workspace-chip--warning",
  recap: "workspace-chip--success",
  memory: "workspace-chip--accent",
  document: "workspace-chip--success",
  subject_line: "workspace-chip--success",
  speech_segment: "",
  keyframe: "",
};
