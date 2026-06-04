import { useCallback, useEffect, useState } from "react";

import MarkdownMessage from "../components/MarkdownMessage";
import { WorkspacePage, WorkspacePanel } from "../components/Workspace";

type PriorityItem = {
  num: string;
  title: string;
  owner: string;
  status: string;
  next_action: string;
  detail_md: string;
};

type PersonItem = {
  name: string;
  focus: string;
  this_week: string[];
};

type TableRow = Record<string, string>;

type FocusSection = {
  id: string;
  title: string;
  kind: "priority_table" | "table" | "list" | "people";
  columns?: string[];
  items: PriorityItem[] | PersonItem[] | TableRow[] | string[];
};

type FocusLane = {
  id: string;
  title: string;
  subtitle?: string;
  available: boolean;
  sourceLabel?: string;
  sourcePath?: string | null;
  sourceWarning?: string | null;
  generatedAt?: string | null;
  sections: FocusSection[];
  weekTitle?: string;
};

type FocusSyncSchedule = {
  enabled: boolean;
  time_of_day: string;
  timezone?: string;
  next_run_at?: string | null;
  last_triggered_at?: string | null;
};

type FocusSyncState = {
  running: boolean;
  message?: string;
  startedAt?: string | null;
  finishedAt?: string | null;
  lastSuccessfulAt?: string | null;
  error?: string | null;
  stale: boolean;
  schedule: FocusSyncSchedule;
};

type FocusOverview = {
  available: boolean;
  generatedAt?: string;
  lanes: FocusLane[];
  sync: FocusSyncState;
};

