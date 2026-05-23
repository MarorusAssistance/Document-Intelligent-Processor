# ADR-0002 — Hexagonal Architecture over Traditional Layered Architecture

**Status:** Accepted
**Date:** 2026-05-20

## Context

The backend needs an architecture pattern from day one. The project roadmap spans 6 milestones and introduces significant complexity over time:

- **M1:** Azure Document Intelligence integration.
- **M3:** Odoo ERP adapter.
- **M4:** delivery note document type.
- **M5:** Business Central ERP adapter (second ERP, replacing or alongside Odoo).
- **M6:** hardening, prod environment.

The `Document` entity has a non-trivial state machine and business rules that must remain correct regardless of which storage backend, queue system, or ERP is in use. Traditional layered architecture (controllers → services → repositories) tends to bleed infrastructure concerns into service logic over time, making it hard to swap out adapters (e.g., Odoo → Business Central) or test business logic in isolation.

## Decision

Use **hexagonal architecture** (ports and adapters) with four explicit layers:

- `domain/` — pure Python, zero infrastructure imports. Owns entities, value objects, state machine, field schemas.
- `application/` — use cases that depend exclusively on `Protocol` interfaces defined in `application/ports/`. No Azure SDK imports.
- `infrastructure/` — concrete adapters implementing the ports (Cosmos DB, Blob Storage, Service Bus, Document Intelligence, Entra External ID, Odoo, Business Central).
- `api/` — HTTP layer only. FastAPI routers, DTOs, middleware. Calls use cases; never touches domain directly.

Ports (`Protocol` classes) are the only coupling point between `application/` and `infrastructure/`. Tests inject fakes that implement the same protocols.

## Consequences

**Better:**
- ERP adapters (Odoo M3, Business Central M5) can be added or swapped without touching business logic.
- Domain and use case tests run without Azure credentials, Docker, or network — fast and reliable.
- The state machine and correction audit logic are protected from infrastructure churn.
- `mypy --strict` enforces the port interfaces at compile time, catching mismatches before runtime.

**Worse:**
- ~15–20% more boilerplate than flat layered architecture at M0 (more files, more explicit wiring).
- `application/ports/` requires maintaining Protocol definitions in sync with adapter implementations.
- Steeper learning curve for contributors unfamiliar with hexagonal/clean architecture.

The extra boilerplate is front-loaded cost that pays off starting at M3 (first ERP adapter). By M5 (second ERP adapter), the architecture has clearly amortized its setup cost.

## Alternatives considered

**Traditional layered (controllers → services → repositories):** simpler at M0, but services quickly accumulate Azure SDK imports and become hard to test. Swapping the ERP adapter at M5 would require touching service classes that also handle document state transitions. Rejected.

**Clean architecture with use case classes (explicit input/output ports):** more rigorous than the chosen approach but adds significant ceremony (request/response objects for every use case). Given the team size and pace, the Python `Protocol`-based approach achieves the same isolation with less overhead. Considered but not chosen.
