"""Tag normalization — shared between LLM provider and vault writer.

We stay tolerant: anything unsalvageable (empty, symbols only) is dropped.
Deliberately no hard-fail — tag quality is cosmetic.
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
    """Merge existing and new tags, dedupe, preserve order.

    Existing tags first (user may have edited them manually); new tags only
    if not already present. Both sides are normalized first.
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
