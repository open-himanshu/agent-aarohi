import sqlite3

import pytest

from aarohi.database import (
    SCHEMA_VERSION,
    backup_database,
    check_database,
    connect,
    initialise,
    restore_database,
    transaction,
)


def _legacy_database(path):
    with sqlite3.connect(path) as db:
        db.execute(
            """CREATE TABLE tasks (
                id TEXT PRIMARY KEY, goal TEXT NOT NULL, status TEXT NOT NULL,
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            )"""
        )
        db.execute(
            """CREATE TABLE task_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT NOT NULL,
                position INTEGER NOT NULL, description TEXT NOT NULL, status TEXT NOT NULL,
                FOREIGN KEY(task_id) REFERENCES tasks(id)
            )"""
        )
        db.execute(
            """CREATE TABLE audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT, event TEXT NOT NULL,
                details TEXT NOT NULL, created_at TEXT NOT NULL
            )"""
        )
        db.execute(
            "INSERT INTO tasks VALUES ('legacy-task', 'Keep this task', 'planned', 't0', 't0')"
        )
        db.execute(
            "INSERT INTO task_steps(task_id, position, description, status) "
            "VALUES ('legacy-task', 1, 'Legacy step', 'pending')"
        )


def test_migrates_legacy_database_without_losing_records(tmp_path):
    database = tmp_path / "legacy.db"
    _legacy_database(database)

    initialise(database)
    initialise(database)

    with connect(database) as db:
        assert db.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION
        assert db.execute("SELECT goal FROM tasks WHERE id='legacy-task'").fetchone()[0] == "Keep this task"
        assert db.execute("SELECT description FROM task_steps").fetchone()[0] == "Legacy step"
        assert db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='memories'"
        ).fetchone() is not None
        assert db.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_task_steps_task_position'"
        ).fetchone() is not None


def test_migration_failure_rolls_back_version_and_partial_ddl(tmp_path, monkeypatch):
    import aarohi.database as database_module

    database = tmp_path / "rollback.db"
    _legacy_database(database)
    monkeypatch.setattr(
        database_module,
        "_MIGRATION_1",
        ("CREATE TABLE migration_probe (id INTEGER)", "CREATE TABLE broken_table ("),
    )

    with pytest.raises(sqlite3.OperationalError):
        initialise(database)

    with connect(database) as db:
        assert db.execute("PRAGMA user_version").fetchone()[0] == 0
        assert db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='migration_probe'"
        ).fetchone() is None


def test_transaction_rolls_back_on_exception(tmp_path):
    database = tmp_path / "transaction.db"
    initialise(database)

    with pytest.raises(RuntimeError, match="abort"), transaction(database) as db:
        db.execute(
            "INSERT INTO tasks VALUES ('rolled-back', 'Goal', 'planned', 't0', 't0')"
        )
        raise RuntimeError("abort")

    with connect(database) as db:
        assert db.execute("SELECT id FROM tasks WHERE id='rolled-back'").fetchone() is None


def test_database_check_reports_integrity_and_foreign_keys(tmp_path):
    database = tmp_path / "healthy.db"
    initialise(database)

    result = check_database(database)

    assert result["healthy"] is True
    assert result["integrity"] == "ok"
    assert result["schema_version"] == SCHEMA_VERSION
    assert result["foreign_key_errors"] == []


def test_backup_and_restore_preserve_database_and_require_overwrite(tmp_path):
    database = tmp_path / "source.db"
    backup = tmp_path / "backups" / "source.db"
    restored = tmp_path / "restored.db"
    initialise(database)
    with connect(database) as db:
        db.execute("INSERT INTO tasks VALUES ('task-1', 'Original', 'planned', 't0', 't0')")

    assert backup_database(database, backup) == backup.resolve()
    assert check_database(backup)["healthy"] is True
    with pytest.raises(FileExistsError):
        backup_database(database, backup)

    initialise(restored)
    with pytest.raises(FileExistsError):
        restore_database(backup, restored)
    # Windows does not permit replacing a database while this process holds it open.
    existing = connect(restored)
    existing.close()
    restore_database(backup, restored, overwrite=True)

    restored_db = connect(restored)
    assert restored_db.execute(
        "SELECT goal FROM tasks WHERE id='task-1'"
    ).fetchone()[0] == "Original"
    restored_db.close()


def test_backup_rejects_same_source_and_destination(tmp_path):
    database = tmp_path / "same.db"
    initialise(database)

    with pytest.raises(ValueError, match="differ"):
        backup_database(database, database)


def test_future_schema_is_not_downgraded(tmp_path):
    database = tmp_path / "future.db"
    with sqlite3.connect(database) as db:
        db.execute("PRAGMA user_version = 999")

    with pytest.raises(RuntimeError, match="newer than supported"):
        initialise(database)


def test_corrupt_backup_is_rejected_before_restore(tmp_path):
    corrupt = tmp_path / "corrupt.db"
    destination = tmp_path / "destination.db"
    corrupt.write_bytes(b"this is not a sqlite database")

    with pytest.raises(sqlite3.DatabaseError):
        restore_database(corrupt, destination)

    assert destination.exists() is False
