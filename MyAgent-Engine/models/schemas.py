from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints

DisplayName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=120)]
Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]


class ApiModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    display_name: DisplayName


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=20, max_length=4096)


class LogoutRequest(BaseModel):
    refresh_token: str = Field(min_length=20, max_length=4096)


class UserResponse(ApiModel):
    id: str
    email: EmailStr
    display_name: str
    role: str
    is_active: bool
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class ProjectCreate(BaseModel):
    name: Title
    description: str = Field(default="", max_length=10_000)
    instructions: str = Field(default="", max_length=30_000)
    default_provider: str | None = Field(default=None, max_length=80)


class ProjectUpdate(BaseModel):
    name: Title | None = None
    description: str | None = Field(default=None, max_length=10_000)
    instructions: str | None = Field(default=None, max_length=30_000)
    default_provider: str | None = Field(default=None, max_length=80)


class ProjectResponse(ApiModel):
    id: str
    owner_id: str
    name: str
    description: str
    instructions: str
    default_provider: str | None
    created_at: datetime
    updated_at: datetime


class ConversationCreate(BaseModel):
    title: Title = "New conversation"
    project_id: str | None = None
    provider: str | None = Field(default=None, max_length=80)


class ConversationUpdate(BaseModel):
    title: Title


class ConversationResponse(ApiModel):
    id: str
    project_id: str | None
    user_id: str
    title: str
    provider: str | None
    created_at: datetime
    updated_at: datetime


class MessageResponse(ApiModel):
    id: str
    conversation_id: str
    role: str
    content: str
    provider: str | None
    model: str | None
    input_tokens: int
    output_tokens: int
    estimated_cost_microusd: int | None
    created_at: datetime


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=20_000)
    conversation_id: str | None = None
    project_id: str | None = None
    provider: str | None = Field(default=None, max_length=80)


class ChatResponse(BaseModel):
    conversation_id: str
    message: str
    provider: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_microusd: int | None = None


class KnowledgeCreate(BaseModel):
    title: Title
    content: str = Field(min_length=1, max_length=2_000_000)
    project_id: str | None = None
    source_type: Literal["text", "markdown", "file"] = "text"


class KnowledgeResponse(ApiModel):
    id: str
    user_id: str
    project_id: str | None
    title: str
    content: str
    source_type: str
    created_at: datetime


class ProviderInfo(BaseModel):
    name: str
    model: str
    configured: bool
    healthy: bool
    is_default: bool = False


class ToolExecuteRequest(BaseModel):
    arguments: dict[str, object] = Field(default_factory=dict)


class ToolInfo(BaseModel):
    name: str
    description: str


class ToolExecuteResponse(BaseModel):
    ok: bool
    output: str
    metadata: dict[str, object] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded", "error"]
    service: str
    version: str
    environment: str
    checks: dict[str, bool] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    error: str
    message: str
    request_id: str | None = None
