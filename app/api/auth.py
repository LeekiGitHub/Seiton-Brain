"""API-Key-Authentifizierung fuer REST-Endpunkte unter ``/v1/``."""

import secrets

from fastapi import Header, HTTPException

from app.config import settings

API_KEY_HEADER = "X-Seiton-Api-Key"


async def verify_api_key(
    x_seiton_api_key: str | None = Header(default=None, alias=API_KEY_HEADER),
) -> None:
    """Schuetzt ``/v1/*`` mit ``SEITON_API_KEY``.

    - Key nicht gesetzt in ``.env`` → API deaktiviert (503), bewusste Entscheidung
      statt offenem Endpunkt im Internet.
    - Key gesetzt, Header fehlt oder falsch → 401.
    """
    configured = settings.seiton_api_key
    if not configured:
        raise HTTPException(
            status_code=503,
            detail=(
                "REST API disabled — set SEITON_API_KEY in .env to enable /v1 endpoints"
            ),
        )

    if not x_seiton_api_key:
        raise HTTPException(status_code=401, detail="Missing API key")

    if len(x_seiton_api_key) != len(configured) or not secrets.compare_digest(
        x_seiton_api_key, configured
    ):
        raise HTTPException(status_code=401, detail="Invalid API key")
