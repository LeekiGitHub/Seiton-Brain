"""Tests fuer Settings-UI (E19-5)."""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.ui.settings import list_recent_backups, load_settings_view, mask_secret

client = TestClient(app)


def test_settings_page_renders():
    response = client.get("/settings")
    assert response.status_code == 200
    assert "Einstellungen" in response.text
    assert "settings.js" in response.text
    assert 'href="/settings"' in response.text


def test_settings_api_returns_view():
    response = client.get("/api/ui/settings")
    assert response.status_code == 200
    data = response.json()
    assert "components" in data
    assert "categories" in data
    assert data["edition"]["license"] == "MIT"
    assert "backup" in data


def test_mask_secret():
    assert mask_secret("") == ""
    assert mask_secret("sk-abcdefghij") == "••••••••ghij"
    assert mask_secret("...") == ""


def test_list_recent_backups(tmp_path, monkeypatch):
    backups = tmp_path / "backups"
    backups.mkdir()
    (backups / "seiton-20260101-120000").mkdir()
    (backups / "seiton-20260102-120000").mkdir()
    monkeypatch.setattr("app.ui.settings._backups_dir", lambda: backups)
    names = list_recent_backups(limit=3)
    assert names[0] == "seiton-20260102-120000"


@patch("app.ui.router.save_settings")
def test_settings_save_api(mock_save):
    from app.setup.schemas import SetupSaveResponse

    mock_save.return_value = SetupSaveResponse(
        saved=True,
        env_file="/tmp/.env",
        restart_required=True,
        message="OK — docker compose up -d",
    )
    response = client.post(
        "/api/ui/settings",
        json={"embeddings_enabled": True, "openai_model": "gpt-4o-mini"},
    )
    assert response.status_code == 200
    assert response.json()["saved"] is True
    mock_save.assert_called_once()


@patch("app.setup.routes.checks.check_openai", new_callable=AsyncMock)
def test_settings_test_api(mock_check):
    mock_check.return_value = (True, "OK")
    response = client.post(
        "/api/ui/settings/test",
        json={"check": "openai", "openai_api_key": "sk-test"},
    )
    assert response.status_code == 200
    assert response.json()["results"]["openai"]["ok"] is True


def test_load_settings_view_has_categories():
    view = load_settings_view()
    assert view.categories["idea"] == "Ideas"
    assert view.llm_provider == "openai"
