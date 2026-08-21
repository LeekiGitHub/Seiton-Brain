import asyncio
import logging

import httpx
from celery.exceptions import Retry
from openai import (
    APIConnectionError,
    APITimeoutError,
    InternalServerError,
    RateLimitError,
)
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.config import settings
from app.db.session import worker_session
from app.logging_config import bind_log_context
from app.models.entry import Entry
from app.services.answer import answer_question, format_answer_for_chat
from app.services.digest import build_digest, format_digest_for_chat
from app.services.document_capture import (
    compose_capture_text,
    extract_document_text,
)
from app.services.process_message import process_text_message
from app.telegram.admin_notify import notify_admin_error
from app.telegram.client import download_file, send_message
from app.webhooks.outbound import emit_capture_event, emit_entry_failed_event
from app.transcription.voice_cache import (
    delete_voice_cache,
    load_voice_cache,
    save_voice_cache,
)
from app.transcription.voice_limits import (
    VoiceTooLargeError,
    assert_voice_within_limit,
    format_voice_too_large_message,
)
from app.transcription.whisper import transcribe_audio
from app.vault.categories import folder_for_category
from app.worker.celery_app import celery_app

logger = logging.getLogger(__name__)

# Transiente Fehler, die einen Retry rechtfertigen (E28-5).
# Bewusst KEIN ``APIError`` (Basisklasse) — die wuerde 4xx/Auth mitretryen.
# OpenAI: RateLimit (429), Timeout, Connection, InternalServerError (5xx).
# httpx.RequestError = Netzwerk (nicht HTTPStatusError/4xx).
RETRYABLE_EXCEPTIONS: tuple[type[BaseException], ...] = (
    RateLimitError,
    APITimeoutError,
    APIConnectionError,
    InternalServerError,
    httpx.RequestError,
    ConnectionError,
    TimeoutError,
)

# Capture-Kinds, fuer die bei permanentem Fehler ein Entry mit status=failed
# angelegt wird (Ask/Digest erzeugen keinen Entry).
_CAPTURE_FAIL_KINDS = frozenset({"text", "voice", "document", "photo"})

# Celery-Retry-Konfiguration. Exponentieller Backoff mit Jitter, deckelt
# bei 60s, gibt nach 3 Versuchen auf. Auf die Art "spuert" der User
# einen Retry kaum (Telegram-Bestaetigung kommt halt 1-2s spaeter), aber
# transiente OpenAI-Hiccups (429, 5xx) brennen nicht mehr die Notiz weg.
RETRY_KWARGS = {
    "autoretry_for": RETRYABLE_EXCEPTIONS,
    "retry_backoff": True,
    "retry_backoff_max": 60,
    "retry_jitter": True,
    "max_retries": 3,
}


async def _process_text(
    text: str,
    chat_id: int,
    *,
    telegram_update_id: int | None = None,
    telegram_message_id: int | None = None,
    kind: str = "text",
) -> None:
    async with worker_session() as db:
        result = await process_text_message(
            text,
            db,
            telegram_update_id=telegram_update_id,
            telegram_message_id=telegram_message_id,
            telegram_chat_id=chat_id,
            kind=kind,
        )
        if result is None:
            logger.info(
                "Skipped confirmation for duplicate telegram_update_id=%s",
                telegram_update_id,
            )
            return
        classification = result.classification
        if classification.action == "append" and classification.target_title:
            message = f"Ergänzt: [[{classification.target_title}]]"
        else:
            folder = folder_for_category(classification.category)
            message = f"Gespeichert als [[{classification.title}]] unter {folder}"
        await send_message(chat_id, message)
        await emit_capture_event(
            result,
            kind=kind,
            telegram_chat_id=chat_id,
            telegram_update_id=telegram_update_id,
        )


async def _process_voice(
    file_id: str,
    chat_id: int,
    *,
    telegram_update_id: int | None = None,
    telegram_message_id: int | None = None,
) -> None:
    try:
        audio_bytes = load_voice_cache(file_id)
        if audio_bytes is None:
            audio_bytes = await download_file(file_id)
            assert_voice_within_limit(len(audio_bytes))
            save_voice_cache(file_id, audio_bytes)
        else:
            assert_voice_within_limit(len(audio_bytes))
        text = await transcribe_audio(audio_bytes)
    except VoiceTooLargeError as exc:
        delete_voice_cache(file_id)
        logger.info(
            "Voice too large chat_id=%s size=%s limit=%s",
            chat_id,
            exc.size_bytes,
            exc.max_bytes,
        )
        await send_message(chat_id, format_voice_too_large_message(exc.max_bytes))
        return
    logger.info("Transcribed voice message for chat_id=%s: %s", chat_id, text[:80])
    await _process_text(
        text,
        chat_id,
        telegram_update_id=telegram_update_id,
        telegram_message_id=telegram_message_id,
        kind="voice",
    )
    delete_voice_cache(file_id)


