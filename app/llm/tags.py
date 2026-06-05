"""Tag-Normalisierung — geteilt zwischen LLM-Provider und Vault-Writer.

Wir bleiben tolerant: was nicht zu retten ist (leer, nur Sonderzeichen) wird
verworfen. Bewusst kein Hard-Fail — Tag-Qualitaet ist Cosmetic.
"""


def normalize_tags(raw_tags: list[str], max_tags: int | None = None) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for raw in raw_tags:
        if not isinstance(raw, str):
            continue
        tag = raw.strip().lstrip("#").lower()
        tag = "-".join(tag.split())
        tag = "".join(ch for ch in tag if ch.isalnum() or ch in "-_")
        if not tag or tag in seen:
            continue
        seen.add(tag)
        cleaned.append(tag)
    if max_tags is not None:
        return cleaned[:max_tags]
    return cleaned


def merge_tags(
    existing: list[str], incoming: list[str], max_tags: int | None = None
) -> list[str]:
    """Vereinigt bestehende und neue Tags, deduppt, behaelt Reihenfolge.

    Bestehende Tags zuerst (Nutzer hat sie evtl. manuell editiert), neue Tags
    nur falls noch nicht enthalten. Beide werden vorher normalisiert.
    """
    normalized_existing = normalize_tags(existing)
    normalized_incoming = normalize_tags(incoming)
    merged: list[str] = []
    seen: set[str] = set()
    for tag in normalized_existing + normalized_incoming:
        if tag not in seen:
            seen.add(tag)
            merged.append(tag)
    if max_tags is not None:
        return merged[:max_tags]
    return merged
