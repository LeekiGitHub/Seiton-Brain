"""Tests fuer Setup-Wizard (E19-1)."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.setup.env_file import read_env_values, update_env_file
from app.setup.status import is_placeholder, is_setup_complete, missing_setup_fields

client = TestClient(app)


def test_is_placeholder_detects_examples():
    assert is_placeholder("...")
    assert is_placeholder("change-me-to-a-long-random-string")
    assert not is_placeholder("sk-real-key-abc")


def test_env_file_roundtrip(tmp_path):
    env_path = tmp_path / ".env"
    env_path.write_text(
        "# comment\nOPENAI_API_KEY=old\nTELEGRAM_BOT_TOKEN=keep\n",
        encoding="utf-8",
    )
    update_env_file(
        {"OPENAI_API_KEY": "new-key", "SEITON_API_KEY": "generated"},
        env_path,
    )
    values = read_env_values(env_path)
    assert values["OPENAI_API_KEY"] == "new-key"
    assert values["SEITON_API_KEY"] == "generated"
    assert values["TELEGRAM_BOT_TOKEN"] == "keep"
    content = env_path.read_text(encoding="utf-8")
    assert "# comment" in content


def test_setup_status_localhost():
    response = client.get("/api/setup/status")
    assert response.status_code == 200
    data = response.json()
    assert "complete" in data
    assert "components" in data


def test_setup_page_renders():
    response = client.get("/setup")
    assert response.status_code == 200
    assert "Seiton Brain" in response.text
    assert "setup.js" in response.text


@patch("app.setup.routes.checks.check_openai", new_callable=AsyncMock)
def test_setup_test_openai(mock_check):
    mock_check.return_value = (True, "OK")
    response = client.post(
        "/api/setup/test",
        json={"check": "openai", "openai_api_key": "sk-test"},
    )
    assert response.status_code == 200
    assert response.json()["results"]["openai"]["ok"] is True


@patch("app.setup.config_save.update_env_file")
def test_setup_save_writes_env(mock_update):
    mock_update.return_value = Path("/tmp/.env")
    response = client.post(
        "/api/setup/save",
        json={
            "obsidian_vault_host_path": "/tmp/vault",
            "openai_api_key": "sk-test",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["saved"] is True
    assert "docker compose" in data["message"].lower()
    mock_update.assert_called_once()


@patch("app.setup.status.is_placeholder", return_value=True)
def test_missing_setup_fields_when_placeholders(_mock):
    assert "openai_api_key" in missing_setup_fields()


@patch("app.setup.status.missing_setup_fields", return_value=[])
def test_setup_complete_when_nothing_missing(_mock):
    assert is_setup_complete() is True
