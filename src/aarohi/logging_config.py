"""Structured, rotating and secret-aware application logging."""
from __future__ import annotations

import json
import logging
import re
from datetime import UTC, datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

_SECRET_KEY = re.compile(r"(password|passwd|secret|token|api[_-]?key|authorization|access[_-]?key)", re.IGNORECASE)
_SECRET_ASSIGNMENT = re.compile(
    r"(?i)\b(password|passwd|secret|token|api[_-]?key|authorization|access[_-]?key)\b(\s*[:=]\s*)([^\s,;]+)"
)
_BEARER = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/-]+=*")
_PROVIDER_KEY = re.compile(r"\b(sk-[A-Za-z0-9_-]{8,})\b")
_REDACTED = "[REDACTED]"


def redact_text(value: str) -> str:
    """Redact common credential patterns from arbitrary text."""
    value = _SECRET_ASSIGNMENT.sub(lambda m: f"{m.group(1)}{m.group(2)}{_REDACTED}", value)
    value = _BEARER.sub(f"Bearer {_REDACTED}", value)
    return _PROVIDER_KEY.sub(_REDACTED, value)


def redact_data(value: Any) -> Any:
    """Recursively redact sensitive mapping values and strings."""
    if isinstance(value, dict):
        return {
            str(key): _REDACTED if _SECRET_KEY.search(str(key)) else redact_data(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [redact_data(item) for item in value]
    if isinstance(value, str):
        return redact_text(value)
    return value


class JsonFormatter(logging.Formatter):
    """Emit one JSON object per log record, with sensitive data redacted."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": redact_text(record.getMessage()),
        }
        standard_keys = set(logging.LogRecord(None, 0, "", 0, "", (), None).__dict__)
        extras = {
            key: value for key, value in record.__dict__.items()
            if key not in standard_keys and not key.startswith("_")
        }
        payload.update(redact_data(extras))
        if record.exc_info:
            payload["exception"] = redact_text(self.formatException(record.exc_info))
        if record.stack_info:
            payload["stack"] = redact_text(self.formatStack(record.stack_info))
        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging(
    *, log_dir: str | Path, level: str = "INFO", max_bytes: int = 5_000_000, backup_count: int = 5
) -> logging.Logger:
    """Configure Aarohi's root logger with console and rotating JSON file handlers."""
    numeric_level = logging.getLevelName(level.upper())
    if not isinstance(numeric_level, int):
        raise ValueError(f"Unsupported logging level: {level}")  # noqa: TRY004
    if max_bytes <= 0 or backup_count < 0:
        raise ValueError("max_bytes must be positive and backup_count cannot be negative")

    target = Path(log_dir)
    target.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("aarohi")
    logger.setLevel(numeric_level)
    logger.propagate = False

    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()

    formatter = JsonFormatter()
    console = logging.StreamHandler()
    console.setLevel(numeric_level)
    console.setFormatter(formatter)
    file_handler = RotatingFileHandler(
        target / "aarohi.log", maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(console)
    logger.addHandler(file_handler)
    return logger


def get_logger(name: str) -> logging.Logger:
    """Return a logger within the Aarohi namespace."""
    return logging.getLogger(name if name.startswith("aarohi") else f"aarohi.{name}")
