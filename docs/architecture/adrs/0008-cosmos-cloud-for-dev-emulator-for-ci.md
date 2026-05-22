# ADR-0008 — Cosmos DB Cloud for Local Dev; Emulator for CI Integration Tests

**Status:** Accepted
**Date:** 2026-05-20

## Context

The backend integration tests hit Cosmos DB. Two environments need a Cosmos DB instance:

1. **Local developer machine:** run integration tests during development.
2. **GitHub Actions CI:** run integration tests on every PR.

Options for each environment:

- **Cloud Cosmos DB (dev account):** always available, no setup, real behavior, zero cost at free tier.
- **Cosmos DB Emulator vNext (Docker):** runs locally or as a CI service container, no Azure account needed, but the `vnext-preview` image is in preview status with some features listed as no-ops.

## Decision

- **Local dev:** connect directly to the cloud Cosmos DB account (`cosno-docproc-dev-weu`) via `DefaultAzureCredential` (resolved from `az login`). No emulator in the local dev workflow.
- **CI integration tests:** run the `mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator:vnext-preview` image as a GitHub Actions service container. The emulator starts with `--protocol http` (no TLS) for simplicity.

The Cosmos endpoint for CI is set via environment variable: `COSMOS_ENDPOINT=http://localhost:8081`.

## Consequences

**Better:**
- Local dev always uses real Cosmos behavior — no emulator drift (missing features, different error codes, no-op operations that silently succeed).
- CI uses the emulator, which is free to run, requires no Azure credentials, and does not consume free-tier RUs or risk polluting the shared dev database.
- The free-tier dev Cosmos DB costs €0 at idle, making the cloud-for-local-dev decision cost-neutral.
- Developers can use the Azure Portal to inspect data during debugging — not possible with the emulator.

**Worse:**
- Local dev requires `az login` and network access to Azure — no air-gapped development.
- The emulator vNext is in preview; some features may behave differently from production. Any discrepancy found in CI tests must be validated against real Cosmos.
- The Cosmos emulator is listed as Risk R2 in the M0 risk register: "may have features as no-ops that pass silently." The smoke tests (`test_cosmos_smoke.py`) specifically validate create, read, and delete operations to catch this.

Risk mitigated by: keeping CI integration tests focused on operations that are smoke-tested against the real Cosmos when running locally, and by running the emulator only for the subset of integration tests that target persistence. Any test that requires real Cosmos semantics (e.g., full-text search, serverless billing behavior) is not run in CI.

## Alternatives considered

**Emulator for both local and CI:** rejected. The vnext-preview emulator has known feature gaps. Developers would debug against emulator behavior that differs from production, leading to bugs that only appear in the real Azure environment.

**Cloud Cosmos DB for both local and CI:** possible in theory (CI could use OIDC to authenticate), but this would require CI to have Azure credentials, consume free-tier RUs, and risk CI polluting the shared dev database. Rejected.

**Mock the repository in integration tests:** rejected. Mocking the Cosmos repository in integration tests removes confidence that the actual Cosmos queries, indexing, and partition key behavior work correctly. The M0 risk register explicitly notes the lesson learned from mock-only integration testing.
