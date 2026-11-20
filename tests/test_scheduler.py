from datetime import UTC, datetime, timedelta

import pytest

from aarohi.database import SCHEMA_VERSION, connect, initialise
from aarohi.scheduler import Scheduler


def test_migration_v3_to_v4_preserves_queue_rows(tmp_path):
    database = tmp_path / "migration.db"
    initialise(database)
    with connect(database) as db:
        db.execute(
            """INSERT INTO jobs
            (id, handler, payload_json, status, attempts, max_attempts, available_at,
             idempotency_key, created_at, updated_at)
            VALUES ('j1','handler','{}','queued',0,3,'now','key','now','now')"""
        )
        db.execute("DROP INDEX idx_schedules_due")
        db.execute("DROP TABLE schedules")
        db.execute("PRAGMA user_version=3")
    initialise(database)
    with connect(database) as db:
        assert db.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION == 4
        assert db.execute("SELECT id FROM jobs WHERE id='j1'").fetchone()


def test_one_shot_schedule_enqueues_once_and_disables(tmp_path):
    database = tmp_path / "scheduler.db"
    scheduler = Scheduler(database)
    now = datetime.now(UTC)
    schedule_id = scheduler.add("safe.report", {"topic": "AI"}, run_at=now)
    first = scheduler.run_due(now=now + timedelta(seconds=1))
    second = scheduler.run_due(now=now + timedelta(seconds=2))
    assert len(first) == 1
    assert second == []
    assert scheduler.list() == []
    assert scheduler.list(include_disabled=True)[0]["id"] == schedule_id


def test_interval_schedule_skips_missed_runs_without_burst(tmp_path):
    scheduler = Scheduler(tmp_path / "interval.db")
    start = datetime(2026, 11, 20, 10, 0, tzinfo=UTC)
    schedule_id = scheduler.add(
        "safe.poll", run_at=start, interval_seconds=60, schedule_id="poller",
    )
    first = scheduler.run_due(now=start + timedelta(minutes=5, seconds=5))
    assert len(first) == 1
    record = scheduler.list()[0]
    assert record["id"] == schedule_id
    assert record["run_at"] == (start + timedelta(minutes=6)).isoformat()
    assert scheduler.run_due(now=start + timedelta(minutes=5, seconds=10)) == []


def test_cancel_schedule_prevents_enqueue(tmp_path):
    scheduler = Scheduler(tmp_path / "cancel.db")
    now = datetime.now(UTC)
    schedule_id = scheduler.add("handler", run_at=now + timedelta(seconds=1))
    assert scheduler.cancel(schedule_id)
    assert not scheduler.cancel(schedule_id)
    assert scheduler.run_due(now=now + timedelta(seconds=5)) == []


def test_schedule_rejects_invalid_intervals_and_payloads(tmp_path):
    scheduler = Scheduler(tmp_path / "invalid.db")
    now = datetime.now(UTC)
    with pytest.raises(ValueError, match="interval_seconds"):
        scheduler.add("handler", run_at=now, interval_seconds=0)
    with pytest.raises(ValueError, match="payload"):
        scheduler.add("handler", ["bad"], run_at=now)
