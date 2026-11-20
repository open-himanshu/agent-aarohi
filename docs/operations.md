# Operations and diagnostics

## Health report

Run:

```powershell
python -c "from aarohi.cli import main; raise SystemExit(main(['health']))"
```

The report checks SQLite integrity/schema/foreign keys and reports queue-state counts and enabled schedule count. It explicitly reports that automatic execution is disabled. A healthy database does not mean an LLM, tool executor, platform connector or worker service is running.

## CLI error behaviour

Commands return exit code 0 on success, 2 for handled validation/operational errors, and 130 for Ctrl+C. Database health failure returns 1. Argument-parser usage errors retain argparse's standard non-zero exit.

Errors printed to the terminal pass through common-pattern redaction. Structured exception logs are also redacted. Redaction is best-effort and cannot guarantee recognition of every proprietary secret format.

## Worker supervision

The application may wrap a configured Worker in WorkerSupervisor. The supervisor retries infrastructure-level failures with bounded exponential delay and then re-raises after the restart budget is exhausted. Handler exceptions are handled by the queue's retry policy and do not restart the process.

The supervisor is a Python component, not an installed Windows service. The host application remains responsible for signal handling, process lifecycle, persistent service registration, monitoring and operator alerting. No default handlers are registered and no worker is started by the CLI.

A handler already running is synchronous and cannot be forcibly interrupted by the stop event. It must implement its own bounded I/O timeouts and cooperative cancellation if needed.

## Audit and privacy boundary

Task submission audit details now redact common inline credential patterns. Queue lifecycle events record job identifiers/state transitions; handler error text is redacted before storage. This is not tamper-evident audit storage.

There is no task executor or tool invocation/approval lifecycle yet. Consequently, tool-call/result/approval audit events cannot be emitted until those components exist. SQLite remains plaintext at rest; backups may contain sensitive data and must be protected by the operator.
