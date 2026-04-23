import { useCallback, useRef, useState } from 'react'
import {
  Box, Button, Card, CardContent, Collapse, Grid, LinearProgress,
  MenuItem, Select, Stack, Typography,
} from '@mui/material'
import PlayArrowIcon from '@mui/icons-material/PlayArrow'
import StopIcon from '@mui/icons-material/Stop'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import ExpandLessIcon from '@mui/icons-material/ExpandLess'

import { useApi } from '../lib/useApi'
import { postJson, getJson } from '../lib/api'
import { PageHeader } from '../components/PageHeader'
import { DataTable } from '../components/DataTable'
import { StatusChip } from '../components/StatusChip'
import { consoleEndpoints } from '../config/endpoints'

interface Profile { id: string; label: string }
interface ProfilesResponse { profiles: Profile[] }

interface TestTask {
  running: boolean
  profile: string
  run_id: string
  started_at: string
  finished_at: string | null
  returncode: number | null
  progress_percent: number | null
  progress_line: string | null
  cancel_requested: boolean
  tail: string[]
}
interface StatusResponse { tasks: { tests: TestTask } }

interface TestReportSummary {
  run_id: string
  timestamp: string
  total_tests: number
  passed: number
  failed: number
  pass_rate: number
  total_duration_s: number
}
interface DurationMetrics {
  p50_s: number
  p95_s: number
  slowest_tests: { name: string; duration_s: number }[]
}
interface CategoryInfo {
  total: number
  passed: number
  failed: number
  pass_rate: number
  p50_s: number
  p95_s: number
  failures: string[]
}
interface PerfEntry {
  data: {
    stages_ms?: Record<string, number>
    fixture?: string
    transcribe_seconds_wall?: number
    command_seconds_wall?: number
    command_count?: number
  }
}
interface TestResult { name: string; status: string; duration_s: number; timestamp: string }
interface TestReport {
  summary: TestReportSummary
  test_duration_metrics?: DurationMetrics
  category_breakdown?: Record<string, CategoryInfo>
  failure_analysis?: Record<string, string[]>
  performance_metrics?: PerfEntry[]
  results?: TestResult[]
}

function fmtNum(n: number | null | undefined, digits = 1): string {
  return typeof n === 'number' && Number.isFinite(n) ? n.toFixed(digits) : '-'
}

interface LatestReportsResponse {
  reports: Record<string, { ok: boolean; report: TestReport; report_mtime_iso: string }>
}
interface HistoryEntry {
  file: string
  summary: TestReportSummary | string | null
  profile_id: string
  report_mtime_iso: string
}
interface HistoryResponse { reports: HistoryEntry[] }
interface SingleReportResponse { ok: boolean; report: TestReport; file: string; profile_id: string }

