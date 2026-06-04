import { useCallback, useEffect, useState } from 'react'
import {
  Box, Button, Card, CardContent, Chip, Dialog, DialogContent, DialogTitle,
  IconButton, InputBase, Stack, Switch, Typography, alpha,
} from '@mui/material'
import Grid from '@mui/material/Grid2'
import CloseIcon from '@mui/icons-material/Close'
import { PageHeader } from '../components/PageHeader'
import { postJson, getJson } from '../lib/api'
import { useApi } from '../lib/useApi'
import { consoleEndpoints } from '../config/endpoints'
import { StatusChip } from '../components/StatusChip'
import type {
  GoogleAccountStatus,
  GoogleIntegrationsSummary,
  GitHubIntegrationStatus,
  IntegrationsStatusResponse,
} from '../../types'

type Probe = { name: string; ok: boolean; status?: number; latency_ms?: number; target?: string; configured?: boolean }
type McpTool = { name: string; description: string; inputSchema?: { properties?: Record<string, unknown> } }
type RecentToolCall = { mcp_actual_tool?: string; mcp_tool?: string }
type McpResource = { name?: string; uri?: string; description?: string; mimeType?: string }

type AgentRuntime = {
  available?: boolean
  execution_available?: boolean
  backend?: string | null
  binary?: string | null
  executor_url?: string | null
  version?: string | null
  model?: string | null
  agents_count?: number
  skills_count?: number
  mcp_server_count?: number
  errors?: string[]
}

type VerificationTicket = {
  ticket_id: string
  summary?: string
  severity?: string
  status?: string
  authority?: string
  last_seen_at?: string
  details?: { examples?: string[] } | Record<string, unknown>
}

type VerificationSnapshot = {
  label?: string
  status?: string
  owner_agents?: string[]
  stale_after_minutes?: number
  latest?: {
    run_id?: string
    timestamp?: string
    passed?: number
    failed?: number
    total_tests?: number
    pass_rate?: number
    age_minutes?: number | null
  } | null
  tickets?: VerificationTicket[]
  auto_run?: {
    scheduled?: boolean
    reason?: string | null
    run_id?: string | null
  }
  task?: {
    running?: boolean
    trigger?: string
    run_id?: string
  }
}

type AutomationsStatus = {
  tickets_open?: number
  verification?: {
    'focus-priorities'?: VerificationSnapshot
  }
}

export type SystemPanelStatus = {
    integrations?: { probes?: Probe[] }
    mcp?: { tools?: McpTool[] }
    flags?: { system_enabled?: boolean; speech_input_enabled?: boolean }
    recent_tool_calls?: RecentToolCall[]
    mcp_resources?: { resources?: McpResource[] }
    repairs?: {
      agent_runtime?: AgentRuntime
    }
  } | null
type Props = {
  status: SystemPanelStatus
}
type FlagsResponse = { flags?: { system_enabled?: boolean; speech_input_enabled?: boolean } }
type AuthorizationResponse = { auth_url?: string; message?: string }
type GoogleImportResponse = { message?: string }

function verificationSeverity(status: string | undefined): 'ok' | 'warn' | 'bad' | 'default' {
  const value = String(status || '').toLowerCase()
  if (value === 'ok') return 'ok'
  if (value === 'failing') return 'bad'
  if (value === 'critical' || value === 'failed' || value === 'error') return 'bad'
  if (value === 'high' || value === 'warning' || value === 'running') return 'warn'
  if (value === 'missing' || value === 'stale') return 'warn'
  return 'default'
}

function formatAgeMinutes(ageMinutes: number | null | undefined): string | null {
  if (ageMinutes == null || !Number.isFinite(ageMinutes)) return null
  if (ageMinutes < 1) return '<1 min old'
  if (ageMinutes < 60) return `${ageMinutes.toFixed(1)} min old`
  const hours = ageMinutes / 60
  if (hours < 24) return `${hours.toFixed(1)} hr old`
  return `${(hours / 24).toFixed(1)} d old`
}

