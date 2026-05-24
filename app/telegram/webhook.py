import os

import httpx
from fastapi import APIRouter, Header, HTTPException, Request

from app.telegram.client import send_message

router = APIRouter()
SECRET = os.environ["TELEGRAM_WEBHOOK_SECRET"]


@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
):
    if x_telegram_bot_api_secret_token != SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")

    update = await request.json()
    message = update.get("message")

    if not message:
        return {"ok": True}

    chat_id = message.get("chat", {}).get("id")
    text = message.get("text")

    if not chat_id:
        return {"ok": True}

    try:
        if text:
            await send_message(chat_id, f"Nachricht empfangen ✓\n\n{text}")
        else:
            await send_message(
                chat_id,
                "Nachricht empfangen — aktuell werden nur Textnachrichten unterstützt.",
            )
    except httpx.HTTPError as exc:
        print(f"Telegram sendMessage failed: {exc}")

    return {"ok": True}
