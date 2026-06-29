from datetime import datetime

from pydantic import BaseModel, Field

from app.llm.schemas import ClassificationResult


class CaptureRequest(BaseModel):
    text: str = Field(min_length=1, max_length=100_000)


class CaptureResponse(BaseModel):
    classification: ClassificationResult
    entry_id: int
    vault_path: str
    status: str


class ClassifyRequest(BaseModel):
    text: str = Field(min_length=1, max_length=100_000)


class EntrySummary(BaseModel):
    id: int
    title: str
    category: str
    summary: str
    vault_path: str | None
    status: str
    kind: str
    created_at: datetime


class EntryListResponse(BaseModel):
    items: list[EntrySummary]
    limit: int
    offset: int


class NoteSearchHit(BaseModel):
    title: str
    vault_path: str
    snippet: str
    category: str
    folder: str


class NoteSearchResponse(BaseModel):
    query: str
    items: list[NoteSearchHit]
    limit: int
    semantic: bool = False


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class DigestRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=200)
    days: int | None = Field(default=7, ge=1, le=365)
    limit: int = Field(default=15, ge=1, le=30)


class NoteContentResponse(BaseModel):
    vault_path: str
    content: str
    title: str | None = None
