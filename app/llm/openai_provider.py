import json
import logging
from collections.abc import Callable
from pathlib import Path
from typing import TypeVar

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
    parse_linker_json,
    parse_router_json,
    parse_writer_json,
)
from app.llm.prompts import load_prompt
from app.llm.roles import merge_role_results
from app.llm.schemas import ClassificationResult, LLMAnswer, LLMDigest, LinkerResult
from app.llm.tags import normalize_tags
from app.vault.categories import (
    format_category_guide_for_prompt,
    format_category_list_for_prompt,
)
from app.vault.index import list_existing_notes
from app.vault.prefilter import prefilter_notes_for_llm
from app.vault.reader import format_notes_for_prompt, known_titles

logger = logging.getLogger(__name__)

ANSWER_PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "answer.txt"
DIGEST_PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "digest.txt"
MAX_RELATED = 3
MAX_TAGS = 5

T = TypeVar("T")


class OpenAIProvider:
    def __init__(
        self,
        *,
        client: AsyncOpenAI | None = None,
        model: str | None = None,
    ) -> None:
        self.client = client or AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = model or settings.openai_model
        self.prompt_template, self.prompt_version = load_prompt("classify")
        self.router_template, _ = load_prompt("router")
        self.writer_template, _ = load_prompt("writer")
        self.linker_template, _ = load_prompt("linker")
        self.answer_template = ANSWER_PROMPT_PATH.read_text()
        self.digest_template = DIGEST_PROMPT_PATH.read_text()

    async def classify(self, text: str) -> ClassificationResult:
        candidates = await list_existing_notes()
        existing = prefilter_notes_for_llm(
            candidates,
            text,
            max_notes=settings.seiton_llm_note_limit,
        )
        if settings.seiton_llm_roles_enabled:
            return await self._classify_with_roles(text, existing)
        return await self._classify_monolithic(text, existing)

    async def _classify_monolithic(
        self, text: str, existing: list
    ) -> ClassificationResult:
        """One-shot classify (fallback when ``SEITON_LLM_ROLES_ENABLED=false``)."""
        prompt = (
            self.prompt_template.replace("{input}", text)
            .replace("{existing_notes}", format_notes_for_prompt(existing))
            .replace("{category_list}", format_category_list_for_prompt())
            .replace("{category_guide}", format_category_guide_for_prompt())
        )
        result = await self._chat_json(
            prompt,
            parse_classification_json,
            label="classification",
        )
        return self._sanitize_classification(result, existing)

    async def _classify_with_roles(
        self, text: str, existing: list
    ) -> ClassificationResult:
        """Router → Writer → (Linker) — max 3 steps (E7-3 / ADR 0003)."""
        notes_block = format_notes_for_prompt(existing)
        category_list = format_category_list_for_prompt()
        category_guide = format_category_guide_for_prompt()

        router_prompt = (
            self.router_template.replace("{input}", text)
            .replace("{existing_notes}", notes_block)
            .replace("{category_list}", category_list)
            .replace("{category_guide}", category_guide)
        )
        router = await self._chat_json(
            router_prompt, parse_router_json, label="router"
        )

        writer_prompt = (
            self.writer_template.replace("{input}", text)
            .replace("{action}", router.action)
            .replace("{target_title}", router.target_title or "null")
            .replace("{category}", router.category)
            .replace("{title}", router.title)
        )
        writer = await self._chat_json(
            writer_prompt, parse_writer_json, label="writer"
        )

        linker: LinkerResult | None = None
        if existing:
            linker_prompt = (
                self.linker_template.replace("{input}", text)
                .replace("{existing_notes}", notes_block)
                .replace("{title}", router.title)
                .replace("{category}", router.category)
                .replace("{summary}", writer.summary)
            )
            linker = await self._chat_json(
                linker_prompt, parse_linker_json, label="linker"
            )

        result = merge_role_results(router, writer, linker)
        return self._sanitize_classification(result, existing)

    def _sanitize_classification(
        self, result: ClassificationResult, existing: list
    ) -> ClassificationResult:
        result = self._sanitize_related(result, existing)
        result = self._sanitize_action(result, existing)
        result = self._sanitize_tags(result)
        return result

    async def _chat_json(
        self,
        prompt: str,
        parse_fn: Callable[[str], T],
        *,
        label: str,
    ) -> T:
        """JSON-mode chat with retry on parse/schema errors."""
        last_error: json.JSONDecodeError | ValidationError | None = None
        for attempt in range(1, MAX_PARSE_ATTEMPTS + 1):
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content or ""
            try:
                return parse_fn(content)
            except (json.JSONDecodeError, ValidationError) as exc:
                last_error = exc
                logger.warning(
                    "LLM %s parse failed (attempt %d/%d): %s",
                    label,
                    attempt,
                    MAX_PARSE_ATTEMPTS,
                    exc,
                )
                continue

        assert last_error is not None
        raise ClassificationParseError(
            f"LLM returned invalid {label} JSON after {MAX_PARSE_ATTEMPTS} attempts"
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
        """Ensure append is only allowed for titles that actually exist.

        If the LLM hallucinates a target_title that is not in the vault, fall
        back to action='create' instead of appending to a non-existent note.
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
        """RAG answer (E17-3): question + context snippets → JSON answer.

        Same retry pattern as ``classify`` (JSON mode, up to
        ``MAX_PARSE_ATTEMPTS`` attempts). Source resolution onto real notes
        happens in the calling service, not here.
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
        """Digest synthesis (E17-8): topic + context notes → JSON."""
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
