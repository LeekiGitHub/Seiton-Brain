"""Notizen-Verwaltung fuer die Web-UI (E19-4)."""

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas import NoteContentResponse
from app.config import settings
from app.models.vault_note_index import VaultNoteIndex
from app.ui.schemas import (
    NoteDeleteResponse,
    NoteListItem,
    NoteListResponse,
    NoteSaveResponse,
    VaultConfigResponse,
)
from app.vault.index import parse_note_file, remove_vault_note_index, upsert_vault_note_index
from app.vault.paths import resolve_vault_file
from app.vault.categories import get_category_folders
from app.vault.writer import delete_note, save_note_content

DEFAULT_NOTE_LIMIT = 50


async def list_notes(
    db: AsyncSession,
    *,
    q: str | None = None,
    folder: str | None = None,
    category: str | None = None,
    limit: int = DEFAULT_NOTE_LIMIT,
    offset: int = 0,
) -> NoteListResponse:
    stmt = select(VaultNoteIndex).order_by(VaultNoteIndex.mtime.desc())
    if folder:
        stmt = stmt.where(VaultNoteIndex.folder == folder)
    if category:
        stmt = stmt.where(VaultNoteIndex.category == category)
    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(
            or_(
                VaultNoteIndex.title.ilike(pattern),
                VaultNoteIndex.body_snippet.ilike(pattern),
                VaultNoteIndex.vault_path.ilike(pattern),
            )
        )
    stmt = stmt.offset(offset).limit(limit)
    rows = (await db.execute(stmt)).scalars().all()
    return NoteListResponse(
        items=[
            NoteListItem(
                title=row.title,
                vault_path=row.vault_path,
                folder=row.folder,
                category=row.category,
                mtime=row.mtime,
            )
            for row in rows
        ],
        limit=limit,
        offset=offset,
    )


def read_note_content(vault_path: str) -> NoteContentResponse:
    filepath = resolve_vault_file(vault_path)
    if not filepath.is_file():
        raise FileNotFoundError(vault_path)
    content = filepath.read_text(encoding="utf-8")
    title: str | None = None
    if filepath.suffix.lower() in {".md", ".markdown"}:
        try:
            title = parse_note_file(filepath).title
        except OSError:
            pass
    return NoteContentResponse(vault_path=vault_path, content=content, title=title)


async def update_note_content(
    db: AsyncSession, vault_path: str, content: str
) -> NoteSaveResponse:
    save_note_content(vault_path, content)
    await upsert_vault_note_index(db, vault_path)
    title: str | None = None
    try:
        title = read_note_content(vault_path).title
    except OSError:
        pass
    return NoteSaveResponse(vault_path=vault_path, title=title)


async def remove_note(db: AsyncSession, vault_path: str) -> NoteDeleteResponse:
    deleted = delete_note(vault_path)
    if deleted:
        await remove_vault_note_index(db, vault_path)
    return NoteDeleteResponse(vault_path=vault_path, deleted=deleted)


def load_vault_config() -> VaultConfigResponse:
    return VaultConfigResponse(
        vault_path=settings.obsidian_vault_path,
        categories=dict(get_category_folders()),
    )
