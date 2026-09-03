"""Tests for vision image description (E18-6)."""

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from app.config import settings
from app.llm.prompts import load_prompt, resolve_prompt_path
from app.llm.schemas import VisionImageResult
from app.vault import vision as vision_mod


def test_vision_prompt_exists():
    path = resolve_prompt_path("vision", "v1")
    assert path.is_file()
    text, ver = load_prompt("vision", "v1")
    assert ver == "v1"
    assert "description" in text
    assert "tags" in text


def test_vision_ready_respects_config(monkeypatch):
    monkeypatch.setattr(settings, "seiton_vision_enabled", False)
    monkeypatch.setattr(settings, "openai_api_key", "sk-test")
    assert vision_mod.vision_ready() is False

    monkeypatch.setattr(settings, "seiton_vision_enabled", True)
    assert vision_mod.vision_ready() is True

    monkeypatch.setattr(settings, "openai_api_key", "")
    assert vision_mod.vision_ready() is False


def test_format_vision_text_includes_tags():
    result = VisionImageResult(
        description="Ein rotes Auto vor einem Haus.",
        tags=["#Car", "house", "car"],
    )
    text = vision_mod.format_vision_text(result)
    assert text.startswith("Ein rotes Auto")
    assert "Tags: car, house" in text


def test_format_vision_text_without_tags():
    result = VisionImageResult(description="Leerer Himmel.", tags=[])
    assert vision_mod.format_vision_text(result) == "Leerer Himmel."


def test_parse_vision_json():
    raw = json.dumps({"description": "D", "tags": ["a"]})
    result = vision_mod.parse_vision_json(raw)
    assert result.description == "D"
    assert result.tags == ["a"]


def test_parse_vision_json_requires_description():
    with pytest.raises(ValidationError):
        vision_mod.parse_vision_json('{"tags":[]}')


def test_describe_image_returns_none_when_disabled(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(vision_mod, "vision_ready", lambda: False)
    img = tmp_path / "a.jpg"
    img.write_bytes(b"x")
    assert vision_mod.describe_image(img) is None


def test_describe_image_calls_openai(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(vision_mod, "vision_ready", lambda: True)
    monkeypatch.setattr(vision_mod, "_vision_model", lambda: "gpt-4o-mini")
    monkeypatch.setattr(
        vision_mod,
        "load_prompt",
        lambda _name: ("Describe JSON", "v1"),
    )

    img = tmp_path / "shot.png"
    img.write_bytes(b"\x89PNG-fake")

    payload = json.dumps(
        {"description": "Berglandschaft im Nebel.", "tags": ["nature", "fog"]}
    )
    client = MagicMock()
    client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content=payload))]
    )

    result = vision_mod.describe_image(img, client=client)
    assert result is not None
    assert "Berglandschaft" in result.description
    assert result.tags == ["nature", "fog"]

    kwargs = client.chat.completions.create.call_args.kwargs
    assert kwargs["model"] == "gpt-4o-mini"
    assert kwargs["response_format"] == {"type": "json_object"}
    content = kwargs["messages"][0]["content"]
    assert content[0]["type"] == "text"
    assert content[1]["type"] == "image_url"
    assert content[1]["image_url"]["url"].startswith("data:image/png;base64,")


def test_describe_image_retries_then_succeeds(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(vision_mod, "vision_ready", lambda: True)
    monkeypatch.setattr(vision_mod, "_vision_model", lambda: "gpt-4o-mini")
    monkeypatch.setattr(vision_mod, "load_prompt", lambda _n: ("p", "v1"))

    img = tmp_path / "a.jpg"
    img.write_bytes(b"jpeg")

    good = MagicMock(
        choices=[
            MagicMock(
                message=MagicMock(
                    content=json.dumps({"description": "Ok", "tags": []})
                )
            )
        ]
    )
    client = MagicMock()
    client.chat.completions.create.side_effect = [
        MagicMock(choices=[MagicMock(message=MagicMock(content="not-json"))]),
        good,
    ]

    result = vision_mod.describe_image(img, client=client)
    assert result is not None
    assert result.description == "Ok"
    assert client.chat.completions.create.call_count == 2


def test_describe_image_returns_none_after_retries(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(vision_mod, "vision_ready", lambda: True)
    monkeypatch.setattr(vision_mod, "_vision_model", lambda: "gpt-4o-mini")
    monkeypatch.setattr(vision_mod, "load_prompt", lambda _n: ("p", "v1"))

    img = tmp_path / "a.jpg"
    img.write_bytes(b"jpeg")

    client = MagicMock()
    client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="{"))]
    )
    assert vision_mod.describe_image(img, client=client) is None
    assert client.chat.completions.create.call_count == 3
