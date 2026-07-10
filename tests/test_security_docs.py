"""Tests fuer SECURITY.md (E11-2)."""

from pathlib import Path

SECURITY = Path("SECURITY.md")


def test_security_md_exists():
    assert SECURITY.is_file()


def test_security_md_covers_reporting_and_threat_model():
    text = SECURITY.read_text(encoding="utf-8")
    for needle in (
        "Schwachstellen melden",
        "Threat Model",
        "TELEGRAM_ALLOWED_USER_IDS",
        "SEITON_API_KEY",
        "localhost",
        "security/advisories",
    ):
        assert needle in text, f"missing in SECURITY.md: {needle}"
