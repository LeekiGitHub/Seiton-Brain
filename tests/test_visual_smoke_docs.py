"""E45-15: visual smoke artifacts stay discoverable without running Playwright."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_visual_smoke_module_and_screenshots_documented():
    assert (ROOT / "tests" / "test_visual_smoke.py").is_file()
    shots = ROOT / "docs" / "ui-screenshots"
    assert (shots / "README.md").is_file()
    for name in (
        "01-setup.png",
        "02-dashboard.png",
        "03-ask.png",
        "04-notes.png",
        "05-settings.png",
        "07-dashboard-mobile.png",
    ):
        assert (shots / name).is_file(), f"missing screenshot {name}"
    eng = (ROOT / "docs" / "engineering.md").read_text(encoding="utf-8")
    assert "SEITON_VISUAL=1" in eng
    assert "pytest-playwright" in (ROOT / "requirements-dev.txt").read_text(
        encoding="utf-8"
    )
