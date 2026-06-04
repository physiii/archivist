import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Collapse,
  Dialog,
  DialogContent,
  DialogTitle,
  IconButton,
  InputBase,
  Stack,
  Tab,
  Tabs,
  Typography,
} from '@mui/material'
import CloseIcon from '@mui/icons-material/Close'
import SendIcon from '@mui/icons-material/Send'

import { useApi } from '../lib/useApi'
import { notifyAgentSessionsChanged } from '../lib/agentSessions'
import { KpiRow } from '../components/KpiRow'
import { DataTable } from '../components/DataTable'
import { StatusChip } from '../components/StatusChip'
import { PageHeader } from '../components/PageHeader'
import MarkdownMessage from '../../components/MarkdownMessage'
import { consoleEndpoints } from '../config/endpoints'

type FleetLaneId = 'system' | 'specialist' | string

interface Finding {
  ticket_id: string
  title: string
  category: string
  severity: string
  status: string
  created_at: string
}

interface ActivityEntry {
  timestamp: string
  action: string
  detail: string
}

interface DispatchedActivity {
  action: string
  detail: string
  executor: string
  result: string
  timestamp: string
}

interface AgentStats {
  critical: number
  high: number
  open: number
  fixed: number
}

interface Ticket {
  ticket_id: string
  summary?: string
  title?: string
  status: string
  severity?: string
  authority?: string
  kind?: string
  issue_code?: string
  source_location?: string
  occurrence_count?: number
  category?: string
  created_at: string
  updated_at?: string
  first_seen_at?: string
  last_seen_at?: string
  details?: Record<string, unknown>
  failure_signature?: Record<string, unknown>
  evidence_paths?: string[]
  sample_outputs?: string[]
  source_session_ids?: string[]
}

interface Agent {
  id: string
  name: string
  description: string
  status: string
  role?: string
  summary?: string
  workspace?: string
  registered?: boolean
  group_label?: string
  lane?: FleetLaneId
  score?: number
  eval_score?: number
  score_summary?: string
  eval_summary?: string
  chat_enabled?: boolean
  stats: AgentStats
  findings: Finding[]
  recent_activity: ActivityEntry[]
  activity: DispatchedActivity[]
  tickets?: Ticket[]
}

interface FleetSummary {
  active_agents?: number
  total_findings?: number
  open_findings?: number
  open_tickets?: number
  critical_findings?: number
  operational_score?: number
  eval_score?: number
  avg_score?: number
  avg_eval_score?: number
}

interface FleetLane {
  id: FleetLaneId
  label: string
  description?: string
  summary?: FleetSummary
  agents: Agent[]
}

interface FleetData {
  fleet_summary?: FleetSummary
  agents?: Agent[]
  lanes?: Record<string, Partial<FleetLane>> | Array<Partial<FleetLane>>
  system?: Partial<FleetLane>
  specialist?: Partial<FleetLane>
}

interface RepairRun {
  ticket_id: string
  artifact: string
  modified: string
}

interface AutomationsData {
  ok: boolean
  tickets_open: number
  tickets: Ticket[]
  experiments: { completed: string[]; current: string | null }
  repair_runs: RepairRun[]
}

type ChatMessage = {
  id: string
  role: 'user' | 'assistant' | 'system'
  text: string
  ts: number
}

function severityToChip(severity: string): 'ok' | 'warn' | 'bad' | 'default' {
  const s = severity.toLowerCase()
  if (s === 'critical') return 'bad'
  if (s === 'high') return 'warn'
  if (s === 'fixed' || s === 'resolved' || s === 'pass') return 'ok'
  return 'default'
}

function statusDotColor(status: string): string {
  const s = status.toLowerCase()
  if (s === 'running' || s === 'active' || s === 'success') return '#22c55e'
  if (s === 'idle' || s === 'degraded' || s === 'attention') return '#f59e0b'
  if (s === 'failed' || s === 'error' || s === 'critical' || s === 'blocked') return '#ef4444'
  return '#64748b'
}

function laneLabel(id: FleetLaneId): string {
  if (id === 'system') return 'System'
  if (id === 'specialist') return 'Specialist'
  const text = String(id || 'agents').replace(/[_-]+/g, ' ').trim()
  return text ? text.replace(/\b\w/g, (m) => m.toUpperCase()) : 'Agents'
}

