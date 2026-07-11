"""Tests fuer CONTRIBUTING und GitHub-Templates (E11-3)."""

from pathlib import Path

CONTRIBUTING = Path("CONTRIBUTING.md")
ISSUE_DIR = Path(".github/ISSUE_TEMPLATE")
PR_TEMPLATE = Path(".github/pull_request_template.md")


def test_contributing_md_exists():
    assert CONTRIBUTING.is_file()


def test_contributing_covers_workflow():
    text = CONTRIBUTING.read_text(encoding="utf-8")
    for needle in (
        "Pull Requests",
        "pytest",
        "ruff check",
        "CHANGELOG.md",
        "ROADMAP.md",
        "worker_session",
        "SECURITY.md",
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
