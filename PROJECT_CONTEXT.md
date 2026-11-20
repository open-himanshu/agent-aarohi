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
- Python installed: 3.13.16 only. Python 3.12 is not installed.
- pyproject.toml requires >=3.12,<3.13, so install/test under Python 3.12 remains an acceptance blocker.
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
- Tests currently pass: 5 passed using installed Python 3.13.16.
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
- Python 3.12 acceptance has not been tested.

## Working protocol for every future chat
1. Read PROJECT_CONTEXT.md and PHASE1_CHECKLIST.md before doing project work.
2. Inspect current Git status and latest commits before editing.
3. Work one small task at a time.
4. After each task, report: task name, completion percentage/status, files changed, tests/commands run and exact results, blockers, next task.
5. Update PHASE1_CHECKLIST.md, docs/WORK_LOG.md and this context file when durable project state changes.
6. Commit completed, tested changes; push and verify GitHub sync when appropriate.
7. Never claim a feature works unless it was run and verified.
8. Do not begin Phase 1B until Phase 1 acceptance criteria are met and the user agrees.

## Immediate next action
Finish Phase 1 acceptance checklist first. Do not start the execution engine (Phase 1B) until the user reviews and approves the checklist.
