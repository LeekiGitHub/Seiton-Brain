"""Doc-Contract für E47 UI-Inventar und Referenz-STOP (E47-1/2)."""

from pathlib import Path

INVENTORY = Path("docs/ui-inventory.md")
REFERENCE_REQUEST = Path("docs/ui-reference-request.md")


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
    ):
        assert needle in text, f"missing in ui-inventory.md: {needle}"


def test_ui_reference_request_is_stop_gate():
    text = REFERENCE_REQUEST.read_text(encoding="utf-8")
    assert REFERENCE_REQUEST.is_file()
    for needle in (
        "STOP",
        "E47-2",
        "Bereich 1",
        "Bereich 6",
        "design-system.md",
        "Deine Referenzen",
        "noch offen",
    ):
        assert needle in text, f"missing in ui-reference-request.md: {needle}"
