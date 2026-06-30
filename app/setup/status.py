"""Erkennung, ob die Erstkonfiguration abgeschlossen ist."""

from __future__ import annotations

from app.config import settings
from app.setup.env_file import read_env_values

_PLACEHOLDER_FRAGMENTS = ("...", "change-me", "your-", "example", "replace")


def is_placeholder(value: str) -> bool:
    stripped = value.strip()
    if not stripped:
        return True
    lower = stripped.lower()
    return any(fragment in lower for fragment in _PLACEHOLDER_FRAGMENTS)


def _effective_values() -> dict[str, str]:
    file_values = read_env_values(settings.seiton_env_file or ".env")
    return {
        "OPENAI_API_KEY": settings.openai_api_key,
        "OBSIDIAN_VAULT_HOST_PATH": file_values.get(
            "OBSIDIAN_VAULT_HOST_PATH", settings.obsidian_vault_path
        ),
        "OBSIDIAN_VAULT_PATH": settings.obsidian_vault_path,
        "TELEGRAM_BOT_TOKEN": settings.telegram_bot_token,
        "TELEGRAM_WEBHOOK_SECRET": settings.telegram_webhook_secret,
        "SEITON_API_KEY": settings.seiton_api_key,
    }


def missing_setup_fields() -> list[str]:
    """Pflichtfelder, die noch konfiguriert werden muessen."""
    values = _effective_values()
    missing: list[str] = []
    if is_placeholder(values["OPENAI_API_KEY"]):
        missing.append("openai_api_key")
    vault_host = values["OBSIDIAN_VAULT_HOST_PATH"]
    if is_placeholder(vault_host):
        missing.append("vault_path")
    return missing


def is_setup_complete() -> bool:
    return not missing_setup_fields()


def is_telegram_configured() -> bool:
    return not is_placeholder(settings.telegram_bot_token) and not is_placeholder(
        settings.telegram_webhook_secret
    )


def component_status() -> dict[str, bool]:
    values = _effective_values()
    return {
        "vault": not is_placeholder(values["OBSIDIAN_VAULT_HOST_PATH"]),
        "openai": not is_placeholder(values["OPENAI_API_KEY"]),
        "telegram": is_telegram_configured(),
        "api_key": not is_placeholder(values["SEITON_API_KEY"]),
    }
