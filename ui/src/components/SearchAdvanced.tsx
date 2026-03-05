import type { SearchAdvancedOptions } from "../types";

type Props = {
  value: SearchAdvancedOptions;
  onChange: (next: SearchAdvancedOptions) => void;
};

export default function SearchAdvanced({ value, onChange }: Props) {
  const metric = (value.metric_type ?? "L2").toUpperCase();
  const thresholdSupported = metric === "L2" || metric === "COSINE";
  return (
    <details className="advanced-panel">
      <summary>Advanced</summary>
      <div className="advanced-grid">
        <label>
          <span className="muted">Path filter</span>
          <input
            value={value.path ?? ""}
            onChange={(event) => onChange({ ...value, path: event.target.value })}
            placeholder="/path/to/file.txt"
          />
        </label>
        <label>
          <span className="muted">Metric</span>
          <select
            value={(value.metric_type ?? "L2").toUpperCase()}
            onChange={(event) => onChange({ ...value, metric_type: event.target.value })}
          >
            <option value="L2">L2</option>
            <option value="IP">IP</option>
            <option value="COSINE">COSINE</option>
          </select>
        </label>
        <label>
          <span className="muted">nprobe</span>
          <input
            type="number"
            min={1}
            value={value.nprobe ?? 16}
            onChange={(event) => onChange({ ...value, nprobe: Number(event.target.value) || 16 })}
          />
        </label>
        <label>
          <span className="muted">Max distance threshold</span>
          <input
            aria-label="Search max distance threshold"
            type="number"
            step="0.01"
            value={value.max_distance ?? ""}
            placeholder="Optional"
            disabled={!thresholdSupported}
            onChange={(event) => {
              const raw = event.target.value.trim();
              if (!raw) {
                const { max_distance: _, ...rest } = value;
                onChange(rest);
                return;
              }
              const parsed = Number(raw);
              onChange({ ...value, max_distance: Number.isFinite(parsed) ? parsed : undefined });
            }}
          />
          <span className="muted" style={{ fontSize: "0.8rem" }}>
            Sphere visualization supports L2/COSINE. Backend filtering applies on dense vector search.
          </span>
        </label>
        <label>
          <span className="muted">Hybrid fusion</span>
          <select
            value={value.hybrid_fusion ?? "weighted"}
            onChange={(event) =>
              onChange({
                ...value,
                hybrid_fusion: event.target.value as "weighted" | "rrf"
              })
            }
          >
            <option value="weighted">weighted</option>
            <option value="rrf">rrf</option>
          </select>
        </label>
        <label>
          <span className="muted">Dense weight</span>
          <input
            type="number"
            min={0}
            max={1}
            step="0.05"
            value={value.hybrid_dense_weight ?? 0.65}
            onChange={(event) => onChange({ ...value, hybrid_dense_weight: Number(event.target.value) || 0.65 })}
          />
        </label>
        <label>
          <span className="muted">Sparse weight</span>
          <input
            type="number"
            min={0}
            max={1}
            step="0.05"
            value={value.hybrid_sparse_weight ?? 0.35}
            onChange={(event) => onChange({ ...value, hybrid_sparse_weight: Number(event.target.value) || 0.35 })}
          />
        </label>
        <label>
          <span className="muted">RRF k</span>
          <input
            type="number"
            min={1}
            value={value.hybrid_rrf_k ?? 60}
            onChange={(event) => onChange({ ...value, hybrid_rrf_k: Number(event.target.value) || 60 })}
          />
        </label>
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={value.unique}
            onChange={(event) => onChange({ ...value, unique: event.target.checked })}
          />
          <span>Unique (dedupe by hash)</span>
        </label>
      </div>
    </details>
  );
}

