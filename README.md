# Agent Aarohi

Aarohi is a modular, local-first personal AI agent. WealthCodeX is its first specialist skill, not the entire product.

## Runtime
- Windows; Python 3.12 target
- Modular monolith with SQLite persistence
- CLI-first; explicitly registered tools
- Deterministic permission policy outside any language model
- No unrestricted shell tool, automatic publishing or unattended scheduling

## Setup
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m aarohi init-db
python -m aarohi about
python -m pytest
```

Set AAROHI_HOME to choose the directory containing the storage folder. By default, the current working directory is used.

## Current capability
Aarohi can accept a goal, persist it as a planned task, list and inspect task records, and enforce a small deterministic risk policy. It does not yet autonomously reason, call an LLM, execute tools or complete submitted tasks.

## Next
Implement planner/executor contracts, tool invocation with policy enforcement, recovery, and the WealthCodeX skill. External publishing remains disabled until its quality and policy gates pass.
