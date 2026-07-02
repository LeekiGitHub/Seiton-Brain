"""Pydantic-Schemas fuer die Web-UI (E19)."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.api.v1.schemas import EntrySummary


class DashboardStats(BaseModel):
    total_entries: int
    entries_by_status: dict[str, int]
    entries_by_kind: dict[str, int]
    vault_notes_indexed: int
    embeddings_enabled: bool


class VaultNotePreview(BaseModel):
    title: str
    vault_path: str
    folder: str
    category: str
    mtime: datetime


class DashboardResponse(BaseModel):
    stats: DashboardStats
    recent_entries: list[EntrySummary]
    recent_vault_notes: list[VaultNotePreview]


class NoteListItem(BaseModel):
    title: str
    vault_path: str
    folder: str
    category: str
    mtime: datetime


class NoteListResponse(BaseModel):
    items: list[NoteListItem]
    limit: int
    offset: int


class NoteSaveRequest(BaseModel):
    vault_path: str = Field(min_length=1, max_length=500)
    content: str = Field(max_length=500_000)


class NoteSaveResponse(BaseModel):
    vault_path: str
    title: str | None = None


class NoteDeleteResponse(BaseModel):
    vault_path: str
    deleted: bool


class VaultConfigResponse(BaseModel):
    vault_path: str
    categories: dict[str, str]
