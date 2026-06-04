import re
from datetime import date
from pathlib import Path

from app.config import settings
from app.llm.schemas import ClassificationResult

CATEGORY_FOLDERS = {
    "school": "School",
    "work": "Work",
    "private": "Private",
    "idea": "Ideas",
    "travel": "Travel",
    "note": "Notes",
}


def _sanitize_filename(title: str) -> str:
    name = re.sub(r'[\\/:*?"<>|]', "", title).strip()
    return name[:200] or "Untitled"


def _related_section(related: list[str]) -> str:
    if not related:
        return ""
    links = "\n".join(f"- [[{title}]]" for title in related)
    return f"\n\n## Related\n{links}"


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
    folder = CATEGORY_FOLDERS.get(result.category.lower(), "Notes")
    target_dir = vault_path / folder
    target_dir.mkdir(parents=True, exist_ok=True)

    base_name = _sanitize_filename(result.title)
    filepath = _next_available_path(target_dir, base_name)

    content = f"""---
title: {result.title}
category: {result.category}
created: {date.today().isoformat()}
---

# {result.title}

{result.summary}{_related_section(result.related)}
"""
    filepath.write_text(content, encoding="utf-8")
    return filepath


def append_to_note(vault_relative_path: str, result: ClassificationResult) -> Path:
    """Haengt einen Update-Block an eine bestehende Notiz an.

    Das Format ist bewusst minimal: eine Leerzeile, eine ``## Update <Datum>``-
    Ueberschrift, der Summary-Text, optional eine kleine Related-Sektion.
    Frontmatter-Updates (``updated:``, Tag-Merge) bleiben Story E3-3.
    """
    vault_root = Path(settings.obsidian_vault_path)
    filepath = vault_root / vault_relative_path
    if not filepath.exists():
        raise FileNotFoundError(
            f"Cannot append to missing vault file: {vault_relative_path}"
        )

    existing = filepath.read_text(encoding="utf-8")
    if not existing.endswith("\n"):
        existing += "\n"

    block = f"\n## Update {date.today().isoformat()}\n\n{result.summary}\n"
    if result.related:
        block += _related_section(result.related).lstrip("\n") + "\n"

    filepath.write_text(existing + block, encoding="utf-8")
    return filepath
