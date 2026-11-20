# Architecture decisions

## ADR-001: Aarohi is the product; WealthCodeX is a skill

Aarohi owns the agent runtime, tools, permissions, memory and audit trail. WealthCodeX content production is a specialised skill and must not define the whole product.

## ADR-002: Modular monolith first

Keep modules separated inside one Python application. Avoid distributed services until measured needs justify them.

## ADR-003: Permission checks outside the model

The model may propose actions; deterministic policy code decides whether they are allowed. Sensitive actions require explicit approval.

## ADR-004: Local-first, replaceable providers

Start on Windows with SQLite and replaceable provider adapters. Do not assume always-on local inference or a paid API.
