"""Structured logging with JSON output and request/task correlation.

Each log line may optionally include:
- ``task_id`` — Celery task (set via ``task_prerun`` signal)
- ``request_id`` — HTTP request (middleware in ``app.main``)
- ``telegram_update_id`` — Telegram update in the worker

Context lives in ``contextvars`` — thread/async-safe, no global dict.
"""

from __future__ import annotations

import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

from app.config import settings

_task_id: ContextVar[str | None] = ContextVar("task_id", default=None)
_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)
_telegram_update_id: ContextVar[int | None] = ContextVar(
    "telegram_update_id", default=None
)

_CONTEXT_VARS: dict[str, ContextVar[Any]] = {
    "task_id": _task_id,
    "request_id": _request_id,
    "telegram_update_id": _telegram_update_id,
}


def bind_log_context(
    *,
    task_id: str | None = None,
    request_id: str | None = None,
    telegram_update_id: int | None = None,
) -> None:
    """Set correlation fields for the current execution (only overwrites
    the passed, non-None values).
    """
    if task_id is not None:
        _task_id.set(task_id)
    if request_id is not None:
        _request_id.set(request_id)
    if telegram_update_id is not None:
        _telegram_update_id.set(telegram_update_id)


def clear_log_context() -> None:
    for var in _CONTEXT_VARS.values():
        var.set(None)


class LogContextFilter(logging.Filter):
    """Inject context variables as attributes on the LogRecord."""

    def filter(self, record: logging.LogRecord) -> bool:
        for key, var in _CONTEXT_VARS.items():
            value = var.get()
            if value is not None:
                setattr(record, key, value)
        return True


class JsonLogFormatter(logging.Formatter):
    """Eine JSON-Zeile pro Log-Eintrag — grep-/jq-freundlich."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key in _CONTEXT_VARS:
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


class TextLogFormatter(logging.Formatter):
    """Human-readable text format for local development (``LOG_JSON=false``)."""

    def format(self, record: logging.LogRecord) -> str:
        base = super().format(record)
        extras: list[str] = []
        for key in _CONTEXT_VARS:
            value = getattr(record, key, None)
            if value is not None:
                extras.append(f"{key}={value}")
        if extras:
            return f"{base} [{', '.join(extras)}]"
        return base


def configure_logging() -> None:
    """Configure the root logger once (idempotent enough for API + worker)."""
    root = logging.getLogger()
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(LogContextFilter())
    if settings.log_json:
        handler.setFormatter(JsonLogFormatter())
    else:
        handler.setFormatter(
            TextLogFormatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
        )

    root.addHandler(handler)
    root.setLevel(settings.log_level.upper())

    # Keep Uvicorn/Celery from double-logging to stderr — reuse the same
    # handler for the common framework loggers.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "celery"):
        framework_logger = logging.getLogger(name)
        framework_logger.handlers.clear()
        framework_logger.propagate = True
