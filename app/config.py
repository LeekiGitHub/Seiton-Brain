"""Central configuration via pydantic-settings.

Reads values from environment variables (and optionally from a ``.env`` file).
Required fields without defaults fail fast at startup instead of raising
cryptic ``KeyError``s later.

Usage::

    from app.config import settings

    api_key = settings.openai_api_key

In tests, override a field per test::

    monkeypatch.setattr(settings, "telegram_allowed_user_ids", "42,99")
"""

from __future__ import annotations

import sys

from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

# field name -> (ENV var, short operator hint; hints stay German for operators)
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
    """Turn a pydantic ValidationError into a readable startup message."""
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

    # Telegram (optional mobile capture; empty = disabled, ADR 0004)
    telegram_bot_token: str = ""
    telegram_webhook_secret: str = ""
    # Comma-separated numeric user IDs.
    # Empty (default): allowlist off → all users allowed.
    # Parsed in the webhook (logging lives there too).
    telegram_allowed_user_ids: str = ""
    # Telegram chat ID for admin DMs on permanent worker failures (E10-3).
    # Empty = disabled. Own ID: /start at @userinfobot.
    telegram_admin_chat_id: str = ""
    # Max accepted webhook body size in bytes. Real Telegram updates are
    # typically <10 KB; 1 MB is generous and guards against resource
    # exhaustion from misdirected or malicious requests.
    telegram_webhook_max_body_bytes: int = 1_048_576
    # Max Telegram voice message size in bytes (E6-1).
    # Telegram/OpenAI allow more — this limit caps expensive downloads and
    # Whisper calls. Default 10 MB.
    telegram_voice_max_bytes: int = 10_485_760
    # Max Telegram document/photo size (E22-2). Bot API allows downloads
    # up to 20 MB — default matches that.
    telegram_document_max_bytes: int = 20_971_520
    # Dir for temporary voice files until processing succeeds
    # (E6-2 replay on crash/retry). Empty = temp/voice relative to CWD.
    telegram_voice_cache_dir: str = "temp/voice"
    # Optional path to vault_config.yaml (E4-3). Empty = <Vault>/vault_config.yaml
    seiton_vault_config: str = ""
    # Long-poll window in seconds for polling mode (app.telegram.polling).
    # Higher = fewer requests, longer hangs per call. Telegram allows up to
    # 50; 25 is a solid default.
    telegram_polling_timeout: int = 25

    # LLM
    llm_provider: str = "openai"
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    # Ollama (E7-2) when LLM_PROVIDER=ollama. Whisper can run locally
    # (WHISPER_PROVIDER=whisper.cpp, E6-4); embeddings stay on OpenAI.
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"

    # Whisper language hint (E6-3), ISO-639-1 e.g. "de" / "en".
    # Empty = automatic language detection (OpenAI default / whisper.cpp auto).
    whisper_language: str = ""
    # Transcription: openai (default) or whisper.cpp (E6-4, local).
    whisper_provider: str = "openai"
    whisper_cpp_binary: str = "whisper-cli"
    # GGML model; default under /models/ (gitignored, ADR 0002).
    whisper_cpp_model: str = "models/ggml-base.bin"
    # On missing binary/model or runtime error → fall back to OpenAI.
    whisper_cpp_fallback_openai: bool = True

    # Max notes in the classify prompt after token prefilter (E5-2).
    seiton_llm_note_limit: int = 30

    # Classify prompt version (E4-4): loads prompts/{name}.{version}.txt
    # (classify / router / writer / linker). Stored in entries.prompt_version.
    seiton_prompt_version: str = "v1"

    # Specialized LLM roles (E7-3): Router → Writer → Linker instead of one-shot.
    # false = legacy one-shot with prompts/classify.{version}.txt (cheaper).
    seiton_llm_roles_enabled: bool = True

    # Semantic search / embeddings (E17-2, pgvector). Off by default — adds
    # embedding API calls (cost). When on, notes are embedded on write/append/
    # sync and `semantic_search` is usable.
    # Embedding model must match the DB vector column dimension
    # (EMBEDDING_DIM in model + migration); default model = 1536 dims.
    embeddings_enabled: bool = False
    embedding_model: str = "text-embedding-3-small"

    # Chunking for retrieval (E18-4). Long docs are split into sections;
    # embeddings and keyword hits run via vault_chunk.
    seiton_chunk_size: int = 1500
    seiton_chunk_overlap: int = 200
    # Incremental vault index sync (E28-1). Interval in seconds for Celery
    # Beat; 0 = Beat task disabled (manual reindex only).
    seiton_index_sync_interval_seconds: int = 60

    # OCR (E18-5). Optional: needs system Tesseract + pip extras
    # (requirements-ocr.txt). If False / not installed, pdf_no_text and
    # image files are not indexed (unless Vision is on).
    seiton_ocr_enabled: bool = True
    seiton_ocr_lang: str = "deu+eng"

    # Vision LLM for pure photos (E18-6). Off by default (API cost), same
    # idea as embeddings. Uses OPENAI_API_KEY; empty model = OPENAI_MODEL.
    seiton_vision_enabled: bool = False
    seiton_vision_model: str = ""

    # OS keystore for secrets (E16-5). true = keys in Keychain/Credential Manager;
    # start via ./scripts/seiton-up.sh. Needs pip install -r requirements-keyring.txt.
    seiton_keyring: bool = False

    # Vault
    obsidian_vault_path: str
    # Vault backend (E15-1/E15-3). filesystem = Markdown folder, git = commit per note.
    vault_backend: str = "filesystem"
    vault_git_push: bool = False
    vault_git_remote: str = "origin"
    vault_git_branch: str = ""
    vault_git_author_name: str = "Seiton Brain"
    vault_git_author_email: str = "seiton@example.invalid"

    # Persistence
    database_url: str
    redis_url: str

    # Logging
    log_level: str = "INFO"
    # true → one JSON line per log (production/Docker); false → human-readable text
    log_json: bool = True

    # REST API (/v1/*). Empty = API disabled (503). Set = Header X-Seiton-Api-Key
    # must match exactly (timing-safe compare).
    seiton_api_key: str = ""

    # Path to local .env for the setup wizard (E19-1).
    seiton_env_file: str = ".env"

    # UI auth (E23-1). Empty = Web UI localhost-only (status quo).
    # Set = login required (session cookie) — remote access then possible;
    # must run behind TLS (docs/remote-access.md).
    ui_password: str = ""
    # Session cookie Secure flag (E27-3). true = send only over HTTPS —
    # set behind a TLS proxy. Localhost/HTTP: leave false.
    ui_cookie_secure: bool = False

    # Outbound webhooks (E13-3). Empty = disabled. One URL for all events;
    # event type is in JSON field ``event`` and header ``X-Seiton-Event``.
    seiton_webhook_url: str = ""

    # Commercial license (E21-1). Empty = no license on file.
    # Format: SEITON1.<payload>.<signature> — see docs/licensing.md
    seiton_license_key: str = ""
    # false = MIT/open source (default). true = process starts only with a valid license.
    seiton_license_required: bool = False

    # Debug mode: e.g. OpenAPI under /docs even without SEITON_API_KEY (E13-4).
    seiton_debug: bool = False


def load_settings() -> Settings:
    try:
        return Settings()  # type: ignore[call-arg]
    except ValidationError as exc:
        print(format_settings_validation_error(exc), file=sys.stderr)
        raise SystemExit(1) from None


settings = load_settings()
