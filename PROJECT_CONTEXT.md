# Agent Aarohi — Persistent Project Context

Last verified: 2026-11-20
Workspace: C:\\PROJECTS\\Agent Aarohi
Repository: https://github.com/open-himanshu/agent-aarohi
Branch: main

## Product identity
- Product/agent name: Agent Aarohi.
- Aarohi is a general-purpose, local-first AI agent; WealthCodeX is its first specialist skill, not the whole product.
- Build a modular monolith first; SQLite initially.
- Target: Windows + Python 3.12. Prefer free/open-source and low-cost components.
- No unrestricted shell execution. Destructive OS/security/credential/bulk-delete actions denied by default.
- External/account/publishing actions require explicit permission and approval.
- Keep credentials out of source, SQLite and logs.
- Build durable jobs, retries, audit history, duplicate protection and recovery before unattended operation.
- Never bypass factual, copyright or platform policy checks.

## WealthCodeX skill (locked direction)
- Existing WealthCodeX channel.
- Hinglish (Roman script), 45–60 seconds, cinematic documentary.
- Content mix: 50% gaming industry/economics, 30% AI/emerging technology, 20% business/innovation.
- One daily story/master video; separate platform metadata and publishing jobs.
- Target platforms: YouTube, Instagram, Facebook, X, TikTok, LinkedIn, subject to API access and policy.
- One consistent fictional female virtual presenter and female Hinglish voice; clearly disclose virtual/AI nature; do not imitate a real person without permission.
- Source provenance, factual verification, media licensing and hard quality gates required. Failed content is quarantined.
- Shadow mode before autonomous publishing.

## Local environment (verified)
- Windows device: PAPER.
- Python environment: Miniconda Conda ml at C:\Users\himan\miniconda3\envs\ml\python.exe, Python 3.12.15. VS Code workspace selects this interpreter and activates it in new terminals.
- pyproject.toml requires >=3.12,<3.13; the existing ml environment satisfies this. Verified in VS Code terminal.
- Git is installed.
- Laptop: 16 GB RAM, integrated GPU; do not assume an always-on local LLM.

## Repository state (verified)
- Local path: C:\\PROJECTS\\Agent Aarohi
- GitHub origin: https://github.com/open-himanshu/agent-aarohi.git
- Branch: main, tracking origin/main.
- Latest verified commit at context creation: 2fd664e (merge GitHub initial README history).
- Local status: main...origin/main, clean except untracked Context/ folder containing the supplied Chat 1.pdf. Do not silently add this PDF to Git.
- Earlier commits: 00d1cbd, ae2281e, c6b658e, 2fd664e.

## Implemented so far
- SQLite tables for tasks, task_steps and audit_events; database initialisation and connection helper.
- Basic task submission/list/show runtime. Submitted tasks remain planned; no actual execution.
- Deterministic risk policy: read allowed; reversible/external require approval; destructive denied.
- In-memory tool registry with duplicate-name protection.
- CLI commands: about, init-db, submit, tasks, show.
- README, AGENT_SPEC.md and architecture decision records.
- Tests pass under Python 3.12.15: 5 passed in 0.27s. CLI about smoke test prints: Aarohi - modular, permissioned personal AI agent.
- Manual CLI smoke checks previously passed for about, init-db, submit and tasks.
- GitHub remote configured and push verified.

## Phase 1 gaps — do not claim complete
- Configuration module and validated settings are not implemented.
- Structured logging is not implemented.
- SQLite exists but needs hardening, schema/version migration strategy and fuller integration tests.
- Persistent queue is only a planned-task record; no worker, claim/lease, retry/backoff or recovery.
- Scheduler is not implemented; no Windows Task Scheduler registration.
- CLI is a basic scaffold; no status/health/diagnostic command.
- Tool registry and permission policy are not yet connected to an executor.
- Audit table exists and task submission is recorded, but full audit lifecycle/events and tamper-resistance are not implemented.
- Python 3.12.15 test acceptance is now verified for the current five-test suite; broader integration/recovery acceptance remains outstanding.

