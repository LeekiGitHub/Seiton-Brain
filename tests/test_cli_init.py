"""Tests fuer ``seiton init`` (E16-3)."""

import io
from argparse import Namespace
from pathlib import Path

from app.cli import __main__ as cli_main
from app.cli.init_wizard import (
    InitAnswers,
    answers_to_updates,
    apply_init,
    collect_interactive,
    ensure_env_from_example,
    run_init,
)
from app.setup.env_file import read_env_values


def test_ensure_env_from_example(tmp_path: Path):
    example = tmp_path / ".env.example"
    example.write_text("OPENAI_API_KEY=...\n", encoding="utf-8")
    env = tmp_path / ".env"
    assert ensure_env_from_example(env, example) is True
    assert env.is_file()
    assert ensure_env_from_example(env, example) is False


def test_answers_to_updates_generates_secrets():
    answers = InitAnswers(
        vault_host_path="/tmp/seiton-vault-test",
        openai_api_key="sk-test",
        telegram_bot_token="123:ABC",
        telegram_webhook_secret="",
        telegram_allowed_user_ids="42",
        seiton_api_key="",
        embeddings_enabled=True,
    )
    updates = answers_to_updates(answers)
    assert updates["OPENAI_API_KEY"] == "sk-test"
    assert updates["TELEGRAM_BOT_TOKEN"] == "123:ABC"
    assert updates["TELEGRAM_ALLOWED_USER_IDS"] == "42"
    assert updates["TELEGRAM_WEBHOOK_SECRET"]
    assert updates["SEITON_API_KEY"]
    assert updates["EMBEDDINGS_ENABLED"] == "true"
    assert updates["OBSIDIAN_VAULT_PATH"] == "/vault"


def test_apply_init_writes_env_and_vault(tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text("OPENAI_API_KEY=...\nSEITON_API_KEY=change-me\n", encoding="utf-8")
    vault = tmp_path / "my-vault"
    answers = InitAnswers(
        vault_host_path=str(vault),
        openai_api_key="sk-live",
        telegram_bot_token="",
        telegram_webhook_secret="",
        telegram_allowed_user_ids="",
        seiton_api_key="fixed-api-key",
        embeddings_enabled=False,
    )
    written = apply_init(answers, env_path=env, example_vault=None)
    assert written == env.resolve()
    values = read_env_values(env)
    assert values["OPENAI_API_KEY"] == "sk-live"
    assert values["SEITON_API_KEY"] == "fixed-api-key"
    assert values["EMBEDDINGS_ENABLED"] == "false"
    assert vault.is_dir()


def test_collect_interactive_uses_defaults():
    prompts = iter(
        [
            "",  # vault default
            "sk-from-prompt",
            "",  # no telegram
            "",  # api key generate later
            "n",  # embeddings
        ]
    )
    answers = collect_interactive(
        existing={},
        default_vault="/default/vault",
        prompt_fn=lambda _label: next(prompts),
    )
    assert answers.vault_host_path == "/default/vault"
    assert answers.openai_api_key == "sk-from-prompt"
    assert answers.telegram_bot_token == ""
    assert answers.embeddings_enabled is False


def test_run_init_non_interactive(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    example = tmp_path / ".env.example"
    example.write_text(
        "OPENAI_API_KEY=...\nSEITON_API_KEY=change-me-to-a-long-random-string\n",
        encoding="utf-8",
    )
    vault = tmp_path / "vault"
    args = Namespace(
        env_file=str(tmp_path / ".env"),
        example=str(example),
        non_interactive=True,
        vault=str(vault),
        openai_api_key="sk-ni",
        telegram_bot_token="tok",
        telegram_webhook_secret="sec",
        telegram_allowed_user_ids="1,2",
        seiton_api_key="api-key",
        embeddings="true",
    )
    buf = io.StringIO()
    code = run_init(args, print_fn=lambda *a, **k: print(*a, file=buf, **k))
    assert code == 0
    values = read_env_values(tmp_path / ".env")
    assert values["OPENAI_API_KEY"] == "sk-ni"
    assert values["TELEGRAM_BOT_TOKEN"] == "tok"
    assert values["TELEGRAM_WEBHOOK_SECRET"] == "sec"
    assert values["EMBEDDINGS_ENABLED"] == "true"
    assert "Kein Netzwerk-Upload" in buf.getvalue()


def test_cli_main_init_non_interactive(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env.example").write_text("OPENAI_API_KEY=...\n", encoding="utf-8")
    code = cli_main.main(
        [
            "init",
            "--non-interactive",
            "--env-file",
            str(tmp_path / ".env"),
            "--example",
            str(tmp_path / ".env.example"),
            "--vault",
            str(tmp_path / "v"),
            "--openai-api-key",
            "sk-x",
            "--seiton-api-key",
            "k",
            "--embeddings",
            "false",
        ]
    )
    assert code == 0
    assert (tmp_path / ".env").is_file()


def test_scripts_seiton_wrapper_exists():
    script = Path("scripts/seiton")
    assert script.is_file()
    text = script.read_text(encoding="utf-8")
    assert "python" in text
    assert "app.cli" in text
