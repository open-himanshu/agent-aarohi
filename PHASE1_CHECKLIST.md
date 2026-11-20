# Phase 1 — Foundation Acceptance Checklist

Status key: [x] verified complete, [~] partial, [ ] not implemented, [!] blocked.

Phase 1 scope is the agreed foundation: configuration, logging, SQLite, scheduler, persistent job queue and CLI. This is a progress ledger, not a claim that Aarohi is autonomous.

## A. Project and environment
- [x] Local project exists at `C:\\PROJECTS\\Agent Aarohi`.
- [x] Product boundary documented: Aarohi is the agent; WealthCodeX is a specialist skill.
- [x] Git repository and main branch exist.
- [x] GitHub origin configured and main push verified.
- [x] README, agent specification and architecture decisions exist.
- [!] Python 3.12 installed and verified — only Python 3.13.16 is installed.
- [ ] Install editable package and run acceptance suite under Python 3.12.

## B. Configuration
- [ ] Central configuration module.
- [ ] Environment-variable loading and validation.
- [ ] Safe defaults and clear startup errors.
- [ ] Secret redaction; no secrets stored in source/database/logs.

## C. Logging and audit
- [ ] Structured application logging with levels and file/console handlers.
- [ ] Log rotation and safe error reporting.
- [~] SQLite audit_events table exists.
- [~] Task submission audit event is recorded.
- [ ] Audit events for task lifecycle, tool invocation, result, failure and approval.
- [ ] Verify sensitive values are redacted from logs/audit details.

## D. SQLite persistence
- [x] SQLite connection helper and schema initialisation.
- [x] Foreign-key enforcement enabled.
- [x] Tables exist for tasks, task_steps and audit_events.
- [~] Basic task create/list/get persistence works.
- [ ] Schema versioning/migration strategy.
- [ ] Transaction and failure-path tests.
- [ ] Backup/restore procedure and test.

## E. Persistent job queue
- [~] Task records persist with planned status.
- [~] Initial task step is recorded as pending.
- [ ] Queue worker and safe job claiming.
- [ ] Explicit task/step state transitions.
- [ ] Retry policy, backoff and max-attempt handling.
- [ ] Crash recovery for interrupted/running jobs.
- [ ] Duplicate/idempotency protection.

## F. Scheduler
- [ ] Scheduler module and configuration.
- [ ] Scheduled job persistence and duplicate prevention.
- [ ] Windows Task Scheduler integration or documented scheduler strategy.
- [ ] Start/stop/status and missed-run behaviour tested.
- [ ] No unattended execution until worker, recovery and monitoring pass.

## G. CLI
- [x] `about` command.
- [x] `init-db` command.
- [x] `submit` command.
- [x] `tasks` command.
- [x] `show` command.
- [~] Basic manual smoke checks passed.
- [ ] CLI tests for all commands and error cases.
- [ ] Health/status/diagnostics command.
- [ ] Reliable project data path independent of current working directory.

## H. Quality gates
- [x] pytest: 5 passed on installed Python 3.13.16.
- [x] Earlier compileall check passed.
- [x] Earlier git diff --check passed.
- [ ] Full test suite under Python 3.12.
- [ ] Lint/type checks and packaging/install test.
- [ ] Fresh clone setup test.
- [ ] Phase 1 acceptance review and user sign-off.

## Current assessment
- Fully verified checklist items: project/Git basics, SQLite initialisation/schema, basic CLI commands, basic task persistence, basic policy and tool registry.
- Partial: configuration, logging, queue, scheduler and audit are not complete; most have only placeholders or no implementation.
- Current test result: 5 passed on Python 3.13.16.
- Python 3.12 remains a blocker because pyproject.toml explicitly requires Python >=3.12,<3.13.
- Phase 1 is **partially complete, not ready for Phase 1B**.
- Do not calculate an overall percentage by counting checkboxes: items have different engineering weights. Track each section and acceptance gate instead.

## Definition of done
Phase 1 is complete only when configuration, logging, SQLite persistence, persistent queue, scheduler and CLI are implemented, tested together under Python 3.12, and the critical failure/restart paths are verified. Then request explicit user sign-off before Phase 1B.
