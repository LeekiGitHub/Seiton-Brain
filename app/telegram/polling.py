"""Telegram Long-Polling als Alternative zum Webhook (E1-5).

Statt auf einen eingehenden Webhook zu warten (der eine oeffentlich
erreichbare HTTPS-URL braucht), pollt dieser Prozess Telegram aktiv per
``getUpdates``. Das passt zum Deployment-Leitbild "Always-on-Box beim
Kunden" (Mini-PC / Mac Mini / Heimserver): kein Reverse-Proxy, kein
Port-Forwarding, kein TLS-Zertifikat noetig.

Webhook und Polling schliessen sich gegenseitig aus — Telegram liefert
Updates entweder per Webhook *oder* per ``getUpdates``. Der Poller ruft
deshalb beim Start ``deleteWebhook`` auf.

Start::

    python -m app.telegram.polling

oder via Compose-Profil::

    docker compose --profile polling up
"""

import asyncio
import logging

import httpx

from app.config import settings
from app.logging_config import configure_logging
from app.telegram.client import delete_webhook, get_updates
from app.telegram.webhook import process_update

logger = logging.getLogger(__name__)

# Backoff nach einem fehlgeschlagenen getUpdates, damit wir bei einem
# Telegram-Ausfall nicht in einer Tight-Loop haengen.
ERROR_BACKOFF_SECONDS = 5


async def run_polling(
    *,
    poll_timeout: int | None = None,
    max_batches: int | None = None,
) -> None:
    """Pollt Telegram und verarbeitet eingehende Updates.

    ``max_batches`` begrenzt die Anzahl der ``getUpdates``-Runden (fuer
    Tests). ``None`` = unendlich (Produktion).
    """
    timeout = poll_timeout or settings.telegram_polling_timeout
    await delete_webhook()

    offset: int | None = None
    batches = 0
    while max_batches is None or batches < max_batches:
        batches += 1
        try:
            updates = await get_updates(offset, timeout=timeout)
        except httpx.HTTPError as exc:
            logger.warning("getUpdates failed: %s — retrying", exc)
            await asyncio.sleep(min(timeout, ERROR_BACKOFF_SECONDS))
            continue

        for update in updates:
            update_id = update.get("update_id")
            try:
                await process_update(update)
            except Exception:
                # Ein einzelnes kaputtes Update darf den Poller nicht killen.
                # process_update faengt das meiste selbst; das hier ist das Netz.
                logger.exception("Failed to process update_id=%s", update_id)
            # Offset auch bei Fehler vorruecken: das Update wurde geloggt,
            # ein Reprocess wuerde nur erneut scheitern (Poison-Update).
            if update_id is not None:
                offset = update_id + 1


def main() -> None:
    configure_logging()
    logger.info(
        "Starting Telegram long-polling (timeout=%ss)",
        settings.telegram_polling_timeout,
    )
    try:
        asyncio.run(run_polling())
    except KeyboardInterrupt:
        logger.info("Polling stopped")


if __name__ == "__main__":
    main()
