"""Tests fuer init.sh (E16-1)."""

import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INIT = ROOT / "scripts" / "init.sh"


def test_init_creates_env_and_vault(tmp_path):
    env_example = tmp_path / ".env.example"
    env_example.write_text(
        "OPENAI_API_KEY=...\nOBSIDIAN_VAULT_PATH=/vault\n",
        encoding="utf-8",
    )
    (tmp_path / "vault.example" / "Notes").mkdir(parents=True)
    (tmp_path / "vault.example" / "Notes" / "Sample.md").write_text("# Hi", encoding="utf-8")
    (tmp_path / "scripts").mkdir()
    shutil.copy(INIT, tmp_path / "scripts" / "init.sh")
    shutil.copytree(ROOT / "scripts" / "lib", tmp_path / "scripts" / "lib")

    env = os.environ.copy()
    env["VAULT_DIR"] = str(tmp_path / "vault")

    subprocess.run(["bash", str(tmp_path / "scripts" / "init.sh")], cwd=tmp_path, check=True, env=env)

    assert (tmp_path / ".env").is_file()
    assert "OBSIDIAN_VAULT_HOST_PATH=" in (tmp_path / ".env").read_text(encoding="utf-8")
    assert (tmp_path / "vault" / "Notes" / "Sample.md").is_file()

    # Idempotent second run
    subprocess.run(["bash", str(tmp_path / "scripts" / "init.sh")], cwd=tmp_path, check=True, env=env)
