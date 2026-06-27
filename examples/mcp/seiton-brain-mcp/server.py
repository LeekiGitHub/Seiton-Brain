"""Seiton Brain MCP-Server (E17-6).

Exponiert ``search_notes``, ``ask_brain`` und ``get_note`` als MCP-Tools —
duenne Wrapper um die REST-API (E17-5). Kein Embedding/RAG in diesem Prozess.

Start (stdio, fuer Cursor / Claude Desktop)::

    SEITON_API_KEY=... python server.py

Cursor-Konfiguration siehe ``README.md`` in diesem Ordner.
"""

from __future__ import annotations

import json
import os

from mcp.server.fastmcp import FastMCP

from client import SeitonApiClient, SeitonApiError

mcp = FastMCP("seiton-brain")
_client: SeitonApiClient | None = None


def _get_client() -> SeitonApiClient:
    global _client
    if _client is None:
        api_key = os.environ.get("SEITON_API_KEY", "").strip()
        if not api_key:
            raise SeitonApiError(
                401,
                "SEITON_API_KEY not set — configure it in the MCP server env",
            )
        _client = SeitonApiClient()
    return _client


def _json_result(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _format_error(exc: SeitonApiError) -> str:
    return json.dumps({"error": exc.detail, "status_code": exc.status_code})


@mcp.tool()
async def search_notes(
    query: str,
    semantic: bool = False,
    limit: int = 10,
) -> str:
    """Search notes in the Seiton Brain vault by keyword or semantic similarity.

    Args:
        query: Search terms or natural-language query.
        semantic: Use embedding search when true (requires EMBEDDINGS_ENABLED on server).
        limit: Max results (1-50).
    """
    try:
        client = _get_client()
        result = await client.search_notes(query, semantic=semantic, limit=limit)
        return _json_result(result)
    except SeitonApiError as exc:
        return _format_error(exc)


@mcp.tool()
async def ask_brain(question: str) -> str:
    """Ask a question about your Second Brain; returns RAG answer with sources.

    Args:
        question: Natural-language question grounded in your vault.
    """
    try:
        client = _get_client()
        result = await client.ask_brain(question)
        return _json_result(result)
    except SeitonApiError as exc:
        return _format_error(exc)


@mcp.tool()
async def get_note(
    entry_id: int | None = None,
    vault_path: str | None = None,
) -> str:
    """Load a full note by database entry ID or vault path (e.g. Ideas/My Note.md).

    Provide exactly one of entry_id or vault_path.
    """
    if entry_id is None and not vault_path:
        return json.dumps(
            {"error": "Provide entry_id or vault_path (not both empty)."}
        )
    if entry_id is not None and vault_path:
        return json.dumps(
            {"error": "Provide only one of entry_id or vault_path."}
        )
    try:
        client = _get_client()
        if entry_id is not None:
            result = await client.get_entry(entry_id)
        else:
            assert vault_path is not None
            result = await client.get_note_content(vault_path)
        return _json_result(result)
    except SeitonApiError as exc:
        return _format_error(exc)


if __name__ == "__main__":
    # Kein print() — wuerde den stdio JSON-RPC-Stream stoeren.
    mcp.run(transport="stdio")
