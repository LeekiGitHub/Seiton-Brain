"""OS keystore for secrets (E16-5) via optional ``keyring``.

Stores API keys at rest in the native store (macOS Keychain, Windows Credential
Manager, libsecret). Docker containers cannot read the keystore — the host
launcher (``scripts/seiton-up.sh``) exports the values as env vars.
"""

from __future__ import annotations

import logging
from typing import Iterable

logger = logging.getLogger(__name__)

SERVICE_NAME = "seiton-brain"

# Secrets that must not sit in plaintext in .env when SEITON_KEYRING=true.
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
    except Exception:  # noqa: BLE001 — optional extra
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
    except Exception:  # noqa: BLE001 — often missing if never set
        pass


def store_secrets(values: dict[str, str]) -> list[str]:
    """Store configured secrets; return the keys that were saved."""
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
    """Read secrets from the keystore (non-empty only)."""
    wanted = tuple(keys) if keys is not None else SECRET_ENV_KEYS
    out: dict[str, str] = {}
    for key in wanted:
        value = get_secret(key)
        if value:
            out[key] = value
    return out


def export_dotenv(keys: Iterable[str] | None = None) -> str:
    """``KEY=value`` lines for shell export (values escaped)."""
    lines: list[str] = []
    for key, value in load_secrets(keys).items():
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        lines.append(f'{key}="{escaped}"')
    return "\n".join(lines) + ("\n" if lines else "")
