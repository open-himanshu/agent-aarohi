# Work Log

## 2026-11-20 — Phase 1 audit and project continuity
- Re-inspected the repository before further changes.
- Confirmed Python 3.13.16 is installed; Python 3.12 is absent.
- Ran `py -3.13 -m pytest -q`: 5 passed.
- Confirmed current modules: SQLite schema/connection, minimal task persistence, risk policy, tool registry and basic CLI.
- Confirmed scheduler, configuration, structured logging and actual queue worker/retry/recovery are not implemented.
- Confirmed Git branch tracks origin/main and is synchronised. Untracked `Context/Chat 1.pdf` is intentionally not staged.
- Created/updated durable project context and Phase 1 acceptance checklist.
- Decision: do not start Phase 1B until Phase 1 acceptance gates pass and user approves.

## 2026-11-20 - VS Code Python 3.12 environment verified
- Selected the existing Conda ml interpreter in VS Code; no separate Python installation was needed.
- Verified python --version: Python 3.12.15.
- Verified sys.executable: C:\Users\himan\miniconda3\envs\ml\python.exe.
- Verified python -m pytest -q: 5 passed in 0.27s.
- Verified CLI about: Aarohi - modular, permissioned personal AI agent.
- Added workspace interpreter/Conda activation settings in .vscode/settings.json.
- Updated the Phase 1 checklist and persistent context. Phase 1 remains incomplete: configuration, structured logging, queue worker/retries/recovery, scheduler and deeper acceptance tests remain.

## 2026-11-20 - Central configuration module
- Added immutable validated settings and a dedicated configuration error type.
- Added `.env` loading without overriding process environment variables; validated AAROHI_ENV and AAROHI_LOG_LEVEL; added AAROHI_HOME and a stable derived database path.
- Updated CLI database operations to use central settings.
- Added tests for defaults, environment precedence, invalid values and dotenv precedence.
- Verification using the exact Conda ml Python 3.12.15 executable: 10 passed in 0.32s; targeted Ruff checks passed; configured-home init-db smoke test passed; git diff --check passed.
- Secret redaction and richer startup diagnostics remain pending; this task does not complete Phase 1.

## 2026-11-20 - Structured logging initial implementation
- Added JSON log formatting, console output, rotating UTF-8 log file (5 MB / 5 backups), and namespaced logger helper.
- Added recursive sensitive-key redaction plus common inline secret, Bearer and provider-key pattern redaction.
- CLI configures logging from Settings and records command start, database initialisation, task submission and missing-task events.
- Added six tests covering JSON output, redaction, rotation configuration and invalid levels.
- Verification on Python 3.12.15: 16 passed in 0.34s; targeted Ruff checks passed; CLI init-db smoke test confirmed JSON output in console and file; git diff --check passed.
- Redaction remains best-effort; SQLite audit detail redaction and full exception/error handling are still pending.

## 2026-11-20 — Memory-first priority decision
- User requested that Aarohi have reliable memory of relevant prior context and explicitly prioritised making memory reliable first.
- Updated the implementation order: memory foundation now precedes SQLite hardening and persistent job queue.
- Inspected the existing `src/aarohi/memory` directory; it currently contains only `__init__.py`, so no memory implementation is present.
- Inspected the existing SQLite schema and confirmed it currently stores tasks, task steps and audit events only. No memory tables or memory API exist.
- Memory design direction: local-first layered memory (working context, durable semantic facts/preferences/decisions, episodic task history), provenance and confidence, conflict/update/forget workflows, deterministic retrieval first, privacy controls, and restart-persistence tests.
- No application code changed in this decision update. Memory implementation is the next engineering task and must be inspected/designed against existing APIs before coding.

