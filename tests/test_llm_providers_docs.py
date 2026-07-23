"""Smoke-Tests fuer LLM-Provider-Doku (E7-2)."""

from pathlib import Path

DOC = Path("docs/llm-providers.md")


def test_llm_providers_doc_exists():
    assert DOC.is_file()


def test_llm_providers_doc_covers_ollama():
    text = DOC.read_text(encoding="utf-8")
    for needle in (
        "LLM_PROVIDER=ollama",
        "OLLAMA_BASE_URL",
        "OLLAMA_MODEL",
        "host.docker.internal",
        "Whisper",
    ):
        assert needle in text, f"missing in llm-providers.md: {needle}"
