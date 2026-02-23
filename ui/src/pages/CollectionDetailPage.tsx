import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import SearchAdvanced from "../components/SearchAdvanced";
import { dropCollection, getCollection, insertText, searchCollection } from "../lib/api";
import type { CollectionDetail, SearchAdvancedOptions, SearchResult } from "../types";

export default function CollectionDetailPage() {
  const params = useParams();
  const name = params.name ?? "";

  const [detail, setDetail] = useState<CollectionDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const [searchOptions, setSearchOptions] = useState<SearchAdvancedOptions>({
    mode: "hybrid",
    limit: 10,
    unique: false,
    path: "",
    metric_type: "L2",
    nprobe: 16,
    hybrid_fusion: "weighted",
    hybrid_dense_weight: 0.65,
    hybrid_sparse_weight: 0.35,
    hybrid_rrf_k: 60
  });
  const [query, setQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResult[] | null>(null);
  const [searching, setSearching] = useState(false);

  const [insertValue, setInsertValue] = useState("");
  const [inserting, setInserting] = useState(false);

  async function refresh() {
    setLoading(true);
    try {
      const payload = await getCollection(name);
      setDetail(payload);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch collection.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, [name]);

  async function runSearch() {
    if (!query.trim()) return;
    setSearching(true);
    try {
      const payload = await searchCollection(name, { query, ...searchOptions });
      setSearchResults(payload.results ?? []);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed.");
    } finally {
      setSearching(false);
    }
  }

  async function runInsert() {
    const text = insertValue.trim();
    if (!text) return;
    setInserting(true);
    try {
      await insertText(name, { text, chunk_size: 1000, overlap: 0 });
      setInsertValue("");
      await refresh();
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Insert failed.");
    } finally {
      setInserting(false);
    }
  }

  async function runDrop() {
    if (!confirm(`Drop collection "${name}"? This cannot be undone.`)) return;
    try {
      await dropCollection(name);
      window.location.href = "/";
    } catch (err) {
      setError(err instanceof Error ? err.message : "Drop failed.");
    }
  }

  const fieldsSummary = useMemo(() => {
    if (!detail) return "";
    const names = detail.fields.map((f) => f.name);
    return names.join(", ");
  }, [detail]);

  return (
    <section style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      {error && <div className="error-banner">{error}</div>}
      <div className="panel">
        <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
          <div>
            <div className="muted">
              <Link to="/">← Back</Link>
            </div>
            <h2 style={{ margin: "6px 0 6px" }}>
              <span className="mono">{name}</span>
            </h2>
            {loading ? (
              <div className="muted">Loading…</div>
            ) : detail ? (
              <div className="muted">
                {detail.num_entities} rows · fields: {fieldsSummary || "—"}
              </div>
            ) : (
              <div className="muted">Not found.</div>
            )}
          </div>
          <div style={{ display: "flex", gap: 8, alignItems: "start" }}>
            <button onClick={() => void refresh()} disabled={loading}>
              Refresh
            </button>
            <button onClick={() => void runDrop()} disabled={loading} style={{ borderColor: "#7b3041" }}>
              Drop
            </button>
          </div>
        </div>
      </div>

      <div className="panel">
        <h3 style={{ marginTop: 0 }}>Search</h3>
        <div className="toolbar" style={{ marginBottom: 12 }}>
          <div className="segmented">
            {(["dense", "bm25", "hybrid"] as const).map((m) => (
              <button key={m} className={searchOptions.mode === m ? "active" : ""} onClick={() => setSearchOptions({ ...searchOptions, mode: m })}>
                {m.toUpperCase()}
              </button>
            ))}
          </div>
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Query…"
            onKeyDown={(event) => {
              if (event.key === "Enter") void runSearch();
            }}
          />
          <input
            style={{ width: 120 }}
            value={String(searchOptions.limit)}
            onChange={(event) => setSearchOptions({ ...searchOptions, limit: Number(event.target.value) || 10 })}
            placeholder="Limit"
          />
          <button disabled={searching} onClick={() => void runSearch()}>
            {searching ? "Searching…" : "Search"}
          </button>
        </div>
        <SearchAdvanced value={searchOptions} onChange={setSearchOptions} />

        {searchResults && (
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            <div className="muted">{searchResults.length} results</div>
            {searchResults.map((r) => (
              <div key={String(r.id)} className="card">
                <div className="card-headline">
                  <h3 className="mono" title={String(r.id)}>
                    #{r.id}
                  </h3>
                  <span className="pill">
                    <span className="status-dot warning" />
                    <span>{Number.isFinite(r.distance) ? r.distance.toFixed(4) : "—"}</span>
                  </span>
                </div>
                <div className="muted mono" style={{ fontSize: "0.84rem" }}>
                  {r.creation_date ?? ""}
                </div>
                <pre className="terminal">{(r.text ?? "").trim() || "—"}</pre>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="panel">
        <h3 style={{ marginTop: 0 }}>Insert text</h3>
        <div style={{ display: "grid", gap: 10 }}>
          <textarea
            value={insertValue}
            onChange={(event) => setInsertValue(event.target.value)}
            placeholder="Paste text to store in this collection…"
          />
          <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
            <button disabled={inserting} onClick={() => void runInsert()}>
              {inserting ? "Inserting…" : "Insert"}
            </button>
            <span className="muted">Uses default embedding settings unless you add options later.</span>
          </div>
        </div>
      </div>
    </section>
  );
}

