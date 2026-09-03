"""Ollama LLM provider (E7-2) via OpenAI-compatible ``/v1`` endpoint.

Uses the same classify/answer/digest pipeline and Pydantic schemas as
``OpenAIProvider`` — only client base URL and model come from
``OLLAMA_BASE_URL`` / ``OLLAMA_MODEL``.
"""

from __future__ import annotations

from openai import AsyncOpenAI

from app.config import settings
from app.llm.openai_provider import OpenAIProvider


def ollama_v1_base_url(base_url: str) -> str:
    """Normalize the Ollama base URL to ``…/v1/`` for the OpenAI client."""
    base = base_url.strip().rstrip("/")
    if base.endswith("/v1"):
        return f"{base}/"
    return f"{base}/v1/"


class OllamaProvider(OpenAIProvider):
    def __init__(self) -> None:
        super().__init__(
            client=AsyncOpenAI(
                api_key="ollama",
                base_url=ollama_v1_base_url(settings.ollama_base_url),
            ),
            model=settings.ollama_model,
        )