async def _process_document(
    file_id: str,
    file_name: str,
    caption: str | None,
    chat_id: int,
    *,
    telegram_update_id: int | None = None,
    telegram_message_id: int | None = None,
    kind: str = "document",
) -> None:
    data = await download_file(file_id)
    if len(data) > settings.telegram_document_max_bytes:
        limit_mb = settings.telegram_document_max_bytes / 1024 / 1024
        await send_message(
            chat_id,
            f"Datei zu groß (max. {limit_mb:.0f} MB) — bitte verkleinern.",
        )
        return

    extracted = await asyncio.to_thread(extract_document_text, data, file_name)
    if not extracted:
        await send_message(
            chat_id,
            "Aus der Datei ließ sich kein Text extrahieren. Bei Scans/Fotos: "
            "OCR (SEITON_OCR_ENABLED) oder Vision (SEITON_VISION_ENABLED) "
            "aktivieren — siehe docs/ocr.md und docs/vision.md.",
        )
        return

    logger.info(
        "Extracted %s chars from %s for chat_id=%s", len(extracted), file_name, chat_id
    )
    await _process_text(
        compose_capture_text(extracted, file_name=file_name, caption=caption),
        chat_id,
        telegram_update_id=telegram_update_id,
        telegram_message_id=telegram_message_id,
        kind=kind,
    )


async def _process_ask(question: str, chat_id: int) -> None:
    async with worker_session() as db:
        result = await answer_question(question, db)
    await send_message(chat_id, format_answer_for_chat(result))


async def _process_digest(topic: str, chat_id: int) -> None:
    async with worker_session() as db:
        result = await build_digest(topic, db)
    await send_message(chat_id, format_digest_for_chat(result))


async def _send_error(chat_id: int) -> None:
    await send_message(chat_id, "Etwas ist schiefgelaufen — bitte später nochmal versuchen.")


def _failed_entry_title(raw_input: str | None, exc: BaseException) -> str:
    src = (raw_input or "").strip() or type(exc).__name__
    first_line = src.split("\n", 1)[0].strip() or "Fehlgeschlagen"
    if len(first_line) > 80:
        first_line = first_line[:77] + "..."
    return f"[Fehler] {first_line}"[:255]


async def _record_failed_entry(
    *,
    exc: BaseException,
    chat_id: int | None,
    telegram_update_id: int | None,
    kind: str | None,
    raw_input: str | None,
) -> None:
    """Persistiert ``entries.status=failed`` bei permanenten Capture-Fehlern (E28-5).

    Ask/Digest erzeugen keinen Entry. Bei vorhandenem ``telegram_update_id``
    wird ein bestehender Eintrag auf failed gesetzt (falls vorhanden), sonst
    neu angelegt. Fehler hier werden nur geloggt — der User hat die Meldung
    schon bekommen.
    """
    if kind not in _CAPTURE_FAIL_KINDS:
        return

    summary = f"{type(exc).__name__}: {exc}"[:2000]
    title = _failed_entry_title(raw_input, exc)
    entry_kind = kind if len(kind) <= 10 else "text"

    try:
        async with worker_session() as db:
            if telegram_update_id is not None:
                existing = (
                    await db.execute(
                        select(Entry)
                        .where(Entry.telegram_update_id == telegram_update_id)
                        .limit(1)
                    )
                ).scalar_one_or_none()
                if existing is not None:
                    existing.status = "failed"
                    existing.summary = summary
                    if not existing.title.startswith("[Fehler]"):
                        existing.title = title
                    await db.commit()
                    logger.info(
                        "Marked entry id=%s as failed (telegram_update_id=%s)",
                        existing.id,
                        telegram_update_id,
                    )
                    return

            entry = Entry(
                title=title,
                category="note",
                summary=summary,
                raw_input=raw_input,
                vault_path=None,
                telegram_update_id=telegram_update_id,
                telegram_chat_id=chat_id,
                kind=entry_kind,
                status="failed",
                prompt_version=settings.seiton_prompt_version,
            )
            db.add(entry)
            try:
                await db.commit()
            except IntegrityError:
                await db.rollback()
                logger.warning(
                    "Could not insert failed entry (duplicate telegram_update_id=%s)",
                    telegram_update_id,
                )
                return
            logger.info(
                "Recorded failed entry id=%s kind=%s",
                entry.id,
                entry_kind,
            )
    except Exception:
        logger.exception("Failed to persist entries.status=failed")


async def _handle_permanent_failure(
    chat_id: int,
    exc: BaseException,
    *,
    task_name: str,
    task_id: str | None,
    telegram_update_id: int | None,
    kind: str | None = None,
    raw_input: str | None = None,
) -> None:
    await _send_error(chat_id)
    await _record_failed_entry(
        exc=exc,
        chat_id=chat_id,
        telegram_update_id=telegram_update_id,
        kind=kind,
        raw_input=raw_input,
    )
    await notify_admin_error(
        task_name=task_name,
        error=exc,
        chat_id=chat_id,
        task_id=task_id,
        telegram_update_id=telegram_update_id,
    )
    await emit_entry_failed_event(
        task_name=task_name,
        error=exc,
        chat_id=chat_id,
        task_id=task_id,
        telegram_update_id=telegram_update_id,
        kind=kind,
        raw_input=raw_input,
    )


