"""CLI-Einstieg: ``python -m app.cli …`` / ``./scripts/seiton …`` (E16-3)."""

from __future__ import annotations

import argparse
import sys

from app.cli.init_wizard import run_init


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
        "--example",
        default=".env.example",
        help="Vorlage, falls .env fehlt",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "init":
        return run_init(args)
    parser.error(f"Unbekanntes Kommando: {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
