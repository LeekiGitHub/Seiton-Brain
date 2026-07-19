"""Tests fuer Vault-Prefilter vor LLM (E5-2)."""

from app.config import settings
from app.vault.prefilter import prefilter_notes_for_llm, score_note, tokenize
from app.vault.reader import VaultNote


def _note(title: str, snippet: str = "", category: str = "note") -> VaultNote:
    return VaultNote(title=title, category=category, folder="Notes", snippet=snippet)


def test_tokenize_drops_stopwords():
    tokens = tokenize("Bitte mehr zur Fitness App und Workout")
    assert "fitness" in tokens
    assert "app" in tokens
    assert "workout" in tokens
    assert "und" not in tokens
    assert "bitte" not in tokens


def test_score_prefers_title_matches():
    query = tokenize("fitness workout")
    titled = _note("Fitness App", "something else")
    snipped = _note("Random", "daily fitness workout log")
    assert score_note(titled, query) > score_note(snipped, query)


def test_prefilter_caps_at_max_notes():
    notes = [_note(f"Note {i}", f"body {i}") for i in range(50)]
    selected = prefilter_notes_for_llm(notes, "hello world", max_notes=30)
    assert len(selected) == 30


def test_prefilter_ranks_matching_notes_first():
    notes = [
        _note("Alpha", "unrelated"),
        _note("Japan Trip", "tokyo kyoto travel"),
        _note("Beta", "noise"),
        _note("Tokyo Food", "ramen"),
    ]
    selected = prefilter_notes_for_llm(notes, "Japan Tokyo travel", max_notes=2)
    titles = [n.title for n in selected]
    assert "Japan Trip" in titles
    assert "Tokyo Food" in titles


def test_prefilter_fills_with_recent_when_few_matches():
    notes = [_note(f"Note {i}") for i in range(10)]
    notes[7] = _note("Fitness Plan", "gym")
    selected = prefilter_notes_for_llm(notes, "fitness gym", max_notes=5)
    assert selected[0].title == "Fitness Plan"
    assert len(selected) == 5


def test_prefilter_empty_query_takes_prefix():
    notes = [_note(f"Note {i}") for i in range(40)]
    selected = prefilter_notes_for_llm(notes, "   ", max_notes=30)
    assert [n.title for n in selected] == [f"Note {i}" for i in range(30)]


def test_default_config_limit():
    assert settings.seiton_llm_note_limit == 30
