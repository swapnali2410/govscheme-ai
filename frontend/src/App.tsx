import { useState } from 'react'
import { ChatPanel } from './components/ChatPanel'
import { DocumentUpload } from './components/DocumentUpload'

type TabId = 'chat' | 'upload'

const TABS: { id: TabId; label: string }[] = [
  { id: 'chat', label: 'Chat' },
  { id: 'upload', label: 'Upload' },
]

export default function App() {
  const [tab, setTab] = useState<TabId>('chat')

  return (
    <div className="mx-auto flex min-h-screen max-w-6xl flex-col px-4 pb-16 pt-8 sm:px-6 lg:px-8">
      <header className="animate-fade-up mb-8">
        <p className="text-xs font-semibold uppercase tracking-[0.22em] text-leaf">
          Indian Government Schemes Assistant
        </p>
        <h1 className="mt-2 font-display text-4xl font-semibold tracking-tight text-forest-deep sm:text-5xl">
          GovScheme AI
        </h1>
      </header>

      <nav
        className="mb-6 flex flex-wrap gap-2 border-b border-line pb-3"
        aria-label="Primary"
      >
        {TABS.map((item) => {
          const active = tab === item.id
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => setTab(item.id)}
              className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
                active
                  ? 'bg-forest text-white shadow-sm'
                  : 'text-ink-soft hover:bg-panel hover:text-forest'
              }`}
            >
              {item.label}
            </button>
          )
        })}
      </nav>

      <main className="animate-fade-up flex-1">
        {tab === 'chat' ? <ChatPanel /> : null}
        {tab === 'upload' ? <DocumentUpload /> : null}
      </main>

      <footer className="mt-12 border-t border-line pt-5 text-xs text-muted">
        Always verify scheme details on official Indian government portals or{' '}
        <a
          href="https://www.myscheme.gov.in/"
          target="_blank"
          rel="noreferrer"
          className="font-semibold text-leaf underline-offset-2 hover:underline"
        >
          myScheme.gov.in
        </a>
        .
      </footer>
    </div>
  )
}
