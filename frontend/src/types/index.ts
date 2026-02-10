export interface KnowledgeBase {
  id: string
  user_id: string
  name: string
  description: string | null
  is_public: boolean
  created_at: string
  updated_at: string
}

export interface Document {
  id: string
  knowledge_base_id: string
  user_id: string
  file_name: string
  file_path: string
  file_size: number | null
  mime_type: string | null
  status: "uploading" | "processing" | "ready" | "failed"
  error_message: string | null
  chunk_count: number
  created_at: string
}

export interface Conversation {
  id: string
  knowledge_base_id: string
  user_id: string | null
  title: string | null
  is_widget: boolean
  share_token: string
  created_at: string
}

export interface Message {
  id: string
  conversation_id: string
  role: "user" | "assistant"
  content: string
  sources: Source[]
  created_at: string
}

export interface Source {
  document_id: string
  file_name: string
  chunk_index: number
  content: string
  similarity: number
}

export interface HealthResponse {
  status: string
  environment: string
}