## Working protocol for every future chat
1. Read PROJECT_CONTEXT.md and PHASE1_CHECKLIST.md before doing project work.
2. Inspect current Git status and latest commits before editing.
3. Work one small task at a time.
4. After each task, report: task name, completion percentage/status, files changed, tests/commands run and exact results, blockers, next task.
5. Update PHASE1_CHECKLIST.md, docs/WORK_LOG.md and this context file when durable project state changes.
6. Commit completed, tested changes; push and verify GitHub sync when appropriate.
7. Never claim a feature works unless it was run and verified.
8. Do not begin Phase 1B until Phase 1 acceptance criteria are met and the user agrees.

## Latest verification - 2026-11-20
- VS Code selected the existing Conda ml interpreter; the new terminal activated the ml environment automatically.
- `python --version`: Python 3.12.15.
- `sys.executable`: `C:\Users\himan\miniconda3\envs\ml\python.exe`.
- `python -m pytest -q`: 5 passed in 0.27s.
- CLI `about` smoke test passed.
- `.vscode/settings.json` configures the workspace interpreter and Conda terminal activation.

## Immediate next action
Finish Phase 1 acceptance checklist first. Do not start the execution engine (Phase 1B) until the user reviews and approves the checklist.

## Configuration module � first implementation complete
- Added `src/aarohi/config.py` with immutable `Settings`, `ConfigurationError`, `.env` loading, environment-variable precedence, validation and safe defaults.
- Supported settings: `AAROHI_ENV` (development/test/production), `AAROHI_LOG_LEVEL` (DEBUG/INFO/WARNING/ERROR/CRITICAL), `AAROHI_HOME`.
- Default data home is the resolved project/current working directory; database path is `<home>/storage/aarohi.db`.
- CLI database commands now use central settings through `load_settings()`.
- Added five configuration tests. Verified with Python 3.12.15: 10 total tests passed; targeted Ruff checks passed; CLI init-db smoke test created the database at configured AAROHI_HOME.
- Secret redaction is not implemented yet; `.env` loading is deliberately simple KEY=VALUE parsing and does not support shell expansion or multiline values.

## Structured logging module - initial implementation complete
- Added `src/aarohi/logging_config.py`: JSON formatter, console handler, rotating UTF-8 file handler, namespace logger helper, and recursive/common-pattern secret redaction.
- Logs are written to `<AAROHI_HOME>/logs/aarohi.log`; rotation defaults to 5 MB with 5 backups.
- CLI database/task commands configure logging from central Settings and record command/task events.
- Redaction covers sensitive structured keys (password, secret, token, API key, authorization, access key), inline assignments, Bearer values and common `sk-` provider keys.
- Added six logging tests. Python 3.12.15: 16 total tests passed; targeted Ruff checks passed; CLI init-db smoke test emitted structured JSON to console and file.
- Limitations: this is best-effort pattern-based redaction, not a guarantee against every proprietary credential format. SQLite audit detail redaction and broad exception handling remain outstanding.

## Memory-first priority update - 2026-11-20
- User explicitly changed implementation priority: reliable Aarohi memory is the next engineering priority, before SQLite hardening and the persistent job queue.
- Memory must preserve useful prior context across conversations and tasks so the user does not need to repeatedly restate project state, decisions and preferences.
- Design memory as a layered, local-first subsystem: (1) working context for the active task, (2) durable semantic facts/preferences/project decisions, (3) episodic history of completed tasks and important events, and (4) provenance/source references with timestamps and confidence.
- Required behaviours: deliberate memory writes, retrieval by relevance, conflict detection and updates, stale-memory handling, explicit correction/forget workflows, privacy boundaries, and tests proving persistence across process restarts.
- Do not blindly store every conversation or treat inferred facts as confirmed. Preserve source, timestamp, confidence/status and scope; distinguish user-confirmed facts from assistant inferences.
- Memory storage will use the existing local-first SQLite direction, but schema design must support versioning and safe migrations. Avoid introducing a separate vector database or paid embedding service at this stage; begin with deterministic metadata/full-text retrieval and evaluate semantic retrieval only when justified.
- Memory implementation is not yet started. First inspect current memory-related modules and database/runtime APIs, then implement a small tested memory foundation. SQLite hardening and persistent queue follow memory acceptance.

