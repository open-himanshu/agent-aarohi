import json
from datetime import UTC, datetime, timedelta

from aarohi.cli import main


def test_schedule_cli_add_list_and_run_due(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("AAROHI_HOME", str(tmp_path))
    now = datetime.now(UTC)
    assert main([
        "schedule", "add", "safe.daily",
        "--run-at", (now - timedelta(seconds=1)).isoformat(),
        "--every-seconds", "86400",
    ]) == 0
    assert "Schedule created:" in capsys.readouterr().out
    assert main(["schedule", "list"]) == 0
    schedules = json.loads(capsys.readouterr().out)
    assert len(schedules) == 1
    assert main(["schedule", "run-due"]) == 0
    jobs = json.loads(capsys.readouterr().out)
    assert len(jobs["enqueued_job_ids"]) == 1


def test_schedule_cli_requires_timezone(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("AAROHI_HOME", str(tmp_path))
    assert main(["schedule", "add", "handler", "--run-at", "2026-11-20T10:00:00"]) == 2
    assert "timezone" in capsys.readouterr().err
