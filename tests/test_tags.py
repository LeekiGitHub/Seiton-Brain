from app.llm.tags import merge_tags, normalize_tags


def test_normalize_tags_lowercases_and_trims():
    assert normalize_tags(["  Idea  ", "FITNESS"]) == ["idea", "fitness"]


def test_normalize_tags_strips_hash_and_spaces():
    assert normalize_tags(["#side project", "fun stuff"]) == [
        "side-project",
        "fun-stuff",
    ]


def test_normalize_tags_deduplicates_preserving_order():
    assert normalize_tags(["a", "b", "a", "B"]) == ["a", "b"]


def test_normalize_tags_drops_unrecoverable():
    assert normalize_tags(["", "   ", "#", "ok", None]) == ["ok"]  # type: ignore[list-item]


def test_normalize_tags_caps_to_max():
    assert normalize_tags(["a", "b", "c", "d"], max_tags=2) == ["a", "b"]


def test_merge_tags_keeps_existing_first():
    assert merge_tags(["a", "b"], ["c", "b"]) == ["a", "b", "c"]


def test_merge_tags_normalizes_both_sides():
    assert merge_tags(["#Old"], ["new tag", "OLD"]) == ["old", "new-tag"]


def test_merge_tags_caps_to_max():
    assert merge_tags(["a", "b"], ["c", "d"], max_tags=3) == ["a", "b", "c"]


def test_merge_tags_empty_inputs():
    assert merge_tags([], []) == []
    assert merge_tags(["a"], []) == ["a"]
    assert merge_tags([], ["b"]) == ["b"]
