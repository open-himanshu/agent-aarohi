from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta

import pytest

from aarohi.database import SCHEMA_VERSION, check_database, connect, initialise
from aarohi.queue import JobQueue, Worker


def _queue(tmp_path):
    database = tmp_path / "queue.db"
    initialise(database)
    return database, JobQueue(database)


def test_migration_v2_to_v4_preserves_existing_rows(tmp_path):
    database = tmp_path / "v2.db"
    initialise(database)
    with connect(database) as db:
        db.execute("DROP INDEX idx_jobs_ready")
        db.execute("DROP INDEX idx_jobs_lease")
        db.execute("DROP TABLE jobs")
        db.execute("PRAGMA user_version = 2")
        db.execute("INSERT INTO tasks VALUES ('t1', 'Existing', 'planned', 'now', 'now')")
    initialise(database)
    with connect(database) as db:
        assert db.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION == 4
        assert db.execute("SELECT goal FROM tasks WHERE id='t1'").fetchone()[0] == "Existing"
        assert db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='jobs'").fetchone()


def test_enqueue_persists_payload_and_idempotency(tmp_path):
    database, queue = _queue(tmp_path)
    first = queue.enqueue("reports.build", {"topic": "AI"}, idempotency_key="report-1")
    duplicate = queue.enqueue("reports.build", {"topic": "different"}, idempotency_key="report-1")
    assert duplicate == first
    job = queue.get(first)
    assert job["payload"] == {"topic": "AI"}
    assert job["status"] == "queued"
    assert check_database(database)["healthy"]


def test_enqueue_validates_task_reference_attempts_and_secrets(tmp_path):
    _, queue = _queue(tmp_path)
    with pytest.raises(ValueError, match="Unknown task_id"):
        queue.enqueue("handler", task_id="missing")
    with pytest.raises(ValueError, match="max_attempts"):
        queue.enqueue("handler", max_attempts=0)
    with pytest.raises(ValueError, match="secret"):
        queue.enqueue("handler", {"api_key": "sk-test-secret"})
    with pytest.raises(ValueError, match="JSON-compatible object"):
        queue.enqueue("handler", ["not", "an", "object"])


def test_claim_is_exclusive_and_completion_is_token_guarded(tmp_path):
    _, queue = _queue(tmp_path)
    job_id = queue.enqueue("handler")
    first = queue.claim("worker-a")
    assert first["id"] == job_id
    assert queue.claim("worker-b") is None
    assert queue.complete(job_id, "wrong-token") is False
    assert queue.complete(job_id, first["lease_token"]) is True
    assert queue.get(job_id)["status"] == "succeeded"


def test_concurrent_workers_cannot_claim_the_same_job(tmp_path):
    _, queue = _queue(tmp_path)
    queue.enqueue("handler")

    def claim(worker_id):
        return JobQueue(queue.database_path).claim(worker_id)

    with ThreadPoolExecutor(max_workers=2) as pool:
        claims = list(pool.map(claim, ["worker-a", "worker-b"]))

    successful_claims = [claim_result for claim_result in claims if claim_result is not None]
    assert len(successful_claims) == 1


def test_lease_can_be_renewed_only_by_current_owner(tmp_path):
    _, queue = _queue(tmp_path)
    job_id = queue.enqueue("handler")
    claim = queue.claim("worker", lease_seconds=30)
    assert queue.renew(job_id, claim["lease_token"], lease_seconds=60)
    assert not queue.renew(job_id, "stale-token", lease_seconds=60)
    assert queue.complete(job_id, claim["lease_token"])


def test_retry_uses_exponential_backoff_and_attempt_limit(tmp_path):
    _, queue = _queue(tmp_path)
    now = datetime.now(UTC)
    job_id = queue.enqueue("handler", max_attempts=2, available_at=now)
    first = queue.claim("worker", now=now)
    assert queue.fail(job_id, first["lease_token"], "temporary", base_delay_seconds=10, now=now)
    assert queue.claim("worker", now=now + timedelta(seconds=9)) is None
    second = queue.claim("worker", now=now + timedelta(seconds=10))
    assert second["attempts"] == 2
    assert queue.fail(
        job_id, second["lease_token"], "again", base_delay_seconds=10,
        now=now + timedelta(seconds=10),
    )
    assert queue.get(job_id)["status"] == "failed"


