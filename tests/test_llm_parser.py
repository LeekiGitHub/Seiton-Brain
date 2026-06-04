from app.llm.openai_provider import OpenAIProvider
from app.llm.schemas import ClassificationResult
from app.vault.reader import VaultNote


def _provider() -> OpenAIProvider:
    return OpenAIProvider.__new__(OpenAIProvider)


def test_sanitize_related_keeps_valid_titles():
    provider = _provider()
    existing = [
        VaultNote(title="Fitness App", category="idea", folder="Ideas", snippet=""),
        VaultNote(title="Other Note", category="note", folder="Notes", snippet=""),
    ]
    result = ClassificationResult(
        category="idea",
        title="Workout Tracker",
        summary="More fitness thoughts.",
        related=["fitness app", "Unknown Note"],
    )

    sanitized = provider._sanitize_related(result, existing)
    assert sanitized.related == ["Fitness App"]


def test_sanitize_related_excludes_self():
    provider = _provider()
    existing = [
        VaultNote(title="Same Title", category="idea", folder="Ideas", snippet=""),
    ]
    result = ClassificationResult(
        category="idea",
        title="Same Title",
        summary="Duplicate.",
        related=["Same Title"],
    )

    sanitized = provider._sanitize_related(result, existing)
    assert sanitized.related == []


def test_sanitize_related_limits_to_three():
    provider = _provider()
    existing = [
        VaultNote(title=f"Note {i}", category="note", folder="Notes", snippet="")
        for i in range(5)
    ]
    result = ClassificationResult(
        category="note",
        title="New Note",
        summary="Links.",
        related=[f"Note {i}" for i in range(5)],
    )

    sanitized = provider._sanitize_related(result, existing)
    assert len(sanitized.related) == 3


def test_classification_result_defaults_related():
    result = ClassificationResult(
        category="note",
        title="Test",
        summary="Summary.",
    )
    assert result.related == []
    assert result.action == "create"
    assert result.target_title is None


def test_sanitize_action_keeps_valid_append():
    provider = _provider()
    existing = [
        VaultNote(title="Fitness App", category="idea", folder="Ideas", snippet=""),
    ]
    result = ClassificationResult(
        category="idea",
        title="Add workout log",
        summary="More features.",
        action="append",
        target_title="fitness app",
    )

    sanitized = provider._sanitize_action(result, existing)
    assert sanitized.action == "append"
    assert sanitized.target_title == "Fitness App"


def test_sanitize_action_falls_back_when_target_missing():
    provider = _provider()
    existing = [
        VaultNote(title="Real Note", category="note", folder="Notes", snippet=""),
    ]
    result = ClassificationResult(
        category="idea",
        title="Something",
        summary="...",
        action="append",
        target_title="Halluzinierter Titel",
    )

    sanitized = provider._sanitize_action(result, existing)
    assert sanitized.action == "create"
    assert sanitized.target_title is None


def test_sanitize_action_falls_back_when_target_empty():
    provider = _provider()
    result = ClassificationResult(
        category="note",
        title="X",
        summary="Y",
        action="append",
        target_title=None,
    )

    sanitized = provider._sanitize_action(result, [])
    assert sanitized.action == "create"


def test_sanitize_action_clears_target_for_create():
    provider = _provider()
    result = ClassificationResult(
        category="note",
        title="X",
        summary="Y",
        action="create",
        target_title="Some Title",
    )

    sanitized = provider._sanitize_action(result, [])
    assert sanitized.target_title is None