## 2026-11-20 — Memory foundation implementation
- Inspected the existing database, runtime, package configuration and tests before editing. Confirmed the memory package had no implementation and no database tests file existed.
- Added a SQLite `memories` table containing content, category, scope, source, confidence, confirmation status, lifecycle status and timestamps.
- Implemented `MemoryStore` save/get/search/update/archive/forget operations. Search is deterministic lexical token overlap with optional scope/category/confirmed filters; no embedding model or external service is used.
- Added basic rejection for common credential-like patterns and validation for confidence, metadata and search limits.
- Exposed `remember()` and `recall()` through `AgentRuntime`.
- Added six memory tests plus a runtime restart/recall integration test.
- Verification on the configured Conda Python 3.12.15: 23 passed in 1.76s. Targeted Ruff checks passed after formatting one pre-existing import block in `tests/test_runtime.py`. `git diff --check` passed.
- Remaining limitations: no automatic chat ingestion/summarisation, semantic search, conflict resolution, expiry, encryption, backup/export, CLI management, or automatic injection into task execution context. Credential detection is best-effort only.
- No commit or push. `Context/` remains untouched and untracked.


## 2026-11-20 — Memory intelligence layer
- Added conservative explicit capture: only statements beginning with a clear “remember” instruction are eligible; ordinary conversational statements are ignored.
- Added same-scope/category lexical similarity candidates. Similar records are flagged for review; no record is overwritten unless the caller supplies the matching memory ID. This detects near-duplicates/potential conflicts, not semantic contradictions.
- Added bounded task-context assembly. Only confirmed memories are selected, with scope, count and character limits; the selected context is persisted as a task-time snapshot in a dedicated SQLite table and returned by task inspection.
- Integrated capture/context methods into AgentRuntime. Task submission remains a planned record; no executor or external tool execution was introduced.
- Added five tests for explicit capture, review-before-replacement, bounded/scoped context, persisted task snapshots and secret-like content rejection.
- Verification on Conda Python 3.12.15: 28 tests passed; targeted Ruff checks passed; git diff --check passed (only expected LF/CRLF warnings).
- Remaining limitations: lexical retrieval only; similarity is not true contradiction detection; no automatic transcript ingestion/summarisation, semantic embeddings, retention/decay, encryption, backup/export or CLI memory commands. Context is snapshotted at task submission, not refreshed later.
- No commit or push. Context/ remains untouched and untracked.
- Explicit capture recognises English “remember” and Roman-Hinglish “yaad rakhna / yaad rakhiye / yaad rakho” prefixes; preference/decision classification includes common Hinglish markers. A regression test covers Hinglish capture.

## 2026-11-20 — Memory management CLI and privacy controls
- Added active-memory listing with scope/category filters and opt-in archived records.
- Added CLI list/search/update/archive/forget commands. Forget requires exact full-ID confirmation unless the user deliberately supplies --yes.
- Strengthened forget semantics: the memory row and its references in persisted task-context snapshots are removed in one SQLite transaction. Added a regression test for snapshot scrubbing.
- Documented plaintext-at-rest storage, best-effort credential detection, archive vs permanent deletion, no automatic expiry, and manual offline backup/restore limitations in docs/memory-privacy.md.
- Updated README usage examples.
- Verification on Conda Python 3.12.15: 34 passed in 3.95s; targeted Ruff checks passed; git diff --check passed; isolated CLI init-db and empty memory-list smoke test passed.
- No commit or push; Context/ remains untouched and excluded.

## 2026-11-20 — SQLite schema hardening and recovery
- Added two transactional schema migrations using PRAGMA user_version, including preservation of legacy rows and rejection of unsupported future schema versions.
- Added explicit BEGIN IMMEDIATE transaction helper, bounded busy timeout, integrity/foreign-key diagnostics and safe database backup/restore APIs.
- Added CLI db check, db backup and db restore commands; replacing an existing configured DB requires --yes.
- Added migration rollback, idempotence, transaction rollback, corruption rejection, backup/restore and CLI tests.
- Backed up the existing unversioned local database before migration to storage/backups/aarohi-pre-migration-20261120.db. Migration completed to schema version 2; quick_check and foreign_key_check passed.
- Added docs/database-operations.md and README usage.
- Verification on Conda Python 3.12.15: 44 tests passed in 2.23s; targeted Ruff checks passed; git diff --check passed; CLI db check returned healthy=true, schema_version=2, no foreign-key errors. Existing local DB still contains its original 1 task and 1 task step.
- No commit or push; Context/ remains untouched and excluded.


