import pytest

from aarohi.agent.runtime import AgentRuntime
from aarohi.memory import MemoryManager, MemoryStore


def test_capture_requires_explicit_remember_instruction(tmp_path):
    manager = MemoryManager(MemoryStore(tmp_path / "aarohi.db"))

    ignored = manager.capture_explicit("I prefer short answers")
    saved = manager.capture_explicit("Remember that I prefer short answers")
    hinglish = manager.capture_explicit("Yaad rakhna, mujhe concise answers pasand hain")

    assert ignored["status"] == "ignored"
    assert saved["status"] == "saved"
    assert hinglish["status"] == "saved"
    assert saved["memory_id"]


def test_similar_memory_requires_review_and_explicit_replacement(tmp_path):
    store = MemoryStore(tmp_path / "aarohi.db")
    first = store.curate(
        "WealthCodeX uses Hinglish Roman script",
        category="fact", scope="wealthcodex", source="user", confirmed=True,
    )
    assert first["status"] == "saved"

    candidate = store.curate(
        "WealthCodeX uses English Roman script",
        category="fact", scope="wealthcodex", source="user correction", confirmed=True,
    )
    assert candidate["status"] == "needs_review"
    assert candidate["candidates"][0]["id"] == first["memory_id"]

    updated = store.curate(
        "WealthCodeX uses English Roman script",
        category="fact", scope="wealthcodex", source="user correction",
        confirmed=True, replace_id=first["memory_id"],
    )
    assert updated["status"] == "updated"
    assert store.get(first["memory_id"])["content"] == "WealthCodeX uses English Roman script"


def test_context_assembly_is_relevant_scoped_and_bounded(tmp_path):
    store = MemoryStore(tmp_path / "aarohi.db")
    store.save(
        "WealthCodeX publishes Hinglish Roman script videos",
        category="decision", scope="wealthcodex", source="user", confirmed=True,
    )
    store.save(
        "Aarohi is a local-first personal AI agent",
        category="decision", scope="aarohi", source="user", confirmed=True,
    )
    manager = MemoryManager(store)

    context = manager.build_context("WealthCodeX Hinglish", scope="wealthcodex")

    assert len(context) == 1
    assert context[0]["scope"] == "wealthcodex"
    with pytest.raises(ValueError, match="max_chars"):
        manager.build_context("WealthCodeX", max_chars=50)


def test_task_submission_persists_memory_context_snapshot(tmp_path):
    database = tmp_path / "aarohi.db"
    runtime = AgentRuntime(database)
    runtime.remember(
        "WealthCodeX uses Hinglish Roman script",
        category="decision", scope="wealthcodex", source="user", confirmed=True,
    )

    task_id = runtime.submit("Prepare a WealthCodeX Hinglish script", memory_scope="wealthcodex")
    task = AgentRuntime(database).get_task(task_id)

    assert task is not None
    assert len(task["memory_context"]) == 1
    assert task["memory_context"][0]["content"] == "WealthCodeX uses Hinglish Roman script"


def test_explicit_memory_capture_rejects_secret_like_content(tmp_path):
    manager = MemoryManager(MemoryStore(tmp_path / "aarohi.db"))

    with pytest.raises(ValueError, match="credentials"):
        manager.capture_explicit("Remember that api_key=sk-example-secret-value")
