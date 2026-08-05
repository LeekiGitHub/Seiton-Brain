"""OS-Keystore fuer Secrets (E16-5) via optionalem ``keyring``.

Speichert API-Keys at-rest im nativen Store (macOS Keychain, Windows Credential
Manager, libsecret). Docker-Container lesen den Keystore nicht — der Host-Launcher
(``scripts/seiton-up.sh``) exportiert die Werte als Env.
"""

from __future__ import annotations

import logging
from typing import Iterable

logger = logging.getLogger(__name__)

SERVICE_NAME = "seiton-brain"

# Secrets, die bei SEITON_KEYRING=true nicht Klartext in der .env liegen sollen.
SECRET_ENV_KEYS: tuple[str, ...] = (
    "OPENAI_API_KEY",
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_WEBHOOK_SECRET",
    "SEITON_API_KEY",
    "SEITON_LICENSE_KEY",
)


def is_keyring_available() -> bool:
    try:
        import keyring  # noqa: F401

        return True
    except Exception:  # noqa: BLE001 — optionales Extra
        return False


def set_secret(key: str, value: str) -> None:
    if not value:
        delete_secret(key)
        return
    import keyring

    keyring.set_password(SERVICE_NAME, key, value)


def get_secret(key: str) -> str | None:
    if not is_keyring_available():
        return None
    try:
        import keyring

        return keyring.get_password(SERVICE_NAME, key)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Keyring-Lesen fehlgeschlagen fuer %s: %s", key, exc)
        return None


def delete_secret(key: str) -> None:
    if not is_keyring_available():
        return
    try:
        import keyring

        keyring.delete_password(SERVICE_NAME, key)
    except Exception:  # noqa: BLE001 — fehlt oft, wenn nie gesetzt
        pass


def store_secrets(values: dict[str, str]) -> list[str]:
    """Speichert gesetzte Secrets; liefert die gespeicherten Keys."""
    stored: list[str] = []
    for key in SECRET_ENV_KEYS:
        if key not in values:
            continue
        value = (values.get(key) or "").strip()
        if not value:
            continue
        set_secret(key, value)
        stored.append(key)
    return stored


def load_secrets(keys: Iterable[str] | None = None) -> dict[str, str]:
    """Liest Secrets aus dem Keystore (nur nicht-leere)."""
    wanted = tuple(keys) if keys is not None else SECRET_ENV_KEYS
    out: dict[str, str] = {}
    for key in wanted:
        value = get_secret(key)
        if value:
            out[key] = value
    return out


def export_dotenv(keys: Iterable[str] | None = None) -> str:
    """``KEY=value``-Zeilen fuer Shell-Export (Werte escaped)."""
    lines: list[str] = []
    for key, value in load_secrets(keys).items():
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        lines.append(f'{key}="{escaped}"')
    return "\n".join(lines) + ("\n" if lines else "")