function laneDescription(id: FleetLaneId): string {
  if (id === 'system') {
    return 'System agents are the durable control plane. They own operator chat, health, repair, observation, and verification.'
  }
  if (id === 'specialist') {
    return 'Specialist agents are runtime experts for specific product or domain lanes.'
  }
  return 'This lane contains application-specific fleet roles derived from the backend roster.'
}

function normalizeAgent(raw: Partial<Agent>, fallbackLane: FleetLaneId): Agent {
  return {
    id: String(raw.id || ''),
    name: String(raw.name || raw.id || 'Unnamed Agent'),
    description: String(raw.description || raw.summary || ''),
    status: String(raw.status || 'unknown'),
    role: raw.role ? String(raw.role) : undefined,
    summary: raw.summary ? String(raw.summary) : undefined,
    workspace: raw.workspace ? String(raw.workspace) : undefined,
    registered: raw.registered == null ? undefined : Boolean(raw.registered),
    group_label: raw.group_label ? String(raw.group_label) : undefined,
    lane: raw.lane ? String(raw.lane) : fallbackLane,
    score: typeof raw.score === 'number' ? raw.score : undefined,
    eval_score: typeof raw.eval_score === 'number' ? raw.eval_score : undefined,
    score_summary: raw.score_summary ? String(raw.score_summary) : undefined,
    eval_summary: raw.eval_summary ? String(raw.eval_summary) : undefined,
    chat_enabled: raw.chat_enabled == null ? undefined : Boolean(raw.chat_enabled),
    stats: {
      critical: Number(raw.stats?.critical || 0),
      high: Number(raw.stats?.high || 0),
      open: Number(raw.stats?.open || 0),
      fixed: Number(raw.stats?.fixed || 0),
    },
    findings: Array.isArray(raw.findings) ? raw.findings as Finding[] : [],
    recent_activity: Array.isArray(raw.recent_activity) ? raw.recent_activity as ActivityEntry[] : [],
    activity: Array.isArray(raw.activity) ? raw.activity as DispatchedActivity[] : [],
    tickets: Array.isArray(raw.tickets) ? raw.tickets as Ticket[] : [],
  }
}

function normalizeLane(raw: Partial<FleetLane> | undefined, fallbackId: FleetLaneId): FleetLane {
  const id = String(raw?.id || fallbackId) as FleetLaneId
  return {
    id,
    label: String(raw?.label || laneLabel(id)),
    description: raw?.description ? String(raw.description) : laneDescription(id),
    summary: raw?.summary ? raw.summary as FleetSummary : undefined,
    agents: Array.isArray(raw?.agents) ? raw.agents!.map((agent) => normalizeAgent(agent, id)) : [],
  }
}

function normalizeFleetLanes(fleet: FleetData | undefined | null): FleetLane[] {
  if (!fleet) return []

  if (Array.isArray(fleet.lanes) && fleet.lanes.length > 0) {
    return fleet.lanes.map((lane, index) => normalizeLane(lane, index === 0 ? 'system' : `lane-${index}`))
  }

  if (fleet.lanes && typeof fleet.lanes === 'object') {
    const entries = Object.entries(fleet.lanes)
    if (entries.length > 0) {
      return entries.map(([laneId, lane]) => normalizeLane({ ...lane, id: lane.id || laneId }, laneId))
    }
  }

  const explicit: FleetLane[] = []
  if (fleet.system) explicit.push(normalizeLane({ ...fleet.system, id: fleet.system.id || 'system' }, 'system'))
  if (fleet.specialist) explicit.push(normalizeLane({ ...fleet.specialist, id: fleet.specialist.id || 'specialist' }, 'specialist'))
  if (explicit.length > 0) return explicit

  const flatAgents = Array.isArray(fleet.agents) ? fleet.agents.map((agent) => normalizeAgent(agent, 'system')) : []
  const grouped = new Map<FleetLaneId, Agent[]>()
  for (const agent of flatAgents) {
    const key = agent.lane || 'system'
    grouped.set(key, [...(grouped.get(key) || []), agent])
  }
  if (grouped.size > 1) {
    return Array.from(grouped.entries()).map(([id, agents]) => ({
      id,
      label: laneLabel(id),
      description: laneDescription(id),
      agents,
      summary: undefined,
    }))
  }
  return flatAgents.length > 0
    ? [{
        id: 'system',
        label: 'System',
        description: 'Flat fleet payload. Treat as a single fleet lane unless the backend separates system and specialist roles.',
        agents: flatAgents,
        summary: fleet.fleet_summary,
      }]
    : []
}

