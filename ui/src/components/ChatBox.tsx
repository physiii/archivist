import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

/* ── Types ─────────────────────────────────────────────────────── */

interface ChatMessage {
  id: number;
  role: "user" | "assistant";
  text: string;
}

interface ChatAction {
  type: string;
  payload: Record<string, unknown>;
}

interface ChatSession {
  session_key: string;
  title: string;
  created_at: string;
  message_count: number;
}

interface OpenClawSession {
  session_key: string;
  kind: string;
  title: string;
  created_at: string;
  message_count: number;
}

/* ── Helpers ───────────────────────────────────────────────────── */

let nextId = 1;

function getApiBase() {
  return "";
}

function makeSid(): string {
  return crypto.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function formatDate(iso: string): string {
  try {
    const d = new Date(iso);
    const now = new Date();
    const diff = now.getTime() - d.getTime();
    if (diff < 60_000) return "just now";
    if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`;
    if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h ago`;
    return d.toLocaleDateString();
  } catch {
    return iso;
  }
}

/* ── Component ─────────────────────────────────────────────────── */

export default function ChatBox() {
  const navigate = useNavigate();
  const base = getApiBase();

  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string>(makeSid);

  /* History panel */
  const [showHistory, setShowHistory] = useState(false);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [ocSessions, setOcSessions] = useState<OpenClawSession[]>([]);
  const [viewingOc, setViewingOc] = useState<string | null>(null);

  const scrollRef = useRef<HTMLDivElement>(null);

  const sessionKey = `main:web:${sessionId}@archivist-main`;

  /* ── Auto-scroll ──────────────────────────────────────────────── */
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, loading]);

  /* ── Actions ──────────────────────────────────────────────────── */
  const executeAction = useCallback(
    (action: ChatAction) => {
      if (action.type === "navigate" && typeof action.payload.path === "string") {
        navigate(action.payload.path);
      }
    },
    [navigate],
  );

  const extractAction = useCallback(
    (text: string): string => {
      const match = text.match(/ACTION:(\{[^}]+\})/);
      if (match) {
        try {
          const action = JSON.parse(match[1]);
          if (action.type && action.payload) executeAction(action);
        } catch { /* ignore parse errors */ }
        return text.replace(/ACTION:\{[^}]*\}/g, "").trim();
      }
      return text;
    },
    [executeAction],
  );

  /* ── Session management ───────────────────────────────────────── */
  const fetchSessions = useCallback(async () => {
    try {
      const res = await fetch(`${base}/api/chat/sessions`);
      if (!res.ok) return;
      const data = await res.json();
      setSessions(data.sessions ?? []);
      setOcSessions(data.oc_sessions ?? []);
    } catch { /* silent */ }
  }, [base]);

  const createSession = useCallback(() => {
    const sid = makeSid();
    setSessionId(sid);
    setMessages([]);
    setViewingOc(null);
    setShowHistory(false);
  }, []);

  const loadSessionMessages = useCallback(
    async (key: string) => {
      try {
        const res = await fetch(`${base}/api/chat/sessions/${encodeURIComponent(key)}/messages`);
        if (!res.ok) return;
        const data = await res.json();
        const msgs: ChatMessage[] = (data.messages ?? []).map((m: { role: string; content: string }) => ({
          id: nextId++,
          role: m.role as "user" | "assistant",
          text: m.content,
        }));
        setMessages(msgs);
      } catch { /* silent */ }
    },
    [base],
  );

  const deleteSession = useCallback(
    async (key: string, e: React.MouseEvent) => {
      e.stopPropagation();
      try {
        await fetch(`${base}/api/chat/sessions/${encodeURIComponent(key)}`, { method: "DELETE" });
        setSessions((prev) => prev.filter((s) => s.session_key !== key));
        if (sessionKey === key) createSession();
      } catch { /* silent */ }
    },
    [base, sessionKey, createSession],
  );

  const selectSession = useCallback(
    (s: ChatSession) => {
      // Extract sid from session key format "main:web:<sid>@<agent-id>"
      const match = s.session_key.match(/^main:web:(.+)@[^@]+$/);
      if (match) setSessionId(match[1]);
      setViewingOc(null);
      loadSessionMessages(s.session_key);
      setShowHistory(false);
    },
    [loadSessionMessages],
  );

  const selectOcSession = useCallback(
    (s: OpenClawSession) => {
      setViewingOc(s.session_key);
      loadSessionMessages(s.session_key);
      setShowHistory(false);
    },
    [loadSessionMessages],
  );

  /* ── Send message ─────────────────────────────────────────────── */
  const sendMessage = useCallback(async () => {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg: ChatMessage = { id: nextId++, role: "user", text };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const response = await fetch(`${base}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, stream: true, session_key: sessionKey }),
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const contentType = response.headers.get("content-type") || "";

      if (contentType.includes("text/event-stream") && response.body) {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullText = "";
        const assistantId = nextId++;

        setMessages((prev) => [...prev, { id: assistantId, role: "assistant", text: "" }]);

        let buffer = "";
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            const payload = line.slice(6).trim();
            if (payload === "[DONE]") continue;

            try {
              const parsed = JSON.parse(payload);
              if (parsed.delta) {
                fullText += parsed.delta;
                const cleanText = fullText.replace(/ACTION:\{[^}]*\}/g, "").trim();
                setMessages((prev) =>
                  prev.map((m) => (m.id === assistantId ? { ...m, text: cleanText } : m)),
                );
              }
              if (parsed.action) executeAction(parsed.action);
            } catch { /* ignore parse errors */ }
          }
        }

        const cleanFinal = extractAction(fullText);
        setMessages((prev) =>
          prev.map((m) => (m.id === assistantId ? { ...m, text: cleanFinal || "No response." } : m)),
        );
      } else {
        const data = await response.json();
        setMessages((prev) => [
          ...prev,
          { id: nextId++, role: "assistant", text: data.reply || "No response." },
        ]);
        if (data.action) executeAction(data.action);
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        { id: nextId++, role: "assistant", text: "Failed to reach the server." },
      ]);
    } finally {
      setLoading(false);
    }
  }, [input, loading, executeAction, extractAction, base, sessionKey]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const toggleHistory = () => {
    const next = !showHistory;
    setShowHistory(next);
    if (next) fetchSessions();
  };

  /* ── FAB (closed state) ──────────────────────────────────────── */
  if (!open) {
    return (
      <button className="chat-fab" onClick={() => setOpen(true)} aria-label="Open chat" title="Open chat">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
        </svg>
      </button>
    );
  }

  const isReadOnly = !!viewingOc;

  /* ── Render ──────────────────────────────────────────────────── */
  return (
    <div className="chat-window">
      {/* Header */}
      <div className="chat-header">
        <span className="chat-title">Archivist Chat</span>
        <div className="chat-header-actions">
          <button className="chat-new-btn" onClick={createSession} title="New chat" aria-label="New chat">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
            </svg>
          </button>
          <button
            className={`chat-history-btn ${showHistory ? "active" : ""}`}
            onClick={toggleHistory}
            title="Chat history"
            aria-label="Chat history"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" />
            </svg>
          </button>
          <button className="chat-close" onClick={() => setOpen(false)} aria-label="Close chat">&times;</button>
        </div>
      </div>

      {/* History panel */}
      {showHistory ? (
        <div className="chat-history-panel">
          <div className="chat-history-header">
            <span className="chat-history-title">Sessions</span>
          </div>
          <div className="chat-history-list">
            {sessions.map((s) => (
              <div
                key={s.session_key}
                className={`chat-session-item ${s.session_key === sessionKey ? "active" : ""}`}
                onClick={() => selectSession(s)}
              >
                <div className="chat-session-info">
                  <span className="chat-session-title">{s.title || "Untitled"}</span>
                  <span className="chat-session-meta">
                    {s.message_count} msgs &middot; {formatDate(s.created_at)}
                  </span>
                </div>
                <button
                  className="chat-session-delete"
                  onClick={(e) => deleteSession(s.session_key, e)}
                  title="Delete session"
                  aria-label="Delete session"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="3 6 5 6 21 6" />
                    <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
                    <path d="M10 11v6" /><path d="M14 11v6" />
                  </svg>
                </button>
              </div>
            ))}
            {sessions.length === 0 && (
              <div className="chat-empty" style={{ marginTop: 32 }}>No saved sessions yet.</div>
            )}

            {ocSessions.length > 0 && (
              <>
                <div className="chat-oc-section-header">OpenClaw Sessions</div>
                {ocSessions.map((s) => (
                  <div
                    key={s.session_key}
                    className={`chat-session-item ${viewingOc === s.session_key ? "active" : ""}`}
                    onClick={() => selectOcSession(s)}
                  >
                    <div className="chat-session-info">
                      <span className="chat-session-title">{s.title || "Untitled"}</span>
                      <span className="chat-session-meta">
                        <span className="chat-oc-kind-badge">{s.kind}</span>{" "}
                        {s.message_count} msgs &middot; {formatDate(s.created_at)}
                      </span>
                    </div>
                  </div>
                ))}
              </>
            )}
          </div>
        </div>
      ) : (
        <>
          {/* Messages */}
          <div className="chat-messages" ref={scrollRef}>
            {messages.length === 0 && !loading && (
              <div className="chat-empty">
                Ask about your collections, search documents, or check backup status.
              </div>
            )}
            {messages.map((msg) => (
              <div key={msg.id} className={`chat-bubble ${msg.role}`}>
                {msg.text}
              </div>
            ))}
            {loading && <div className="chat-bubble assistant chat-thinking">Thinking...</div>}
          </div>

          {/* Input */}
          <div className="chat-input-row">
            <input
              type="text"
              className="chat-input"
              placeholder={isReadOnly ? "Read-only \u2014 viewing OpenClaw session" : "Ask anything..."}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isReadOnly}
            />
            <button
              className="chat-send"
              onClick={sendMessage}
              disabled={!input.trim() || loading || isReadOnly}
              aria-label="Send message"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
              </svg>
            </button>
          </div>
        </>
      )}
    </div>
  );
}
