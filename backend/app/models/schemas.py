from datetime import datetime

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    environment: str


class ErrorDetail(BaseModel):
    code: str
    message: str
    status: int
    request_id: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class UserInfo(BaseModel):
    id: str
    email: str


# ─── Knowledge Base schemas ───


class KnowledgeBaseCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)


class KnowledgeBaseUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)


class KnowledgeBaseResponse(BaseModel):
    id: str
    user_id: str
    name: str
    description: str | None
    is_public: bool
    created_at: datetime
    updated_at: datetime
    document_count: int


# ─── Document schemas ───


class DocumentResponse(BaseModel):
    id: str
    knowledge_base_id: str
    user_id: str
    file_name: str
    file_path: str
    file_size: int | None
    mime_type: str | None
    status: str
    error_message: str | None
    chunk_count: int
    created_at: datetime


# ─── Chat schemas ───


class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    conversation_id: str | None = None


class SourceItem(BaseModel):
    document_id: str
    file_name: str
    chunk_index: int
    content: str
    similarity: float
    title: str = ""


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    sources: list[SourceItem]
    domain_context: str | None = None
    created_at: datetime


class ConversationResponse(BaseModel):
    id: str
    knowledge_base_id: str
    user_id: str | None
    title: str | None
    is_widget: bool
    share_token: str
    created_at: datetime
