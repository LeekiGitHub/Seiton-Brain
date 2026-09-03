"""Specialized LLM roles (E7-3): Router → Writer → Linker.

No agent framework — max. 2–3 typed prompt steps (ADR 0003).
Result remains ``ClassificationResult`` for vault/API.
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
    """Aggregate role outputs into a ``ClassificationResult``."""
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
