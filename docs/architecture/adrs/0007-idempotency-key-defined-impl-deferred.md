# ADR-0007 — `Idempotency-Key` Header: Defined in M0, Implemented in M6

**Status:** Accepted
**Date:** 2026-05-20

## Context

Mutating POST endpoints (document upload, correction submission, ERP push) are at risk of duplicate execution if the client retries a request after a network timeout. Without idempotency support, a second identical POST could create a duplicate document, apply a correction twice, or trigger a double push to the ERP.

The `Idempotency-Key` pattern (RFC draft, used by Stripe, Adyen, etc.) solves this: the client generates a unique key per logical operation; the server stores the response keyed by that value and returns the cached response on retry.

Implementing idempotency correctly requires:
- A durable store for responses keyed by `(clientId, idempotency_key)` with TTL.
- Concurrent request handling (locking while the first request processes).
- Appropriate TTL strategy.

## Decision

**Define the `Idempotency-Key` request header in the OpenAPI contract in M0 but do not enforce or implement it until M6.**

- The header appears in the OpenAPI spec for all mutating POSTs with a description: `"RESERVED. Not yet enforced. Implementation planned for M6."`.
- The middleware accepts but ignores the header in M0–M5.
- The format is defined: arbitrary string, max 128 characters, client-generated UUID recommended.
- Implementation in M6 will use Cosmos DB (same free tier account) to store response snapshots with a 24-hour TTL.

## Consequences

**Better:**
- Clients can start sending `Idempotency-Key` from day one without breaking changes.
- The API contract is stable across all milestones — no header added mid-flight.
- Frontend and integration partners can implement retry logic correctly from M1 onwards, even though the server does not deduplicate yet.
- Defers significant implementation complexity (locking, TTL, response serialization) to M6 when the rest of the system is stable.

**Worse:**
- Between M1 and M5, duplicate POSTs from retrying clients can cause duplicate documents or corrections. This risk is accepted for the dev/beta phase.
- The OpenAPI description must clearly document that the header is not yet enforced — failure to document this risks clients assuming deduplication guarantees that do not exist.
- Clients that implement retry logic and rely on the header before M6 will be surprised by duplicates. Explicit documentation and change log entries are required.

Risk classification: **R5** in the M0 risk register — medium probability, medium impact, mitigated by explicit OpenAPI documentation of the limitation.

## Alternatives considered

**Implement idempotency in M0:** rejected. The complexity is disproportionate to M0 scope (which has no real business logic yet). The extra infrastructure (Cosmos response store, locking) adds risk to the foundational milestone with no user-visible benefit.

**Never implement idempotency; rely on client-side deduplication:** rejected. ERP push duplicates (M3+) can create real financial errors. The feature must exist before production.

**Implement at M3 (first ERP push):** considered. ERP push is the highest-risk mutation. However, defining the header API in M0 and implementing consistently in M6 is cleaner than a partial rollout.
