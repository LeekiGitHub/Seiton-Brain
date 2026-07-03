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


class EditionInfo(BaseModel):
    name: str
    license: str
    description: str


class BackupInfo(BaseModel):
    command: str
    directory: str
    recent: list[str]


class SettingsViewResponse(BaseModel):
    complete: bool
    components: dict[str, bool]
    env_file: str
    vault_host_path: str
    vault_container_path: str
    llm_provider: str
    openai_model: str
    embeddings_enabled: bool
    embedding_model: str
    openai_key_masked: str
    seiton_api_key_masked: str
    telegram_configured: bool
    telegram_allowed_user_ids: str
    seiton_webhook_url: str
    categories: dict[str, str]
    edition: EditionInfo
    backup: BackupInfo


class SettingsSaveRequest(BaseModel):
    obsidian_vault_host_path: str | None = None
    openai_api_key: str = ""
    embeddings_enabled: bool | None = None
    openai_model: str = ""
    telegram_bot_token: str = ""
    telegram_webhook_secret: str = ""
    telegram_allowed_user_ids: str = ""
    seiton_api_key: str = ""
    seiton_webhook_url: str | None = None
