import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import SearchAdvanced from "../components/SearchAdvanced";
import Embeddings3D from "../components/Embeddings3D";
import { getCollectionDetail, getEmbeddingsPreview, searchCollection } from "../lib/api";
import type { CollectionDetail, EmbeddingsPreviewPoint, SearchAdvancedOptions, SearchResult } from "../types";

export default function CollectionDetailPage() {
  const { name = "" } = useParams();
  const [detail, setDetail] = useState<CollectionDetail | null>(null);
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [previewPoints, setPreviewPoints] = useState<EmbeddingsPreviewPoint[]>([]);
  const [previewQueryPoint, setPreviewQueryPoint] = useState<{ vector: number[]; label: string; text?: string; distance?: number } | null>(null);
  const [selectedPointId, setSelectedPointId] = useState<string | number | null>(null);
  const [previewQueryError, setPreviewQueryError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [previewLimit, setPreviewLimit] = useState(300);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [working, setWorking] = useState(false);
  const [searchOptions, setSearchOptions] = useState<SearchAdvancedOptions>({
    mode: "hybrid",
    limit: 20,
    unique: false,
    path: "",
    metric_type: "COSINE",
    nprobe: 16,
    hybrid_fusion: "weighted",
    hybrid_dense_weight: 0.65,
    hybrid_sparse_weight: 0.35,
    hybrid_rrf_k: 60
  });

  async function refreshMeta() {
    try {
      const payload = await getCollectionDetail(name);
      setDetail(payload);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load collection.");
    } finally {
      setLoading(false);
    }
  }

  async function loadPreview(activeQuery?: string) {
    setPreviewLoading(true);
    try {
      const payload = await getEmbeddingsPreview(name, {
        limit: Math.max(50, Math.min(previewLimit, 10000)),
        query: (activeQuery ?? query).trim() || undefined,
        metric_type: searchOptions.metric_type
      });
      setPreviewPoints(payload.points ?? []);
      setPreviewQueryPoint(payload.query_point ?? null);
      setSelectedPointId(null);
      setPreviewQueryError(payload.query_error ?? null);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load embeddings preview.");
    } finally {
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

      <div className="toolbar">
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder={`Search in ${decodeURIComponent(name)}…`}
          onKeyDown={(event) => {
            if (event.key === "Enter") void runSearch();
          }}
        />
        <button disabled={working} onClick={() => void runSearch()}>
          {working ? "Searching…" : "Search"}
        </button>
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
              onChange={(event) => setPreviewLimit(Number(event.target.value) || 300)}
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
            selectedPointId={selectedPointId}
            onSelectPoint={(pointId) => setSelectedPointId(pointId)}
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
            {searchResults.map((result) => (
              <div
                key={`${String(result.id)}:${result.distance}`}
                className={`snapshot-row clickable ${String(selectedPointId ?? "") === String(result.id) ? "active" : ""}`}
                onClick={() => setSelectedPointId(result.id)}
              >
                <div className="card-headline">
                  <span className="mono">#{String(result.id)}</span>
                  <span className="pill">{Number.isFinite(result.distance) ? result.distance.toFixed(4) : "—"}</span>
                </div>
                <p className="muted">{result.creation_date ?? ""}</p>
                <pre className="terminal">{(result.text ?? "").trim() || "—"}</pre>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
