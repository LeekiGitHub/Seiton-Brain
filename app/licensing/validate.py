"""Lizenzschlüssel parsen und offline pruefen (E21-1)."""

from __future__ import annotations

import base64
import json
from datetime import UTC, date, datetime

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from app.licensing.keys import load_public_key
from app.licensing.schemas import LicenseInfo, LicensePayload

LICENSE_PREFIX = "SEITON1"


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def parse_license_key(key: str) -> tuple[str, bytes, bytes]:
    """Liefert (payload_b64, payload_bytes, signature)."""
    parts = key.strip().split(".")
    if len(parts) != 3 or parts[0] != LICENSE_PREFIX:
        raise ValueError("Ungültiges Lizenzformat")
    payload_b64, sig_b64 = parts[1], parts[2]
    if not payload_b64 or not sig_b64:
        raise ValueError("Ungültiges Lizenzformat")
    return payload_b64, _b64url_decode(payload_b64), _b64url_decode(sig_b64)


def verify_license_key(
    key: str,
    *,
    public_key: Ed25519PublicKey | None = None,
    today: date | None = None,
) -> LicenseInfo:
    """Prueft Signatur und Gueltigkeit — komplett offline."""
    stripped = key.strip()
    if not stripped:
        return LicenseInfo(valid=False, message="Kein Lizenzschlüssel")

    try:
        payload_b64, payload_bytes, signature = parse_license_key(stripped)
        verifier = public_key or load_public_key()
        verifier.verify(signature, payload_b64.encode("ascii"))
        raw = json.loads(payload_bytes.decode("utf-8"))
        payload = LicensePayload.model_validate(raw)
    except InvalidSignature:
        return LicenseInfo(valid=False, message="Ungültige Signatur")
    except (ValueError, json.JSONDecodeError, TypeError) as exc:
        return LicenseInfo(valid=False, message=f"Ungültiger Schlüssel: {exc}")

    check_date = today or datetime.now(UTC).date()
    if payload.expires is not None and check_date > payload.expires:
        return LicenseInfo(
            valid=False,
            edition=payload.edition,
            licensee=payload.licensee,
            issued=payload.issued,
            expires=payload.expires,
            features=payload.features,
            message="Lizenz abgelaufen",
        )

    return LicenseInfo(
        valid=True,
        edition=payload.edition,
        licensee=payload.licensee,
        issued=payload.issued,
        expires=payload.expires,
        features=payload.features,
        message="Lizenz gültig",
    )


def build_license_key(payload: LicensePayload, private_key) -> str:
    """Erstellt einen signierten Lizenzschlüssel (nur fuer Issuer-Tool)."""
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    if not isinstance(private_key, Ed25519PrivateKey):
        raise TypeError("Expected Ed25519 private key")
    payload_json = payload.model_dump_json()
    payload_b64 = _b64url_encode(payload_json.encode("utf-8"))
    signature = private_key.sign(payload_b64.encode("ascii"))
    sig_b64 = _b64url_encode(signature)
    return f"{LICENSE_PREFIX}.{payload_b64}.{sig_b64}"
