import { useCallback, useEffect, useRef, useState, type FormEvent } from 'react'
import {
  Box, Button, Chip, CircularProgress, Collapse, IconButton,
  InputBase, List, ListItemButton, ListItemIcon, ListItemText, Paper,
  Stack, Tab, Tabs, Tooltip, Typography, alpha, Badge,
} from '@mui/material'
import SendIcon from '@mui/icons-material/Send'
import StopIcon from '@mui/icons-material/Stop'
import BugReportIcon from '@mui/icons-material/BugReport'
import TerminalIcon from '@mui/icons-material/Terminal'
import BuildIcon from '@mui/icons-material/Build'
import HistoryIcon from '@mui/icons-material/History'
import AddIcon from '@mui/icons-material/Add'
import AutoFixHighIcon from '@mui/icons-material/AutoFixHigh'
import ScienceIcon from '@mui/icons-material/Science'
import SmartToyIcon from '@mui/icons-material/SmartToy'
import SettingsIcon from '@mui/icons-material/Settings'
import ChatIcon from '@mui/icons-material/ChatBubbleOutline'
import GroupsIcon from '@mui/icons-material/Groups'
import MarkdownMessage from '../components/MarkdownMessage'
import { getJson, postJson } from './lib/api'
import {
  type AgentChatMessage,
  type SessionSummary,
  formatSessionKey,
  formatSessionTime,
  isMainAgentChatSession,
  notifyAgentSessionsChanged,
  sessionKind,
  sessionPreview,
  subscribeAgentSessionsChanged,
} from './lib/agentSessions'
import AgentFleetPanel from './panels/FleetPanel'
import SystemPanel from './panels/SystemPanel'
import TestsPanel from './panels/TestsPanel'
import { consoleBranding } from './config/branding'
import { consoleEndpoints } from './config/endpoints'

type ChatMessage = AgentChatMessage

function mapApiMessages(sessionId: string, rawMessages: any[]): ChatMessage[] {
  return (rawMessages || []).map((message: any, index: number) => ({
    id: `${sessionId}-${index}`,
    role: message?.role === 'user' || message?.role === 'assistant' || message?.role === 'system' || message?.role === 'tool'
      ? message.role
      : 'system',
    text: String(message?.text || ''),
    ts: Number(message?.ts || 0),
    toolName: message?.toolName,
  }))
}

