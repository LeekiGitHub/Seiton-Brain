"""Tests fuer Vault-Doku (E15-2)."""

from pathlib import Path

VAULT_DOC = Path("docs/vault.md")


def test_vault_doc_exists():
    assert VAULT_DOC.is_file()


def test_vault_doc_obsidian_optional():
    text = VAULT_DOC.read_text(encoding="utf-8")
    for needle in (
        "Obsidian optional",
        "vault.example",
        "OBSIDIAN_VAULT_HOST_PATH",
        "vault_config",
        "Markdown",
        "/notes",
    ):
        assert needle in text, f"missing in vault.md: {needle}"
