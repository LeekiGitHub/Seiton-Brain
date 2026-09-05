"""Tests for CONTRIBUTING and GitHub templates (E11-3)."""

from pathlib import Path

CONTRIBUTING = Path("CONTRIBUTING.md")
ISSUE_DIR = Path(".github/ISSUE_TEMPLATE")
PR_TEMPLATE = Path(".github/pull_request_template.md")


def test_contributing_md_exists():
    assert CONTRIBUTING.is_file()


def test_contributing_covers_workflow():
    text = CONTRIBUTING.read_text(encoding="utf-8")
    for needle in (
        "pull requests",
        "pytest",
        "ruff check",
        "CHANGELOG.md",
        "ROADMAP.md",
        "worker_session",
        "SECURITY.md",
        "short-lived",
        "protected",
        "Definition of Done",
        "Mini-Handcheck",
        "E45-14",
    ):
        assert needle in text, f"missing in CONTRIBUTING.md: {needle}"


def test_github_issue_templates_exist():
    assert (ISSUE_DIR / "bug_report.yml").is_file()
    assert (ISSUE_DIR / "feature_request.yml").is_file()
    assert (ISSUE_DIR / "config.yml").is_file()


def test_github_pr_template_exists():
    text = PR_TEMPLATE.read_text(encoding="utf-8")
    assert "Test plan" in text
    assert "CHANGELOG" in text
    assert "Change type" in text
    assert "Mini-Handcheck" in text
    assert "E45-14" in text


def test_engineering_dod_is_binding():
    text = Path("docs/engineering.md").read_text(encoding="utf-8")
    assert "Definition of Done — risikobasiert (E45-14)" in text
    assert "verbindlich" in text
    assert "Mini-Handcheck" in text
    roadmap = Path("ROADMAP.md").read_text(encoding="utf-8")
    assert "| E45-14 |" in roadmap and "🟢" in roadmap
    assert "docs/engineering.md" in roadmap
