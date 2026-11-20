"""Validated application configuration for Agent Aarohi.

Configuration precedence: process environment > project .env file > safe defaults.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

_VALID_ENVIRONMENTS = {"development", "test", "production"}
_VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


class ConfigurationError(ValueError):
    """Raised when application configuration is invalid."""


def _load_dotenv(path: Path) -> None:
    """Load simple KEY=VALUE entries without overriding existing environment values."""
    if not path.is_file():
        return

    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ConfigurationError(f"Invalid .env entry at line {line_number}: expected KEY=VALUE")
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key or not key.replace("_", "").isalnum() or key[0].isdigit():
            raise ConfigurationError(f"Invalid .env key at line {line_number}")
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        os.environ.setdefault(key, value)


@dataclass(frozen=True, slots=True)
class Settings:
    """Immutable, validated settings used by the application."""

    environment: str
    log_level: str
    home: Path

    @property
    def database_path(self) -> Path:
        return self.home / "storage" / "aarohi.db"

    @property
    def log_dir(self) -> Path:
        return self.home / "logs"


def _discover_project_root() -> Path:
    """Find the source checkout root; fall back to the current directory when installed."""
    package_root = Path(__file__).resolve().parents[2]
    if (package_root / "pyproject.toml").is_file():
        return package_root
    return Path.cwd().resolve()


def load_settings(*, project_root: Path | None = None, load_env_file: bool = True) -> Settings:
    """Load settings from environment, optional project .env, and safe defaults."""
    root = (project_root or _discover_project_root()).expanduser().resolve()
    if load_env_file:
        _load_dotenv(root / ".env")

    environment = os.environ.get("AAROHI_ENV", "development").strip().lower()
    log_level = os.environ.get("AAROHI_LOG_LEVEL", "INFO").strip().upper()
    home_value = os.environ.get("AAROHI_HOME", str(root)).strip()

    if environment not in _VALID_ENVIRONMENTS:
        allowed = ", ".join(sorted(_VALID_ENVIRONMENTS))
        raise ConfigurationError(f"AAROHI_ENV must be one of: {allowed}")
    if log_level not in _VALID_LOG_LEVELS:
        allowed = ", ".join(sorted(_VALID_LOG_LEVELS))
        raise ConfigurationError(f"AAROHI_LOG_LEVEL must be one of: {allowed}")
    if not home_value:
        raise ConfigurationError("AAROHI_HOME cannot be empty")

    return Settings(
        environment=environment,
        log_level=log_level,
        home=Path(home_value).expanduser().resolve(),
    )
