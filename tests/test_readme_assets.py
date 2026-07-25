"""Smoke-Tests fuer README-Assets (E11-4)."""

from pathlib import Path

ASSETS = Path("docs/assets")
README = Path("README.md")


def test_readme_assets_exist():
    for name in ("flow.gif", "dashboard.png", "ask.png"):
        path = ASSETS / name
        assert path.is_file(), f"missing {path}"
        assert path.stat().st_size > 1000, f"too small: {path}"


def test_readme_embeds_assets():
    text = README.read_text(encoding="utf-8")
    for needle in (
        "docs/assets/flow.gif",
        "docs/assets/dashboard.png",
        "docs/assets/ask.png",
    ):
        assert needle in text, f"README missing embed: {needle}"
