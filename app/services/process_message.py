import logging

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.llm.provider import get_llm_provider
from app.llm.schemas import ClassificationResult
from app.models.entry import Entry
from app.vault.writer import write_note

logger = logging.getLogger(__name__)


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

    entry = Entry(
        title=result.title,
        category=result.category,
        summary=result.summary,
        raw_input=text,
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
        # den gleichen update_id eingefügt. UNIQUE-Constraint hat uns gerettet.
        await db.rollback()
        logger.info(
            "Race on telegram_update_id=%s, skipping after IntegrityError",
            telegram_update_id,
        )
        return None

    write_note(result)
    return result
