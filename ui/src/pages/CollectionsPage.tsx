import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import SearchAdvanced from "../components/SearchAdvanced";
import { WorkspaceEmpty, WorkspacePage, WorkspacePanel } from "../components/Workspace";
import { globalSearchCollections, listCollections } from "../lib/api";
import { parseStoredTags } from "../lib/tags";
import type { CollectionCard, SearchAdvancedOptions, SearchResult } from "../types";

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
  return `${result.collection ?? "unknown"}:${String(result.id)}:${result.distance}`;
}

function formatDistance(distance: number) {
  return Number.isFinite(distance) ? distance.toFixed(4) : "—";
}

function ResultDetails({ result }: { result: SearchResult }) {
  const tags = parseStoredTags(result.tags);
  return (
    <div className="record-row-expanded">
      <div className="record-row-expanded-head">
        <dl className="detail-list detail-list--inline">
          <div>
            <dt>Row id</dt>
            <dd className="mono">#{String(result.id)}</dd>
          </div>
          <div>
            <dt>Collection</dt>
            <dd>{result.collection ?? "unknown"}</dd>
          </div>
          <div>
            <dt>Distance</dt>
            <dd>{formatDistance(result.distance)}</dd>
          </div>
          <div>
            <dt>Indexed</dt>
            <dd>{result.creation_date || "Unknown"}</dd>
          </div>
          <div>
            <dt>Path</dt>
            <dd className="mono" title={getResultPath(result)}>
              {getResultPath(result) || "Unavailable"}
            </dd>
          </div>
        </dl>
        {result.collection ? (
          <Link className="button-link" to={`/collections/${encodeURIComponent(result.collection)}`}>
            Open collection
          </Link>
        ) : null}
      </div>
      {tags.length > 0 ? (
        <div className="workspace-chip-row">
          {tags.map((tag) => (
            <span key={`${resultKey(result)}:${tag}`} className="workspace-chip">
              {tag}
            </span>
          ))}
        </div>
      ) : null}
      <pre className="detail-preview compact">{(result.text ?? "").trim() || "No text available."}</pre>
    </div>
  );
}

function CollectionInlineDetails({ collection }: { collection: CollectionCard }) {
  return (
    <div className="collection-row-expanded">
      <div className="collection-detail-strip">
        <div>
          <span className="collection-detail-label">Rows</span>
          <strong>{typeof collection.num_entities === "number" ? collection.num_entities.toLocaleString() : "Unknown"}</strong>
        </div>
        <div>
          <span className="collection-detail-label">Embedding</span>
          <strong>{collection.vector_dim ? `${collection.vector_dim} dims` : "Unavailable"}</strong>
        </div>
        <div>
          <span className="collection-detail-label">Retrieval</span>
          <strong>{collection.has_sparse ? "Hybrid" : "Dense"}</strong>
        </div>
        <div>
          <span className="collection-detail-label">Raw name</span>
          <strong className="mono" title={collection.raw_name}>{collection.raw_name}</strong>
        </div>
      </div>
      <div className="collection-detail-footer">
        {collection.stats_error ? (
          <span className="inline-warning">Stats error: {collection.stats_error}</span>
        ) : (
          <span className="collection-detail-note">Open the collection to search within this source and inspect row-level evidence.</span>
        )}
        <Link className="button-link collection-open-link" to={`/collections/${encodeURIComponent(collection.name)}`}>
          Open collection
        </Link>
      </div>
    </div>
  );
}

