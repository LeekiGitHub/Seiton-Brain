"""Provider-unabhaengiges Parsen von LLM-Klassifikations-JSON.

Jeder Provider (OpenAI heute, Ollama spaeter) soll dieselbe Validierung nutzen,
statt json.loads + Pydantic inline zu duplizieren.
"""

import json
import logging

from app.llm.schemas import ClassificationResult

logger = logging.getLogger(__name__)

# Wie viele LLM-Aufrufe bei kaputtem JSON/Schema maximal versucht werden.
MAX_PARSE_ATTEMPTS = 3


class ClassificationParseError(Exception):
    """LLM lieferte nach ``MAX_PARSE_ATTEMPTS`` Versuchen kein gueltiges Ergebnis."""


def parse_classification_json(content: str) -> ClassificationResult:
    """Parst rohen LLM-Text in ``ClassificationResult``.

    Raises:
        json.JSONDecodeError: kein gueltiges JSON
        ValidationError: JSON passt nicht zum Pydantic-Schema
    """
    data = json.loads(content)
    return ClassificationResult.model_validate(data)
