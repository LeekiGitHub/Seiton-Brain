"""HTTP-Client fuer die Seiton-Brain REST-API (E17-5).

Wird vom MCP-Server genutzt; keine Engine-Logik hier — nur duenne
API-Wrapper, damit Cursor/Claude Desktop den Vault als Tool nutzen koennen.
"""

from __future__ import annotations

import os

import httpx

API_KEY_HEADER = "X-Seiton-Api-Key"
DEFAULT_BASE_URL = "http://localhost:8000"


class SeitonApiError(Exception):
    """API-Fehler mit HTTP-Status und Body-Snippet."""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"Seiton API {status_code}: {detail}")


class SeitonApiClient:
    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        *,
        timeout: float = 60.0,
    ) -> None:
        self.base_url = (
            base_url or os.environ.get("SEITON_API_URL", DEFAULT_BASE_URL)
        ).rstrip("/")
        self.api_key = api_key or os.environ.get("SEITON_API_KEY", "")
        self.timeout = timeout
        self._headers = {API_KEY_HEADER: self.api_key}

    async def search_notes(
        self, query: str, *, semantic: bool = False, limit: int = 10
    ) -> dict:
        return await self._get(
            "/v1/notes/search",
            params={"q": query, "semantic": semantic, "limit": limit},
        )

    async def ask_brain(self, question: str) -> dict:
        return await self._post("/v1/ask", json={"question": question})

    async def get_entry(self, entry_id: int) -> dict:
        return await self._get(f"/v1/entries/{entry_id}")

    async def get_note_content(self, vault_path: str) -> dict:
        return await self._get("/v1/notes/content", params={"vault_path": vault_path})

    async def _get(self, path: str, *, params: dict | None = None) -> dict:
        async with httpx.AsyncClient(
            base_url=self.base_url, headers=self._headers, timeout=self.timeout
        ) as client:
            response = await client.get(path, params=params)
            return _parse_response(response)

    async def _post(self, path: str, *, json: dict) -> dict:
        async with httpx.AsyncClient(
            base_url=self.base_url, headers=self._headers, timeout=self.timeout
        ) as client:
            response = await client.post(path, json=json)
            return _parse_response(response)


def _parse_response(response: httpx.Response) -> dict:
    if response.is_success:
        return response.json()
    detail = response.text[:500] if response.text else response.reason_phrase
    try:
        payload = response.json()
        if isinstance(payload, dict) and "detail" in payload:
            detail = str(payload["detail"])
    except Exception:
        pass
    raise SeitonApiError(response.status_code, detail)
