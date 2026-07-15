import pytest
from pydantic import ValidationError

from app.config import Settings, format_settings_validation_error, settings


def test_settings_singleton_loads_required_fields_from_env():
    """Die Modul-Level-Instanz wurde beim Import via conftest aus den
    Env-Variablen befuellt (TELEGRAM_*, OPENAI_API_KEY, DATABASE_URL, ...)."""
    assert settings.telegram_bot_token == "123456:TEST-BOT-TOKEN"
    assert settings.telegram_webhook_secret == "test-webhook-secret"
    assert settings.openai_api_key == "test-openai-key"
    assert settings.database_url.startswith("postgresql+asyncpg://")
    assert settings.redis_url.startswith("redis://")
    assert settings.obsidian_vault_path


def test_settings_defaults_are_applied():
    """Felder ohne Env-Variable bekommen die Default-Werte."""
    assert settings.llm_provider == "openai"
    assert settings.openai_model == "gpt-4o-mini"
    assert settings.telegram_allowed_user_ids == ""
    assert settings.telegram_admin_chat_id == ""
    assert settings.log_level == "INFO"
    assert settings.log_json is True
    assert settings.seiton_api_key == "test-seiton-api-key"
    assert settings.seiton_webhook_url == ""
    assert settings.seiton_license_key == ""
    assert settings.seiton_license_required is False
    assert settings.seiton_debug is False
    assert settings.whisper_language == ""


def test_settings_accept_extra_env_vars():
    """``extra='ignore'`` -- zusaetzliche Env-Vars wie OBSIDIAN_VAULT_HOST_PATH
    sollen die Settings-Instantiation nicht crashen lassen."""
    s = Settings(  # type: ignore[call-arg]
        _env_file=None,  # bypass .env discovery; nur explizit gesetzte Werte
        openai_api_key="z",
        obsidian_vault_path="/tmp/v",
        database_url="postgresql+asyncpg://u:p@h/d",
        redis_url="redis://h:6379/0",
    )
    assert s.llm_provider == "openai"


def test_format_settings_validation_error_lists_env_names(monkeypatch):
    for key in (
        "OPENAI_API_KEY",
        "OBSIDIAN_VAULT_PATH",
        "DATABASE_URL",
        "REDIS_URL",
    ):
        monkeypatch.delenv(key, raising=False)

    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)  # type: ignore[call-arg]

    message = format_settings_validation_error(exc_info.value)
    assert "OPENAI_API_KEY" in message
    assert "TELEGRAM_BOT_TOKEN" not in message
    assert ".env.example" in message
    assert "docs/setup.md" in message


def test_settings_monkeypatch_works_per_test(monkeypatch):
    """Sicherheitsnetz: Tests duerfen Felder pro Test ueberschreiben,
    monkeypatch raeumt am Ende auf."""
    monkeypatch.setattr(settings, "telegram_allowed_user_ids", "42,99")
    assert settings.telegram_allowed_user_ids == "42,99"
