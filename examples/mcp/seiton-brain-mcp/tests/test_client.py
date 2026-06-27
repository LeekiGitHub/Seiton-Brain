"""Tests fuer den Seiton-Brain MCP HTTP-Client."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx
import pytest

# client.py liegt im Parent-Ordner (kein installiertes Paket)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from client import SeitonApiClient, SeitonApiError, _parse_response


def test_parse_response_success():
    response = httpx.Response(200, json={"ok": True})
    assert _parse_response(response) == {"ok": True}


def test_parse_response_error_raises():
    response = httpx.Response(401, json={"detail": "Invalid API key"})
    with pytest.raises(SeitonApiError) as exc:
        _parse_response(response)
    assert exc.value.status_code == 401
    assert "Invalid API key" in exc.value.detail


@pytest.mark.asyncio
@patch.object(SeitonApiClient, "_get", new_callable=AsyncMock)
async def test_search_notes_calls_api(mock_get):
    mock_get.return_value = {"items": [], "query": "fitness", "limit": 5, "semantic": True}
    client = SeitonApiClient(base_url="http://test", api_key="secret")

    result = await client.search_notes("fitness", semantic=True, limit=5)

    assert result["query"] == "fitness"
    mock_get.assert_awaited_once_with(
        "/v1/notes/search",
        params={"q": "fitness", "semantic": True, "limit": 5},
    )


@pytest.mark.asyncio
@patch.object(SeitonApiClient, "_post", new_callable=AsyncMock)
async def test_ask_brain_calls_api(mock_post):
    mock_post.return_value = {"answer": "Ja", "sources": [], "confidence": 0.8}
    client = SeitonApiClient(base_url="http://test", api_key="k")

    result = await client.ask_brain("Frage?")

    assert result["answer"] == "Ja"
    mock_post.assert_awaited_once_with("/v1/ask", json={"question": "Frage?"})


@pytest.mark.asyncio
@patch.object(SeitonApiClient, "_get", new_callable=AsyncMock)
async def test_get_entry_and_note_content(mock_get):
    client = SeitonApiClient(base_url="http://test", api_key="k")
    mock_get.return_value = {"id": 1, "title": "T"}

    await client.get_entry(42)
    mock_get.assert_awaited_with("/v1/entries/42")

    mock_get.return_value = {"vault_path": "Notes/A.md", "content": "# A"}
    await client.get_note_content("Notes/A.md")
    mock_get.assert_awaited_with(
        "/v1/notes/content", params={"vault_path": "Notes/A.md"}
    )
