import json
import logging

import httpx
from fastapi import APIRouter, Header, HTTPException, Request
from sqlalchemy import select

from app.config import settings
from app.setup.status import is_telegram_configured
from app.db.session import SessionLocal
from app.models.entry import Entry
from app.telegram.client import send_message
from app.telegram.commands import handle_command
from app.transcription.voice_limits import format_voice_too_large_message
from app.services.document_capture import photo_extraction_ready, supported_document
from app.worker.tasks import (
    process_ask_message_task,
    process_digest_message_task,
    process_document_message_task,
    process_text_message_task,
    process_voice_message_task,
)

router = APIRouter()
logger = logging.getLogger(__name__)

# Update types Telegram sends that we deliberately ignore.
# Answer 200 OK without a log warning — otherwise Telegram retries.
# Quelle: https://core.telegram.org/bots/api#update
KNOWN_UNSUPPORTED_UPDATE_KEYS = frozenset(
    {
        "edited_message",
        "channel_post",
        "edited_channel_post",
        "business_connection",
        "business_message",
        "edited_business_message",
        "deleted_business_messages",
        "message_reaction",
        "message_reaction_count",
        "inline_query",
        "chosen_inline_result",
        "callback_query",
        "shipping_query",
        "pre_checkout_query",
        "purchased_paid_media",
        "poll",
        "poll_answer",
        "my_chat_member",
        "chat_member",
        "chat_join_request",
        "chat_boost",
        "removed_chat_boost",
    }
)


def _get_secret() -> str:
    return settings.telegram_webhook_secret


async def _is_duplicate_update(update_id: int) -> bool:
    """True if an entry with this telegram_update_id already exists."""
    async with SessionLocal() as db:
        result = await db.execute(
            select(Entry.id)
            .where(Entry.telegram_update_id == update_id)
            .limit(1)
        )
        return result.scalar_one_or_none() is not None


def _get_allowed_user_ids() -> set[int] | None:
    """Parse allowlist from TELEGRAM_ALLOWED_USER_IDS.

    Returning ``None`` means: allowlist not configured → everyone allowed.
    Returning ``set[int]``: only those user IDs are allowed (strict).
    """
    raw = settings.telegram_allowed_user_ids.strip()
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