## 2026-11-20 — Persistent SQLite job queue

- Inspected the current schema, runtime, CLI and tests before implementation. Kept task submission in its existing planned state; no automatic task execution was introduced.
- Added schema migration v3 with a persistent jobs table, status constraints, unique idempotency keys and ready/lease indexes. Existing task and memory rows are preserved.
- Added JobQueue enqueue/get/list/claim/complete/fail APIs. Claims are transactional; worker leases use unique fencing tokens; expired leases can be reclaimed after process crashes.
- Added exponential retry backoff, max-attempt terminal failure, missing-handler fail-closed behaviour and queue lifecycle audit events.
- Added Worker dispatch that accepts only an explicit mapping of trusted handler names to callables. No arbitrary shell or user-supplied code execution.
- Added best-effort secret redaction/rejection for job payloads and stored handler errors. Secret detection remains pattern-based and is not a guarantee.
- Added CLI queue enqueue/list commands. The CLI deliberately does not launch an unattended worker.
- Documented at-least-once delivery: handlers with side effects must be idempotent because a process can crash after a side effect but before marking the job successful.
- Added tests for v2→v3 migration, persistence, idempotency, invalid payloads/secrets, exclusive claim, lease-token fencing, retry backoff, max attempts, crash recovery, handler allow-listing, handler failure, missing handlers and CLI operations.
- Verification on Conda Python 3.12.15: 57 tests passed. Targeted Ruff checks passed. `git diff --check` passed (only normal LF/CRLF warnings).
- Remaining queue limitations: no heartbeat/lease renewal, cancellation, manual retry, worker supervisor, graceful shutdown loop or unattended worker command. Task submission remains planned and is not automatically enqueued.
- No commit or push. `Context/` remains untouched and untracked; `.vscode/` remains untracked.


## 2026-11-20 — Scheduler, lease renewal and integration checks

- Added schema migration v4: persistent schedules table with enabled state, due timestamp, optional positive interval and due index. Existing jobs/tasks/memories preserved.
- Added `src/aarohi/scheduler.py`: one-shot and fixed-interval schedules, cancellation, listing and transactional due-run enqueue. A schedule occurrence and its queue job are committed in the same SQLite transaction; occurrence idempotency key is schedule ID + scheduled timestamp.
- Fixed-interval schedules skip missed backlog and advance to the next future interval; they do not burst through every missed run. This is elapsed-time scheduling, not local-calendar daily recurrence.
- Added CLI `schedule add/list/cancel/run-due`. `run-due` only enqueues; it does not run handlers. No background scheduler, Windows Task Scheduler registration or unattended process was enabled.
- Added `JobQueue.renew()` to extend a live lease only for its current token; stale/expired leases cannot be resurrected. No automatic heartbeat loop yet.
- Added tests for v3→v4 migration preserving queued jobs, one-shot schedule, interval/missed-run semantics, cancellation, validation, CLI timezone validation and lease renewal.
- First test run exposed one stale assertion that expected schema version 3; updated migration test to expect version 4. Final full suite: 66 passed in 6.05s on Conda Python 3.12.15.
- Targeted Ruff checks on changed queue/scheduler/database/CLI modules passed. `git diff --check` passed (normal LF/CRLF warnings only).
- Editable package build/install succeeded using `python -m pip install -e . --no-deps`. The `aarohi.exe` launcher remains blocked by Windows Application Control / PATH conditions; use the tested Python module entry pattern until that environment issue is resolved.
- Backed up actual database to `storage/backups/aarohi-pre-scheduler-20261120.db`, migrated it to schema v4, and verified CLI db check: integrity ok, no foreign-key errors, healthy=true. CLI schedule list, queue list and about smoke checks returned successfully.
- Remaining limitations: no scheduler daemon/OS registration, cron/calendar/DST semantics, automatic worker heartbeat, cancellation/manual retry, graceful shutdown/supervisor, complete CLI error-path coverage, fresh-clone test or Phase 1 sign-off.
- No commit or push. `Context/` untouched; `.vscode/` remains untracked.


