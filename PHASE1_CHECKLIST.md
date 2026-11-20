# Phase 1 — Foundation Acceptance Checklist

Status key: [x] verified complete, [~] partial, [ ] not implemented, [!] blocked.

Phase 1 scope is the agreed foundation: configuration, logging, SQLite, scheduler, persistent job queue and CLI. This is a progress ledger, not a claim that Aarohi is autonomous.

## A. Project and environment
- [x] Local project exists at `C:\\PROJECTS\\Agent Aarohi`.
- [x] Product boundary documented: Aarohi is the agent; WealthCodeX is a specialist skill.
- [x] Git repository and main branch exist.
- [x] GitHub origin configured and main push verified.
- [x] README, agent specification and architecture decisions exist.
- [x] Python 3.12.15 installed and verified in the existing Conda ml environment.
- [x] Editable package installed and acceptance suite run under Python 3.12.15.

## B. Configuration
- [x] Central configuration module.
- [x] Environment-variable loading and validation.
- [x] Safe defaults and clear startup errors.
- [~] No secrets stored in source; structured log redaction, CLI error redaction, queue payload rejection/error redaction and task-submission audit redaction are implemented. Pattern-based detection remains best-effort and SQLite is plaintext at rest.

## C. Logging and audit
- [x] Structured JSON application logging with levels and file/console handlers.
- [x] Rotating file handler configured (5 MB, 5 backups); structured exception formatting and consistent CLI error reporting are covered.
- [x] SQLite audit_events table exists and records task submission plus queue lifecycle events.
- [x] Task submission audit event is recorded with common-pattern credential redaction.
- [~] Queue lifecycle audit events exist. Task transition, tool invocation/result and approval events are deferred until a task executor and approval workflow exist; those components are not part of the current foundation.
- [~] Sensitive values are redacted from structured logs and applicable task/queue audit details. Detection remains pattern-based and best-effort; SQLite audit storage is not encrypted or tamper-evident.

## D. SQLite persistence
- [x] SQLite connection helper and schema initialisation.
- [x] Foreign-key enforcement enabled.
- [x] Tables exist for tasks, task_steps and audit_events.
- [~] Basic task create/list/get persistence works.
- [x] Schema versioning/migration strategy (`PRAGMA user_version`, three transactional migrations, future-version guard).
- [x] Explicit transaction helper with rollback; migration rollback and failure-path tests.
- [x] SQLite online backup API, validated restore, explicit overwrite confirmation, CLI and recovery tests.

## E. Persistent job queue
- [~] Task records persist with planned status; task submission is not automatically executable.
- [~] Initial task step is recorded as pending; task/step lifecycle transitions remain separate from job state.
- [x] SQLite-backed queue with transactional enqueue and atomic worker claims.
- [x] Expiring leases, lease-token fencing and crash/restart reclaim.
- [x] Exponential retry backoff, configurable max attempts and terminal failure.
- [x] Idempotency keys prevent duplicate enqueue; handlers must be idempotent because delivery is at-least-once.
- [x] Explicit handler registry boundary; missing handlers fail closed; no arbitrary shell execution.
- [x] Queue audit events and CLI enqueue/list commands.
- [x] Worker heartbeat renews live leases during long-running synchronous handlers; uncertain renewal fails closed.
- [x] Cooperative worker polling loop supports stop-event shutdown and bounded job counts.
- [~] Added in-process WorkerSupervisor with bounded exponential restart on infrastructure failures. OS-level service management, signal-handler integration, cancellation/manual retry and unattended worker CLI remain absent by design.

## F. Scheduler
- [x] SQLite scheduler module and schema migration v4.
- [x] One-shot and fixed-interval schedule persistence.
- [x] Transactional occurrence enqueue with schedule/timestamp idempotency key.
- [x] Cancellation and CLI list/add/run-due commands.
- [x] Missed interval behaviour tested: skip stale backlog and advance to next future interval.
- [~] Scheduler is manually invoked; no background service or Windows Task Scheduler registration.
- [x] No unattended execution; run-due only enqueues jobs and never invokes handlers.

## G. CLI
- [x] `about` command.
- [x] `init-db` command.
- [x] `submit` command.
- [x] `tasks` command.
- [x] `show` command.
- [x] Manual smoke checks passed for core task, database, queue, schedule and memory command paths.
- [~] Automated CLI tests cover principal commands and common validation/failure cases; not every memory subcommand and argparse branch has an individual test.
- [x] `db check` integrity/schema/foreign-key diagnostics and `health` report for DB, queue counts, enabled schedules and execution-disabled status.
- [x] Source-checkout default data home resolves from the package location, independent of the shell's current working directory; AAROHI_HOME remains the explicit override.

