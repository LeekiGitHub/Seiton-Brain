"""Tests for the proxy-safe localhost guard (E27-1).

Behind a local reverse proxy the peer IP is always 127.0.0.1 —
so the guard must evaluate Forwarded headers fail-closed.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.setup.security import is_localhost_host
from app.ui import auth

client = TestClient(app)

REMOTE_XFF = {"X-Forwarded-For": "203.0.113.7"}


@pytest.fixture(autouse=True)
def _auth_disabled(monkeypatch):
    monkeypatch.setattr(settings, "ui_password", "")


# --- Host-Normalisierung ------------------------------------------------------


def test_is_localhost_host_variants():
    assert is_localhost_host("127.0.0.1")
    assert is_localhost_host("::1")
    assert is_localhost_host("LOCALHOST")
    assert is_localhost_host("127.0.0.1:8080")
    assert is_localhost_host("[::1]:4711")
    assert is_localhost_host('"[::1]"')


def test_is_localhost_host_rejects_remote():
    assert not is_localhost_host("203.0.113.7")
    assert not is_localhost_host("203.0.113.7:80")
    assert not is_localhost_host("unknown")
    assert not is_localhost_host("")
    assert not is_localhost_host("2001:db8::1")


# --- Setup-Endpunkte ----------------------------------------------------------


def test_setup_status_allows_direct_localhost():
    assert client.get("/api/setup/status").status_code == 200


def test_setup_status_blocks_forwarded_remote():
    response = client.get("/api/setup/status", headers=REMOTE_XFF)
    assert response.status_code == 403


def test_setup_page_blocks_forwarded_remote():
    response = client.get("/setup", headers=REMOTE_XFF)
    assert response.status_code == 403


def test_setup_blocks_spoofed_xff_chain():
    # nginx haengt die echte Client-IP an: "gespooft, echt" → ablehnen.
    headers = {"X-Forwarded-For": "127.0.0.1, 203.0.113.7"}
    assert client.get("/api/setup/status", headers=headers).status_code == 403


def test_setup_allows_local_via_local_proxy():
    # Local access via local proxy: all hops are localhost.
    headers = {"X-Forwarded-For": "127.0.0.1"}
    assert client.get("/api/setup/status", headers=headers).status_code == 200


def test_setup_blocks_x_real_ip_remote():
    headers = {"X-Real-IP": "203.0.113.7"}
    assert client.get("/api/setup/status", headers=headers).status_code == 403


def test_setup_blocks_forwarded_header_remote():
    headers = {"Forwarded": "for=203.0.113.7;proto=https"}
    assert client.get("/api/setup/status", headers=headers).status_code == 403


def test_setup_allows_forwarded_header_localhost():
    headers = {"Forwarded": 'for="[::1]:4711";proto=https'}
    assert client.get("/api/setup/status", headers=headers).status_code == 200


def test_setup_blocks_unparseable_forwarded_header():
    # Fail-closed: Forwarded without a parseable for= is not verifiable.
    headers = {"Forwarded": "proto=https"}
    assert client.get("/api/setup/status", headers=headers).status_code == 403


# --- UI pages (without UI password: localhost-only) --------------------------


def test_ui_page_blocks_forwarded_remote_without_password():
    response = client.get("/dashboard", headers=REMOTE_XFF, follow_redirects=False)
    assert response.status_code == 403


def test_ui_api_blocks_forwarded_remote_without_password():
    assert client.get("/api/ui/settings", headers=REMOTE_XFF).status_code == 403


def test_ui_page_with_session_allows_forwarded_remote(monkeypatch):
    # Mit UI_PASSWORD + Session bleibt Remote-Zugriff hinter TLS-Proxy moeglich.
    monkeypatch.setattr(settings, "ui_password", "korrekt-pferd-batterie")
    cookies = {auth.SESSION_COOKIE: auth.create_session_token()}
    response = client.get(
        "/dashboard", headers=REMOTE_XFF, cookies=cookies, follow_redirects=False
    )
    assert response.status_code == 200


# --- OpenAPI-Guard ------------------------------------------------------------


@patch("app.main.is_openapi_enabled", return_value=True)
def test_openapi_blocks_forwarded_remote(_mock):
    assert client.get("/docs", headers=REMOTE_XFF).status_code == 403


@patch("app.main.is_openapi_enabled", return_value=True)
def test_openapi_allows_direct_localhost(_mock):
    assert client.get("/docs").status_code == 200


# --- Deploy examples block setup/docs (defense in depth) ---------------------


def test_deploy_examples_block_setup_and_docs():
    from pathlib import Path

    caddy = Path("deploy/Caddyfile.example").read_text(encoding="utf-8")
    assert "/setup*" in caddy and "/api/setup/*" in caddy
    assert "respond @blocked 403" in caddy

    nginx = Path("deploy/nginx-seiton.conf.example").read_text(encoding="utf-8")
    assert "^/(setup|api/setup|docs|redoc|openapi\\.json)" in nginx
    assert "return 403" in nginx
