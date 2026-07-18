"""Tests fuer konfigurierbare Kategorien (E4-3)."""

from pathlib import Path

from app.config import settings
from app.vault.categories import (
    clear_category_cache,
    folder_for_category,
    format_category_list_for_prompt,
    get_category_folders,
)
from app.vault.writer import write_note
from app.llm.schemas import ClassificationResult


def test_defaults_without_config(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "obsidian_vault_path", str(tmp_path))
    monkeypatch.setattr(settings, "seiton_vault_config", "")
    clear_category_cache()
    folders = get_category_folders()
    assert folders["idea"] == "Ideas"
    assert folder_for_category("unknown") == "Notes"


def test_load_vault_config_from_vault_root(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "obsidian_vault_path", str(tmp_path))
    monkeypatch.setattr(settings, "seiton_vault_config", "")
    (tmp_path / "vault_config.yaml").write_text(
        """
categories:
  idea: Concepts
  project: Projects
  note: Inbox
default_folder: Inbox
""",
        encoding="utf-8",
    )
    clear_category_cache()
    folders = get_category_folders()
    assert folders == {
        "idea": "Concepts",
        "project": "Projects",
        "note": "Inbox",
    }
    assert folder_for_category("project") == "Projects"
    assert folder_for_category("missing") == "Inbox"
    assert "project" in format_category_list_for_prompt()


def test_explicit_seiton_vault_config_path(tmp_path, monkeypatch):
    cfg = tmp_path / "custom.yaml"
    cfg.write_text(
        "categories:\n  hobby: Hobbies\n  note: Notes\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(settings, "obsidian_vault_path", str(tmp_path / "vault"))
    monkeypatch.setattr(settings, "seiton_vault_config", str(cfg))
    clear_category_cache()
    assert get_category_folders()["hobby"] == "Hobbies"


def test_write_note_uses_custom_folder(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "obsidian_vault_path", str(tmp_path))
    monkeypatch.setattr(settings, "seiton_vault_config", "")
    (tmp_path / "vault_config.yaml").write_text(
        "categories:\n  idea: Concepts\n  note: Notes\n",
        encoding="utf-8",
    )
    clear_category_cache()
    path = write_note(
        ClassificationResult(
            category="idea",
            title="Custom Folder",
            summary="Body.",
        )
    )
    assert path.parent.name == "Concepts"
    assert path.is_file()


def test_example_vault_config_parses():
    example = Path("vault_config.example.yaml")
    assert example.is_file()
    text = example.read_text(encoding="utf-8")
    assert "categories:" in text
    assert "school:" in text
