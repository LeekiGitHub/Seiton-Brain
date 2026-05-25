import os

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.process_message import process_text_message
from app.telegram.client import send_message
from app.vault.writer import CATEGORY_FOLDERS

router = APIRouter()
SECRET = os.environ["TELEGRAM_WEBHOOK_SECRET"]


@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
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
        if not text:
            await send_message(
                chat_id,
                "Aktuell werden nur Textnachrichten unterstützt.",
            )
            return {"ok": True}

        result = await process_text_message(text, db)
        folder = CATEGORY_FOLDERS.get(result.category.lower(), "Notes")
        await send_message(
            chat_id,
            f"Gespeichert als [[{result.title}]] unter {folder}",
        )
    except Exception as exc:
        print(f"Message processing failed: {exc}")
        try:
            await send_message(
                chat_id,
                "Etwas ist schiefgelaufen — bitte später nochmal versuchen.",
            )
        except httpx.HTTPError as send_exc:
            print(f"Telegram sendMessage failed: {send_exc}")

    return {"ok": True}
