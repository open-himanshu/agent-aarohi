"""SQLite connection management, versioned migrations and safe backup/restore."""
from __future__ import annotations

import os
import sqlite3
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

SCHEMA_VERSION = 4

_MIGRATION_1 = (
    """CREATE TABLE IF NOT EXISTS tasks (
        id TEXT PRIMARY KEY, goal TEXT NOT NULL, status TEXT NOT NULL,
        created_at TEXT NOT NULL, updated_at TEXT NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS task_steps (
        id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT NOT NULL,
        position INTEGER NOT NULL, description TEXT NOT NULL, status TEXT NOT NULL,
        FOREIGN KEY(task_id) REFERENCES tasks(id)
    )""",
    """CREATE TABLE IF NOT EXISTS task_context (
        task_id TEXT PRIMARY KEY, context_json TEXT NOT NULL, created_at TEXT NOT NULL,
        FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE
    )""",
    """CREATE TABLE IF NOT EXISTS audit_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT, event TEXT NOT NULL,
        details TEXT NOT NULL, created_at TEXT NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS memories (
        id TEXT PRIMARY KEY, content TEXT NOT NULL, category TEXT NOT NULL,
        scope TEXT NOT NULL, source TEXT NOT NULL,
        confidence REAL NOT NULL CHECK(confidence >= 0 AND confidence <= 1),
        confirmed INTEGER NOT NULL CHECK(confirmed IN (0, 1)),
        status TEXT NOT NULL CHECK(status IN ('active', 'archived')),
        created_at TEXT NOT NULL, updated_at TEXT NOT NULL, last_accessed_at TEXT
    )""",
    "CREATE INDEX IF NOT EXISTS idx_tasks_created ON tasks(created_at)",
    "CREATE INDEX IF NOT EXISTS idx_audit_task ON audit_events(task_id)",
    "CREATE INDEX IF NOT EXISTS idx_memories_scope_status ON memories(scope, status)",
    "CREATE INDEX IF NOT EXISTS idx_memories_category ON memories(category)",
)

_MIGRATION_2 = (
    "CREATE INDEX IF NOT EXISTS idx_task_steps_task_position ON task_steps(task_id, position)",
    "CREATE INDEX IF NOT EXISTS idx_task_context_created ON task_context(created_at)",
)

_MIGRATION_3 = (
    """CREATE TABLE IF NOT EXISTS jobs (
        id TEXT PRIMARY KEY, task_id TEXT, handler TEXT NOT NULL,
        payload_json TEXT NOT NULL, status TEXT NOT NULL
            CHECK(status IN ('queued', 'running', 'succeeded', 'failed')),
        attempts INTEGER NOT NULL DEFAULT 0 CHECK(attempts >= 0),
        max_attempts INTEGER NOT NULL CHECK(max_attempts >= 1),
        available_at TEXT NOT NULL, lease_owner TEXT, lease_token TEXT,
        lease_expires_at TEXT, idempotency_key TEXT NOT NULL UNIQUE,
        last_error TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
        FOREIGN KEY(task_id) REFERENCES tasks(id)
    )""",
    "CREATE INDEX IF NOT EXISTS idx_jobs_ready ON jobs(status, available_at, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_jobs_lease ON jobs(status, lease_expires_at)",
)


_MIGRATION_4 = (
    """CREATE TABLE IF NOT EXISTS schedules (
        id TEXT PRIMARY KEY, handler TEXT NOT NULL, payload_json TEXT NOT NULL,
        run_at TEXT NOT NULL, interval_seconds INTEGER,
        enabled INTEGER NOT NULL CHECK(enabled IN (0, 1)),
        created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
        CHECK(interval_seconds IS NULL OR interval_seconds >= 1)
    )""",
    "CREATE INDEX IF NOT EXISTS idx_schedules_due ON schedules(enabled, run_at)",
)


