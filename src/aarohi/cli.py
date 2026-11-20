"""Command-line interface for Agent Aarohi."""
import argparse
import json
import logging
import sys
from collections.abc import Sequence
from datetime import datetime

from aarohi.agent.runtime import AgentRuntime
from aarohi.config import load_settings
from aarohi.database import (
    backup_database,
    check_database,
    initialise,
    restore_database,
)
from aarohi.logging_config import configure_logging, get_logger
from aarohi.memory import MemoryStore
from aarohi.queue import JobQueue
from aarohi.scheduler import Scheduler


def _memory_command(args: argparse.Namespace, store: MemoryStore) -> None:
    if args.memory_action == "list":
        records = store.list_memories(
            scope=args.scope, category=args.category,
            include_archived=args.include_archived, limit=args.limit,
        )
        print(json.dumps(records, indent=2))
        return

    if args.memory_action == "search":
        records = store.search(
            args.query, scope=args.scope, category=args.category, limit=args.limit,
        )
        print(json.dumps(records, indent=2))
        return

    if args.memory_action == "update":
        changes = {
            key: value for key, value in {
                "content": args.content, "category": args.category,
                "scope": args.scope, "source": args.source,
                "confidence": args.confidence, "confirmed": args.confirmed,
            }.items() if value is not None
        }
        if not changes:
            raise ValueError("Provide at least one field to update")
        if not store.update(args.memory_id, **changes):
            print("Active memory not found")
        else:
            print(f"Memory updated: {args.memory_id}")
        return

    if args.memory_action == "archive":
        if store.archive(args.memory_id):
            print(f"Memory archived: {args.memory_id}")
        else:
            print("Active memory not found")
        return

    if args.memory_action == "forget":
        record = store.get(args.memory_id)
        if record is None:
            print("Memory not found")
            return
        print("PERMANENT DELETION â€” this cannot be undone.")
        print(f"ID: {record['id']}")
        print(f"Content: {record['content']}")
        if not args.yes:
            try:
                confirmation = input("Type the full memory ID to permanently delete it: ").strip()
            except EOFError:
                confirmation = ""
            if confirmation != args.memory_id:
                print("Deletion cancelled")
                return
        if store.forget(args.memory_id):
            print(f"Memory permanently deleted: {args.memory_id}")
        else:
            print("Memory not found; nothing deleted")


