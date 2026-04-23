import { useCallback, useEffect, useMemo, useRef, useState, type ChangeEvent, type CSSProperties, type WheelEvent as ReactWheelEvent } from "react";

import { WorkspaceEmpty, WorkspacePage, WorkspacePanel } from "../components/Workspace";
import type { JournalOverviewDay, JournalOverviewResponse, JournalOverviewSource } from "../types";

/* ── Constants ─────────────────────────────────────────────────────── */

type JournalSourceFilter = "all" | string;
type TimelineMetric = "overall" | "activity" | "importance" | "intensity" | "excitement" | "wonder" | "sadness" | "friction" | "connection" | "momentum";
type TimelineStyle = CSSProperties & {
  "--timeline-color": string;
};
type SpectrumBandStyle = CSSProperties & {
  "--band-height": string;
  "--band-color": string;
};
type SpectrumMetricStyle = CSSProperties & {
  "--metric-color": string;
  "--metric-fill": string;
};

const SOURCE_COLORS: Record<string, string> = {
  calendar: "#5b8cff",
  email: "#f2b36d",
  drive: "#7cc7ff",
  chat: "#f8a86a",
  git: "#43d389",
  media: "#c084fc",
  github: "#f0f0f0",
};

const WEEKDAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const EARLIEST_JOURNAL_YEAR = 1990;
const JOURNAL_CACHE_PREFIX = "archivist:journal:v5:";
const journalMonthCache = new Map<string, JournalOverviewResponse>();
const journalMonthInflight = new Map<string, Promise<JournalOverviewResponse>>();
const TIMELINE_METRIC_LABELS: Record<TimelineMetric, string> = {
  overall: "Overall",
  activity: "Activity",
  importance: "Importance",
  intensity: "Intensity",
  excitement: "Excitement",
  wonder: "Wonder",
  sadness: "Sadness",
  friction: "Friction",
  connection: "Connection",
  momentum: "Momentum",
};
const TIMELINE_METRIC_COLORS: Record<TimelineMetric, string> = {
  overall: "#8fb2ff",
  activity: "#57d5ff",
  importance: "#f3c969",
  intensity: "#ff8a65",
  excitement: "#66d9e8",
  wonder: "#c084fc",
  sadness: "#7895cb",
  friction: "#f08a9d",
  connection: "#7bd88f",
  momentum: "#43d389",
};

type FullscreenHost = HTMLDivElement & {
  webkitRequestFullscreen?: () => Promise<void> | void;
};

type FullscreenDocument = Document & {
  webkitExitFullscreen?: () => Promise<void> | void;
  webkitFullscreenElement?: Element | null;
};

/* ── Date helpers ──────────────────────────────────────────────────── */

const longDateFmt = new Intl.DateTimeFormat(undefined, { weekday: "long", month: "long", day: "numeric", year: "numeric" });
const shortDateFmt = new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric" });
const monthNameFmt = new Intl.DateTimeFormat(undefined, { month: "long" });
const monthTitleFmt = new Intl.DateTimeFormat(undefined, { month: "long", year: "numeric" });

function journalDate(date: string) { return new Date(`${date}T12:00:00`); }

function dateKey(date: Date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}

function shiftDate(date: Date, days: number) {
  const d = new Date(date);
  d.setDate(d.getDate() + days);
  return d;
}

function startOfMonth(date: Date) { return new Date(date.getFullYear(), date.getMonth(), 1, 12); }
function endOfMonth(date: Date) { return new Date(date.getFullYear(), date.getMonth() + 1, 0, 12); }
function mondayColumn(date: Date) { return (date.getDay() + 6) % 7; }

function shiftMonth(date: Date, delta: number) {
  return new Date(date.getFullYear(), date.getMonth() + delta, 1, 12);
}

function monthParamForDate(date: Date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
}

function quietTimelineScore() {
  return {
    overall: 12,
    rank: 0,
    percentile: 1,
    label: "Quiet",
    mood: "Quiet",
    reasons: ["baseline"],
    metrics: {
      activity: 10,
      importance: 8,
      intensity: 8,
      excitement: 8,
      wonder: 8,
      sadness: 3,
      friction: 4,
      connection: 6,
      momentum: 5,
    },
  };
}

