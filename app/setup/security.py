"""Zugriffsschutz fuer den Setup-Wizard — nur localhost."""

from fastapi import HTTPException, Request

_LOCALHOST_HOSTS = frozenset({"127.0.0.1", "::1", "testclient"})


def require_localhost(request: Request) -> None:
    """Setup-Endpunkte nur von localhost (und TestClient)."""
    host = request.client.host if request.client else ""
    if host not in _LOCALHOST_HOSTS:
        raise HTTPException(
            status_code=403,
            detail="Setup ist nur von localhost erreichbar.",
        )
