import pytest

from aarohi.memory import MemoryStore


def test_memory_survives_store_restart(tmp_path):
    database = tmp_path / "aarohi.db"
    first = MemoryStore(database)
    memory_id = first.save(
        "User prefers concise technical explanations",
        category="preference",
        source="user statement",
        confirmed=True,
    )

    second = MemoryStore(database)
    result = second.get(memory_id)

    assert result is not None
    assert result["content"] == "User prefers concise technical explanations"
    assert result["confirmed"] is True
    assert result["source"] == "user statement"


def test_search_ranks_and_filters_memories(tmp_path):
    store = MemoryStore(tmp_path / "aarohi.db")
    store.save("Aarohi is a local-first AI agent", category="decision", source="project spec", scope="aarohi", confirmed=True)
    store.save("User likes concise answers", category="preference", source="user", scope="global", confirmed=True)
    store.save("Old unconfirmed Aarohi concept", category="idea", source="assistant inference", scope="aarohi")

    results = store.search("Aarohi local-first agent", scope="aarohi", confirmed_only=True)

    assert len(results) == 1
    assert results[0]["category"] == "decision"


def test_update_archive_and_forget(tmp_path):
    store = MemoryStore(tmp_path / "aarohi.db")
    memory_id = store.save("Initial project name", source="user")

    assert store.update(memory_id, content="Updated project name", confirmed=True)
    assert store.get(memory_id)["content"] == "Updated project name"
    assert store.archive(memory_id)
    assert store.search("Updated project name") == []
    assert store.forget(memory_id)
    assert store.get(memory_id) is None


def test_rejects_empty_or_secret_like_content(tmp_path):
    store = MemoryStore(tmp_path / "aarohi.db")
    with pytest.raises(ValueError):
        store.save("  ", source="user")
    with pytest.raises(ValueError, match="credentials"):
        store.save("api_key=sk-example-secret-value", source="user")


def test_validates_confidence_and_search_limit(tmp_path):
    store = MemoryStore(tmp_path / "aarohi.db")
    with pytest.raises(ValueError, match="confidence"):
        store.save("A fact", source="user", confidence=1.5)
    with pytest.raises(ValueError, match="limit"):
        store.search("fact", limit=101)


def test_update_rejects_unknown_fields(tmp_path):
    store = MemoryStore(tmp_path / "aarohi.db")
    memory_id = store.save("A fact", source="user")
    with pytest.raises(ValueError, match="Unsupported"):
        store.update(memory_id, arbitrary="value")
