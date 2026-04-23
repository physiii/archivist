import { Suspense, lazy, useEffect, useMemo, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";

import SearchAdvanced from "../components/SearchAdvanced";
import { WorkspaceEmpty, WorkspacePage, WorkspacePanel } from "../components/Workspace";
import { getCollectionDetail, getEmbeddingsPreview, searchCollection } from "../lib/api";
import { parseStoredTags } from "../lib/tags";
import type {
  CollectionDetail,
  EmbeddingsPreviewPoint,
  EmbeddingsPreviewResponse,
  SearchAdvancedOptions,
  SearchResult,
} from "../types";

const Embeddings3D = lazy(() => import("../components/Embeddings3D"));

const DEFAULT_OPTIONS: SearchAdvancedOptions = {
  mode: "hybrid",
  limit: 20,
  unique: false,
  path: "",
  nprobe: 16,
  hybrid_fusion: "weighted",
  hybrid_dense_weight: 0.65,
  hybrid_sparse_weight: 0.35,
  hybrid_rrf_k: 60,
};

function getResultPath(result: SearchResult): string {
  return String(result.path || result.source_id || "").trim();
}

function resultKey(result: SearchResult): string {
  return `${String(result.id)}:${result.distance}`;
}

function formatDistance(distance: number) {
  return Number.isFinite(distance) ? distance.toFixed(4) : "—";
}

export default function CollectionDetailPage() {
  const { name = "" } = useParams();
  const decodedName = decodeURIComponent(name);
  const [detail, setDetail] = useState<CollectionDetail | null>(null);
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [previewPoints, setPreviewPoints] = useState<EmbeddingsPreviewPoint[]>([]);
  const [previewQueryPoint, setPreviewQueryPoint] = useState<{ vector: number[]; label: string; text?: string; distance?: number } | null>(null);
  const [previewMeta, setPreviewMeta] = useState<EmbeddingsPreviewResponse["meta"] | null>(null);
  const [selectedPointId, setSelectedPointId] = useState<string | number | null>(null);
  const [selectedResultKey, setSelectedResultKey] = useState<string | null>(null);
  const [previewQueryError, setPreviewQueryError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [previewLimit, setPreviewLimit] = useState(1200);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [working, setWorking] = useState(false);
  const metaRequestSeqRef = useRef(0);
  const previewRequestSeqRef = useRef(0);
  const [searchOptions, setSearchOptions] = useState<SearchAdvancedOptions>(DEFAULT_OPTIONS);

  async function refreshMeta() {
    const requestSeq = ++metaRequestSeqRef.current;
    try {
      const payload = await getCollectionDetail(name);
      if (requestSeq !== metaRequestSeqRef.current) return;
      setDetail(payload);
      setError(null);
    } catch (err) {
      if (requestSeq !== metaRequestSeqRef.current) return;
      setError(err instanceof Error ? err.message : "Failed to load collection.");
    } finally {
      if (requestSeq !== metaRequestSeqRef.current) return;
      setLoading(false);
    }
  }

  async function loadPreview(activeQuery?: string) {
    const requestSeq = ++previewRequestSeqRef.current;
    setPreviewLoading(true);
    try {
      const payload = await getEmbeddingsPreview(name, {
        limit: Math.max(50, Math.min(previewLimit, 10000)),
        query: (activeQuery ?? query).trim() || undefined,
      });
      if (requestSeq !== previewRequestSeqRef.current) return;
      setPreviewPoints(payload.points ?? []);
      setPreviewQueryPoint(payload.query_point ?? null);
      setPreviewMeta(payload.meta ?? null);
      setSelectedPointId(null);
      setPreviewQueryError(payload.query_error ?? null);
      setError(null);
    } catch (err) {
      if (requestSeq !== previewRequestSeqRef.current) return;
      setError(err instanceof Error ? err.message : "Failed to load embeddings preview.");
    } finally {
      if (requestSeq !== previewRequestSeqRef.current) return;
      setPreviewLoading(false);
    }
  }

  async function runSearch() {
    if (!query.trim()) return;
    setWorking(true);
    try {
      const payload = await searchCollection(name, {
        query: query.trim(),
        ...searchOptions,
        path: "",
      });
      const nextResults = payload.results ?? [];
      setSearchResults(nextResults);
      setSelectedResultKey(nextResults[0] ? resultKey(nextResults[0]) : null);
      await loadPreview(query.trim());
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Collection search failed.");
    } finally {
      setWorking(false);
    }
  }

  useEffect(() => {
    void refreshMeta();
    void loadPreview();
  }, [name]);

  const selectedResult = useMemo(
    () => searchResults.find((result) => resultKey(result) === selectedResultKey) ?? null,
    [searchResults, selectedResultKey],
  );

  return (
    <WorkspacePage
      eyebrow="Collection Detail"
      title={decodedName}
      subtitle="Work inside a single collection with result inspection and a live embeddings preview tied to the same query context."
      actions={
        <Link className="button-link" to="/collections">
          Back to collections
        </Link>
      }
      stats={[
        { label: "Entities", value: detail?.num_entities?.toLocaleString() ?? "—", meta: loading ? "Loading…" : "Indexed rows" },
        { label: "Fields", value: detail?.fields.length ?? "—", meta: "Schema columns" },
        { label: "Preview points", value: previewPoints.length.toLocaleString(), meta: previewLoading ? "Refreshing…" : previewMeta?.projection_method ?? "Projection" },
      ]}
    >
      {error ? <div className="error-banner">{error}</div> : null}

      <WorkspacePanel
        title="Search inside this collection"
        description="Use the same search controls as the global view, then keep the chosen result pinned while you inspect the embedding space."
      >
        <div className="search-composer">
          <textarea
            className="search-composer-input"
            rows={4}
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder={`Search in ${decodedName}`}
            onKeyDown={(event) => {
              if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
                event.preventDefault();
                void runSearch();
              }
            }}
          />
          <div className="search-composer-actions">
            <span className="muted">Press Ctrl/Cmd+Enter to search</span>
            <button disabled={working || !query.trim()} onClick={() => void runSearch()}>
              {working ? "Searching…" : "Search"}
            </button>
          </div>
        </div>
        <SearchAdvanced value={searchOptions} onChange={setSearchOptions} />
      </WorkspacePanel>

      <div className="workspace-grid workspace-grid--two">
        <WorkspacePanel
          title="Search results"
          description="The result list is dense by design so you can move through a large response set without losing context."
        >
          {searchResults.length === 0 ? (
            <WorkspaceEmpty title="No results yet" description="Run a collection search to populate the result list." />
          ) : (
            <div className="record-list" role="list" aria-label="Collection search results">
              {searchResults.map((result) => (
                <button
                  key={resultKey(result)}
                  type="button"
                  className={`record-row ${selectedResultKey === resultKey(result) ? "active" : ""}`}
                  onClick={() => {
                    setSelectedResultKey(resultKey(result));
                    setSelectedPointId(result.id);
                  }}
                >
                  <div className="record-row-head">
                    <div className="record-row-title-group">
                      <strong className="record-row-title mono">#{String(result.id)}</strong>
                      <span className="workspace-chip">{formatDistance(result.distance)}</span>
                    </div>
                    {result.creation_date ? <span className="record-row-meta">{result.creation_date}</span> : null}
                  </div>
                  {getResultPath(result) ? (
                    <span className="record-row-subtitle mono" title={getResultPath(result)}>
                      {getResultPath(result)}
                    </span>
                  ) : null}
                  <span className="record-row-preview">{(result.text ?? "").trim() || "No text preview available."}</span>
                </button>
              ))}
            </div>
          )}
        </WorkspacePanel>

        <WorkspacePanel
          title="Result inspector"
          description="Selected rows stay expanded on the right with tags and source metadata."
        >
          {selectedResult ? (
            <>
              <dl className="detail-list">
                <div>
                  <dt>Row id</dt>
                  <dd className="mono">#{String(selectedResult.id)}</dd>
                </div>
                <div>
                  <dt>Distance</dt>
                  <dd>{formatDistance(selectedResult.distance)}</dd>
                </div>
                <div>
                  <dt>Indexed</dt>
                  <dd>{selectedResult.creation_date || "Unknown"}</dd>
                </div>
                <div>
                  <dt>Path</dt>
                  <dd className="mono" title={getResultPath(selectedResult)}>
                    {getResultPath(selectedResult) || "Unavailable"}
                  </dd>
                </div>
              </dl>
              {parseStoredTags(selectedResult.tags).length > 0 ? (
                <div className="workspace-chip-row">
                  {parseStoredTags(selectedResult.tags).map((tag) => (
                    <span key={`${resultKey(selectedResult)}:${tag}`} className="workspace-chip">
                      {tag}
                    </span>
                  ))}
                </div>
              ) : null}
              <pre className="detail-preview">{(selectedResult.text ?? "").trim() || "No row text available."}</pre>
            </>
          ) : (
            <WorkspaceEmpty title="No result selected" description="Click any search result to keep it pinned in the inspector." />
          )}
        </WorkspacePanel>
      </div>

      <div className="workspace-grid workspace-grid--wide-aside">
        <WorkspacePanel
          title="Embeddings preview"
          description="Query context and row selection are kept in sync with the 3D projection so the chart becomes a navigation aid instead of decoration."
          actions={
            <div className="workspace-inline-actions">
              <input
                className="workspace-number-input"
                type="number"
                min={50}
                max={10000}
                value={previewLimit}
                onChange={(event) => setPreviewLimit(Number(event.target.value) || 1200)}
              />
              <button onClick={() => void loadPreview(query.trim())} disabled={previewLoading}>
                {previewLoading ? "Refreshing…" : "Refresh preview"}
              </button>
            </div>
          }
        >
          {previewQueryError ? <div className="inline-warning">Query note: {previewQueryError}</div> : null}
          <div className="workspace-chip-row">
            {previewMeta?.projection_method ? <span className="workspace-chip">{previewMeta.projection_method}</span> : null}
            {previewMeta?.metric_type ? <span className="workspace-chip">{previewMeta.metric_type}</span> : null}
            {previewQueryPoint ? <span className="workspace-chip workspace-chip--accent">Query point loaded</span> : null}
          </div>
          {!previewLoading && previewPoints.length === 0 ? (
            <WorkspaceEmpty title="No preview points returned" description="Adjust the preview limit or rerun the query." />
          ) : (
            <Suspense fallback={<p className="muted">Loading embeddings preview…</p>}>
              <Embeddings3D
                points={previewPoints}
                queryPoint={previewQueryPoint}
                axisLabels={previewMeta?.axis_labels}
                projectionMethod={previewMeta?.projection_method}
                selectedPointId={selectedPointId}
                externalSelection={
                  selectedResult
                    ? { id: selectedResult.id, text: selectedResult.text, distance: selectedResult.distance, tags: selectedResult.tags }
                    : null
                }
                onSelectPoint={(pointId) => {
                  setSelectedPointId(pointId);
                  const matchingResult = searchResults.find((result) => String(result.id) === String(pointId));
                  if (matchingResult) {
                    setSelectedResultKey(resultKey(matchingResult));
                  }
                }}
                loading={previewLoading}
              />
            </Suspense>
          )}
        </WorkspacePanel>

        <WorkspacePanel
          title="Collection schema"
          description="Metadata stays visible beside the preview so you can confirm what the collection actually contains."
        >
          {loading ? (
            <WorkspaceEmpty title="Loading schema" description="Waiting for collection metadata." />
          ) : detail ? (
            <>
              <dl className="detail-list">
                <div>
                  <dt>Raw name</dt>
                  <dd className="mono" title={detail.raw_name}>
                    {detail.raw_name}
                  </dd>
                </div>
                <div>
                  <dt>Rows</dt>
                  <dd>{detail.num_entities.toLocaleString()}</dd>
                </div>
                <div>
                  <dt>Fields</dt>
                  <dd>{detail.fields.length}</dd>
                </div>
              </dl>
              <div className="field-list">
                {detail.fields.map((field) => (
                  <div key={field.name} className="field-row">
                    <div>
                      <strong>{field.name}</strong>
                      <span className="record-row-subtitle">{field.dtype}</span>
                    </div>
                    <div className="workspace-chip-row">
                      {field.is_primary ? <span className="workspace-chip workspace-chip--accent">Primary</span> : null}
                      {field.auto_id ? <span className="workspace-chip">Auto ID</span> : null}
                    </div>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <WorkspaceEmpty title="Collection metadata unavailable" description="The schema endpoint did not return a payload." />
          )}
        </WorkspacePanel>
      </div>
    </WorkspacePage>
  );
}