function uniqueTickets(tickets: Ticket[]): Ticket[] {
  const seen = new Set<string>()
  const rows: Ticket[] = []
  for (const ticket of tickets) {
    const key = String(ticket.ticket_id || '')
    if (!key || seen.has(key)) continue
    seen.add(key)
    rows.push(ticket)
  }
  return rows
}

function ticketsForAgent(agent: Agent, tickets: Ticket[]): Ticket[] {
  const scoped = tickets.filter((ticket) => {
    const authority = String(ticket.authority || '')
    return authority === agent.id || String(ticket.ticket_id || '').startsWith(`${agent.id}:`)
  })
  return uniqueTickets([...(agent.tickets || []), ...scoped]).slice(0, 12)
}

function deriveLaneSummary(lane: FleetLane, tickets: Ticket[]): FleetSummary {
  const findings = lane.agents.flatMap((agent) => agent.findings || [])
  const scopedTickets = uniqueTickets(lane.agents.flatMap((agent) => ticketsForAgent(agent, tickets)))
  const explicit = lane.summary || {}
  const criticalFindings = findings.filter((finding) => String(finding.severity || '').toLowerCase() === 'critical').length
  const criticalTickets = scopedTickets.filter((ticket) => String(ticket.severity || '').toLowerCase() === 'critical').length
  return {
    active_agents: explicit.active_agents ?? lane.agents.length,
    total_findings: explicit.total_findings ?? findings.length,
    open_tickets: explicit.open_tickets ?? explicit.open_findings ?? scopedTickets.length,
    critical_findings: explicit.critical_findings ?? (criticalFindings + criticalTickets),
    operational_score: explicit.operational_score,
    eval_score: explicit.eval_score ?? explicit.avg_eval_score,
    avg_score: explicit.avg_score,
  }
}

function formatTimestamp(ts: number): string {
  if (!ts) return ''
  return new Date(ts).toLocaleString()
}

async function sendAgentChatStream(agent: Agent, text: string, laneId: FleetLaneId): Promise<ChatMessage[]> {
  const response = await fetch(consoleEndpoints.agentChat, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message: text,
      sessionId: consoleEndpoints.systemAgentSessionRef(agent.id),
      surface: 'console',
      historyScope: `fleet-${String(laneId || 'system')}`,
      context: {
        page: 'Fleet',
        lane: String(laneId || 'system'),
        agent_id: agent.id,
        agent_name: agent.name,
      },
    }),
  })
  if (!response.ok) throw new Error(`HTTP ${response.status}`)
  if (!response.body) return []

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let accumulated = ''
  let currentEvent = ''
  let fullText = ''
  const emitted: ChatMessage[] = []

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    accumulated += decoder.decode(value, { stream: true })
    const lines = accumulated.split('\n')
    accumulated = lines.pop() || ''
    for (const line of lines) {
      if (line.startsWith('event: ')) currentEvent = line.slice(7).trim()
      else if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6))
        if (currentEvent === 'text' && data.text) fullText += String(data.text)
        if (currentEvent === 'system' && data.text) {
          emitted.push({ id: `sys-${Date.now()}-${emitted.length}`, role: 'system', text: String(data.text), ts: Date.now() })
        }
        if (currentEvent === 'error' && data.message) throw new Error(String(data.message))
      }
    }
  }

  if (fullText.trim()) {
    emitted.push({ id: `a-${Date.now()}`, role: 'assistant', text: fullText.trim(), ts: Date.now() })
  }
  return emitted
}

