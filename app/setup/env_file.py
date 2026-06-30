"""Lesen und Schreiben der lokalen ``.env`` fuer den Setup-Wizard."""

from __future__ import annotations

import re
from pathlib import Path

_ENV_LINE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$")


def resolve_env_path(path: str | None = None) -> Path:
    return Path(path or ".env").expanduser().resolve()


def read_env_values(path: Path | None = None) -> dict[str, str]:
    """Parst KEY=VALUE-Zeilen; ignoriert Kommentare und leere Zeilen."""
    env_path = resolve_env_path(str(path)) if path is not None else resolve_env_path()
    if not env_path.is_file():
        return {}

    values: dict[str, str] = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = _ENV_LINE.match(stripped)
        if match:
            key, raw = match.group(1), match.group(2)
            values[key] = _unquote(raw.strip())
    return values


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _quote_if_needed(value: str) -> str:
    if not value:
        return ""
    if any(ch.isspace() for ch in value) or "#" in value:
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return value


def update_env_file(updates: dict[str, str], path: Path | None = None) -> Path:
    """Aktualisiert oder haengt Keys in ``.env`` an; erhaelt Kommentare/Reihenfolge."""
    env_path = resolve_env_path(str(path)) if path is not None else resolve_env_path()
    existing_lines: list[str] = []
    if env_path.is_file():
        existing_lines = env_path.read_text(encoding="utf-8").splitlines()

    remaining = dict(updates)
    new_lines: list[str] = []
    seen_keys: set[str] = set()

    for line in existing_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            new_lines.append(line)
            continue
        match = _ENV_LINE.match(stripped)
        if not match:
            new_lines.append(line)
            continue
        key = match.group(1)
        if key in remaining:
            new_lines.append(f"{key}={_quote_if_needed(remaining.pop(key))}")
            seen_keys.add(key)
        else:
            new_lines.append(line)
            seen_keys.add(key)

    for key, value in remaining.items():
        if key not in seen_keys:
            new_lines.append(f"{key}={_quote_if_needed(value)}")

    env_path.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(new_lines)
    if content and not content.endswith("\n"):
        content += "\n"
    env_path.write_text(content, encoding="utf-8")
    return env_path
