"""Tests fuer SECURITY.md (E11-2)."""

from pathlib import Path

SECURITY = Path("SECURITY.md")


def test_security_md_exists():
    assert SECURITY.is_file()


def test_security_md_covers_reporting_and_threat_model():
    text = SECURITY.read_text(encoding="utf-8")
    for needle in (
        "Reporting a vulnerability",
        "Threat model",
        "TELEGRAM_ALLOWED_USER_IDS",
        "SEITON_API_KEY",
        "localhost",
        "security/advisories",
        "Dependabot",
        "CodeQL",
    ):
        assert needle in text, f"missing in SECURITY.md: {needle}"
