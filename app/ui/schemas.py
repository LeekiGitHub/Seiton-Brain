"""Pydantic-Schemas fuer die Web-UI (E19)."""

from datetime import datetime

from pydantic import BaseModel

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
