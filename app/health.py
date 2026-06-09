"""Health-Checks fuer Abhaengigkeiten (DB, Redis).

Wird vom ``GET /health``-Endpunkt genutzt. Jeder Check liefert ``"ok"`` oder
``"error"`` — Details landen im Log, nicht in der HTTP-Antwort (kein Leak von
Connection-Strings o.ae.).
"""

import logging

from redis.asyncio import Redis
from sqlalchemy import text

from app.config import settings
from app.db.session import engine

logger = logging.getLogger(__name__)

CheckResult = dict[str, str]


async def check_database() -> str:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return "ok"
    except Exception:
        logger.exception("Health check: database unreachable")
        return "error"


async def check_redis() -> str:
    client = Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        pong = await client.ping()
        if pong is True or pong == "PONG":
            return "ok"
        logger.warning("Health check: redis ping returned %r", pong)
        return "error"
    except Exception:
        logger.exception("Health check: redis unreachable")
        return "error"
    finally:
        await client.aclose()


async def run_health_checks() -> CheckResult:
    return {
        "database": await check_database(),
        "redis": await check_redis(),
    }