def _run(coro) -> None:
    asyncio.run(coro)


@celery_app.task(name="process_text_message", bind=True, **RETRY_KWARGS)
def process_text_message_task(
    self,
    text: str,
    chat_id: int,
    telegram_update_id: int | None = None,
    telegram_message_id: int | None = None,
) -> None:
    bind_log_context(
        task_id=self.request.id,
        telegram_update_id=telegram_update_id,
    )
    logger.info("process_text_message started chat_id=%s", chat_id)
    try:
        _run(
            _process_text(
                text,
                chat_id,
                telegram_update_id=telegram_update_id,
                telegram_message_id=telegram_message_id,
            )
        )
        logger.info("process_text_message done chat_id=%s", chat_id)
    except Retry:
        # Celery hat den Retry geplant. Nicht als "echten" Fehler behandeln,
        # keine Telegram-Nachricht senden — der User wuerde sonst pro Retry
        # eine "schiefgelaufen"-Meldung bekommen.
        raise
    except Exception as exc:
        logger.exception("process_text_message failed permanently chat_id=%s", chat_id)
        _run(
            _handle_permanent_failure(
                chat_id,
                exc,
                task_name="process_text_message",
                task_id=self.request.id,
                telegram_update_id=telegram_update_id,
                kind="text",
                raw_input=text,
            )
        )
        raise


@celery_app.task(name="process_ask_message", bind=True, **RETRY_KWARGS)
def process_ask_message_task(self, question: str, chat_id: int) -> None:
    bind_log_context(task_id=self.request.id)
    logger.info("process_ask_message started chat_id=%s", chat_id)
    try:
        _run(_process_ask(question, chat_id))
        logger.info("process_ask_message done chat_id=%s", chat_id)
    except Retry:
        raise
    except Exception as exc:
        logger.exception("process_ask_message failed permanently chat_id=%s", chat_id)
        _run(
            _handle_permanent_failure(
                chat_id,
                exc,
                task_name="process_ask_message",
                task_id=self.request.id,
                telegram_update_id=None,
                kind="qa",
                raw_input=question,
            )
        )
        raise


@celery_app.task(name="process_digest_message", bind=True, **RETRY_KWARGS)
def process_digest_message_task(self, topic: str, chat_id: int) -> None:
    bind_log_context(task_id=self.request.id)
    logger.info("process_digest_message started chat_id=%s", chat_id)
    try:
        _run(_process_digest(topic, chat_id))
        logger.info("process_digest_message done chat_id=%s", chat_id)
    except Retry:
        raise
    except Exception as exc:
        logger.exception("process_digest_message failed permanently chat_id=%s", chat_id)
        _run(
            _handle_permanent_failure(
                chat_id,
                exc,
                task_name="process_digest_message",
                task_id=self.request.id,
                telegram_update_id=None,
                kind="digest",
                raw_input=topic,
            )
        )
        raise


@celery_app.task(name="process_document_message", bind=True, **RETRY_KWARGS)
def process_document_message_task(
    self,
    file_id: str,
    file_name: str,
    caption: str | None,
    chat_id: int,
    telegram_update_id: int | None = None,
    telegram_message_id: int | None = None,
    kind: str = "document",
) -> None:
    bind_log_context(
        task_id=self.request.id,
        telegram_update_id=telegram_update_id,
    )
    logger.info(
        "process_document_message started chat_id=%s file=%s", chat_id, file_name
    )
    try:
        _run(
            _process_document(
                file_id,
                file_name,
                caption,
                chat_id,
                telegram_update_id=telegram_update_id,
                telegram_message_id=telegram_message_id,
                kind=kind,
            )
        )
        logger.info("process_document_message done chat_id=%s", chat_id)
    except Retry:
        raise
    except Exception as exc:
        logger.exception(
            "process_document_message failed permanently chat_id=%s", chat_id
        )
        _run(
            _handle_permanent_failure(
                chat_id,
                exc,
                task_name="process_document_message",
                task_id=self.request.id,
                telegram_update_id=telegram_update_id,
                kind=kind,
                raw_input=file_name,
            )
        )
        raise


@celery_app.task(name="process_voice_message", bind=True, **RETRY_KWARGS)
def process_voice_message_task(
    self,
    file_id: str,
    chat_id: int,
    telegram_update_id: int | None = None,
    telegram_message_id: int | None = None,
) -> None:
    bind_log_context(
        task_id=self.request.id,
        telegram_update_id=telegram_update_id,
    )
    logger.info("process_voice_message started chat_id=%s", chat_id)
    try:
        _run(
            _process_voice(
                file_id,
                chat_id,
                telegram_update_id=telegram_update_id,
                telegram_message_id=telegram_message_id,
            )
        )
        logger.info("process_voice_message done chat_id=%s", chat_id)
    except Retry:
        raise
    except Exception as exc:
        logger.exception("process_voice_message failed permanently chat_id=%s", chat_id)
        _run(
            _handle_permanent_failure(
                chat_id,
                exc,
                task_name="process_voice_message",
                task_id=self.request.id,
                telegram_update_id=telegram_update_id,
                kind="voice",
            )
        )
        raise
