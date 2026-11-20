import json

from aarohi.cli import main


def test_queue_cli_enqueue_and_list(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("AAROHI_HOME", str(tmp_path))
    assert main(["init-db"]) == 0
    capsys.readouterr()

    assert main([
        "queue", "enqueue", "wealthcodex.research",
        "--payload", '{"topic":"gaming economy"}',
        "--idempotency-key", "daily-research-2026-11-20",
    ]) == 0
    output = capsys.readouterr().out
    assert "Job queued:" in output

    assert main(["queue", "list"]) == 0
    jobs = json.loads(capsys.readouterr().out)
    assert len(jobs) == 1
    assert jobs[0]["handler"] == "wealthcodex.research"
    assert jobs[0]["status"] == "queued"


def test_queue_cli_rejects_non_object_payload(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("AAROHI_HOME", str(tmp_path))
    assert main(["queue", "enqueue", "handler", "--payload", '["not", "object"]']) == 2
    assert "JSON object" in capsys.readouterr().err
