"""Seiton Brain MCP server (E17-6, E22-4).

Exposes ``search_notes``, ``ask_brain``, ``get_note``, ``capture_note``
and ``digest`` as MCP tools — thin wrappers around the REST API (E17-5).
No embedding/RAG in this process.

Start (stdio, for Cursor / Claude Desktop)::

    SEITON_API_KEY=... python server.py

Cursor config: see ``README.md`` in this folder.
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


@mcp.tool()
async def capture_note(text: str) -> str:
    """Save a thought, idea, task or note into the Seiton Brain (E22-4).

    The text is classified by the LLM (category, title, tags) and stored in
    the vault + database — same pipeline as Telegram/Web-UI capture.

    Args:
        text: The note content to capture (plain text or markdown).
    """
    if not text.strip():
        return json.dumps({"error": "text must not be empty"})
    try:
        client = _get_client()
        result = await client.capture_note(text)
        return _json_result(result)
    except SeitonApiError as exc:
        return _format_error(exc)


@mcp.tool()
async def digest(
    topic: str,
    days: int | None = 7,
    limit: int = 15,
) -> str:
    """Synthesize related notes on a topic into a digest with sources (E22-4).

    Args:
        topic: Topic, folder or category to summarize (e.g. "Ideas", "fitness").
        days: Look-back window in days (1-365); null/None means all notes.
        limit: Max notes considered (1-30).
    """
    try:
        client = _get_client()
        result = await client.digest_topic(topic, days=days, limit=limit)
        return _json_result(result)
    except SeitonApiError as exc:
        return _format_error(exc)


if __name__ == "__main__":
    # No print() — would corrupt the stdio JSON-RPC stream.
    mcp.run(transport="stdio")
