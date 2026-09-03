"""Tests for specialized LLM roles (E7-3)."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError

from app.config import settings
from app.llm.openai_provider import OpenAIProvider
from app.llm.parser import (
    ClassificationParseError,
    parse_linker_json,
    parse_router_json,
    parse_writer_json,
)
from app.llm.prompts import load_prompt, resolve_prompt_path
from app.llm.roles import merge_role_results
from app.llm.schemas import LinkerResult, RouterResult, WriterResult
from app.vault.reader import VaultNote


def test_merge_role_results():
    router = RouterResult(
        action="append",
        target_title="Fitness App",
        category="idea",
        title="Workout log",
    )
    writer = WriterResult(summary="Neue Features.", tags=["fitness"])
    linker = LinkerResult(related=["Other"])
    result = merge_role_results(router, writer, linker)
    assert result.action == "append"
    assert result.target_title == "Fitness App"
    assert result.category == "idea"
    assert result.title == "Workout log"
    assert result.summary == "Neue Features."
    assert result.tags == ["fitness"]
    assert result.related == ["Other"]


def test_merge_role_results_without_linker():
    router = RouterResult(category="note", title="T")
    writer = WriterResult(summary="S")
    result = merge_role_results(router, writer, None)
    assert result.related == []
    assert result.action == "create"


def test_parse_role_json_roundtrip():
    assert parse_router_json(
        '{"action":"create","category":"note","title":"T","target_title":null}'
    ).title == "T"
    assert parse_writer_json('{"summary":"S","tags":["a"]}').tags == ["a"]
    assert parse_linker_json('{"related":["X"]}').related == ["X"]


def test_parse_router_json_requires_fields():
    with pytest.raises(ValidationError):
        parse_router_json('{"action":"create"}')


def test_role_prompt_files_exist():
    for name in ("router", "writer", "linker"):
        path = resolve_prompt_path(name, "v1")
        assert path.is_file()
        text, ver = load_prompt(name, "v1")
        assert ver == "v1"
        assert "{input}" in text


def _role_provider() -> OpenAIProvider:
    provider = OpenAIProvider.__new__(OpenAIProvider)
    provider.client = MagicMock()
    provider.model = "gpt-4o-mini"
    provider.prompt_version = "v1"
    provider.router_template = (
        "{input} {existing_notes} {category_list} {category_guide}"
    )
    provider.writer_template = (
        "{input} {action} {target_title} {category} {title}"
    )
    provider.linker_template = (
        "{input} {existing_notes} {title} {category} {summary}"
    )
    return provider


@pytest.mark.asyncio
async def test_classify_roles_two_steps_when_vault_empty(monkeypatch):
    monkeypatch.setattr(settings, "seiton_llm_roles_enabled", True)
    provider = _role_provider()
    router = json.dumps(
        {"action": "create", "category": "note", "title": "Neu", "target_title": None}
    )
    writer = json.dumps({"summary": "Inhalt.", "tags": ["x"]})
    provider.client.chat.completions.create = AsyncMock(
        side_effect=[
            MagicMock(choices=[MagicMock(message=MagicMock(content=router))]),
            MagicMock(choices=[MagicMock(message=MagicMock(content=writer))]),
        ]
    )

    with (
        patch(
            "app.llm.openai_provider.list_existing_notes",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch("app.llm.openai_provider.prefilter_notes_for_llm", return_value=[]),
    ):
        result = await provider.classify("hallo")

    assert result.title == "Neu"
    assert result.summary == "Inhalt."
    assert result.tags == ["x"]
    assert result.related == []
    assert provider.client.chat.completions.create.await_count == 2


@pytest.mark.asyncio
async def test_classify_roles_three_steps_with_links(monkeypatch):
    monkeypatch.setattr(settings, "seiton_llm_roles_enabled", True)
    provider = _role_provider()
    existing = [
        VaultNote(title="Fitness App", category="idea", folder="Ideas", snippet=""),
    ]
    router = json.dumps(
        {
            "action": "append",
            "category": "idea",
            "title": "Update",
            "target_title": "fitness app",
        }
    )
    writer = json.dumps({"summary": "Mehr Features.", "tags": ["#Fitness"]})
    linker = json.dumps({"related": ["fitness app", "Unknown"]})
    provider.client.chat.completions.create = AsyncMock(
        side_effect=[
            MagicMock(choices=[MagicMock(message=MagicMock(content=router))]),
            MagicMock(choices=[MagicMock(message=MagicMock(content=writer))]),
            MagicMock(choices=[MagicMock(message=MagicMock(content=linker))]),
        ]
    )

    with (
        patch(
            "app.llm.openai_provider.list_existing_notes",
            new_callable=AsyncMock,
            return_value=existing,
        ),
        patch(
            "app.llm.openai_provider.prefilter_notes_for_llm",
            return_value=existing,
        ),
    ):
        result = await provider.classify("add to fitness")

    assert result.action == "append"
    assert result.target_title == "Fitness App"
    assert result.tags == ["fitness"]
    assert result.related == ["Fitness App"]  # Unknown verworfen
    assert provider.client.chat.completions.create.await_count == 3


@pytest.mark.asyncio
async def test_classify_roles_retries_router(monkeypatch):
    monkeypatch.setattr(settings, "seiton_llm_roles_enabled", True)
    provider = _role_provider()
    bad = MagicMock(choices=[MagicMock(message=MagicMock(content="nope"))])
    router = MagicMock(
        choices=[
            MagicMock(
                message=MagicMock(
                    content=json.dumps(
                        {
                            "action": "create",
                            "category": "note",
                            "title": "Ok",
                            "target_title": None,
                        }
                    )
                )
            )
        ]
    )
    writer = MagicMock(
        choices=[
            MagicMock(
                message=MagicMock(content=json.dumps({"summary": "S", "tags": []}))
            )
        ]
    )
    provider.client.chat.completions.create = AsyncMock(side_effect=[bad, router, writer])

    with (
        patch(
            "app.llm.openai_provider.list_existing_notes",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch("app.llm.openai_provider.prefilter_notes_for_llm", return_value=[]),
    ):
        result = await provider.classify("x")

    assert result.title == "Ok"
    assert provider.client.chat.completions.create.await_count == 3


@pytest.mark.asyncio
async def test_classify_roles_raises_when_router_exhausted(monkeypatch):
    monkeypatch.setattr(settings, "seiton_llm_roles_enabled", True)
    provider = _role_provider()
    bad = MagicMock(choices=[MagicMock(message=MagicMock(content="{"))])
    provider.client.chat.completions.create = AsyncMock(return_value=bad)

    with (
        patch(
            "app.llm.openai_provider.list_existing_notes",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch("app.llm.openai_provider.prefilter_notes_for_llm", return_value=[]),
        pytest.raises(ClassificationParseError),
    ):
        await provider.classify("x")

    assert provider.client.chat.completions.create.await_count == 3
