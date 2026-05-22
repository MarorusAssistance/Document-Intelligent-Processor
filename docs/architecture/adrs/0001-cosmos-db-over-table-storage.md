# ADR-0001 — Cosmos DB NoSQL over Azure Table Storage

**Status:** Accepted
**Date:** 2026-05-20

## Context

The project needs a metadata store for `Document`, `ExtractedField`, `Correction`, `PushAttempt`, and `Job` entities. Two Azure-native options were evaluated: Azure Table Storage (cheapest serverless key-value store) and Cosmos DB NoSQL API.

Requirements driving the decision:

- **M2 HITL UI:** the review interface needs to filter documents by `status`, `documentKind`, `assignedTo`, and `createdAfter` simultaneously and display paginated results.
- **M3+ ERP push:** queries across multiple fields to find pending pushes, correlate jobs with documents.
- **Transactional batch:** applying a correction must atomically update `ExtractedField.value` and create a `Correction` record — a hard requirement for audit integrity.
- **Cost at idle:** the project runs on a dev Azure account where cost sensitivity is high.

## Decision

Use **Cosmos DB NoSQL API** with the free tier (1 account per subscription, 1000 RU/s shared across containers). If the free tier is already consumed in the subscription, fall back to serverless billing (pay-per-request, ~$0.25/million RUs).

## Consequences

**Better:**
- Multi-field filtering works natively via SQL queries over indexed properties.
- Transactional batch operations are supported within a partition key — critical for the HITL correction flow.
- Continuation token pagination maps directly to the cursor-based API contract.
- Cosmos DB free tier has zero idle cost; serverless fallback costs cents/month at low traffic.
- `_etag`-based optimistic concurrency is built-in, exposable as `ConcurrencyError` to the application layer without extra infrastructure.

**Worse:**
- More configuration than Table Storage (containers, indexing policy, partition key design).
- Only one free-tier account per subscription — must handle the fallback to serverless via a Bicep parameter.
- Cosmos SDK (async) adds a dependency; Table Storage SDK would be lighter.

## Alternatives considered

**Azure Table Storage:** rejected because it has no support for multi-field server-side filtering (all filtering is done client-side), no join-like queries, and no transactional batch across different entity types. This would make the M2 HITL UI unworkable without a full table scan on every page load, and the correction atomic operation would require application-level two-phase commit. The minor cost saving (a few cents/month) does not justify this technical debt.

**Azure SQL / PostgreSQL Flexible Server:** overkill for the data model and volume (hundreds to low-thousands of documents/month). Adds a persistent compute cost even at minimum tier. Rejected in favor of a serverless NoSQL solution.
