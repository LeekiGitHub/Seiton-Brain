import json
import logging
from pathlib import Path

from openai import AsyncOpenAI
from pydantic import ValidationError

from app.config import settings
from app.llm.parser import (
    MAX_PARSE_ATTEMPTS,
    AnswerParseError,
    ClassificationParseError,
    DigestParseError,
    parse_answer_json,
    parse_classification_json,
    parse_digest_json,
)
from app.llm.schemas import ClassificationResult, LLMAnswer, LLMDigest
from app.llm.tags import normalize_tags
from app.vault.index import list_existing_notes
from app.vault.reader import format_notes_for_prompt, known_titles

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "classify.txt"
ANSWER_PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "answer.txt"
DIGEST_PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "digest.txt"
MAX_RELATED = 3
MAX_TAGS = 5


class OpenAIProvider:
    def __init__(self) -> None:
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.prompt_template = PROMPT_PATH.read_text()
        self.answer_template = ANSWER_PROMPT_PATH.read_text()
        self.digest_template = DIGEST_PROMPT_PATH.read_text()

    async def classify(self, text: str) -> ClassificationResult:
        existing = await list_existing_notes()
        prompt = (
            self.prompt_template.replace("{input}", text)
            .replace("{existing_notes}", format_notes_for_prompt(existing))
        )

        last_error: json.JSONDecodeError | ValidationError | None = None
        for attempt in range(1, MAX_PARSE_ATTEMPTS + 1):
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content or ""
            try:
                result = parse_classification_json(content)
            except (json.JSONDecodeError, ValidationError) as exc:
                last_error = exc
                logger.warning(
                    "LLM classification parse failed (attempt %d/%d): %s",
                    attempt,
                    MAX_PARSE_ATTEMPTS,
                    exc,
                )
                continue

            result = self._sanitize_related(result, existing)
            result = self._sanitize_action(result, existing)
            result = self._sanitize_tags(result)
            return result

        assert last_error is not None
        raise ClassificationParseError(
            f"LLM returned invalid classification JSON after {MAX_PARSE_ATTEMPTS} attempts"
        ) from last_error

    def _sanitize_related(
        self, result: ClassificationResult, existing: list
    ) -> ClassificationResult:
        titles = known_titles(existing)
        resolved: list[str] = []
        for title in result.related:
            canonical = titles.get(title.lower())
            if canonical and canonical.lower() != result.title.lower():
                if canonical not in resolved:
                    resolved.append(canonical)
        result.related = resolved[:MAX_RELATED]
        return result

    def _sanitize_action(
        self, result: ClassificationResult, existing: list
    ) -> ClassificationResult:
        """Stellt sicher, dass append nur fuer real existierende Titel erlaubt ist.

        Halluziniert das LLM einen target_title, der nicht im Vault existiert,
        fallen wir auf action='create' zurueck statt eine nicht existierende
        Notiz zu ergaenzen.
        """
        if result.action != "append":
            result.target_title = None
            return result

        if not result.target_title:
            logger.warning(
                "LLM returned action=append without target_title; falling back to create"
            )
            result.action = "create"
            result.target_title = None
            return result

        titles = known_titles(existing)
        canonical = titles.get(result.target_title.lower())
        if not canonical:
            logger.warning(
                "LLM hallucinated target_title=%r; falling back to action=create",
                result.target_title,
            )
            result.action = "create"
            result.target_title = None
            return result

        result.target_title = canonical
        return result

    def _sanitize_tags(self, result: ClassificationResult) -> ClassificationResult:
        result.tags = normalize_tags(result.tags, max_tags=MAX_TAGS)
        return result

    async def answer(self, question: str, context: str) -> LLMAnswer:
        """RAG-Antwort (E17-3): Frage + Kontext-Snippets -> JSON-Antwort.

        Gleiches Retry-Muster wie ``classify`` (JSON-Mode, bis zu
        ``MAX_PARSE_ATTEMPTS`` Versuche). Quellen-Aufloesung auf echte Notizen
        passiert im aufrufenden Service, nicht hier.
        """
        prompt = self.answer_template.replace("{question}", question).replace(
            "{context}", context
        )

        last_error: json.JSONDecodeError | ValidationError | None = None
        for attempt in range(1, MAX_PARSE_ATTEMPTS + 1):
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content or ""
            try:
                return parse_answer_json(content)
            except (json.JSONDecodeError, ValidationError) as exc:
                last_error = exc
                logger.warning(
                    "RAG answer parse failed (attempt %d/%d): %s",
                    attempt,
                    MAX_PARSE_ATTEMPTS,
                    exc,
                )
                continue

        assert last_error is not None
        raise AnswerParseError(
            f"LLM returned invalid answer JSON after {MAX_PARSE_ATTEMPTS} attempts"
        ) from last_error

    async def digest(self, topic: str, context: str, *, days: int | None) -> LLMDigest:
        """Digest-Synthese (E17-8): Thema + Kontext-Notizen -> JSON."""
        days_label = str(days) if days is not None else "all"
        prompt = (
            self.digest_template.replace("{topic}", topic)
            .replace("{context}", context)
            .replace("{days}", days_label)
        )

        last_error: json.JSONDecodeError | ValidationError | None = None
        for attempt in range(1, MAX_PARSE_ATTEMPTS + 1):
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content or ""
            try:
                return parse_digest_json(content)
            except (json.JSONDecodeError, ValidationError) as exc:
                last_error = exc
                logger.warning(
                    "Digest parse failed (attempt %d/%d): %s",
                    attempt,
                    MAX_PARSE_ATTEMPTS,
                    exc,
                )
                continue

        assert last_error is not None
        raise DigestParseError(
            f"LLM returned invalid digest JSON after {MAX_PARSE_ATTEMPTS} attempts"
        ) from last_error
