"""Filesystem Markdown VaultBackend (E15-1) — Obsidian-compatible."""

from __future__ import annotations

import contextlib
import os
import re
import tempfile
from collections.abc import Iterator
from datetime import date
from pathlib import Path

from app.config import settings
from app.llm.schemas import ClassificationResult
from app.llm.tags import merge_tags
from app.vault.categories import folder_for_category
from app.vault.paths import resolve_vault_file
from app.vault.templates import render_note_body

FRONTMATTER_KEY_ORDER = ("title", "category", "created", "updated", "tags")

try:
    import fcntl
except ImportError:  # Windows — no cross-process flock
    fcntl = None  # type: ignore[assignment]


def _sanitize_filename(title: str) -> str:
    name = re.sub(r'[\\/:*?"<>|]', "", title).strip()
    return name[:200] or "Untitled"


@contextlib.contextmanager
def _file_lock(lock_target: Path) -> Iterator[None]:
    """Cross-process exclusive lock (E28-2).

    Lock file: ``.<name>.lock`` next to the target. Without ``fcntl`` (Windows)
    there is no cross-process lock — single-worker dev remains fine.
    """
    lock_path = lock_target.parent / f".{lock_target.name}.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with open(lock_path, "a+", encoding="utf-8") as fh:
        if fcntl is not None:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            if fcntl is not None:
                fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


def _sanitize_frontmatter_scalar(value: str) -> str:
    """Sanitize a frontmatter scalar against YAML/structure injection (E27-4).

    Newlines, control chars, and ``---`` sequences would otherwise break note
    structure (frontmatter terminator). Quotes are escaped so the value stays
    a safe single YAML line.
    """
    cleaned = re.sub(r"[\x00-\x1f\x7f]", " ", value)
    cleaned = cleaned.replace("---", "—").strip()
    # Escape YAML special chars inside single quotes
    if any(c in cleaned for c in (":", "#", "'", '"', "[", "]", "{", "}", ",")):
        return "'" + cleaned.replace("'", "''") + "'"
    return cleaned


def _sanitize_frontmatter_tags(tags: list[str]) -> list[str]:
    """Sanitize tags for YAML inline lists (no newlines/commas/brackets)."""
    out: list[str] = []
    for tag in tags:
        cleaned = re.sub(r"[\x00-\x1f\x7f]", "", tag)
        cleaned = re.sub(r"[,\[\]{}]", "", cleaned).strip()
        if cleaned:
            out.append(cleaned)
    return out


def _related_section(related: list[str]) -> str:
    if not related:
        return ""
    links = "\n".join(f"- [[{title}]]" for title in related)
    return f"\n\n## Related\n{links}"


def _tags_frontmatter_line(tags: list[str]) -> str:
    """Render tags as a YAML inline list in frontmatter.

    Empty tag list → empty string (no frontmatter line). Obsidian treats
    inline lists the same as block lists.
    """
    safe = _sanitize_frontmatter_tags(tags)
    if not safe:
        return ""
    return f"tags: [{', '.join(safe)}]\n"