## Memory subsystem — first implementation (2026-11-20)
- Added `memories` table to the existing SQLite schema with category, scope, source/provenance, confidence, confirmed flag, active/archived status, timestamps and last-access metadata.
- Added `src/aarohi/memory/store.py` and exported `MemoryStore`.
- Implemented save, get, deterministic token-overlap search with scope/category/confirmed filters, update, archive and permanent forget.
- Added basic credential-pattern rejection before saving/updating content/source. This is a safety filter, not a guarantee that all secrets are detected.
- Integrated `MemoryStore` into `AgentRuntime` through `remember()` and `recall()`.
- Added tests for persistence across runtime recreation, retrieval/filtering, update/archive/forget, validation and credential rejection.
- Verification on Conda Python 3.12.15: 23 tests passed; targeted Ruff checks passed after import formatting; `git diff --check` passed.
- Limitations: retrieval is lexical, not semantic; no automatic conversation summarisation/ingestion, memory conflict resolution, expiry/decay, encryption, export/backup, or CLI memory commands yet. Memory is not automatically injected into task execution because no task executor/context assembler exists.
- Memory foundation is partial, not complete. Next: add explicit memory policy and lifecycle tests, improve secret handling, integrate controlled recall into task context assembly, then harden SQLite migrations/backup before queue work.


## Memory intelligence layer — 2026-11-20
- Added src/aarohi/memory/policy.py with MemoryManager.
- capture_explicit() only captures statements with an explicit “remember” prefix. Ordinary statements are ignored; no blind conversation ingestion.
- MemoryStore.find_conflicts() finds same-scope/category records with lexical Jaccard similarity. These are review candidates, not proof of contradiction.
- MemoryStore.curate() refuses silent replacement. A caller must explicitly provide the matching replace_id to update a candidate.
- build_context() uses deterministic lexical retrieval, only confirmed memories, optional scope, maximum item count and maximum character budget.
- AgentRuntime.submit() attaches a bounded memory snapshot to each planned task in the new task_context table. get_task() returns memory_context with provenance and confirmation metadata. This is context assembly only; no executor exists yet.
- Added tests covering explicit capture, conflict review/replacement, scoped/bounded context, persisted snapshots and credential-like rejection.
- Verified with Conda Python 3.12.15: 28 tests passed; targeted Ruff checks passed; git diff --check passed.
- Limitations: lexical search only; similarity does not understand semantic contradiction; no automatic transcript ingestion/summarisation, embeddings, expiry/decay, encryption, export/backup or CLI memory commands. Context snapshots do not refresh after task creation.
- No commit/push. Context/ is still excluded from staging and untouched.

## Immediate next action
Continue memory acceptance with CLI memory inspection/correction commands and tests, then document privacy/backup behaviour. After memory acceptance, proceed to SQLite schema versioning/migrations and backup/restore, then the persistent queue. Do not start Phase 1B without explicit approval.
- Explicit capture recognises English remember-prefix commands and Roman-Hinglish yaad-rakhna variants. This is prefix-based deterministic capture, not natural-language understanding of arbitrary conversations.

## Memory CLI and privacy controls — implementation update (2026-11-20)
- Added MemoryStore.list_memories() with active-by-default listing, scope/category filters, bounded limits and opt-in archived records.
- Added CLI commands: memory list, memory search, memory update, memory archive, memory forget.
- Permanent forget displays the target record and requires typing the full memory ID; --yes is an explicit non-interactive confirmation switch.
- Forget now deletes the memory row and removes its ID from persisted task-context snapshots in the current database, within the same SQLite transaction.
- Added docs/memory-privacy.md documenting plaintext-at-rest storage, best-effort secret detection, archive-vs-forget, retention, manual offline backup/restore and backup limitations.
- Updated README with memory CLI examples and privacy documentation pointer.
- Added CLI and forget-snapshot regression tests. Verified with Conda Python 3.12.15: 34 tests passed in 3.95s; targeted Ruff checks passed; git diff --check passed; isolated CLI init-db and memory-list smoke test passed.
- Important limitations remain: no database encryption, automatic retention/expiry, automated backup/export, semantic search or scrubbing of copies in external backups and independent task/audit/log text.
- No commit/push. Do not stage Context/.

