"""E45-15: one browser happy-path smoke (opt-in).

Not part of the default suite — needs Chromium binaries and a short-lived
uvicorn process. Stub empty UI API payloads so the PoC does not require
Postgres/Redis; the goal is shell + CSS + JS + console hygiene, not full
data E2E.

Run::

    playwright install chromium
    SEITON_VISUAL=1 pytest -m visual tests/test_visual_smoke.py
"""

from __future__ import annotations

import json
import os
import socket
import threading
import time
import urllib.error
import urllib.request
from collections.abc import Generator
from datetime import UTC, datetime
from pathlib import Path

import pytest
from playwright.sync_api import Page, Route, expect

pytestmark = [
    pytest.mark.visual,
    pytest.mark.skipif(
        os.environ.get("SEITON_VISUAL") != "1",
        reason="opt-in: SEITON_VISUAL=1 pytest -m visual tests/test_visual_smoke.py",
    ),
]

SCREENSHOT_DIR = Path(__file__).resolve().parents[1] / "docs" / "ui-screenshots"

# Empty / minimal JSON for DB-backed UI APIs so pages render without Postgres.
_DASHBOARD = {
    "stats": {
        "total_entries": 1,
        "entries_by_status": {"processed": 1},
        "entries_by_kind": {"text": 1, "voice": 0},
        "vault_notes_indexed": 1,
        "embeddings_enabled": False,
    },
    "recent_entries": [
        {
            "id": 1,
            "title": "Visual smoke sample",
            "category": "idea",
            "summary": "PoC fixture",
            "vault_path": "Ideas/Visual-smoke.md",
            "kind": "text",
            "status": "processed",
            "created_at": datetime(2026, 9, 4, 12, 0, tzinfo=UTC).isoformat(),
        }
    ],
    "recent_vault_notes": [
        {
            "title": "Visual smoke sample",
            "vault_path": "Ideas/Visual-smoke.md",
            "folder": "Ideas",
            "category": "idea",
            "mtime": datetime(2026, 9, 4, 12, 0, tzinfo=UTC).isoformat(),
        }
    ],
}
_NOTES = {
    "items": [
        {
            "title": "Visual smoke sample",
            "vault_path": "Ideas/Visual-smoke.md",
            "folder": "Ideas",
            "category": "idea",
            "mtime": datetime(2026, 9, 4, 12, 0, tzinfo=UTC).isoformat(),
        }
    ],
    "limit": 50,
    "offset": 0,
}
_NOTE_CONTENT = {
    "vault_path": "Ideas/Visual-smoke.md",
    "title": "Visual smoke sample",
    "content": "# Visual smoke sample\n\nFixture note for E45-15.\n",
}
_VAULT_CONFIG = {"vault_path": "/tmp/seiton-test-vault", "categories": {"idea": "Ideas"}}
_SEARCH = {"query": "smoke", "items": [], "limit": 15, "semantic": False}


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_http(url: str, timeout_s: float = 15.0) -> None:
    deadline = time.monotonic() + timeout_s
    last_err: Exception | None = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=0.5) as resp:
                if resp.status < 500:
                    return
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_err = exc
            time.sleep(0.1)
    raise RuntimeError(f"server not ready at {url}: {last_err}")


@pytest.fixture(scope="module")
def live_server() -> Generator[str, None, None]:
    import uvicorn

    from app.main import app

    port = _free_port()
    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=port,
        log_level="warning",
        access_log=False,
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, name="e45-15-uvicorn", daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"
    try:
        _wait_http(f"{base}/dashboard")
        yield base
    finally:
        server.should_exit = True
        thread.join(timeout=5)


@pytest.fixture
def screenshot_dir() -> Path:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    return SCREENSHOT_DIR