def connect(path: str | Path) -> sqlite3.Connection:
    """Open a SQLite connection with foreign keys and bounded lock waiting."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(str(target), timeout=10.0)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    db.execute("PRAGMA busy_timeout = 10000")
    return db


@contextmanager
def transaction(path: str | Path) -> Iterator[sqlite3.Connection]:
    """Run a group of statements atomically, rolling back on every failure."""
    db = connect(path)
    try:
        db.execute("BEGIN IMMEDIATE")
        yield db
        db.commit()
    except BaseException:
        db.rollback()
        raise
    finally:
        db.close()


def _apply_migration(db: sqlite3.Connection, statements: tuple[str, ...], version: int) -> None:
    db.execute("BEGIN IMMEDIATE")
    try:
        for statement in statements:
            db.execute(statement)
        db.execute(f"PRAGMA user_version = {version}")
        db.commit()
    except BaseException:
        db.rollback()
        raise


def initialise(path: str | Path) -> None:
    """Create or upgrade the database without discarding existing records."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with connect(target) as db:
        version = int(db.execute("PRAGMA user_version").fetchone()[0])
        if version > SCHEMA_VERSION:
            raise RuntimeError(
                f"Database schema version {version} is newer than supported version {SCHEMA_VERSION}"
            )
        if version < 1:
            _apply_migration(db, _MIGRATION_1, 1)
            version = 1
        if version < 2:
            _apply_migration(db, _MIGRATION_2, 2)
            version = 2
        if version < 3:
            _apply_migration(db, _MIGRATION_3, 3)
            version = 3
        if version < 4:
            _apply_migration(db, _MIGRATION_4, 4)


def check_database(path: str | Path) -> dict[str, object]:
    """Return SQLite integrity, foreign-key and schema-version diagnostics."""
    target = Path(path)
    if not target.is_file():
        raise FileNotFoundError(target)
    with connect(target) as db:
        integrity_rows = [row[0] for row in db.execute("PRAGMA quick_check")]
        foreign_key_errors = [
            tuple(row) for row in db.execute("PRAGMA foreign_key_check")
        ]
        version = int(db.execute("PRAGMA user_version").fetchone()[0])
    return {
        "path": str(target.resolve()),
        "schema_version": version,
        "supported_schema_version": SCHEMA_VERSION,
        "integrity": "ok" if integrity_rows == ["ok"] else integrity_rows,
        "foreign_key_errors": foreign_key_errors,
        "healthy": integrity_rows == ["ok"] and not foreign_key_errors
        and version <= SCHEMA_VERSION,
    }


def _validated_source(path: str | Path) -> Path:
    source = Path(path).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    result = check_database(source)
    if not result["healthy"]:
        raise sqlite3.DatabaseError(f"Database failed integrity checks: {result}")
    return source


def _copy_database(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.{uuid.uuid4().hex}.tmp")
    source_db = sqlite3.connect(str(source), timeout=10.0)
    destination_db = sqlite3.connect(str(temporary), timeout=10.0)
    try:
        source_db.backup(destination_db, pages=256)
        result = destination_db.execute("PRAGMA quick_check").fetchone()[0]
        if result != "ok":
            raise sqlite3.DatabaseError(f"Backup integrity check failed: {result}")
        destination_db.commit()
        destination_db.close()
        destination_db = None
        os.replace(temporary, destination)
    finally:
        if destination_db is not None:
            destination_db.close()
        source_db.close()
        if temporary.exists():
            temporary.unlink()


def backup_database(source_path: str | Path, backup_path: str | Path, *, overwrite: bool = False) -> Path:
    """Create a consistent SQLite backup through SQLite's online backup API."""
    source = _validated_source(source_path)
    destination = Path(backup_path).expanduser().resolve()
    if source == destination:
        raise ValueError("Backup destination must differ from the source database")
    if destination.exists() and not overwrite:
        raise FileExistsError(destination)
    _copy_database(source, destination)
    return destination


def restore_database(
    backup_path: str | Path, database_path: str | Path, *, overwrite: bool = False,
) -> Path:
    """Restore a validated backup; replacing an existing DB requires explicit consent."""
    source = _validated_source(backup_path)
    destination = Path(database_path).expanduser().resolve()
    if source == destination:
        raise ValueError("Restore source and destination must differ")
    if destination.exists() and not overwrite:
        raise FileExistsError(destination)
    if not destination.exists():
        _copy_database(source, destination)
        return destination

    # SQLite's backup API replaces the destination transactionally. This also
    # avoids Windows rename failures when SQLite has recently held the file open.
    source_db = sqlite3.connect(str(source), timeout=10.0)
    destination_db = sqlite3.connect(str(destination), timeout=10.0)
    try:
        source_db.backup(destination_db, pages=256)
        result = destination_db.execute("PRAGMA quick_check").fetchone()[0]
        if result != "ok":
            raise sqlite3.DatabaseError(f"Restored database integrity check failed: {result}")
        destination_db.commit()
    finally:
        destination_db.close()
        source_db.close()
    return destination