function AgentChatPanel({
  messages,
  input,
  onInputChange,
  onSend,
  busy,
  error,
  helperText,
  placeholder,
}: {
  messages: ChatMessage[]
  input: string
  onInputChange: (value: string) => void
  onSend: () => void
  busy: boolean
  error: string | null
  helperText: string
  placeholder: string
}) {
  return (
    <Box>
      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
        {helperText}
      </Typography>
      <Box
        sx={{
          border: '1px solid',
          borderColor: 'divider',
          borderRadius: 2,
          bgcolor: 'rgba(255,255,255,0.02)',
          p: 1,
          minHeight: 220,
          maxHeight: 320,
          overflowY: 'auto',
        }}
      >
        <Stack spacing={1}>
          {messages.map((message) => (
            <Box
              key={message.id}
              sx={{
                alignSelf: message.role === 'user' ? 'flex-end' : 'stretch',
                maxWidth: '92%',
              }}
            >
              <Box
                sx={{
                  px: 1.25,
                  py: 0.9,
                  borderRadius: 1.5,
                  bgcolor:
                    message.role === 'user'
                      ? 'rgba(59,130,246,0.18)'
                      : message.role === 'assistant'
                        ? 'rgba(255,255,255,0.05)'
                        : 'rgba(245,158,11,0.12)',
                  border: '1px solid',
                  borderColor:
                    message.role === 'user'
                      ? 'rgba(59,130,246,0.35)'
                      : message.role === 'assistant'
                        ? 'rgba(255,255,255,0.08)'
                        : 'rgba(245,158,11,0.25)',
                }}
              >
                <MarkdownMessage text={message.text} fontSize="0.82rem" />
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                  {formatTimestamp(message.ts)}
                </Typography>
              </Box>
            </Box>
          ))}
          {messages.length === 0 && (
            <Typography variant="caption" color="text.secondary">
              No messages yet.
            </Typography>
          )}
        </Stack>
      </Box>
      <Box
        sx={{
          mt: 1,
          border: '1px solid',
          borderColor: 'divider',
          borderRadius: 2,
          bgcolor: 'rgba(255,255,255,0.02)',
          px: 1,
          py: 0.5,
        }}
      >
        <Stack direction="row" spacing={1} alignItems="center">
          <InputBase
            value={input}
            onChange={(event) => onInputChange(event.target.value)}
            placeholder={placeholder}
            sx={{ flex: 1, fontSize: '0.875rem' }}
            onKeyDown={(event) => {
              if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault()
                onSend()
              }
            }}
          />
          <Button
            size="small"
            variant="contained"
            onClick={onSend}
            disabled={busy || !input.trim()}
            startIcon={<SendIcon fontSize="small" />}
          >
            Send
          </Button>
        </Stack>
      </Box>
      {error && (
        <Typography variant="caption" sx={{ display: 'block', mt: 0.75, color: '#fecaca' }}>
          {error}
        </Typography>
      )}
    </Box>
  )
}

type AgentFleetProps = {
  embedded?: boolean
}

