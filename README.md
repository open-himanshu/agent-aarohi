# Agent Aarohi

Aarohi is a modular, local-first personal AI agent. WealthCodeX is its first specialist skill, not the entire product.

## Runtime
- Windows; Python 3.12 target
- Modular monolith with SQLite persistence
- CLI-first; explicitly registered tools
- Deterministic permission policy outside any language model
- No unrestricted shell tool, automatic publishing or unattended scheduling

## Setup
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m aarohi init-db
python -m aarohi about
python -m pytest
```

Set AAROHI_HOME to choose the directory containing the storage folder. In a source checkout, the repository root is the default regardless of the shell's current directory; set AAROHI_HOME explicitly for installed deployments.

## Memory management
```powershell
python -c "from aarohi.cli import main; main(['memory', 'list'])"
python -c "from aarohi.cli import main; main(['memory', 'search', 'WealthCodeX'])"
python -c "from aarohi.cli import main; main(['memory', 'update', '<MEMORY_ID>', '--content', 'Corrected text'])"
python -c "from aarohi.cli import main; main(['memory', 'archive', '<MEMORY_ID>'])"
python -c "from aarohi.cli import main; main(['memory', 'forget', '<MEMORY_ID>'])"
```

See docs/memory-privacy.md before storing personal information. The database is not encrypted; credential detection is best-effort. Forget requires exact confirmation and also scrubs the memory ID from task-context snapshots in the live database.

## Database operations
```powershell
python -c "from aarohi.cli import main; main(['db', 'check'])"
python -c "from aarohi.cli import main; main(['db', 'backup', 'storage/backups/aarohi.db'])"
python -c "from aarohi.cli import main; main(['db', 'restore', 'storage/backups/aarohi.db', '--yes'])"
```

Read docs/database-operations.md before restoring. Stop Aarohi before restore; --yes confirms replacement of the configured database.

## Persistent job queue
```powershell
python -c "from aarohi.cli import main; main(['queue', 'enqueue', 'wealthcodex.research', '--idempotency-key', 'research-2026-11-20'])"
python -c "from aarohi.cli import main; main(['queue', 'list'])"
```

The SQLite queue supports atomic claims, expiring leases, crash recovery, exponential retry backoff, max attempts, idempotency keys and audit events. Workers execute only explicitly registered application handlers. Delivery is at-least-once: handlers with side effects must be idempotent. The CLI does not start an unattended worker. See docs/job-queue.md.

## Persistent scheduler
The SQLite scheduler supports one-shot and fixed-interval schedules, cancellation, duplicate-safe enqueueing and missed-interval skipping. Use timezone-aware timestamps. `run-due` only enqueues jobs; it does not execute them. No background service or Windows Task Scheduler registration is enabled. See docs/scheduler.md.

## Current capability
Aarohi can accept a goal and persist it as a planned task, manage durable memories, enqueue bounded handler jobs, schedule queue jobs and inspect tasks/jobs/schedules. The worker API dispatches only registered handlers. Aarohi does not yet autonomously reason, call an LLM or execute arbitrary tools; submitted goals remain planned and are not automatically enqueued.

## Next
Complete Phase 1 integration acceptance, operational worker lifecycle, reliable data paths and fresh-clone verification. External publishing remains disabled until its quality and policy gates pass.


## Operations and diagnostics
```powershell
python -c "from aarohi.cli import main; raise SystemExit(main(['health']))"
```

Health checks SQLite integrity/schema/foreign keys and reports queue and enabled-schedule counts. It does not claim an AI executor or background worker is running. CLI handled errors return non-zero exit codes. See docs/operations.md for worker supervision, error behaviour and audit/privacy boundaries.
