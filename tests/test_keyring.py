"""Tests fuer OS-Keystore (E16-5)."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.cli import __main__ as cli_main
from app.cli.init_wizard import InitAnswers, apply_init
from app.cli import keyring_store as kr
from app.setup.env_file import read_env_values


@pytest.fixture
def fake_keyring(monkeypatch):
    store: dict[tuple[str, str], str] = {}

    def set_password(service, key, value):
        store[(service, key)] = value

    def get_password(service, key):
        return store.get((service, key))

    def delete_password(service, key):
        store.pop((service, key), None)

    mod = MagicMock()
    mod.set_password = set_password
    mod.get_password = get_password
    mod.delete_password = delete_password
    monkeypatch.setattr(kr, "is_keyring_available", lambda: True)
    monkeypatch.setitem(__import__("sys").modules, "keyring", mod)
    return store


def test_store_and_load_secrets(fake_keyring):
    stored = kr.store_secrets(
        {"OPENAI_API_KEY": "sk-a", "SEITON_API_KEY": "k", "TELEGRAM_BOT_TOKEN": ""}
    )
    assert stored == ["OPENAI_API_KEY", "SEITON_API_KEY"]
    loaded = kr.load_secrets()
    assert loaded["OPENAI_API_KEY"] == "sk-a"
    assert loaded["SEITON_API_KEY"] == "k"
    assert "TELEGRAM_BOT_TOKEN" not in loaded


def test_export_dotenv(fake_keyring):
    kr.set_secret("OPENAI_API_KEY", 'sk-"x"')
    text = kr.export_dotenv()
    assert 'OPENAI_API_KEY=' in text
    assert "sk-" in text


def test_apply_init_with_keyring_clears_env_secrets(tmp_path: Path, fake_keyring):
    env = tmp_path / ".env"
    env.write_text("OPENAI_API_KEY=old\n", encoding="utf-8")
    vault = tmp_path / "vault"
    answers = InitAnswers(
        vault_host_path=str(vault),
        openai_api_key="sk-secret",
        telegram_bot_token="tok",
        telegram_webhook_secret="wh",
        telegram_allowed_user_ids="",
        seiton_api_key="api",
        embeddings_enabled=False,
        use_keyring=True,
    )
    apply_init(answers, env_path=env, example_vault=None)
    values = read_env_values(env)
    assert values.get("SEITON_KEYRING") == "true"
    assert values.get("OPENAI_API_KEY", "") == ""
    assert values.get("TELEGRAM_BOT_TOKEN", "") == ""
    assert values.get("SEITON_API_KEY", "") == ""
    assert kr.get_secret("OPENAI_API_KEY") == "sk-secret"
    assert kr.get_secret("SEITON_API_KEY") == "api"


def test_apply_init_keyring_missing_package(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(kr, "is_keyring_available", lambda: False)
    env = tmp_path / ".env"
    env.write_text("", encoding="utf-8")
    answers = InitAnswers(
        vault_host_path=str(tmp_path / "v"),
        openai_api_key="sk",
        telegram_bot_token="",
        telegram_webhook_secret="",
        telegram_allowed_user_ids="",
        seiton_api_key="k",
        embeddings_enabled=None,
        use_keyring=True,
    )
    with pytest.raises(RuntimeError, match="keyring"):
        apply_init(answers, env_path=env, example_vault=None)


def test_keyring_export_shell(fake_keyring, capsys):
    kr.set_secret("SEITON_API_KEY", "abc")
    code = cli_main.main(["keyring-export", "--shell"])
    assert code == 0
    out = capsys.readouterr().out
    assert 'export SEITON_API_KEY="abc"' in out


def test_init_non_interactive_keyring(tmp_path: Path, monkeypatch, fake_keyring):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env.example").write_text("OPENAI_API_KEY=...\n", encoding="utf-8")
    code = cli_main.main(
        [
            "init",
            "--non-interactive",
            "--keyring",
            "--env-file",
            str(tmp_path / ".env"),
            "--example",
            str(tmp_path / ".env.example"),
            "--vault",
            str(tmp_path / "v"),
            "--openai-api-key",
            "sk-kr",
            "--seiton-api-key",
            "api-kr",
            "--embeddings",
            "false",
        ]
    )
    assert code == 0
    assert kr.get_secret("OPENAI_API_KEY") == "sk-kr"
    assert read_env_values(tmp_path / ".env").get("SEITON_KEYRING") == "true"


def test_compose_keyring_override_exists():
    path = Path("deploy/compose.keyring.yml")
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "OPENAI_API_KEY" in text
    assert "poller:" in text


def test_seiton_up_script_exists():
    script = Path("scripts/seiton-up.sh")
    assert script.is_file()
    text = script.read_text(encoding="utf-8")
    assert "keyring-export" in text
    assert "compose.keyring.yml" in text
