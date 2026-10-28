import { useEffect, useRef, useState, type FormEvent } from 'react'
import { api } from '../api/client'
import type { ChatMessage } from '../api/types'
import { LoadingDots } from './LoadingDots'
import { MarkdownMessage } from './MarkdownMessage'
import { StatusBanner } from './StatusBanner'

const SUGGESTIONS = [
  'Tell me about PM-KISAN and how to apply',
  'What health cover does Ayushman Bharat PM-JAY provide?',
  'List documents available in the knowledge base, including uploads',
]

function newId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

export function ChatPanel() {
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  async function sendMessage(text: string) {
    const trimmed = text.trim()
    if (!trimmed || loading) return

    setError(null)
    setInput('')
    const userMessage: ChatMessage = {
      id: newId(),
      role: 'user',
      content: trimmed,
      createdAt: Date.now(),
    }
    setMessages((prev) => [...prev, userMessage])
    setLoading(true)

    try {
      const response = await api.chat(trimmed, sessionId)
      setSessionId(response.session_id)
      setMessages((prev) => [
        ...prev,
        {
          id: newId(),
          role: 'assistant',
          content: response.reply,
          createdAt: Date.now(),
        },
      ])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Chat request failed')
    } finally {
      setLoading(false)
    }
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault()
    void sendMessage(input)
  }

  function startNewChat() {
    setSessionId(null)
    setMessages([])
    setError(null)
    setInput('')
  }

  return (
    <section className="flex h-full min-h-[32rem] flex-col">
      <div className="mb-4 flex items-end justify-between gap-3">
        <div>
          <h2 className="font-display text-2xl font-semibold text-forest-deep tracking-tight">
            Ask GovScheme AI
          </h2>
        </div>
        <button
          type="button"
          onClick={startNewChat}
          className="rounded-lg border border-line bg-panel-strong px-3 py-2 text-xs font-semibold uppercase tracking-wide text-ink-soft transition hover:border-leaf/40 hover:text-forest"
        >
          New chat
        </button>
      </div>

      {error ? (
        <div className="mb-3">
          <StatusBanner type="error" message={error} onDismiss={() => setError(null)} />
        </div>
      ) : null}

      <div className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-2xl border border-line bg-panel shadow-[0_18px_50px_-28px_rgba(10,61,50,0.45)]">
        <div className="flex-1 space-y-4 overflow-y-auto px-4 py-5 sm:px-5">
          {messages.length === 0 ? (
            <div className="animate-fade-up mx-auto max-w-lg py-8 text-center">
              <p className="font-display text-xl text-forest">Start a conversation</p>
              <p className="mt-2 text-sm text-muted">
                Try a suggestion or ask about education, farming, housing, or business schemes.
              </p>
              <div className="mt-6 flex flex-wrap justify-center gap-2">
                {SUGGESTIONS.map((suggestion) => (
                  <button
                    key={suggestion}
                    type="button"
                    onClick={() => void sendMessage(suggestion)}
                    className="rounded-full border border-line bg-panel-strong px-3.5 py-2 text-left text-sm text-ink-soft transition hover:border-leaf/50 hover:text-forest"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={`animate-fade-up flex ${
                  message.role === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                    message.role === 'user'
                      ? 'bg-forest text-white whitespace-pre-wrap'
                      : 'border border-line bg-panel-strong text-ink'
                  }`}
                >
                  {message.role === 'assistant' ? (
                    <MarkdownMessage content={message.content} />
                  ) : (
                    message.content
                  )}
                </div>
              </div>
            ))
          )}
          {loading ? (
            <div className="flex justify-start">
              <div className="rounded-2xl border border-line bg-panel-strong px-4 py-3">
                <LoadingDots label="Agent is thinking" />
              </div>
            </div>
          ) : null}
          <div ref={bottomRef} />
        </div>

        <form
          onSubmit={onSubmit}
          className="border-t border-line bg-panel-strong/80 p-3 sm:p-4"
        >
          <div className="flex gap-2">
            <label className="sr-only" htmlFor="chat-input">
              Message
            </label>
            <input
              id="chat-input"
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="Ask about a scheme, eligibility, or benefits…"
              disabled={loading}
              className="min-w-0 flex-1 rounded-xl border border-line bg-white/70 px-4 py-3 text-sm outline-none transition placeholder:text-muted/70 focus:border-leaf focus:ring-2 focus:ring-leaf/20 disabled:opacity-60"
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="rounded-xl bg-marigold px-4 py-3 text-sm font-semibold text-forest-deep transition hover:bg-marigold-deep hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
            >
              Send
            </button>
          </div>
          {sessionId ? (
            <p className="mt-2 truncate text-[11px] text-muted">
              Session {sessionId}
            </p>
          ) : null}
        </form>
      </div>
    </section>
  )
}
