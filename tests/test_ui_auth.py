"""Tests fuer UI-Auth (E23-1): Passwort-Login + Session-Cookies."""

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.ui import auth

client = TestClient(app)

PASSWORD = "korrekt-pferd-batterie"


@pytest.fixture(autouse=True)
def _clean_lockouts():
    auth.reset_lockouts()
    yield
    auth.reset_lockouts()


@pytest.fixture
def auth_enabled(monkeypatch):
    monkeypatch.setattr(settings, "ui_password", PASSWORD)


# --- Token-Logik -------------------------------------------------------------


def test_token_roundtrip(auth_enabled):
    token = auth.create_session_token()
    assert auth.verify_session_token(token) is True


def test_token_expiry(auth_enabled):
    token = auth.create_session_token(now=1000.0)
    assert auth.verify_session_token(token, now=1000.0 + auth.SESSION_TTL_SECONDS - 1)
    assert not auth.verify_session_token(token, now=1000.0 + auth.SESSION_TTL_SECONDS + 1)


def test_token_tamper_rejected(auth_enabled):
    token = auth.create_session_token()
    expires, sig = token.rsplit(".", 1)
    assert not auth.verify_session_token(f"{int(expires) + 9999}.{sig}")
    assert not auth.verify_session_token("garbage")
    assert not auth.verify_session_token("")


def test_password_change_invalidates_sessions(auth_enabled, monkeypatch):
    token = auth.create_session_token()
    monkeypatch.setattr(settings, "ui_password", "neues-passwort")
    assert not auth.verify_session_token(token)


def test_tokens_invalid_when_auth_disabled(auth_enabled, monkeypatch):
    token = auth.create_session_token()
    monkeypatch.setattr(settings, "ui_password", "")
    assert not auth.verify_session_token(token)


# --- Guards ------------------------------------------------------------------


def test_pages_redirect_to_login_without_session(auth_enabled):
    response = client.get("/dashboard", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_api_returns_401_without_session(auth_enabled):
    response = client.get("/api/ui/dashboard")
    assert response.status_code == 401


def test_login_page_reachable_without_session(auth_enabled):
    response = client.get("/login")
    assert response.status_code == 200
    assert "Anmelden" in response.text


def test_login_page_redirects_when_auth_disabled():
    response = client.get("/login", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/dashboard"


def test_setup_stays_localhost_only(auth_enabled):
    # TestClient gilt als localhost — Setup bleibt ohne Session erreichbar.
    response = client.get("/setup")
    assert response.status_code == 200


# --- Login-Flow --------------------------------------------------------------


def test_login_api_disabled_returns_404():
    response = client.post("/api/ui/login", json={"password": "egal"})
    assert response.status_code == 404


def test_login_wrong_password(auth_enabled):
    response = client.post("/api/ui/login", json={"password": "falsch"})
    assert response.status_code == 401


def test_login_success_sets_cookie_and_grants_access(auth_enabled):
    response = client.post("/api/ui/login", json={"password": PASSWORD})
    assert response.status_code == 200
    assert response.json() == {"ok": True}
    token = response.cookies.get(auth.SESSION_COOKIE)
    assert token and auth.verify_session_token(token)
    set_cookie = response.headers.get("set-cookie", "").lower()
    assert "httponly" in set_cookie
    assert "secure" not in set_cookie  # Default: UI_COOKIE_SECURE=false

    page = client.get(
        "/dashboard", cookies={auth.SESSION_COOKIE: token}, follow_redirects=False
    )
    assert page.status_code == 200

    api = client.get("/api/ui/settings", cookies={auth.SESSION_COOKIE: token})
    assert api.status_code == 200


def test_login_sets_secure_cookie_when_configured(auth_enabled, monkeypatch):
    monkeypatch.setattr(settings, "ui_cookie_secure", True)
    response = client.post("/api/ui/login", json={"password": PASSWORD})
    assert response.status_code == 200
    set_cookie = response.headers.get("set-cookie", "").lower()
    assert "secure" in set_cookie


def test_login_lockout_after_failed_attempts(auth_enabled):
    for _ in range(auth.MAX_FAILED_ATTEMPTS):
        response = client.post("/api/ui/login", json={"password": "falsch"})
        assert response.status_code == 401
    locked = client.post("/api/ui/login", json={"password": PASSWORD})
    assert locked.status_code == 429
    assert "Fehlversuche" in locked.json()["detail"]


def test_logout_clears_cookie(auth_enabled):
    login = client.post("/api/ui/login", json={"password": PASSWORD})
    token = login.cookies.get(auth.SESSION_COOKIE)
    response = client.post(
        "/logout", cookies={auth.SESSION_COOKIE: token}, follow_redirects=False
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/login"
    set_cookie = response.headers.get("set-cookie", "")
    assert auth.SESSION_COOKIE in set_cookie and "Max-Age=0" in set_cookie


def test_logout_get_does_not_clear_cookie(auth_enabled):
    """GET /logout darf die Session nicht mehr invalidieren (E27-3 CSRF)."""
    login = client.post("/api/ui/login", json={"password": PASSWORD})
    token = login.cookies.get(auth.SESSION_COOKIE)
    response = client.get(
        "/logout", cookies={auth.SESSION_COOKIE: token}, follow_redirects=False
    )
    assert response.status_code == 302
    assert response.headers["location"] == "/login"
    set_cookie = response.headers.get("set-cookie", "")
    assert "Max-Age=0" not in set_cookie


def test_logout_link_rendered_when_auth_enabled(auth_enabled):
    token = auth.create_session_token()
    page = client.get("/dashboard", cookies={auth.SESSION_COOKIE: token})
    assert 'action="/logout"' in page.text
    assert "Abmelden" in page.text


def test_no_logout_link_when_auth_disabled():
    page = client.get("/dashboard")
    assert "Abmelden" not in page.text
    assert 'action="/logout"' not in page.text
