"""Provider-agnostic parsing of LLM classification JSON.

Every provider (OpenAI today, Ollama later) should use the same validation
instead of duplicating json.loads + Pydantic inline.
"""

import json
import logging

from app.llm.schemas import (
    ClassificationResult,
    LinkerResult,
    LLMAnswer,
    LLMDigest,
    RouterResult,
    WriterResult,
)

logger = logging.getLogger(__name__)

# Max LLM retries when JSON/schema validation fails.
MAX_PARSE_ATTEMPTS = 3


class ClassificationParseError(Exception):
    """LLM did not return a valid result after ``MAX_PARSE_ATTEMPTS`` attempts."""


class AnswerParseError(Exception):
    """RAG LLM did not return valid JSON after ``MAX_PARSE_ATTEMPTS`` attempts."""


class DigestParseError(Exception):
    """Digest LLM did not return valid JSON after ``MAX_PARSE_ATTEMPTS`` attempts."""


def parse_classification_json(content: str) -> ClassificationResult:
    """Parse raw LLM text into ``ClassificationResult``.

    Raises:
        json.JSONDecodeError: not valid JSON
        ValidationError: JSON does not match the Pydantic schema
    """
    data = json.loads(content)
    return ClassificationResult.model_validate(data)


def parse_router_json(content: str) -> RouterResult:
    """Parse Router JSON (E7-3)."""
    data = json.loads(content)
    return RouterResult.model_validate(data)


def parse_writer_json(content: str) -> WriterResult:
    """Parse Writer JSON (E7-3)."""
    data = json.loads(content)
    return WriterResult.model_validate(data)


def parse_linker_json(content: str) -> LinkerResult:
    """Parse Linker JSON (E7-3)."""
    data = json.loads(content)
    return LinkerResult.model_validate(data)


def parse_answer_json(content: str) -> LLMAnswer:
    """Parse raw RAG LLM answer into ``LLMAnswer`` (E17-3).

    Raises:
        json.JSONDecodeError: not valid JSON
        ValidationError: JSON does not match the Pydantic schema
    """
    data = json.loads(content)
    return LLMAnswer.model_validate(data)


def parse_digest_json(content: str) -> LLMDigest:
    """Parse raw digest LLM answer into ``LLMDigest`` (E17-8)."""
    data = json.loads(content)
    return LLMDigest.model_validate(data)
