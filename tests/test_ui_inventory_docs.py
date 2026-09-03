"""Doc-Contract für E47 UI-Inventar, Referenzen und Designsystem (E47-1/2/3)."""

from pathlib import Path

INVENTORY = Path("docs/ui-inventory.md")
REFERENCE_REQUEST = Path("docs/ui-reference-request.md")
DESIGN_SYSTEM = Path("docs/design-system.md")
UI_RULE = Path(".cursor/rules/ui-design-system.mdc")


def test_ui_inventory_exists_and_covers_screens():
    text = INVENTORY.read_text(encoding="utf-8")
    assert INVENTORY.is_file()
    for needle in (
        "E47-1",
        "/dashboard",
        "/ask",
        "/notes",
        "/settings",
        "/setup",
        "/login",
        "app.css",
        "setup.css",
        "--accent",
        "alert()",
        "ui-reference-request.md",
        "design-system.md",
    ):
        assert needle in text, f"missing in ui-inventory.md: {needle}"


def test_ui_reference_request_covers_six_areas():
    text = REFERENCE_REQUEST.read_text(encoding="utf-8")
    assert REFERENCE_REQUEST.is_file()
    for needle in (
        "E47-2",
        "Bereich 1",
        "Bereich 6",
        "design-system.md",
        "Deine Referenzen",
        "Input vorhanden",
    ):
        assert needle in text, f"missing in ui-reference-request.md: {needle}"


def test_design_system_exists_and_covers_core():
    text = DESIGN_SYSTEM.read_text(encoding="utf-8")
    assert DESIGN_SYSTEM.is_file()
    for needle in (
        "E47-3",
        "Design-Prinzipien",
        "--accent",
        "Sidebar",
        "Topbar",
        "Markdown",
        "Quicknote",
        "Chat-Panel",
        "Split Live-Preview",
        "Für Agents",
    ):
        assert needle in text, f"missing in design-system.md: {needle}"


def test_ui_design_system_cursor_rule_exists():
    text = UI_RULE.read_text(encoding="utf-8")
    assert UI_RULE.is_file()
    assert "design-system.md" in text
    assert "app/ui" in text or "globs: app/ui" in text
