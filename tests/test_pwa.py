"""Tests fuer PWA-Grundlagen (E23-2): Manifest, Icons, Service Worker."""

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

STATIC = Path("app/ui/static")


def test_manifest_file_valid():
    manifest = json.loads((STATIC / "manifest.webmanifest").read_text("utf-8"))
    assert manifest["name"] == "Seiton Brain"
    assert manifest["start_url"] == "/dashboard"
    assert manifest["scope"] == "/"
    assert manifest["display"] == "standalone"
    sizes = {icon["sizes"] for icon in manifest["icons"]}
    assert {"192x192", "512x512"} <= sizes
    assert any(icon.get("purpose") == "maskable" for icon in manifest["icons"])


def test_icon_files_exist():
    for name in (
        "icon-192.png",
        "icon-512.png",
        "icon-maskable-512.png",
        "apple-touch-icon.png",
    ):
        assert (STATIC / "icons" / name).is_file(), f"missing icon: {name}"


def test_manifest_route_served_with_mime():
    response = client.get("/manifest.webmanifest")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/manifest+json")
    assert response.json()["short_name"] == "Seiton"


def test_service_worker_served_on_root_scope():
    response = client.get("/sw.js")
    assert response.status_code == 200
    assert "javascript" in response.headers["content-type"]
    assert "addEventListener" in response.text


def test_base_template_wires_up_pwa():
    page = client.get("/dashboard")
    assert page.status_code == 200
    assert '<link rel="manifest" href="/manifest.webmanifest"' in page.text
    assert 'name="theme-color"' in page.text
    assert "serviceWorker" in page.text
    assert "apple-touch-icon" in page.text


def test_sw_does_not_cache_private_routes():
    """Der SW darf nur /ui/static/* cachen — HTML/API niemals (Auth!)."""
    sw = (STATIC / "sw.js").read_text("utf-8")
    assert '"/ui/static/"' in sw
    assert "startsWith(STATIC_PREFIX)" in sw
