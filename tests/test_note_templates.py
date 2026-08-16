"""Tests fuer Notiz-Templates (E26-1 Render, E26-2 Validierung/Fallback)."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.config import settings
from app.llm.schemas import ClassificationResult
from app.vault.templates import (
    DEFAULT_TEMPLATE,
    TEMPLATE_RELATIVE_PATH,
    load_note_template,
    render_note_body,
    template_status,
    validate_template,
)
from app.vault.writer import write_note


def _result(**overrides) -> ClassificationResult:
    defaults = dict(
        category="idea",
        title="Meine Idee",
        summary="Eine kurze Zusammenfassung.",
        tags=["fitness", "app"],
        related=[],
    )
    defaults.update(overrides)
    return ClassificationResult(**defaults)


def _write_template(vault, text: str) -> None:
    path = vault / TEMPLATE_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


# ─── E26-2: Validierung ─────────────────────────────────────────────────────


def test_validate_default_template_ok():
    assert validate_template(DEFAULT_TEMPLATE) == []


def test_validate_rejects_unknown_placeholder():
    errors = validate_template("# {{title}}\n{{summary}}\n{{unknown_field}}")
    assert any("{{unknown_field}}" in e for e in errors)


def test_validate_rejects_own_frontmatter():
    errors = validate_template("---\ntitle: x\n---\n{{summary}}")
    assert any("Frontmatter" in e for e in errors)


def test_validate_requires_summary():
    errors = validate_template("# {{title}}\n\n{{tags}}")
    assert any("{{summary}}" in e for e in errors)


# ─── Laden + Status ─────────────────────────────────────────────────────────


def test_load_returns_default_without_file(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "obsidian_vault_path", str(tmp_path))
    assert load_note_template() == DEFAULT_TEMPLATE
    assert template_status() == "default"


def test_load_returns_custom_template(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "obsidian_vault_path", str(tmp_path))
    _write_template(tmp_path, "## {{title}}\n\n{{summary}}\n")
    assert load_note_template() == "## {{title}}\n\n{{summary}}\n"
    assert template_status() == "custom"


def test_load_falls_back_on_invalid_template(tmp_path, monkeypatch, caplog):
    monkeypatch.setattr(settings, "obsidian_vault_path", str(tmp_path))
    _write_template(tmp_path, "{{summary}} {{kaputt}}")
    with caplog.at_level("WARNING"):
        assert load_note_template() == DEFAULT_TEMPLATE
    assert "ungültig" in caplog.text
    assert template_status() == "invalid"


def test_load_falls_back_on_empty_template(tmp_path, monkeypatch, caplog):
    monkeypatch.setattr(settings, "obsidian_vault_path", str(tmp_path))
    _write_template(tmp_path, "   \n")
    with caplog.at_level("WARNING"):
        assert load_note_template() == DEFAULT_TEMPLATE


# ─── E26-1: Rendering ───────────────────────────────────────────────────────


def test_render_default_matches_legacy_layout(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "obsidian_vault_path", str(tmp_path))
    body = render_note_body(_result())
    assert body == "# Meine Idee\n\nEine kurze Zusammenfassung.\n"


def test_render_default_with_related(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "obsidian_vault_path", str(tmp_path))
    body = render_note_body(_result(related=["Alte Notiz"]))
    assert body == (
        "# Meine Idee\n\nEine kurze Zusammenfassung."
        "\n\n## Related\n- [[Alte Notiz]]\n"
    )


def test_render_custom_template_all_placeholders(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "obsidian_vault_path", str(tmp_path))
    _write_template(
        tmp_path,
        "## {{title}}\n\n> {{date}} · {{category}} · {{tags}}\n\n{{summary}}{{related}}\n",
    )
    body = render_note_body(_result(related=["Andere"]))
    today = date.today().isoformat()
    assert f"> {today} · idea · #fitness #app" in body
    assert body.startswith("## Meine Idee\n")
    assert "## Related\n- [[Andere]]" in body
    assert body.endswith("\n") and not body.endswith("\n\n")


def test_render_empty_placeholders_render_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "obsidian_vault_path", str(tmp_path))
    _write_template(tmp_path, "{{summary}}\n\nTags: {{tags}}{{related}}\n")
    body = render_note_body(_result(tags=[], related=[]))
    assert body == "Eine kurze Zusammenfassung.\n\nTags:\n"


# ─── Integration: write_note nutzt das Template ─────────────────────────────


def test_write_note_uses_custom_template_keeps_frontmatter(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "obsidian_vault_path", str(tmp_path))
    monkeypatch.setattr(settings, "vault_backend", "filesystem")
    _write_template(tmp_path, "## {{title}}\n\n{{summary}}\n\n{{tags}}\n")

    path = write_note(_result())
    content = path.read_text(encoding="utf-8")

    # Frontmatter bleibt fix (E26-2 Leitplanke).
    assert content.startswith("---\ntitle: Meine Idee\ncategory: idea\ncreated: ")
    assert "tags: [fitness, app]" in content
    # Body kommt aus dem Template.
    assert "## Meine Idee\n\nEine kurze Zusammenfassung.\n\n#fitness #app\n" in content


def test_write_note_output_unchanged_without_template(tmp_path, monkeypatch):
    """Format-Regression: ohne Template-Datei bleibt das Layout byte-identisch."""
    monkeypatch.setattr(settings, "obsidian_vault_path", str(tmp_path))
    monkeypatch.setattr(settings, "vault_backend", "filesystem")

    path = write_note(_result())
    content = path.read_text(encoding="utf-8")

    expected = (
        "---\n"
        "title: Meine Idee\n"
        "category: idea\n"
        f"created: {date.today().isoformat()}\n"
        "tags: [fitness, app]\n"
        "---\n\n"
        "# Meine Idee\n\n"
        "Eine kurze Zusammenfassung.\n"
    )
    assert content == expected


# ─── Index klammert _seiton/ aus ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_index_sync_skips_seiton_folder(tmp_path, monkeypatch):
    from app.vault.index import sync_vault_index_from_disk

    monkeypatch.setattr(settings, "obsidian_vault_path", str(tmp_path))
    (tmp_path / "Notes").mkdir()
    (tmp_path / "Notes" / "Hello.md").write_text(
        "---\ntitle: Hello\n---\n\nBody.", encoding="utf-8"
    )
    _write_template(tmp_path, "# {{title}}\n\n{{summary}}\n")

    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.flush = AsyncMock()
    db.execute = AsyncMock(
        return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None))
    )

    count = await sync_vault_index_from_disk(db)
    assert count == 1  # nur Notes/Hello.md — _seiton/templates/note.md ignoriert
