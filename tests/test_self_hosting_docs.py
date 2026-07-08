"""Tests fuer Self-Hosting-Doku (E9-2)."""

from pathlib import Path

SELF_HOSTING = Path("docs/self-hosting.md")


def test_self_hosting_doc_exists():
    assert SELF_HOSTING.is_file()


def test_self_hosting_covers_platforms_and_compose_modes():
    text = SELF_HOSTING.read_text(encoding="utf-8")
    for needle in (
        "macOS",
        "Windows",
        "Linux",
        "VPS",
        "docker-compose.consumer.yml",
        "docker-compose.vps.yml",
        "packaging.md",
        "vps-deployment.md",
        "install.sh",
        "install.ps1",
    ):
        assert needle in text, f"missing in self-hosting.md: {needle}"
