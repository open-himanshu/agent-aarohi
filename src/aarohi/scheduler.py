"""Persistent interval and one-shot scheduler backed by SQLite."""
from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

from aarohi.database import connect, initialise, transaction
from aarohi.queue import _stamp


class Scheduler:
    """Enqueue due schedules transactionally; no background loop is started here."""

    def __init__(self, database_path: str | Path):
        self.database_path = Path(database_path)
        initialise(self.database_path)

    def add(
        self, handler: str, payload: dict[str, Any] | None = None, *,
        run_at: datetime, interval_seconds: int | None = None,
        schedule_id: str | None = None,
    ) -> str:
        if not handler or not handler.strip():
            raise ValueError("Handler name cannot be empty")
        if interval_seconds is not None and interval_seconds < 1:
            raise ValueError("interval_seconds must be at least 1")
        if payload is not None and not isinstance(payload, dict):
            raise ValueError("Schedule payload must be an object")
        schedule_id = schedule_id or str(uuid4())
        now = datetime.now(UTC)
        with transaction(self.database_path) as db:
            db.execute(
                """INSERT INTO schedules
                (id, handler, payload_json, run_at, interval_seconds, enabled, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 1, ?, ?)""",
                (schedule_id, handler.strip(), json.dumps(payload or {}, sort_keys=True),
                 _stamp(run_at), interval_seconds, _stamp(now), _stamp(now)),
            )
        return schedule_id

    def list(self, *, include_disabled: bool = False) -> list[dict[str, Any]]:
        query = "SELECT * FROM schedules"
        if not include_disabled:
            query += " WHERE enabled=1"
        query += " ORDER BY run_at"
        with connect(self.database_path) as db:
            return [dict(row) for row in db.execute(query).fetchall()]

    def cancel(self, schedule_id: str) -> bool:
        with transaction(self.database_path) as db:
            cursor = db.execute(
                "UPDATE schedules SET enabled=0, updated_at=? WHERE id=? AND enabled=1",
                (_stamp(datetime.now(UTC)), schedule_id),
            )
        return cursor.rowcount == 1

    def run_due(self, *, now: datetime | None = None, limit: int = 100) -> list[str]:
        if not 1 <= limit <= 1000:
            raise ValueError("limit must be between 1 and 1000")
        current = now or datetime.now(UTC)
        current_s = _stamp(current)
        created: list[str] = []
        with transaction(self.database_path) as db:
            rows = db.execute(
                "SELECT * FROM schedules WHERE enabled=1 AND run_at<=? ORDER BY run_at LIMIT ?",
                (current_s, limit),
            ).fetchall()
            for row in rows:
                occurrence = row["run_at"]
                job_id = str(uuid4())
                key = f"schedule:{row['id']}:{occurrence}"
                db.execute(
                    """INSERT OR IGNORE INTO jobs
                    (id, task_id, handler, payload_json, status, attempts, max_attempts,
                     available_at, lease_owner, lease_token, lease_expires_at,
                     idempotency_key, last_error, created_at, updated_at)
                    VALUES (?, NULL, ?, ?, 'queued', 0, 3, ?, NULL, NULL, NULL, ?, NULL, ?, ?)""",
                    (job_id, row["handler"], row["payload_json"], current_s, key, current_s, current_s),
                )
                existing = db.execute(
                    "SELECT id FROM jobs WHERE idempotency_key=?", (key,)
                ).fetchone()
                created.append(str(existing["id"]))
                if row["interval_seconds"] is None:
                    db.execute(
                        "UPDATE schedules SET enabled=0, updated_at=? WHERE id=?",
                        (current_s, row["id"]),
                    )
                else:
                    # Skip missed intervals rather than generating a burst of stale jobs.
                    interval = int(row["interval_seconds"])
                    previous = datetime.fromisoformat(occurrence)
                    elapsed = max(0.0, (current - previous).total_seconds())
                    steps = int(elapsed // interval) + 1
                    next_run = previous + timedelta(seconds=steps * interval)
                    db.execute(
                        "UPDATE schedules SET run_at=?, updated_at=? WHERE id=?",
                        (_stamp(next_run), current_s, row["id"]),
                    )
                db.execute(
                    "INSERT INTO audit_events(task_id, event, details, created_at) VALUES (NULL, ?, ?, ?)",
                    ("schedule.enqueued", json.dumps({"schedule_id": row["id"], "job_id": job_id}), current_s),
                )
        return created