## SQLite hardening — implementation update (2026-11-20)
- Replaced unversioned schema bootstrap with PRAGMA user_version migrations. Version 1 creates any missing tables/indexes while preserving legacy rows; version 2 adds task-step and task-context indexes. Future schema versions are rejected.
- Added 10-second SQLite lock timeout, explicit BEGIN IMMEDIATE transaction helper, rollback on exceptions and database diagnostics using quick_check/foreign_key_check.
- Added validated SQLite online backup and restore APIs. Backup creation uses a temporary file and integrity verification; restoring an existing DB requires explicit overwrite consent and uses SQLite's backup API. Windows users must stop Aarohi processes before restore.
- Added CLI: db check, db backup DESTINATION, db restore SOURCE --yes.
- Added migration, rollback, integrity, backup, restore and CLI tests. Existing local storage/aarohi.db was version 0 with one task and one task step; backed it up to storage/backups/aarohi-pre-migration-20261120.db before migrating it to schema version 2. Integrity and foreign-key checks reported healthy. Record counts are being rechecked.
- Added docs/database-operations.md and README instructions. Verified on Conda Python 3.12.15: 44 tests passed; targeted Ruff checks passed; git diff --check passed; CLI db check passed. Actual database is schema v2 with one task and one task step preserved.
- No commit/push. Context/ remains untouched and untracked.


## Persistent job queue — implementation update (2026-11-20)

- Added SQLite schema migration v3. The `jobs` table stores handler name, JSON payload, state, attempt count/limit, next eligible time, lease owner/token/expiry, idempotency key, last error and timestamps. Ready and lease indexes added.
- Added `src/aarohi/queue.py` with `JobQueue` and `Worker`.
- Queue API: enqueue/get/list/claim/complete/fail. Enqueue is transactional; supplied idempotency keys return the existing job instead of creating duplicates.
- Claim uses `BEGIN IMMEDIATE`, increments attempts and issues a unique lease token. Expired jobs can be reclaimed after a worker crash. Expired attempts at the configured limit become terminal failures.
- Completion/failure requires the current unexpired lease token, fencing off stale workers.
- Retry delay is exponential and bounded by a configurable maximum; max attempts are enforced.
- Worker runs only handlers explicitly provided in its handler mapping. Missing handlers fail terminally; arbitrary shell execution is not supported.
- Queue audit events record queued, claimed, retry-scheduled, succeeded and failed transitions.
- Added CLI `queue enqueue` and `queue list`. No CLI worker loop or unattended worker process.
- Payloads that match existing secret-redaction patterns are rejected; handler errors are redacted before storage. Detection is best-effort.
- Delivery is at-least-once, not exactly-once. Side-effecting handlers must be idempotent and verify outcomes. A crash after a side effect but before success acknowledgement can cause a retry.
- Task submission remains planned and is not automatically enqueued or executed.
- Documentation: `docs/job-queue.md`; README updated.
- Verification: 58 tests passed on Conda Python 3.12.15; targeted Ruff checks passed; `git diff --check` passed.
- Remaining work: lease heartbeat/renewal, cancellation/manual retry, supervised worker lifecycle, scheduler and full Phase 1 integration acceptance.
- No commit/push. Do not touch or stage `Context/`; do not stage `.vscode/` without approval.

## Immediate next task

Implement the scheduler only after reviewing queue lifecycle constraints. Then complete Phase 1 integration acceptance, CLI/error-path coverage, packaging and fresh-clone checks. Do not begin Phase 1B until Phase 1 acceptance criteria pass and the user explicitly approves.


## Scheduler and worker lease update (2026-11-20)

