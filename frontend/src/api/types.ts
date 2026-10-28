export interface ChatResponse {
  session_id: string
  message: string
  reply: string
}

export interface DocumentUploadResponse {
  success: boolean
  id: string
  name: string
  category?: string | null
  characters: number
  message: string
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  createdAt: number
}
