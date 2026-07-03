"""Gemeinsame Konfigurationsspeicherung fuer Setup und Settings (E19)."""

from __future__ import annotations

import secrets
from pathlib import Path

from app.config import settings
from app.setup.env_file import read_env_values, resolve_env_path, update_env_file
from app.setup.schemas import SetupSaveRequest, SetupSaveResponse
from app.setup.status import is_placeholder


def _effective_env() -> dict[str, str]:
    return read_env_values(settings.seiton_env_file)


def save_setup_config(body: SetupSaveRequest) -> SetupSaveResponse:
    """Erstkonfiguration aus dem Setup-Wizard."""
    vault_host = body.obsidian_vault_host_path.strip()
    updates: dict[str, str] = {
        "OBSIDIAN_VAULT_HOST_PATH": vault_host,
        "OBSIDIAN_VAULT_PATH": settings.obsidian_vault_path,
        "OPENAI_API_KEY": body.openai_api_key.strip(),
        "EMBEDDINGS_ENABLED": "true" if body.embeddings_enabled else "false",
    }

    api_key = body.seiton_api_key.strip() or secrets.token_urlsafe(32)
    updates["SEITON_API_KEY"] = api_key

    token = body.telegram_bot_token.strip()
    if token:
        updates["TELEGRAM_BOT_TOKEN"] = token
        secret = body.telegram_webhook_secret.strip() or secrets.token_urlsafe(32)
        updates["TELEGRAM_WEBHOOK_SECRET"] = secret
        if body.telegram_allowed_user_ids.strip():
            updates["TELEGRAM_ALLOWED_USER_IDS"] = body.telegram_allowed_user_ids.strip()

    env_path = update_env_file(updates, resolve_env_path(settings.seiton_env_file))
    return _save_response(env_path)


def save_settings_config(
    *,
    obsidian_vault_host_path: str | None = None,
    openai_api_key: str = "",
    embeddings_enabled: bool | None = None,
    openai_model: str = "",
    telegram_bot_token: str = "",
    telegram_webhook_secret: str = "",
    telegram_allowed_user_ids: str = "",
    seiton_api_key: str = "",
    seiton_webhook_url: str | None = None,
) -> SetupSaveResponse:
    """Einstellungen aktualisieren — leere Secrets behalten bestehende Werte."""
    file_values = _effective_env()
    updates: dict[str, str] = {}

    vault_host = (
        (obsidian_vault_host_path or "").strip()
        or file_values.get("OBSIDIAN_VAULT_HOST_PATH", settings.obsidian_vault_path)
    ).strip()
    updates["OBSIDIAN_VAULT_HOST_PATH"] = vault_host
    updates["OBSIDIAN_VAULT_PATH"] = settings.obsidian_vault_path

    openai = openai_api_key.strip() or file_values.get(
        "OPENAI_API_KEY", settings.openai_api_key
    )
    if is_placeholder(openai):
        raise ValueError("OpenAI API key is required")
    updates["OPENAI_API_KEY"] = openai

    if embeddings_enabled is not None:
        updates["EMBEDDINGS_ENABLED"] = "true" if embeddings_enabled else "false"

    model = openai_model.strip() or file_values.get(
        "OPENAI_MODEL", settings.openai_model
    )
    updates["OPENAI_MODEL"] = model

    api_key = (
        seiton_api_key.strip()
        or file_values.get("SEITON_API_KEY", settings.seiton_api_key)
        or secrets.token_urlsafe(32)
    )
    updates["SEITON_API_KEY"] = api_key

    token = telegram_bot_token.strip() or file_values.get(
        "TELEGRAM_BOT_TOKEN", settings.telegram_bot_token
    )
    if token:
        updates["TELEGRAM_BOT_TOKEN"] = token
        secret = (
            telegram_webhook_secret.strip()
            or file_values.get("TELEGRAM_WEBHOOK_SECRET", settings.telegram_webhook_secret)
            or secrets.token_urlsafe(32)
        )
        updates["TELEGRAM_WEBHOOK_SECRET"] = secret
        allowed = telegram_allowed_user_ids.strip() or file_values.get(
            "TELEGRAM_ALLOWED_USER_IDS", settings.telegram_allowed_user_ids
        )
        if allowed:
            updates["TELEGRAM_ALLOWED_USER_IDS"] = allowed

    if seiton_webhook_url is not None:
        updates["SEITON_WEBHOOK_URL"] = seiton_webhook_url.strip()

    env_path = update_env_file(updates, resolve_env_path(settings.seiton_env_file))
    return _save_response(env_path)


def _save_response(env_path: Path) -> SetupSaveResponse:
    return SetupSaveResponse(
        saved=True,
        env_file=str(env_path),
        restart_required=True,
        message=(
            "Konfiguration gespeichert. Bitte Container neu starten: "
            "docker compose up -d"
        ),
    )
