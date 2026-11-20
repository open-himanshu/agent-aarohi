"""Tests for validated application configuration."""
import pytest

from aarohi.config import ConfigurationError, load_settings


def test_defaults_are_safe_and_use_project_root(tmp_path, monkeypatch):
    monkeypatch.delenv("AAROHI_ENV", raising=False)
    monkeypatch.delenv("AAROHI_LOG_LEVEL", raising=False)
    monkeypatch.delenv("AAROHI_HOME", raising=False)

    settings = load_settings(project_root=tmp_path, load_env_file=False)

    assert settings.environment == "development"
    assert settings.log_level == "INFO"
    assert settings.home == tmp_path.resolve()
    assert settings.database_path == tmp_path.resolve() / "storage" / "aarohi.db"


def test_environment_values_override_dotenv(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("AAROHI_ENV=test\nAAROHI_LOG_LEVEL=DEBUG\n", encoding="utf-8")
    monkeypatch.setenv("AAROHI_ENV", "production")
    monkeypatch.delenv("AAROHI_LOG_LEVEL", raising=False)

    settings = load_settings(project_root=tmp_path)

    assert settings.environment == "production"
    assert settings.log_level == "DEBUG"


def test_invalid_environment_is_rejected(tmp_path, monkeypatch):
    monkeypatch.setenv("AAROHI_ENV", "prod-ish")

    with pytest.raises(ConfigurationError, match="AAROHI_ENV"):
        load_settings(project_root=tmp_path, load_env_file=False)


def test_invalid_log_level_is_rejected(tmp_path, monkeypatch):
    monkeypatch.delenv("AAROHI_ENV", raising=False)
    monkeypatch.setenv("AAROHI_LOG_LEVEL", "TRACE")

    with pytest.raises(ConfigurationError, match="AAROHI_LOG_LEVEL"):
        load_settings(project_root=tmp_path, load_env_file=False)


def test_dotenv_does_not_override_existing_environment(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("AAROHI_LOG_LEVEL=ERROR\n", encoding="utf-8")
    monkeypatch.setenv("AAROHI_LOG_LEVEL", "WARNING")
    monkeypatch.delenv("AAROHI_ENV", raising=False)

    settings = load_settings(project_root=tmp_path)

    assert settings.log_level == "WARNING"


def test_default_home_is_independent_of_working_directory(tmp_path, monkeypatch):
    from aarohi import config

    monkeypatch.delenv("AAROHI_HOME", raising=False)
    monkeypatch.delenv("AAROHI_ENV", raising=False)
    monkeypatch.delenv("AAROHI_LOG_LEVEL", raising=False)
    monkeypatch.chdir(tmp_path)

    expected_root = config.Path(config.__file__).resolve().parents[2]
    if (expected_root / "pyproject.toml").is_file():
        assert config.load_settings(load_env_file=False).home == expected_root
    else:
        assert config.load_settings(load_env_file=False).home == tmp_path.resolve()
