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
