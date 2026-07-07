"""Tests fuer Offline-Lizenzierung (E21-1)."""

from datetime import date, timedelta
from unittest.mock import patch

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from fastapi.testclient import TestClient

from app.licensing.keys import load_public_key
from app.licensing.schemas import LicensePayload
from app.licensing.startup import check_current_license, enforce_license_if_required
from app.licensing.validate import build_license_key, parse_license_key, verify_license_key
from app.main import app

client = TestClient(app)


@pytest.fixture
def keypair():
    private_key = Ed25519PrivateKey.generate()
    return private_key, private_key.public_key()


def _sample_payload(**overrides) -> LicensePayload:
    base = dict(
        edition="consumer",
        licensee="buyer@example.com",
        issued=date.today(),
        expires=None,
        features=["ui", "updates"],
    )
    base.update(overrides)
    return LicensePayload(**base)


def test_build_and_verify_roundtrip(keypair):
    private_key, public_key = keypair
    payload = _sample_payload()
    license_key = build_license_key(payload, private_key)
    assert license_key.startswith("SEITON1.")
    info = verify_license_key(license_key, public_key=public_key)
    assert info.valid is True
    assert info.edition == "consumer"
    assert info.licensee == "buyer@example.com"
    assert info.features == ["ui", "updates"]


def test_verify_rejects_tampered_payload(keypair):
    private_key, public_key = keypair
    license_key = build_license_key(_sample_payload(), private_key)
    parts = license_key.split(".")
    parts[1] = parts[1][:-2] + "XX"
    tampered = ".".join(parts)
    info = verify_license_key(tampered, public_key=public_key)
    assert info.valid is False
    assert "Signatur" in info.message


def test_verify_rejects_expired_license(keypair):
    private_key, public_key = keypair
    yesterday = date.today() - timedelta(days=1)
    license_key = build_license_key(
        _sample_payload(issued=yesterday - timedelta(days=30), expires=yesterday),
        private_key,
    )
    info = verify_license_key(license_key, public_key=public_key, today=date.today())
    assert info.valid is False
    assert info.message == "Lizenz abgelaufen"


def test_parse_license_key_invalid_format():
    with pytest.raises(ValueError, match="Ungültiges Lizenzformat"):
        parse_license_key("INVALID")


def test_load_public_key_from_repo():
    key = load_public_key()
    assert isinstance(key, Ed25519PublicKey)


def test_enforce_skipped_when_not_required(monkeypatch):
    monkeypatch.setattr("app.licensing.startup.settings.seiton_license_required", False)
    enforce_license_if_required()


def test_enforce_exits_when_required_and_invalid(monkeypatch):
    monkeypatch.setattr("app.licensing.startup.settings.seiton_license_required", True)
    monkeypatch.setattr("app.licensing.startup.settings.seiton_license_key", "")
    with pytest.raises(SystemExit) as exc:
        enforce_license_if_required()
    assert exc.value.code == 1


def test_check_current_license_empty(monkeypatch):
    monkeypatch.setattr("app.licensing.startup.settings.seiton_license_key", "")
    info = check_current_license()
    assert info.valid is False


def test_license_status_api():
    response = client.get("/api/ui/license")
    assert response.status_code == 200
    data = response.json()
    assert data["required"] is False
    assert data["valid"] is False
    assert "Keine Lizenz" in data["message"]


@patch("app.ui.router.save_license")
def test_license_save_api(mock_save):
    from app.setup.schemas import SetupSaveResponse

    mock_save.return_value = SetupSaveResponse(
        saved=True,
        env_file="/tmp/.env",
        restart_required=True,
        message="OK",
    )
    response = client.post(
        "/api/ui/license",
        json={"license_key": "SEITON1.eyJ0ZXN0IjoidHJ1ZSJ9.invalid"},
    )
    assert response.status_code == 200
    mock_save.assert_called_once()


def test_license_save_api_rejects_invalid():
    response = client.post(
        "/api/ui/license",
        json={"license_key": "not-a-license"},
    )
    assert response.status_code == 400


def test_issue_license_script_generates_valid_key(keypair, tmp_path):
    private_key, public_key = keypair
    pem = tmp_path / "signing.pem"
    from cryptography.hazmat.primitives import serialization

    pem.write_bytes(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    payload = _sample_payload()
    license_key = build_license_key(payload, private_key)
    info = verify_license_key(license_key, public_key=public_key)
    assert info.valid is True
