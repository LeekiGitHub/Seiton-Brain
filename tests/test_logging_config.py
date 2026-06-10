import json
import logging

import pytest

from app.logging_config import (
    JsonLogFormatter,
    LogContextFilter,
    TextLogFormatter,
    bind_log_context,
    clear_log_context,
    configure_logging,
)


@pytest.fixture(autouse=True)
def _reset_log_context():
    clear_log_context()
    yield
    clear_log_context()


def test_json_formatter_emits_valid_json_with_context():
    bind_log_context(task_id="abc-123", telegram_update_id=42)
    record = logging.LogRecord(
        name="app.worker.tasks",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="hello",
        args=(),
        exc_info=None,
    )
    LogContextFilter().filter(record)
    line = JsonLogFormatter().format(record)
    data = json.loads(line)
    assert data["level"] == "INFO"
    assert data["logger"] == "app.worker.tasks"
    assert data["message"] == "hello"
    assert data["task_id"] == "abc-123"
    assert data["telegram_update_id"] == 42
    assert "timestamp" in data


def test_json_formatter_includes_exception():
    try:
        raise ValueError("boom")
    except ValueError:
        import sys

        exc_info = sys.exc_info()
    record = logging.LogRecord(
        name="test",
        level=logging.ERROR,
        pathname=__file__,
        lineno=1,
        msg="failed",
        args=(),
        exc_info=exc_info,
    )
    data = json.loads(JsonLogFormatter().format(record))
    assert "exception" in data
    assert "ValueError" in data["exception"]


def test_text_formatter_appends_context_suffix():
    bind_log_context(request_id="req-1")
    record = logging.LogRecord(
        name="app.main",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="ok",
        args=(),
        exc_info=None,
    )
    LogContextFilter().filter(record)
    formatted = TextLogFormatter("%(message)s").format(record)
    assert formatted == "ok [request_id=req-1]"


def test_configure_logging_json_mode(monkeypatch, capsys):
    monkeypatch.setattr("app.logging_config.settings.log_json", True)
    monkeypatch.setattr("app.logging_config.settings.log_level", "INFO")

    configure_logging()
    logging.getLogger("test.seiton").info("ping")

    out = capsys.readouterr().out.strip()
    data = json.loads(out)
    assert data["message"] == "ping"


def test_configure_logging_text_mode(monkeypatch, capsys):
    monkeypatch.setattr("app.logging_config.settings.log_json", False)
    monkeypatch.setattr("app.logging_config.settings.log_level", "INFO")

    configure_logging()
    bind_log_context(task_id="t-99")
    logging.getLogger("test.seiton").info("plain")

    out = capsys.readouterr().out
    assert "plain" in out
    assert "task_id=t-99" in out


def test_clear_log_context_removes_fields():
    bind_log_context(task_id="x", request_id="y")
    clear_log_context()

    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="m",
        args=(),
        exc_info=None,
    )
    LogContextFilter().filter(record)
    assert not hasattr(record, "task_id") or getattr(record, "task_id", None) is None
