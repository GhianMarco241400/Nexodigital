from datetime import datetime
from typing import Literal

from pydantic import BaseModel

ReviewMode = Literal["heuristic", "llm", "hybrid"]
ReviewProvider = Literal["gemini", "groq", "openrouter", "ollama", "openai"]


class ReviewConfigOut(BaseModel):
    mode: ReviewMode
    provider: ReviewProvider
    model: str
    ai_enabled: bool
    has_api_key: bool
    updated_by: str | None = None
    updated_at: datetime | None = None


class ReviewConfigUpdate(BaseModel):
    mode: ReviewMode | None = None
    provider: ReviewProvider | None = None
    model: str | None = None


class ReviewTestResult(BaseModel):
    ok: bool
    provider: ReviewProvider | None = None
    model: str | None = None
    latency_ms: int | None = None
    error: str | None = None
