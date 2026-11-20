"""Command-line interface for Agent Aarohi."""
import argparse
import json
import os
from pathlib import Path
from collections.abc import Sequence
from aarohi.agent.runtime import AgentRuntime
from aarohi.database import initialise

def _database_path() -> Path:
    root = Path(os.environ.get("AAROHI_HOME", Path.cwd()))
    return root / "storage" / "aarohi.db"

def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="aarohi", description="Agent Aarohi")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("about")
    sub.add_parser("init-db")
    submit = sub.add_parser("submit")
    submit.add_argument("goal", nargs="+")
    sub.add_parser("tasks")
    show = sub.add_parser("show")
    show.add_argument("task_id")
    args = parser.parse_args(argv)
    if args.command in (None, "about"):
        print("Aarohi - modular, permissioned personal AI agent")
    elif args.command == "init-db":
        initialise(_database_path())
        print(f"Database ready: {_database_path()}")
    elif args.command == "submit":
        task_id = AgentRuntime(_database_path()).submit(" ".join(args.goal))
        print(f"Task created: {task_id}")
    elif args.command == "tasks":
        print(json.dumps(AgentRuntime(_database_path()).list_tasks(), indent=2))
    elif args.command == "show":
        task = AgentRuntime(_database_path()).get_task(args.task_id)
        print(json.dumps(task, indent=2) if task else "Task not found")
