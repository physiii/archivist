import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import MarkdownMessage from "../components/MarkdownMessage";
import { WorkspaceEmpty, WorkspacePage, WorkspacePanel } from "../components/Workspace";
import type {
  MediaArtifact,
  MediaAsset,
  MediaDocumentSection,
  MediaPipelineJob,
  MediaPipelineResult,
} from "../types";
import {
  KIND_COLORS,
  artifactKindSort,
  buildMarkdownFromSections,
  clip,
  coerceMarkdownText,
  findSection,
  formatBytes,
  formatDocumentFormat,
  formatDuration,
  formatRange,
  humanizeLabel,
  jobPhaseLabel,
  relativeTime,
  readablePreview,
  safeStringArray,
  stripMarkdownSyntax,
  subtitlePreview,
  summarizeValue,
  transcriptFromResult,
} from "./mediaShared";

export default function MediaDetailPage() {
  const navigate = useNavigate();
  const { mediaId = "" } = useParams();

  const [assets, setAssets] = useState<MediaAsset[]>([]);
  const [jobs, setJobs] = useState<MediaPipelineJob[]>([]);
  const [pipelineResult, setPipelineResult] = useState<MediaPipelineResult | null>(null);
  const [artifacts, setArtifacts] = useState<MediaArtifact[]>([]);
  const [traceArtifacts, setTraceArtifacts] = useState<MediaArtifact[]>([]);
  const [artifactFilter, setArtifactFilter] = useState<string>("all");
  const [selectedArtifactId, setSelectedArtifactId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"deliverables" | "transcript" | "technical">("deliverables");
  const [showRawArtifacts, setShowRawArtifacts] = useState(false);
  const [traceLoading, setTraceLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDetail = useCallback(async () => {
    if (!mediaId) return;
    setLoading(true);
    try {
      const [assetsRes, jobsRes, pipelineRes, artifactsRes] = await Promise.all([
        fetch("/api/media/assets", { cache: "no-store" }),
        fetch("/api/media/jobs", { cache: "no-store" }),
        fetch(`/api/media/pipeline/${mediaId}`, { cache: "no-store" }),
        fetch(`/api/media/artifacts/${mediaId}?scope=public`, { cache: "no-store" }),
      ]);

      if (assetsRes.ok) {
        const data = (await assetsRes.json()) as { assets?: MediaAsset[] };
        setAssets(data.assets ?? []);
      } else {
        setAssets([]);
      }

      if (jobsRes.ok) {
        const data = (await jobsRes.json()) as { jobs?: MediaPipelineJob[] };
        setJobs(data.jobs ?? []);
      } else {
        setJobs([]);
      }

      setPipelineResult(pipelineRes.ok ? ((await pipelineRes.json()) as MediaPipelineResult) : null);

      if (artifactsRes.ok) {
        const payload = (await artifactsRes.json()) as { artifacts?: MediaArtifact[] };
        setArtifacts(payload.artifacts ?? []);
      } else {
        setArtifacts([]);
      }
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load media detail.");
      setPipelineResult(null);
      setArtifacts([]);
    } finally {
      setLoading(false);
    }
  }, [mediaId]);

  useEffect(() => {
    void fetchDetail();
    const interval = setInterval(() => {
      void fetchDetail();
    }, 4000);
    return () => clearInterval(interval);
  }, [fetchDetail]);

  useEffect(() => {
    setShowRawArtifacts(false);
    setArtifactFilter("all");
    setSelectedArtifactId(null);
    setTraceArtifacts([]);
  }, [mediaId]);

  const loadRawTrace = useCallback(async () => {
    if (!mediaId || traceLoading || traceArtifacts.length > 0) return;
    setTraceLoading(true);
    try {
      const response = await fetch(`/api/media/artifacts/${mediaId}?scope=trace`, { cache: "no-store" });
      if (!response.ok) {
        throw new Error("Failed to load raw trace.");
      }
      const payload = (await response.json()) as { artifacts?: MediaArtifact[] };
      setTraceArtifacts(payload.artifacts ?? []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load raw trace.");
    } finally {
      setTraceLoading(false);
    }
  }, [mediaId, traceArtifacts.length, traceLoading]);

  useEffect(() => {
    if (showRawArtifacts) {
      void loadRawTrace();
    }
  }, [loadRawTrace, showRawArtifacts]);

  useEffect(() => {
    if (traceArtifacts.length === 0) {
      setSelectedArtifactId(null);
      return;
    }
    const filtered = artifactFilter === "all" ? traceArtifacts : traceArtifacts.filter((artifact) => artifact.kind === artifactFilter);
    if (filtered.length === 0) {
      setSelectedArtifactId(null);
      return;
    }
    if (!selectedArtifactId || !filtered.some((artifact) => artifact.artifact_id === selectedArtifactId)) {
      setSelectedArtifactId(filtered[0].artifact_id);
    }
  }, [artifactFilter, traceArtifacts, selectedArtifactId]);

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

  const selectedAsset = assets.find((asset) => asset.media_id === mediaId) ?? null;
  const selectedJob = jobsByMediaId.get(mediaId) ?? null;

  const artifactCounts = useMemo(() => {
    const counts = new Map<string, number>();
    for (const artifact of artifacts) {
      counts.set(artifact.kind, (counts.get(artifact.kind) ?? 0) + 1);
    }
    return counts;
  }, [artifacts]);
  const artifactKinds = useMemo(
    () => [...artifactCounts.keys()].sort(artifactKindSort),
    [artifactCounts],
  );
  const traceArtifactCounts = useMemo(() => {
    const counts = new Map<string, number>();
    for (const artifact of traceArtifacts) {
      counts.set(artifact.kind, (counts.get(artifact.kind) ?? 0) + 1);
    }
    return counts;
  }, [traceArtifacts]);
  const traceArtifactKinds = useMemo(
    () => [...traceArtifactCounts.keys()].sort(artifactKindSort),
    [traceArtifactCounts],
  );
  const filteredArtifacts = useMemo(
    () => (artifactFilter === "all" ? traceArtifacts : traceArtifacts.filter((artifact) => artifact.kind === artifactFilter)),
    [artifactFilter, traceArtifacts],
  );
  const selectedArtifact = filteredArtifacts.find((artifact) => artifact.artifact_id === selectedArtifactId) ?? null;

  const transcriptArtifact = useMemo(
    () => artifacts.find((artifact) => artifact.kind === "transcript") ?? null,
    [artifacts],
  );
  const documentArtifact = useMemo(
    () => artifacts.find((artifact) => artifact.kind === "document") ?? null,
    [artifacts],
  );
  const memoryArtifact = useMemo(
    () => artifacts.find((artifact) => artifact.kind === "memory") ?? null,
    [artifacts],
  );
  const subjectArtifact = useMemo(
    () => artifacts.find((artifact) => artifact.kind === "subject_line") ?? null,
    [artifacts],
  );

  const documentSections = (pipelineResult?.document?.sections ?? []) as MediaDocumentSection[];
  const walkthroughSection = findSection(documentSections, /(discussion|timeline|walkthrough|chronology)/i);
  const explicitContextSections = documentSections.filter((section) => section.kind === "context");
  const summarySections = explicitContextSections.length
    ? explicitContextSections
    : documentSections.filter((section) => section !== walkthroughSection);
  const parsedMemory = useMemo(() => {
    if (!memoryArtifact?.content) return null;
    try {
      const payload = JSON.parse(memoryArtifact.content) as Record<string, unknown>;
      return typeof payload === "object" && payload ? payload : null;
    } catch {
      return null;
    }
  }, [memoryArtifact]);
  const memoryLayer = (pipelineResult?.layers?.L4_memory ?? {}) as Record<string, unknown>;
  const contextOverview =
    (typeof parsedMemory?.context_overview === "string" && parsedMemory.context_overview.trim()) ||
    (typeof memoryLayer.context_overview === "string" && memoryLayer.context_overview.trim()) ||
    "";
  const participants = safeStringArray(parsedMemory?.main_actors ?? memoryLayer.main_actors);
  const themes = safeStringArray(parsedMemory?.inferred_themes ?? memoryLayer.themes ?? memoryLayer.inferred_themes);
  const finalTakeaways = safeStringArray(parsedMemory?.final_takeaways);
  const notableEvidence = safeStringArray(parsedMemory?.notable_evidence);
  const openLoops = safeStringArray(parsedMemory?.open_loops);
  const openLoopsCount =
    openLoops.length || (typeof memoryLayer.open_loops_count === "number" ? memoryLayer.open_loops_count : 0);
  const documentFullText =
    typeof pipelineResult?.document?.full_text === "string" && pipelineResult.document.full_text.trim()
      ? pipelineResult.document.full_text
      : documentArtifact?.content || "";
  const memoryContextMarkdown = [
    contextOverview ? `## Context Overview\n${contextOverview}` : "",
    finalTakeaways.length ? `## Key Takeaways\n${finalTakeaways.map((item) => `- ${item}`).join("\n")}` : "",
    themes.length ? `## Key Topics\n${themes.map((theme) => `- ${theme}`).join("\n")}` : "",
    notableEvidence.length ? `## Evidence Notes\n${notableEvidence.slice(0, 5).map((item) => `- ${item}`).join("\n")}` : "",
    openLoopsCount > 0
      ? `## Open Questions\n${
          openLoops.length
            ? openLoops.map((item) => `- ${item}`).join("\n")
            : `- ${openLoopsCount} unresolved questions remain.`
        }`
      : "",
  ].filter(Boolean).join("\n\n");
  const contextMarkdown = explicitContextSections.length
    ? buildMarkdownFromSections(explicitContextSections)
    : memoryContextMarkdown || (summarySections.length
      ? buildMarkdownFromSections(summarySections)
      : [
        participants.length ? `## Participants\n${participants.map((participant) => `- ${participant}`).join("\n")}` : "",
        themes.length ? `## Themes\n${themes.map((theme) => `- ${theme}`).join("\n")}` : "",
        `## Open Questions\n${openLoopsCount > 0 ? `- ${openLoopsCount} unresolved questions remain.` : "- No unresolved questions detected."}`,
      ].filter(Boolean).join("\n\n"));
  const walkthroughMarkdown = walkthroughSection
    ? buildMarkdownFromSections([walkthroughSection])
    : documentFullText
      ? coerceMarkdownText(documentFullText)
      : buildMarkdownFromSections(documentSections);
  const transcriptText = transcriptFromResult(pipelineResult, transcriptArtifact);
  const transcriptVttText =
    typeof pipelineResult?.transcript?.vtt_text === "string" ? pipelineResult.transcript.vtt_text.trim() : "";
  const summaryLead = summarySections.map((section) => readablePreview(section.content || "", 180)).find(Boolean) || "";
  const contextSnapshot = [
    summaryLead || readablePreview(contextMarkdown, 180),
    participants.length ? `Participants: ${participants.join(", ")}.` : "",
    themes.length ? `Themes: ${themes.join(", ")}.` : "",
    openLoopsCount > 0 ? `${openLoopsCount} open questions remain.` : "No open questions detected.",
  ].filter(Boolean).join(" ");
  const contextPreview = contextSnapshot || readablePreview(contextMarkdown, 220);
  const walkthroughPreview = readablePreview(walkthroughMarkdown, 240);
  const transcriptPreview = transcriptText ? clip(stripMarkdownSyntax(transcriptText), 220) : "";
  const sectionLabels = documentSections.map((section) => section.heading);
  const transcriptVttPreview = subtitlePreview(transcriptVttText, 220);

  const subjectLine =
    (typeof pipelineResult?.subject_line === "string" && pipelineResult.subject_line.trim()) ||
    (typeof pipelineResult?.document?.subject_line === "string" && pipelineResult.document.subject_line.trim()) ||
    subjectArtifact?.content ||
    "";

  const injection = (pipelineResult?.injection ?? {}) as Record<string, unknown>;
  const transcriptEmbedded = injection.transcript_stream_embedded === true;
  const artifactBundleAttached = injection.artifact_bundle_attached === true;
  const transcriptSidecarPath =
    typeof injection.transcript_sidecar_path === "string" && injection.transcript_sidecar_path
      ? injection.transcript_sidecar_path
      : "";
  const publicArtifactCount = typeof pipelineResult?.artifact_count === "number" ? pipelineResult.artifact_count : artifacts.length;
  const traceArtifactCount =
    typeof pipelineResult?.trace_artifact_count === "number" ? pipelineResult.trace_artifact_count : traceArtifacts.length;
  const processingActive = Boolean(selectedJob && selectedJob.status !== "done" && selectedJob.status !== "error");
  const transcriptSidecarLabel = transcriptSidecarPath.split("/").filter(Boolean).pop() || transcriptSidecarPath || "No .vtt sidecar path recorded";
  const traceArtifactCountsFromPipeline = useMemo(() => {
    const counts = new Map<string, number>();
    const rawCounts = pipelineResult?.trace_artifact_counts;
    if (!rawCounts || typeof rawCounts !== "object") {
      return counts;
    }
    for (const [kind, count] of Object.entries(rawCounts)) {
      if (typeof count === "number" && Number.isFinite(count)) {
        counts.set(kind, count);
      }
    }
    return counts;
  }, [pipelineResult]);
  const traceCountsForDisplay = traceArtifacts.length > 0 ? traceArtifactCounts : traceArtifactCountsFromPipeline;
  const traceKindsForDisplay = [...traceCountsForDisplay.keys()].sort(artifactKindSort);
  const overallStatus =
    selectedJob ? (selectedJob.status === "done" ? "Ready" : selectedJob.status) : pipelineResult ? "Ready" : "Unknown";

  const deliverableChecks = [
    {
      label: "Subject line",
      ready: Boolean(subjectLine),
      detail: subjectLine ? clip(subjectLine, 120) : "No single-sentence subject line stored yet.",
    },
    {
      label: "Context",
      ready: Boolean(contextMarkdown || participants.length || openLoopsCount),
      detail: contextMarkdown ? "Context sections are available for reading." : "Fallback context only.",
    },
    {
      label: "Walkthrough",
      ready: Boolean(walkthroughMarkdown),
      detail: walkthroughMarkdown ? "A composed walkthrough is available." : "No walkthrough document yet.",
    },
    {
      label: "Transcript",
      ready: Boolean(transcriptText),
      detail: transcriptText ? "Transcript text is available." : "No transcript captured yet.",
    },
  ];

  const readyOutputs = deliverableChecks.filter((item) => item.ready).length;
  const pageTitle = subjectLine || selectedAsset?.filename || `Media File ${mediaId}`;
  const pageSubtitle = selectedAsset?.filename || selectedAsset?.path || "Review the stored outputs and technical trace for this processed media file.";

  return (
    <WorkspacePage
      eyebrow="Media Detail"
      title={pageTitle}
      subtitle={pageSubtitle}
      actions={
        <>
          <button onClick={() => navigate("/media")}>Back To Files</button>
          <button onClick={() => void fetchDetail()}>Refresh</button>
        </>
      }
      stats={[
        {
          label: "Status",
          value: overallStatus,
          meta: selectedJob ? jobPhaseLabel(selectedJob) : pipelineResult ? "Stored bundle available" : "No tracked job",
          tone: selectedJob?.status === "done" || (!selectedJob && pipelineResult) ? "success" : selectedJob?.status === "error" ? "warning" : "default",
        },
        {
          label: "Bundle",
          value: publicArtifactCount,
          meta: "subject, context, walkthrough, transcript",
        },
        {
          label: "Transcript",
          value: transcriptEmbedded ? "Embedded" : transcriptText || transcriptVttText ? "Ready" : "Missing",
          meta: transcriptSidecarLabel,
        },
      ]}
    >
      {error ? <div className="error-banner">{error}</div> : null}

      {loading ? (
        <WorkspaceEmpty title="Loading file detail" description="Fetching the pipeline result and stored outputs for this media file." />
      ) : !selectedAsset && !pipelineResult ? (
        <WorkspaceEmpty title="File not found" description="This media id is not present in the processed asset index." />
      ) : (
        <div className="workspace-stack">
          <WorkspacePanel
            title="Source file"
            description="Original file identity and media properties for this processed result."
          >
            <div className="media-source-head">
              <div>
                <div className="media-source-kicker">Processed file</div>
                <h3 className="inspector-title">{selectedAsset?.filename || mediaId}</h3>
                <p className="inspector-subtitle mono media-source-path" title={selectedAsset?.path || mediaId}>
                  {selectedAsset?.path || mediaId}
                </p>
              </div>
              <div className="workspace-chip-row">
                {selectedAsset?.modality ? <span className="workspace-chip">{selectedAsset.modality}</span> : null}
                <span
                  className={`workspace-chip ${
                    overallStatus === "Ready"
                      ? "workspace-chip--success"
                      : selectedJob?.status === "error"
                        ? "workspace-chip--warning"
                        : "workspace-chip--accent"
                  }`}
                >
                  {overallStatus}
                </span>
                {pipelineResult?.document?.format ? (
                  <span className="workspace-chip">{formatDocumentFormat(pipelineResult.document.format)}</span>
                ) : null}
                {processingActive ? (
                  <span className="workspace-chip workspace-chip--accent">processing</span>
                ) : null}
              </div>
            </div>

            <dl className="detail-list">
              <div>
                <dt>Media id</dt>
                <dd className="mono">{mediaId}</dd>
              </div>
              <div>
                <dt>Duration</dt>
                <dd>{selectedAsset?.duration_s ? formatDuration(selectedAsset.duration_s) : "Unknown"}</dd>
              </div>
              <div>
                <dt>Size</dt>
                <dd>{selectedAsset ? formatBytes(selectedAsset.file_size_bytes) : "Unknown"}</dd>
              </div>
              <div>
                <dt>Codec</dt>
                <dd>{selectedAsset?.codec || "Unknown"}</dd>
              </div>
              <div>
                <dt>Resolution</dt>
                <dd>{selectedAsset?.width && selectedAsset?.height ? `${selectedAsset.width} × ${selectedAsset.height}` : "Unknown"}</dd>
              </div>
              <div>
                <dt>Indexed</dt>
                <dd>{selectedAsset ? relativeTime(selectedAsset.indexed_at) : "Unknown"}</dd>
              </div>
            </dl>
          </WorkspacePanel>

          <div className="workspace-tabbar" role="tablist" aria-label="File detail views">
            {(["deliverables", "transcript", "technical"] as const).map((tab) => (
              <button
                key={tab}
                type="button"
                className={`workspace-tab ${activeTab === tab ? "active" : ""}`}
                onClick={() => setActiveTab(tab)}
              >
                {tab === "deliverables" ? "Outputs" : tab === "transcript" ? "Transcript" : "Technical"}
              </button>
            ))}
          </div>

          {activeTab === "deliverables" ? (
            <>
              <WorkspacePanel
                title="Subject"
                description="Single-sentence description generated from the processed outputs."
              >
                <div className="media-hero">
                  <span className="media-hero-eyebrow">Subject line</span>
                  <p className="media-hero-title">
                    {subjectLine || "No subject line generated for this file yet."}
                  </p>
                  <div className="workspace-chip-row">
                    {participants.length > 0 ? (
                      <span className="workspace-chip workspace-chip--accent">{participants.length} participants</span>
                    ) : null}
                    {themes.length > 0 ? <span className="workspace-chip">{themes.length} themes</span> : null}
                    {openLoopsCount > 0 ? (
                      <span className="workspace-chip workspace-chip--warning">{openLoopsCount} open questions</span>
                    ) : null}
                    {pipelineResult?.document?.format ? (
                      <span className="workspace-chip workspace-chip--success">
                        {formatDocumentFormat(pipelineResult.document.format)}
                      </span>
                    ) : null}
                  </div>
                </div>
              </WorkspacePanel>

              <WorkspacePanel
                title="Outputs"
                description="Clean stored outputs for this file. Open any card to read the full body."
              >
                <div className="media-output-list">
                  <article className="media-output-item">
                    <div className="media-output-header">
                      <div>
                        <h4 className="media-output-title">Context</h4>
                        <p className="media-output-subtitle">
                          Participants, themes, open questions, and higher-level interpretation for quick orientation.
                        </p>
                      </div>
                      <span className={`workspace-chip ${deliverableChecks[1]?.ready ? "workspace-chip--success" : "workspace-chip--warning"}`}>
                        {deliverableChecks[1]?.ready ? "ready" : "missing"}
                      </span>
                    </div>
                    <p className="record-row-preview">
                      {contextPreview || "No contextual summary text yet. The structured chips below are the fallback output for now."}
                    </p>
                    <div className="workspace-chip-row">
                      {participants.map((participant) => (
                        <span key={participant} className="workspace-chip">
                          {participant}
                        </span>
                      ))}
                      {themes.map((theme) => (
                        <span key={theme} className="workspace-chip">
                          {theme}
                        </span>
                      ))}
                      {openLoopsCount > 0 ? (
                        <span className="workspace-chip workspace-chip--warning">{openLoopsCount} open questions</span>
                      ) : null}
                      {summarySections.length > 0 ? (
                        <span className="workspace-chip">{summarySections.length} context sections</span>
                      ) : null}
                    </div>
                    {contextMarkdown ? (
                      <details className="media-output-details">
                        <summary>Open full context</summary>
                        <div className="media-markdown-shell media-markdown-shell--full">
                          <MarkdownMessage text={contextMarkdown} />
                        </div>
                      </details>
                    ) : null}
                  </article>

                  <article className="media-output-item">
                    <div className="media-output-header">
                      <div>
                        <h4 className="media-output-title">Walkthrough</h4>
                        <p className="media-output-subtitle">
                          The readable meeting-minutes or step-by-step document built from the internal timeline and recap trace.
                        </p>
                      </div>
                      <span className={`workspace-chip ${deliverableChecks[2]?.ready ? "workspace-chip--success" : "workspace-chip--warning"}`}>
                        {deliverableChecks[2]?.ready ? "ready" : "missing"}
                      </span>
                    </div>
                    <p className="record-row-preview">
                      {walkthroughPreview || "No walkthrough document has been composed for this file yet."}
                    </p>
                    <div className="workspace-chip-row">
                      {pipelineResult?.document?.format ? (
                        <span className="workspace-chip workspace-chip--success">
                          {formatDocumentFormat(pipelineResult.document.format)}
                        </span>
                      ) : null}
                      {sectionLabels.length > 0 ? <span className="workspace-chip">{sectionLabels.length} sections</span> : null}
                    </div>
                    {walkthroughMarkdown ? (
                      <details className="media-output-details">
                        <summary>Open full walkthrough</summary>
                        <div className="media-markdown-shell media-markdown-shell--full">
                          <MarkdownMessage text={walkthroughMarkdown} />
                        </div>
                      </details>
                    ) : null}
                  </article>

                  <article className="media-output-item">
                    <div className="media-output-header">
                      <div>
                        <h4 className="media-output-title">Readable transcript</h4>
                        <p className="media-output-subtitle">
                          Full spoken text in readable form, with the raw subtitle file available separately.
                        </p>
                      </div>
                      <span className={`workspace-chip ${deliverableChecks[3]?.ready ? "workspace-chip--success" : "workspace-chip--warning"}`}>
                        {deliverableChecks[3]?.ready ? "ready" : "missing"}
                      </span>
                    </div>
                    <p className="record-row-preview">
                      {transcriptPreview || "No transcript text is available for this file yet."}
                    </p>
                    <div className="workspace-chip-row">
                      <span className={`workspace-chip ${transcriptEmbedded ? "workspace-chip--success" : "workspace-chip--warning"}`}>
                        {transcriptEmbedded ? "Embedded in media" : "Not embedded in media"}
                      </span>
                      {transcriptSidecarPath ? <span className="workspace-chip mono">{transcriptSidecarLabel}</span> : null}
                    </div>
                    {(transcriptText || transcriptVttText) ? (
                      <div className="workspace-inline-actions">
                        <button className="tiny-button" onClick={() => setActiveTab("transcript")}>
                          Open transcript views
                        </button>
                      </div>
                    ) : null}
                  </article>

                  <article className="media-output-item">
                    <div className="media-output-header">
                      <div>
                        <h4 className="media-output-title">Subtitle file (.vtt)</h4>
                        <p className="media-output-subtitle">
                          The exact subtitle sidecar text written alongside the media file and embedded back into the container.
                        </p>
                      </div>
                      <span className={`workspace-chip ${transcriptVttText ? "workspace-chip--success" : "workspace-chip--warning"}`}>
                        {transcriptVttText ? "ready" : "missing"}
                      </span>
                    </div>
                    <p className="record-row-preview">
                      {transcriptVttPreview || "No .vtt subtitle text is available for this file yet."}
                    </p>
                    <div className="workspace-chip-row">
                      {transcriptSidecarPath ? <span className="workspace-chip mono">{transcriptSidecarLabel}</span> : null}
                    </div>
                    {transcriptVttText ? (
                      <details className="media-output-details">
                        <summary>Open full .vtt file</summary>
                        <pre className="detail-preview detail-preview--full">{transcriptVttText}</pre>
                      </details>
                    ) : null}
                  </article>
                </div>
              </WorkspacePanel>
            </>
          ) : activeTab === "transcript" ? (
            <div className="workspace-grid workspace-grid--two media-transcript-grid">
              <WorkspacePanel
                title="Readable transcript"
                description="Full transcript text for reading or spot-checking the generated output."
              >
                {transcriptText ? (
                  <div className="workspace-stack">
                    <div className="workspace-chip-row">
                      <span className={`workspace-chip ${transcriptEmbedded ? "workspace-chip--success" : "workspace-chip--warning"}`}>
                        {transcriptEmbedded ? "Embedded in media" : "Not embedded in media"}
                      </span>
                      {transcriptSidecarPath ? <span className="workspace-chip mono">{transcriptSidecarLabel}</span> : null}
                    </div>
                    <pre className="detail-preview detail-preview--full media-transcript-preview">{transcriptText}</pre>
                  </div>
                ) : (
                  <WorkspaceEmpty title="No readable transcript available" description="This file does not have transcript text yet." />
                )}
              </WorkspacePanel>

              <WorkspacePanel
                title="Subtitle file (.vtt)"
                description="Exact subtitle sidecar text, including cue timing and sequence formatting."
              >
                {transcriptVttText ? (
                  <div className="workspace-stack">
                    {transcriptSidecarPath ? (
                      <div className="workspace-chip-row">
                        <span className="workspace-chip mono">{transcriptSidecarLabel}</span>
                      </div>
                    ) : null}
                    <pre className="detail-preview detail-preview--full media-transcript-preview">{transcriptVttText}</pre>
                  </div>
                ) : (
                  <WorkspaceEmpty title="No .vtt transcript file available" description="This file does not have a stored subtitle sidecar yet." />
                )}
              </WorkspacePanel>
            </div>
          ) : (
            <>
              <WorkspacePanel
                title="Storage & embedding"
                description="How the clean outputs are stored back into the file, sidecars, and JSON bundle."
              >
                <div className="workspace-grid workspace-grid--two-narrow media-mini-grid">
                  <div className="media-deliverable-status-list">
                    <div className="media-deliverable-status-row">
                      <div>
                        <strong>Stored outputs</strong>
                        <p>Subject line, context memory, walkthrough document, and transcript are the user-facing outputs for this file.</p>
                      </div>
                      <span className="workspace-chip workspace-chip--success">{readyOutputs} ready</span>
                    </div>
                    <div className="media-deliverable-status-row">
                      <div>
                        <strong>Pipeline trace</strong>
                        <p>Speech segments, recaps, events, and keyframes are intermediate trace items used to produce those outputs.</p>
                      </div>
                      <span className="workspace-chip">{traceArtifactCount} trace items</span>
                    </div>
                  </div>

                  <div className="workspace-stack">
                    <div className="workspace-chip-row">
                      <span className={`workspace-chip ${transcriptEmbedded ? "workspace-chip--success" : "workspace-chip--warning"}`}>
                        {transcriptEmbedded ? "Transcript embedded" : "Transcript not embedded"}
                      </span>
                      <span className={`workspace-chip ${artifactBundleAttached ? "workspace-chip--success" : "workspace-chip--warning"}`}>
                        {artifactBundleAttached ? "JSON bundle attached" : "JSON bundle not attached"}
                      </span>
                      {transcriptSidecarPath ? <span className="workspace-chip mono">{transcriptSidecarLabel}</span> : null}
                    </div>
                    <div className="workspace-chip-row">
                      {artifactKinds.map((kind) => (
                        <span key={kind} className={`workspace-chip ${KIND_COLORS[kind] ?? ""}`}>
                          {humanizeLabel(kind)} · {artifactCounts.get(kind) ?? 0}
                        </span>
                      ))}
                    </div>
                    {traceKindsForDisplay.length > 0 ? (
                      <div className="workspace-chip-row">
                        {traceKindsForDisplay.map((kind) => (
                          <span key={kind} className={`workspace-chip ${KIND_COLORS[kind] ?? ""}`}>
                            {humanizeLabel(kind)} · {traceCountsForDisplay.get(kind) ?? 0}
                          </span>
                        ))}
                      </div>
                    ) : null}
                  </div>
                </div>
              </WorkspacePanel>

              <WorkspacePanel
                title="Pipeline trace"
                description="Internal pipeline trace used to produce the clean outputs. Leave this closed unless you are debugging the pipeline itself."
                actions={
                  <button className="tiny-button" onClick={() => setShowRawArtifacts((value) => !value)}>
                    {showRawArtifacts ? "Hide trace" : "Show trace"}
                  </button>
                }
              >
                {showRawArtifacts ? (
                  <>
                    <div className="workspace-chip-row">
                      <button
                        type="button"
                        className={`workspace-chip button-reset ${artifactFilter === "all" ? "workspace-chip--accent" : ""}`}
                        onClick={() => setArtifactFilter("all")}
                      >
                        All · {traceArtifactCount}
                      </button>
                      {traceArtifactKinds.map((kind) => (
                        <button
                          key={kind}
                          type="button"
                          className={`workspace-chip button-reset ${artifactFilter === kind ? "workspace-chip--accent" : KIND_COLORS[kind] ?? ""}`}
                          onClick={() => setArtifactFilter(kind)}
                        >
                          {humanizeLabel(kind)} · {traceArtifactCounts.get(kind) ?? 0}
                        </button>
                      ))}
                    </div>

                    {traceLoading ? (
                      <WorkspaceEmpty title="Loading raw trace" description="Fetching the low-level pipeline evidence for troubleshooting." />
                    ) : filteredArtifacts.length === 0 ? (
                      <WorkspaceEmpty title="No raw items in this filter" description="Choose a different filter to inspect the technical trace." />
                    ) : (
                      <div className="workspace-grid workspace-grid--two-narrow">
                        <div className="record-list compact" role="list" aria-label="Raw trace list">
                          {filteredArtifacts.map((artifact) => (
                            <button
                              key={artifact.artifact_id}
                              type="button"
                              className={`record-row ${selectedArtifactId === artifact.artifact_id ? "active" : ""}`}
                              onClick={() => setSelectedArtifactId(artifact.artifact_id)}
                            >
                              <div className="record-row-head">
                                <div className="record-row-title-group">
                                  <strong className="record-row-title">{humanizeLabel(artifact.kind)}</strong>
                                  <span className="workspace-chip">{formatRange(artifact.start_s, artifact.end_s)}</span>
                                </div>
                                <span className="record-row-meta">
                                  {artifact.confidence > 0 && artifact.confidence < 1 ? `${Math.round(artifact.confidence * 100)}%` : ""}
                                </span>
                              </div>
                              <span className="record-row-preview">{clip(artifact.content, 140) || "No raw trace content."}</span>
                            </button>
                          ))}
                        </div>

                        <div className="inspector-panel nested">
                          {selectedArtifact ? (
                            <>
                              <div className="inspector-header">
                                <div>
                                  <h3 className="inspector-title">{humanizeLabel(selectedArtifact.kind)}</h3>
                                  <p className="inspector-subtitle">{formatRange(selectedArtifact.start_s, selectedArtifact.end_s)}</p>
                                </div>
                                <span className="workspace-chip">{selectedArtifact.artifact_id}</span>
                              </div>
                              {Object.keys(selectedArtifact.metadata ?? {}).length > 0 ? (
                                <div className="workspace-chip-row">
                                  {Object.entries(selectedArtifact.metadata).map(([key, value]) => (
                                    <span key={key} className="workspace-chip">
                                      {key} · {summarizeValue(value)}
                                    </span>
                                  ))}
                                </div>
                              ) : null}
                              <pre className="detail-preview">{selectedArtifact.content || "No raw trace content."}</pre>
                              {selectedArtifact.source_refs.length > 0 ? (
                                <div className="workspace-stack">
                                  <h3 className="subpanel-title">Source refs</h3>
                                  <div className="workspace-chip-row">
                                    {selectedArtifact.source_refs.map((sourceRef) => (
                                      <span key={sourceRef} className="workspace-chip mono">
                                        {sourceRef}
                                      </span>
                                    ))}
                                  </div>
                                </div>
                              ) : null}
                            </>
                          ) : (
                            <WorkspaceEmpty title="No raw item selected" description="Click a raw trace row to inspect it here." />
                          )}
                        </div>
                      </div>
                    )}
                  </>
                ) : (
                  <p className="inspector-copy">
                    Keep this closed for normal review. The Outputs tab is the clean view; this section is only for troubleshooting how the pipeline built those results.
                  </p>
                )}
              </WorkspacePanel>
            </>
          )}
        </div>
      )}
    </WorkspacePage>
  );
}