@pytest.fixture
def stub_ui_data_apis(page: Page) -> Generator[None, None, None]:
    """Stub DB-backed UI JSON so shells render without Postgres."""

    def fulfill(route: Route, body: object, status: int = 200) -> None:
        route.fulfill(
            status=status,
            content_type="application/json",
            body=json.dumps(body),
        )

    def handler(route: Route) -> None:
        path = route.request.url.split("?", 1)[0]
        method = route.request.method.upper()
        if path.endswith("/api/ui/dashboard") and method == "GET":
            fulfill(route, _DASHBOARD)
            return
        if path.endswith("/api/ui/notes") and method == "GET":
            fulfill(route, _NOTES)
            return
        if "/api/ui/notes/content" in path and method == "GET":
            fulfill(route, _NOTE_CONTENT)
            return
        if path.endswith("/api/ui/vault-config") and method == "GET":
            fulfill(route, _VAULT_CONFIG)
            return
        if "/api/ui/search" in path and method == "GET":
            fulfill(route, _SEARCH)
            return
        route.continue_()

    page.route("**/api/ui/**", handler)
    yield
    page.unroute("**/api/ui/**")


@pytest.fixture
def console_errors(page: Page) -> Generator[list[str], None, None]:
    errors: list[str] = []

    def on_console(msg) -> None:
        if msg.type == "error":
            # Service worker / offline noise is out of scope for shell smoke.
            text = msg.text
            if "sw.js" in text or "Service Worker" in text:
                return
            errors.append(text)

    def on_page_error(exc) -> None:
        errors.append(f"pageerror: {exc}")

    page.on("console", on_console)
    page.on("pageerror", on_page_error)
    yield errors


def _shot(page: Page, directory: Path, name: str) -> None:
    page.screenshot(path=str(directory / f"{name}.png"), full_page=True)


def test_ui_shell_happy_path(
    page: Page,
    live_server: str,
    screenshot_dir: Path,
    stub_ui_data_apis: None,
    console_errors: list[str],
) -> None:
    """One path: setup → main shells → mobile dashboard; screenshots + console."""
    page.set_viewport_size({"width": 1280, "height": 800})

    page.goto(f"{live_server}/setup", wait_until="networkidle")
    expect(page.locator("h1")).to_contain_text("Setup")
    # Incomplete wizard: #btn-start. Completed: done panel with #btn-edit-setup.
    # Avoid `#a, #b`.first — that picks the first in DOM even when hidden.
    start = page.locator("#btn-start")
    edit = page.locator("#btn-edit-setup")
    assert start.is_visible() or edit.is_visible(), "expected setup start or edit control"
    _shot(page, screenshot_dir, "01-setup")

    page.goto(f"{live_server}/dashboard", wait_until="networkidle")
    expect(page.locator("nav.topnav .brand")).to_contain_text("Seiton Brain")
    expect(page.locator("#stat-total")).to_have_text("1")
    expect(page.locator("#entries-table-wrap")).to_contain_text("Visual smoke sample")
    _shot(page, screenshot_dir, "02-dashboard")

    page.goto(f"{live_server}/ask", wait_until="networkidle")
    expect(page.locator("h1")).to_be_visible()
    expect(page.locator("#search-form, #ask-form, form").first).to_be_visible()
    _shot(page, screenshot_dir, "03-ask")

    page.goto(f"{live_server}/notes", wait_until="networkidle")
    expect(page.locator("nav.topnav a[href='/notes']")).to_be_visible()
    _shot(page, screenshot_dir, "04-notes")

    page.goto(f"{live_server}/settings", wait_until="networkidle")
    expect(page.locator("h1")).to_contain_text("Einstellung")
    _shot(page, screenshot_dir, "05-settings")

    page.set_viewport_size({"width": 375, "height": 812})
    page.goto(f"{live_server}/dashboard", wait_until="networkidle")
    expect(page.locator("#capture-form")).to_be_visible()
    _shot(page, screenshot_dir, "07-dashboard-mobile")

    assert not console_errors, f"browser console errors: {console_errors}"