- Schema is now version 4. Migration v4 adds persistent `schedules` and due index.
- `src/aarohi/scheduler.py`: one-shot and fixed-interval schedule creation/list/cancel/run_due.
- Due occurrence and corresponding job insertion happen in one SQLite transaction. Idempotency key is `schedule:<schedule_id>:<scheduled_timestamp>`.
- Interval schedules skip missed occurrences and calculate the next future run; no burst catch-up. Intervals are elapsed-time, not local-calendar recurrence. No cron/DST/calendar rules.
- CLI commands: `schedule add`, `schedule list`, `schedule cancel`, `schedule run-due`. ISO timestamps must include timezone. `run-due` enqueues only; it does not execute handlers.
- No scheduler daemon, Windows Task Scheduler registration or unattended process.
- Added `JobQueue.renew(job_id, lease_token, lease_seconds=...)`; only current unexpired lease owner can renew. No automatic worker heartbeat loop yet.
- Docs: `docs/scheduler.md`; README updated.
- Verification: full suite 66 passed on Conda Python 3.12.15; targeted Ruff passed; git diff --check passed; editable package build/install succeeded.
- Actual DB backed up to `storage/backups/aarohi-pre-scheduler-20261120.db`, migrated v3→v4 and CLI db check reported healthy=true, integrity ok, no foreign-key errors. CLI schedule list, queue list and about smoke checks passed.
- `aarohi.exe` launcher remains blocked by Windows Application Control/PATH; Python module entry pattern is the current verified invocation route.
- Remaining Phase 1 work: worker heartbeat loop/supervisor, cancellation/manual retry, graceful shutdown, broad CLI error-path coverage, reliable data path independent of current working directory, fresh-clone verification and final acceptance.
- No commit/push; `Context/` untouched; do not stage `.vscode/` without approval.


## Worker lifecycle update — 2026-11-20
- Worker now runs a daemon heartbeat thread while a synchronous handler is executing and renews its current lease at a configurable interval. Renewal errors or lease loss fail closed; the worker will not acknowledge success with uncertain ownership.
- Added run_forever(stop_event, poll_interval, max_jobs) for cooperative polling/shutdown. The host application must set the stop event. Infrastructure errors propagate to an external supervisor.
- Added tests for long-running handler renewal, cooperative stop and invalid lifecycle settings.
- Full suite: 69 passed on Conda Python 3.12.15. Targeted Ruff and git diff --check passed after import sorting.
- Not present: OS-level service/daemon, signal integration, automatic process restart policy, cancellation/manual retry, worker CLI or unattended operation. At-least-once side-effect duplication risk remains.
- No commit/push. Context/ and .vscode/ remain untouched.


## Stable data path update — 2026-11-20
- config.py now discovers the source-checkout root from the package location (pyproject.toml) and uses it as the default AAROHI_HOME, independent of the shell's current working directory.
- AAROHI_HOME continues to override the default. For a non-editable installed package where the source checkout is not present, discovery falls back to CWD; deployment should set AAROHI_HOME explicitly.
- Regression test changes the working directory and checks the resolved source-checkout home.
- Full suite: 70 passed on Python 3.12.15; targeted Ruff and git diff --check passed.
- Remaining: CLI diagnostics/error handling, full CLI error-path coverage, fresh-clone setup and final Phase 1 acceptance.


## Phase 1 acceptance hardening — 2026-11-20
- Added CLI `health`: checks SQLite integrity/schema/foreign keys and reports queue counts, enabled schedules and `execution_enabled=false`.
- CLI now returns stable handled-error exit codes (2 validation/operational, 130 interrupt, 1 unhealthy DB) and prints common-pattern-redacted errors. Existing CLI tests updated for this contract.
- Added `src/aarohi/worker_supervisor.py`: bounded in-process restart with exponential backoff for infrastructure errors; queue-managed handler failures do not restart the process. No Windows service, signal registration or unattended worker CLI.
- Task-submission audit details now redact common inline credentials; test added. Queue lifecycle audit events exist. Tool/result/approval audit events await the future executor/approval components.
- Added `docs/operations.md`, README health usage, and updated Phase 1 checklist/work log.
- Verification: 77 tests passed on Python 3.12.15; full-repo Ruff, compileall, git diff --check passed. Temporary Git clone + current worktree overlay editable install passed; 77 tests and health check passed. Local editable installation restored.
- Actual database health: schema v4, integrity ok, no FK errors, healthy true.
- Remaining limitations documented: no OS-level Windows service/signal supervisor, scheduler daemon, cancellation/manual retry UI, executor/tool/approval lifecycle, encrypted DB or comprehensive secret detection. Unattended execution remains disabled.
- Phase 1 is ready for final user acceptance review, not yet signed off. No Phase 1B, commit or push.
