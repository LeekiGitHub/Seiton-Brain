import json
import logging

import httpx
from fastapi import APIRouter, Header, HTTPException, Request
from sqlalchemy import select

from app.config import settings
from app.db.session import SessionLocal
from app.models.entry import Entry
from app.telegram.client import send_message
from app.telegram.commands import handle_command
from app.worker.tasks import (
    process_ask_message_task,
    process_text_message_task,
    process_voice_message_task,
)

router = APIRouter()
logger = logging.getLogger(__name__)

# Update-Typen, die Telegram sendet, die wir aber bewusst nicht verarbeiten.
# Werden mit 200 OK ohne Log-Warning beantwortet — Telegram retried sonst.
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
    """True wenn bereits ein Entry mit dieser telegram_update_id existiert."""
    async with SessionLocal() as db:
        result = await db.execute(
            select(Entry.id)
            .where(Entry.telegram_update_id == update_id)
            .limit(1)
        )
        return result.scalar_one_or_none() is not None


def _get_allowed_user_ids() -> set[int] | None:
    """Parsed Allowlist aus TELEGRAM_ALLOWED_USER_IDS.

    Rückgabe ``None`` bedeutet: Allowlist nicht konfiguriert -> alle erlaubt.
    Rückgabe ``set[int]``: nur diese User-IDs sind erlaubt (strict).
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
    """Verarbeitet ein einzelnes Telegram-Update — **transport-agnostisch**.

    Genutzt vom Webhook (``POST /webhook``) und vom Long-Polling-Poller
    (``app.telegram.polling``). Behandelt Allowlist, Idempotenz,
    Slash-Commands und das Einreihen in den Worker. Wirft keine Exceptions
    nach aussen (Fehler werden geloggt), damit der Poller an einem einzelnen
    Update nicht stirbt.
    """
    message = update.get("message")

    if not message:
        # Bekannte aber unsupported Update-Typen: kein Warn-Spam.
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

    try:
        if text and text.startswith("/"):
            parts = text.strip().split(maxsplit=1)
            cmd = parts[0].split("@", 1)[0].lower()
            args = parts[1].strip() if len(parts) > 1 else ""
            if cmd == "/ask":
                # RAG ist ein LLM-Call -> in den Worker, nicht synchron im
                # Request (sonst blockiert er Webhook/Poller mehrere Sekunden).
                if not args:
                    await send_message(
                        chat_id,
                        "Nutzung: /ask <frage> — ich durchsuche dein Brain "
                        "und antworte mit Quellen.",
                    )
                else:
                    process_ask_message_task.delay(args, chat_id)
                    await send_message(chat_id, "Ich durchsuche dein Brain…")
            else:
                # Andere Slash-Commands synchron — schnelle DB-Lookups, kein LLM.
                async with SessionLocal() as db:
                    reply = await handle_command(text, chat_id, db)
                if reply is not None:
                    await send_message(chat_id, reply)
        elif text:
            process_text_message_task.delay(text, chat_id, update_id, message_id)
            await send_message(chat_id, "Wird verarbeitet…")
        elif voice:
            process_voice_message_task.delay(
                voice["file_id"], chat_id, update_id, message_id
            )
            await send_message(chat_id, "Sprachnachricht wird verarbeitet…")
        else:
            await send_message(
                chat_id,
                "Aktuell werden nur Text- und Sprachnachrichten unterstützt.",
            )
    except httpx.HTTPError as exc:
        logger.warning("Telegram sendMessage failed: %s", exc)


@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
):
    if x_telegram_bot_api_secret_token != _get_secret():
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Body-Size-Limit. Wir lesen den Body selbst (statt request.json()), um den
    # Length-Check vor JSON-Parsing zu machen. Content-Length-Header reicht
    # nicht: er ist optional und manipulierbar.
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
