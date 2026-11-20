import json

from aarohi.cli import main
from aarohi.memory import MemoryStore


def _memory_id(tmp_path, monkeypatch):
    monkeypatch.setenv("AAROHI_HOME", str(tmp_path))
    store = MemoryStore(tmp_path / "storage" / "aarohi.db")
    return store.save(
        "User prefers concise technical answers",
        category="preference", scope="global", source="user", confirmed=True,
    )


def test_memory_list_and_search_cli(tmp_path, monkeypatch, capsys):
    memory_id = _memory_id(tmp_path, monkeypatch)

    main(["memory", "list"])
    listed = json.loads(capsys.readouterr().out)
    assert [item["id"] for item in listed] == [memory_id]

    main(["memory", "search", "concise answers"])
    searched = json.loads(capsys.readouterr().out)
    assert searched[0]["id"] == memory_id


def test_memory_update_cli_validates_and_updates(tmp_path, monkeypatch, capsys):
    memory_id = _memory_id(tmp_path, monkeypatch)

    main(["memory", "update", memory_id, "--content", "User prefers concise Hinglish answers", "--no-confirmed"])
    assert "Memory updated" in capsys.readouterr().out

    record = MemoryStore(tmp_path / "storage" / "aarohi.db").get(memory_id)
    assert record["content"] == "User prefers concise Hinglish answers"
    assert record["confirmed"] is False


def test_memory_archive_is_hidden_unless_requested(tmp_path, monkeypatch, capsys):
    memory_id = _memory_id(tmp_path, monkeypatch)

    main(["memory", "archive", memory_id])
    assert "Memory archived" in capsys.readouterr().out

    main(["memory", "list"])
    assert json.loads(capsys.readouterr().out) == []

    main(["memory", "list", "--include-archived"])
    records = json.loads(capsys.readouterr().out)
    assert records[0]["status"] == "archived"


def test_memory_forget_requires_exact_confirmation(tmp_path, monkeypatch, capsys):
    memory_id = _memory_id(tmp_path, monkeypatch)
    monkeypatch.setattr("builtins.input", lambda _: "wrong-id")

    main(["memory", "forget", memory_id])
    assert "Deletion cancelled" in capsys.readouterr().out
    assert MemoryStore(tmp_path / "storage" / "aarohi.db").get(memory_id) is not None


def test_memory_forget_yes_is_explicit_and_permanent(tmp_path, monkeypatch, capsys):
    memory_id = _memory_id(tmp_path, monkeypatch)

    main(["memory", "forget", memory_id, "--yes"])
    assert "permanently deleted" in capsys.readouterr().out
    assert MemoryStore(tmp_path / "storage" / "aarohi.db").get(memory_id) is None


def test_forget_scrubs_memory_from_existing_task_context(tmp_path):
    from aarohi.agent.runtime import AgentRuntime

    database = tmp_path / "aarohi.db"
    runtime = AgentRuntime(database)
    memory_id = runtime.remember(
        "WealthCodeX uses Hinglish Roman script",
        category="decision", scope="wealthcodex", source="user", confirmed=True,
    )
    task_id = runtime.submit("Prepare a WealthCodeX Hinglish script", memory_scope="wealthcodex")
    assert runtime.get_task(task_id)["memory_context"][0]["id"] == memory_id

    assert runtime.memory.forget(memory_id) is True
    assert AgentRuntime(database).get_task(task_id)["memory_context"] == []
