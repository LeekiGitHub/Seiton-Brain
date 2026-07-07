"""Zentrale Konfiguration via pydantic-settings.

Liest Werte aus Umgebungsvariablen (und optional aus einer ``.env``-Datei).
Pflichtfelder ohne Default sorgen fuer einen klaren Fail-Fast beim Start,
statt spaeter mit kryptischen ``KeyError`` aufzuschlagen.

Verwendung im Code::

    from app.config import settings

    api_key = settings.openai_api_key

Im Test kann ein Feld pro Test ueberschrieben werden::

    monkeypatch.setattr(settings, "telegram_allowed_user_ids", "42,99")
"""

from __future__ import annotations

import sys

from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

# Feldname -> (ENV-Variable, kurze Hilfe fuer den Operator)
FIELD_HINTS: dict[str, tuple[str, str]] = {
    "telegram_bot_token": (
        "TELEGRAM_BOT_TOKEN",
        "Token von @BotFather fuer deinen Telegram-Bot",
    ),
    "telegram_webhook_secret": (
        "TELEGRAM_WEBHOOK_SECRET",
        "Geheimer String fuer den Webhook (Header X-Telegram-Bot-Api-Secret-Token)",
    ),
    "openai_api_key": (
        "OPENAI_API_KEY",
        "OpenAI API Key (https://platform.openai.com/api-keys)",
    ),
    "obsidian_vault_path": (
        "OBSIDIAN_VAULT_PATH",
        "Pfad zum Obsidian-Vault (lokal oder /vault in Docker)",
    ),
    "database_url": (
        "DATABASE_URL",
        "Postgres-URL, z. B. postgresql+asyncpg://user:pass@db:5432/seitonbrain",
    ),
    "redis_url": (
        "REDIS_URL",
        "Redis-URL fuer Celery, z. B. redis://redis:6379/0",
    ),
}


def format_settings_validation_error(exc: ValidationError) -> str:
    """Wandelt pydantic ValidationError in eine lesbare Startmeldung um."""
    lines = [
        "Seiton Brain konnte nicht starten — fehlende oder ungültige Konfiguration:",
        "",
    ]
    seen: set[str] = set()
    for err in exc.errors():
        loc = err.get("loc", ())
        field = loc[-1] if loc else "?"
        if not isinstance(field, str) or field in seen:
            continue
        seen.add(field)
        if field in FIELD_HINTS:
            env_name, hint = FIELD_HINTS[field]
            lines.append(f"  • {env_name}")
            lines.append(f"    {hint}")
        else:
            lines.append(f"  • {field}: {err.get('msg', 'ungültig')}")
    lines.extend(
        [
            "",
            "Tipp: Kopiere .env.example nach .env und fülle die Pflichtfelder aus.",
            "Setup-Anleitung: docs/setup.md",
        ]
    )
    return "\n".join(lines)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Telegram (optional — mobiles Erfassen; leer = deaktiviert, ADR 0004)
    telegram_bot_token: str = ""
    telegram_webhook_secret: str = ""
    # Kommaseparierte Liste numerischer User-IDs.
    # Leer (Default) bedeutet: Allowlist deaktiviert -> alle erlaubt.
    # Geparst wird im Webhook (dort sitzt auch der Logger).
    telegram_allowed_user_ids: str = ""
    # Telegram-Chat-ID fuer Admin-DMs bei dauerhaften Worker-Fehlern (E10-3).
    # Leer = deaktiviert. Eigene ID: /start an @userinfobot.
    telegram_admin_chat_id: str = ""
    # Maximale akzeptierte Webhook-Body-Groesse in Bytes. Echte Telegram-
    # Updates sind typischerweise <10 KB; 1 MB ist grosszuegig und schuetzt
    # vor Resource-Exhaustion durch fehlgeleitete oder boesartige Requests.
    telegram_webhook_max_body_bytes: int = 1_048_576
    # Long-Poll-Fenster in Sekunden fuer den Polling-Modus (app.telegram.polling).
    # Hoehere Werte = weniger Requests, laengere Hangs pro Aufruf. Telegram
    # erlaubt bis 50; 25 ist ein guter Default.
    telegram_polling_timeout: int = 25

    # LLM
    llm_provider: str = "openai"
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"

    # Semantische Suche / Embeddings (E17-2, pgvector). Standardmaessig aus —
    # erzeugt zusaetzliche Embedding-API-Calls (Kosten). Wenn aktiviert, werden
    # Notizen beim Schreiben/Append/Sync embedded und `semantic_search` nutzbar.
    # Das Embedding-Modell muss zur Vektor-Dimension der DB-Spalte passen
    # (EMBEDDING_DIM im Model + Migration); Default-Modell = 1536 Dimensionen.
    embeddings_enabled: bool = False
    embedding_model: str = "text-embedding-3-small"

    # Vault
    obsidian_vault_path: str

    # Persistenz
    database_url: str
    redis_url: str

    # Logging
    log_level: str = "INFO"
    # true -> eine JSON-Zeile pro Log (Production/Docker); false -> lesbares Text-Format
    log_json: bool = True

    # REST API (/v1/*). Leer = API deaktiviert (503). Gesetzt = Header X-Seiton-Api-Key
    # muss exakt uebereinstimmen (timing-safe Vergleich).
    seiton_api_key: str = ""

    # Pfad zur lokalen .env fuer den Setup-Wizard (E19-1).
    seiton_env_file: str = ".env"

    # Outbound Webhooks (E13-3). Leer = deaktiviert. Eine URL fuer alle Events;
    # Event-Typ steht im JSON-Feld ``event`` und Header ``X-Seiton-Event``.
    seiton_webhook_url: str = ""

    # Kommerzielle Lizenz (E21-1). Leer = keine Lizenz hinterlegt.
    # Format: SEITON1.<payload>.<signature> — siehe docs/licensing.md
    seiton_license_key: str = ""
    # false = MIT/Portfolio (Default). true = Prozess startet nur mit gueltiger Lizenz.
    seiton_license_required: bool = False


def load_settings() -> Settings:
    try:
        return Settings()  # type: ignore[call-arg]
    except ValidationError as exc:
        print(format_settings_validation_error(exc), file=sys.stderr)
        raise SystemExit(1) from None


settings = load_settings()
