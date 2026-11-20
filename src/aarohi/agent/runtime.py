"""Minimal persistent task runtime; no arbitrary command execution."""
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from aarohi.database import connect, initialise

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

class AgentRuntime:
    def __init__(self, database_path: str | Path):
        self.database_path = Path(database_path)
        initialise(self.database_path)

    def submit(self, goal: str) -> str:
        goal = goal.strip()
        if not goal:
            raise ValueError("Goal cannot be empty")
        task_id, now = str(uuid4()), _now()
        with connect(self.database_path) as db:
            db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)",
                       (task_id, goal, "planned", now, now))
            db.execute(
                "INSERT INTO task_steps(task_id, position, description, status) VALUES (?, ?, ?, ?)",
                (task_id, 1, "Analyse the goal and define bounded execution steps", "pending"))
            db.execute(
                "INSERT INTO audit_events(task_id, event, details, created_at) VALUES (?, ?, ?, ?)",
                (task_id, "task.submitted", goal, now))
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
        return task