function columnLabel(col: string): string {
  return col.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatTimestamp(value?: string | null): string {
  if (!value) return "Unknown";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "Unknown";
  return parsed.toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function formatShortDate(value?: string | null): string {
  if (!value) return "Unknown";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "Unknown";
  return parsed.toLocaleDateString([], {
    month: "short",
    day: "numeric",
  });
}

function sectionItemCount(section: FocusSection): number {
  return Array.isArray(section.items) ? section.items.length : 0;
}

function defaultCollapsedSectionIds(lanes: FocusLane[]): Set<string> {
  const defaults = new Set<string>();
  for (const lane of lanes) {
    for (const section of lane.sections) {
      const key = `${lane.id}:${section.id}`;
      if (lane.id === "work" && ["open_questions", "product_ideas", "github"].includes(section.id)) {
        defaults.add(key);
      }
      if (lane.id === "personal" && section.id === "watchlist") {
        defaults.add(key);
      }
    }
  }
  return defaults;
}

function laneTabMeta(lane: FocusLane, sync: FocusSyncState): string {
  if (!lane.available) return "Waiting";
  if (lane.id === "personal") {
    if (sync.running) return "Refreshing";
    if (sync.stale) return "Needs refresh";
  }
  return lane.generatedAt ? `Updated ${formatShortDate(lane.generatedAt)}` : `${lane.sections.length} sections`;
}

function PrioritySection({
  laneId,
  items,
  expanded,
  toggle,
}: {
  laneId: string;
  items: PriorityItem[];
  expanded: Set<string>;
  toggle: (id: string) => void;
}) {
  return (
    <div className="focus-rows">
      {items.map((p) => {
        const key = `${laneId}-p-${p.num}`;
        const open = expanded.has(key);
        const hasDetail = !!(p.detail_md || p.next_action);
        return (
          <div key={key} className={`focus-row ${open ? "is-open" : ""} ${hasDetail ? "is-clickable" : ""}`}>
            <div
              className="focus-row-head"
              onClick={hasDetail ? () => toggle(key) : undefined}
              role={hasDetail ? "button" : undefined}
              tabIndex={hasDetail ? 0 : undefined}
              onKeyDown={hasDetail ? (e) => {
                if (e.key === "Enter" || e.key === " ") toggle(key);
              } : undefined}
            >
              <span className="focus-row-num">{p.num}</span>
              <div className="focus-row-copy">
                <div className="focus-row-title-line">
                  <span className="focus-row-title">{p.title}</span>
                  {p.owner ? <span className="focus-row-owner">{p.owner}</span> : null}
                </div>
                {p.status ? <span className="focus-row-summary">{p.status}</span> : null}
              </div>
              {hasDetail ? <span className="focus-row-chevron">{open ? "\u25B4" : "\u25BE"}</span> : null}
            </div>
            {open ? (
              <div className="focus-row-detail">
                {p.next_action ? (
                  <p className="focus-next-action">
                    <strong>Next:</strong> {p.next_action}
                  </p>
                ) : null}
                {p.detail_md ? <MarkdownMessage text={p.detail_md} /> : null}
              </div>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}

function TableSection({ items, columns }: { items: TableRow[]; columns?: string[] }) {
  const cols = columns ?? (items.length > 0 ? Object.keys(items[0]) : []);
  if (!cols.length) return null;
  return (
    <div className="focus-table-wrap">
      <table className="focus-table">
        <thead>
          <tr>{cols.map((c) => <th key={c}>{columnLabel(c)}</th>)}</tr>
        </thead>
        <tbody>
          {items.map((row, i) => (
            <tr key={i}>
              {cols.map((c) => (
                <td key={c} data-label={columnLabel(c)}>{row[c] ?? ""}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ListSection({ items }: { items: string[] }) {
  return (
    <ul className="focus-list">
      {items.map((item, i) => <li key={i}>{item}</li>)}
    </ul>
  );
}

function PeopleSection({
  laneId,
  items,
  expanded,
  toggle,
}: {
  laneId: string;
  items: PersonItem[];
  expanded: Set<string>;
  toggle: (id: string) => void;
}) {
  return (
    <div className="focus-rows">
      {items.map((p) => {
        const key = `${laneId}-dr-${p.name}`;
        const open = expanded.has(key);
        const hasDetail = p.this_week.length > 0;
        return (
          <div key={key} className={`focus-row ${open ? "is-open" : ""} ${hasDetail ? "is-clickable" : ""}`}>
            <div
              className="focus-row-head"
              onClick={hasDetail ? () => toggle(key) : undefined}
              role={hasDetail ? "button" : undefined}
              tabIndex={hasDetail ? 0 : undefined}
              onKeyDown={hasDetail ? (e) => {
                if (e.key === "Enter" || e.key === " ") toggle(key);
              } : undefined}
            >
              <span className="focus-row-num focus-row-num--person">{p.name.slice(0, 1)}</span>
              <div className="focus-row-copy">
                <div className="focus-row-title-line">
                  <span className="focus-row-title">{p.name}</span>
                </div>
                {p.focus ? <span className="focus-row-summary">{p.focus}</span> : null}
              </div>
              {hasDetail ? <span className="focus-row-chevron">{open ? "\u25B4" : "\u25BE"}</span> : null}
            </div>
            {open ? (
              <div className="focus-row-detail">
                <ul className="focus-this-week">
                  {p.this_week.map((item, i) => <li key={i}>{item}</li>)}
                </ul>
              </div>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}

function FocusLaneSection({
  lane,
  section,
  expanded,
  toggle,
  collapsedSections,
  toggleSection,
}: {
  lane: FocusLane;
  section: FocusSection;
  expanded: Set<string>;
  toggle: (id: string) => void;
  collapsedSections: Set<string>;
  toggleSection: (id: string) => void;
}) {
  const collapseKey = `${lane.id}:${section.id}`;
  const isCollapsed = collapsedSections.has(collapseKey);
  const itemCount = sectionItemCount(section);
  return (
    <section className="focus-lane-section">
      <div className="focus-lane-section-head">
        <div className="focus-lane-section-title-group">
          <h3 className="focus-lane-section-title">{section.title}</h3>
          {itemCount > 0 ? <span className="focus-lane-section-count">{itemCount} item{itemCount === 1 ? "" : "s"}</span> : null}
        </div>
        <button
          className="focus-collapse-btn"
          onClick={() => toggleSection(collapseKey)}
          title={isCollapsed ? "Expand section" : "Collapse section"}
        >
          {isCollapsed ? "\u25B6" : "\u25BC"}
        </button>
      </div>
      {!isCollapsed ? (
        <>
          {section.kind === "priority_table" ? (
            <PrioritySection
              laneId={lane.id}
              items={section.items as PriorityItem[]}
              expanded={expanded}
              toggle={toggle}
            />
          ) : null}
          {section.kind === "table" ? (
            <TableSection
              items={section.items as TableRow[]}
              columns={section.columns}
            />
          ) : null}
          {section.kind === "list" ? (
            <ListSection items={section.items as string[]} />
          ) : null}
          {section.kind === "people" ? (
            <PeopleSection
              laneId={lane.id}
              items={section.items as PersonItem[]}
              expanded={expanded}
              toggle={toggle}
            />
          ) : null}
        </>
      ) : null}
    </section>
  );
}

function FocusLanePanel({
  lane,
  expanded,
  toggle,
  collapsedSections,
  toggleSection,
}: {
  lane: FocusLane;
  expanded: Set<string>;
  toggle: (id: string) => void;
  collapsedSections: Set<string>;
  toggleSection: (id: string) => void;
}) {
  const descriptionBits = [lane.subtitle].filter(Boolean);
  const hasSections = lane.available && lane.sections.length > 0;
  return (
    <WorkspacePanel
      title={
        <div className="focus-lane-header">
          <div>
            <span className="focus-lane-title">{lane.title}</span>
            {lane.weekTitle ? <span className="focus-lane-week">{lane.weekTitle}</span> : null}
          </div>
          <span className={`focus-lane-pill ${lane.available ? "is-ready" : "is-empty"}`}>
            {lane.available ? "Live" : "Waiting"}
          </span>
        </div>
      }
      description={descriptionBits.join(" · ") || undefined}
      className={`focus-lane-panel focus-lane-panel--${lane.id}`}
    >
      {lane.sourceWarning ? <p className="focus-lane-warning">{lane.sourceWarning}</p> : null}
      {hasSections ? (
        <div className="focus-lane-sections">
          {lane.sections.map((section) => (
            <FocusLaneSection
              key={`${lane.id}:${section.id}`}
              lane={lane}
              section={section}
              expanded={expanded}
              toggle={toggle}
              collapsedSections={collapsedSections}
              toggleSection={toggleSection}
            />
          ))}
        </div>
      ) : (
        <div className="workspace-empty">
          <strong>No current focus items</strong>
          <p>No current evidence in this lane.</p>
        </div>
      )}
      <div className="focus-lane-meta">
        <span>{lane.generatedAt ? `Updated ${formatTimestamp(lane.generatedAt)}` : "No recent update yet"}</span>
        {lane.sourceLabel ? <span>{lane.sourceLabel}</span> : null}
        {lane.sourcePath ? <span className="focus-source-path">{lane.sourcePath}</span> : null}
      </div>
    </WorkspacePanel>
  );
}

export default function FocusPage() {
  const [overview, setOverview] = useState<FocusOverview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [collapsedSections, setCollapsedSections] = useState<Set<string>>(new Set());
  const [collapsedInitialized, setCollapsedInitialized] = useState(false);
  const [syncRequested, setSyncRequested] = useState(false);
  const [activeLaneId, setActiveLaneId] = useState("work");

  const toggle = useCallback((id: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);

  const toggleSection = useCallback((id: string) => {
    setCollapsedSections((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);

  const loadOverview = useCallback(async () => {
    try {
      const res = await fetch("/api/focus/overview", { cache: "no-store" });
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      const data = (await res.json()) as FocusOverview;
      setOverview(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load.");
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      if (cancelled) return;
      await loadOverview();
    }
    void load();
    const intervalMs = overview?.sync?.running ? 5000 : 30000;
    const interval = window.setInterval(() => {
      void load();
    }, intervalMs);
    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, [loadOverview, overview?.sync?.running]);

  useEffect(() => {
    if (!overview || collapsedInitialized) return;
    setCollapsedSections(defaultCollapsedSectionIds(overview.lanes));
    setCollapsedInitialized(true);
  }, [overview, collapsedInitialized]);

  useEffect(() => {
    if (!overview?.lanes.length) return;
    if (!overview.lanes.some((lane) => lane.id === activeLaneId)) {
      setActiveLaneId(overview.lanes[0].id);
    }
  }, [overview, activeLaneId]);

  const handleSyncNow = useCallback(async () => {
    setSyncRequested(true);
    try {
      const res = await fetch("/api/focus/sync", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ force: true, reason: "manual" }),
      });
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      await loadOverview();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to sync focus.");
    } finally {
      setSyncRequested(false);
    }
  }, [loadOverview]);

  if (!overview) {
    return (
      <WorkspacePage title="Focus" subtitle={error ?? "Loading focus lanes..."}>
        <WorkspacePanel title="Loading">
          <p>Loading focus lanes...</p>
        </WorkspacePanel>
      </WorkspacePage>
    );
  }

  const orderedLanes = [...overview.lanes].sort((a, b) => {
    const rank = (lane: FocusLane) => (lane.id === "work" ? 0 : lane.id === "personal" ? 1 : 2);
    return rank(a) - rank(b);
  });
  const activeLane = orderedLanes.find((lane) => lane.id === activeLaneId) ?? orderedLanes[0] ?? null;
  const sync = overview.sync;
  const headerAction = activeLane?.id === "personal" ? (
    <button
      className="focus-sync-btn"
      onClick={() => void handleSyncNow()}
      disabled={sync.running || syncRequested}
    >
      {sync.running || syncRequested ? "Refreshing..." : "Refresh personal"}
    </button>
  ) : null;

  return (
    <WorkspacePage
      title="Focus"
      subtitle="Current business and personal priorities."
      actions={headerAction}
    >
      {!overview.available ? (
        <WorkspacePanel title="Getting started">
          <p>No usable business or personal evidence yet.</p>
        </WorkspacePanel>
      ) : (
        <>
        <div className="focus-lane-tabs" role="tablist" aria-label="Focus lanes">
          {orderedLanes.map((lane) => (
            <button
              key={lane.id}
              className={`focus-lane-tab ${lane.id === activeLane?.id ? "is-active" : ""}`}
              type="button"
              role="tab"
              aria-selected={lane.id === activeLane?.id}
              onClick={() => setActiveLaneId(lane.id)}
            >
              <span className="focus-lane-tab-title">{lane.title}</span>
              <span className="focus-lane-tab-meta">
                {laneTabMeta(lane, sync)}
              </span>
            </button>
          ))}
        </div>
        {activeLane ? (
          <div className="focus-lane-tab-panel" role="tabpanel">
            <FocusLanePanel
              lane={activeLane}
              expanded={expanded}
              toggle={toggle}
              collapsedSections={collapsedSections}
              toggleSection={toggleSection}
            />
          </div>
        ) : null}
        </>
      )}
    </WorkspacePage>
  );
}