def test_expired_lease_is_reclaimed_after_worker_crash(tmp_path):
    _, queue = _queue(tmp_path)
    now = datetime.now(UTC)
    job_id = queue.enqueue("handler", available_at=now)
    first = queue.claim("worker-crashed", lease_seconds=5, now=now)
    recovered = queue.claim("worker-recovery", lease_seconds=5, now=now + timedelta(seconds=6))
    assert recovered["id"] == job_id
    assert recovered["attempts"] == 2
    assert recovered["lease_token"] != first["lease_token"]
    assert queue.complete(job_id, first["lease_token"]) is False
    assert queue.complete(job_id, recovered["lease_token"]) is True


def test_expired_lease_at_attempt_limit_becomes_failed(tmp_path):
    _, queue = _queue(tmp_path)
    now = datetime.now(UTC)
    job_id = queue.enqueue("handler", max_attempts=1, available_at=now)
    queue.claim("lost-worker", lease_seconds=1, now=now)
    assert queue.claim("recovery", now=now + timedelta(seconds=2)) is None
    assert queue.get(job_id)["status"] == "failed"


def test_worker_runs_only_registered_handler(tmp_path):
    _, queue = _queue(tmp_path)
    seen = []
    job_id = queue.enqueue("safe.echo", {"value": 42})
    worker = Worker(queue, "worker-1", {"safe.echo": lambda payload: seen.append(payload["value"])})
    result = worker.run_once()
    assert result["status"] == "succeeded"
    assert result["job_id"] == job_id
    assert seen == [42]


def test_handler_failure_schedules_retry(tmp_path):
    _, queue = _queue(tmp_path)
    job_id = queue.enqueue("safe.fail", max_attempts=2)
    worker = Worker(
        queue, "worker-1", {"safe.fail": lambda payload: (_ for _ in ()).throw(RuntimeError("boom"))},
        base_delay_seconds=0,
    )
    assert worker.run_once()["status"] == "retry_or_failed"
    assert queue.get(job_id)["status"] == "queued"
    assert queue.get(job_id)["last_error"] == "RuntimeError: boom"


def test_missing_handler_is_quarantined_as_terminal_failure(tmp_path):
    _, queue = _queue(tmp_path)
    job_id = queue.enqueue("not.registered", max_attempts=5)
    result = Worker(queue, "worker-1", {}).run_once()
    assert result["status"] == "handler_missing"
    assert queue.get(job_id)["status"] == "failed"


def test_expired_worker_cannot_complete_after_lease_timeout(tmp_path):
    _, queue = _queue(tmp_path)
    now = datetime.now(UTC)
    job_id = queue.enqueue("handler", available_at=now)
    claimed = queue.claim("worker", lease_seconds=1, now=now)
    # A later claimant replaces the expired lease token.
    next_claim = queue.claim("worker-2", lease_seconds=30, now=now + timedelta(seconds=2))
    assert next_claim["id"] == job_id
    assert queue.complete(job_id, claimed["lease_token"]) is False


def test_worker_renews_lease_during_long_handler(tmp_path):
    import time

    _, queue = _queue(tmp_path)
    job_id = queue.enqueue("slow.handler")
    worker = Worker(
        queue, "worker-long", {"slow.handler": lambda payload: time.sleep(1.2)},
        lease_seconds=3, heartbeat_interval=0.4,
    )
    result = worker.run_once()
    assert result["status"] == "succeeded"
    assert queue.get(job_id)["status"] == "succeeded"


def test_worker_run_forever_respects_cooperative_stop(tmp_path):
    from threading import Event

    _, queue = _queue(tmp_path)
    worker = Worker(queue, "worker-stop", {})
    stop = Event()
    stop.set()
    assert worker.run_forever(stop, poll_interval=0.01) == 0


def test_worker_validates_heartbeat_and_poll_settings(tmp_path):
    from threading import Event

    _, queue = _queue(tmp_path)
    with pytest.raises(ValueError, match="lease_seconds"):
        Worker(queue, "worker", {}, lease_seconds=2)
    worker = Worker(queue, "worker", {})
    with pytest.raises(ValueError, match="heartbeat_interval"):
        Worker(queue, "worker", {}, heartbeat_interval=60)
    with pytest.raises(ValueError, match="poll_interval"):
        worker.run_forever(Event(), poll_interval=0)
    with pytest.raises(ValueError, match="max_jobs"):
        worker.run_forever(Event(), max_jobs=0)
