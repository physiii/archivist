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
        return nextCollections[0]?.name ?? null;
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
      setSelectedResultKey(nextResults[0] ? resultKey(nextResults[0]) : null);
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

  const selectedCollection = collections.find((collection) => collection.name === selectedCollectionName) ?? null;
  const selectedResult = globalResults?.find((result) => resultKey(result) === selectedResultKey) ?? null;

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
        description="Use the global query bar for fast triage, then inspect the selected hit in the side panel before drilling into the source collection."
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
          <div className="workspace-grid workspace-grid--two">
            <div className="workspace-stack">
              <div className="workspace-inline-meta">
                <span>{globalResults.length} visible matches</span>
                <span>{typeof globalTotalCandidates === "number" ? `${globalTotalCandidates} total candidates` : "Candidate count unavailable"}</span>
              </div>
              <div className="record-list" role="list" aria-label="Global search results">
                {globalResults.map((result) => {
                  const key = resultKey(result);
                  return (
                    <button
                      key={key}
                      type="button"
                      className={`record-row ${selectedResultKey === key ? "active" : ""}`}
                      onClick={() => setSelectedResultKey(key)}
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
                  );
                })}
              </div>
            </div>

            <div className="inspector-panel">
              {selectedResult ? (
                <>
                  <div className="inspector-header">
                    <div>
                      <h3 className="inspector-title">Selected match</h3>
                      <p className="inspector-subtitle">Inspect the row before opening the source collection.</p>
                    </div>
                    <Link className="button-link" to={`/collections/${encodeURIComponent(selectedResult.collection ?? "")}`}>
                      Open collection
                    </Link>
                  </div>
                  <dl className="detail-list">
                    <div>
                      <dt>Collection</dt>
                      <dd>{selectedResult.collection ?? "unknown"}</dd>
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
                  <pre className="detail-preview">{(selectedResult.text ?? "").trim() || "No text available."}</pre>
                </>
              ) : (
                <WorkspaceEmpty
                  title="No match selected"
                  description="Run a search, then click any result row to inspect the full context here."
                />
              )}
            </div>
          </div>
        ) : (
          <WorkspaceEmpty
            title="Search is ready"
            description="The result list and inspector appear here after you run a cross-collection query."
          />
        )}
      </WorkspacePanel>

      <div className="workspace-grid workspace-grid--two">
        <WorkspacePanel
          title="Collection catalog"
          description="Dense catalog rows keep the overview scannable even when the instance grows well beyond a handful of collections."
        >
          {loading ? (
            <WorkspaceEmpty title="Loading collections" description="Waiting for collection metadata." />
          ) : collections.length === 0 ? (
            <WorkspaceEmpty title="No collections found" description="Create or index a collection to populate the catalog." />
          ) : (
            <div className="record-list" role="list" aria-label="Collection catalog">
              {collections.map((collection) => (
                <button
                  key={collection.raw_name}
                  type="button"
                  className={`record-row ${selectedCollectionName === collection.name ? "active" : ""}`}
                  onClick={() => setSelectedCollectionName(collection.name)}
                >
                  <div className="record-row-head">
                    <div className="record-row-title-group">
                      <strong className="record-row-title mono">{collection.name}</strong>
                      <span className={`workspace-chip ${collection.has_sparse ? "workspace-chip--success" : ""}`}>
                        {collection.has_sparse ? "Hybrid" : "Dense"}
                      </span>
                    </div>
                    <span className="workspace-chip">{typeof collection.num_entities === "number" ? `${collection.num_entities} rows` : "—"}</span>
                  </div>
                  <span className="record-row-subtitle mono" title={collection.raw_name}>
                    {collection.raw_name}
                  </span>
                  <span className="record-row-preview">
                    {collection.vector_dim ? `Vector dim ${collection.vector_dim}` : "Vector dimension unavailable"}
                    {collection.stats_error ? ` · ${collection.stats_error}` : ""}
                  </span>
                </button>
              ))}
            </div>
          )}
        </WorkspacePanel>

        <WorkspacePanel
          title="Collection details"
          description="Selection details stay pinned on the right so you do not need to navigate away just to confirm basic metadata."
          actions={
            selectedCollection ? (
              <Link className="button-link" to={`/collections/${encodeURIComponent(selectedCollection.name)}`}>
                Open collection
              </Link>
            ) : null
          }
        >
          {selectedCollection ? (
            <>
              <dl className="detail-list">
                <div>
                  <dt>Name</dt>
                  <dd className="mono">{selectedCollection.name}</dd>
                </div>
                <div>
                  <dt>Raw name</dt>
                  <dd className="mono" title={selectedCollection.raw_name}>
                    {selectedCollection.raw_name}
                  </dd>
                </div>
                <div>
                  <dt>Rows</dt>
                  <dd>{selectedCollection.num_entities ?? "Unknown"}</dd>
                </div>
                <div>
                  <dt>Embedding</dt>
                  <dd>{selectedCollection.vector_dim ? `${selectedCollection.vector_dim} dimensions` : "Unavailable"}</dd>
                </div>
                <div>
                  <dt>Retrieval mode</dt>
                  <dd>{selectedCollection.has_sparse ? "Dense + sparse hybrid" : "Dense only"}</dd>
                </div>
              </dl>
              {selectedCollection.stats_error ? (
                <div className="inline-warning">Stats error: {selectedCollection.stats_error}</div>
              ) : (
                <p className="inspector-copy">
                  This collection is ready for inspection. Open it to search within a single source and view the embeddings preview alongside individual row details.
                </p>
              )}
            </>
          ) : (
            <WorkspaceEmpty title="No collection selected" description="Choose a collection row to inspect it here." />
          )}
        </WorkspacePanel>
      </div>
    </WorkspacePage>
  );
}
