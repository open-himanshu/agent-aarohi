import pytest

from aarohi.agent.runtime import AgentRuntime
from aarohi.security.policy import Risk, authorise
from aarohi.tools.registry import ToolRegistry, ToolSpec


def test_submit_persists_task(tmp_path):
    runtime = AgentRuntime(tmp_path / "aarohi.db")
    task_id = runtime.submit("Research battery recycling in India")
    task = runtime.get_task(task_id)
    assert task is not None
    assert task["status"] == "planned"
    assert task["steps"][0]["status"] == "pending"

def test_empty_goal_rejected(tmp_path):
    runtime = AgentRuntime(tmp_path / "aarohi.db")
    with pytest.raises(ValueError):
        runtime.submit("  ")

def test_policy_requires_approval():
    assert authorise(Risk.READ).allowed
    assert not authorise(Risk.REVERSIBLE).allowed
    assert authorise(Risk.REVERSIBLE, approved=True).allowed
    assert not authorise(Risk.DESTRUCTIVE, approved=True).allowed

def test_registry_rejects_duplicate_tools():
    registry = ToolRegistry()
    tool = ToolSpec("clock", "Read current time", Risk.READ, lambda: "now")
    registry.register(tool)
    with pytest.raises(ValueError):
        registry.register(tool)


def test_runtime_memory_api_persists_and_recalls_context(tmp_path):
    database = tmp_path / "aarohi.db"
    runtime = AgentRuntime(database)
    runtime.remember(
        "WealthCodeX uses Hinglish Roman script",
        category="project_decision",
        scope="wealthcodex",
        source="user instruction",
        confirmed=True,
    )

    restarted_runtime = AgentRuntime(database)
    memories = restarted_runtime.recall("WealthCodeX Hinglish", scope="wealthcodex")

    assert len(memories) == 1
    assert memories[0]["confirmed"] is True


def test_task_submission_audit_redacts_common_secret_patterns(tmp_path):
    from aarohi.agent.runtime import AgentRuntime
    from aarohi.database import connect

    database = tmp_path / "audit.db"
    task_id = AgentRuntime(database).submit("Investigate password=hunter2")
    with connect(database) as db:
        details = db.execute(
            "SELECT details FROM audit_events WHERE task_id=? AND event='task.submitted'",
            (task_id,),
        ).fetchone()["details"]
    assert "hunter2" not in details
    assert "[REDACTED]" in details
