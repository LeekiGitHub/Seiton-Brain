import os
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class VaultNote:
    title: str
    category: str
    folder: str
    snippet: str


def _parse_frontmatter(content: str) -> dict[str, str]:
    if not content.startswith("---"):
        return {}
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}
    meta: dict[str, str] = {}
    for line in parts[1].strip().splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
    return meta


def _body_snippet(content: str, limit: int = 120) -> str:
    if content.startswith("---"):
        parts = content.split("---", 2)
        body = parts[2] if len(parts) > 2 else content
    else:
        body = content
    text = re.sub(r"#+\s*", "", body)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def list_existing_notes(limit: int = 80) -> list[VaultNote]:
    vault_path = Path(os.environ["OBSIDIAN_VAULT_PATH"])
    if not vault_path.exists():
        return []

    notes: list[VaultNote] = []
    for md_file in sorted(vault_path.rglob("*.md")):
        if md_file.name.startswith("."):
            continue
        try:
            content = md_file.read_text(encoding="utf-8")
        except OSError:
            continue

        meta = _parse_frontmatter(content)
        title = meta.get("title") or md_file.stem
        category = meta.get("category", "")
        folder = md_file.parent.name
        snippet = _body_snippet(content)

        notes.append(
            VaultNote(
                title=title,
                category=category,
                folder=folder,
                snippet=snippet,
            )
        )

    notes.sort(key=lambda n: (n.folder.lower(), n.title.lower()))
    return notes[:limit]


def format_notes_for_prompt(notes: list[VaultNote]) -> str:
    if not notes:
        return "(no existing notes yet)"
    lines = []
    for note in notes:
        category_hint = note.category or note.folder
        lines.append(f"- [{category_hint}] {note.title}: {note.snippet}")
    return "\n".join(lines)


def known_titles(notes: list[VaultNote]) -> dict[str, str]:
    return {note.title.lower(): note.title for note in notes}
