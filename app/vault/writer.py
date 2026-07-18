import os
import re
import tempfile
from datetime import date
from pathlib import Path

from app.config import settings
from app.llm.schemas import ClassificationResult
from app.llm.tags import merge_tags
from app.vault.categories import CATEGORY_FOLDERS, folder_for_category, get_category_folders
from app.vault.paths import resolve_vault_file

__all__ = [
    "CATEGORY_FOLDERS",
    "get_category_folders",
    "write_note",
    "append_to_note",
    "save_note_content",
    "delete_note",
]

FRONTMATTER_KEY_ORDER = ("title", "category", "created", "updated", "tags")


def _sanitize_filename(title: str) -> str:
    name = re.sub(r'[\\/:*?"<>|]', "", title).strip()
    return name[:200] or "Untitled"


def _related_section(related: list[str]) -> str:
    if not related:
        return ""
    links = "\n".join(f"- [[{title}]]" for title in related)
    return f"\n\n## Related\n{links}"


def _tags_frontmatter_line(tags: list[str]) -> str:
    """Rendert Tags als YAML-Inline-Liste im Frontmatter.

    Leere Tag-Liste -> leerer String (keine Frontmatter-Zeile). Obsidian
    erkennt Inline-Listen genauso wie Block-Listen.
    """
    if not tags:
        return ""
    return f"tags: [{', '.join(tags)}]\n"


def _atomic_write(target: Path, content: str) -> None:
    """Schreibt ``content`` atomar in ``target``.

    Strategie: Tempfile im selben Verzeichnis anlegen, vollstaendig
    beschreiben, fsync, dann ``os.replace`` auf den Zielpfad. ``os.replace``
    ist auf POSIX und Windows atomar, *solange* Quelle und Ziel auf demselben
    Dateisystem liegen — deshalb das Tempfile zwingend ins selbe Verzeichnis.

    Damit sehen Sync-Clients (Obsidian Sync, Syncthing, iCloud) nie eine halb
    geschriebene Datei, und ein Crash zwischen Schreiben und Replace
    hinterlaesst hoechstens eine ``.tmp``-Datei statt korrupten Inhalt am Ziel.
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
        # Schreiben oder Replace fehlgeschlagen — Tempfile aufraeumen, damit
        # das Vault-Verzeichnis nicht mit Leichen vollaeuft.
        tmp_path.unlink(missing_ok=True)
        raise


def _next_available_path(target_dir: Path, base_name: str) -> Path:
    """Erster freier Pfad: `<base>.md`, `<base> (2).md`, `<base> (3).md`, …

    Nutzt Obsidian-Style-Suffixe statt stillschweigend zu ueberschreiben.
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


def write_note(result: ClassificationResult) -> Path:
    vault_path = Path(settings.obsidian_vault_path)
    folder = folder_for_category(result.category)
    target_dir = vault_path / folder
    target_dir.mkdir(parents=True, exist_ok=True)

    base_name = _sanitize_filename(result.title)
    filepath = _next_available_path(target_dir, base_name)

    content = f"""---
title: {result.title}
category: {result.category}
created: {date.today().isoformat()}
{_tags_frontmatter_line(result.tags)}---

# {result.title}

{result.summary}{_related_section(result.related)}
"""
    _atomic_write(filepath, content)
    return filepath


def _parse_frontmatter(text: str) -> tuple[dict[str, str | list[str]] | None, str]:
    """Trennt YAML-Frontmatter (zwischen ``---``-Linien) vom Body.

    Bewusst minimal: wir parsen nur das Format, das wir selbst erzeugen
    (``key: value`` pro Zeile, ``tags: [a, b]`` als Inline-Liste oder
    ``tags:`` gefolgt von ``- foo``-Zeilen). Reicht voellig fuer unseren
    Use-Case und vermeidet eine PyYAML-Abhaengigkeit.

    Bei nicht-erkennbarem Frontmatter: ``(None, text)`` zurueck — Caller
    behandelt das wie "keine Frontmatter".
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
            if not value:
                continue
            lines.append(f"{key}: [{', '.join(value)}]")
        else:
            lines.append(f"{key}: {value}")
    for key, value in data.items():
        if key in rendered:
            continue
        if isinstance(value, list):
            if not value:
                continue
            lines.append(f"{key}: [{', '.join(value)}]")
        else:
            lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def save_note_content(vault_relative_path: str, content: str) -> Path:
    """Ueberschreibt eine bestehende Vault-Datei atomar (E19-4 UI-Editor)."""
    filepath = resolve_vault_file(vault_relative_path)
    if not filepath.is_file():
        raise FileNotFoundError(f"Note not found: {vault_relative_path}")
    _atomic_write(filepath, content)
    return filepath


def delete_note(vault_relative_path: str) -> bool:
    """Loescht eine Vault-Datei, wenn sie existiert.

    Liefert ``True``, wenn geloescht wurde, ``False`` wenn die Datei nicht
    (mehr) da war. Wirft nichts — der Caller soll selbst entscheiden, ob
    eine fehlende Datei ein Fehler ist (zB hat der User sie schon manuell
    geloescht).
    """
    try:
        filepath = resolve_vault_file(vault_relative_path)
    except ValueError:
        return False
    if not filepath.exists():
        return False
    filepath.unlink()
    return True


def append_to_note(vault_relative_path: str, result: ClassificationResult) -> Path:
    """Haengt einen Update-Block an eine bestehende Notiz an und pflegt
    das Frontmatter (``updated:``-Datum, Tag-Merge — Story E3-3).
    """
    vault_root = Path(settings.obsidian_vault_path)
    filepath = vault_root / vault_relative_path
    if not filepath.exists():
        raise FileNotFoundError(
            f"Cannot append to missing vault file: {vault_relative_path}"
        )

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
    return filepath
