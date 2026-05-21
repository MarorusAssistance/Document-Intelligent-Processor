# CLAUDE.md

Operational rules for this repo. Read in full before any task.

**Project:** Document Processor — IDP (Intelligent Document Processing) for supply chain. Ingests scanned invoices/delivery notes, extracts data via Azure Document Intelligence, allows human review (HITL), pushes to ERP (Odoo / Business Central).

**Source of truth:** `docs/milestones/M{n}-spec.md`. This file is rules, not architecture.
**Current milestone:** see latest spec in `docs/milestones/`. Don't skip ahead milestones.

## Stack (pinned)

Python 3.12 · uv · FastAPI · Pydantic v2 · structlog · `azure-cosmos.aio` (async only) · Node 24 LTS · Next.js 15 · Tailwind 4 + shadcn/ui · Bicep · Azure CLI.

## Out-of-scope — never propose

Conversational assistant · RAG · custom ML training · forecasting · infrastructure-level multi-tenancy · billing · analytical dashboards.

## Core rules

- **Stop and ask** when the spec is silent, ambiguous, or when a task implies functionality from a later milestone.
- **Hexagonal layout is law.** `domain/` has zero infra imports. `application/` depends on `Protocol` in `application/ports/`. `infrastructure/` implements them. `api/` is HTTP only. Details in `backend/CLAUDE.md`.
- **English** everywhere: code, commits, branches, comments, docstrings.
- **Conventional Commits** with the scope list in M0-spec.md §9. Pre-commit hooks enforce.
- **PRs always**, even solo. Squash merge.
- **ADR for any non-obvious decision** in `docs/architecture/adrs/` (template in `docs/architecture/adrs/README.md`). Numbering monotonic.
- **No new dependency** without: (a) proving it's strictly necessary, (b) confirming it fits existing ADRs, (c) updating or creating the relevant ADR. Pin versions.
- **Managed identity only** for Azure resources. No connection strings for Azure services in this repo.
- **No PII in logs.** No full filenames, no extracted document content, no emails.
- **`mypy --strict`** is enforced — type everything.

## When this file disagrees with a milestone spec

The milestone spec wins. Open a PR to fix this file.

## Subdirectory rules

- `backend/CLAUDE.md` — Python, FastAPI, hexagonal, async, testing
- `frontend/CLAUDE.md` — Next.js, types, MSAL
- `infra/CLAUDE.md` — Bicep, naming, RBAC

## Commands

```bash
make dev              # backend + frontend
make test             # unit + integration
make lint             # ruff + mypy + prettier
make openapi-export   # regenerate docs/api/openapi.json
make infra-whatif     # preview infra changes
make infra-deploy     # deploy dev (after whatif review)
```
