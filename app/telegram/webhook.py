import httpx
from fastapi import APIRouter, Header, HTTPException, Request

from app.telegram.client import send_message
from app.worker.tasks import process_text_message_task, process_voice_message_task

router = APIRouter()


def _get_secret() -> str:
    import os

    return os.environ["TELEGRAM_WEBHOOK_SECRET"]


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
        print(f"Telegram sendMessage failed: {exc}")

    return {"ok": True}
