"""Tests for structured logging and credential redaction."""
import json
import logging
from logging.handlers import RotatingFileHandler

import pytest

from aarohi.logging_config import configure_logging, redact_data, redact_text


@pytest.fixture
def isolated_logger(tmp_path):
    logger = configure_logging(log_dir=tmp_path / "logs", level="DEBUG")
    yield logger
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()


def test_writes_structured_json_to_file_and_console(tmp_path, isolated_logger):
    isolated_logger.info("Task accepted", extra={"task_id": "task-123", "attempt": 2})
    record = json.loads((tmp_path / "logs" / "aarohi.log").read_text(encoding="utf-8"))

    assert record["level"] == "INFO"
    assert record["message"] == "Task accepted"
    assert record["task_id"] == "task-123"
    assert any(type(handler) is logging.StreamHandler for handler in isolated_logger.handlers)


def test_redacts_sensitive_keys_and_inline_credentials(isolated_logger, tmp_path):
    isolated_logger.info(
        "Calling provider", extra={"api_key": "private-value", "endpoint": "https://example.test"}
    )
    content = (tmp_path / "logs" / "aarohi.log").read_text(encoding="utf-8")

    assert "private-value" not in content
    assert "[REDACTED]" in content


def test_redacts_common_secret_patterns():
    text = "password=hunter2 Bearer abc.def sk-1234567890abcdef token:abc123"
    safe = redact_text(text)

    assert "hunter2" not in safe
    assert "abc.def" not in safe
    assert "1234567890abcdef" not in safe
    assert "abc123" not in safe


def test_recursively_redacts_nested_data():
    safe = redact_data({"metadata": [{"access_token": "secret-value"}], "label": "ok"})

    assert safe == {"metadata": [{"access_token": "[REDACTED]"}], "label": "ok"}


def test_rotating_file_handler_is_configured(isolated_logger):
    handler = next(h for h in isolated_logger.handlers if isinstance(h, RotatingFileHandler))

    assert handler.maxBytes == 5_000_000
    assert handler.backupCount == 5


def test_invalid_level_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="Unsupported logging level"):
        configure_logging(log_dir=tmp_path, level="TRACE")
