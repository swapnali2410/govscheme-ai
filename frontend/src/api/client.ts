import type { ChatResponse, DocumentUploadResponse } from './types'

const API_BASE = import.meta.env.VITE_API_BASE ?? ''

async function parseError(response: Response): Promise<string> {
  try {
    const data = await response.json()
    if (typeof data.detail === 'string') return data.detail
    if (Array.isArray(data.detail)) {
      return data.detail
        .map((item: { msg?: string }) => item.msg)
        .filter(Boolean)
        .join(', ')
    }
    return JSON.stringify(data)
  } catch {
    return response.statusText || 'Request failed'
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init)
  if (!response.ok) {
    throw new Error(await parseError(response))
  }
  return response.json() as Promise<T>
}

export const api = {
  createChatSession(): Promise<{ session_id: string }> {
    return request('/api/chat/session', { method: 'POST' })
  },

  chat(message: string, sessionId?: string | null): Promise<ChatResponse> {
    return request('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        session_id: sessionId || undefined,
      }),
    })
  },

  uploadDocumentText(payload: {
    name: string
    content: string
    category?: string
    doc_id?: string
  }): Promise<DocumentUploadResponse> {
    return request('/api/documents/text', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
  },

  async uploadDocumentFile(
    file: File,
    options?: { name?: string; category?: string },
  ): Promise<DocumentUploadResponse> {
    const form = new FormData()
    form.append('file', file)
    if (options?.name) form.append('name', options.name)
    if (options?.category) form.append('category', options.category)

    const response = await fetch(`${API_BASE}/api/documents/upload`, {
      method: 'POST',
      body: form,
    })
    if (!response.ok) {
      throw new Error(await parseError(response))
    }
    return response.json()
  },
}
