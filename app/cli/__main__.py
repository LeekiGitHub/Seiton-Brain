"""CLI entry: ``python -m app.cli …`` / ``./scripts/seiton …`` (E16-3/E16-5)."""

from __future__ import annotations

import argparse
import sys

from app.cli.init_wizard import run_init
from app.cli.keyring_store import export_dotenv, is_keyring_available, load_secrets


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="seiton",
        description="Seiton Brain CLI — lokale Setup- und Diagnose-Hilfen.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    init_p = sub.add_parser(
        "init",
        help="Interaktiv lokale .env schreiben (kein Netzwerk-Upload).",
    )
    init_p.add_argument(
        "--env-file",
        default=".env",
        help="Ziel-.env (Default: .env im aktuellen Verzeichnis)",
    )
    init_p.add_argument(
        "--non-interactive",
        action="store_true",
        help="Ohne Prompts; Werte nur aus Flags / Defaults",
    )
    init_p.add_argument("--vault", default="", help="Vault-Pfad (Host)")
    init_p.add_argument("--openai-api-key", default="", dest="openai_api_key")
    init_p.add_argument("--telegram-bot-token", default="", dest="telegram_bot_token")
    init_p.add_argument(
        "--telegram-webhook-secret",
        default="",
        dest="telegram_webhook_secret",
    )
    init_p.add_argument(
        "--telegram-allowed-user-ids",
        default="",
        dest="telegram_allowed_user_ids",
    )
    init_p.add_argument("--seiton-api-key", default="", dest="seiton_api_key")
    init_p.add_argument(
        "--embeddings",
        choices=("true", "false", ""),
        default="",
        help="EMBEDDINGS_ENABLED setzen (true/false)",
    )
    init_p.add_argument(
        "--keyring",
        action="store_true",
        help="Secrets im OS-Keystore ablegen (E16-5; braucht keyring-Paket)",
    )
    init_p.add_argument(
        "--example",
        default=".env.example",
        help="Vorlage, falls .env fehlt",
    )

    kr_p = sub.add_parser(
        "keyring-export",
        help="Secrets aus dem OS-Keystore als Env-Zeilen ausgeben (E16-5).",
    )
    kr_p.add_argument(
        "--shell",
        action="store_true",
        help="Als `export KEY=...` fuer eval in Bash",
    )
    return parser


def run_keyring_export(args: argparse.Namespace) -> int:
    if not is_keyring_available():
        print(
            "Fehler: Paket 'keyring' fehlt — pip install -r requirements-keyring.txt",
            file=sys.stderr,
        )
        return 1
    secrets = load_secrets()
    if not secrets:
        print("# (keine Secrets im Keystore)", file=sys.stderr)
        return 0
    if args.shell:
        for key, value in secrets.items():
            escaped = value.replace("\\", "\\\\").replace('"', '\\"')
            print(f'export {key}="{escaped}"')
    else:
        sys.stdout.write(export_dotenv())
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "init":
        return run_init(args)
    if args.command == "keyring-export":
        return run_keyring_export(args)
    parser.error(f"Unbekanntes Kommando: {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
