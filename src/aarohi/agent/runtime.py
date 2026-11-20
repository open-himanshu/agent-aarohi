"""Minimal persistent task runtime; no arbitrary command execution."""
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from aarohi.database import connect, initialise
from aarohi.logging_config import redact_text
from aarohi.memory import MemoryManager, MemoryStore


def _now() -> str:
    return datetime.now(UTC).isoformat()


class AgentRuntime:
    def __init__(self, database_path: str | Path):
        self.database_path = Path(database_path)
        initialise(self.database_path)
        self.memory = MemoryStore(self.database_path)
        self.memory_manager = MemoryManager(self.memory)

    def remember(self, content: str, **metadata: object) -> str:
        """Save durable context through Aarohi's memory subsystem."""
        return self.memory.save(content, **metadata)

    def capture_memory(self, statement: str, *, source: str = "explicit user request", scope: str = "global") -> dict:
        """Capture only statements explicitly prefixed with a remember instruction."""
        return self.memory_manager.capture_explicit(statement, source=source, scope=scope)

    def recall(self, query: str, **filters: object) -> list[dict]:
        """Retrieve relevant active memories for a future task/context."""
        return self.memory.search(query, **filters)

    def build_context(self, query: str, *, scope: str | None = None, limit: int = 5, max_chars: int = 4000) -> list[dict]:
        return self.memory_manager.build_context(query, scope=scope, limit=limit, max_chars=max_chars)

    def submit(self, goal: str, *, memory_scope: str | None = None) -> str:
        goal = goal.strip()
        if not goal:
            raise ValueError("Goal cannot be empty")
        task_id, now = str(uuid4()), _now()
        context = self.build_context(goal, scope=memory_scope)
        with connect(self.database_path) as db:
            db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)",
                       (task_id, goal, "planned", now, now))
            db.execute(
                "INSERT INTO task_steps(task_id, position, description, status) VALUES (?, ?, ?, ?)",
                (task_id, 1, "Analyse the goal and define bounded execution steps", "pending"))
            db.execute(
                "INSERT INTO task_context(task_id, context_json, created_at) VALUES (?, ?, ?)",
                (task_id, json.dumps(context, ensure_ascii=False), now),
            )
            db.execute(
                "INSERT INTO audit_events(task_id, event, details, created_at) VALUES (?, ?, ?, ?)",
                (task_id, "task.submitted", redact_text(goal), now))
        return task_id

    def list_tasks(self) -> list[dict]:
        with connect(self.database_path) as db:
            rows = db.execute(
                "SELECT id, goal, status, created_at FROM tasks ORDER BY created_at DESC"
            ).fetchall()
        return [dict(row) for row in rows]

    def get_task(self, task_id: str) -> dict | None:
        with connect(self.database_path) as db:
            row = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
            if row is None:
                return None
            task = dict(row)
            task["steps"] = [dict(step) for step in db.execute(
                "SELECT position, description, status FROM task_steps WHERE task_id = ? ORDER BY position",
                (task_id,)).fetchall()]
            context_row = db.execute(
                "SELECT context_json FROM task_context WHERE task_id = ?", (task_id,)
            ).fetchone()
            task["memory_context"] = json.loads(context_row["context_json"]) if context_row else []
        return task
