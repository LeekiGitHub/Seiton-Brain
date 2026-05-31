import logging
import os
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.llm.provider import get_llm_provider
from app.llm.schemas import ClassificationResult
from app.models.entry import Entry
from app.vault.writer import write_note

logger = logging.getLogger(__name__)


def _to_vault_relative(note_path: Path) -> str:
    """Macht den Vault-Pfad relativ zum Vault-Root fuer die DB-Spalte."""
    vault_root = Path(os.environ["OBSIDIAN_VAULT_PATH"])
    try:
        return str(note_path.relative_to(vault_root))
    except ValueError:
        # Sollte nie passieren — Writer schreibt immer unterhalb des Vault-Roots.
        # Fallback: absoluten Pfad speichern, statt den Insert zu sprengen.
        return str(note_path)


async def process_text_message(
    text: str,
    db: AsyncSession,
    *,
    telegram_update_id: int | None = None,
    telegram_message_id: int | None = None,
    telegram_chat_id: int | None = None,
    kind: str = "text",
) -> ClassificationResult | None:
    """Klassifiziert die Nachricht und persistiert Entry + Vault-Datei.

    Liefert ``None``, wenn ein Entry mit der gleichen ``telegram_update_id``
    bereits existiert (Telegram-Retry / Race) — dann passiert nichts, der
    Aufrufer sollte keine zweite Bestätigung an Telegram senden.
    """
    if telegram_update_id is not None:
        existing = await db.execute(
            select(Entry.id)
            .where(Entry.telegram_update_id == telegram_update_id)
            .limit(1)
        )
        if existing.scalar_one_or_none() is not None:
            logger.info(
                "Duplicate telegram_update_id=%s in service pre-check, skipping",
                telegram_update_id,
            )
            return None

    llm = get_llm_provider()
    result = await llm.classify(text)

    # Erst die Vault-Datei schreiben — der Writer findet einen kollisionsfreien
    # Pfad (Title.md / Title (2).md / Title (3).md / ...). Den finalen Pfad
    # speichern wir am Entry, damit wir spaeter z.B. Append-Updates wieder an
    # die richtige Datei adressieren koennen (E3-2).
    note_path = write_note(result)
    vault_relative = _to_vault_relative(note_path)

    entry = Entry(
        title=result.title,
        category=result.category,
        summary=result.summary,
        raw_input=text,
        vault_path=vault_relative,
        telegram_update_id=telegram_update_id,
        telegram_message_id=telegram_message_id,
        telegram_chat_id=telegram_chat_id,
        kind=kind,
    )
    db.add(entry)
    try:
        await db.commit()
    except IntegrityError:
        # Race-Fallback: zwischen Pre-Check und Commit hat ein anderer Lauf
        # den gleichen update_id eingefuegt. UNIQUE-Constraint hat uns
        # gerettet. Die Vault-Datei wurde aber schon geschrieben — sie bleibt
        # als Schatten-Datei liegen (gleicher Titel -> hat ein
        # Kollisions-Suffix bekommen). Race ist in der Praxis nahezu
        # unmoeglich (Telegram-Retries kommen Sekunden auseinander).
        await db.rollback()
        logger.warning(
            "Race on telegram_update_id=%s after IntegrityError; "
            "orphan vault file may exist at %s",
            telegram_update_id,
            note_path,
        )
        return None

    return result
