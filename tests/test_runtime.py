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
