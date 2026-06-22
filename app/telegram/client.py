import httpx

from app.config import settings

API_URL = f"https://api.telegram.org/bot{settings.telegram_bot_token}"


async def send_message(chat_id: int, text: str) -> None:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_URL}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=10.0,
        )
        response.raise_for_status()


async def get_updates(offset: int | None = None, timeout: int = 25) -> list[dict]:
    """Holt neue Updates per Long-Polling (``getUpdates``).

    ``timeout`` ist das serverseitige Long-Poll-Fenster in Sekunden; der
    HTTP-Client-Timeout liegt bewusst darueber. ``offset`` = letzte
    verarbeitete ``update_id`` + 1 (bestaetigt aeltere Updates).
    """
    params: dict = {"timeout": timeout}
    if offset is not None:
        params["offset"] = offset
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_URL}/getUpdates",
            params=params,
            timeout=timeout + 10,
        )
        response.raise_for_status()
        return response.json().get("result", [])


async def delete_webhook(drop_pending_updates: bool = False) -> None:
    """Entfernt einen ggf. registrierten Webhook.

    Telegram erlaubt ``getUpdates`` nicht, solange ein Webhook gesetzt ist —
    der Poller ruft dies daher beim Start auf.
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_URL}/deleteWebhook",
            json={"drop_pending_updates": drop_pending_updates},
            timeout=10.0,
        )
        response.raise_for_status()


async def download_file(file_id: str) -> bytes:
    async with httpx.AsyncClient() as client:
        file_response = await client.get(
            f"{API_URL}/getFile",
            params={"file_id": file_id},
            timeout=10.0,
        )
        file_response.raise_for_status()
        file_path = file_response.json()["result"]["file_path"]

        download_response = await client.get(
            f"https://api.telegram.org/file/bot{settings.telegram_bot_token}/{file_path}",
            timeout=30.0,
        )
        download_response.raise_for_status()
        return download_response.content
