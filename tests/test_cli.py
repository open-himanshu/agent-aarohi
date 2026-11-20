from aarohi.cli import main


def test_about_command(capsys):
    main([])
    captured = capsys.readouterr()
    assert "Aarohi" in captured.out
    assert "personal AI agent" in captured.out
import json


def test_health_command_reports_db_queue_and_execution_disabled(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("AAROHI_HOME", str(tmp_path))
    monkeypatch.setenv("AAROHI_LOG_LEVEL", "ERROR")
    assert main(["health"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "healthy"
    assert report["database"]["healthy"] is True
    assert report["queue"] == {}
    assert report["enabled_schedules"] == 0
    assert report["execution_enabled"] is False


def test_invalid_queue_payload_returns_clean_error(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("AAROHI_HOME", str(tmp_path))
    monkeypatch.setenv("AAROHI_LOG_LEVEL", "CRITICAL")
    result = main(["queue", "enqueue", "demo.handler", "--payload", "{bad-json"])
    captured = capsys.readouterr()
    assert result == 2
    assert captured.out == ""
    assert captured.err.startswith("Error:")
    assert "Traceback" not in captured.err


def test_missing_database_task_is_reported_cleanly(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("AAROHI_HOME", str(tmp_path))
    monkeypatch.setenv("AAROHI_LOG_LEVEL", "CRITICAL")
    result = main(["show", "missing-task"])
    assert result == 0
    assert "Task not found" in capsys.readouterr().out
