"""Dashboard-Daten fuer die Web-UI (E19-2)."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas import EntrySummary
from app.config import settings
from app.models.entry import Entry
from app.models.vault_note_index import VaultNoteIndex
from app.ui.schemas import DashboardResponse, DashboardStats, VaultNotePreview

DEFAULT_RECENT_ENTRIES = 20
DEFAULT_RECENT_VAULT_NOTES = 10


def _entry_to_summary(row: Entry) -> EntrySummary:
    return EntrySummary(
        id=row.id,
        title=row.title,
        category=row.category,
        summary=row.summary,
        vault_path=row.vault_path,
        status=row.status,
        kind=row.kind,
        created_at=row.created_at,
    )


async def _count_entries(db: AsyncSession) -> int:
    return (await db.execute(select(func.count()).select_from(Entry))).scalar_one()


async def _entries_grouped(
    db: AsyncSession, column, labels: set[str]
) -> dict[str, int]:
    rows = (
        await db.execute(select(column, func.count()).group_by(column))
    ).all()
    counts = {str(status): count for status, count in rows}
    return {label: counts.get(label, 0) for label in labels}


async def load_dashboard(
    db: AsyncSession,
    *,
    entry_limit: int = DEFAULT_RECENT_ENTRIES,
    vault_limit: int = DEFAULT_RECENT_VAULT_NOTES,
) -> DashboardResponse:
    """Laedt Statistik und letzte Aktivitaet fuer das Dashboard."""
    entry_rows = (
        await db.execute(
            select(Entry)
            .order_by(Entry.created_at.desc())
            .limit(entry_limit)
        )
    ).scalars().all()

    vault_rows = (
        await db.execute(
            select(VaultNoteIndex)
            .order_by(VaultNoteIndex.mtime.desc())
            .limit(vault_limit)
        )
    ).scalars().all()

    vault_total = (
        await db.execute(select(func.count()).select_from(VaultNoteIndex))
    ).scalar_one()

    return DashboardResponse(
        stats=DashboardStats(
            total_entries=await _count_entries(db),
            entries_by_status=await _entries_grouped(
                db, Entry.status, {"processed", "appended", "failed", "rejected"}
            ),
            entries_by_kind=await _entries_grouped(
                db, Entry.kind, {"text", "voice"}
            ),
            vault_notes_indexed=vault_total,
            embeddings_enabled=settings.embeddings_enabled,
        ),
        recent_entries=[_entry_to_summary(row) for row in entry_rows],
        recent_vault_notes=[
            VaultNotePreview(
                title=row.title,
                vault_path=row.vault_path,
                folder=row.folder,
                category=row.category,
                mtime=row.mtime,
            )
            for row in vault_rows
        ],
    )