function dayScore(day: JournalOverviewDay | null | undefined) {
  return day?.score ?? quietTimelineScore();
}

function timelineMetricValue(day: JournalOverviewDay | null | undefined, metric: TimelineMetric) {
  const score = dayScore(day);
  return metric === "overall" ? score.overall : score.metrics[metric];
}

const POSITIVE_SPECTRUM_METRICS = ["activity", "importance", "intensity", "connection"] as const;
const NEGATIVE_SPECTRUM_METRICS = ["friction", "sadness"] as const;

function readCachedJournal(month: string): JournalOverviewResponse | null {
  const cached = journalMonthCache.get(month);
  if (cached) return cached;
  try {
    const raw = window.sessionStorage.getItem(`${JOURNAL_CACHE_PREFIX}${month}`);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as JournalOverviewResponse;
    journalMonthCache.set(month, parsed);
    return parsed;
  } catch {
    return null;
  }
}

function writeCachedJournal(month: string, payload: JournalOverviewResponse) {
  journalMonthCache.set(month, payload);
  try {
    window.sessionStorage.setItem(`${JOURNAL_CACHE_PREFIX}${month}`, JSON.stringify(payload));
  } catch {
    // Ignore storage quota and private-mode failures.
  }
}

async function fetchJournalCached(month: string): Promise<JournalOverviewResponse> {
  const existing = journalMonthInflight.get(month);
  if (existing) return existing;
  const task = fetchJournal(month)
    .then((payload) => {
      writeCachedJournal(month, payload);
      return payload;
    })
    .finally(() => {
      if (journalMonthInflight.get(month) === task) journalMonthInflight.delete(month);
    });
  journalMonthInflight.set(month, task);
  return task;
}

function prefetchJournalMonth(month: string) {
  if (readCachedJournal(month) || journalMonthInflight.has(month)) return;
  void fetchJournalCached(month);
}

/* ── Fetch ─────────────────────────────────────────────────────────── */

async function fetchJournal(month: string, signal?: AbortSignal): Promise<JournalOverviewResponse> {
  const url = month ? `/api/journal/overview?month=${encodeURIComponent(month)}` : "/api/journal/overview";
  const res = await fetch(url, { cache: "no-store", headers: { Accept: "application/json" }, signal });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return (await res.json()) as JournalOverviewResponse;
}

/* ── Day Modal ─────────────────────────────────────────────────────── */