export default function AgentFleetPanel({ embedded = false }: AgentFleetProps) {
  const { data: fleet } = useApi<FleetData>(consoleEndpoints.agentsFleet, { pollMs: 8000 })
  const { data: automations } = useApi<AutomationsData>(consoleEndpoints.automationsStatus, { pollMs: 8000 })

  const [selectedLaneId, setSelectedLaneId] = useState<FleetLaneId>('system')
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null)
  const [detailTab, setDetailTab] = useState(0)
  const [repairRunsOpen, setRepairRunsOpen] = useState(false)
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([])
  const [chatInput, setChatInput] = useState('')
  const [chatBusy, setChatBusy] = useState(false)
  const [chatError, setChatError] = useState<string | null>(null)

  const lanes = useMemo(() => normalizeFleetLanes(fleet), [fleet])
  const tickets = useMemo(() => automations?.tickets ?? [], [automations])
  const experiments = automations?.experiments
  const repairRuns = automations?.repair_runs ?? []

  useEffect(() => {
    if (lanes.length === 0) return
    if (!lanes.some((lane) => lane.id === selectedLaneId)) {
      setSelectedLaneId(lanes[0].id)
    }
  }, [lanes, selectedLaneId])

  const activeLane = useMemo(() => {
    if (lanes.length === 0) return null
    return lanes.find((lane) => lane.id === selectedLaneId) || lanes[0]
  }, [lanes, selectedLaneId])

  useEffect(() => {
    if (!activeLane) {
      setSelectedAgentId(null)
      return
    }
    if (!activeLane.agents.some((agent) => agent.id === selectedAgentId)) {
      setSelectedAgentId(null)
      setDetailTab(0)
    }
  }, [activeLane, selectedAgentId])

  const selectedAgent = useMemo(() => (
    activeLane?.agents.find((agent) => agent.id === selectedAgentId) || null
  ), [activeLane, selectedAgentId])

  const laneSummary = useMemo(() => (
    activeLane ? deriveLaneSummary(activeLane, tickets) : null
  ), [activeLane, tickets])

  const selectedAgentTickets = useMemo(() => (
    selectedAgent ? ticketsForAgent(selectedAgent, tickets) : []
  ), [selectedAgent, tickets])

  useEffect(() => {
    setChatMessages([])
    setChatInput('')
    setChatError(null)
    setChatBusy(false)
  }, [activeLane?.id, selectedAgent?.id])

  const sendAgentChat = useCallback(async () => {
    if (!selectedAgent || !activeLane) return
    const text = chatInput.trim()
    if (!text || chatBusy) return
    setChatBusy(true)
    setChatError(null)
    try {
      const userMessage: ChatMessage = { id: `u-${Date.now()}`, role: 'user', text, ts: Date.now() }
      setChatMessages((prev) => [...prev, userMessage])
      const streamed = await sendAgentChatStream(selectedAgent, text, activeLane.id)
      setChatInput('')
      if (streamed.length > 0) {
        setChatMessages((prev) => [...prev, ...streamed])
      }
    } catch (error) {
      setChatError(String(error))
    } finally {
      setChatBusy(false)
      notifyAgentSessionsChanged()
    }
  }, [activeLane, chatBusy, chatInput, selectedAgent])

  const showSystemSections = !activeLane || lanes.length <= 1 || activeLane.id === 'system'
  const showAgentChat = Boolean(selectedAgent && selectedAgent.chat_enabled !== false)

  const summaryScoreChips = [
    laneSummary?.operational_score != null ? `Operational ${laneSummary.operational_score}` : null,
    laneSummary?.eval_score != null ? `Eval ${laneSummary.eval_score}` : null,
    laneSummary?.avg_score != null ? `Avg ${laneSummary.avg_score}` : null,
  ].filter(Boolean) as string[]

  return (
    <Box data-testid={embedded ? 'console-fleet-panel' : 'agent-fleet-page'}>
      {!embedded && (
        <PageHeader
          title="Agent Fleet"
          subtitle="System agents and specialist agents across the Archivist fleet"
        />
      )}

      {embedded && (
        <Box sx={{ mb: 2 }}>
          <Typography variant="h6" sx={{ fontWeight: 800 }}>
            Fleet
          </Typography>
          <Typography variant="caption" color="text.secondary">
            System and specialist lanes, repair queue, and agent activity
          </Typography>
        </Box>
      )}

      <Card sx={{ border: '1px solid', borderColor: 'divider' }}>
        <CardContent>
          <Stack
            direction={{ xs: 'column', md: 'row' }}
            spacing={1}
            justifyContent="space-between"
            alignItems={{ xs: 'flex-start', md: 'center' }}
            sx={{ mb: 1.25 }}
          >
            <Box>
              <Typography variant="subtitle1" sx={{ fontWeight: 800 }}>
                Fleet Summary
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {activeLane?.description || 'Inspect the current system or specialist lane.'}
              </Typography>
            </Box>
            {lanes.length > 1 && (
              <Stack direction="row" spacing={0.75}>
                {lanes.map((lane) => (
                  <Button
                    key={String(lane.id)}
                    size="small"
                    variant={activeLane?.id === lane.id ? 'contained' : 'outlined'}
                    onClick={() => {
                      setSelectedLaneId(lane.id)
                      setSelectedAgentId(null)
                      setDetailTab(0)
                    }}
                  >
                    {lane.label} {lane.agents.length}
                  </Button>
                ))}
              </Stack>
            )}
          </Stack>

          <KpiRow
            items={[
              { label: 'Active Agents', value: laneSummary?.active_agents ?? 0, color: (laneSummary?.active_agents || 0) > 0 ? 'good' : 'default' },
              { label: 'Findings', value: laneSummary?.total_findings ?? 0 },
              { label: 'Open Tickets', value: laneSummary?.open_tickets ?? 0, color: (laneSummary?.open_tickets || 0) > 0 ? 'warn' : 'default' },
              { label: 'Critical', value: laneSummary?.critical_findings ?? 0, color: (laneSummary?.critical_findings || 0) > 0 ? 'bad' : 'default' },
            ]}
          />

          {summaryScoreChips.length > 0 && (
            <Stack direction="row" spacing={0.75} useFlexGap flexWrap="wrap" sx={{ mt: 0.5 }}>
              {summaryScoreChips.map((chip) => (
                <Chip key={chip} size="small" label={chip} variant="outlined" />
              ))}
            </Stack>
          )}
        </CardContent>
      </Card>

      <Typography variant="overline" color="text.secondary" sx={{ mt: 3, mb: 1, display: 'block' }}>
        {activeLane?.label || 'Agents'}
      </Typography>

      <Box
        data-testid="fleet-agent-grid"
        sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 1.5 }}
      >
        {(activeLane?.agents || []).map((agent) => (
          <Card
            key={agent.id}
            data-testid={`fleet-agent-card-${agent.id}`}
            onClick={() => {
              setSelectedAgentId(selectedAgent?.id === agent.id ? null : agent.id)
              setDetailTab(0)
            }}
            sx={{
              cursor: 'pointer',
              border: '1px solid',
              borderColor: selectedAgent?.id === agent.id ? 'primary.main' : 'divider',
              transition: 'border-color 0.15s',
              '&:hover': { borderColor: 'primary.dark' },
            }}
          >
            <CardContent sx={{ pb: '12px !important' }}>
              <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 0.5 }}>
                <Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: statusDotColor(agent.status), flexShrink: 0 }} />
                <Typography variant="subtitle2" noWrap>{agent.name}</Typography>
                {agent.group_label && (
                  <Chip size="small" label={agent.group_label} variant="outlined" sx={{ height: 20, fontSize: '0.65rem' }} />
                )}
              </Stack>
              {agent.role && (
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                  {agent.role}
                </Typography>
              )}
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1, minHeight: 32 }}>
                {agent.description}
              </Typography>
              <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
                {agent.stats.critical > 0 && <StatusChip severity="bad" label={`${agent.stats.critical} crit`} />}
                {agent.stats.high > 0 && <StatusChip severity="warn" label={`${agent.stats.high} high`} />}
                {agent.stats.open > 0 && <StatusChip severity="default" label={`${agent.stats.open} open`} />}
                {agent.stats.fixed > 0 && <StatusChip severity="ok" label={`${agent.stats.fixed} fixed`} />}
              </Stack>
            </CardContent>
          </Card>
        ))}
      </Box>

      {activeLane && activeLane.agents.length === 0 && (
        <Card sx={{ mt: 2, border: '1px solid', borderColor: 'divider' }}>
          <CardContent>
            <Typography variant="body2" color="text.secondary">
              No agents are available in the {activeLane.label.toLowerCase()} lane.
            </Typography>
          </CardContent>
        </Card>
      )}

      <Dialog
        open={selectedAgent !== null}
        onClose={() => setSelectedAgentId(null)}
        fullWidth
        maxWidth="lg"
        PaperProps={{ sx: { border: '1px solid', borderColor: 'divider' } }}
      >
        {selectedAgent && (
          <>
            <DialogTitle sx={{ pb: 1 }}>
              <Stack direction="row" spacing={1} alignItems="center">
                <Typography variant="subtitle1" fontWeight={700}>
                  {selectedAgent.name}
                </Typography>
                <Chip size="small" label={activeLane?.label || 'Agent'} variant="outlined" sx={{ height: 22 }} />
                <Box sx={{ flex: 1 }} />
                <Chip size="small" label={selectedAgent.status} variant="outlined" sx={{ height: 22 }} />
                <IconButton size="small" onClick={() => setSelectedAgentId(null)} aria-label="Close agent details">
                  <CloseIcon fontSize="small" />
                </IconButton>
              </Stack>
            </DialogTitle>
            <DialogContent sx={{ pt: 0 }}>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1.25 }}>
                {selectedAgent.summary || selectedAgent.description}
              </Typography>

              <Tabs value={detailTab} onChange={(_, value) => setDetailTab(value)} sx={{ mb: 1.5, minHeight: 36 }}>
                <Tab label="Overview" sx={{ minHeight: 36, py: 0 }} />
                <Tab label="Findings" sx={{ minHeight: 36, py: 0 }} />
                <Tab label="Activity" sx={{ minHeight: 36, py: 0 }} />
                <Tab label="Tickets" sx={{ minHeight: 36, py: 0 }} />
                {showAgentChat && <Tab label="Chat" sx={{ minHeight: 36, py: 0 }} />}
              </Tabs>

              {detailTab === 0 && (
                <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' }, gap: 1 }}>
                  {[
                    ['Lane', activeLane?.label || 'Agent'],
                    ['Role', selectedAgent.role || 'Not provided'],
                    ['Workspace', selectedAgent.workspace || 'Not provided'],
                    ['Registered', selectedAgent.registered == null ? 'Unknown' : selectedAgent.registered ? 'Yes' : 'No'],
                    ['Operational Score', selectedAgent.score == null ? 'Not provided' : String(selectedAgent.score)],
                    ['Eval Score', selectedAgent.eval_score == null ? 'Not provided' : String(selectedAgent.eval_score)],
                  ].map(([key, value]) => (
                    <Box key={key}>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                        {key}
                      </Typography>
                      <Typography variant="body2">
                        {value}
                      </Typography>
                    </Box>
                  ))}
                </Box>
              )}

              {detailTab === 1 && (
                <DataTable>
                  <table>
                    <thead>
                      <tr>
                        <th>Ticket</th>
                        <th>Title</th>
                        <th>Category</th>
                        <th>Severity</th>
                        <th>Status</th>
                        <th>Created</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedAgent.findings.map((finding) => (
                        <tr key={finding.ticket_id}>
                          <td>{finding.ticket_id}</td>
                          <td>{finding.title}</td>
                          <td>{finding.category}</td>
                          <td><StatusChip severity={severityToChip(finding.severity)} label={finding.severity} /></td>
                          <td><StatusChip severity={severityToChip(finding.status)} label={finding.status} /></td>
                          <td>{finding.created_at}</td>
                        </tr>
                      ))}
                      {selectedAgent.findings.length === 0 && (
                        <tr><td colSpan={6} style={{ textAlign: 'center', opacity: 0.5 }}>No findings</td></tr>
                      )}
                    </tbody>
                  </table>
                </DataTable>
              )}

              {detailTab === 2 && (
                <DataTable>
                  <table>
                    <thead>
                      <tr><th>Timestamp</th><th>Action</th><th>Detail</th></tr>
                    </thead>
                    <tbody>
                      {selectedAgent.recent_activity.map((activity, index) => (
                        <tr key={`${activity.timestamp}-${index}`}>
                          <td>{activity.timestamp}</td>
                          <td>{activity.action}</td>
                          <td>{activity.detail}</td>
                        </tr>
                      ))}
                      {selectedAgent.activity.map((activity, index) => (
                        <tr key={`${activity.timestamp}-${activity.action}-${index}`}>
                          <td>{activity.timestamp}</td>
                          <td>{activity.action}</td>
                          <td>{`${activity.executor} · ${activity.result} · ${activity.detail}`}</td>
                        </tr>
                      ))}
                      {selectedAgent.recent_activity.length === 0 && selectedAgent.activity.length === 0 && (
                        <tr><td colSpan={3} style={{ textAlign: 'center', opacity: 0.5 }}>No recent activity</td></tr>
                      )}
                    </tbody>
                  </table>
                </DataTable>
              )}

              {detailTab === 3 && (
                <DataTable>
                  <table>
                    <thead>
                      <tr><th>Ticket</th><th>Severity</th><th>Status</th><th>Authority</th><th>Seen</th></tr>
                    </thead>
                    <tbody>
                      {selectedAgentTickets.map((ticket) => (
                        <tr key={ticket.ticket_id}>
                          <td>{ticket.summary || ticket.title || ticket.ticket_id}</td>
                          <td><StatusChip severity={severityToChip(ticket.severity || ticket.status)} label={ticket.severity || ticket.status} /></td>
                          <td>{ticket.status}</td>
                          <td>{ticket.authority || ticket.kind || 'system'}</td>
                          <td>{ticket.last_seen_at || ticket.created_at}</td>
                        </tr>
                      ))}
                      {selectedAgentTickets.length === 0 && (
                        <tr><td colSpan={5} style={{ textAlign: 'center', opacity: 0.5 }}>No linked tickets</td></tr>
                      )}
                    </tbody>
                  </table>
                </DataTable>
              )}

              {showAgentChat && detailTab === 4 && (
                <AgentChatPanel
                  messages={chatMessages}
                  input={chatInput}
                  onInputChange={setChatInput}
                  onSend={sendAgentChat}
                  busy={chatBusy}
                  error={chatError}
                  helperText="Detail chat uses the same durable Archivist agent route as the main console chat, scoped to this role."
                  placeholder={`Ask ${selectedAgent.name}...`}
                />
              )}
            </DialogContent>
          </>
        )}
      </Dialog>

      {showSystemSections && (
        <>
          <Card data-testid="console-repair-queue" sx={{ mt: 2, border: '1px solid', borderColor: 'divider' }}>
            <CardContent>
              <Typography variant="overline" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                Repair Queue
              </Typography>
              <DataTable>
                <table>
                  <thead>
                    <tr><th>Issue</th><th>Severity</th><th>Status</th><th>#</th><th>Seen</th></tr>
                  </thead>
                  <tbody>
                    {tickets.map((ticket) => (
                      <tr key={ticket.ticket_id} style={{ cursor: 'pointer' }} data-testid={`ticket-row-${ticket.ticket_id}`}>
                        <td style={{ maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {ticket.summary || ticket.title || ticket.ticket_id}
                        </td>
                        <td><StatusChip severity={severityToChip(ticket.severity || ticket.status)} label={ticket.severity || ticket.status} /></td>
                        <td>{ticket.status}</td>
                        <td>{ticket.occurrence_count ?? 1}</td>
                        <td>{ticket.last_seen_at || ticket.created_at}</td>
                      </tr>
                    ))}
                    {tickets.length === 0 && (
                      <tr><td colSpan={5} style={{ textAlign: 'center', opacity: 0.5 }}>No tickets</td></tr>
                    )}
                  </tbody>
                </table>
              </DataTable>
            </CardContent>
          </Card>

          <Card sx={{ mt: 2, border: '1px solid', borderColor: 'divider' }}>
            <CardContent>
              <Typography variant="overline" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                S2S Experiment Runner
              </Typography>
              {experiments ? (
                <Stack spacing={1}>
                  {experiments.current && (
                    <Stack direction="row" spacing={1} alignItems="center">
                      <Chip size="small" label="Running" color="primary" variant="outlined" />
                      <Typography variant="body2">{experiments.current}</Typography>
                    </Stack>
                  )}
                  {(experiments.completed ?? []).length > 0 ? (
                    (experiments.completed ?? []).map((experiment) => (
                      <Stack key={experiment} direction="row" spacing={1} alignItems="center">
                        <StatusChip severity="ok" label="Done" />
                        <Typography variant="body2">{experiment}</Typography>
                      </Stack>
                    ))
                  ) : (
                    !experiments.current && (
                      <Typography variant="caption" color="text.secondary">No experiments</Typography>
                    )
                  )}
                </Stack>
              ) : (
                <Typography variant="caption" color="text.secondary">Loading...</Typography>
              )}
            </CardContent>
          </Card>

          <Card sx={{ mt: 2, border: '1px solid', borderColor: 'divider' }}>
            <CardContent sx={{ pb: repairRunsOpen ? undefined : '12px !important' }}>
              <Stack direction="row" justifyContent="space-between" alignItems="center">
                <Typography variant="overline" color="text.secondary">
                  Recent Repair Runs ({repairRuns.length})
                </Typography>
                <Button size="small" onClick={() => setRepairRunsOpen((open) => !open)}>
                  {repairRunsOpen ? 'Collapse' : 'Expand'}
                </Button>
              </Stack>
              <Collapse in={repairRunsOpen} unmountOnExit>
                <Box sx={{ mt: 1 }}>
                  <DataTable>
                    <table>
                      <thead>
                        <tr><th>Ticket</th><th>Artifact</th><th>Modified</th></tr>
                      </thead>
                      <tbody>
                        {repairRuns.map((run, index) => (
                          <tr key={`${run.ticket_id}-${index}`}>
                            <td>{run.ticket_id}</td>
                            <td>{run.artifact}</td>
                            <td>{run.modified}</td>
                          </tr>
                        ))}
                        {repairRuns.length === 0 && (
                          <tr><td colSpan={3} style={{ textAlign: 'center', opacity: 0.5 }}>No repair runs</td></tr>
                        )}
                      </tbody>
                    </table>
                  </DataTable>
                </Box>
              </Collapse>
            </CardContent>
          </Card>
        </>
      )}
    </Box>
  )
}
