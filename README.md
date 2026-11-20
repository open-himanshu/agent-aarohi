# Agent Aarohi

Aarohi is a modular, local-first AI agent for carrying out goal-oriented work through approved tools and specialised skills. It is not a YouTube-only automation script.

## Product direction

- **Agent identity:** Aarohi
- **Workspace:** `C:\\PROJECTS\\Agent Aarohi`
- **Runtime target:** Windows, Python 3.12
- **Architecture:** modular monolith first; provider- and skill-based extensions
- **Initial flagship skill:** WealthCodeX content research, production and distribution
- **Future skills:** added only when designed, tested and permissioned

## Agent vs automation

A fixed automation executes a predefined pipeline. Aarohi should accept a goal, understand the context, make a plan, select tools/skills, execute bounded steps, inspect results, recover from safe failures and report what happened. It must not invent success or silently exceed granted permissions.

## Core architecture (planned)

1. **Agent runtime** — task lifecycle, planner/executor loop, cancellation and resumability.
2. **Tool registry** — discoverable tools with typed input/output contracts.
3. **Skills** — isolated domain capabilities (WealthCodeX is the first skill, not the whole agent).
4. **Memory and state** — SQLite initially; explicit separation of task state, user-approved preferences and searchable knowledge.
5. **Permission and policy layer** — least privilege, risk classification, approval for sensitive actions.
6. **Audit and recovery** — append-only action history, checkpoints, idempotency and compensating/rollback actions where possible.
7. **Interfaces** — CLI first; dashboard and remote/mobile control later.
8. **Providers** — replaceable LLM, speech, media and external-service adapters.

## Safety boundaries

- No secrets in source code, SQLite or logs.
- No destructive filesystem, OS, financial or account action without appropriate explicit approval.
- No unrestricted shell execution as the default tool.
- Keep a human-visible audit trail; report uncertainty and failures.
- External publishing is gated by factual, licensing, quality and platform-policy checks.
- Do not enable unattended schedules until the worker, recovery and monitoring paths pass tests.

## First milestone

Build and test the agent foundation before expanding the WealthCodeX skill: configuration, structured logging, SQLite, task/job state machine, tool contracts, permission checks, audit events and CLI. Then verify the existing Phase 1 starter files before integrating or changing them.

## Current status

- Workspace directory created.
- No application code has been copied or executed in this folder yet.
- Python 3.12 and GitHub repository setup remain to be verified.
- Publishing and unattended scheduling remain disabled.
