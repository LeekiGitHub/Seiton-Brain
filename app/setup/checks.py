"""Verbindungstests fuer den Setup-Wizard."""

from __future__ import annotations

import logging
import os
from pathlib import Path

import httpx
from openai import AsyncOpenAI
from redis.asyncio import Redis
from sqlalchemy import text

from app.config import settings
from app.db.session import engine

logger = logging.getLogger(__name__)

CheckOutcome = tuple[bool, str]


async def check_vault_path(vault_path: str) -> CheckOutcome:
    path = Path(vault_path).expanduser()
    if not path.exists():
        return False, f"Ordner existiert nicht: {path}"
    if not path.is_dir():
        return False, "Pfad ist kein Ordner"
    if not os.access(path, os.W_OK):
        return False, "Ordner ist nicht beschreibbar"
    return True, "Vault-Ordner erreichbar und beschreibbar"


async def check_openai(api_key: str) -> CheckOutcome:
    key = api_key.strip()
    if not key:
        return False, "Kein API-Key angegeben"
    try:
        client = AsyncOpenAI(api_key=key)
        await client.models.list()
        return True, "OpenAI-Verbindung erfolgreich"
    except Exception as exc:  # noqa: BLE001 — Operator-Feedback
        logger.warning("OpenAI setup check failed: %s", exc)
        return False, f"OpenAI-Test fehlgeschlagen: {exc}"


async def check_telegram(bot_token: str) -> CheckOutcome:
    token = bot_token.strip()
    if not token:
        return False, "Kein Bot-Token angegeben"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"https://api.telegram.org/bot{token}/getMe"
            )
            response.raise_for_status()
            data = response.json()
            if not data.get("ok"):
                return False, data.get("description", "Telegram API Fehler")
            username = data.get("result", {}).get("username", "?")
            return True, f"Bot @{username} erreichbar"
    except Exception as exc:  # noqa: BLE001
        logger.warning("Telegram setup check failed: %s", exc)
        return False, f"Telegram-Test fehlgeschlagen: {exc}"


async def check_database() -> CheckOutcome:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True, "Datenbank erreichbar"
    except Exception as exc:  # noqa: BLE001
        logger.warning("Database setup check failed: %s", exc)
        return False, f"Datenbank nicht erreichbar: {exc}"


async def check_redis() -> CheckOutcome:
    client = Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        pong = await client.ping()
        if pong is True or pong == "PONG":
            return True, "Redis erreichbar"
        return False, f"Redis ping unerwartet: {pong!r}"
    except Exception as exc:  # noqa: BLE001
        logger.warning("Redis setup check failed: %s", exc)
        return False, f"Redis nicht erreichbar: {exc}"
    finally:
        await client.aclose()