def _run_command(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="aarohi", description="Agent Aarohi")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("about")
    sub.add_parser("init-db")
    sub.add_parser("health", help="Show application and persistence health")
    database = sub.add_parser("db", help="Check, back up or restore the SQLite database")
    database_sub = database.add_subparsers(dest="database_action", required=True)
    database_sub.add_parser("check", help="Run SQLite integrity and foreign-key checks")
    backup = database_sub.add_parser("backup", help="Create a consistent database backup")
    backup.add_argument("destination")
    backup.add_argument("--overwrite", action="store_true")
    restore = database_sub.add_parser("restore", help="Restore a database backup")
    restore.add_argument("source")
    restore.add_argument(
        "--yes", action="store_true",
        help="Confirm replacing the configured database if it already exists",
    )
    submit = sub.add_parser("submit")
    submit.add_argument("goal", nargs="+")
    sub.add_parser("tasks")
    show = sub.add_parser("show")
    show.add_argument("task_id")

    memory = sub.add_parser("memory", help="Inspect and manage local memories")
    memory_sub = memory.add_subparsers(dest="memory_action", required=True)
    memory_list = memory_sub.add_parser("list", help="List active memories")
    memory_list.add_argument("--scope")
    memory_list.add_argument("--category")
    memory_list.add_argument("--include-archived", action="store_true")
    memory_list.add_argument("--limit", type=int, default=100)
    memory_search = memory_sub.add_parser("search", help="Search active memories")
    memory_search.add_argument("query")
    memory_search.add_argument("--scope")
    memory_search.add_argument("--category")
    memory_search.add_argument("--limit", type=int, default=10)
    update = memory_sub.add_parser("update", help="Correct an active memory")
    update.add_argument("memory_id")
    update.add_argument("--content")
    update.add_argument("--category")
    update.add_argument("--scope")
    update.add_argument("--source")
    update.add_argument("--confidence", type=float)
    update.add_argument("--confirmed", action=argparse.BooleanOptionalAction, default=None)
    archive = memory_sub.add_parser("archive", help="Archive an active memory")
    archive.add_argument("memory_id")
    forget = memory_sub.add_parser("forget", help="Permanently delete a memory")
    forget.add_argument("memory_id")
    forget.add_argument("--yes", action="store_true", help="Confirm permanent deletion")

    queue_parser = sub.add_parser("queue", help="Inspect and enqueue registered-handler jobs")
    queue_sub = queue_parser.add_subparsers(dest="queue_action", required=True)
    queue_sub.add_parser("list", help="List persistent jobs")
    enqueue = queue_sub.add_parser("enqueue", help="Enqueue a job for an application-registered handler")
    enqueue.add_argument("handler")
    enqueue.add_argument("--payload", default="{}", help="JSON object passed to the registered handler")
    enqueue.add_argument("--task-id")
    enqueue.add_argument("--idempotency-key")
    enqueue.add_argument("--max-attempts", type=int, default=3)

    schedule_parser = sub.add_parser("schedule", help="Manage persistent scheduled jobs")
    schedule_sub = schedule_parser.add_subparsers(dest="schedule_action", required=True)
    schedule_sub.add_parser("list")
    schedule_add = schedule_sub.add_parser("add")
    schedule_add.add_argument("handler")
    schedule_add.add_argument("--run-at", required=True, help="Timezone-aware ISO-8601 timestamp")
    schedule_add.add_argument("--every-seconds", type=int)
    schedule_add.add_argument("--payload", default="{}")
    schedule_cancel = schedule_sub.add_parser("cancel")
    schedule_cancel.add_argument("schedule_id")
    schedule_sub.add_parser("run-due", help="Enqueue due occurrences; does not execute handlers")

    args = parser.parse_args(argv)
    if args.command in (None, "about"):
        print("Aarohi - modular, permissioned personal AI agent")
        return 0

    settings = load_settings()
    logger = configure_logging(log_dir=settings.log_dir, level=settings.log_level)
    logger.info("CLI command started", extra={"command": args.command, "environment": settings.environment})

    if args.command == "health":
        initialise(settings.database_path)
        db_health = check_database(settings.database_path)
        from aarohi.database import connect
        with connect(settings.database_path) as db:
            queue_counts = {
                row["status"]: row["count"]
                for row in db.execute("SELECT status, COUNT(*) AS count FROM jobs GROUP BY status")
            }
            schedule_count = db.execute(
                "SELECT COUNT(*) FROM schedules WHERE enabled=1"
            ).fetchone()[0]
        report = {
            "status": "healthy" if db_health["healthy"] else "degraded",
            "environment": settings.environment,
            "database": db_health,
            "queue": queue_counts,
            "enabled_schedules": schedule_count,
            "execution_enabled": False,
        }
        print(json.dumps(report, indent=2))
        return 0 if db_health["healthy"] else 1
    if args.command == "init-db":
        initialise(settings.database_path)
        logger.info("Database initialised", extra={"database_path": str(settings.database_path)})
        print(f"Database ready: {settings.database_path}")
    elif args.command == "db":
        if args.database_action == "check":
            result = check_database(settings.database_path)
            print(json.dumps(result, indent=2))
            if not result["healthy"]:
                raise RuntimeError("Database health check failed")
        elif args.database_action == "backup":
            destination = backup_database(
                settings.database_path, args.destination, overwrite=args.overwrite,
            )
            print(f"Database backup created: {destination}")
        elif args.database_action == "restore":
            if settings.database_path.exists() and not args.yes:
                raise ValueError(
                    "Configured database already exists. Stop Aarohi and rerun with --yes "
                    "only after confirming replacement."
                )
            destination = restore_database(
                args.source, settings.database_path, overwrite=args.yes,
            )
            print(f"Database restored: {destination}")
    elif args.command == "submit":
        task_id = AgentRuntime(settings.database_path).submit(" ".join(args.goal))
        logger.info("Task submitted", extra={"task_id": task_id})
        print(f"Task created: {task_id}")
    elif args.command == "tasks":
        print(json.dumps(AgentRuntime(settings.database_path).list_tasks(), indent=2))
    elif args.command == "show":
        task = AgentRuntime(settings.database_path).get_task(args.task_id)
        if task is None:
            get_logger(__name__).warning("Task not found", extra={"task_id": args.task_id})
            print("Task not found")
        else:
            print(json.dumps(task, indent=2))
    elif args.command == "memory":
        _memory_command(args, MemoryStore(settings.database_path))
    elif args.command == "schedule":
        scheduler = Scheduler(settings.database_path)
        if args.schedule_action == "list":
            print(json.dumps(scheduler.list(include_disabled=True), indent=2))
        elif args.schedule_action == "add":
            run_at = datetime.fromisoformat(args.run_at)
            if run_at.tzinfo is None:
                raise ValueError("--run-at must include a timezone offset")
            payload = json.loads(args.payload)
            if not isinstance(payload, dict):
                raise ValueError("Schedule payload must be a JSON object")
            schedule_id = scheduler.add(
                args.handler, payload, run_at=run_at,
                interval_seconds=args.every_seconds,
            )
            print(f"Schedule created: {schedule_id}")
        elif args.schedule_action == "cancel":
            print("Schedule cancelled" if scheduler.cancel(args.schedule_id) else "Active schedule not found")
        elif args.schedule_action == "run-due":
            print(json.dumps({"enqueued_job_ids": scheduler.run_due()}, indent=2))
    elif args.command == "queue":
        queue = JobQueue(settings.database_path)
        if args.queue_action == "list":
            print(json.dumps(queue.list_jobs(), indent=2))
        elif args.queue_action == "enqueue":
            payload = json.loads(args.payload)
            if not isinstance(payload, dict):
                raise ValueError("Job payload must be a JSON object")
            job_id = queue.enqueue(
                args.handler, payload, task_id=args.task_id,
                idempotency_key=args.idempotency_key,
                max_attempts=args.max_attempts,
            )
            print(f"Job queued: {job_id}")

    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run a CLI command with consistent, secret-aware error reporting."""
    try:
        return _run_command(argv)
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        return 130
    except (ValueError, OSError, RuntimeError, json.JSONDecodeError) as exc:
        if logging.getLogger("aarohi").handlers:
            get_logger(__name__).exception(
                "CLI command failed", extra={"error_type": type(exc).__name__}
            )
        from aarohi.logging_config import redact_text
        print(f"Error: {redact_text(str(exc))}", file=sys.stderr)
        return 2
