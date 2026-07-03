"""Tests fuer app/setup/config_save.py."""

import pytest

from app.setup.config_save import save_settings_config, save_setup_config
from app.setup.env_file import read_env_values
from app.setup.schemas import SetupSaveRequest


def test_save_setup_config_writes_env(tmp_path, monkeypatch):
    env_path = tmp_path / ".env"
    monkeypatch.setattr("app.setup.config_save.settings.seiton_env_file", str(env_path))
    monkeypatch.setattr("app.setup.config_save.settings.obsidian_vault_path", "/vault")

    result = save_setup_config(
        SetupSaveRequest(
            obsidian_vault_host_path="/host/vault",
            openai_api_key="sk-test",
            embeddings_enabled=True,
        )
    )

    assert result.saved is True
    values = read_env_values(env_path)
    assert values["OPENAI_API_KEY"] == "sk-test"
    assert values["EMBEDDINGS_ENABLED"] == "true"
    assert values["OBSIDIAN_VAULT_HOST_PATH"] == "/host/vault"
    assert values["SEITON_API_KEY"]


def test_save_settings_keeps_existing_openai_key(tmp_path, monkeypatch):
    env_path = tmp_path / ".env"
    env_path.write_text("OPENAI_API_KEY=sk-existing\n", encoding="utf-8")
    monkeypatch.setattr("app.setup.config_save.settings.seiton_env_file", str(env_path))
    monkeypatch.setattr("app.setup.config_save.settings.obsidian_vault_path", "/vault")
    monkeypatch.setattr("app.setup.config_save.settings.openai_api_key", "sk-existing")

    save_settings_config(openai_api_key="", embeddings_enabled=False)

    values = read_env_values(env_path)
    assert values["OPENAI_API_KEY"] == "sk-existing"
    assert values["EMBEDDINGS_ENABLED"] == "false"


def test_save_settings_requires_openai_key(tmp_path, monkeypatch):
    env_path = tmp_path / ".env"
    monkeypatch.setattr("app.setup.config_save.settings.seiton_env_file", str(env_path))
    monkeypatch.setattr("app.setup.config_save.settings.obsidian_vault_path", "/vault")
    monkeypatch.setattr("app.setup.config_save.settings.openai_api_key", "...")

    with pytest.raises(ValueError, match="OpenAI"):
        save_settings_config(openai_api_key="")
