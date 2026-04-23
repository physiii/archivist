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
  context?: string;
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

type FocusEventCandidate = {
  title: string;
  whenLabel: string;
  detail?: string;
  sortTime: number | null;
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

function totalLaneItems(lane: FocusLane): number {
  return lane.sections.reduce((sum, section) => sum + sectionItemCount(section), 0);
}

function leadSectionPreview(lane: FocusLane): { label: string; title: string; detail: string } | null {
  const preferredSectionIds = lane.id === "work"
    ? ["manual_priorities", "current_business_signals", "priorities"]
    : ["manual_priorities", "priorities", "upcoming"];

  for (const sectionId of preferredSectionIds) {
    const section = lane.sections.find((item) => item.id === sectionId);
    if (!section) continue;
    if (section.kind === "priority_table") {
      const item = (section.items as PriorityItem[])[0];
      if (!item) continue;
      return {
        label: sectionId === "manual_priorities" ? "Manual layer" : sectionId === "priorities" ? "Top priority" : "Lead thread",
        title: item.title,
        detail: item.next_action || item.status || "Review the supporting evidence.",
      };
    }
    if (section.kind === "table") {
      const row = (section.items as TableRow[])[0];
      if (!row) continue;
      return {
        label: "Lead thread",
        title: row.event || row.title || row.blocker || row.idea || "Current item",
        detail: row.why || row.status || row.impact || "Review the current lane details.",
      };
    }
  }
  return null;
}

function parseClockTime(value?: string | null): { hours: number; minutes: number } | null {
  const raw = String(value ?? "").trim();
  if (!raw || raw === "-" || raw === "--" || raw === "—" || /^TBD$/i.test(raw)) return null;
  if (/^AM$/i.test(raw)) return { hours: 9, minutes: 0 };
  if (/^PM$/i.test(raw)) return { hours: 15, minutes: 0 };

  const meridiemMatch = raw.match(/^(\d{1,2})(?::(\d{2}))?\s*(AM|PM)$/i);
  if (meridiemMatch) {
    let hours = Number(meridiemMatch[1]) % 12;
    if (/PM/i.test(meridiemMatch[3])) hours += 12;
    return { hours, minutes: Number(meridiemMatch[2] ?? "0") };
  }

  const twentyFourHourMatch = raw.match(/^(\d{1,2}):(\d{2})$/);
  if (twentyFourHourMatch) {
    return { hours: Number(twentyFourHourMatch[1]), minutes: Number(twentyFourHourMatch[2]) };
  }

  return null;
}

function parseFocusEventMoment(value?: string | null, time?: string | null): Date | null {
  const raw = String(value ?? "").trim();
  if (!raw) return null;

  const now = new Date();
  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const clock = parseClockTime(time);

  const withClock = (date: Date) => new Date(
    date.getFullYear(),
    date.getMonth(),
    date.getDate(),
    clock?.hours ?? 12,
    clock?.minutes ?? 0,
    0,
    0,
  );

  if (/^\d{4}-\d{2}-\d{2}$/.test(raw)) {
    const [year, month, day] = raw.split("-").map(Number);
    return withClock(new Date(year, month - 1, day));
  }

  if (/^today\b/i.test(raw)) return withClock(startOfToday);
  if (/^tomorrow\b/i.test(raw)) return withClock(new Date(startOfToday.getFullYear(), startOfToday.getMonth(), startOfToday.getDate() + 1));

  const monthDayMatch = raw.match(/^(?:(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+)?([A-Za-z]{3,9})\s+(\d{1,2})(?:,?\s*(\d{4}))?(?:\s+.*)?$/);
  if (monthDayMatch) {
    const month = monthDayMatch[2];
    const day = Number(monthDayMatch[3]);
    const year = Number(monthDayMatch[4] ?? String(startOfToday.getFullYear()));
    const parsed = new Date(`${month} ${day}, ${year}`);
    if (!Number.isNaN(parsed.getTime())) return withClock(parsed);
  }

  const parsed = new Date(raw);
  if (!Number.isNaN(parsed.getTime())) return parsed;
  return null;
}

function laneEventCandidates(lane: FocusLane): FocusEventCandidate[] {
  const candidates: FocusEventCandidate[] = [];
  const pushCandidate = (title: string, whenLabel: string, detail?: string, time?: string) => {
    const cleanTitle = title.trim();
    if (!cleanTitle) return;
    const cleanWhen = whenLabel.trim();
    const parsed = parseFocusEventMoment(cleanWhen, time);
    candidates.push({
      title: cleanTitle,
      whenLabel: cleanWhen && time && cleanWhen !== time ? `${cleanWhen} - ${time}` : cleanWhen || time || "Scheduled",
      detail: detail?.trim(),
      sortTime: parsed ? parsed.getTime() : null,
    });
  };

  for (const section of lane.sections) {
    if (section.kind !== "table") continue;
    const rows = section.items as TableRow[];
    for (const row of rows) {
      if (section.id === "upcoming") {
        pushCandidate(row.event ?? "", row.when ?? "", row.why);
      } else if (section.id === "calendar") {
        pushCandidate(row.event ?? "", row.day ?? "", undefined, row.time);
      } else if (section.id === "recent_business_meetings") {
        pushCandidate(row.event ?? "", row.when ?? "", row.calendar);
      }
    }
  }

  return candidates;
}

function summarizeLaneEvents(lane: FocusLane): {
  nextEvent: FocusEventCandidate | null;
  latestPastEvent: FocusEventCandidate | null;
} {
  const candidates = laneEventCandidates(lane);
  const startOfToday = new Date();
  startOfToday.setHours(0, 0, 0, 0);

  const futureEvents = candidates
    .filter((candidate) => candidate.sortTime !== null && candidate.sortTime >= startOfToday.getTime())
    .sort((a, b) => (a.sortTime ?? Number.MAX_SAFE_INTEGER) - (b.sortTime ?? Number.MAX_SAFE_INTEGER));

  const pastEvents = candidates
    .filter((candidate) => candidate.sortTime !== null && candidate.sortTime < startOfToday.getTime())
    .sort((a, b) => (b.sortTime ?? 0) - (a.sortTime ?? 0));

  return {
    nextEvent: futureEvents[0] ?? null,
    latestPastEvent: pastEvents[0] ?? null,
  };
}

function laneStatusSummary(lane: FocusLane, sync: FocusSyncState): { value: string; meta: string; detail: string } {
  if (lane.id === "personal") {
    return {
      value: sync.running ? "Refreshing" : sync.stale ? "Needs refresh" : lane.available ? "Current" : "Waiting",
      meta: sync.lastSuccessfulAt ? `Last refresh ${formatTimestamp(sync.lastSuccessfulAt)}` : "No completed refresh yet",
      detail: lane.sourceLabel || "Personal lane is built from archive evidence.",
    };
  }

  return {
    value: lane.sourceWarning ? "Needs fresher notes" : lane.available ? "Live" : "Waiting",
    meta: lane.generatedAt ? `Updated ${formatTimestamp(lane.generatedAt)}` : "No recent business update",
    detail: lane.sourceWarning || lane.sourceLabel || "Business lane is built from notes and archive signals.",
  };
}

function laneTabMeta(lane: FocusLane, sync: FocusSyncState): string {
  if (!lane.available) return "Waiting";
  if (lane.id === "personal") {
    if (sync.running) return "Refreshing";
    if (sync.stale) return "Needs refresh";
  }
  return lane.generatedAt ? `Updated ${formatShortDate(lane.generatedAt)}` : `${lane.sections.length} sections`;
}

function laneComposerPlaceholder(laneId: string): string {
  if (laneId === "personal") {
    return "Move travel prep to the top, drop anything already handled, and add Jonas pickup time plus the bank paperwork.";
  }
  return "Move the launch review to the top, remove stale follow-ups, and add the highest-risk business thread that needs attention today.";
}

function FocusManualComposer({
  lane,
  draft,
  pending,
  error,
  onDraftChange,
  onSubmit,
}: {
  lane: FocusLane;
  draft: string;
  pending: boolean;
  error: string | null;
  onDraftChange: (value: string) => void;
  onSubmit: () => void;
}) {
  const helperCopy = lane.id === "personal"
    ? "Use this to add, remove, reorder, or talk through your personal priorities. Archivist will revise the manual layer in this lane and keep it alongside the rest of your context."
    : "Use this to add, remove, reorder, or talk through business priorities. Archivist will revise the manual layer in this lane alongside notes and archive signals.";

  return (
    <section className="focus-manual-composer">
      <div className="focus-manual-header">
        <div>
          <span className="focus-manual-label">Discuss Priorities</span>
          <p className="focus-manual-copy">{helperCopy}</p>
        </div>
        <button
          type="button"
          className="focus-sync-btn"
          onClick={onSubmit}
          disabled={pending || !draft.trim()}
        >
          {pending ? "Updating..." : "Update priorities"}
        </button>
      </div>
      <textarea
        className="focus-manual-input"
        value={draft}
        placeholder={laneComposerPlaceholder(lane.id)}
        onChange={(event) => onDraftChange(event.target.value)}
        onKeyDown={(event) => {
          if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
            event.preventDefault();
            if (!pending && draft.trim()) onSubmit();
          }
        }}
      />
      {error ? <p className="focus-manual-error">{error}</p> : null}
    </section>
  );
}

function FocusLaneSummary({ lane, sync }: { lane: FocusLane; sync: FocusSyncState }) {
  const { nextEvent, latestPastEvent } = summarizeLaneEvents(lane);
  const status = laneStatusSummary(lane, sync);
  const lead = leadSectionPreview(lane);
  const itemCount = totalLaneItems(lane);
  const sectionPreview = lane.sections
    .slice(0, 3)
    .map((section) => section.title)
    .join(", ");

  return (
    <div className="focus-lane-summary-grid">
      <article className="focus-summary-card focus-summary-card--primary">
        <span className="focus-summary-label">Next event</span>
        <strong className="focus-summary-value">
          {nextEvent ? nextEvent.title : "No future event in this lane"}
        </strong>
        <span className="focus-summary-meta">
          {nextEvent
            ? nextEvent.whenLabel
            : latestPastEvent
              ? `Most recent: ${latestPastEvent.whenLabel}`
              : lane.generatedAt
                ? `Snapshot updated ${formatTimestamp(lane.generatedAt)}`
                : "Awaiting dated events"}
        </span>
        <p className="focus-summary-detail">
          {nextEvent
            ? (nextEvent.detail || "This is the next scheduled item in the selected lane.")
            : lane.id === "work"
              ? "The current business snapshot does not contain a future meeting or calendar item yet."
              : "The current personal snapshot does not contain a future scheduled item yet."}
        </p>
      </article>

      <article className="focus-summary-card">
        <span className="focus-summary-label">{lead?.label ?? "Lead thread"}</span>
        <strong className="focus-summary-value">
          {lead?.title ?? "No active thread yet"}
        </strong>
        <span className="focus-summary-meta">
          {lead ? "What is most immediate in this lane." : "This lane has not populated a lead item yet."}
        </span>
        <p className="focus-summary-detail">
          {lead?.detail ?? "Refresh the lane or wait for more evidence to surface."}
        </p>
      </article>

      <article className="focus-summary-card">
        <span className="focus-summary-label">Lane status</span>
        <strong className="focus-summary-value">{status.value}</strong>
        <span className="focus-summary-meta">{status.meta}</span>
        <p className="focus-summary-detail">{status.detail}</p>
      </article>

      <article className="focus-summary-card">
        <span className="focus-summary-label">In view</span>
        <strong className="focus-summary-value">
          {lane.sections.length} section{lane.sections.length === 1 ? "" : "s"}
        </strong>
        <span className="focus-summary-meta">
          {itemCount} visible item{itemCount === 1 ? "" : "s"}
        </span>
        <p className="focus-summary-detail">
          {sectionPreview ? `Includes ${sectionPreview}.` : "This lane has not populated section details yet."}
        </p>
      </article>
    </div>
  );
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
  sync,
  manualDraft,
  manualPending,
  manualError,
  onManualDraftChange,
  onSubmitManual,
  expanded,
  toggle,
  collapsedSections,
  toggleSection,
}: {
  lane: FocusLane;
  sync: FocusSyncState;
  manualDraft: string;
  manualPending: boolean;
  manualError: string | null;
  onManualDraftChange: (value: string) => void;
  onSubmitManual: () => void;
  expanded: Set<string>;
  toggle: (id: string) => void;
  collapsedSections: Set<string>;
  toggleSection: (id: string) => void;
}) {
  const descriptionBits = [lane.subtitle].filter(Boolean);
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
      <div className="focus-lane-meta">
        <span>{lane.generatedAt ? `Updated ${formatTimestamp(lane.generatedAt)}` : "No recent update yet"}</span>
        {lane.sourceLabel ? <span>{lane.sourceLabel}</span> : null}
        {lane.sourcePath ? <span className="focus-source-path">{lane.sourcePath}</span> : null}
      </div>
      <FocusManualComposer
        lane={lane}
        draft={manualDraft}
        pending={manualPending}
        error={manualError}
        onDraftChange={onManualDraftChange}
        onSubmit={onSubmitManual}
      />
      <FocusLaneSummary lane={lane} sync={sync} />
      {lane.sourceWarning ? <p className="focus-lane-warning">{lane.sourceWarning}</p> : null}
      {lane.context ? <p className="focus-lane-context">{lane.context}</p> : null}
      {lane.available && lane.sections.length > 0 ? (
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
          <strong>No focus items yet</strong>
          <p>This lane will populate as Archivist refreshes its sources.</p>
        </div>
      )}
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
  const [manualDrafts, setManualDrafts] = useState<Record<string, string>>({ work: "", personal: "" });
  const [manualPendingLaneId, setManualPendingLaneId] = useState<string | null>(null);
  const [manualError, setManualError] = useState<string | null>(null);

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

  useEffect(() => {
    setManualError(null);
  }, [activeLaneId]);

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

  const handleManualPrioritySubmit = useCallback(async (laneId: string) => {
    const text = String(manualDrafts[laneId] ?? "").trim();
    if (!text) return;
    setManualPendingLaneId(laneId);
    setManualError(null);
    try {
      const res = await fetch("/api/focus/manual-priorities", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ laneId, text }),
      });
      const payload = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(typeof payload?.error === "string" ? payload.error : `${res.status} ${res.statusText}`);
      }
      setManualDrafts((prev) => ({ ...prev, [laneId]: "" }));
      await loadOverview();
    } catch (err) {
      setManualError(err instanceof Error ? err.message : "Failed to update manual priorities.");
    } finally {
      setManualPendingLaneId(null);
    }
  }, [loadOverview, manualDrafts]);

  if (!overview) {
    return (
      <WorkspacePage title="Focus" subtitle={error ?? "Loading focus lanes..."}>
        <WorkspacePanel title="Loading">
          <p>Splitting business and personal focus...</p>
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
  const activeDraft = activeLane ? manualDrafts[activeLane.id] ?? "" : "";
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
      subtitle="Business and personal priorities, kept current from notes and archive activity."
      actions={headerAction}
    >
      {!overview.available ? (
        <WorkspacePanel title="Getting started">
          <p>Archivist has not found usable business notes or enough personal archive evidence yet.</p>
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
              sync={sync}
              manualDraft={activeDraft}
              manualPending={manualPendingLaneId === activeLane.id}
              manualError={manualError}
              onManualDraftChange={(value) => setManualDrafts((prev) => ({ ...prev, [activeLane.id]: value }))}
              onSubmitManual={() => void handleManualPrioritySubmit(activeLane.id)}
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
