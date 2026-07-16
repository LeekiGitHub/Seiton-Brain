import asyncio
import logging

import httpx
from celery.exceptions import Retry
from openai import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    RateLimitError,
)

from app.db.session import worker_session
from app.logging_config import bind_log_context
from app.services.answer import answer_question, format_answer_for_chat
from app.services.digest import build_digest, format_digest_for_chat
from app.services.process_message import process_text_message
from app.telegram.admin_notify import notify_admin_error
from app.telegram.client import download_file, send_message
from app.webhooks.outbound import emit_capture_event, emit_entry_failed_event
from app.transcription.voice_limits import (
    VoiceTooLargeError,
    assert_voice_within_limit,
    format_voice_too_large_message,
)
from app.transcription.whisper import transcribe_audio
from app.vault.writer import CATEGORY_FOLDERS
from app.worker.celery_app import celery_app

logger = logging.getLogger(__name__)

# Transiente Fehler, die einen Retry rechtfertigen. Bewusst keine
# Validation-/Auth-Fehler (4xx ausser 429) — die werden nie besser durch
# Warten. Wir verlassen uns auf die OpenAI-SDK-Hierarchie:
#   - RateLimitError, APITimeoutError, APIConnectionError -> spezifisch
#   - APIError -> Basisklasse, faengt 5xx und generische API-Fehler
# Daneben httpx- und Standard-Netzwerk-Fehler fuer alles davor (Telegram-
# Download, andere HTTP-Calls).
RETRYABLE_EXCEPTIONS: tuple[type[BaseException], ...] = (
    RateLimitError,
    APITimeoutError,
    APIConnectionError,
    APIError,
    httpx.HTTPError,
    ConnectionError,
    TimeoutError,
)

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
            folder = CATEGORY_FOLDERS.get(classification.category.lower(), "Notes")
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
        audio_bytes = await download_file(file_id)
        assert_voice_within_limit(len(audio_bytes))
        text = await transcribe_audio(audio_bytes)
    except VoiceTooLargeError as exc:
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
