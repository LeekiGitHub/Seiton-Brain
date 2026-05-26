import os
import re
from datetime import date
from pathlib import Path

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


def write_note(result: ClassificationResult) -> Path:
    vault_path = Path(os.environ["OBSIDIAN_VAULT_PATH"])
    folder = CATEGORY_FOLDERS.get(result.category.lower(), "Notes")
    target_dir = vault_path / folder
    target_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{_sanitize_filename(result.title)}.md"
    filepath = target_dir / filename

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
