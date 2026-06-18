"""Vault-Index in Postgres (E5-1) und Keyword-Suche (E17-1)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import case, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import SessionLocal
from app.models.vault_note_index import VaultNoteIndex
from app.vault.reader import VaultNote, _body_snippet, _parse_frontmatter

logger = logging.getLogger(__name__)

# Fuer ILIKE-Suche; Anzeige im LLM-Prompt bleibt bei 120 Zeichen (reader).
BODY_INDEX_CHARS = 2000
LLM_NOTE_LIMIT = 80


@dataclass(frozen=True)
class SearchHit:
    title: str
    vault_path: str
    snippet: str
    category: str
    folder: str


def _vault_root() -> Path:
    return Path(settings.obsidian_vault_path)


def _relative_vault_path(path: Path) -> str:
    return str(path.relative_to(_vault_root()))


def _file_mtime(path: Path) -> datetime:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)


def _index_body_snippet(content: str) -> str:
    return _body_snippet(content, limit=BODY_INDEX_CHARS)


def parse_note_file(path: Path) -> VaultNote:
    content = path.read_text(encoding="utf-8")
    meta = _parse_frontmatter(content)
    title = meta.get("title") or path.stem
    category = meta.get("category", "")
    folder = path.parent.name
    snippet = _body_snippet(content)
    return VaultNote(title=title, category=category, folder=folder, snippet=snippet)


def _note_to_index_row(path: Path) -> VaultNoteIndex:
    content = path.read_text(encoding="utf-8")
    meta = _parse_frontmatter(content)
    title = meta.get("title") or path.stem
    return VaultNoteIndex(
        vault_path=_relative_vault_path(path),
        title=title,
        category=meta.get("category", ""),
        folder=path.parent.name,
        body_snippet=_index_body_snippet(content),
        mtime=_file_mtime(path),
    )


def _ilike_pattern(query: str) -> str:
    escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


async def upsert_vault_note_index(db: AsyncSession, vault_relative_path: str) -> None:
    """Indexiert eine Datei (relativ zum Vault-Root). Ignoriert fehlende Pfade."""
    filepath = _vault_root() / vault_relative_path
    if not filepath.is_file():
        await remove_vault_note_index(db, vault_relative_path)
        return

    row = _note_to_index_row(filepath)
    existing = (
        await db.execute(
            select(VaultNoteIndex).where(
                VaultNoteIndex.vault_path == vault_relative_path
            )
        )
    ).scalar_one_or_none()

    if existing is None:
        db.add(row)
    else:
        existing.title = row.title
        existing.category = row.category
        existing.folder = row.folder
        existing.body_snippet = row.body_snippet
        existing.mtime = row.mtime
        existing.indexed_at = datetime.now(UTC)

    await db.commit()


async def remove_vault_note_index(db: AsyncSession, vault_relative_path: str) -> None:
    await db.execute(
        delete(VaultNoteIndex).where(VaultNoteIndex.vault_path == vault_relative_path)
    )
    await db.commit()


async def sync_vault_index_from_disk(db: AsyncSession) -> int:
    """Voller Vault-Scan — Bootstrap oder Reparatur des Index."""
    vault_path = _vault_root()
    if not vault_path.exists():
        return 0

    found_paths: set[str] = set()
    count = 0
    for md_file in sorted(vault_path.rglob("*.md")):
        if md_file.name.startswith("."):
            continue
        try:
            rel = _relative_vault_path(md_file)
            found_paths.add(rel)
            row = _note_to_index_row(md_file)
            existing = (
                await db.execute(
                    select(VaultNoteIndex).where(
                        VaultNoteIndex.vault_path == rel
                    )
                )
            ).scalar_one_or_none()
            if existing is None:
                db.add(row)
            else:
                existing.title = row.title
                existing.category = row.category
                existing.folder = row.folder
                existing.body_snippet = row.body_snippet
                existing.mtime = row.mtime
            count += 1
        except OSError as exc:
            logger.warning("Skipping unreadable vault file %s: %s", md_file, exc)

    if found_paths:
        await db.execute(
            delete(VaultNoteIndex).where(
                VaultNoteIndex.vault_path.not_in(found_paths)
            )
        )
    else:
        await db.execute(delete(VaultNoteIndex))

    await db.commit()
    logger.info("Vault index sync complete: %d notes", count)
    return count


async def ensure_vault_index(db: AsyncSession) -> None:
    total = (await db.execute(select(func.count()).select_from(VaultNoteIndex))).scalar_one()
    if total == 0 and _vault_root().exists():
        await sync_vault_index_from_disk(db)


async def list_indexed_notes(db: AsyncSession, limit: int = LLM_NOTE_LIMIT) -> list[VaultNote]:
    await ensure_vault_index(db)
    rows = (
        await db.execute(
            select(VaultNoteIndex)
            .order_by(VaultNoteIndex.mtime.desc(), VaultNoteIndex.title.asc())
            .limit(limit)
        )
    ).scalars().all()
    return [
        VaultNote(
            title=row.title,
            category=row.category,
            folder=row.folder,
            snippet=row.body_snippet[:120],
        )
        for row in rows
    ]


async def list_existing_notes(limit: int = LLM_NOTE_LIMIT) -> list[VaultNote]:
    """LLM-Kontext: liest aus dem Vault-Index (E5-1), nicht mehr ``rglob``."""
    async with SessionLocal() as db:
        return await list_indexed_notes(db, limit=limit)


async def search_vault_notes(
    db: AsyncSession, query: str, limit: int = 10
) -> list[SearchHit]:
    await ensure_vault_index(db)
    term = query.strip()
    if not term:
        return []

    pattern = _ilike_pattern(term)
    title_match = VaultNoteIndex.title.ilike(pattern)
    body_match = VaultNoteIndex.body_snippet.ilike(pattern)

    stmt = (
        select(VaultNoteIndex)
        .where(or_(title_match, body_match))
        .order_by(
            case((title_match, 0), else_=1),
            VaultNoteIndex.mtime.desc(),
        )
        .limit(limit)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return [
        SearchHit(
            title=row.title,
            vault_path=row.vault_path,
            snippet=_body_snippet(row.body_snippet, limit=120),
            category=row.category,
            folder=row.folder,
        )
        for row in rows
    ]
