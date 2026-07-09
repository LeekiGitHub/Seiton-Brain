"""Tests fuer OpenAPI/Swagger (E13-4)."""

from fastapi.testclient import TestClient

from app.api.openapi import is_openapi_enabled
from app.config import settings
from app.main import app

client = TestClient(app)


def test_openapi_enabled_with_api_key(monkeypatch):
    monkeypatch.setattr(settings, "seiton_api_key", "secret-key")
    monkeypatch.setattr(settings, "seiton_debug", False)
    assert is_openapi_enabled() is True


def test_openapi_enabled_with_debug(monkeypatch):
    monkeypatch.setattr(settings, "seiton_api_key", "")
    monkeypatch.setattr(settings, "seiton_debug", True)
    assert is_openapi_enabled() is True


def test_openapi_disabled_without_key_or_debug(monkeypatch):
    monkeypatch.setattr(settings, "seiton_api_key", "")
    monkeypatch.setattr(settings, "seiton_debug", False)
    assert is_openapi_enabled() is False


def test_openapi_json_available_when_enabled():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "Seiton Brain"
    assert "/v1/capture" in schema["paths"]
    assert "ApiKeyAuth" in schema["components"]["securitySchemes"]
    capture = schema["paths"]["/v1/capture"]["post"]
    assert capture["security"] == [{"ApiKeyAuth": []}]


def test_swagger_ui_available_when_enabled():
    response = client.get("/docs")
    assert response.status_code == 200
    assert "swagger" in response.text.lower()


def test_redoc_available_when_enabled():
    response = client.get("/redoc")
    assert response.status_code == 200
