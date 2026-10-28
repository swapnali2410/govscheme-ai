import { useState, type FormEvent, type ReactNode } from 'react'
import { api } from '../api/client'
import type { DocumentUploadResponse } from '../api/types'
import { LoadingDots } from './LoadingDots'
import { StatusBanner } from './StatusBanner'

export function DocumentUpload() {
  const [mode, setMode] = useState<'file' | 'text'>('file')
  const [name, setName] = useState('')
  const [category, setCategory] = useState('')
  const [content, setContent] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<DocumentUploadResponse | null>(null)

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setLoading(true)
    setError(null)
    setSuccess(null)

    try {
      let response: DocumentUploadResponse
      if (mode === 'file') {
        if (!file) {
          throw new Error('Choose a .txt, .md, or .pdf file to upload.')
        }
        response = await api.uploadDocumentFile(file, {
          name: name || undefined,
          category: category || undefined,
        })
      } else {
        if (!name.trim() || !content.trim()) {
          throw new Error('Name and content are required.')
        }
        response = await api.uploadDocumentText({
          name: name.trim(),
          content: content.trim(),
          category: category || undefined,
        })
      }
      setSuccess(response)
      setContent('')
      setFile(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="space-y-6">
      <div>
        <h2 className="font-display text-2xl font-semibold text-forest-deep tracking-tight">
          Upload documents
        </h2>
        <p className="mt-1 text-sm text-muted">
          Upload feeds Chat. Files (.txt, .md, .pdf) are extracted, embedded, and stored in the
          same ChromaDB knowledge base the chat agent searches — then ask about them in Chat.
        </p>
      </div>

      {error ? (
        <StatusBanner type="error" message={error} onDismiss={() => setError(null)} />
      ) : null}
      {success ? (
        <StatusBanner
          type="success"
          message={`${success.message} Saved as ${success.id} (${success.characters} characters). Go to Chat and ask about “${success.name}”.`}
          onDismiss={() => setSuccess(null)}
        />
      ) : null}

      <div className="flex gap-2">
        <ModeButton active={mode === 'file'} onClick={() => setMode('file')}>
          File upload
        </ModeButton>
        <ModeButton active={mode === 'text'} onClick={() => setMode('text')}>
          Paste text
        </ModeButton>
      </div>

      <form
        onSubmit={onSubmit}
        className="space-y-4 rounded-2xl border border-line bg-panel p-5"
      >
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label htmlFor="doc-name" className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-muted">
              Scheme name {mode === 'file' ? '(optional)' : ''}
            </label>
            <input
              id="doc-name"
              value={name}
              onChange={(event) => setName(event.target.value)}
              className="w-full rounded-xl border border-line bg-white/70 px-3 py-3 text-sm outline-none focus:border-leaf focus:ring-2 focus:ring-leaf/20"
              placeholder="Scheme Name"
            />
          </div>
          <div>
            <label htmlFor="doc-category" className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-muted">
              Category
            </label>
            <select
              id="doc-category"
              value={category}
              onChange={(event) => setCategory(event.target.value)}
              className="w-full rounded-xl border border-line bg-white/70 px-3 py-3 text-sm outline-none focus:border-leaf"
            >
              <option value="">None</option>
              <option value="education">Education</option>
              <option value="agriculture">Agriculture</option>
              <option value="business">Business</option>
              <option value="housing">Housing</option>
              <option value="health">Health</option>
              <option value="energy">Energy</option>
              <option value="general">General</option>
            </select>
          </div>
        </div>

        {mode === 'file' ? (
          <div>
            <label htmlFor="doc-file" className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-muted">
              File
            </label>
            <input
              id="doc-file"
              type="file"
              accept=".txt,.md,.pdf,text/plain,text/markdown,application/pdf"
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
              className="block w-full text-sm text-ink-soft file:mr-3 file:rounded-lg file:border-0 file:bg-forest file:px-3 file:py-2 file:text-sm file:font-semibold file:text-white"
            />
            {file ? (
              <p className="mt-2 text-xs text-muted">Selected: {file.name}</p>
            ) : null}
          </div>
        ) : (
          <div>
            <label htmlFor="doc-content" className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-muted">
              Content
            </label>
            <textarea
              id="doc-content"
              value={content}
              onChange={(event) => setContent(event.target.value)}
              rows={8}
              className="w-full rounded-xl border border-line bg-white/70 px-3 py-3 text-sm outline-none focus:border-leaf focus:ring-2 focus:ring-leaf/20"
              placeholder="Paste scheme description text…"
            />
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="rounded-xl bg-forest px-5 py-3 text-sm font-semibold text-white transition hover:bg-forest-deep disabled:opacity-50"
        >
          {loading ? 'Uploading…' : 'Upload to knowledge base'}
        </button>
      </form>

      {loading ? <LoadingDots label="Embedding and storing document" /> : null}
    </section>
  )
}

function ModeButton({
  active,
  onClick,
  children,
}: {
  active: boolean
  onClick: () => void
  children: ReactNode
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
        active
          ? 'bg-forest text-white'
          : 'border border-line bg-panel text-ink-soft hover:border-leaf/40'
      }`}
    >
      {children}
    </button>
  )
}
