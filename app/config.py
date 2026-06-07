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

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Telegram
    telegram_bot_token: str
    telegram_webhook_secret: str
    # Kommaseparierte Liste numerischer User-IDs.
    # Leer (Default) bedeutet: Allowlist deaktiviert -> alle erlaubt.
    # Geparst wird im Webhook (dort sitzt auch der Logger).
    telegram_allowed_user_ids: str = ""
    # Maximale akzeptierte Webhook-Body-Groesse in Bytes. Echte Telegram-
    # Updates sind typischerweise <10 KB; 1 MB ist grosszuegig und schuetzt
    # vor Resource-Exhaustion durch fehlgeleitete oder boesartige Requests.
    telegram_webhook_max_body_bytes: int = 1_048_576

    # LLM
    llm_provider: str = "openai"
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"

    # Vault
    obsidian_vault_path: str

    # Persistenz
    database_url: str
    redis_url: str


settings = Settings()  # type: ignore[call-arg]