export default function ConsoleWorkspace({ status }: { status?: any }) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [sessions, setSessions] = useState<SessionSummary[]>([])
  const [showSessions, setShowSessions] = useState(false)
  const [streamingText, setStreamingText] = useState('')
  const [activeTab, setActiveTab] = useState(0)
  const scrollRef = useRef<HTMLDivElement>(null)
  const abortRef = useRef<AbortController | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    const el = scrollRef.current
    if (!el) return
    const raf = requestAnimationFrame(() => { el.scrollTop = el.scrollHeight })
    return () => cancelAnimationFrame(raf)
  }, [messages.length, streamingText])

  const loadSessions = useCallback(async () => {
    try {
      const rows = await getJson<SessionSummary[]>(consoleEndpoints.agentSessions)
      setSessions(rows || [])
    } catch {}
  }, [])

  useEffect(() => {
    void loadSessions()
    return subscribeAgentSessionsChanged(() => { void loadSessions() })
  }, [loadSessions])

  useEffect(() => {
    if (activeTab === 0) {
      void loadSessions()
      const t = setTimeout(() => inputRef.current?.focus(), 100)
      return () => clearTimeout(t)
    }
  }, [activeTab, loadSessions])

  async function loadSession(id: string) {
    try {
      const r = await getJson<any>(consoleEndpoints.agentSession(id))
      setSessionId(r.id)
      setMessages(mapApiMessages(r.id, r.messages || []))
      setShowSessions(false)
    } catch {}
  }

  function handleSSEEvent(event: string, data: any, appendText: (t: string) => void) {
    switch (event) {
      case 'text': if (data.text) appendText(data.text); break
      case 'result': break
      case 'system':
        if (data.text) {
          setMessages(prev => [...prev, {
            id: `sys-${Date.now()}`, role: 'system', text: data.text, ts: Date.now(),
          }])
        }
        break
      case 'error':
        if (data.message) {
          setMessages(prev => [...prev, {
            id: `err-${Date.now()}`, role: 'system', text: `Error: ${data.message}`, ts: Date.now(),
          }])
        }
        break
    }
  }

  const sendMessage = useCallback(async (text: string) => {
    if (!text.trim() || streaming) return
    const userMsg: ChatMessage = { id: `u-${Date.now()}`, role: 'user', text: text.trim(), ts: Date.now() }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setStreaming(true)
    setStreamingText('')

    try {
      const controller = new AbortController()
      abortRef.current = controller
      const response = await fetch(consoleEndpoints.agentChat, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text.trim(),
          sessionId: sessionId || undefined,
          surface: 'console',
          historyScope: 'main-chat',
        }),
        signal: controller.signal,
      })
      if (!response.ok || !response.body) throw new Error(`HTTP ${response.status}`)

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let accumulated = '', currentEvent = '', fullText = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        accumulated += decoder.decode(value, { stream: true })
        const lines = accumulated.split('\n')
        accumulated = lines.pop() || ''
        for (const line of lines) {
          if (line.startsWith('event: ')) currentEvent = line.slice(7).trim()
          else if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              handleSSEEvent(currentEvent, data, (t) => { fullText += t; setStreamingText(fullText) })
              if (currentEvent === 'session_start' && data.id) setSessionId(data.id)
              if (currentEvent === 'tool_use' && data.name) {
                setMessages(prev => [...prev, {
                  id: `tool-${Date.now()}-${Math.random()}`, role: 'tool',
                  text: JSON.stringify(data.input, null, 2)?.slice(0, 500) || '',
                  ts: Date.now(), toolName: data.name,
                }])
              }
            } catch {}
          }
        }
      }
      if (fullText.trim()) {
        setMessages(prev => [...prev, { id: `a-${Date.now()}`, role: 'assistant', text: fullText.trim(), ts: Date.now() }])
      }
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        setMessages(prev => [...prev, { id: `err-${Date.now()}`, role: 'system', text: `Error: ${err.message}`, ts: Date.now() }])
      }
    } finally {
      setStreaming(false)
      setStreamingText('')
      abortRef.current = null
      void loadSessions()
      notifyAgentSessionsChanged()
    }
  }, [loadSessions, streaming, sessionId])

  function stopAgent() {
    abortRef.current?.abort()
    if (sessionId) postJson(consoleEndpoints.agentStop(sessionId), {}).catch(() => {})
    setStreaming(false)
    setStreamingText('')
  }

  function newSession() {
    setSessionId(null)
    setMessages([])
    setStreamingText('')
  }

  const mainChatSessions = sessions.filter(isMainAgentChatSession)
  const otherAgentSessions = sessions.filter((session) => !isMainAgentChatSession(session))

  const quickActions = [
    {
      label: 'Diagnose',
      icon: <AutoFixHighIcon sx={{ fontSize: 16 }} />,
      prompt:
        'Inspect the current Archivist workspace, runtime status, and recent failures, then summarize the most important issues first.',
    },
    {
      label: 'Run tests',
      icon: <ScienceIcon sx={{ fontSize: 16 }} />,
      prompt:
        'Summarize the available Archivist test coverage and tell me the fastest safe command to verify the current UI changes.',
    },
    {
      label: 'Repair queue',
      icon: <BugReportIcon sx={{ fontSize: 16 }} />,
      prompt:
        'Inspect the current repair queue or missing runtime signals and summarize the highest priority issues.',
    },
    {
      label: 'Sessions',
      icon: <TerminalIcon sx={{ fontSize: 16 }} />,
      prompt:
        'Review recent Archivist sessions and summarize recurring failures, missing context, or repeated commands.',
    },
  ]

  return (
    <Box
      data-testid="console-page"
      sx={{
        minHeight: 0,
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <Stack direction="row" alignItems="center" sx={{ gap: 0.5, mb: 0.5 }}>
        <Tabs
          value={activeTab}
          onChange={(_, v) => setActiveTab(v)}
          sx={{
            minHeight: 34,
            '& .MuiTab-root': {
              minHeight: 34, py: 0, px: 1.5,
              fontSize: '0.8rem', textTransform: 'none', minWidth: 'auto',
              gap: 0.5,
            },
            '& .MuiTab-iconWrapper': { marginRight: 0 },
          }}
        >
          <Tab icon={<ChatIcon sx={{ fontSize: 15 }} />} iconPosition="start" label="Chat" />
          <Tab icon={<GroupsIcon sx={{ fontSize: 15 }} />} iconPosition="start" label="Fleet" />
          <Tab icon={<SettingsIcon sx={{ fontSize: 15 }} />} iconPosition="start" label="System" />
          <Tab icon={<ScienceIcon sx={{ fontSize: 15 }} />} iconPosition="start" label="Tests" />
        </Tabs>
        <Box sx={{ flex: 1 }} />
        {activeTab === 0 && (
          <>
            <Chip
              label={streaming ? 'Running' : sessionId ? 'Connected' : 'Ready'}
              color={streaming ? 'warning' : sessionId ? 'success' : 'default'}
              size="small" variant="outlined"
              sx={{ height: 22, fontSize: '0.7rem' }}
            />
            <Tooltip title="Sessions" arrow>
              <Button size="small" variant="outlined"
                onClick={() => setShowSessions(!showSessions)}
                startIcon={<HistoryIcon sx={{ fontSize: 16 }} />}
                sx={{ minHeight: 28, fontSize: '0.75rem', px: 1 }}
              >
                {sessions.length}
              </Button>
            </Tooltip>
            <Tooltip title="New session" arrow>
              <IconButton aria-label="New session" size="small" onClick={newSession}
                sx={{ minWidth: 28, minHeight: 28, color: 'text.secondary', '&:hover': { color: 'primary.main' } }}>
                <AddIcon sx={{ fontSize: 18 }} />
              </IconButton>
            </Tooltip>
          </>
        )}
      </Stack>

      {activeTab === 0 && (
        <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
          <Collapse in={showSessions}>
            <Paper variant="outlined" sx={{ mb: 1, maxHeight: 300, overflow: 'auto', borderRadius: '6px' }}>
              <List dense disablePadding>
                {mainChatSessions.length > 0 && (
                  <Typography variant="overline" sx={{ px: 2, pt: 1, display: 'block', color: 'text.secondary', fontSize: '0.65rem' }}>
                    Chat Sessions
                  </Typography>
                )}
                {mainChatSessions.map(s => (
                  <ListItemButton key={s.id} onClick={() => loadSession(s.id)} selected={s.id === sessionId}
                    sx={{ py: 0.5 }}>
                    <ListItemIcon sx={{ minWidth: 28 }}>
                      <Badge variant="dot" color="success"><TerminalIcon sx={{ fontSize: 16 }} /></Badge>
                    </ListItemIcon>
                    <ListItemText
                      primary={sessionPreview(s)}
                      secondary={[`${s.messageCount} msgs`, formatSessionTime(s.updatedAt || s.createdAt)].filter(Boolean).join(' · ')}
                      primaryTypographyProps={{ noWrap: true, fontSize: '0.8rem' }}
                      secondaryTypographyProps={{ fontSize: '0.7rem' }}
                    />
                    <Chip label={sessionKind(s)} size="small" variant="outlined" sx={{ fontSize: '0.65rem', height: 18 }} />
                  </ListItemButton>
                ))}
                {otherAgentSessions.length > 0 && (
                  <Typography variant="overline" sx={{ px: 2, pt: 0.5, display: 'block', color: 'text.secondary', fontSize: '0.65rem' }}>
                    Other Agent Sessions ({otherAgentSessions.length})
                  </Typography>
                )}
                {otherAgentSessions.map(s => {
                  const label = formatSessionKey(s.id)
                  const statusColor = s.status === 'running' ? 'warning' as const
                    : s.status === 'done' ? 'success' as const
                    : s.status === 'failed' ? 'error' as const
                    : 'default' as const
                  return (
                    <ListItemButton key={s.id} onClick={() => loadSession(s.id)} selected={s.id === sessionId}
                      disabled={!s.hasData} sx={{ py: 0.5, opacity: s.hasData ? 1 : 0.5 }}>
                      <ListItemIcon sx={{ minWidth: 28 }}>
                        <Badge variant="dot" color={statusColor}><TerminalIcon sx={{ fontSize: 16 }} /></Badge>
                      </ListItemIcon>
                      <ListItemText
                        primary={sessionPreview(s)}
                        secondary={[label, s.status, s.contextTokens ? `${Math.round(s.contextTokens / 1000)}k` : '', formatSessionTime(s.updatedAt || s.createdAt)].filter(Boolean).join(' · ')}
                        primaryTypographyProps={{ noWrap: true, fontSize: '0.8rem' }}
                        secondaryTypographyProps={{ fontSize: '0.7rem' }}
                      />
                      <Chip label={sessionKind(s)} size="small" variant="outlined" sx={{ fontSize: '0.65rem', height: 18 }} />
                    </ListItemButton>
                  )
                })}
                {!sessions.length && (
                  <Typography variant="body2" color="text.secondary" sx={{ p: 2, textAlign: 'center', fontSize: '0.8rem' }}>
                    No sessions yet
                  </Typography>
                )}
              </List>
            </Paper>
          </Collapse>

          <Stack direction="row" sx={{ mb: 1, gap: 0.5, flexWrap: 'wrap' }}>
            {quickActions.map(qa => (
              <Chip key={qa.label} icon={qa.icon} label={qa.label}
                onClick={() => sendMessage(qa.prompt)}
                variant="outlined" size="small" disabled={streaming}
                sx={{ cursor: 'pointer', height: 26, fontSize: '0.75rem' }}
              />
            ))}
          </Stack>

          <Box
            ref={scrollRef}
            sx={{
              flex: 1, overflowY: 'auto', minHeight: 0,
              px: 2, py: 1.5,
              bgcolor: (t) => alpha(t.palette.common.black, 0.12),
              borderRadius: '6px',
              border: '1px solid', borderColor: 'divider',
            }}
          >
            <Stack spacing={1.5}>
              {messages.map(msg => <MessageBubble key={msg.id} message={msg} />)}
              {streaming && streamingText && (
                <Box sx={{
                  px: 2, py: 1.5, borderRadius: '6px 6px 6px 2px',
                  bgcolor: 'rgba(255,255,255,0.03)',
                  border: '1px solid', borderColor: 'divider',
                  maxWidth: '90%',
                }}>
                  <Typography variant="caption" sx={{ fontWeight: 700, display: 'block', mb: 0.5, color: 'warning.main', fontSize: '0.7rem' }}>
                    {consoleBranding.assistantName} (streaming)
                  </Typography>
                  <MarkdownMessage text={streamingText} fontSize="0.82rem" />
                </Box>
              )}
              {streaming && !streamingText && (
                <Stack direction="row" spacing={1} sx={{ alignItems: 'center', py: 1 }}>
                  <CircularProgress size={14} />
                  <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.8rem' }}>Working...</Typography>
                </Stack>
              )}
              {!messages.length && !streaming && (
                <Box sx={{ minHeight: 200, display: 'grid', placeItems: 'center' }}>
                  <Stack spacing={1} sx={{ alignItems: 'center', textAlign: 'center', px: 3 }}>
                    <SmartToyIcon sx={{ fontSize: 36, opacity: 0.15 }} />
                    <Typography color="text.secondary" variant="body2" sx={{ fontSize: '0.85rem' }}>
                      {consoleBranding.chatEmptyState}
                    </Typography>
                  </Stack>
                </Box>
              )}
            </Stack>
          </Box>

          <Stack
            component="form"
            direction="row"
            alignItems="center"
            onSubmit={(e: FormEvent) => { e.preventDefault(); sendMessage(input) }}
            sx={{ mt: 1, gap: 0.75 }}
          >
            <InputBase
              inputRef={inputRef}
              placeholder={streaming ? 'Agent is working...' : consoleBranding.chatInputPlaceholder}
              value={input}
              onChange={e => setInput(e.target.value)}
              disabled={streaming}
              onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(input) } }}
              multiline maxRows={4} fullWidth
              sx={{
                px: 1.5, py: 0.75, borderRadius: '4px',
                bgcolor: (t) => alpha(t.palette.common.white, 0.04),
                fontSize: '0.85rem',
                border: '1px solid', borderColor: 'divider',
                '&:focus-within': { borderColor: 'primary.main' },
              }}
            />
            {streaming ? (
              <Tooltip title="Stop" arrow>
                <IconButton color="error" onClick={stopAgent}
                  sx={{ minWidth: 36, minHeight: 36, p: 0.5 }}>
                  <StopIcon sx={{ fontSize: 20 }} />
                </IconButton>
              </Tooltip>
            ) : (
              <Tooltip title="Send" arrow>
                <span>
                  <IconButton color="primary" type="submit" disabled={!input.trim()}
                    sx={{ minWidth: 36, minHeight: 36, p: 0.5 }}>
                    <SendIcon sx={{ fontSize: 20 }} />
                  </IconButton>
                </span>
              </Tooltip>
            )}
          </Stack>
        </Box>
      )}

      {activeTab === 1 && (
        <Box sx={{ flex: 1, overflow: 'auto', minHeight: 0 }}>
          <AgentFleetPanel embedded />
        </Box>
      )}

      {activeTab === 2 && (
        <Box sx={{ flex: 1, overflow: 'auto', minHeight: 0 }}>
          <SystemPanel status={status} />
        </Box>
      )}

      {activeTab === 3 && (
        <Box sx={{ flex: 1, overflow: 'auto', minHeight: 0 }}>
          <TestsPanel />
        </Box>
      )}
    </Box>
  )
}

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user'
  const isTool = message.role === 'tool'
  const isSystem = message.role === 'system'

  if (isTool) {
    return (
      <Box sx={{
        px: 1.5, py: 1, borderRadius: '4px', maxWidth: '90%',
        bgcolor: (t) => alpha(t.palette.info.main, 0.06),
        border: (t) => `1px solid ${alpha(t.palette.info.main, 0.15)}`,
      }}>
        <Chip icon={<BuildIcon />} label={message.toolName || 'tool'} size="small" color="info" variant="outlined"
          sx={{ mb: 0.5, height: 22, fontSize: '0.7rem' }} />
        <Typography variant="body2" sx={{
          whiteSpace: 'pre-wrap', wordBreak: 'break-word',
          fontFamily: '"IBM Plex Mono", monospace', fontSize: '0.78rem', lineHeight: 1.5,
        }}>
          {message.text.slice(0, 500)}
        </Typography>
      </Box>
    )
  }

  if (isSystem) {
    return (
      <Typography variant="caption" color="text.secondary"
        sx={{ textAlign: 'center', display: 'block', py: 0.25, fontStyle: 'italic', fontSize: '0.75rem' }}>
        {message.text}
      </Typography>
    )
  }

  return (
    <Box sx={{ display: 'flex', justifyContent: isUser ? 'flex-end' : 'flex-start' }}>
      <Box sx={{
        maxWidth: '85%', px: 1.75, py: 1,
        borderRadius: isUser ? '6px 6px 2px 6px' : '6px 6px 6px 2px',
        bgcolor: isUser ? 'primary.main' : 'rgba(255,255,255,0.04)',
        color: isUser ? 'primary.contrastText' : 'text.primary',
        border: isUser ? 'none' : '1px solid',
        borderColor: 'divider',
      }}>
        {!isUser && (
          <Typography variant="caption" sx={{ fontWeight: 700, display: 'block', mb: 0.25, color: 'text.secondary', fontSize: '0.7rem' }}>
            {consoleBranding.assistantName}
          </Typography>
        )}
        {isUser ? (
          <Typography variant="body2" sx={{
            whiteSpace: 'pre-wrap', wordBreak: 'break-word', lineHeight: 1.5,
            fontSize: '0.85rem',
          }}>
            {message.text}
          </Typography>
        ) : (
          <MarkdownMessage text={message.text} fontSize="0.82rem" />
        )}
      </Box>
    </Box>
  )
}
