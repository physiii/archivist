import type { SearchAdvancedOptions } from "../types";

type Props = {
  value: SearchAdvancedOptions;
  onChange: (next: SearchAdvancedOptions) => void;
};

export default function SearchAdvanced({ value, onChange }: Props) {
  return (
    <details className="advanced-panel">
      <summary>Advanced</summary>
      <div className="advanced-grid">
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
      <p className="muted" style={{ marginTop: 10 }}>
        Dense search uses the collection&apos;s configured vector metric automatically.
      </p>
    </details>
  );
}