function formatTimestamp(iso: string): string {
  if (!iso) return '-'
  const d = new Date(iso)
  if (isNaN(d.getTime())) return iso
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

function summarizeHistoryEntry(s: HistoryEntry['summary']): string {
  if (!s) return '-'
  if (typeof s === 'string') return s
  const passed = s.passed ?? 0
  const total = s.total_tests ?? 0
  const rate = typeof s.pass_rate === 'number' ? `${s.pass_rate.toFixed(0)}%` : '-'
  return `${passed}/${total} pass (${rate})`
}

function passRateColor(rate: number): 'ok' | 'warn' | 'bad' {
  if (rate >= 95) return 'ok'
  if (rate >= 75) return 'warn'
  return 'bad'
}

function pctColor(rate: number): string {
  if (rate >= 95) return '#2dd4bf'
  if (rate >= 75) return '#fbbf24'
  return '#ef4444'
}

export default function TestsPanel() {
  const [selectedProfile, setSelectedProfile] = useState('')
  const [selectedFile, setSelectedFile] = useState('')
  const [activeReport, setActiveReport] = useState<TestReport | null>(null)
  const [activeProfileId, setActiveProfileId] = useState<string | null>(null)
  const [expandedCategory, setExpandedCategory] = useState<string | null>(null)
  const [expandedFailures, setExpandedFailures] = useState<Record<string, boolean>>({})
  const [narrative, setNarrative] = useState<string | null>(null)
  const [narrativeLoading, setNarrativeLoading] = useState(false)
  const [showLog, setShowLog] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)

  const { data: profiles, error: profilesError } = useApi<ProfilesResponse>(consoleEndpoints.testsProfiles)
  const { data: status, error: statusError } = useApi<StatusResponse>(consoleEndpoints.testsStatus, { pollMs: 2000 })
  const { data: latest, error: latestError, refetch: refetchLatest } = useApi<LatestReportsResponse>(consoleEndpoints.reportsLatest)
  const { data: history, error: historyError, refetch: refetchHistory } = useApi<HistoryResponse>(consoleEndpoints.reportsHistory)

  const task = status?.tasks?.tests
  const profileList = profiles?.profiles ?? []
  const profileOptions = profileList.some(p => p.id === 'all')
    ? profileList
    : [{ id: 'all', label: 'All profiles' }, ...profileList]
  const testsUnavailable = Boolean(profilesError || statusError || latestError || historyError)
  const unavailableMessage = profilesError || statusError || latestError || historyError
  const effectiveProfile = selectedProfile || 'all'

  const loadLatest = useCallback(() => {
    if (!latest?.reports) return
    const entry = latest.reports[effectiveProfile]
    if (entry?.ok && entry.report) {
      setActiveReport(entry.report)
      setActiveProfileId(effectiveProfile)
      setNarrative(null)
    }
  }, [latest, effectiveProfile])

  const loadFileReport = useCallback(async (file: string) => {
    try {
      const res = await getJson<SingleReportResponse>(consoleEndpoints.reportByFile(file))
      if (res.ok && res.report) {
        setActiveReport(res.report)
        setActiveProfileId(res.profile_id)
        setNarrative(null)
      }
    } catch {}
  }, [])

  const runTests = async () => {
    setActionError(null)
    try {
      await postJson(consoleEndpoints.testsRun, { profile: effectiveProfile })
    } catch (e) { setActionError(String(e)) }
  }

  const cancelTests = async () => {
    setActionError(null)
    try {
      await postJson(consoleEndpoints.testsCancel, {})
    } catch (e) { setActionError(String(e)) }
  }

  const generateSummary = async () => {
    setNarrativeLoading(true)
    setNarrative(null)
    try {
      const res = await postJson<{ ok: boolean; summary: string }>(consoleEndpoints.testsSummarize, { profile: 'all' })
      if (res.ok) setNarrative(res.summary)
    } catch (e) { setNarrative(`Error: ${e}`) }
    setNarrativeLoading(false)
  }

  const handleHistorySelect = (file: string) => {
    setSelectedFile(file)
    if (file) void loadFileReport(file)
  }

  if (latest && !activeReport) loadLatest()

  const prevReportRef = useRef<string | null>(null)
  const currentRunId = activeReport?.summary?.run_id ?? null
  if (currentRunId && currentRunId !== prevReportRef.current && !narrative && !narrativeLoading) {
    prevReportRef.current = currentRunId
    void generateSummary()
  }

  const rpt = activeReport
  const cats = rpt ? (Object.entries(rpt.category_breakdown ?? {}) as [string, CategoryInfo][]) : []
  const failures = rpt ? (Object.entries(rpt.failure_analysis ?? {}) as [string, string[]][]) : []
  const perfs = rpt?.performance_metrics ?? []
  const slowest = rpt?.test_duration_metrics?.slowest_tests ?? []
  const results = rpt?.results ?? []
  const passRateSafe = typeof rpt?.summary?.pass_rate === 'number' ? rpt.summary.pass_rate : 0
  const stageEntries = perfs.filter(p => p.data.stages_ms)
  const quantEntries = perfs.filter(p => p.data.transcribe_seconds_wall != null || p.data.command_seconds_wall != null)

  return (
    <Box>
      <PageHeader title="Test Runner" subtitle="Run profiles, inspect reports, and track quality" data-testid="tests-header" />

      <Card sx={{ mb: 2 }}>
        <CardContent>
          {testsUnavailable && unavailableMessage && (
            <Typography variant="caption" color="warning.main" sx={{ mb: 1, display: 'block' }}>
              {unavailableMessage}
            </Typography>
          )}
          <Stack direction="row" spacing={1.5} alignItems="center" flexWrap="wrap">
            <Select
              size="small"
              value={effectiveProfile}
              onChange={e => setSelectedProfile(e.target.value)}
              displayEmpty
              sx={{ minWidth: 180, fontSize: '0.8125rem' }}
            >
              {profileOptions.length === 0 && <MenuItem value="">Loading...</MenuItem>}
              {profileOptions.map(p => (
                <MenuItem key={p.id} value={p.id} sx={{ fontSize: '0.8125rem' }}>{p.label}</MenuItem>
              ))}
            </Select>
            <Button
              data-testid="tests-run-btn"
              variant="contained"
              size="small"
              startIcon={<PlayArrowIcon />}
              disabled={!!task?.running || testsUnavailable || profileOptions.length === 0}
              onClick={runTests}
            >
              Run
            </Button>
            <Button
              variant="outlined"
              size="small"
              color="error"
              startIcon={<StopIcon />}
              disabled={!task?.running || testsUnavailable}
              onClick={cancelTests}
            >
              Cancel
            </Button>
            {task?.running && (
              <StatusChip severity="warn" label={`RUNNING: ${task.profile || effectiveProfile}`} />
            )}
            {task && !task.running && task.returncode != null && (
              <StatusChip
                severity={task.returncode === 0 ? 'ok' : 'bad'}
                label={task.returncode === 0 ? 'PASSED' : `EXIT ${task.returncode}`}
              />
            )}
          </Stack>

          {task?.running && (
            <Box sx={{ mt: 1.5 }}>
              <LinearProgress
                variant={task.progress_percent != null ? 'determinate' : 'indeterminate'}
                value={task.progress_percent ?? 0}
                sx={{ height: 6, borderRadius: 3 }}
              />
              {task.progress_line && (
                <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                  {task.progress_line}
                </Typography>
              )}
            </Box>
          )}

          {task?.started_at && (
            <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
              Started {formatTimestamp(task.started_at)}
              {task.finished_at && ` | Finished ${formatTimestamp(task.finished_at)}`}
            </Typography>
          )}

          {actionError && (
            <Typography variant="caption" color="error" sx={{ mt: 0.5, display: 'block' }}>{actionError}</Typography>
          )}
        </CardContent>
      </Card>

      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Stack direction="row" spacing={1.5} alignItems="center" flexWrap="wrap">
            <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>Report:</Typography>
            <Select
              size="small"
              value={selectedFile}
              onChange={e => handleHistorySelect(e.target.value)}
              displayEmpty
              sx={{ minWidth: 320, fontSize: '0.8125rem' }}
            >
              <MenuItem value="" sx={{ fontSize: '0.8125rem' }}>Latest</MenuItem>
              {(history?.reports ?? [])
                .filter(h => !!h.file)
                .map(h => (
                  <MenuItem key={h.file} value={h.file} sx={{ fontSize: '0.8125rem' }}>
                    [{h.profile_id}] {formatTimestamp(h.report_mtime_iso)} - {summarizeHistoryEntry(h.summary)}
                  </MenuItem>
                ))}
            </Select>
            <Button size="small" variant="outlined" onClick={() => { setSelectedFile(''); loadLatest(); refetchLatest(); refetchHistory() }}>
              Refresh
            </Button>
          </Stack>
        </CardContent>
      </Card>

      {rpt && (
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Stack direction="row" spacing={2} alignItems="center" flexWrap="wrap" sx={{ mb: 1 }}>
              <Typography variant="h6" sx={{ fontWeight: 800 }}>
                {activeProfileId ?? 'Report'}
              </Typography>
              <StatusChip
                severity={passRateColor(passRateSafe)}
                label={`${fmtNum(rpt.summary?.pass_rate, 1)}% pass`}
              />
              <Typography variant="body2" color="text.secondary">
                {rpt.summary?.passed ?? 0} passed / {rpt.summary?.failed ?? 0} failed / {rpt.summary?.total_tests ?? 0} total
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {fmtNum(rpt.summary?.total_duration_s, 1)}s
              </Typography>
            </Stack>
            <LinearProgress
              variant="determinate"
              value={passRateSafe}
              sx={{
                height: 8, borderRadius: 4,
                bgcolor: 'rgba(239,68,68,0.2)',
                '& .MuiLinearProgress-bar': { bgcolor: pctColor(passRateSafe), borderRadius: 4 },
              }}
            />
            <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
              Run {rpt.summary?.run_id ?? '-'} at {formatTimestamp(rpt.summary?.timestamp ?? '')}
              {rpt.test_duration_metrics && ` | p50 ${fmtNum(rpt.test_duration_metrics.p50_s, 2)}s  p95 ${fmtNum(rpt.test_duration_metrics.p95_s, 2)}s`}
            </Typography>
          </CardContent>
        </Card>
      )}

      {rpt && (
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1 }}>AI Summary</Typography>
            {narrativeLoading && <LinearProgress sx={{ mb: 1 }} />}
            {narrativeLoading && !narrative && (
              <Typography variant="caption" color="text.secondary">Generating summary...</Typography>
            )}
            {narrative && (
              <Typography
                variant="body2"
                sx={{ whiteSpace: 'pre-wrap', fontFamily: '"IBM Plex Mono", monospace', fontSize: '0.8125rem' }}
              >
                {narrative}
              </Typography>
            )}
            {!narrative && !narrativeLoading && (
              <Typography variant="caption" color="text.secondary">
                Summary will generate automatically when test results are available.
              </Typography>
            )}
          </CardContent>
        </Card>
      )}

      {cats.length > 0 && (
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1.5 }}>Results by Category</Typography>
            <Grid container spacing={1.5}>
              {cats.map(([cat, info]) => {
                const rate = typeof info?.pass_rate === 'number' ? info.pass_rate : 0
                return (
                  <Grid item xs={12} sm={6} md={4} lg={3} key={cat}>
                    <Card
                      variant="outlined"
                      sx={{
                        cursor: 'pointer',
                        bgcolor: expandedCategory === cat ? 'rgba(255,255,255,0.04)' : 'transparent',
                        '&:hover': { bgcolor: 'rgba(255,255,255,0.03)' },
                      }}
                      onClick={() => setExpandedCategory(expandedCategory === cat ? null : cat)}
                    >
                      <CardContent sx={{ py: 1.5, px: 2, '&:last-child': { pb: 1.5 } }}>
                        <Typography variant="body2" sx={{ fontWeight: 700, mb: 0.5 }}>{cat}</Typography>
                        <Stack direction="row" spacing={1} alignItems="center">
                          <StatusChip severity={passRateColor(rate)} label={`${fmtNum(info?.pass_rate, 0)}%`} />
                          <Typography variant="caption" color="text.secondary">
                            {info?.passed ?? 0}/{info?.total ?? 0}
                          </Typography>
                        </Stack>
                        <LinearProgress
                          variant="determinate"
                          value={rate}
                          sx={{
                            mt: 1, height: 4, borderRadius: 2,
                            bgcolor: 'rgba(239,68,68,0.15)',
                            '& .MuiLinearProgress-bar': { bgcolor: pctColor(rate), borderRadius: 2 },
                          }}
                        />
                      </CardContent>
                    </Card>
                  </Grid>
                )
              })}
            </Grid>
          </CardContent>
        </Card>
      )}

      {expandedCategory && rpt?.category_breakdown?.[expandedCategory] && (
        <Card sx={{ mb: 2 }}>
          <CardContent>
            {(() => {
              const info = rpt.category_breakdown![expandedCategory]
              const rate = typeof info?.pass_rate === 'number' ? info.pass_rate : 0
              const failuresList = info?.failures ?? []
              return (
                <>
                  <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
                    <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
                      Category: {expandedCategory}
                    </Typography>
                    <StatusChip severity={passRateColor(rate)} label={`${fmtNum(info?.pass_rate, 1)}%`} />
                  </Stack>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                    {info?.passed ?? 0} passed / {info?.failed ?? 0} failed / {info?.total ?? 0} total | p50 {fmtNum(info?.p50_s, 2)}s  p95 {fmtNum(info?.p95_s, 2)}s
                  </Typography>
                  {failuresList.length > 0 && (
                    <Box sx={{ mt: 1 }}>
                      <Typography variant="caption" sx={{ fontWeight: 700, color: '#fecaca' }}>Failures:</Typography>
                      {failuresList.map((f, i) => (
                        <Typography
                          key={i}
                          variant="caption"
                          sx={{ display: 'block', fontFamily: '"IBM Plex Mono", monospace', color: 'rgba(255,255,255,0.7)', ml: 1 }}
                        >
                          {f}
                        </Typography>
                      ))}
                    </Box>
                  )}
                  <DataTable>
                    <table>
                      <thead>
                        <tr><th>Test</th><th>Status</th><th>Duration</th></tr>
                      </thead>
                      <tbody>
                        {results
                          .filter(r => (r?.name ?? '').toLowerCase().includes(expandedCategory.toLowerCase()))
                          .map((r, i) => (
                            <tr key={i}>
                              <td>{r.name}</td>
                              <td>
                                <StatusChip
                                  severity={r.status === 'passed' ? 'ok' : r.status === 'failed' ? 'bad' : 'default'}
                                  label={r.status}
                                />
                              </td>
                              <td>{fmtNum(r.duration_s, 2)}s</td>
                            </tr>
                          ))}
                      </tbody>
                    </table>
                  </DataTable>
                </>
              )
            })()}
          </CardContent>
        </Card>
      )}

      {failures.length > 0 && (
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1 }}>Failure Analysis</Typography>
            {failures.map(([cause, tests]) => (
              <Box key={cause} sx={{ mb: 1 }}>
                <Stack
                  direction="row"
                  spacing={0.5}
                  alignItems="center"
                  sx={{ cursor: 'pointer' }}
                  onClick={() => setExpandedFailures(prev => ({ ...prev, [cause]: !prev[cause] }))}
                >
                  {expandedFailures[cause] ? <ExpandLessIcon fontSize="small" /> : <ExpandMoreIcon fontSize="small" />}
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    {cause}
                  </Typography>
                  <StatusChip severity="bad" label={`${tests.length}`} />
                </Stack>
                <Collapse in={expandedFailures[cause]}>
                  <Box sx={{ pl: 3, pt: 0.5 }}>
                    {tests.map((t, i) => (
                      <Typography
                        key={i}
                        variant="caption"
                        sx={{ display: 'block', fontFamily: '"IBM Plex Mono", monospace', color: 'rgba(255,255,255,0.7)' }}
                      >
                        {t}
                      </Typography>
                    ))}
                  </Box>
                </Collapse>
              </Box>
            ))}
          </CardContent>
        </Card>
      )}

      {(stageEntries.length > 0 || slowest.length > 0) && (
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1.5 }}>Performance & Latency</Typography>

            {stageEntries.length > 0 && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="caption" sx={{ fontWeight: 700, mb: 0.5, display: 'block' }}>Stage Timings</Typography>
                <DataTable>
                  <table>
                    <thead>
                      <tr><th>Fixture</th><th>Stage</th><th>ms</th></tr>
                    </thead>
                    <tbody>
                      {stageEntries.map((p, pi) =>
                        Object.entries(p.data.stages_ms!).map(([stage, ms], si) => (
                          <tr key={`${pi}-${si}`}>
                            {si === 0 && (
                              <td rowSpan={Object.keys(p.data.stages_ms!).length}>
                                {p.data.fixture ?? `#${pi + 1}`}
                              </td>
                            )}
                            <td>{stage}</td>
                            <td>{typeof ms === 'number' ? ms.toFixed(0) : ms}</td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </DataTable>
              </Box>
            )}

            {slowest.length > 0 && (
              <Box>
                <Typography variant="caption" sx={{ fontWeight: 700, mb: 0.5, display: 'block' }}>Slowest Tests</Typography>
                <DataTable>
                  <table>
                    <thead>
                      <tr><th>Test</th><th>Duration</th></tr>
                    </thead>
                    <tbody>
                      {slowest.map((t, i) => (
                        <tr key={i}>
                          <td>{t.name}</td>
                          <td>{fmtNum(t.duration_s, 2)}s</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </DataTable>
              </Box>
            )}
          </CardContent>
        </Card>
      )}

      {quantEntries.length > 0 && (
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1 }}>Quantitative Metrics</Typography>
            <DataTable>
              <table>
                <thead>
                  <tr>
                    <th>Fixture</th>
                    <th>Transcribe (s)</th>
                    <th>Command (s)</th>
                    <th>Commands</th>
                  </tr>
                </thead>
                <tbody>
                  {quantEntries.map((p, i) => (
                    <tr key={i}>
                      <td>{p.data.fixture ?? `#${i + 1}`}</td>
                      <td>{fmtNum(p.data.transcribe_seconds_wall, 2)}</td>
                      <td>{fmtNum(p.data.command_seconds_wall, 2)}</td>
                      <td>{p.data.command_count ?? '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </DataTable>
          </CardContent>
        </Card>
      )}

      {task?.tail && task.tail.length > 0 && (
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Stack
              direction="row"
              spacing={1}
              alignItems="center"
              sx={{ cursor: 'pointer', mb: showLog ? 1 : 0 }}
              onClick={() => setShowLog(v => !v)}
            >
              {showLog ? <ExpandLessIcon fontSize="small" /> : <ExpandMoreIcon fontSize="small" />}
              <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>Run Log</Typography>
              <Typography variant="caption" color="text.secondary">({task.tail.length} lines)</Typography>
            </Stack>
            <Collapse in={showLog}>
              <Box
                component="pre"
                sx={{
                  fontFamily: '"IBM Plex Mono", monospace',
                  fontSize: '0.75rem',
                  lineHeight: 1.6,
                  color: 'rgba(255,255,255,0.75)',
                  bgcolor: 'rgba(0,0,0,0.3)',
                  p: 1.5,
                  borderRadius: 1,
                  overflow: 'auto',
                  maxHeight: 480,
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-all',
                }}
              >
                {task.tail.join('\n')}
              </Box>
            </Collapse>
          </CardContent>
        </Card>
      )}
    </Box>
  )
}
