"""UI-Auth (E23-1): optionales Passwort + signierte Session-Cookies.

Ohne ``UI_PASSWORD`` bleibt alles beim Status quo (localhost-Guard).
Mit Passwort gilt Login-Pflicht für UI-Seiten und ``/api/ui/*`` — damit wird
Remote-/Mobile-Zugriff möglich (hinter TLS-Proxy, siehe
``docs/remote-access.md``).

Sessions sind zustandslos: ``<expiry>.<hmac>``-Cookies, signiert mit einem
aus dem Passwort abgeleiteten Schlüssel. Passwortwechsel invalidiert damit
automatisch alle Sessions; es gibt nichts in der DB zu persistieren.
"""

from __future__ import annotations

import hashlib
import hmac
import time

from app.config import settings

SESSION_COOKIE = "seiton_ui_session"
SESSION_TTL_SECONDS = 7 * 24 * 3600

# Brute-Force-Bremse: nach N Fehlversuchen pro Client-IP kurz sperren.
# In-Memory reicht — Single-User-System, ein API-Prozess.
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_SECONDS = 60

_failed_attempts: dict[str, list[float]] = {}


def ui_auth_enabled() -> bool:
    return bool(settings.ui_password)


def _session_key() -> bytes:
    return hashlib.sha256(
        ("seiton-ui-session:" + settings.ui_password).encode()
    ).digest()


def _sign(payload: str) -> str:
    return hmac.new(_session_key(), payload.encode(), hashlib.sha256).hexdigest()


def create_session_token(now: float | None = None) -> str:
    expires = int((now if now is not None else time.time()) + SESSION_TTL_SECONDS)
    return f"{expires}.{_sign(str(expires))}"


def verify_session_token(token: str, now: float | None = None) -> bool:
    if not ui_auth_enabled() or not token or "." not in token:
        return False
    expires_raw, signature = token.rsplit(".", 1)
    try:
        expires = int(expires_raw)
    except ValueError:
        return False
    if not hmac.compare_digest(signature, _sign(expires_raw)):
        return False
    return (now if now is not None else time.time()) < expires


def verify_password(candidate: str) -> bool:
    return ui_auth_enabled() and hmac.compare_digest(
        candidate.encode(), settings.ui_password.encode()
    )


def lockout_remaining(host: str, now: float | None = None) -> int:
    """Sekunden bis zum nächsten erlaubten Versuch, 0 = nicht gesperrt."""
    current = now if now is not None else time.time()
    attempts = [
        t for t in _failed_attempts.get(host, []) if current - t < LOCKOUT_SECONDS
    ]
    _failed_attempts[host] = attempts
    if len(attempts) < MAX_FAILED_ATTEMPTS:
        return 0
    return max(1, int(LOCKOUT_SECONDS - (current - attempts[0])))


def register_failed_attempt(host: str, now: float | None = None) -> None:
    current = now if now is not None else time.time()
    _failed_attempts.setdefault(host, []).append(current)


def clear_failed_attempts(host: str) -> None:
    _failed_attempts.pop(host, None)


def reset_lockouts() -> None:
    """Test-Hilfe."""
    _failed_attempts.clear()