def _atomic_write(target: Path, content: str) -> None:
    """Write ``content`` to ``target`` atomically.

    Strategy: create a tempfile in the same directory, write fully, fsync,
    then ``os.replace`` onto the target. ``os.replace`` is atomic on POSIX and
    Windows *as long as* source and destination share a filesystem — hence the
    tempfile must live in the same directory.

    Sync clients (Obsidian Sync, Syncthing, iCloud) never see a half-written
    file; a crash between write and replace leaves at most a ``.tmp`` file
    instead of corrupt content at the target.
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path_str = tempfile.mkstemp(
        prefix=f".{target.name}.",
        suffix=".tmp",
        dir=str(target.parent),
    )
    tmp_path = Path(tmp_path_str)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_path, target)
    except BaseException:
        # Write or replace failed — remove tempfile so the vault dir is not
        # littered with orphans.
        tmp_path.unlink(missing_ok=True)
        raise


def _next_available_path(target_dir: Path, base_name: str) -> Path:
    """First free path: `<base>.md`, `<base> (2).md`, `<base> (3).md`, …

    Uses Obsidian-style suffixes instead of silently overwriting.
    """
    candidate = target_dir / f"{base_name}.md"
    if not candidate.exists():
        return candidate
    counter = 2
    while True:
        candidate = target_dir / f"{base_name} ({counter}).md"
        if not candidate.exists():
            return candidate
        counter += 1


def _parse_frontmatter(text: str) -> tuple[dict[str, str | list[str]] | None, str]:
    """Split YAML frontmatter (between ``---`` lines) from the body.

    Intentionally minimal: we only parse the format we ourselves emit
    (``key: value`` per line, ``tags: [a, b]`` as inline list or ``tags:``
    followed by ``- foo`` lines). Enough for our use case and avoids a
    PyYAML dependency.

    Unrecognized frontmatter: return ``(None, text)`` — caller treats that
    as "no frontmatter".
    """
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return None, text

    fm_block = text[4:end]
    body = text[end + len("\n---\n") :]

    data: dict[str, str | list[str]] = {}
    lines = fm_block.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or ":" not in line:
            i += 1
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()

        if value.startswith("[") and value.endswith("]"):
            items = [v.strip() for v in value[1:-1].split(",") if v.strip()]
            data[key] = items
        elif value == "":
            block_items: list[str] = []
            j = i + 1
            while j < len(lines) and lines[j].lstrip().startswith("- "):
                block_items.append(lines[j].lstrip()[2:].strip())
                j += 1
            data[key] = block_items
            i = j
            continue
        else:
            data[key] = value
        i += 1

    return data, body


def _render_frontmatter(data: dict[str, str | list[str]]) -> str:
    lines: list[str] = ["---"]
    rendered: set[str] = set()
    for key in FRONTMATTER_KEY_ORDER:
        if key not in data:
            continue
        rendered.add(key)
        value = data[key]
        if isinstance(value, list):
            safe_list = _sanitize_frontmatter_tags(value)
            if not safe_list:
                continue
            lines.append(f"{key}: [{', '.join(safe_list)}]")
        else:
            lines.append(f"{key}: {_sanitize_frontmatter_scalar(str(value))}")
    for key, value in data.items():
        if key in rendered:
            continue
        if isinstance(value, list):
            safe_list = _sanitize_frontmatter_tags(value)
            if not safe_list:
                continue
            lines.append(f"{key}: [{', '.join(safe_list)}]")
        else:
            lines.append(f"{key}: {_sanitize_frontmatter_scalar(str(value))}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def _to_relative(filepath: Path) -> str:
    root = Path(settings.obsidian_vault_path).resolve()
    return str(filepath.resolve().relative_to(root))


class FilesystemVaultBackend:
    """Markdown files under ``OBSIDIAN_VAULT_PATH`` (default backend)."""

    def write_note(self, result: ClassificationResult) -> str:
        vault_path = Path(settings.obsidian_vault_path)
        folder = folder_for_category(result.category)
        target_dir = vault_path / folder
        target_dir.mkdir(parents=True, exist_ok=True)

        base_name = _sanitize_filename(result.title)
        # Lock on basename: allocate + write atomic vs parallel captures
        with _file_lock(target_dir / f"{base_name}.md"):
            filepath = _next_available_path(target_dir, base_name)

            frontmatter = f"""---
title: {_sanitize_frontmatter_scalar(result.title)}
category: {_sanitize_frontmatter_scalar(result.category)}
created: {date.today().isoformat()}
{_tags_frontmatter_line(result.tags)}---

"""
            # Body via note template (E26-1) — default matches the old layout.
            content = frontmatter + render_note_body(result)
            _atomic_write(filepath, content)
            return _to_relative(filepath)

    def append_to_note(self, vault_path: str, result: ClassificationResult) -> str:
        """Append an update block and maintain frontmatter (E3-3)."""
        filepath = resolve_vault_file(vault_path)
        if not filepath.exists():
            raise FileNotFoundError(
                f"Cannot append to missing vault file: {vault_path}"
            )

        with _file_lock(filepath):
            existing = filepath.read_text(encoding="utf-8")
            fm, body = _parse_frontmatter(existing)

            if fm is not None:
                fm["updated"] = date.today().isoformat()
                existing_tags = fm.get("tags", [])
                if not isinstance(existing_tags, list):
                    existing_tags = []
                if result.tags or existing_tags:
                    fm["tags"] = merge_tags(existing_tags, result.tags)
                rebuilt = _render_frontmatter(fm) + body
            else:
                rebuilt = existing

            if not rebuilt.endswith("\n"):
                rebuilt += "\n"

            block = f"\n## Update {date.today().isoformat()}\n\n{result.summary}\n"
            if result.related:
                block += _related_section(result.related).lstrip("\n") + "\n"

            _atomic_write(filepath, rebuilt + block)
            return vault_path

    def save_note_content(self, vault_path: str, content: str) -> str:
        filepath = resolve_vault_file(vault_path)
        if not filepath.is_file():
            raise FileNotFoundError(f"Note not found: {vault_path}")
        _atomic_write(filepath, content)
        return vault_path

    def delete_note(self, vault_path: str) -> bool:
        try:
            filepath = resolve_vault_file(vault_path)
        except ValueError:
            return False
        if not filepath.exists():
            return False
        filepath.unlink()
        return True

    def note_exists(self, vault_path: str) -> bool:
        try:
            return resolve_vault_file(vault_path).is_file()
        except ValueError:
            return False