function JournalDayModal({
  day,
  sourceMap,
  onClose,
}: {
  day: JournalOverviewDay;
  sourceMap: Map<string, JournalOverviewSource>;
  onClose: () => void;
}) {
  useEffect(() => {
    function onKey(e: KeyboardEvent) { if (e.key === "Escape") onClose(); }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);

  const evidenceGroups = day.evidence ?? [];

  return (
    <div className="journal-modal-backdrop" onClick={onClose}>
      <div className="journal-modal" onClick={(e) => e.stopPropagation()}>
        <div className="journal-modal-header">
          <div>
            <span className="journal-modal-date">{longDateFmt.format(journalDate(day.date))}</span>
            <h2 className="journal-modal-title">{day.title}</h2>
          </div>
          <button className="journal-modal-close" onClick={onClose} aria-label="Close">&times;</button>
        </div>

        <div className="journal-modal-meta">
          <span className="journal-modal-tone">{day.tone}</span>
          {day.score ? <span className="journal-modal-score">{day.score.label} · {day.score.overall}</span> : null}
          <span className="journal-modal-signals">{day.signalCount} signals</span>
          <span className="journal-modal-focus">{day.focus}</span>
        </div>

        <div className="journal-modal-content-grid">
          <div className="journal-modal-primary">
            <p className="journal-modal-summary">{day.summary}</p>

            <div className="journal-modal-body">
              {day.sections.map((section) => (
                <section key={section.label} className="journal-modal-section">
                  <h3>{section.label}</h3>
                  <p>{section.text}</p>
                </section>
              ))}
            </div>

            {evidenceGroups.length > 0 ? (
              <div className="journal-evidence-panel">
                <h3>Evidence trail</h3>
                <div className="journal-evidence-groups">
                  {evidenceGroups.map((group) => {
                    const source = sourceMap.get(group.key);
                    return (
                      <section key={group.key} className="journal-evidence-group">
                        <div className="journal-evidence-group-head">
                          <span className="journal-modal-signal-dot" style={{ background: SOURCE_COLORS[group.key] || "#666" }} />
                          <strong>{source?.shortLabel || group.key}</strong>
                          <span>{group.count.toLocaleString()} signal{group.count === 1 ? "" : "s"}</span>
                        </div>
                        <div className="journal-evidence-list">
                          {group.items.map((item, index) => (
                            <article key={`${group.key}-${item.title}-${index}`} className="journal-evidence-item">
                              <div className="journal-evidence-item-head">
                                <span>{item.title}</span>
                                {item.kind ? <em>{item.kind}</em> : null}
                              </div>
                              {item.meta || item.detail ? (
                                <p>
                                  {[item.meta, item.detail].filter(Boolean).join(" · ")}
                                </p>
                              ) : null}
                            </article>
                          ))}
                        </div>
                      </section>
                    );
                  })}
                </div>
              </div>
            ) : null}
          </div>

          <aside className="journal-modal-sidebar">
            {day.signals.length > 0 ? (
              <div className="journal-source-summary">
                <h3>Sources</h3>
                <div className="journal-modal-signals-bar">
                  {day.signals.map((sig) => {
                    const src = sourceMap.get(sig.key);
                    return (
                      <div key={sig.key} className="journal-modal-signal" title={sig.note}>
                        <span className="journal-modal-signal-dot" style={{ background: SOURCE_COLORS[sig.key] || "#666" }} />
                        <span className="journal-modal-signal-label">{src?.shortLabel || sig.key}</span>
                        <span className="journal-modal-signal-count">{sig.count}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            ) : null}
            <div className="journal-modal-closing">{day.closing}</div>
          </aside>
        </div>
      </div>
    </div>
  );
}

/* ── Chronological Timeline ───────────────────────────────────────── */

function JournalTimeline({
  calendarMonth,
  filteredDays,
  allDayMap,
  focusedDate,
  onFocusDate,
  onOpenDay,
}: {
  calendarMonth: Date;
  filteredDays: JournalOverviewDay[];
  allDayMap: Map<string, JournalOverviewDay>;
  focusedDate: string;
  onFocusDate: (date: string) => void;
  onOpenDay: (dayId: string) => void;
}) {
  const viewportRef = useRef<HTMLDivElement | null>(null);
  const itemRefs = useRef<Map<string, HTMLButtonElement>>(new Map());
  const skipSyncScrollRef = useRef(false);

  const filteredDayMap = useMemo(() => new Map(filteredDays.map((d) => [d.date, d])), [filteredDays]);
  const timelineItems = useMemo(() => {
    const start = startOfMonth(calendarMonth);
    const total = endOfMonth(calendarMonth).getDate();
    return Array.from({ length: total }, (_, index) => {
      const date = shiftDate(start, index);
      const key = dateKey(date);
      const rawDay = allDayMap.get(key) ?? null;
      const day = filteredDayMap.get(key) ?? null;
      return {
        key,
        date,
        day,
        rawDay,
        hasHiddenActivity: Boolean(rawDay && !day),
      };
    });
  }, [allDayMap, calendarMonth, filteredDayMap]);

  const activeItems = useMemo(() => timelineItems.filter((item) => item.day), [timelineItems]);
  const focusedItem = useMemo(() => {
    return timelineItems.find((item) => item.key === focusedDate) ?? timelineItems[timelineItems.length - 1] ?? null;
  }, [focusedDate, timelineItems]);
  const focusedIndex = useMemo(() => {
    const index = timelineItems.findIndex((item) => item.key === focusedDate);
    return index >= 0 ? index : Math.max(0, timelineItems.length - 1);
  }, [focusedDate, timelineItems]);
  const focusedEntry = focusedItem?.day ?? null;
  const focusedScore = dayScore(focusedItem?.rawDay ?? focusedEntry);
  const scrubProgress = timelineItems.length > 1
    ? Math.round((focusedIndex / (timelineItems.length - 1)) * 100)
    : 0;

  const topOverall = useMemo(() => {
    return [...activeItems].sort((a, b) => timelineMetricValue(b.day, "overall") - timelineMetricValue(a.day, "overall"))[0] ?? null;
  }, [activeItems]);
  const monthMean = useMemo(() => {
    if (!timelineItems.length) return 0;
    const total = timelineItems.reduce((sum, item) => sum + timelineMetricValue(item.rawDay ?? item.day, "overall"), 0);
    return Math.round(total / timelineItems.length);
  }, [timelineItems]);

  const setItemRef = useCallback((key: string, node: HTMLButtonElement | null) => {
    if (node) itemRefs.current.set(key, node);
    else itemRefs.current.delete(key);
  }, []);

  const scrollToDate = useCallback((date: string, behavior: ScrollBehavior = "smooth") => {
    itemRefs.current.get(date)?.scrollIntoView({ behavior, block: "nearest", inline: "center" });
  }, []);

  useEffect(() => {
    if (!focusedItem) return;
    if (skipSyncScrollRef.current) {
      skipSyncScrollRef.current = false;
      return;
    }
    scrollToDate(focusedItem.key, "smooth");
  }, [focusedItem, scrollToDate]);

  const selectTimelineItem = useCallback((date: string) => {
    skipSyncScrollRef.current = true;
    onFocusDate(date);
    scrollToDate(date);
  }, [onFocusDate, scrollToDate]);

  const stepTimeline = useCallback((direction: -1 | 1) => {
    if (!timelineItems.length) return;
    const selectedIndex = timelineItems.findIndex((item) => item.key === focusedDate);
    const baseIndex = selectedIndex >= 0 ? selectedIndex : (direction > 0 ? -1 : timelineItems.length);
    const nextIndex = Math.max(0, Math.min(timelineItems.length - 1, baseIndex + direction));
    const next = timelineItems[nextIndex];
    if (next) {
      skipSyncScrollRef.current = true;
      onFocusDate(next.key);
      scrollToDate(next.key);
    }
  }, [focusedDate, onFocusDate, scrollToDate, timelineItems]);

  const handleViewportWheel = useCallback((event: ReactWheelEvent<HTMLDivElement>) => {
    const viewport = viewportRef.current;
    if (!viewport) return;
    if (Math.abs(event.deltaY) <= Math.abs(event.deltaX)) return;
    event.preventDefault();
    viewport.scrollLeft += event.deltaY;
  }, []);

  const handleScrubChange = useCallback((event: ChangeEvent<HTMLInputElement>) => {
    const next = timelineItems[event.target.valueAsNumber];
    if (!next) return;
    skipSyncScrollRef.current = true;
    onFocusDate(next.key);
    scrollToDate(next.key, "auto");
  }, [onFocusDate, scrollToDate, timelineItems]);

  const focusTitle = focusedEntry
    ? focusedEntry.title
    : focusedItem?.hasHiddenActivity
      ? "Hidden by current filter"
      : "Quiet day";
  const focusSummary = focusedEntry
    ? focusedEntry.summary
    : focusedItem?.hasHiddenActivity
      ? "This day has journal activity, but the current source filter removes its details from view."
      : "No strong journal signal landed on this day. It still holds the month’s baseline rhythm.";
  const focusDateLabel = focusedItem ? longDateFmt.format(focusedItem.date) : monthTitleFmt.format(calendarMonth);

  return (
    <WorkspacePanel
      className="journal-spectrum-panel"
      title={(
        <div className="journal-spectrum-titlebar">
          <span>Timeline</span>
          <small>{monthTitleFmt.format(calendarMonth)}</small>
        </div>
      )}
    >
      <div className="journal-spectrum-shell">
        <section className="journal-spectrum-focuscard">
          <div className="journal-spectrum-focuscopy">
            <span className="journal-spectrum-focusdate">{focusDateLabel}</span>
            <div className="journal-spectrum-focushead compact">
              <div>
                <h3>{focusTitle}</h3>
                <p>{focusSummary}</p>
              </div>
              <div className="journal-spectrum-scorehero">
                <strong>{focusedScore.overall}</strong>
                <span>{focusedScore.label}</span>
              </div>
            </div>

            <div className="journal-spectrum-badges">
              <span className="journal-spectrum-badge is-primary">{focusedScore.mood}</span>
              <span className="journal-spectrum-badge is-secondary">Mean {monthMean}</span>
              <span className="journal-spectrum-badge is-secondary">Peak {topOverall?.day?.score?.overall ?? 0}</span>
              {focusedEntry ? <span className="journal-spectrum-badge is-primary">{focusedEntry.signalCount} signals</span> : null}
            </div>

            <div className="journal-spectrum-meta">
              {focusedEntry ? (
                <>
                  <span className="is-primary">{focusedEntry.focus}</span>
                  <span className="is-secondary">{focusedEntry.movement}</span>
                </>
              ) : (
                <span className="journal-spectrum-badge">{focusedScore.label}</span>
              )}
            </div>
          </div>

          <div className="journal-spectrum-quickstats">
            {(["activity", "importance", "intensity", "friction"] as TimelineMetric[]).map((key) => (
              <div
                key={key}
                className="journal-spectrum-mini-stat"
                style={{
                  "--metric-color": TIMELINE_METRIC_COLORS[key],
                  "--metric-fill": `${Math.max(8, timelineMetricValue(focusedItem?.rawDay ?? focusedEntry, key))}%`,
                } as SpectrumMetricStyle}
              >
                <span className="journal-spectrum-mini-head">
                  <em>{TIMELINE_METRIC_LABELS[key]}</em>
                  <strong>{timelineMetricValue(focusedItem?.rawDay ?? focusedEntry, key)}</strong>
                </span>
                <span className="journal-spectrum-mini-meter">
                  <i />
                </span>
              </div>
            ))}
          </div>
        </section>

        <div className="journal-spectrum-controls">
          <button className="journal-spectrum-step" type="button" onClick={() => stepTimeline(-1)} aria-label="Previous day in the timeline">&lsaquo;</button>
          <div className="journal-spectrum-scrub" style={{ "--scrub-progress": `${scrubProgress}%` } as CSSProperties}>
            <div className="journal-spectrum-track-meta">
              <span>{focusedItem ? `${shortDateFmt.format(focusedItem.date)} · Day ${focusedIndex + 1} of ${timelineItems.length}` : monthTitleFmt.format(calendarMonth)}</span>
              <span>{activeItems.length} captured days</span>
            </div>
            <input
              className="journal-spectrum-range"
              type="range"
              min={0}
              max={Math.max(0, timelineItems.length - 1)}
              step={1}
              value={focusedIndex}
              onChange={handleScrubChange}
              aria-label="Journal timeline slider"
            />
          </div>
          <button className="journal-spectrum-step" type="button" onClick={() => stepTimeline(1)} aria-label="Next day in the timeline">&rsaquo;</button>
          <button
            type="button"
            className="journal-spectrum-open"
            onClick={() => focusedEntry && onOpenDay(focusedEntry.id)}
            disabled={!focusedEntry}
          >
            Open day details
          </button>
        </div>

        <div className="journal-spectrum-rail">
          <div
            ref={viewportRef}
            className="journal-spectrum-viewport"
            aria-label={`${monthTitleFmt.format(calendarMonth)} sliding journal timeline`}
            onWheel={handleViewportWheel}
          >
            <div className="journal-spectrum-track">
              {timelineItems.map((item) => {
                const scoreSource = item.rawDay ?? item.day;
                const score = dayScore(scoreSource);
                const isSelected = item.key === focusedDate;
                const style: TimelineStyle = {
                  "--timeline-color": TIMELINE_METRIC_COLORS.overall,
                };

                return (
                  <button
                    key={item.key}
                    ref={(node) => setItemRef(item.key, node)}
                    type="button"
                    className={`journal-spectrum-item ${item.day ? "has-entry" : "is-quiet"} ${item.hasHiddenActivity ? "is-filtered" : ""} ${isSelected ? "active" : ""}`}
                    style={style}
                    onClick={() => selectTimelineItem(item.key)}
                    aria-pressed={isSelected}
                    title={item.day?.title ?? (item.hasHiddenActivity ? "Hidden by current filter" : "Quiet day")}
                  >
                    <span className="journal-spectrum-wave">
                      <span className="journal-spectrum-half is-up">
                        {POSITIVE_SPECTRUM_METRICS.map((key) => {
                          const value = score.metrics[key];
                          const bandStyle: SpectrumBandStyle = {
                            "--band-height": `${Math.max(10, value)}%`,
                            "--band-color": TIMELINE_METRIC_COLORS[key],
                          };
                          return <i key={key} className="journal-spectrum-band" style={bandStyle} />;
                        })}
                      </span>
                      <span className="journal-spectrum-score">{score.overall}</span>
                      <span className="journal-spectrum-half is-down">
                        {NEGATIVE_SPECTRUM_METRICS.map((key) => {
                          const value = score.metrics[key];
                          const bandStyle: SpectrumBandStyle = {
                            "--band-height": `${Math.max(8, value)}%`,
                            "--band-color": TIMELINE_METRIC_COLORS[key],
                          };
                          return <i key={key} className="journal-spectrum-band" style={bandStyle} />;
                        })}
                      </span>
                      <span className="journal-spectrum-glow" style={{ opacity: Math.max(0.18, score.overall / 100) }} />
                    </span>
                    <span className="journal-spectrum-caption">
                      <strong>{item.date.getDate()}</strong>
                      <em>{score.label}</em>
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </WorkspacePanel>
  );
}

/* ── Main Component ────────────────────────────────────────────────── */

export default function JournalPage() {
  const initialMonth = startOfMonth(new Date());
  const [overview, setOverview] = useState<JournalOverviewResponse | null>(() => readCachedJournal(monthParamForDate(initialMonth)));
  const [error, setError] = useState<string | null>(null);
  const [selectedSource, setSelectedSource] = useState<JournalSourceFilter>("all");
  const [focusedDate, setFocusedDate] = useState<string>(dateKey(initialMonth));
  const [openedDayId, setOpenedDayId] = useState<string>("");
  const [calendarMonth, setCalendarMonth] = useState<Date>(() => initialMonth);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const fullscreenHostRef = useRef<HTMLDivElement | null>(null);

  /* Derive month string from calendarMonth state */
  const monthParam = monthParamForDate(calendarMonth);

  /* Fetch on mount + poll every 30s, re-fetch on month change */
  useEffect(() => {
    let cancelled = false;
    const cached = readCachedJournal(monthParam);
    if (cached) {
      setOverview(cached);
      setError(null);
    }
    async function load() {
      try {
        const next = await fetchJournalCached(monthParam);
        if (!cancelled) {
          setOverview(next);
          setError(null);
        }
        prefetchJournalMonth(monthParamForDate(shiftMonth(calendarMonth, -1)));
        prefetchJournalMonth(monthParamForDate(shiftMonth(calendarMonth, 1)));
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Failed to load.");
      }
    }
    void load();
    const iv = window.setInterval(() => {
      if (document.hidden) return;
      void load();
    }, 30000);
    return () => { cancelled = true; window.clearInterval(iv); };
  }, [calendarMonth, monthParam]);

  useEffect(() => {
    const doc = document as FullscreenDocument;
    const onFullscreenChange = () => {
      const activeElement = document.fullscreenElement ?? doc.webkitFullscreenElement ?? null;
      setIsFullscreen(activeElement === fullscreenHostRef.current);
    };
    document.addEventListener("fullscreenchange", onFullscreenChange);
    document.addEventListener("webkitfullscreenchange", onFullscreenChange as EventListener);
    onFullscreenChange();
    return () => {
      document.removeEventListener("fullscreenchange", onFullscreenChange);
      document.removeEventListener("webkitfullscreenchange", onFullscreenChange as EventListener);
    };
  }, []);

  const journalSources = overview?.sources?.length ? overview.sources : [];
  const journalDays = overview?.days || [];
  const sourceMap = useMemo(() => new Map(journalSources.map((s) => [s.key, s])), [journalSources]);

  const filteredDays = useMemo(() => {
    if (selectedSource === "all") return journalDays;
    return journalDays.filter((d) => d.sources.includes(selectedSource));
  }, [journalDays, selectedSource]);

  const allDayMap = useMemo(() => new Map(journalDays.map((d) => [d.date, d])), [journalDays]);
  const filteredDayMap = useMemo(() => new Map(filteredDays.map((d) => [d.date, d])), [filteredDays]);
  const openedDay = journalDays.find((d) => d.id === openedDayId) ?? null;

  /* Month nav */
  const prevMonth = useCallback(() => setCalendarMonth((m) => shiftMonth(m, -1)), []);
  const nextMonth = useCallback(() => setCalendarMonth((m) => shiftMonth(m, 1)), []);
  const goToday = useCallback(() => setCalendarMonth(startOfMonth(new Date())), []);
  const changeYear = useCallback((event: ChangeEvent<HTMLSelectElement>) => {
    const year = Number.parseInt(event.target.value, 10);
    if (!Number.isFinite(year)) return;
    setCalendarMonth((month) => new Date(year, month.getMonth(), 1, 12));
  }, []);

  const yearOptions = useMemo(() => {
    const currentYear = new Date().getFullYear();
    const lastYear = Math.max(currentYear + 5, calendarMonth.getFullYear());
    return Array.from({ length: lastYear - EARLIEST_JOURNAL_YEAR + 1 }, (_, index) => lastYear - index);
  }, [calendarMonth]);

  useEffect(() => {
    const today = dateKey(new Date());
    const monthPrefix = monthParamForDate(calendarMonth);
    setFocusedDate((current) => {
      if (current && current.startsWith(monthPrefix)) return current;
      if (today.startsWith(monthPrefix)) return today;
      return filteredDays[filteredDays.length - 1]?.date ?? dateKey(endOfMonth(calendarMonth));
    });
  }, [calendarMonth, filteredDays]);

  useEffect(() => {
    if (!openedDayId) return;
    if (journalDays.some((day) => day.id === openedDayId)) return;
    setOpenedDayId("");
  }, [journalDays, openedDayId]);

  /* Calendar cells */
  const calendarCells = useMemo(() => {
    const mStart = startOfMonth(calendarMonth);
    const mEnd = endOfMonth(calendarMonth);
    const lead = mondayColumn(mStart);
    const total = Math.ceil((lead + mEnd.getDate()) / 7) * 7;
    const first = shiftDate(mStart, -lead);

    return Array.from({ length: total }, (_, i) => {
      const cellDate = shiftDate(first, i);
      const key = dateKey(cellDate);
      const day = filteredDayMap.get(key) ?? null;
      const hidden = selectedSource !== "all" && allDayMap.has(key) && !day;
      return { key, label: cellDate.getDate(), inMonth: cellDate.getMonth() === mStart.getMonth(), day, hidden };
    });
  }, [allDayMap, calendarMonth, filteredDayMap, selectedSource]);

  /* All unique source keys across all days for filter chips */
  const allSourceKeys = useMemo(() => {
    const keys = new Set<string>();
    for (const d of journalDays) for (const s of d.sources) keys.add(s);
    return Array.from(keys);
  }, [journalDays]);

  const subtitle = overview?.available
    ? `${overview.dayCount} days from ${overview.accountCount || 0} account(s)`
    : overview?.import?.running ? "Importing Google history..." : "Import Google history to populate the journal.";

  const toggleFullscreen = useCallback(async () => {
    const host = fullscreenHostRef.current as FullscreenHost | null;
    if (!host) return;
    const doc = document as FullscreenDocument;
    const activeElement = document.fullscreenElement ?? doc.webkitFullscreenElement ?? null;
    if (activeElement === host) {
      if (document.exitFullscreen) {
        await document.exitFullscreen();
        return;
      }
      if (doc.webkitExitFullscreen) {
        await doc.webkitExitFullscreen();
      }
      return;
    }
    if (host.requestFullscreen) {
      await host.requestFullscreen();
      return;
    }
    if (host.webkitRequestFullscreen) {
      await host.webkitRequestFullscreen();
    }
  }, []);

  return (
    <WorkspacePage title="Journal" subtitle={error ?? subtitle}>
      <div ref={fullscreenHostRef} className={`journal-panel-shell ${isFullscreen ? "is-fullscreen" : ""}`}>
        <WorkspacePanel
          className="journal-panel"
          title={(
            <div className="journal-panel-titlebar">
              <div className="journal-panel-heading">
                <span className="journal-panel-month">{monthNameFmt.format(calendarMonth)}</span>
                <select
                  className="journal-year-select"
                  value={calendarMonth.getFullYear()}
                  onChange={changeYear}
                  aria-label="Select journal year"
                >
                  {yearOptions.map((year) => (
                    <option key={year} value={year}>{year}</option>
                  ))}
                </select>
              </div>
              <div className="journal-month-nav" aria-label="Journal month navigation">
                <button className="journal-nav-btn" onClick={prevMonth} aria-label="Previous month">&lsaquo;</button>
                <button className="journal-nav-today" onClick={goToday}>Today</button>
                <button className="journal-nav-btn" onClick={nextMonth} aria-label="Next month">&rsaquo;</button>
              </div>
            </div>
          )}
          actions={
            <div className="journal-panel-actions-group">
              <button
                type="button"
                className={`journal-fullscreen-btn ${isFullscreen ? "active" : ""}`}
                onClick={() => void toggleFullscreen()}
                aria-pressed={isFullscreen}
                title={isFullscreen ? "Exit full screen calendar view" : "Open full screen calendar view"}
              >
                {isFullscreen ? "Exit full screen" : "Full screen"}
              </button>
              <div className="journal-filter-bar">
                <button
                  className={`journal-filter-chip ${selectedSource === "all" ? "active" : ""}`}
                  onClick={() => setSelectedSource("all")}
                >All</button>
                {allSourceKeys.map((key) => {
                  const src = sourceMap.get(key);
                  return (
                    <button
                      key={key}
                      className={`journal-filter-chip ${selectedSource === key ? "active" : ""}`}
                      onClick={() => setSelectedSource(key)}
                    >
                      <span className="journal-filter-dot" style={{ background: SOURCE_COLORS[key] || "#666" }} />
                      {src?.shortLabel || key}
                    </button>
                  );
                })}
              </div>
            </div>
          }
        >
          {filteredDays.length > 0 || calendarCells.some((c) => c.day) ? (
            <div className="journal-calendar-board" role="grid" aria-label={`${monthTitleFmt.format(calendarMonth)} calendar`}>
              {WEEKDAY_LABELS.map((l) => (
                <div key={l} className="journal-calendar-weekday" role="columnheader">{l}</div>
              ))}

              {calendarCells.map((cell) => {
                if (!cell.day) {
                  return (
                    <div
                      key={cell.key}
                      className={`journal-cal-cell journal-cal-cell--empty ${cell.inMonth ? "" : "is-outside"} ${cell.hidden ? "is-filtered" : ""}`}
                      role="gridcell"
                      aria-disabled="true"
                    >
                      <span className="journal-cal-num">{cell.label}</span>
                    </div>
                  );
                }

                const d = cell.day;
                return (
                  <button
                    key={d.id}
                    type="button"
                    className={`journal-cal-cell journal-cal-cell--filled ${focusedDate === d.date ? "active" : ""}`}
                    onClick={() => {
                      setFocusedDate(d.date);
                      setOpenedDayId(d.id);
                    }}
                    role="gridcell"
                    aria-pressed={focusedDate === d.date}
                    title={d.title}
                  >
                    <span className="journal-cal-num">{cell.label}</span>
                    <div className="journal-cal-copy">
                      <span className="journal-cal-title">{d.title}</span>
                      <span className="journal-cal-summary">{d.summary}</span>
                    </div>
                    <div className="journal-cal-dots">
                      {d.sources.map((src) => (
                        <span key={src} className="journal-cal-dot" style={{ background: SOURCE_COLORS[src] || "#666" }} />
                      ))}
                    </div>
                  </button>
                );
              })}
            </div>
          ) : (
            <WorkspaceEmpty
              title={overview?.import?.running ? "Import running" : "No days this month"}
              description={overview?.import?.running
                ? "Journal entries will appear as the import finishes."
                : "Navigate to a month with imported data, or run a Google history import from System."}
            />
          )}
        </WorkspacePanel>
      </div>

      <JournalTimeline
        calendarMonth={calendarMonth}
        filteredDays={filteredDays}
        allDayMap={allDayMap}
        focusedDate={focusedDate}
        onFocusDate={setFocusedDate}
        onOpenDay={setOpenedDayId}
      />

      {openedDay && (
        <JournalDayModal
          day={openedDay}
          sourceMap={sourceMap}
          onClose={() => setOpenedDayId("")}
        />
      )}
    </WorkspacePage>
  );
}
