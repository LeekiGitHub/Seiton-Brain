"""Tests for consumer stack eval ADR 0006 (E9-5)."""

from pathlib import Path

ADR6 = Path("docs/adr/0006-consumer-stack-no-sqlite-fork.md")
ADR4 = Path("docs/adr/0004-commercial-consumer-product.md")


def test_adr_0006_exists_and_rejects_sqlite_fork():
    assert ADR6.is_file()
    text = ADR6.read_text(encoding="utf-8")
    assert "Accepted" in text
    assert "E9-5" in text
    assert "SQLite" in text
    assert "pgvector" in text
    assert "kein" in text.lower() or "Kein" in text
    assert "eine Codebasis" in text.lower() or "Ein Stack" in text


def test_adr_0004_points_to_adr_0006():
    text = ADR4.read_text(encoding="utf-8")
    assert "0006-consumer-stack-no-sqlite-fork.md" in text
