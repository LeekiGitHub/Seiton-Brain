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

{result.summary}
"""
    filepath.write_text(content, encoding="utf-8")
    return filepath
