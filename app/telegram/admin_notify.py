"""Telegram-DM an den Admin bei dauerhaften Worker-Fehlern (E10-3)."""

from __future__ import annotations

import logging
import traceback

from app.config import settings
from app.telegram.client import send_message

logger = logging.getLogger(__name__)

# Telegram-Limit ist 4096 Zeichen; Stacktrace kuerzen wir bewusst.
_MAX_ERROR_CHARS = 800
_MAX_MESSAGE_CHARS = 3900


def _admin_chat_id() -> int | None:
    raw = settings.telegram_admin_chat_id.strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        logger.warning(
            "Invalid TELEGRAM_ADMIN_CHAT_ID=%r — admin error notify disabled",
            raw,
        )
        return None


def format_admin_error_message(
    *,
    task_name: str,
    error: BaseException,
    chat_id: int | None = None,
    task_id: str | None = None,
    telegram_update_id: int | None = None,
) -> str:
    lines = [
        "Seiton Brain — Fehler",
        "",
        f"Task: {task_name}",
    ]
    if task_id:
        lines.append(f"Task-ID: {task_id}")
    if chat_id is not None:
        lines.append(f"Chat: {chat_id}")
    if telegram_update_id is not None:
        lines.append(f"Update: {telegram_update_id}")
    lines.extend(["", f"{type(error).__name__}: {error}"])

    tb = "".join(
        traceback.format_exception(type(error), error, error.__traceback__)
    ).strip()
    if tb:
        if len(tb) > _MAX_ERROR_CHARS:
            tb = tb[: _MAX_ERROR_CHARS - 3] + "..."
        lines.extend(["", "Traceback:", tb])

    message = "\n".join(lines)
    if len(message) > _MAX_MESSAGE_CHARS:
        message = message[: _MAX_MESSAGE_CHARS - 3] + "..."
    return message


async def notify_admin_error(
    *,
    task_name: str,
    error: BaseException,
    chat_id: int | None = None,
    task_id: str | None = None,
    telegram_update_id: int | None = None,
) -> None:
    """Sendet eine DM an den Admin. Fehler beim Senden werden nur geloggt."""
    admin_id = _admin_chat_id()
    if admin_id is None:
        return

    text = format_admin_error_message(
        task_name=task_name,
        error=error,
        chat_id=chat_id,
        task_id=task_id,
        telegram_update_id=telegram_update_id,
    )
    try:
        await send_message(admin_id, text)
    except Exception:
        logger.exception("Failed to send admin error notification to chat_id=%s", admin_id)
