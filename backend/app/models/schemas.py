from pydantic import BaseModel


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
