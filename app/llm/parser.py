"""Provider-unabhaengiges Parsen von LLM-Klassifikations-JSON.

Jeder Provider (OpenAI heute, Ollama spaeter) soll dieselbe Validierung nutzen,
statt json.loads + Pydantic inline zu duplizieren.
"""

import json
import logging

from app.llm.schemas import ClassificationResult, LLMAnswer, LLMDigest

logger = logging.getLogger(__name__)

# Wie viele LLM-Aufrufe bei kaputtem JSON/Schema maximal versucht werden.
MAX_PARSE_ATTEMPTS = 3


class ClassificationParseError(Exception):
    """LLM lieferte nach ``MAX_PARSE_ATTEMPTS`` Versuchen kein gueltiges Ergebnis."""


class AnswerParseError(Exception):
    """RAG-LLM lieferte nach ``MAX_PARSE_ATTEMPTS`` Versuchen kein gueltiges JSON."""


class DigestParseError(Exception):
    """Digest-LLM lieferte nach ``MAX_PARSE_ATTEMPTS`` Versuchen kein gueltiges JSON."""


def parse_classification_json(content: str) -> ClassificationResult:
    """Parst rohen LLM-Text in ``ClassificationResult``.

    Raises:
        json.JSONDecodeError: kein gueltiges JSON
        ValidationError: JSON passt nicht zum Pydantic-Schema
    """
    data = json.loads(content)
    return ClassificationResult.model_validate(data)


def parse_answer_json(content: str) -> LLMAnswer:
    """Parst rohe RAG-LLM-Antwort in ``LLMAnswer`` (E17-3).

    Raises:
        json.JSONDecodeError: kein gueltiges JSON
        ValidationError: JSON passt nicht zum Pydantic-Schema
    """
    data = json.loads(content)
    return LLMAnswer.model_validate(data)


def parse_digest_json(content: str) -> LLMDigest:
    """Parst rohe Digest-LLM-Antwort in ``LLMDigest`` (E17-8)."""
    data = json.loads(content)
    return LLMDigest.model_validate(data)
