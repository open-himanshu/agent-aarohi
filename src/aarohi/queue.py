"""SQLite-backed job queue with leases, retries and bounded handlers."""
from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Event, Thread
from typing import Any
from uuid import uuid4

from aarohi.database import connect, initialise, transaction
from aarohi.logging_config import redact_data


def _now() -> datetime:
    return datetime.now(UTC)


def _stamp(value: datetime) -> str:
    if value.tzinfo is None:
        raise ValueError("Queue timestamps must be timezone-aware")
    return value.astimezone(UTC).isoformat()


class JobQueue:
    """Persistent at-least-once queue; handlers must be idempotent."""

    def __init__(self, database_path: str | Path):
        self.database_path = Path(database_path)
        initialise(self.database_path)

    def enqueue(
        self,
        handler: str,
        payload: dict[str, Any] | None = None,
        *,
        task_id: str | None = None,
        idempotency_key: str | None = None,
        max_attempts: int = 3,
        available_at: datetime | None = None,
    ) -> str:
        if not handler or not handler.strip():
            raise ValueError("Handler name cannot be empty")
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if payload is not None and not isinstance(payload, dict):
            raise ValueError("Job payload must be a JSON-compatible object")
        job_id = str(uuid4())
        now = _now()
        key = idempotency_key or str(uuid4())
        payload_data = payload or {}
        safe_payload = redact_data(payload_data)
        if safe_payload != payload_data:
            raise ValueError("Job payload appears to contain a secret; pass a secret reference instead")
        encoded = json.dumps(safe_payload, ensure_ascii=False, sort_keys=True)
        with transaction(self.database_path) as db:
            existing = db.execute(
                "SELECT id FROM jobs WHERE idempotency_key = ?", (key,)
            ).fetchone()
            if existing:
                return str(existing["id"])
            if task_id is not None and db.execute(
                "SELECT 1 FROM tasks WHERE id = ?", (task_id,)
            ).fetchone() is None:
                raise ValueError(f"Unknown task_id: {task_id}")
            db.execute(
                """INSERT INTO jobs
                (id, task_id, handler, payload_json, status, attempts, max_attempts,
                 available_at, lease_owner, lease_token, lease_expires_at,
                 idempotency_key, last_error, created_at, updated_at)
                VALUES (?, ?, ?, ?, 'queued', 0, ?, ?, NULL, NULL, NULL, ?, NULL, ?, ?)""",
                (job_id, task_id, handler.strip(), encoded, max_attempts,
                 _stamp(available_at or now), key, _stamp(now), _stamp(now)),
            )
            db.execute(
                "INSERT INTO audit_events(task_id, event, details, created_at) VALUES (?, ?, ?, ?)",
                (task_id, "job.queued", json.dumps({"job_id": job_id, "handler": handler}), _stamp(now)),
            )
        return job_id

    def get(self, job_id: str) -> dict[str, Any] | None:
        with connect(self.database_path) as db:
            row = db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if row is None:
            return None
        job = dict(row)
        job["payload"] = json.loads(job.pop("payload_json"))
        return job

    def list_jobs(self, *, limit: int = 100) -> list[dict[str, Any]]:
        if not 1 <= limit <= 1000:
            raise ValueError("limit must be between 1 and 1000")
        with connect(self.database_path) as db:
            rows = db.execute(
                "SELECT id, task_id, handler, status, attempts, max_attempts, "
                "available_at, lease_expires_at, last_error, created_at, updated_at "
                "FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(row) for row in rows]

    def claim(
        self, worker_id: str, *, lease_seconds: int = 60, now: datetime | None = None,
    ) -> dict[str, Any] | None:
        if not worker_id or not worker_id.strip():
            raise ValueError("worker_id cannot be empty")
        if lease_seconds < 1:
            raise ValueError("lease_seconds must be at least 1")
        current = now or _now()
        current_s = _stamp(current)
        expiry_s = _stamp(current + timedelta(seconds=lease_seconds))
        token = str(uuid4())
        with transaction(self.database_path) as db:
            # Expired jobs at their attempt limit are terminal, not endlessly reclaimed.
            db.execute(
                """UPDATE jobs SET status='failed', lease_owner=NULL, lease_token=NULL,
                   lease_expires_at=NULL, last_error=COALESCE(last_error, 'Worker lease expired'),
                   updated_at=?
                   WHERE status='running' AND lease_expires_at <= ? AND attempts >= max_attempts""",
                (current_s, current_s),
            )
            row = db.execute(
                """SELECT * FROM jobs
                   WHERE attempts < max_attempts AND (
                     (status='queued' AND available_at <= ?) OR
                     (status='running' AND lease_expires_at <= ?)
                   )
                   ORDER BY available_at, created_at LIMIT 1""",
                (current_s, current_s),
            ).fetchone()
            if row is None:
                return None
            db.execute(
                """UPDATE jobs SET status='running', attempts=attempts+1,
                   lease_owner=?, lease_token=?, lease_expires_at=?, updated_at=?
                   WHERE id=?""",
                (worker_id, token, expiry_s, current_s, row["id"]),
            )
            db.execute(
                "INSERT INTO audit_events(task_id, event, details, created_at) VALUES (?, ?, ?, ?)",
                (row["task_id"], "job.claimed",
                 json.dumps({"job_id": row["id"], "worker_id": worker_id, "attempt": row["attempts"] + 1}),
                 current_s),
            )
            claimed = db.execute("SELECT * FROM jobs WHERE id=?", (row["id"],)).fetchone()
        job = dict(claimed)
        job["payload"] = json.loads(job.pop("payload_json"))
        return job

    def renew(self, job_id: str, lease_token: str, *, lease_seconds: int = 60) -> bool:
        """Extend a live lease; expired/stale workers cannot resurrect ownership."""
        if lease_seconds < 1:
            raise ValueError("lease_seconds must be at least 1")
        now = _now()
        now_s = _stamp(now)
        expiry = _stamp(now + timedelta(seconds=lease_seconds))
        with transaction(self.database_path) as db:
            cursor = db.execute(
                """UPDATE jobs SET lease_expires_at=?, updated_at=?
                   WHERE id=? AND status='running' AND lease_token=?
                   AND lease_expires_at > ?""",
                (expiry, now_s, job_id, lease_token, now_s),
            )
        return cursor.rowcount == 1

    def complete(self, job_id: str, lease_token: str) -> bool:
        now = _stamp(_now())
        with transaction(self.database_path) as db:
            row = db.execute(
                "SELECT task_id FROM jobs WHERE id=? AND status='running' "
                "AND lease_token=? AND lease_expires_at > ?",
                (job_id, lease_token, now),
            ).fetchone()
            if row is None:
                return False
            db.execute(
                """UPDATE jobs SET status='succeeded', lease_owner=NULL, lease_token=NULL,
                   lease_expires_at=NULL, last_error=NULL, updated_at=? WHERE id=?""",
                (now, job_id),
            )
            db.execute(
                "INSERT INTO audit_events(task_id, event, details, created_at) VALUES (?, ?, ?, ?)",
                (row["task_id"], "job.succeeded", json.dumps({"job_id": job_id}), now),
            )
        return True

    def fail(
        self, job_id: str, lease_token: str, error: str, *,
        base_delay_seconds: int = 5, max_delay_seconds: int = 3600,
        now: datetime | None = None, permanent: bool = False,
    ) -> bool:
        if base_delay_seconds < 0 or max_delay_seconds < 0:
            raise ValueError("Retry delays cannot be negative")
        current = now or _now()
        current_s = _stamp(current)
        safe_error = str(redact_data(error))[:2000]
        with transaction(self.database_path) as db:
            row = db.execute(
                "SELECT task_id, attempts, max_attempts FROM jobs "
                "WHERE id=? AND status='running' AND lease_token=? AND lease_expires_at > ?",
                (job_id, lease_token, current_s),
            ).fetchone()
            if row is None:
                return False
            terminal = permanent or row["attempts"] >= row["max_attempts"]
            delay = min(base_delay_seconds * (2 ** max(0, row["attempts"] - 1)), max_delay_seconds)
            available = _stamp(current + timedelta(seconds=delay))
            status = "failed" if terminal else "queued"
            db.execute(
                """UPDATE jobs SET status=?, available_at=?, lease_owner=NULL,
                   lease_token=NULL, lease_expires_at=NULL, last_error=?, updated_at=?
                   WHERE id=?""",
                (status, available, safe_error, current_s, job_id),
            )
            db.execute(
                "INSERT INTO audit_events(task_id, event, details, created_at) VALUES (?, ?, ?, ?)",
                (row["task_id"], "job.failed" if terminal else "job.retry_scheduled",
                 json.dumps({"job_id": job_id, "error": safe_error[:500], "retry_at": available}), current_s),
            )
        return True


class Worker:
    """Run allow-listed handlers with lease renewal and cooperative shutdown."""

    def __init__(
        self, queue: JobQueue, worker_id: str,
        handlers: dict[str, Callable[[dict[str, Any]], Any]],
        *, lease_seconds: int = 60, base_delay_seconds: int = 5,
        max_delay_seconds: int = 3600, heartbeat_interval: float | None = None,
    ):
        if lease_seconds < 3:
            raise ValueError("lease_seconds must be at least 3")
        interval = heartbeat_interval if heartbeat_interval is not None else lease_seconds / 3
        if interval <= 0 or interval >= lease_seconds:
            raise ValueError("heartbeat_interval must be positive and shorter than the lease")
        self.queue = queue
        self.worker_id = worker_id
        self.handlers = dict(handlers)
        self.lease_seconds = lease_seconds
        self.base_delay_seconds = base_delay_seconds
        self.max_delay_seconds = max_delay_seconds
        self.heartbeat_interval = interval

    def _heartbeat(
        self, job_id: str, token: str, stop: Event, lease_lost: Event,
    ) -> None:
        while not stop.wait(self.heartbeat_interval):
            try:
                renewed = self.queue.renew(
                    job_id, token, lease_seconds=self.lease_seconds,
                )
            except Exception:  # noqa: BLE001 - fail closed if lease status is uncertain
                lease_lost.set()
                return
            if not renewed:
                lease_lost.set()
                return

    def run_once(self) -> dict[str, Any] | None:
        job = self.queue.claim(self.worker_id, lease_seconds=self.lease_seconds)
        if job is None:
            return None
        token = job["lease_token"]
        handler = self.handlers.get(job["handler"])
        if handler is None:
            self.queue.fail(
                job["id"], token, f"No registered handler: {job['handler']}",
                base_delay_seconds=0, max_delay_seconds=0, permanent=True,
            )
            return {"job_id": job["id"], "status": "handler_missing"}

        heartbeat_stop = Event()
        lease_lost = Event()
        heartbeat = Thread(
            target=self._heartbeat,
            args=(job["id"], token, heartbeat_stop, lease_lost),
            name=f"aarohi-heartbeat-{job['id'][:8]}",
            daemon=True,
        )
        heartbeat.start()
        try:
            try:
                result = handler(job["payload"])
            except Exception as exc:  # noqa: BLE001 - isolate handler failures for retry
                if lease_lost.is_set():
                    return {"job_id": job["id"], "status": "lease_lost"}
                failed = self.queue.fail(
                    job["id"], token, f"{type(exc).__name__}: {exc}",
                    base_delay_seconds=self.base_delay_seconds,
                    max_delay_seconds=self.max_delay_seconds,
                )
                return {
                    "job_id": job["id"],
                    "status": "retry_or_failed" if failed else "lease_lost",
                }
        finally:
            heartbeat_stop.set()
            heartbeat.join(timeout=self.lease_seconds)

        if lease_lost.is_set():
            return {"job_id": job["id"], "status": "lease_lost"}
        completed = self.queue.complete(job["id"], token)
        safe_result = (
            result if isinstance(result, (str, int, float, bool, type(None), dict, list))
            else repr(result)
        )
        return {
            "job_id": job["id"],
            "status": "succeeded" if completed else "lease_lost",
            "result": safe_result,
        }

    def run_forever(
        self, stop_event: Event, *, poll_interval: float = 1.0,
        max_jobs: int | None = None,
    ) -> int:
        """Poll until cooperatively stopped; return the number of claimed jobs."""
        if poll_interval <= 0:
            raise ValueError("poll_interval must be positive")
        if max_jobs is not None and max_jobs < 1:
            raise ValueError("max_jobs must be at least 1 when supplied")
        processed = 0
        while not stop_event.is_set() and (max_jobs is None or processed < max_jobs):
            outcome = self.run_once()
            if outcome is None:
                stop_event.wait(poll_interval)
                continue
            processed += 1
        return processed
