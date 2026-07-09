"""OpenAPI/Swagger-Konfiguration (E13-4)."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.api.auth import API_KEY_HEADER
from app.config import settings

OPENAPI_VERSION = "0.2.0"


def is_openapi_enabled() -> bool:
    """Swagger nur wenn REST-API aktiv (Key gesetzt) oder Debug-Modus."""
    if settings.seiton_debug:
        return True
    return bool(settings.seiton_api_key.strip())


def fastapi_openapi_kwargs() -> dict:
    """Kwargs fuer FastAPI(docs_url=..., openapi_url=...)."""
    enabled = is_openapi_enabled()
    if not enabled:
        return {
            "docs_url": None,
            "redoc_url": None,
            "openapi_url": None,
        }
    return {
        "title": "Seiton Brain",
        "description": (
            "REST-API v1 fuer Capture, Suche, RAG und Digest. "
            f"Authentifizierung: Header `{API_KEY_HEADER}`."
        ),
        "version": OPENAPI_VERSION,
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "openapi_url": "/openapi.json",
    }


def attach_openapi_schema(app: FastAPI) -> None:
    """Registriert API-Key-Security-Schema fuer /v1/*-Pfade."""

    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        components = schema.setdefault("components", {})
        security_schemes = components.setdefault("securitySchemes", {})
        security_schemes["ApiKeyAuth"] = {
            "type": "apiKey",
            "in": "header",
            "name": API_KEY_HEADER,
            "description": "Gleicher Wert wie SEITON_API_KEY in .env",
        }
        for path, path_item in schema.get("paths", {}).items():
            if not path.startswith("/v1"):
                continue
            for operation in path_item.values():
                if isinstance(operation, dict):
                    operation["security"] = [{"ApiKeyAuth": []}]
        app.openapi_schema = schema
        return app.openapi_schema

    app.openapi = custom_openapi  # type: ignore[method-assign]