## H. Quality gates
- [x] pytest: 5 passed on Python 3.12.15 (VS Code Conda ml environment).
- [x] Earlier compileall check passed.
- [x] Earlier git diff --check passed.
- [x] Full current test suite under Python 3.12.15: 77 passed, including worker supervisor, CLI errors, health and audit redaction.
- [x] Full-repository Ruff check passes.
- [x] `compileall`, `git diff --check`, editable package install and actual DB health check pass.
- [x] Temporary Git clone + current working-tree overlay installed successfully; 77 tests passed and fresh-clone health command reported schema v4 healthy. Local editable install restored afterwards.
- [ ] Phase 1 acceptance review and user sign-off.

## Current assessment
- Core Phase 1 implementation and integration checks are complete for the current architecture: configuration, logging, SQLite, memory foundation, queue, worker heartbeat/restart supervisor, scheduler, CLI diagnostics and packaging.
- Remaining explicit limitations: no OS-level Windows service/signal supervisor, no automatic scheduler daemon, no cancellation/manual retry UI, no executor/tool/approval lifecycle (therefore those audit events do not yet exist), plaintext SQLite and best-effort secret detection. These are documented and must not be represented as implemented.
- Current verification: 77 tests passed on Python 3.12.15; full Ruff, compileall, git diff --check, editable install, temporary Git clone + working-tree overlay installation/tests/health, and actual database schema-v4 health all passed.
- Phase 1 is **ready for final user acceptance review**, not yet signed off. No Phase 1B work has started.
- Do not calculate an overall percentage by counting checkboxes: items have different engineering weights. Track each section and acceptance gate instead.

## Definition of done
Phase 1 is complete only when configuration, logging, SQLite persistence, persistent queue, scheduler and CLI are implemented, tested together under Python 3.12, and the critical failure/restart paths are verified. Then request explicit user sign-off before Phase 1B.

## Memory subsystem — newly prioritised (before SQLite hardening and queue)
- [~] Durable confirmed facts/preferences/decisions are implemented; separate episodic history and a distinct short-lived working-memory tier are not.
- [x] Store provenance, timestamps, scope, confidence/confirmation status and lifecycle metadata.
- [x] Implement explicit create/read/update/archive/forget operations with review-before-replacement.
- [x] Implement deterministic lexical retrieval with relevance and scope filters; semantic retrieval is not implemented.
- [x] Persist across runtime recreation and test retrieval/update/forget behaviour.
- [~] Enforce privacy boundaries and reject common secret patterns; detection is best-effort and SQLite is not encrypted.
- [x] Integrate confirmed memory context snapshots with task submission without granting unrestricted tool access.
- [x] Document current backup/export and data-retention behaviour and limitations (manual offline DB copy; no automated export/backup/expiry).

Historical priority order (implemented): reliable memory foundation → SQLite hardening/migrations/backup → persistent job queue/recovery → scheduler → worker heartbeat/restart policy → CLI health/error handling → fresh-clone-style integration acceptance. Remaining gate: final user review/sign-off. Memory work does not authorise Phase 1B by itself.

### Memory implementation progress — 2026-11-20
- [x] SQLite memory records with provenance, confidence, confirmation, scope and lifecycle metadata.
- [x] Save/read/update/archive/permanent-forget API.
- [x] Deterministic lexical retrieval with scope/category/confirmation filters.
- [x] Persistence across runtime recreation verified.
- [x] Basic credential-pattern rejection and tests.
- [x] Runtime exposes `remember()` and `recall()`; confirmed memories are assembled into bounded task-submission snapshots. No executor is implemented.
- [x] Explicit remember-command capture; ordinary statements are not automatically ingested.
- [x] Similarity-based conflict candidates; replacement requires an explicit matching memory ID.
- [x] Bounded task-context assembly; only confirmed memories are injected and a snapshot is persisted per task.
- [ ] Semantic retrieval, robust contradiction detection, encryption, automated export/backup and retention controls.
- [x] CLI memory inspection/management commands (list/search/update/archive/forget; forget requires explicit confirmation).

Memory is now the active priority. The intelligence layer supports explicit capture, conservative similarity-based review and confirmed-only task context snapshots. Semantic retrieval and automatic conversation ingestion are not implemented.
