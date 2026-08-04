"""``seiton init`` — interaktiv lokale ``.env`` schreiben (E16-3).

Kein Netzwerk-Upload: nur Dateisystem. Secrets bleiben auf der Maschine.
"""

from __future__ import annotations

import argparse
import secrets
import shutil
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from app.setup.env_file import read_env_values, resolve_env_path, update_env_file
from app.setup.status import is_placeholder

PromptFn = Callable[[str], str]
PrintFn = Callable[..., None]


@dataclass(frozen=True)
class InitAnswers:
    vault_host_path: str
    openai_api_key: str
    telegram_bot_token: str
    telegram_webhook_secret: str
    telegram_allowed_user_ids: str
    seiton_api_key: str
    embeddings_enabled: bool | None


def ensure_env_from_example(env_path: Path, example_path: Path) -> bool:
    """Kopiert Example → env, wenn env fehlt. True wenn neu angelegt."""
    if env_path.is_file():
        return False
    if not example_path.is_file():
        raise FileNotFoundError(f"Vorlage fehlt: {example_path}")
    env_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(example_path, env_path)
    return True


def ensure_vault_dir(vault_dir: Path, *, example_dir: Path | None = None) -> None:
    vault_dir.mkdir(parents=True, exist_ok=True)
    if example_dir is None:
        example_dir = Path("vault.example")
    if example_dir.is_dir() and not any(vault_dir.iterdir()):
        shutil.copytree(example_dir, vault_dir, dirs_exist_ok=True)


def _prompt(
    prompt_fn: PromptFn,
    label: str,
    *,
    default: str = "",
    secret: bool = False,
) -> str:
    suffix = ""
    if default and not secret:
        suffix = f" [{default}]"
    elif default and secret:
        suffix = " [unverändert]"
    raw = prompt_fn(f"{label}{suffix}: ").strip()
    if not raw:
        return default
    return raw


def _prompt_yes_no(prompt_fn: PromptFn, label: str, *, default: bool = False) -> bool:
    hint = "Y/n" if default else "y/N"
    raw = prompt_fn(f"{label} [{hint}]: ").strip().lower()
    if not raw:
        return default
    return raw in {"y", "yes", "j", "ja", "true", "1"}


def collect_interactive(
    *,
    existing: dict[str, str],
    default_vault: str,
    prompt_fn: PromptFn,
) -> InitAnswers:
    vault = _prompt(
        prompt_fn,
        "Vault-Pfad (Host)",
        default=existing.get("OBSIDIAN_VAULT_HOST_PATH") or default_vault,
    )
    openai_default = existing.get("OPENAI_API_KEY", "")
    if is_placeholder(openai_default):
        openai_default = ""
    openai = _prompt(
        prompt_fn,
        "OpenAI API Key (leer = überspringen)",
        default=openai_default,
        secret=True,
    )
    telegram_default = existing.get("TELEGRAM_BOT_TOKEN", "")
    if is_placeholder(telegram_default):
        telegram_default = ""
    telegram = _prompt(
        prompt_fn,
        "Telegram Bot Token (optional)",
        default=telegram_default,
        secret=True,
    )
    webhook_secret = ""
    allowed = ""
    if telegram:
        existing_secret = existing.get("TELEGRAM_WEBHOOK_SECRET", "")
        if is_placeholder(existing_secret):
            existing_secret = ""
        webhook_secret = _prompt(
            prompt_fn,
            "Telegram Webhook Secret (leer = neu generieren)",
            default=existing_secret,
            secret=True,
        )
        allowed = _prompt(
            prompt_fn,
            "Telegram Allowed User IDs (optional, kommagetrennt)",
            default=existing.get("TELEGRAM_ALLOWED_USER_IDS", ""),
        )
    api_default = existing.get("SEITON_API_KEY", "")
    if is_placeholder(api_default) or api_default == "change-me-to-a-long-random-string":
        api_default = ""
    seiton_key = _prompt(
        prompt_fn,
        "Seiton API Key (leer = neu generieren)",
        default=api_default,
        secret=True,
    )
    emb_default = existing.get("EMBEDDINGS_ENABLED", "false").lower() == "true"
    embeddings = _prompt_yes_no(
        prompt_fn,
        "Semantische Suche (Embeddings) aktivieren?",
        default=emb_default,
    )
    return InitAnswers(
        vault_host_path=vault,
        openai_api_key=openai,
        telegram_bot_token=telegram,
        telegram_webhook_secret=webhook_secret,
        telegram_allowed_user_ids=allowed,
        seiton_api_key=seiton_key,
        embeddings_enabled=embeddings,
    )