export default function SystemPanel({ status }: Props) {
  const [searchQ, setSearchQ] = useState('')
  const [activeTool, setActiveTool] = useState<string | null>(null)
  const [systemEnabled, setSystemEnabled] = useState(true)
  const [speechEnabled, setSpeechEnabled] = useState(true)
  const [googleStatus, setGoogleStatus] = useState<GoogleIntegrationsSummary | null>(null)
  const [githubStatus, setGithubStatus] = useState<GitHubIntegrationStatus | null>(null)
  const [controlError, setControlError] = useState<string | null>(null)
  const [integrationMessage, setIntegrationMessage] = useState<string | null>(null)
  const [integrationAuthUrl, setIntegrationAuthUrl] = useState<string | null>(null)
  const [importMessage, setImportMessage] = useState<string | null>(null)
  const [nowMs, setNowMs] = useState(() => Date.now())
  const { data: automations } = useApi<AutomationsStatus>(consoleEndpoints.automationsStatus, { pollMs: 10000 })

  const flags = status?.flags || {}
  useEffect(() => {
    let cancelled = false
    queueMicrotask(() => {
      if (cancelled) return
      setSystemEnabled(flags.system_enabled !== false)
      setSpeechEnabled(flags.speech_input_enabled !== false)
    })
    return () => { cancelled = true }
  }, [flags.system_enabled, flags.speech_input_enabled])

  const syncGoogle = useCallback(async () => {
    try {
      const j = await getJson<IntegrationsStatusResponse>(consoleEndpoints.integrationsStatus)
      setGoogleStatus(j.google || null)
      setGithubStatus(j.github || null)
    } catch {
      setGoogleStatus(null)
      setGithubStatus(null)
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    queueMicrotask(() => {
      if (!cancelled) void syncGoogle()
    })
    const t = setInterval(syncGoogle, 10000)
    return () => { cancelled = true; clearInterval(t) }
  }, [syncGoogle])

  useEffect(() => {
    const t = setInterval(() => setNowMs(Date.now()), 60000)
    return () => clearInterval(t)
  }, [])

  useEffect(() => {
    const onMessage = (event: MessageEvent) => {
      if (event.origin !== window.location.origin) return
      const data = event.data as { type?: string; success?: boolean; message?: string } | null
      if (!data || data.type !== 'archivist-google-oauth-complete') return
      setIntegrationAuthUrl(null)
      setIntegrationMessage(data.message || (data.success ? 'Authorization complete.' : 'Authorization failed.'))
      void syncGoogle()
    }
    window.addEventListener('message', onMessage)
    return () => window.removeEventListener('message', onMessage)
  }, [syncGoogle])

  const toggleSystem = async (checked: boolean) => {
    setControlError(null)
    try {
      const res = await postJson<FlagsResponse>(consoleEndpoints.flags, { flags: { system_enabled: checked, speech_input_enabled: checked ? speechEnabled : false } })
      const f = res.flags || {}
      setSystemEnabled(f.system_enabled !== false)
      setSpeechEnabled(f.speech_input_enabled !== false)
    } catch (error) {
      setControlError(error instanceof Error ? error.message : String(error))
    }
  }

  const toggleSpeech = async (checked: boolean) => {
    setControlError(null)
    try {
      const res = await postJson<FlagsResponse>(consoleEndpoints.flags, { flags: { speech_input_enabled: checked } })
      setSpeechEnabled(res.flags?.speech_input_enabled !== false)
    } catch (error) {
      setControlError(error instanceof Error ? error.message : String(error))
    }
  }

  const launchGoogleAuthorization = useCallback(async () => {
    setIntegrationMessage(null)
    setIntegrationAuthUrl(null)

    const popup = window.open('', 'archivist-google-auth', 'popup,width=540,height=720')
    if (popup) {
      try {
        popup.document.title = 'Archivist Google Authorization'
        popup.document.body.innerHTML = '<main style="font-family: Arial, sans-serif; padding: 24px; color: #0f172a;">Preparing Google authorization…</main>'
      } catch {
        // Ignore cross-window DOM write issues and continue with navigation.
      }
    }

    try {
      const j = await postJson<AuthorizationResponse>(consoleEndpoints.integrationsAuthorize, {})
      if (j.auth_url) {
        setIntegrationAuthUrl(j.auth_url)
        if (popup && !popup.closed) {
          popup.location.href = j.auth_url
          popup.focus()
          setIntegrationMessage(j.message || 'Continue authorization in the Google window.')
        } else {
          setIntegrationMessage('Popup blocked. Use the link below to continue authorization in this browser.')
        }
        return
      }
      if (popup && !popup.closed) popup.close()
      setIntegrationMessage(j.message || 'Authorization complete.')
      void syncGoogle()
    } catch (error) {
      if (popup && !popup.closed) popup.close()
      setIntegrationMessage(error instanceof Error ? error.message : String(error))
    }
  }, [syncGoogle])

  const probes = status?.integrations?.probes || []
  const agentRuntime = status?.repairs?.agent_runtime || {}
  const tools = (status?.mcp?.tools || []) as McpTool[]
  const filteredTools = tools.filter(t => {
    if (!searchQ) return true
    const q = searchQ.toLowerCase()
    return t.name?.toLowerCase().includes(q) || t.description?.toLowerCase().includes(q)
  })

  const selectedTool = tools.find(t => t.name === activeTool) || null
  const recentCalls = (status?.recent_tool_calls || []).filter(
    (c) => (c.mcp_actual_tool || c.mcp_tool) === activeTool
  )
  const resources = status?.mcp_resources?.resources || []

  const googleAccounts = googleStatus?.accounts || []
  const googleServiceSummary = googleStatus?.services || []
  const googleEnabledServices = googleStatus?.enabledServices || []
  const googleRequestedScopes = googleStatus?.requestedScopes || []
  const googleArchive = googleStatus?.archive
  const googleImport = googleStatus?.import
  const hasConnectedGoogleAccount = (googleStatus?.connectedAccountCount || 0) > 0
  const googleNeedsReauth = googleAccounts.some((account) =>
    account.services.some((service) => service.status === 'needs_auth')
  )
  const focusVerification = automations?.verification?.['focus-priorities'] || null
  const focusLatest = focusVerification?.latest || null
  const focusTickets = focusVerification?.tickets || []
  const focusRunning = Boolean(focusVerification?.task?.running)
  const focusAutoScheduled = Boolean(focusVerification?.auto_run?.scheduled)
  const focusExamples = focusTickets
    .flatMap((ticket) => Array.isArray(ticket.details?.examples) ? ticket.details.examples : [])
    .slice(0, 2)
  const focusSummary = [
    focusLatest?.total_tests != null ? `${focusLatest.passed || 0}/${focusLatest.total_tests} passing` : null,
    typeof focusLatest?.pass_rate === 'number' ? `${focusLatest.pass_rate.toFixed(0)}% pass rate` : null,
    formatAgeMinutes(focusLatest?.age_minutes),
  ].filter(Boolean).join(' · ')

  return (
    <Box>
      <PageHeader title="System" subtitle="Integrations, controls, and MCP tools" />

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, lg: 7 }}>
          <Card>
            <CardContent>
              <Typography variant="subtitle1" sx={{ fontWeight: 800, mb: 0.5 }}>Service Health</Typography>
              <Typography variant="caption" color="text.secondary" sx={{ mb: 1.5, display: 'block' }}>
                Probes, external services, and agent runtime status
              </Typography>

              <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)' }, gap: 1 }}>
                {probes.map(p => (
                  <Box
                    key={p.name}
                    sx={{
                      border: '1px solid', borderColor: 'divider', borderRadius: '8px',
                      p: 1.25, cursor: 'pointer', transition: 'border-color 0.15s',
                      '&:hover': { borderColor: 'rgba(148,163,184,0.28)' },
                    }}
                  >
                    <Stack direction="row" justifyContent="space-between" alignItems="center">
                      <Typography variant="body2" sx={{ fontWeight: 800, fontSize: '0.8125rem' }}>{p.name}</Typography>
                      <Chip size="small" label={p.ok ? 'OK' : 'FAIL'}
                        sx={{
                          height: 22, fontSize: '0.6875rem', fontWeight: 700,
                          bgcolor: p.ok ? 'rgba(45,212,191,0.10)' : 'rgba(239,68,68,0.10)',
                          color: p.ok ? '#c7f9e9' : '#fecaca',
                          border: '1px solid',
                          borderColor: p.ok ? 'rgba(45,212,191,0.35)' : 'rgba(239,68,68,0.35)',
                        }}
                      />
                    </Stack>
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                      {[p.status != null ? `HTTP ${p.status}` : null, p.latency_ms != null ? `${p.latency_ms}ms` : null, p.target].filter(Boolean).join(' · ')}
                    </Typography>
                  </Box>
                ))}
              </Box>

              <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid', borderColor: 'divider' }}>
                <Typography variant="overline" color="text.secondary" sx={{ mb: 1, display: 'block' }}>Regression Checks</Typography>
                <Box
                  data-testid="system-regression-focus-priorities"
                  sx={{ border: '1px solid', borderColor: 'divider', borderRadius: '8px', p: 1.25, bgcolor: alpha('#020617', 0.28) }}
                >
                  <Stack direction="row" justifyContent="space-between" alignItems="center">
                    <Box>
                      <Typography variant="body2" sx={{ fontWeight: 800, fontSize: '0.8125rem' }}>
                        {focusVerification?.label || 'Focus Priority Evals'}
                      </Typography>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.35 }}>
                        Manual-priority add/remove/reorder/query behavior and route-budget checks for the focus lane.
                      </Typography>
                    </Box>
                    <StatusChip
                      severity={verificationSeverity(focusVerification?.status)}
                      label={String(focusVerification?.status || 'unknown').toUpperCase()}
                    />
                  </Stack>
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 0.9, display: 'block' }}>
                    {focusSummary || 'No verification report has been captured yet.'}
                  </Typography>
                  <Stack direction="row" spacing={0.75} useFlexGap flexWrap="wrap" sx={{ mt: 1 }}>
                    {focusVerification?.owner_agents?.map((agentId) => (
                      <Chip key={agentId} size="small" label={`Owner ${agentId}`} variant="outlined" />
                    ))}
                    {focusRunning && <StatusChip severity="warn" label="Run active" />}
                    {focusAutoScheduled && (
                      <StatusChip severity="warn" label={`Auto-run ${focusVerification?.auto_run?.reason || 'scheduled'}`} />
                    )}
                    {typeof automations?.tickets_open === 'number' && (
                      <Chip size="small" label={`${automations.tickets_open} open ticket${automations.tickets_open === 1 ? '' : 's'}`} variant="outlined" />
                    )}
                  </Stack>
                  {focusTickets.length > 0 && (
                    <Stack spacing={0.75} sx={{ mt: 1.1 }}>
                      {focusTickets.slice(0, 3).map((ticket) => (
                        <Box
                          key={ticket.ticket_id}
                          sx={{
                            border: '1px solid',
                            borderColor: alpha('#94a3b8', 0.18),
                            borderRadius: '8px',
                            px: 1,
                            py: 0.85,
                            bgcolor: alpha('#0f172a', 0.32),
                          }}
                        >
                          <Stack direction="row" spacing={1} alignItems="center" justifyContent="space-between">
                            <Typography variant="caption" sx={{ fontWeight: 700, color: '#e2e8f0' }}>
                              {ticket.summary || ticket.ticket_id}
                            </Typography>
                            <StatusChip severity={verificationSeverity(ticket.severity || ticket.status)} label={ticket.severity || ticket.status || 'open'} />
                          </Stack>
                          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.35 }}>
                            {[ticket.authority, ticket.last_seen_at ? new Date(ticket.last_seen_at).toLocaleString() : null].filter(Boolean).join(' · ')}
                          </Typography>
                        </Box>
                      ))}
                    </Stack>
                  )}
                  {focusExamples.length > 0 && (
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                      Examples: {focusExamples.join(' · ')}
                    </Typography>
                  )}
                </Box>
              </Box>

              <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid', borderColor: 'divider' }}>
                <Typography variant="overline" color="text.secondary" sx={{ mb: 1, display: 'block' }}>External</Typography>
                <Box sx={{ border: '1px solid', borderColor: 'divider', borderRadius: '8px', p: 1.25 }}>
                  <Stack direction="row" justifyContent="space-between" alignItems="center">
                    <Typography variant="body2" sx={{ fontWeight: 800, fontSize: '0.8125rem' }}>Google Workspace</Typography>
                    <Chip size="small" label={googleStatus?.connected ? 'CONNECTED' : 'NOT CONNECTED'}
                      sx={{
                        height: 22, fontSize: '0.6875rem', fontWeight: 700,
                        bgcolor: googleStatus?.connected ? 'rgba(45,212,191,0.10)' : 'rgba(239,68,68,0.10)',
                        color: googleStatus?.connected ? '#c7f9e9' : '#fecaca',
                        border: '1px solid',
                        borderColor: googleStatus?.connected ? 'rgba(45,212,191,0.35)' : 'rgba(239,68,68,0.35)',
                      }}
                    />
                  </Stack>
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 0.75, display: 'block' }}>
                    {googleAccounts.length
                      ? `${googleStatus?.connectedAccountCount || 0} of ${googleAccounts.length} account${googleAccounts.length === 1 ? '' : 's'} connected`
                      : 'Read-only access only. Re-authorize after enabling additional Google services or scopes.'}
                  </Typography>
                  <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
                    <Button size="small" variant="contained" onClick={() => { void launchGoogleAuthorization() }}>
                      {googleAccounts.length
                        ? (googleNeedsReauth ? 'Re-authorize' : 'Re-authorize / add account')
                        : 'Authorize account'}
                    </Button>
                    <Button
                      size="small"
                      variant="outlined"
                      disabled={!hasConnectedGoogleAccount || !!googleImport?.running}
                      onClick={async () => {
                        setImportMessage(null)
                        try {
                          const j = await postJson<GoogleImportResponse>(consoleEndpoints.googleImport, {})
                          setImportMessage(j.message || 'Google history import started.')
                          void syncGoogle()
                        } catch (error) {
                          setImportMessage(error instanceof Error ? error.message : String(error))
                        }
                      }}
                    >
                      {googleImport?.running ? 'Importing…' : 'Import history'}
                    </Button>
                    <Button size="small" variant="outlined" onClick={() => { void syncGoogle() }}>Refresh</Button>
                  </Stack>
                  {googleServiceSummary.length ? (
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                      {googleServiceSummary.map((service) => `${service.name}: ${service.status}`).join(' · ')}
                    </Typography>
                  ) : null}
                  {googleEnabledServices.length ? (
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                      Requested services: {googleEnabledServices.map((service) => service.name).join(', ')}
                    </Typography>
                  ) : null}
                  {googleAccounts.length ? (
                    <Stack spacing={0.75} sx={{ mt: 1 }}>
                      {googleAccounts.map((account: GoogleAccountStatus) => (
                        <Box
                          key={account.id}
                          sx={{
                            border: '1px solid',
                            borderColor: 'divider',
                            borderRadius: '8px',
                            px: 1,
                            py: 0.75,
                            bgcolor: alpha('#0f172a', 0.18),
                          }}
                        >
                          <Typography variant="caption" sx={{ display: 'block', fontWeight: 700, color: account.connected ? '#c7f9e9' : '#fde68a' }}>
                            {account.account || account.label}
                          </Typography>
                          <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                            {account.services.map((service) => `${service.name}: ${service.status}`).join(' · ')}
                          </Typography>
                        </Box>
                      ))}
                    </Stack>
                  ) : null}
                  {googleArchive ? (
                    <Box
                      sx={{
                        mt: 1,
                        border: '1px solid',
                        borderColor: 'divider',
                        borderRadius: '8px',
                        px: 1,
                        py: 0.9,
                        bgcolor: alpha('#020617', 0.24),
                      }}
                    >
                      <Typography variant="caption" sx={{ display: 'block', fontWeight: 700, color: '#e2e8f0' }}>
                        Archive
                      </Typography>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.35 }}>
                        {googleArchive.available
                          ? `${googleArchive.gmailMessages} email message(s), ${googleArchive.calendarEvents} calendar event(s), ${googleArchive.driveFiles ?? 0} drive file(s), ${googleArchive.chatMessages ?? 0} chat message(s), ${googleArchive.dayCount} journal day(s)`
                          : 'No Google history imported yet.'}
                      </Typography>
                      {googleArchive.lastImportedAt ? (
                        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.35 }}>
                          Last import: {new Date(googleArchive.lastImportedAt).toLocaleString()}
                        </Typography>
                      ) : null}
                    </Box>
                  ) : null}
                  {googleImport ? (
                    <Typography
                      variant="caption"
                      sx={{
                        mt: 1,
                        display: 'block',
                        color: googleImport.running ? '#93c5fd' : '#cbd5e1',
                      }}
                    >
                      {googleImport.message || (googleImport.running ? 'Google history import is running.' : 'Google history import is idle.')}
                    </Typography>
                  ) : null}
                  {importMessage ? (
                    <Typography
                      variant="caption"
                      sx={{
                        mt: 0.5,
                        display: 'block',
                        color: importMessage.toLowerCase().includes('failed') ? '#fecaca' : '#c7f9e9',
                      }}
                    >
                      {importMessage}
                    </Typography>
                  ) : null}
                  {integrationMessage ? (
                    <Typography variant="caption" sx={{ mt: 1, display: 'block', color: integrationMessage.startsWith('Authorization') ? '#c7f9e9' : '#fde68a' }}>
                      {integrationMessage}
                    </Typography>
                  ) : null}
                  {googleRequestedScopes.length ? (
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block', wordBreak: 'break-all' }}>
                      OAuth scopes: {googleRequestedScopes.join(', ')}
                    </Typography>
                  ) : null}
                  {integrationAuthUrl ? (
                    <Box sx={{ mt: 1, p: 1, borderRadius: '8px', bgcolor: alpha('#020617', 0.6), border: '1px solid', borderColor: 'divider' }}>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.75 }}>
                        If Google blocks the popup, use this link to complete authorization on this machine.
                      </Typography>
                      <InputBase
                        value={integrationAuthUrl}
                        readOnly
                        sx={{
                          width: '100%',
                          fontSize: '0.74rem',
                          color: '#e2e8f0',
                          px: 1,
                          py: 0.75,
                          borderRadius: '6px',
                          bgcolor: alpha('#0f172a', 0.72),
                          border: '1px solid',
                          borderColor: alpha('#94a3b8', 0.2),
                        }}
                      />
                      <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
                        <Button
                          size="small"
                          variant="outlined"
                          onClick={async () => {
                            try {
                              await navigator.clipboard.writeText(integrationAuthUrl)
                              setIntegrationMessage('Authorization link copied. Paste it into Chrome or Firefox on this machine.')
                            } catch {
                              setIntegrationMessage('Copy failed. Select the link manually and open it in Chrome or Firefox on this machine.')
                            }
                          }}
                        >
                          Copy link
                        </Button>
                        <Button
                          size="small"
                          variant="outlined"
                          onClick={() => { window.location.assign(integrationAuthUrl) }}
                        >
                          Open here
                        </Button>
                      </Stack>
                    </Box>
                  ) : null}
                </Box>

                {/* GitHub integration */}
                <Box sx={{ border: '1px solid', borderColor: 'divider', borderRadius: '8px', p: 1.25, mt: 1 }}>
                  <Stack direction="row" justifyContent="space-between" alignItems="center">
                    <Typography variant="body2" sx={{ fontWeight: 800, fontSize: '0.8125rem' }}>GitHub</Typography>
                    <Chip size="small" label={githubStatus?.connected ? 'CONNECTED' : 'NOT CONFIGURED'}
                      sx={{
                        height: 22, fontSize: '0.6875rem', fontWeight: 700,
                        bgcolor: githubStatus?.connected ? 'rgba(45,212,191,0.10)' : 'rgba(239,68,68,0.10)',
                        color: githubStatus?.connected ? '#c7f9e9' : '#fecaca',
                        border: '1px solid',
                        borderColor: githubStatus?.connected ? 'rgba(45,212,191,0.35)' : 'rgba(239,68,68,0.35)',
                      }}
                    />
                  </Stack>
                  {githubStatus?.connected ? (
                    <>
                      <Typography variant="caption" color="text.secondary" sx={{ mt: 0.75, display: 'block' }}>
                        Authenticated as <strong style={{ color: '#e2e8f0' }}>{githubStatus.login}</strong>
                        {githubStatus.name ? ` (${githubStatus.name})` : ''}
                      </Typography>
                      {githubStatus.expires_at ? (() => {
                        const exp = new Date(githubStatus.expires_at)
                        const daysLeft = Math.ceil((exp.getTime() - nowMs) / 86400000)
                        const isWarning = daysLeft < 30
                        return (
                          <Typography variant="caption" sx={{
                            mt: 0.5, display: 'block',
                            color: isWarning ? '#fde68a' : '#94a3b8',
                          }}>
                            Token expires: {exp.toLocaleDateString()} ({daysLeft} days remaining)
                            {isWarning ? ' ⚠ Renew soon' : ''}
                          </Typography>
                        )
                      })() : null}
                      <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                        Scopes: {githubStatus.scopes || 'unknown'}
                      </Typography>
                      {githubStatus.rate_limit ? (
                        <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                          Rate limit: {githubStatus.rate_remaining?.toLocaleString()} / {githubStatus.rate_limit?.toLocaleString()} remaining
                        </Typography>
                      ) : null}
                    </>
                  ) : (
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 0.75, display: 'block' }}>
                      {githubStatus?.error || 'Set GITHUB_TOKEN environment variable to enable GitHub integration.'}
                    </Typography>
                  )}
                </Box>
              </Box>

              <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid', borderColor: 'divider' }}>
                <Typography variant="overline" color="text.secondary" sx={{ mb: 1, display: 'block' }}>Agent Runtime</Typography>
                <Box
                  data-testid="system-agents-integration"
                  sx={{ border: '1px solid', borderColor: 'divider', borderRadius: '8px', p: 1.25 }}
                >
                  <Stack direction="row" justifyContent="space-between" alignItems="center">
                    <Typography variant="body2" sx={{ fontWeight: 800, fontSize: '0.8125rem' }}>
                      Agent
                    </Typography>
                    <Chip
                      size="small"
                      label={agentRuntime.execution_available ? 'EXECUTOR ONLINE' : agentRuntime.available ? 'CATALOG ONLINE' : 'OFFLINE'}
                      sx={{
                        height: 22,
                        fontSize: '0.6875rem',
                        fontWeight: 700,
                        bgcolor: agentRuntime.available ? 'rgba(45,212,191,0.10)' : 'rgba(239,68,68,0.10)',
                        color: agentRuntime.available ? '#c7f9e9' : '#fecaca',
                        border: '1px solid',
                        borderColor: agentRuntime.available ? 'rgba(45,212,191,0.35)' : 'rgba(239,68,68,0.35)',
                      }}
                    />
                  </Stack>
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                    {agentRuntime.execution_available
                      ? 'Executor configured; catalog, skills, and MCP registry are loaded from /media/mass/agents'
                      : agentRuntime.available
                        ? 'Catalog mode; configure an agent executor only when live chat dispatch is needed'
                        : 'Shared agents repository unavailable'}
                  </Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                    {[
                      agentRuntime.backend || null,
                      agentRuntime.model ? `model ${agentRuntime.model}` : null,
                      agentRuntime.agents_count != null ? `${agentRuntime.agents_count} agents` : null,
                      agentRuntime.skills_count != null ? `${agentRuntime.skills_count} skills` : null,
                      agentRuntime.mcp_server_count != null ? `${agentRuntime.mcp_server_count} MCP` : null,
                      agentRuntime.version || null,
                    ].filter(Boolean).join(' · ') || 'No runtime metadata'}
                  </Typography>
                  {!agentRuntime.available && agentRuntime.errors?.[0] && (
                    <Typography variant="caption" sx={{ mt: 0.5, display: 'block', color: '#fecaca', wordBreak: 'break-all' }}>
                      {agentRuntime.errors[0]}
                    </Typography>
                  )}
                  {agentRuntime.available && agentRuntime.binary && (
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block', wordBreak: 'break-all' }}>
                      {agentRuntime.binary}
                    </Typography>
                  )}
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, lg: 5 }}>
          <Card>
            <CardContent>
              <Typography variant="subtitle1" sx={{ fontWeight: 800, mb: 0.5 }}>Controls</Typography>
              <Typography variant="caption" color="text.secondary" sx={{ mb: 1.5, display: 'block' }}>
                Safety switches for speech and system behavior
              </Typography>
              <Stack spacing={1.5}>
                <Box sx={{ border: '1px solid', borderColor: 'divider', borderRadius: '8px', p: 1.5, display: 'flex', gap: 1.5, alignItems: 'flex-start' }}>
                  <Switch checked={speechEnabled} onChange={(_, c) => toggleSpeech(c)} size="small" />
                  <Box>
                    <Typography variant="body2" sx={{ fontWeight: 800, fontSize: '0.8125rem' }}>Process incoming speech</Typography>
                    <Typography variant="caption" color="text.secondary">If off: ignores microphones/RTSP audio; web chat still works.</Typography>
                  </Box>
                </Box>
                <Box sx={{ border: '1px solid', borderColor: 'rgba(239,68,68,0.35)', borderRadius: '8px', p: 1.5, bgcolor: 'rgba(239,68,68,0.06)' }}>
                  <Typography variant="body2" sx={{ fontWeight: 800, color: '#fecaca', mb: 1, fontSize: '0.8125rem' }}>Danger zone</Typography>
                  <Box sx={{ display: 'flex', gap: 1.5, alignItems: 'flex-start' }}>
                    <Switch checked={systemEnabled} onChange={(_, c) => toggleSystem(c)} size="small" />
                    <Box>
                      <Typography variant="body2" sx={{ fontWeight: 800, fontSize: '0.8125rem' }}>Enable system</Typography>
                      <Typography variant="caption" color="text.secondary">If off: disables speech + commands + reminders.</Typography>
                    </Box>
                  </Box>
                </Box>
                <Typography variant="caption" color="text.secondary">Changes apply immediately and persist across restarts.</Typography>
                {controlError ? (
                  <Typography variant="caption" color="error">{controlError}</Typography>
                ) : null}
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={12}>
          <Card>
            <CardContent>
              <Typography variant="subtitle1" sx={{ fontWeight: 800, mb: 0.5 }}>MCP Tools</Typography>
              <Typography variant="caption" color="text.secondary" sx={{ mb: 1.5, display: 'block' }}>
                Search + click for schema details
              </Typography>
              <InputBase
                placeholder="Search tools..."
                value={searchQ}
                onChange={e => setSearchQ(e.target.value)}
                sx={{
                  mb: 1.5, px: 1.5, py: 0.75, borderRadius: '8px', width: '100%',
                  bgcolor: (t) => alpha(t.palette.common.white, 0.04),
                  border: '1px solid', borderColor: 'divider', fontSize: '0.875rem',
                }}
              />
              <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 1 }}>
                {filteredTools.map(t => (
                  <Box
                    key={t.name}
                    onClick={() => setActiveTool(t.name)}
                    sx={{
                      border: '1px solid', borderColor: 'divider', borderRadius: '8px',
                      p: 1.25, cursor: 'pointer', minHeight: 72,
                      display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
                      transition: 'border-color 0.15s, transform 0.15s, box-shadow 0.15s',
                      '&:hover': { borderColor: 'rgba(148,163,184,0.28)', transform: 'translateY(-1px)', boxShadow: '0 4px 12px rgba(0,0,0,0.2)' },
                    }}
                  >
                    <Typography variant="body2" sx={{ fontWeight: 800, fontSize: '0.8125rem' }}>{t.name}</Typography>
                    <Typography variant="caption" color="text.secondary" sx={{
                      mt: 0.5, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden',
                    }}>{t.description}</Typography>
                    <Stack direction="row" justifyContent="space-between" sx={{ mt: 1 }}>
                      <Chip size="small" label={`${Object.keys(t.inputSchema?.properties || {}).length} fields`}
                        sx={{ height: 22, fontSize: '0.6875rem' }} />
                      <Chip size="small" label="Open" sx={{ height: 22, fontSize: '0.6875rem' }} />
                    </Stack>
                  </Box>
                ))}
                {!filteredTools.length && (
                  <Typography variant="body2" color="text.secondary">No tools found.</Typography>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Dialog open={!!activeTool} onClose={() => setActiveTool(null)} maxWidth="md" fullWidth>
        <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box>
            <Typography variant="h6" sx={{ fontWeight: 800 }}>{activeTool || 'Tool'}</Typography>
            <Typography variant="caption" color="text.secondary">{selectedTool?.description}</Typography>
          </Box>
          <IconButton onClick={() => setActiveTool(null)}><CloseIcon /></IconButton>
        </DialogTitle>
        <DialogContent>
          {selectedTool && (
            <Stack spacing={2}>
              <Box>
                <Typography variant="overline" color="text.secondary">Fields</Typography>
                <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                  {Object.keys(selectedTool.inputSchema?.properties || {}).join(', ') || '(none)'}
                </Typography>
              </Box>
              <Box>
                <Typography variant="overline" color="text.secondary">Schema</Typography>
                <Box component="pre" sx={{
                  fontFamily: 'monospace', fontSize: '0.75rem', whiteSpace: 'pre-wrap',
                  p: 1.5, borderRadius: '8px', bgcolor: 'rgba(2,6,23,0.35)', border: '1px solid', borderColor: 'divider',
                  maxHeight: 300, overflow: 'auto',
                }}>
                  {JSON.stringify(selectedTool.inputSchema, null, 2)}
                </Box>
              </Box>
              {resources.length > 0 && (
                <Box>
                  <Typography variant="overline" color="text.secondary">Resources ({resources.length})</Typography>
                  <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 1, mt: 0.5 }}>
                    {resources.slice(0, 12).map((r, i: number) => (
                      <Box key={i} sx={{ border: '1px solid', borderColor: 'divider', borderRadius: '8px', p: 1 }}>
                        <Typography variant="body2" sx={{ fontWeight: 700, fontSize: '0.8125rem' }}>{r.name || r.uri}</Typography>
                        <Typography variant="caption" color="text.secondary">{r.description || r.mimeType}</Typography>
                      </Box>
                    ))}
                  </Box>
                </Box>
              )}
              {recentCalls.length > 0 && (
                <Box>
                  <Typography variant="overline" color="text.secondary">Recent Calls</Typography>
                  <Box component="pre" sx={{
                    fontFamily: 'monospace', fontSize: '0.75rem', whiteSpace: 'pre-wrap',
                    p: 1.5, borderRadius: '8px', bgcolor: 'rgba(2,6,23,0.35)', border: '1px solid', borderColor: 'divider',
                    maxHeight: 200, overflow: 'auto',
                  }}>
                    {JSON.stringify(recentCalls.slice(-20), null, 2)}
                  </Box>
                </Box>
              )}
            </Stack>
          )}
        </DialogContent>
      </Dialog>
    </Box>
  )
}
