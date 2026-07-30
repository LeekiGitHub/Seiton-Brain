"""Spezialisierte LLM-Rollen (E7-3): Router → Writer → Linker.

Kein Agent-Framework — max. 2–3 typisierte Prompt-Steps (ADR 0003).
Ergebnis bleibt ``ClassificationResult`` fuer Vault/API.
"""

from __future__ import annotations

from app.llm.schemas import (
    ClassificationResult,
    LinkerResult,
    RouterResult,
    WriterResult,
)


def merge_role_results(
    router: RouterResult,
    writer: WriterResult,
    linker: LinkerResult | None = None,
) -> ClassificationResult:
    """Aggregiert Rollen-Outputs zu einem ``ClassificationResult``."""
    related = list(linker.related) if linker is not None else []
    return ClassificationResult(
        category=router.category,
        title=router.title,
        summary=writer.summary,
        tags=list(writer.tags),
        related=related,
        action=router.action,
        target_title=router.target_title,
    )
