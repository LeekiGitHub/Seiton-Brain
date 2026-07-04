import subprocess
from pathlib import Path

SCRIPTS = (
    "scripts/backup.sh",
    "scripts/bootstrap_github.sh",
    "scripts/install.sh",
    "scripts/doctor.sh",
)


def test_shell_scripts_have_valid_syntax():
    for relative in SCRIPTS:
        script = Path(relative)
        assert script.is_file(), f"missing script: {relative}"
        subprocess.run(["bash", "-n", str(script)], check=True)
