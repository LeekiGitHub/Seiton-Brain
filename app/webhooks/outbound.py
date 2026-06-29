"""Outbound Webhooks fuer externe Integrationen (n8n, Slack, …)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

import httpx

from app.config import settings
from app.services.process_message import ProcessMessageResult

logger = logging.getLogger(__name__)

EVENT_NOTE_CREATED = "note.created"
EVENT_NOTE_APPENDED = "note.appended"
EVENT_NOTE_INDEXED = "note.indexed"
EVENT_ENTRY_FAILED = "entry.failed"

_RAW_INPUT_PREVIEW_CHARS = 200


def event_for_capture_status(status: str) -> str:
    if status == "appended":
        return EVENT_NOTE_APPENDED
    return EVENT_NOTE_CREATED


def build_note_event_payload(
    result: ProcessMessageResult,
    *,
    kind: str = "text",
    telegram_chat_id: int | None = None,
    telegram_update_id: int | None = None,
) -> dict[str, Any]:
    event = event_for_capture_status(result.status)
    payload: dict[str, Any] = {
        "event": event,
        "timestamp": datetime.now(UTC).isoformat(),
        "entry_id": result.entry_id,
        "vault_path": result.vault_path,
        "status": result.status,
        "kind": kind,
        "classification": result.classification.model_dump(),
    }
    if telegram_chat_id is not None:
        payload["telegram_chat_id"] = telegram_chat_id
    if telegram_update_id is not None:
        payload["telegram_update_id"] = telegram_update_id
    return payload


def build_entry_failed_payload(
    *,
    task_name: str,
    error: BaseException,
    chat_id: int | None = None,
    task_id: str | None = None,
    telegram_update_id: int | None = None,
    kind: str | None = None,
    raw_input: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "event": EVENT_ENTRY_FAILED,
        "timestamp": datetime.now(UTC).isoformat(),
        "task": task_name,
        "error_type": type(error).__name__,
        "error_message": str(error),
    }
    if chat_id is not None:
        payload["telegram_chat_id"] = chat_id
    if task_id is not None:
        payload["task_id"] = task_id
    if telegram_update_id is not None:
        payload["telegram_update_id"] = telegram_update_id
    if kind is not None:
        payload["kind"] = kind
    if raw_input:
        preview = raw_input.strip()
        if len(preview) > _RAW_INPUT_PREVIEW_CHARS:
            preview = preview[: _RAW_INPUT_PREVIEW_CHARS - 3] + "..."
        payload["raw_input_preview"] = preview
    return payload


async def emit_webhook(payload: dict[str, Any]) -> None:
    """POST JSON an ``SEITON_WEBHOOK_URL``. Fehler werden nur geloggt."""
    url = settings.seiton_webhook_url.strip()
    if not url:
        return

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Seiton-Brain-Webhook/1.0",
        "X-Seiton-Event": str(payload.get("event", "")),
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=10.0)
            response.raise_for_status()
    except Exception:
        logger.exception(
            "Outbound webhook failed event=%s url=%s",
            payload.get("event"),
            url,
        )


async def emit_capture_event(
    result: ProcessMessageResult,
    *,
    kind: str = "text",
    telegram_chat_id: int | None = None,
    telegram_update_id: int | None = None,
) -> None:
    payload = build_note_event_payload(
        result,
        kind=kind,
        telegram_chat_id=telegram_chat_id,
        telegram_update_id=telegram_update_id,
    )
    await emit_webhook(payload)


def build_note_indexed_payload(
    *,
    vault_path: str,
    title: str,
    category: str = "",
    folder: str = "",
    doc_type: str = "markdown",
) -> dict[str, Any]:
    """Payload nach erfolgreicher Embedding-Berechnung (E17-7)."""
    return {
        "event": EVENT_NOTE_INDEXED,
        "timestamp": datetime.now(UTC).isoformat(),
        "vault_path": vault_path,
        "title": title,
        "category": category,
        "folder": folder,
        "doc_type": doc_type,
    }


async def emit_note_indexed_event(
    *,
    vault_path: str,
    title: str,
    category: str = "",
    folder: str = "",
    doc_type: str = "markdown",
) -> None:
    payload = build_note_indexed_payload(
        vault_path=vault_path,
        title=title,
        category=category,
        folder=folder,
        doc_type=doc_type,
    )
    await emit_webhook(payload)


async def emit_entry_failed_event(
    *,
    task_name: str,
    error: BaseException,
    chat_id: int | None = None,
    task_id: str | None = None,
    telegram_update_id: int | None = None,
    kind: str | None = None,
    raw_input: str | None = None,
) -> None:
    payload = build_entry_failed_payload(
        task_name=task_name,
        error=error,
        chat_id=chat_id,
        task_id=task_id,
        telegram_update_id=telegram_update_id,
        kind=kind,
        raw_input=raw_input,
    )
    await emit_webhook(payload)