def collect_non_interactive(args: argparse.Namespace, existing: dict[str, str]) -> InitAnswers:
    vault = (
        args.vault.strip()
        or existing.get("OBSIDIAN_VAULT_HOST_PATH")
        or str(Path("vault").resolve())
    )
    openai = args.openai_api_key.strip()
    if not openai:
        cur = existing.get("OPENAI_API_KEY", "")
        openai = "" if is_placeholder(cur) else cur

    telegram = args.telegram_bot_token.strip()
    if not telegram:
        cur = existing.get("TELEGRAM_BOT_TOKEN", "")
        telegram = "" if is_placeholder(cur) else cur

    webhook = args.telegram_webhook_secret.strip()
    allowed = args.telegram_allowed_user_ids.strip()
    seiton_key = args.seiton_api_key.strip()
    if not seiton_key:
        cur = existing.get("SEITON_API_KEY", "")
        if cur and cur != "change-me-to-a-long-random-string" and not is_placeholder(cur):
            seiton_key = cur

    embeddings: bool | None = None
    if args.embeddings == "true":
        embeddings = True
    elif args.embeddings == "false":
        embeddings = False

    return InitAnswers(
        vault_host_path=vault,
        openai_api_key=openai,
        telegram_bot_token=telegram,
        telegram_webhook_secret=webhook,
        telegram_allowed_user_ids=allowed,
        seiton_api_key=seiton_key,
        embeddings_enabled=embeddings,
    )


def answers_to_updates(answers: InitAnswers) -> dict[str, str]:
    vault = Path(answers.vault_host_path).expanduser().resolve()
    updates: dict[str, str] = {
        "OBSIDIAN_VAULT_HOST_PATH": str(vault),
        "OBSIDIAN_VAULT_PATH": "/vault",
    }
    if answers.openai_api_key.strip():
        updates["OPENAI_API_KEY"] = answers.openai_api_key.strip()

    if answers.telegram_bot_token.strip():
        updates["TELEGRAM_BOT_TOKEN"] = answers.telegram_bot_token.strip()
        secret = answers.telegram_webhook_secret.strip() or secrets.token_urlsafe(32)
        updates["TELEGRAM_WEBHOOK_SECRET"] = secret
        if answers.telegram_allowed_user_ids.strip():
            updates["TELEGRAM_ALLOWED_USER_IDS"] = answers.telegram_allowed_user_ids.strip()

    api_key = answers.seiton_api_key.strip() or secrets.token_urlsafe(32)
    updates["SEITON_API_KEY"] = api_key

    if answers.embeddings_enabled is not None:
        updates["EMBEDDINGS_ENABLED"] = "true" if answers.embeddings_enabled else "false"

    return updates


def apply_init(
    answers: InitAnswers,
    *,
    env_path: Path,
    example_vault: Path | None = None,
) -> Path:
    updates = answers_to_updates(answers)
    vault = Path(updates["OBSIDIAN_VAULT_HOST_PATH"])
    ensure_vault_dir(vault, example_dir=example_vault)
    return update_env_file(updates, env_path)


def run_init(
    args: argparse.Namespace,
    *,
    prompt_fn: PromptFn = input,
    print_fn: PrintFn = print,
) -> int:
    env_path = resolve_env_path(args.env_file)
    example_path = Path(args.example)
    cwd = Path.cwd()

    print_fn("Seiton Brain — init (E16-3)")
    print_fn("Keys bleiben lokal in der .env. Kein Netzwerk-Upload.")
    print_fn("")

    try:
        created = ensure_env_from_example(env_path, example_path)
    except FileNotFoundError as exc:
        print(f"Fehler: {exc}", file=sys.stderr)
        return 1

    if created:
        print_fn(f"[ok] {env_path.name} aus {example_path.name} angelegt")
    else:
        print_fn(f"[ok] {env_path} vorhanden")

    existing = read_env_values(env_path)
    default_vault = str((cwd / "vault").resolve())

    if args.non_interactive:
        answers = collect_non_interactive(args, existing)
    else:
        print_fn("Leere Eingabe = Default / unverändert behalten.")
        answers = collect_interactive(
            existing=existing,
            default_vault=default_vault,
            prompt_fn=prompt_fn,
        )

    written = apply_init(answers, env_path=env_path, example_vault=cwd / "vault.example")
    print_fn("")
    print_fn(f"[ok] Konfiguration geschrieben: {written}")
    print_fn(f"[ok] Vault: {Path(answers.vault_host_path).expanduser().resolve()}")
    print_fn("")
    print_fn("Naechste Schritte:")
    print_fn("  1. Stack starten:  ./scripts/install.sh   # oder docker compose up -d")
    print_fn("  2. Diagnose:       ./scripts/doctor.sh")
    print_fn("  3. UI (nach Start): http://localhost:8000/setup  (Keys nachpflegen)")
    print_fn("")
    return 0
