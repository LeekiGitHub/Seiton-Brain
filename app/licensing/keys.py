"""Oeffentlicher Schluessel fuer Lizenzpruefung."""

from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

_DEFAULT_PUBLIC_KEY = Path(__file__).resolve().parent / "public_key.pem"


def load_public_key(path: Path | None = None) -> Ed25519PublicKey:
    pem_path = path or _DEFAULT_PUBLIC_KEY
    data = pem_path.read_bytes()
    key = serialization.load_pem_public_key(data)
    if not isinstance(key, Ed25519PublicKey):
        raise TypeError("Expected Ed25519 public key")
    return key
