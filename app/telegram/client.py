import os

import httpx

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"


async def send_message(chat_id: int, text: str) -> None:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_URL}/sendMessage",
            json={"chat_id": chat_id, "text": text},
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
            f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}",
            timeout=30.0,
        )
        download_response.raise_for_status()
        return download_response.content