## 2026-11-20 — Worker lease heartbeat and cooperative lifecycle

- Added a daemon heartbeat thread around each synchronous handler. It renews the current lease at a configurable interval; a failed or uncertain renewal marks ownership as lost and prevents the worker from acknowledging completion.
- Added Worker.run_forever(stop_event, poll_interval, max_jobs) for bounded polling and cooperative shutdown. The host must set the stop event; infrastructure errors propagate so an external process supervisor can decide whether to restart.
- Added validation for lease and polling settings. The worker remains restricted to application-supplied handler callables.
- Added tests for a handler that runs longer than its original lease, cooperative stop, and invalid lifecycle settings.
- Updated queue documentation and Phase 1 checklist.
- Verification: full Python 3.12.15 suite **69 passed in 8.96s**. Ruff initially caught one import-order issue; fixed it. git diff --check passed (only standard LF/CRLF warnings).
- Not implemented: OS service/daemon, signal handlers, automatic process restart supervisor, cancellation/manual retry, worker CLI, or unattended execution. Side-effecting handlers still require idempotency because delivery is at-least-once.
- No commit or push. Context/ untouched; .vscode/ untouched.


## 2026-11-20 — Stable source-checkout data directory

- Added source-checkout root discovery in config.py. When Aarohi runs from its source checkout, the default AAROHI_HOME now resolves from the package location rather than the shell's current working directory.
- Explicit AAROHI_HOME still takes precedence. If the package is installed without a source checkout/pyproject.toml, configuration falls back to the current working directory; production installs should set AAROHI_HOME explicitly.
- Added a regression test that changes the working directory and verifies source-checkout path stability.
- Verification: full Python 3.12.15 suite **70 passed in 8.42s**. Ruff initially identified an import style issue in the new test; fixed it and reran targeted Ruff successfully. git diff --check passed (standard LF/CRLF warnings only).
- Remaining CLI work: consistent user-facing error handling, health diagnostics, broad command/error-path coverage and fresh-clone setup test.
- No commit/push. Context/ and .vscode/ remain untouched.


## 2026-11-20 — Phase 1 acceptance hardening

- Added `health` CLI command reporting SQLite integrity/schema/foreign keys, queue-state counts, enabled schedules and the explicit `execution_enabled=false` boundary.
- Wrapped CLI execution with consistent exit codes and secret-redacted terminal errors. Updated existing CLI tests to assert the new stable error contract instead of expecting exceptions to escape.
- Added `WorkerSupervisor`: bounded in-process restart on infrastructure-level exceptions with exponential backoff and stop-event support. Handler failures remain governed by queue retry policy. This is not a Windows service or OS-level supervisor.
- Redacted common credential patterns from task-submission audit details and added a regression test. Queue lifecycle audit events and handler-error redaction already existed.
- Added `docs/operations.md`, documented health and operational limits in README, and corrected the default data-home documentation.
- Full suite: **77 passed in 8.74s** on Conda Python 3.12.15. Full-repository Ruff passed after fixing four import/style issues (including two pre-existing files); compileall passed; git diff --check passed.
- Fresh-clone-style verification: cloned the current Git repository to a temporary directory, overlaid the uncommitted working tree while excluding Context/, .vscode/ and local runtime data, installed editable, ran **77 tests passed in 8.82s**, and ran health successfully (schema v4, integrity ok, no FK errors). Restored the local editable install and removed the temporary clone.
- Actual local DB health: schema v4, integrity ok, foreign_key_errors empty, healthy true.
- Explicit remaining boundaries: no OS-level Windows service/signal supervisor, scheduler daemon, cancellation/manual retry UI, task executor/tool invocation/approval workflow, associated future audit events, database encryption or comprehensive secret detection. No unattended execution enabled.
- Phase 1 is ready for user acceptance review, not signed off. No Phase 1B work started. No commit/push. Context/ and .vscode/ untouched.
