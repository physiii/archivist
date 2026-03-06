import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import SearchAdvanced from "../components/SearchAdvanced";
import { globalSearchCollections, listCollections } from "../lib/api";
import type { CollectionCard, SearchAdvancedOptions, SearchResult } from "../types";

function getResultPath(result: SearchResult): string {
  return String(result.path || result.source_id || "").trim();
}

export default function CollectionsPage() {
  const [collections, setCollections] = useState<CollectionCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [globalResults, setGlobalResults] = useState<SearchResult[] | null>(null);
  const [globalTotalCandidates, setGlobalTotalCandidates] = useState<number | null>(null);
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

  async function refresh() {
    try {
      const payload = await listCollections(true);
      setCollections(payload.collections ?? []);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch collections.");
    } finally {
      setLoading(false);
    }
  }

  async function runGlobalSearch() {
    if (!query.trim()) return;
    setSearching(true);
    try {
      const payload = await globalSearchCollections({
        query,
        ...searchOptions,
        path: "",
        per_collection_limit: Math.max(searchOptions.limit, 20)
      });
      setGlobalResults(payload.results ?? []);
      setGlobalTotalCandidates(payload.total_candidates ?? null);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Global search failed.");
    } finally {
      setSearching(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  return (
    <section>
      {error && <div className="error-banner">{error}</div>}
      <div className="toolbar">
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search across all collections…"
          onKeyDown={(event) => {
            if (event.key === "Enter") void runGlobalSearch();
          }}
        />
        <div className="segmented">
          {(["dense", "bm25", "hybrid"] as const).map((m) => (
            <button key={m} className={searchOptions.mode === m ? "active" : ""} onClick={() => setSearchOptions({ ...searchOptions, mode: m })}>
              {m.toUpperCase()}
            </button>
          ))}
        </div>
        <input
          style={{ width: 110 }}
          type="number"
          min={1}
          value={searchOptions.limit}
          onChange={(event) => setSearchOptions({ ...searchOptions, limit: Number(event.target.value) || 20 })}
          placeholder="Limit"
        />
        <button onClick={() => void runGlobalSearch()} disabled={searching}>
          {searching ? "Searching…" : "Search"}
        </button>
        <button onClick={() => void refresh()}>Reload Collections</button>
      </div>
      <SearchAdvanced value={searchOptions} onChange={setSearchOptions} />

      {globalResults && (
        <div className="panel" style={{ marginBottom: 14 }}>
          <div className="card-headline">
            <h3 style={{ margin: 0 }}>Global search results</h3>
            <span className="muted">
              {globalResults.length}
              {typeof globalTotalCandidates === "number" ? ` / ${globalTotalCandidates}` : ""} rows
            </span>
          </div>
          <div style={{ marginTop: 10, display: "flex", flexDirection: "column", gap: 10 }}>
            {globalResults.map((r) => {
              const resultPath = getResultPath(r);
              return (
                <div key={`${r.collection ?? "unknown"}:${String(r.id)}:${r.distance}`} className="card">
                  <div className="card-headline">
                    <h3 className="mono" title={String(r.id)}>
                      #{r.id}
                    </h3>
                    <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                      <span className="pill">{r.collection ?? "unknown"}</span>
                      <span className="pill">
                        <span className="status-dot warning" />
                        <span>{Number.isFinite(r.distance) ? r.distance.toFixed(4) : "—"}</span>
                      </span>
                    </div>
                  </div>
                  <div className="muted mono" style={{ fontSize: "0.84rem" }}>
                    {r.creation_date ? `Indexed ${r.creation_date}` : ""}
                  </div>
                  {resultPath && (
                    <div className="muted mono" style={{ fontSize: "0.84rem" }} title={resultPath}>
                      {resultPath}
                    </div>
                  )}
                  <pre className="terminal">{(r.text ?? "").trim() || "—"}</pre>
                  <div>
                    <Link className="button-link" to={`/collections/${encodeURIComponent(r.collection ?? "")}`}>
                      Open Collection
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {loading ? (
        <div className="muted">Loading collections…</div>
      ) : (
        <div className="grid">
          {collections.map((col) => (
            <div key={col.raw_name} className="card">
              <div className="card-headline">
                <h3 title={col.raw_name}>
                  <span className="mono">{col.name}</span>
                </h3>
                <span className="pill" title={col.raw_name}>
                  <span className="status-dot success" />
                  <span>{typeof col.num_entities === "number" ? `${col.num_entities} rows` : "—"}</span>
                </span>
              </div>
              <div className="muted">
                {col.vector_dim ? `dim ${col.vector_dim}` : "dim unknown"} · {col.has_sparse ? "hybrid-ready" : "dense-only"}
              </div>
              {col.stats_error && <div className="muted">Stats error: {col.stats_error}</div>}
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                <Link className="button-link" to={`/collections/${encodeURIComponent(col.name)}`}>
                  Open
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

