import asyncio
import logging

from app.db.session import worker_session
from app.services.process_message import process_text_message
from app.telegram.client import download_file, send_message
from app.transcription.whisper import transcribe_audio
from app.vault.writer import CATEGORY_FOLDERS
from app.worker.celery_app import celery_app

logger = logging.getLogger(__name__)


async def _process_text(text: str, chat_id: int) -> None:
    async with worker_session() as db:
        result = await process_text_message(text, db)
        folder = CATEGORY_FOLDERS.get(result.category.lower(), "Notes")
        await send_message(chat_id, f"Gespeichert als [[{result.title}]] unter {folder}")


async def _process_voice(file_id: str, chat_id: int) -> None:
    audio_bytes = await download_file(file_id)
    text = await transcribe_audio(audio_bytes)
    logger.info("Transcribed voice message for chat_id=%s: %s", chat_id, text[:80])
    await _process_text(text, chat_id)


async def _send_error(chat_id: int) -> None:
    await send_message(chat_id, "Etwas ist schiefgelaufen — bitte später nochmal versuchen.")


def _run(coro) -> None:
    asyncio.run(coro)


@celery_app.task(name="process_text_message", bind=True)
def process_text_message_task(self, text: str, chat_id: int) -> None:
    logger.info("Task %s started: process_text_message chat_id=%s", self.request.id, chat_id)
    try:
        _run(_process_text(text, chat_id))
        logger.info("Task %s done: process_text_message chat_id=%s", self.request.id, chat_id)
    except Exception:
        logger.exception("Task %s failed: process_text_message chat_id=%s", self.request.id, chat_id)
        _run(_send_error(chat_id))
        raise


@celery_app.task(name="process_voice_message", bind=True)
def process_voice_message_task(self, file_id: str, chat_id: int) -> None:
    logger.info("Task %s started: process_voice_message chat_id=%s", self.request.id, chat_id)
    try:
        _run(_process_voice(file_id, chat_id))
        logger.info("Task %s done: process_voice_message chat_id=%s", self.request.id, chat_id)
    except Exception:
        logger.exception("Task %s failed: process_voice_message chat_id=%s", self.request.id, chat_id)
        _run(_send_error(chat_id))
        raise
