import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";

import SearchAdvanced from "../components/SearchAdvanced";
import Embeddings3D from "../components/Embeddings3D";
import { getCollectionDetail, getEmbeddingsPreview, searchCollection } from "../lib/api";
import { parseStoredTags } from "../lib/tags";
import type {
  CollectionDetail,
  EmbeddingsPreviewPoint,
  EmbeddingsPreviewResponse,
  SearchAdvancedOptions,
  SearchResult
} from "../types";

function getResultPath(result: SearchResult): string {
  return String(result.path || result.source_id || "").trim();
}

export default function CollectionDetailPage() {
  const { name = "" } = useParams();
  const [detail, setDetail] = useState<CollectionDetail | null>(null);
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [previewPoints, setPreviewPoints] = useState<EmbeddingsPreviewPoint[]>([]);
  const [previewQueryPoint, setPreviewQueryPoint] = useState<{ vector: number[]; label: string; text?: string; distance?: number } | null>(null);
  const [previewMeta, setPreviewMeta] = useState<EmbeddingsPreviewResponse["meta"] | null>(null);
  const [selectedPointId, setSelectedPointId] = useState<string | number | null>(null);
  const [selectedResult, setSelectedResult] = useState<SearchResult | null>(null);
  const [previewQueryError, setPreviewQueryError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [previewLimit, setPreviewLimit] = useState(1200);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [working, setWorking] = useState(false);
  const metaRequestSeqRef = useRef(0);
  const previewRequestSeqRef = useRef(0);
  const [searchOptions, setSearchOptions] = useState<SearchAdvancedOptions>({
    mode: "hybrid",
    limit: 20,
    unique: false,
    path: "",
    nprobe: 16,
    hybrid_fusion: "weighted",
    hybrid_dense_weight: 0.65,
    hybrid_sparse_weight: 0.35,
    hybrid_rrf_k: 60
  });
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
        query: (activeQuery ?? query).trim() || undefined
      });
      if (requestSeq !== previewRequestSeqRef.current) return;
      setPreviewPoints(payload.points ?? []);
      setPreviewQueryPoint(payload.query_point ?? null);
      setPreviewMeta(payload.meta ?? null);
      setSelectedPointId(null);
      setSelectedResult(null);
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
        path: ""
      });
      // Backend already sorts according to mode/metric semantics.
      // Re-sorting here can invert hybrid ranking and confuse distance coloring.
      setSearchResults(payload.results ?? []);
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

  return (
    <section>
      {error && <div className="error-banner">{error}</div>}
      <div className="panel">
        <div className="card-headline">
          <h2>Collection: {decodeURIComponent(name)}</h2>
          <Link className="button-link" to="/collections">
            Back to Collections
          </Link>
        </div>
        {loading ? (
          <p className="muted">Loading collection details…</p>
        ) : detail ? (
          <p className="muted">
            Raw: <span className="mono">{detail.raw_name}</span> · Entities: {detail.num_entities}
          </p>
        ) : (
          <p className="muted">Collection metadata unavailable.</p>
        )}
      </div>

      <div className="search-composer">
        <textarea
          className="search-composer-input"
          rows={4}
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder={`Search in ${decodeURIComponent(name)}…`}
          onKeyDown={(event) => {
            if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
              event.preventDefault();
              void runSearch();
            }
          }}
        />
        <div className="search-composer-actions">
          <span className="muted">Press Ctrl/Cmd+Enter to search</span>
          <button disabled={working} onClick={() => void runSearch()}>
            {working ? "Searching…" : "Search"}
          </button>
        </div>
      </div>
      <SearchAdvanced value={searchOptions} onChange={setSearchOptions} />

      <div className="panel">
        <div className="card-headline">
          <h3>Embeddings 3D</h3>
          <div className="inline-actions">
            <input
              style={{ width: 90 }}
              type="number"
              min={50}
              max={10000}
              value={previewLimit}
              onChange={(event) => setPreviewLimit(Number(event.target.value) || 1200)}
            />
            <button onClick={() => void loadPreview(query.trim())} disabled={previewLoading}>
              {previewLoading ? "Refreshing…" : "Refresh Preview"}
            </button>
          </div>
        </div>
        {previewQueryError && <p className="muted">Query note: {previewQueryError}</p>}
        {!previewLoading && previewPoints.length === 0 ? (
          <p className="muted">No preview points returned.</p>
        ) : (
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
              setSelectedResult(null);
            }}
            loading={previewLoading}
          />
        )}
      </div>

      <div className="panel">
        <h3>Collection Search Results</h3>
        {searchResults.length === 0 ? (
          <p className="muted">Run a search to inspect rows in this collection.</p>
        ) : (
          <div className="run-list">
            {searchResults.map((result) => {
              const resultPath = getResultPath(result);
              return (
                <div
                  key={`${String(result.id)}:${result.distance}`}
                  className={`snapshot-row clickable ${String(selectedPointId ?? "") === String(result.id) ? "active" : ""}`}
                  onClick={() => {
                    setSelectedPointId(result.id);
                    setSelectedResult(result);
                  }}
                >
                  <div className="card-headline">
                    <span className="mono">#{String(result.id)}</span>
                    <span className="pill">{Number.isFinite(result.distance) ? result.distance.toFixed(4) : "—"}</span>
                  </div>
                  <p className="muted">{result.creation_date ? `Indexed ${result.creation_date}` : ""}</p>
                  {resultPath && (
                    <p className="muted mono" style={{ fontSize: "0.84rem", marginTop: -4 }} title={resultPath}>
                      {resultPath}
                    </p>
                  )}
                  {parseStoredTags(result.tags).length > 0 && (
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 10 }}>
                      {parseStoredTags(result.tags).map((tag) => (
                        <span key={`${String(result.id)}:${tag}`} className="pill">
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                  <pre className="terminal">{(result.text ?? "").trim() || "—"}</pre>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </section>
  );
}