export default function CollectionsPage() {
  const [collections, setCollections] = useState<CollectionCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [globalResults, setGlobalResults] = useState<SearchResult[] | null>(null);
  const [globalTotalCandidates, setGlobalTotalCandidates] = useState<number | null>(null);
  const [selectedCollectionName, setSelectedCollectionName] = useState<string | null>(null);
  const [selectedResultKey, setSelectedResultKey] = useState<string | null>(null);
  const [searchOptions, setSearchOptions] = useState<SearchAdvancedOptions>(DEFAULT_OPTIONS);

  async function refresh(includeStats = false, surfaceErrors = true) {
    try {
      const payload = await listCollections(includeStats);
      const nextCollections = payload.collections ?? [];
      setCollections(nextCollections);
      setSelectedCollectionName((current) => {
        if (current && nextCollections.some((collection) => collection.name === current)) {
          return current;
        }
        return null;
      });
      if (surfaceErrors) {
        setError(null);
      }
    } catch (err) {
      if (surfaceErrors) {
        setError(err instanceof Error ? err.message : "Failed to fetch collections.");
      }
    } finally {
      setLoading(false);
    }
  }

  async function runGlobalSearch() {
    if (!query.trim()) return;
    setSearching(true);
    try {
      const payload = await globalSearchCollections({
        query: query.trim(),
        ...searchOptions,
        path: "",
        per_collection_limit: Math.max(searchOptions.limit, 20),
      });
      const nextResults = payload.results ?? [];
      setGlobalResults(nextResults);
      setGlobalTotalCandidates(payload.total_candidates ?? null);
      setSelectedResultKey(null);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Global search failed.");
    } finally {
      setSearching(false);
    }
  }

  useEffect(() => {
    let cancelled = false;
    void refresh(false);
    const idleHandle = window.setTimeout(() => {
      if (!cancelled) {
        void refresh(true, false);
      }
    }, 350);
    return () => {
      cancelled = true;
      window.clearTimeout(idleHandle);
    };
  }, []);

  const totalRows = useMemo(
    () => collections.reduce((sum, collection) => sum + (collection.num_entities ?? 0), 0),
    [collections],
  );
  const hybridReady = useMemo(
    () => collections.filter((collection) => collection.has_sparse).length,
    [collections],
  );

  return (
    <WorkspacePage
      eyebrow="Knowledge Workspace"
      title="Collections"
      subtitle="Browse indexed collections, run cross-collection search, and inspect the exact row behind each match without leaving the page."
      actions={
        <button onClick={() => void refresh(true)} disabled={loading}>
          Reload catalog
        </button>
      }
      stats={[
        { label: "Collections", value: collections.length, meta: loading ? "Loading…" : "Live catalog" },
        { label: "Indexed rows", value: totalRows.toLocaleString(), meta: "Across all collections", tone: "accent" },
        { label: "Hybrid ready", value: hybridReady, meta: `${Math.max(collections.length - hybridReady, 0)} dense-only`, tone: "success" },
      ]}
    >
      {error ? <div className="error-banner">{error}</div> : null}

      <WorkspacePanel
        title="Cross-collection search"
        description="Use the global query bar for fast triage. Click any result to expand the row in place."
      >
        <div className="workspace-search-shell">
          <div className="workspace-search-row">
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search across all collections"
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  void runGlobalSearch();
                }
              }}
            />
            <div className="segmented">
              {(["dense", "bm25", "hybrid"] as const).map((mode) => (
                <button
                  key={mode}
                  className={searchOptions.mode === mode ? "active" : ""}
                  onClick={() => setSearchOptions({ ...searchOptions, mode })}
                >
                  {mode.toUpperCase()}
                </button>
              ))}
            </div>
            <input
              className="workspace-number-input"
              type="number"
              min={1}
              value={searchOptions.limit}
              onChange={(event) => setSearchOptions({ ...searchOptions, limit: Number(event.target.value) || 20 })}
              placeholder="Limit"
            />
            <button onClick={() => void runGlobalSearch()} disabled={searching || !query.trim()}>
              {searching ? "Searching…" : "Search"}
            </button>
          </div>
          <SearchAdvanced value={searchOptions} onChange={setSearchOptions} />
        </div>

        {globalResults ? (
          <div className="workspace-stack">
            <div className="workspace-inline-meta">
              <span>{globalResults.length} visible matches</span>
              <span>{typeof globalTotalCandidates === "number" ? `${globalTotalCandidates} total candidates` : "Candidate count unavailable"}</span>
            </div>
            <div className="record-list" role="list" aria-label="Global search results">
              {globalResults.map((result) => {
                const key = resultKey(result);
                const isSelected = selectedResultKey === key;
                return (
                  <article key={key} className={`record-row ${isSelected ? "active" : ""}`}>
                    <button
                      type="button"
                      className="record-row-click"
                      onClick={() => setSelectedResultKey(isSelected ? null : key)}
                      aria-expanded={isSelected}
                    >
                      <div className="record-row-head">
                        <div className="record-row-title-group">
                          <strong className="record-row-title mono">#{result.id}</strong>
                          <span className="workspace-chip workspace-chip--accent">{result.collection ?? "unknown"}</span>
                        </div>
                        <span className="workspace-chip">{formatDistance(result.distance)}</span>
                      </div>
                      {getResultPath(result) ? (
                        <span className="record-row-subtitle mono" title={getResultPath(result)}>
                          {getResultPath(result)}
                        </span>
                      ) : null}
                      <span className="record-row-preview">{(result.text ?? "").trim() || "No text preview available."}</span>
                    </button>
                    {isSelected ? <ResultDetails result={result} /> : null}
                  </article>
                );
              })}
            </div>
          </div>
        ) : (
          <WorkspaceEmpty
            title="Search is ready"
            description="The result list appears here after you run a cross-collection query."
          />
        )}
      </WorkspacePanel>

      <WorkspacePanel
        title="Collection catalog"
        description="Click a collection to expand its metadata inline, then open it when you are ready to inspect rows."
      >
        {loading ? (
          <WorkspaceEmpty title="Loading collections" description="Waiting for collection metadata." />
        ) : collections.length === 0 ? (
          <WorkspaceEmpty title="No collections found" description="Create or index a collection to populate the catalog." />
        ) : (
          <div className="record-list collection-catalog-list" role="list" aria-label="Collection catalog">
            {collections.map((collection) => {
              const isSelected = selectedCollectionName === collection.name;
              return (
                <article
                  key={collection.raw_name}
                  className={`record-row collection-catalog-row ${isSelected ? "active" : ""}`}
                >
                  <button
                    type="button"
                    className="record-row-click collection-row-trigger"
                    onClick={() => setSelectedCollectionName(isSelected ? null : collection.name)}
                    aria-expanded={isSelected}
                  >
                    <div className="record-row-head">
                      <div className="record-row-title-group">
                        <strong className="record-row-title mono">{collection.name}</strong>
                        <span className={`workspace-chip ${collection.has_sparse ? "workspace-chip--success" : ""}`}>
                          {collection.has_sparse ? "Hybrid" : "Dense"}
                        </span>
                      </div>
                      <span className="workspace-chip">{typeof collection.num_entities === "number" ? `${collection.num_entities.toLocaleString()} rows` : "—"}</span>
                    </div>
                    <span className="record-row-subtitle mono" title={collection.raw_name}>
                      {collection.raw_name}
                    </span>
                    <span className="record-row-preview">
                      {collection.vector_dim ? `Vector dim ${collection.vector_dim}` : "Vector dimension unavailable"}
                      {collection.stats_error ? ` · ${collection.stats_error}` : ""}
                    </span>
                  </button>
                  {isSelected ? <CollectionInlineDetails collection={collection} /> : null}
                </article>
              );
            })}
          </div>
        )}
      </WorkspacePanel>
    </WorkspacePage>
  );
}
