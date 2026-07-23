"""Ollama-LLM-Provider (E7-2) via OpenAI-kompatiblem ``/v1``-Endpoint.

Nutzt dieselbe Classify-/Answer-/Digest-Pipeline und dieselben Pydantic-Schemas
wie ``OpenAIProvider`` — nur Client-Base-URL und Modell kommen aus
``OLLAMA_BASE_URL`` / ``OLLAMA_MODEL``.
"""

from __future__ import annotations

from openai import AsyncOpenAI

from app.config import settings
from app.llm.openai_provider import OpenAIProvider


def ollama_v1_base_url(base_url: str) -> str:
    """Normalisiert die Ollama-Basis-URL auf ``…/v1/`` fuer den OpenAI-Client."""
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
