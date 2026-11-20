# Agent Aarohi — Product and Engineering Specification

## 1. Mission

Build a dependable personal AI agent that can understand user goals and complete multi-step work through a controlled set of tools and specialised skills. You interact with Aarohi as an agent, not merely as a video-generation button.

## 2. Product boundary

Aarohi is the agent platform. WealthCodeX is its first business skill/use case: researching, producing and distributing original 45–60 second Hinglish cinematic-documentary videos. The agent core must remain independent of that skill so other useful skills can be added without rewriting the runtime.

## 3. Agent operating loop

1. Receive a goal and clarify only essential ambiguity.
2. Inspect available context, memory and tool capabilities.
3. Create a visible, bounded plan with success conditions.
4. Classify action risk and check permissions.
5. Execute one step at a time using registered tools.
6. Verify outputs rather than trusting tool intent.
7. Retry/recover only when safe and idempotent.
8. Record actions, decisions, outputs and failures.
9. Return a concise completion report and next step.

The planner must not be allowed to bypass policy or permission checks. LLM output is a proposal, not an authority.

## 4. Core modules

- `agent/`: runtime, planner interface, executor, task manager
- `tools/`: typed tool registry and adapters
- `skills/`: domain workflows; `wealthcodex/` is the first skill
- `memory/`: SQLite-backed task state and controlled memory
- `security/`: permission policy, risk levels, secret handling
- `audit/`: event log, checkpoints and recovery metadata
- `interfaces/`: CLI first; dashboard/remote interface later
- `providers/`: replaceable model, voice and media providers
- `tests/`: unit, integration and safety tests

## 5. Permissions

- Read-only actions: allowed only within configured workspace/scope.
- Reversible edits: require a checkpoint and scoped permission.
- External communication, publishing, purchases, account changes and sensitive data access: require explicit policy and account authorisation; high-impact actions require user approval.
- Destructive OS, credential, security or bulk-delete actions: denied by default.
- Never store API keys, OAuth tokens or passwords in source files, SQLite records or logs.

## 6. WealthCodeX initial skill

- Language: Hinglish (Roman script)
- Duration: 45–60 seconds
- Visual identity: cinematic documentary
- Content mix: 50% gaming industry/economics, 30% AI/emerging technology, 20% business/innovation
- One consistent fictional female virtual presenter and female Hinglish voice; disclose AI/virtual nature.
- One master video, platform-specific metadata and independent publishing adapters.
- Platforms: YouTube, Instagram, Facebook, X, TikTok and LinkedIn, subject to each platform's current API access and permissions.
- Daily target: one video, but quality/policy failure means quarantine rather than forced publication.
- Research provenance, factual verification, asset licensing, duplicate protection, retries and audit records are mandatory.
- Shadow-mode commissioning precedes autonomous publishing.

## 7. Engineering constraints

- Windows, Python 3.12
- Prefer free/open-source and low-cost providers
- Modular monolith before microservices
- SQLite initially
- FFmpeg, Pillow/OpenCV, pytest
- Provider and platform adapters must be replaceable
- Persistent jobs, retries, audit trail, backups and recovery
- No automatic task registration until a real worker and recovery path exist

## 8. Development order

1. Inspect existing Phase 1 starter repository and acceptance criteria.
2. Agent foundation: config, logging, database, task state machine, CLI.
3. Tool contracts, permissions, audit and recovery.
4. WealthCodeX research and script skill.
5. Presenter, voice, assets, render and quality gates.
6. Platform adapters one at a time.
7. Dashboard, analytics, backup and remote interface.
8. Shadow-mode validation, then carefully enabled autonomy.

## 9. Non-goals for the first milestone

- No unrestricted autonomous control of the whole Windows machine.
- No always-on local LLM on the 16 GB integrated-GPU laptop.
- No microservices or expensive cloud stack prematurely.
- No pretending all six social platforms are immediately publishable.
