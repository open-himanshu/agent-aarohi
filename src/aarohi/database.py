"""SQLite persistence for tasks and append-only audit events."""
from pathlib import Path
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
 id TEXT PRIMARY KEY, goal TEXT NOT NULL, status TEXT NOT NULL,
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS task_steps (
 id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT NOT NULL,
 position INTEGER NOT NULL, description TEXT NOT NULL, status TEXT NOT NULL,
 FOREIGN KEY(task_id) REFERENCES tasks(id)
);
CREATE TABLE IF NOT EXISTS audit_events (
 id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT, event TEXT NOT NULL,
 details TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_tasks_created ON tasks(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_task ON audit_events(task_id);
"""

def connect(path: str | Path) -> sqlite3.Connection:
    db = sqlite3.connect(str(path))
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db

def initialise(path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with connect(target) as db:
        db.executescript(SCHEMA)
