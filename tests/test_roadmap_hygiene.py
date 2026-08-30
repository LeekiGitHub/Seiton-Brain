"""E45-13: Roadmap-/Agent-Kontext-Hygiene — Archiv und Kurzstand existieren."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_current_state_exists_and_points_to_roadmap():
    path = ROOT / "docs" / "current-state.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "ROADMAP.md" in text
    assert "archive/roadmap-phases-a-h.md" in text


def test_archive_phases_a_h_preserves_epics():
    path = ROOT / "docs" / "archive" / "roadmap-phases-a-h.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    for epic in ("### E1 —", "### E19 —", "### E26 —"):
        assert epic in text, f"missing archived epic heading: {epic}"
    assert "Sprint Phase H" in text or "Phase H" in text


def test_roadmap_is_compact_and_links_archive():
    path = ROOT / "ROADMAP.md"
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    assert len(lines) <= 400, f"active ROADMAP too long: {len(lines)} lines"
    assert "docs/archive/roadmap-phases-a-h.md" in text
    assert "docs/current-state.md" in text
    assert "E45-13" in text
    # Done hygiene story should be marked done
    assert "| E45-13 |" in text and "🟢" in text
    # Historical epic dumps should not live in the active file
    assert "### E1 —" not in text
    assert "### E19 —" not in text


def test_engineering_docs_branch_protection():
    text = (ROOT / "docs" / "engineering.md").read_text(encoding="utf-8")
    assert "Protect main" in text
    assert "Head-Branches nach Merge" in text
    assert "lint-and-test" in text


def test_phases_m_o_detail_file_exists():
    path = ROOT / "docs" / "roadmap-phases-m-o.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "### E32 —" in text
    assert "### E44 —" in text


def test_cursor_rule_points_to_current_state():
    path = ROOT / ".cursor" / "rules" / "seiton-brain.mdc"
    text = path.read_text(encoding="utf-8")
    assert "docs/current-state.md" in text
    assert "docs/archive/roadmap-phases-a-h.md" in text
