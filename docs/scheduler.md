# Persistent Scheduler

Aarohi stores one-shot and fixed-interval schedules in SQLite. The scheduler is deliberately invoked by an external supervisor or manually; importing the module does not start a background thread or Windows service.

## Supported schedule types

- One-shot: enqueues one job and disables the schedule.
- Fixed interval: enqueues at most one occurrence per scheduler tick. If several intervals were missed while Aarohi was offline, it skips the backlog and calculates the next future occurrence. This avoids a sudden burst of stale work.
- Cancellation: disables a schedule; it does not cancel a job that was already enqueued.

## CLI

Use timezone-aware ISO-8601 timestamps:

```powershell
python -c "from aarohi.cli import main; main(['schedule', 'add', 'wealthcodex.research', '--run-at', '2026-11-21T09:00:00+05:30', '--every-seconds', '86400'])"
python -c "from aarohi.cli import main; main(['schedule', 'list'])"
python -c "from aarohi.cli import main; main(['schedule', 'run-due'])"
python -c "from aarohi.cli import main; main(['schedule', 'cancel', 'SCHEDULE_ID'])"
```

`run-due` only creates queue jobs. It does not run their handlers. A trusted application worker must claim and execute those jobs.

## Reliability

The scheduler advances a schedule and inserts its queue job within the same SQLite transaction. The occurrence idempotency key is derived from schedule ID and scheduled timestamp. Concurrent scheduler invocations serialize through `BEGIN IMMEDIATE`; they cannot independently create duplicate occurrences.

## Not implemented

- No cron expressions, calendar rules, timezone/DST recurrence policy or random jitter.
- No Windows Task Scheduler registration or always-on daemon.
- No automatic startup, monitoring, missed-run alerting or supervisor.
- Fixed intervals are elapsed-time intervals, not local-wall-clock daily schedules.
- Schedule records and payloads are local plaintext SQLite data.
