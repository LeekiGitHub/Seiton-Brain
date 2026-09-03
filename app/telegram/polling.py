"""Telegram long-polling as an alternative to the webhook (E1-5).

Instead of waiting for an inbound webhook (which needs a publicly reachable
HTTPS URL), this process actively polls Telegram via ``getUpdates``. That
fits the "always-on box at the customer" deployment model (mini-PC / Mac Mini /
home server): no reverse proxy, no port forwarding, no TLS certificate.

Webhook and polling are mutually exclusive — Telegram delivers updates either
via webhook *or* via ``getUpdates``. The poller therefore calls
``deleteWebhook`` at startup.

Start::

    python -m app.telegram.polling

or via Compose profile::

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

# Backoff after a failed getUpdates so a Telegram outage does not
# trap us in a tight loop.
ERROR_BACKOFF_SECONDS = 5


async def run_polling(
    *,
    poll_timeout: int | None = None,
    max_batches: int | None = None,
) -> None:
    """Poll Telegram and process incoming updates.

    ``max_batches`` limits the number of ``getUpdates`` rounds (for
    tests). ``None`` = unlimited (production).
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
                # A single broken update must not kill the poller.
                # process_update catches most cases; this is the safety net.
                logger.exception("Failed to process update_id=%s", update_id)
            # Advance offset even on error: the update was logged;
            # reprocessing would only fail again (poison update).
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
