"""Heuristisches Pre-Filtering der Vault-Notizen vor dem LLM (E5-2).

Token-Overlap auf Titel/Snippet; max. ``max_notes`` (Default 30) fuer den
Classify-Prompt — spart Tokens und verbessert Append-Treffer.
"""

from __future__ import annotations

import logging
import re

from app.vault.reader import VaultNote

logger = logging.getLogger(__name__)

DEFAULT_MAX_NOTES = 30

# Kurze DE/EN-Stopwords — nicht als Match-Signal zaehlen.
_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "and",
        "or",
        "to",
        "of",
        "in",
        "on",
        "for",
        "is",
        "it",
        "my",
        "me",
        "i",
        "der",
        "die",
        "das",
        "und",
        "oder",
        "ein",
        "eine",
        "einer",
        "einem",
        "einen",
        "zu",
        "von",
        "im",
        "am",
        "mit",
        "auf",
        "fuer",
        "für",
        "ist",
        "ich",
        "mir",
        "mein",
        "meine",
        "noch",
        "mehr",
        "auch",
        "add",
        "bitte",
        "please",
    }
)

_TOKEN_RE = re.compile(r"[a-z0-9äöüß]{2,}", re.IGNORECASE)


def tokenize(text: str) -> set[str]:
    """Extrahiert Kleinbuchstaben-Tokens, ohne Stopwords."""
    tokens: set[str] = set()
    for match in _TOKEN_RE.finditer(text.lower()):
        tok = match.group(0)
        if tok not in _STOPWORDS:
            tokens.add(tok)
    return tokens


def score_note(note: VaultNote, query_tokens: set[str]) -> int:
    """Gewichtet Titel-Treffer hoeher als Snippet-Treffer."""
    if not query_tokens:
        return 0
    title_tokens = tokenize(note.title)
    snippet_tokens = tokenize(note.snippet)
    category_tokens = tokenize(f"{note.category} {note.folder}")
    score = 0
    for tok in query_tokens:
        if tok in title_tokens:
            score += 3
        if tok in snippet_tokens:
            score += 1
        if tok in category_tokens:
            score += 1
    return score


def prefilter_notes_for_llm(
    notes: list[VaultNote],
    query: str,
    *,
    max_notes: int = DEFAULT_MAX_NOTES,
) -> list[VaultNote]:
    """Waehlt die relevantesten Notizen fuer den Classify-Kontext.

    - Mit Query-Tokens: Notizen mit Score > 0 zuerst (Score absteigend),
      Luecken mit den uebrigen (Reihenfolge beibehalten = juengste zuerst) auffuellen.
    - Ohne Tokens oder leere Query: einfach die ersten ``max_notes``.
    """
    if max_notes <= 0:
        return []
    if len(notes) <= max_notes:
        return list(notes)

    query_tokens = tokenize(query)
    if not query_tokens:
        selected = notes[:max_notes]
        logger.debug(
            "Prefilter: keine Tokens — nehme %d juengste von %d",
            len(selected),
            len(notes),
        )
        return selected

    scored: list[tuple[int, int, VaultNote]] = []
    for idx, note in enumerate(notes):
        scored.append((score_note(note, query_tokens), -idx, note))

    scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
    matched = [note for score, _, note in scored if score > 0]
    if len(matched) >= max_notes:
        selected = matched[:max_notes]
    else:
        selected_ids = {id(n) for n in matched}
        filler = [n for n in notes if id(n) not in selected_ids]
        selected = matched + filler[: max_notes - len(matched)]

    logger.info(
        "Prefilter: %d/%d Notizen fuer LLM (Tokens=%d, Matches=%d)",
        len(selected),
        len(notes),
        len(query_tokens),
        len(matched),
    )
    return selected
