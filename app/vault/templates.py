"""Note templates (E26-1/E26-2): users control the body layout of new notes.

Template file: ``<Vault>/_seiton/templates/note.md`` — deliberately in the vault
(visible in Obsidian, portable, travels with backups). If the file is missing,
the default layout (current format) applies.

Placeholders: ``{{title}}``, ``{{summary}}``, ``{{tags}}``, ``{{date}}``,
``{{category}}``, ``{{related}}``. ``{{related}}`` renders the full section
including the ``## Related`` heading (starting with a blank line), or nothing
when there are no related notes.

Guardrails (E26-2):
- The template controls **the body only**. Frontmatter stays fixed so
  append logic (E3-3/E4-1) and the index do not break.
- Broken templates (unknown placeholders, own frontmatter, missing
  ``{{summary}}``) → default layout + log warning. Capture must never fail
  because of a template.
"""

from __future__ import annotations

import logging
import re
from datetime import date
from pathlib import Path

from app.config import settings
from app.llm.schemas import ClassificationResult

logger = logging.getLogger(__name__)

TEMPLATE_RELATIVE_PATH = "_seiton/templates/note.md"

KNOWN_PLACEHOLDERS = frozenset(
    {"title", "summary", "tags", "date", "category", "related"}
)

# Matches the previous hard-coded layout exactly.
DEFAULT_TEMPLATE = "# {{title}}\n\n{{summary}}{{related}}\n"

_PLACEHOLDER_RE = re.compile(r"\{\{\s*([a-zA-Z_:]+)\s*\}\}")


def template_path() -> Path:
    return Path(settings.obsidian_vault_path) / TEMPLATE_RELATIVE_PATH


def validate_template(text: str) -> list[str]:
    """Return error list — empty means usable (E26-2)."""
    errors: list[str] = []
    if text.lstrip().startswith("---"):
        errors.append(
            "Template darf kein eigenes Frontmatter enthalten (--- am Anfang) — "
            "Frontmatter wird von Seiton verwaltet."
        )
    placeholders = set(_PLACEHOLDER_RE.findall(text))
    unknown = placeholders - KNOWN_PLACEHOLDERS
    if unknown:
        errors.append(
            "Unbekannte Platzhalter: "
            + ", ".join(sorted(f"{{{{{name}}}}}" for name in unknown))
        )
    if "summary" not in placeholders:
        errors.append("{{summary}} fehlt — der Notiz-Inhalt würde verloren gehen.")
    return errors


def template_status() -> str:
    """For the settings UI: ``default`` | ``custom`` | ``invalid``."""
    path = template_path()
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return "default"
    except OSError:
        return "invalid"
    return "invalid" if validate_template(text) else "custom"


def load_note_template() -> str:
    """Active template — default when the file is missing or invalid."""
    path = template_path()
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return DEFAULT_TEMPLATE
    except OSError as exc:
        logger.warning("Notiz-Template %s nicht lesbar (%s) — nutze Default.", path, exc)
        return DEFAULT_TEMPLATE

    errors = validate_template(text)
    if errors:
        logger.warning(
            "Notiz-Template %s ungültig — nutze Default. Probleme: %s",
            path,
            " | ".join(errors),
        )
        return DEFAULT_TEMPLATE
    if not text.strip():
        logger.warning("Notiz-Template %s ist leer — nutze Default.", path)
        return DEFAULT_TEMPLATE
    return text


def _related_block(related: list[str]) -> str:
    if not related:
        return ""
    links = "\n".join(f"- [[{title}]]" for title in related)
    return f"\n\n## Related\n{links}"


def _tags_inline(tags: list[str]) -> str:
    return " ".join(f"#{tag}" for tag in tags)


def render_note_body(result: ClassificationResult) -> str:
    """Render the note body from the active template (E26-1)."""
    template = load_note_template()
    values = {
        "title": result.title,
        "summary": result.summary,
        "tags": _tags_inline(result.tags),
        "date": date.today().isoformat(),
        "category": result.category,
        "related": _related_block(result.related),
    }

    def _substitute(match: re.Match[str]) -> str:
        return values.get(match.group(1), match.group(0))

    body = _PLACEHOLDER_RE.sub(_substitute, template)
    # Empty placeholders would otherwise leave ugly trailing spaces.
    body = "\n".join(line.rstrip() for line in body.split("\n"))
    return body.rstrip("\n") + "\n"
