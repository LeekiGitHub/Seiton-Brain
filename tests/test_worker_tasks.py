"""Tests fuer Worker-Tasks — Retry-Konfiguration und Fehler-Pfade.

Wir simulieren Celery's Retry-Mechanik nicht End-to-End (das ist Job des
Celery-Workers selbst), sondern pruefen:

1. dass die Tasks ueberhaupt mit den richtigen Retry-Kwargs konfiguriert sind
2. dass die transienten Exceptions in der Retry-Liste stehen
3. dass eine ``Retry``-Exception NICHT zur "Etwas ist schiefgelaufen"-
   Telegram-Meldung fuehrt (sonst Spam bei jedem Retry)
4. dass nicht-retryable Exceptions zur Fehlermeldung fuehren
"""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from celery.exceptions import Retry
from openai import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    RateLimitError,
)

from app.llm.schemas import AnswerResult, NoteRef
from app.worker.tasks import (
    RETRY_KWARGS,
    RETRYABLE_EXCEPTIONS,
    _process_ask,
    process_ask_message_task,
    process_text_message_task,
    process_voice_message_task,
)


def test_retry_kwargs_have_sensible_defaults():
    assert RETRY_KWARGS["max_retries"] == 3
    assert RETRY_KWARGS["retry_backoff"] is True
    assert RETRY_KWARGS["retry_backoff_max"] == 60
    assert RETRY_KWARGS["retry_jitter"] is True
    assert RETRY_KWARGS["autoretry_for"] is RETRYABLE_EXCEPTIONS


def test_retryable_exceptions_cover_openai_transient_errors():
    assert RateLimitError in RETRYABLE_EXCEPTIONS
    assert APITimeoutError in RETRYABLE_EXCEPTIONS
    assert APIConnectionError in RETRYABLE_EXCEPTIONS
    assert APIError in RETRYABLE_EXCEPTIONS


def test_retryable_exceptions_cover_network_errors():
    assert httpx.HTTPError in RETRYABLE_EXCEPTIONS
    assert ConnectionError in RETRYABLE_EXCEPTIONS
    assert TimeoutError in RETRYABLE_EXCEPTIONS


def test_text_task_is_registered_with_retry_config():
    task = process_text_message_task
    assert task.max_retries == 3
    assert task.retry_backoff is True
    assert task.retry_backoff_max == 60
    assert task.retry_jitter is True
    assert RateLimitError in task.autoretry_for


def test_voice_task_is_registered_with_retry_config():
    task = process_voice_message_task
    assert task.max_retries == 3
    assert RateLimitError in task.autoretry_for


def _close_coro_and_raise(exc: BaseException):
    """Hilfs-Side-Effect: schliesst die uebergebene Coroutine sauber
    (vermeidet "coroutine was never awaited"-Warnings) und raised dann.
    """

    def side_effect(coro):
        if hasattr(coro, "close"):
            coro.close()
        raise exc

    return side_effect


@patch("app.worker.tasks._handle_permanent_failure")
@patch("app.worker.tasks._run")
def test_text_task_does_not_send_error_on_retry(mock_run, mock_handle_failure):
    """Beim Celery-Retry darf der User keine Fehler-Meldung sehen — er
    bekommt sie nur, wenn alle Versuche erschoepft sind."""
    mock_run.side_effect = _close_coro_and_raise(Retry())

    with pytest.raises(Retry):
        process_text_message_task.run("hi", 42)

    mock_handle_failure.assert_not_called()


@patch("app.worker.tasks._handle_permanent_failure")
@patch("app.worker.tasks._run")
def test_text_task_sends_error_on_permanent_failure(mock_run, mock_handle_failure):
    """Bei nicht-retryable Exception bekommt der User die Fehlermeldung."""
    call_count = {"n": 0}

    def side_effect(coro):
        if hasattr(coro, "close"):
            coro.close()
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise ValueError("boom — programming error, no retry")

    mock_run.side_effect = side_effect

    with pytest.raises(ValueError):
        process_text_message_task.run("hi", 42)

    # _run wurde 2x aufgerufen: einmal fuer _process_text (failt), einmal
    # fuer _handle_permanent_failure
    assert call_count["n"] == 2
    mock_handle_failure.assert_called_once()
    kwargs = mock_handle_failure.call_args.kwargs
    assert mock_handle_failure.call_args.args[0] == 42
    assert isinstance(mock_handle_failure.call_args.args[1], ValueError)
    assert kwargs["task_name"] == "process_text_message"


@patch("app.worker.tasks._handle_permanent_failure")
@patch("app.worker.tasks._run")
def test_voice_task_does_not_send_error_on_retry(mock_run, mock_handle_failure):
    mock_run.side_effect = _close_coro_and_raise(Retry())

    with pytest.raises(Retry):
        process_voice_message_task.run("voice123", 42)

    mock_handle_failure.assert_not_called()


# ─── E17-4: /ask RAG-Task ────────────────────────────────────────────────


def test_ask_task_is_registered_with_retry_config():
    task = process_ask_message_task
    assert task.max_retries == 3
    assert task.retry_backoff is True
    assert RateLimitError in task.autoretry_for


@patch("app.worker.tasks._handle_permanent_failure")
@patch("app.worker.tasks._run")
def test_ask_task_does_not_send_error_on_retry(mock_run, mock_handle_failure):
    mock_run.side_effect = _close_coro_and_raise(Retry())

    with pytest.raises(Retry):
        process_ask_message_task.run("Was weiß ich über X?", 42)

    mock_handle_failure.assert_not_called()


@patch("app.worker.tasks._handle_permanent_failure")
@patch("app.worker.tasks._run")
def test_ask_task_sends_error_on_permanent_failure(mock_run, mock_handle_failure):
    call_count = {"n": 0}

    def side_effect(coro):
        if hasattr(coro, "close"):
            coro.close()
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise ValueError("boom — no retry")

    mock_run.side_effect = side_effect

    with pytest.raises(ValueError):
        process_ask_message_task.run("frage", 42)

    assert call_count["n"] == 2
    mock_handle_failure.assert_called_once()
    kwargs = mock_handle_failure.call_args.kwargs
    assert mock_handle_failure.call_args.args[0] == 42
    assert kwargs["task_name"] == "process_ask_message"
    assert kwargs["kind"] == "qa"


@pytest.mark.asyncio
@patch("app.worker.tasks.send_message", new_callable=AsyncMock)
@patch("app.worker.tasks.answer_question", new_callable=AsyncMock)
@patch("app.worker.tasks.worker_session")
async def test_process_ask_sends_formatted_answer(
    mock_session, mock_answer, mock_send
):
    db = AsyncMock()
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=db)
    cm.__aexit__ = AsyncMock(return_value=False)
    mock_session.return_value = cm
    mock_answer.return_value = AnswerResult(
        answer="Du warst in Tokio.",
        sources=[NoteRef(title="Japan Reiseroute", vault_path="Travel/Japan.md")],
        confidence=0.9,
    )

    await _process_ask("Wo war ich?", 42)

    mock_answer.assert_awaited_once_with("Wo war ich?", db)
    mock_send.assert_awaited_once()
    sent_text = mock_send.call_args[0][1]
    assert "Du warst in Tokio." in sent_text
    assert "[[Japan Reiseroute]]" in sent_text
