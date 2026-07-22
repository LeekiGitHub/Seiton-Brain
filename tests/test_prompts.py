"""Tests fuer Prompt-Versionierung (E4-4)."""

from pathlib import Path

from app.config import settings
from app.llm.prompts import load_prompt, normalize_prompt_version, resolve_prompt_path
from app.models.entry import Entry


def test_normalize_prompt_version():
    assert normalize_prompt_version("") == "v1"
    assert normalize_prompt_version("v1") == "v1"
    assert normalize_prompt_version("V2") == "v2"
    assert normalize_prompt_version("2") == "v2"


def test_resolve_classify_v1():
    path = resolve_prompt_path("classify", "v1")
    assert path.name == "classify.v1.txt"
    assert path.is_file()


def test_load_prompt_returns_version(monkeypatch):
    monkeypatch.setattr(settings, "seiton_prompt_version", "v1")
    text, version = load_prompt("classify")
    assert version == "v1"
    assert "category" in text
    assert "{input}" in text


def test_missing_version_falls_back_to_legacy(tmp_path, monkeypatch):
    monkeypatch.setattr("app.llm.prompts.PROMPTS_DIR", tmp_path)
    (tmp_path / "classify.txt").write_text("LEGACY {input}", encoding="utf-8")
    path = resolve_prompt_path("classify", "v99")
    assert path.name == "classify.txt"
    text, version = load_prompt("classify", "v99")
    assert text.startswith("LEGACY")
    assert version == "v99"


def test_entry_accepts_prompt_version():
    entry = Entry(
        title="T",
        category="note",
        summary="S",
        prompt_version="v1",
    )
    assert entry.prompt_version == "v1"


def test_default_config_prompt_version():
    assert settings.seiton_prompt_version == "v1"


def test_classify_v1_matches_legacy_content():
    v1 = Path("prompts/classify.v1.txt").read_text(encoding="utf-8")
    legacy = Path("prompts/classify.txt").read_text(encoding="utf-8")
    assert v1 == legacy
