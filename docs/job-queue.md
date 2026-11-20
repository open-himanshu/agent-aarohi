# Persistent Job Queue

Aarohi's queue is stored in SQLite and is designed for **at-least-once execution**.

## What it provides

- Transactional enqueue and atomic claim using SQLite `BEGIN IMMEDIATE`.
- Unique idempotency keys to prevent duplicate enqueue requests.
- Worker leases with unique tokens; expired leases can be reclaimed after a crash.
- Retry scheduling with exponential backoff and a configurable maximum attempt count.
- Terminal failure after the attempt limit, or immediately when a handler is not registered.
- Audit events for enqueue, claim, retry, success and failure.
- Workers dispatch only handlers explicitly supplied by application code.
- A daemon heartbeat renews leases during long-running synchronous handlers; uncertain renewal fails closed.
- `run_forever(stop_event)` supports cooperative shutdown and bounded polling; infrastructure exceptions propagate to the process supervisor.

## Important delivery guarantee

A worker can perform an external side effect and crash before recording success. The lease will eventually expire and the job may run again. Therefore this is **at-least-once**, not exactly-once delivery. Every handler that performs side effects must be idempotent (for example, use the job ID as the downstream idempotency key) and must verify its own outcome.

A lease token prevents a stale worker from completing or failing a job after its lease has expired or another worker has reclaimed it. It cannot undo a side effect already performed by that stale worker.

## CLI

```powershell
python -c "from aarohi.cli import main; main(['queue', 'enqueue', 'wealthcodex.research', '--idempotency-key', 'research-2026-11-20'])"
python -c "from aarohi.cli import main; main(['queue', 'list'])"
```

The handler name is only a label until application code registers it. The CLI does not execute arbitrary handler names, shell commands or Python supplied by a user. The `Worker` API receives an explicit mapping of trusted handler names to callables.

## Python integration

```python
from aarohi.queue import JobQueue, Worker

queue = JobQueue("storage/aarohi.db")
worker = Worker(
    queue,
    worker_id="aarohi-worker-1",
    handlers={"safe.echo": lambda payload: payload["message"]},
)
worker.run_once()
```

`run_forever(stop_event)` is a cooperative worker loop. The host application must arrange for the stop event to be set (for example, from its signal handler) and must supervise/restart the process. It is not a Windows service, does not install signal handlers, and is not exposed as an unattended CLI command.

## Current limitations

- No OS-level daemon/service supervisor, automatic process restart policy, signal-handler integration, operational dashboard, cancellation or manual retry command.
- No exactly-once guarantee; external side effects require handler-level idempotency.
- Task submission remains a planned task and is not automatically enqueued for execution.
- Queue records and audit details are stored locally in plaintext SQLite.