async def process_update(update: dict) -> None:
    """Process a single Telegram update — **transport-agnostic**.

    Used by the webhook (``POST /webhook``) and the long-polling poller
    (``app.telegram.polling``). Handles allowlist, idempotency,
    slash commands and enqueueing to the worker. Raises no exceptions
    outward (errors are logged) so the poller does not die on one update.
    """
    message = update.get("message")

    if not message:
        # Known but unsupported update types: no warning spam.
        unsupported = KNOWN_UNSUPPORTED_UPDATE_KEYS.intersection(update.keys())
        if unsupported:
            logger.debug(
                "Ignoring unsupported update types: %s",
                ", ".join(sorted(unsupported)),
            )
        else:
            logger.debug(
                "Update without 'message' field: keys=%s",
                list(update.keys()),
            )
        return

    chat_id = message.get("chat", {}).get("id")
    if not chat_id:
        return

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
            return

    update_id = update.get("update_id")
    if update_id is not None and await _is_duplicate_update(update_id):
        logger.info(
            "Duplicate update_id=%s chat_id=%s, silently ignoring",
            update_id,
            chat_id,
        )
        return

    message_id = message.get("message_id")
    text = message.get("text")
    voice = message.get("voice")
    document = message.get("document")
    photo = message.get("photo")
    caption = message.get("caption")

    try:
        if text and text.startswith("/"):
            parts = text.strip().split(maxsplit=1)
            cmd = parts[0].split("@", 1)[0].lower()
            args = parts[1].strip() if len(parts) > 1 else ""
            if cmd == "/ask":
                # RAG is an LLM call → push to the worker, not sync in the
                # request (otherwise webhook/poller blocks for seconds).
                if not args:
                    await send_message(
                        chat_id,
                        "Nutzung: /ask <frage> — ich durchsuche dein Brain "
                        "und antworte mit Quellen.",
                    )
                else:
                    process_ask_message_task.delay(args, chat_id)
                    await send_message(chat_id, "Ich durchsuche dein Brain…")
            elif cmd == "/digest":
                if not args:
                    await send_message(
                        chat_id,
                        "Nutzung: /digest <thema> — z. B. Ideas, Work oder "
                        "ein Stichwort. Ich fasse passende Notizen zusammen.",
                    )
                else:
                    process_digest_message_task.delay(args, chat_id)
                    await send_message(chat_id, "Ich erstelle deinen Digest…")
            else:
                # Other slash commands sync — fast DB lookups, no LLM.
                async with SessionLocal() as db:
                    reply = await handle_command(text, chat_id, db)
                if reply is not None:
                    await send_message(chat_id, reply)
        elif text:
            process_text_message_task.delay(text, chat_id, update_id, message_id)
            await send_message(chat_id, "Wird verarbeitet…")
        elif voice:
            file_size = voice.get("file_size")
            if (
                file_size is not None
                and file_size > settings.telegram_voice_max_bytes
            ):
                await send_message(
                    chat_id,
                    format_voice_too_large_message(settings.telegram_voice_max_bytes),
                )
            else:
                process_voice_message_task.delay(
                    voice["file_id"], chat_id, update_id, message_id
                )
                await send_message(chat_id, "Sprachnachricht wird verarbeitet…")
        elif document:
            file_name = (document.get("file_name") or "").strip() or "dokument"
            file_size = document.get("file_size")
            if (
                file_size is not None
                and file_size > settings.telegram_document_max_bytes
            ):
                limit_mb = settings.telegram_document_max_bytes / 1024 / 1024
                await send_message(
                    chat_id,
                    f"Datei zu groß (max. {limit_mb:.0f} MB) — bitte verkleinern.",
                )
            elif not supported_document(file_name):
                await send_message(
                    chat_id,
                    f"Dateityp von „{file_name}“ wird nicht unterstützt "
                    "(Markdown, Text, PDF, Word, PowerPoint; Bilder mit "
                    "OCR/Vision).",
                )
            else:
                process_document_message_task.delay(
                    document["file_id"],
                    file_name,
                    caption,
                    chat_id,
                    update_id,
                    message_id,
                )
                await send_message(chat_id, "Dokument wird verarbeitet…")
        elif photo:
            if not photo_extraction_ready():
                await send_message(
                    chat_id,
                    "Foto-Capture braucht OCR (SEITON_OCR_ENABLED) oder "
                    "Vision (SEITON_VISION_ENABLED) — siehe docs/ocr.md "
                    "und docs/vision.md.",
                )
            else:
                largest = max(photo, key=lambda p: p.get("file_size") or 0)
                file_size = largest.get("file_size")
                if (
                    file_size is not None
                    and file_size > settings.telegram_document_max_bytes
                ):
                    limit_mb = settings.telegram_document_max_bytes / 1024 / 1024
                    await send_message(
                        chat_id,
                        f"Foto zu groß (max. {limit_mb:.0f} MB).",
                    )
                else:
                    process_document_message_task.delay(
                        largest["file_id"],
                        "foto.jpg",
                        caption,
                        chat_id,
                        update_id,
                        message_id,
                        "photo",
                    )
                    await send_message(chat_id, "Foto wird verarbeitet…")
        else:
            await send_message(
                chat_id,
                "Aktuell werden Text, Sprachnachrichten, Dokumente und "
                "Fotos unterstützt.",
            )
    except httpx.HTTPError as exc:
        logger.warning("Telegram sendMessage failed: %s", exc)


@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
):
    if not is_telegram_configured():
        raise HTTPException(status_code=503, detail="Telegram not configured")

    if x_telegram_bot_api_secret_token != _get_secret():
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Body-size limit. We read the body ourselves (instead of request.json())
    # to enforce the length check before JSON parsing. Content-Length alone is
    # not enough: it is optional and spoofable.
    body = await request.body()
    if len(body) > settings.telegram_webhook_max_body_bytes:
        logger.warning(
            "Webhook body too large: %d bytes (limit %d)",
            len(body),
            settings.telegram_webhook_max_body_bytes,
        )
        raise HTTPException(status_code=413, detail="Payload too large")

    try:
        update = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    if not isinstance(update, dict):
        raise HTTPException(status_code=400, detail="Invalid update payload")

    await process_update(update)
    return {"ok": True}
