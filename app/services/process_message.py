import logging
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.llm.provider import get_llm_provider
from app.llm.schemas import ClassificationResult
from app.models.entry import Entry
from app.vault.index import upsert_vault_note_index
from app.vault.writer import append_to_note, write_note

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProcessMessageResult:
    """Ergebnis einer vollstaendigen Capture-Pipeline (LLM + Vault + DB)."""

    classification: ClassificationResult
    entry_id: int
    vault_path: str
    status: str


def _to_vault_relative(note_path: Path) -> str:
    """Macht den Vault-Pfad relativ zum Vault-Root fuer die DB-Spalte."""
    vault_root = Path(settings.obsidian_vault_path)
    try:
        return str(note_path.relative_to(vault_root))
    except ValueError:
        # Sollte nie passieren — Writer schreibt immer unterhalb des Vault-Roots.
        # Fallback: absoluten Pfad speichern, statt den Insert zu sprengen.
        return str(note_path)


async def _resolve_append_target(
    db: AsyncSession, target_title: str
) -> str | None:
    """Findet den juengsten Entry mit passendem Titel und liefert vault_path.

    Liefert ``None``, wenn kein Eintrag passt oder die Vault-Datei verschwunden
    ist — der Caller soll dann auf ``create`` zurueckfallen.
    """
    stmt = (
        select(Entry.vault_path)
        .where(Entry.title == target_title)
        .where(Entry.vault_path.is_not(None))
        .order_by(Entry.created_at.desc())
        .limit(1)
    )
    vault_relative = (await db.execute(stmt)).scalar_one_or_none()
    if vault_relative is None:
        return None

    abs_path = Path(settings.obsidian_vault_path) / vault_relative
    if not abs_path.exists():
        logger.warning(
            "Append target %r has vault_path=%r but file is missing on disk",
            target_title,
            vault_relative,
        )
        return None

    return vault_relative


async def process_text_message(
    text: str,
    db: AsyncSession,
    *,
    telegram_update_id: int | None = None,
    telegram_message_id: int | None = None,
    telegram_chat_id: int | None = None,
    kind: str = "text",
) -> ProcessMessageResult | None:
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

    # Append vs. Create. Bei action=append versuchen wir, die Ziel-Notiz ueber
    # ihren Titel in der DB zu finden (juengster Entry). Klappt das nicht
    # (z.B. Notiz wurde manuell geloescht, oder Titel existiert nur im Vault
    # aber nicht in unserer DB), fallen wir transparent auf Create zurueck.
    entry_status = "processed"
    if result.action == "append" and result.target_title:
        target_relative = await _resolve_append_target(db, result.target_title)
        if target_relative is not None:
            note_path = append_to_note(target_relative, result)
            vault_relative = target_relative
            entry_status = "appended"
        else:
            logger.info(
                "Append fallback to create: target_title=%r not resolvable",
                result.target_title,
            )
            result.action = "create"
            result.target_title = None
            note_path = write_note(result)
            vault_relative = _to_vault_relative(note_path)
    else:
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
        status=entry_status,
        prompt_version=getattr(llm, "prompt_version", None) or settings.seiton_prompt_version,
    )
    db.add(entry)
    try:
        await db.commit()
        await db.refresh(entry)
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

    if entry_status == "appended":
        logger.info(
            "Appended to existing note %s (target_title=%r)",
            vault_relative,
            result.target_title,
        )

    await upsert_vault_note_index(db, vault_relative)

    return ProcessMessageResult(
        classification=result,
        entry_id=entry.id,
        vault_path=vault_relative,
        status=entry_status,
    )
