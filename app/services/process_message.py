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
from app.vault.backend import get_vault_backend
from app.vault.index import upsert_vault_note_index

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProcessMessageResult:
    """Result of a full capture pipeline (LLM + vault + DB)."""

    classification: ClassificationResult
    entry_id: int
    vault_path: str
    status: str


async def _resolve_append_target(
    db: AsyncSession, target_title: str
) -> str | None:
    """Find the newest entry with a matching title and return vault_path.

    Returns ``None`` if no entry matches or the vault file is gone — the
    caller should then fall back to ``create``.
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


def _compensate_orphan_create(vault, vault_relative: str | None) -> None:
    """Delete a newly created vault file after a failed DB commit (E28-3)."""
    if not vault_relative:
        return
    try:
        if vault.delete_note(vault_relative):
            logger.info("Compensated orphan vault file after DB failure: %s", vault_relative)
    except Exception:
        logger.exception(
            "Failed to compensate orphan vault file at %s", vault_relative
        )


async def process_text_message(
    text: str,
    db: AsyncSession,
    *,
    telegram_update_id: int | None = None,
    telegram_message_id: int | None = None,
    telegram_chat_id: int | None = None,
    kind: str = "text",
) -> ProcessMessageResult | None:
    """Classify the message and persist entry + vault file.

    Returns ``None`` when an entry with the same ``telegram_update_id``
    already exists (Telegram retry / race) — then nothing happens; the
    caller should not send a second confirmation to Telegram.

    With ``telegram_update_id`` set, the UNIQUE claim is secured via ``flush``
    *before* the vault write (E28-3 idempotency window). Newly created
    files are deleted again on DB error (compensation).
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
    vault = get_vault_backend()

    # Resolve append vs create intent — write only after optional claim.
    will_append = False
    target_relative: str | None = None
    if result.action == "append" and result.target_title:
        target_relative = await _resolve_append_target(db, result.target_title)
        if target_relative is not None and vault.note_exists(target_relative):
            will_append = True
        else:
            logger.info(
                "Append fallback to create: target_title=%r not resolvable",
                result.target_title,
            )
            result.action = "create"
            result.target_title = None

    entry = Entry(
        title=result.title,
        category=result.category,
        summary=result.summary,
        raw_input=text,
        vault_path=None,
        telegram_update_id=telegram_update_id,
        telegram_message_id=telegram_message_id,
        telegram_chat_id=telegram_chat_id,
        kind=kind,
        status="processed",
        prompt_version=getattr(llm, "prompt_version", None)
        or settings.seiton_prompt_version,
    )
    db.add(entry)

    # UNIQUE claim before vault mutation (closes race: two workers writing files)
    if telegram_update_id is not None:
        try:
            await db.flush()
        except IntegrityError:
            await db.rollback()
            logger.warning(
                "Race on telegram_update_id=%s at flush — skipping before vault write",
                telegram_update_id,
            )
            return None

    created_new_file = False
    vault_relative: str | None = None
    entry_status = "processed"

    try:
        if will_append and target_relative is not None:
            vault_relative = vault.append_to_note(target_relative, result)
            entry_status = "appended"
        else:
            vault_relative = vault.write_note(result)
            created_new_file = True
            entry_status = "processed"

        entry.vault_path = vault_relative
        entry.status = entry_status
        await db.commit()
        await db.refresh(entry)
    except IntegrityError:
        await db.rollback()
        if created_new_file:
            _compensate_orphan_create(vault, vault_relative)
        logger.warning(
            "Race on telegram_update_id=%s after IntegrityError; "
            "compensated orphan=%s path=%s",
            telegram_update_id,
            created_new_file,
            vault_relative,
        )
        return None
    except Exception:
        await db.rollback()
        if created_new_file:
            _compensate_orphan_create(vault, vault_relative)
        raise

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
