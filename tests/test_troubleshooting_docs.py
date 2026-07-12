"""Tests fuer Troubleshooting-Doku (E12-3)."""

from pathlib import Path

TROUBLESHOOTING = Path("docs/troubleshooting.md")


def test_troubleshooting_doc_exists():
    assert TROUBLESHOOTING.is_file()


def test_troubleshooting_covers_key_topics():
    text = TROUBLESHOOTING.read_text(encoding="utf-8")
    for needle in (
        "doctor.sh",
        "ngrok",
        "Migration",
        "TELEGRAM_ALLOWED_USER_IDS",
        "SEITON_API_KEY",
        "poller",
        "Permission denied",
        "EMBEDDINGS_ENABLED",
    ):
        assert needle in text, f"missing in troubleshooting.md: {needle}"
