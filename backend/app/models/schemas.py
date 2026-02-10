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
