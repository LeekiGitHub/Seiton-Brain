#!/usr/bin/env python3
"""Lizenzschlüssel ausstellen (E21-1) — nur lokal, Private Key nie ins Repo.

Beispiele:
  python scripts/issue-license.py --generate-keys
  python scripts/issue-license.py --licensee user@example.com --edition consumer
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.licensing.schemas import LicensePayload
from app.licensing.validate import build_license_key, verify_license_key

DEFAULT_PRIVATE = ROOT / "keys" / "license-signing.pem"
DEFAULT_PUBLIC = ROOT / "app" / "licensing" / "public_key.pem"


def _load_private(path: Path) -> Ed25519PrivateKey:
    key = serialization.load_pem_private_key(path.read_bytes(), password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise TypeError("Expected Ed25519 private key")
    return key


def generate_keys(private_path: Path, public_path: Path) -> None:
    private_path.parent.mkdir(parents=True, exist_ok=True)
    public_path.parent.mkdir(parents=True, exist_ok=True)
    priv = Ed25519PrivateKey.generate()
    pub = priv.public_key()
    private_path.write_bytes(
        priv.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    public_path.write_bytes(
        pub.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )
    print(f"Private Key: {private_path} (gitignored)")
    print(f"Public Key:  {public_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Seiton Brain Lizenz ausstellen")
    parser.add_argument("--generate-keys", action="store_true", help="Neues Schlüsselpaar erzeugen")
    parser.add_argument("--private-key", type=Path, default=DEFAULT_PRIVATE)
    parser.add_argument("--licensee", default="customer@example.com")
    parser.add_argument("--edition", default="consumer")
    parser.add_argument("--expires", default=None, help="YYYY-MM-DD oder leer = unbegrenzt")
    args = parser.parse_args()

    if args.generate_keys:
        generate_keys(args.private_key, DEFAULT_PUBLIC)
        return 0

    if not args.private_key.is_file():
        print(f"Fehler: Private Key fehlt: {args.private_key}", file=sys.stderr)
        print("Zuerst: python scripts/issue-license.py --generate-keys", file=sys.stderr)
        return 1

    expires = date.fromisoformat(args.expires) if args.expires else None
    payload = LicensePayload(
        edition=args.edition,
        licensee=args.licensee,
        issued=date.today(),
        expires=expires,
        features=["ui", "updates", "telegram"],
    )
    private_key = _load_private(args.private_key)
    license_key = build_license_key(payload, private_key)
    info = verify_license_key(license_key, public_key=private_key.public_key())
    if not info.valid:
        print(f"Interner Fehler: {info.message}", file=sys.stderr)
        return 1
    print(license_key)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
