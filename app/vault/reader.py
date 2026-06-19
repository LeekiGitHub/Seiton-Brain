import re
from dataclasses import dataclass


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
