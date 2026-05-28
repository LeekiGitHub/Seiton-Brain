import logging
import os

import httpx
from fastapi import APIRouter, Header, HTTPException, Request

from app.telegram.client import send_message
from app.worker.tasks import process_text_message_task, process_voice_message_task

router = APIRouter()
logger = logging.getLogger(__name__)


def _get_secret() -> str:
    return os.environ["TELEGRAM_WEBHOOK_SECRET"]


def _get_allowed_user_ids() -> set[int] | None:
    """Parsed Allowlist aus TELEGRAM_ALLOWED_USER_IDS.

    Rückgabe ``None`` bedeutet: Allowlist nicht konfiguriert -> alle erlaubt.
    Rückgabe ``set[int]``: nur diese User-IDs sind erlaubt (strict).
    """
    raw = os.environ.get("TELEGRAM_ALLOWED_USER_IDS", "").strip()
    if not raw:
        return None
    ids: set[int] = set()
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        try:
            ids.add(int(chunk))
        except ValueError:
            logger.warning("Invalid TELEGRAM_ALLOWED_USER_IDS entry: %r", chunk)
    return ids or None


@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
):
    if x_telegram_bot_api_secret_token != _get_secret():
        raise HTTPException(status_code=401, detail="Unauthorized")

    update = await request.json()
    message = update.get("message")

    if not message:
        return {"ok": True}

    chat_id = message.get("chat", {}).get("id")
    if not chat_id:
        return {"ok": True}

    allowed_ids = _get_allowed_user_ids()
    if allowed_ids is not None:
        user_id = message.get("from", {}).get("id")
        if user_id not in allowed_ids:
            logger.warning(
                "Rejected message from non-allowed user_id=%s chat_id=%s",
                user_id,
                chat_id,
            )
            try:
                await send_message(chat_id, "Dieser Bot ist privat.")
            except httpx.HTTPError as exc:
                logger.warning("Telegram sendMessage failed: %s", exc)
            return {"ok": True}

    text = message.get("text")
    voice = message.get("voice")

    try:
        if text:
            process_text_message_task.delay(text, chat_id)
            await send_message(chat_id, "Wird verarbeitet…")
        elif voice:
            process_voice_message_task.delay(voice["file_id"], chat_id)
            await send_message(chat_id, "Sprachnachricht wird verarbeitet…")
        else:
            await send_message(
                chat_id,
                "Aktuell werden nur Text- und Sprachnachrichten unterstützt.",
            )
    except httpx.HTTPError as exc:
        logger.warning("Telegram sendMessage failed: %s", exc)

    return {"ok": True}
