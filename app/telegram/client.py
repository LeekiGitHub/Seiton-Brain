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
    """Fetch new updates via long-polling (``getUpdates``).

    ``timeout`` is the server-side long-poll window in seconds; the HTTP
    client timeout sits deliberately above it. ``offset`` = last processed
    ``update_id`` + 1 (acknowledges older updates).
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
    """Remove a registered webhook if present.

    Telegram does not allow ``getUpdates`` while a webhook is set —
    the poller therefore calls this at startup.
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
