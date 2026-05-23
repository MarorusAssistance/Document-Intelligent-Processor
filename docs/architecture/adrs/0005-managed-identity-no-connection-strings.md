# ADR-0005 — Managed Identity Only; No Connection Strings for Azure Resources

**Status:** Accepted
**Date:** 2026-05-20

## Context

The backend needs to authenticate to multiple Azure services: Cosmos DB, Blob Storage, Service Bus, Document Intelligence, and Key Vault. Two authentication models are possible:

1. **Connection strings / access keys:** include the secret in environment variables or Key Vault. The application uses the key to authenticate. Simple to set up, but the secret must be rotated, stored securely, and protected against leakage.
2. **Managed identity (passwordless):** the Azure-hosted workload (Container App) is assigned a User-Assigned Managed Identity (UAMI). Azure issues short-lived tokens automatically. No secret to store or rotate.

## Decision

Use **managed identity exclusively** for all Azure resource authentication. Concretely:

- All backend code uses `DefaultAzureCredential()` from `azure-identity`. This resolves to the UAMI in Azure and to the developer's `az login` credentials locally.
- Role assignments are centralized in `infra/modules/identity.bicep` as a declarative table — never scattered across individual resource modules.
- No connection strings for Cosmos DB, Storage, Service Bus, Document Intelligence, or Key Vault appear anywhere in the codebase or CI/CD.
- Key Vault stores only third-party secrets (Odoo API key, Entra External ID client secret). It is not used to store Azure resource credentials.
- Cosmos DB has `disableLocalAuth: true`; Storage, Service Bus, and Document Intelligence likewise disable key-based auth where supported.

## Consequences

**Better:**
- Zero secret rotation burden for Azure resources. No connection string in `.env`, CI variables, or Key Vault for first-party Azure services.
- Eliminates a class of security incidents: a leaked connection string in a log or env var cannot compromise Azure resources.
- RBAC assignments are auditable and declarative (Bicep). The identity module lists exactly what each managed identity can do.
- `DefaultAzureCredential` works transparently in both local dev (via `az login`) and Azure (via UAMI), with no code change.
- Azure Defender / security posture improvements: managed identity authentication appears in audit logs with principal identity, not just a shared key.

**Worse:**
- Requires `az login` on developer machines — one extra setup step compared to copying a connection string.
- The Cosmos DB data-plane RBAC uses a different assignment resource (`sqlRoleAssignments`) from standard Azure RBAC, which is less familiar and requires Bicep-level knowledge.
- Integration tests in CI that target the real Azure environment need OIDC federated credentials set up — a one-time setup step per repository.
- Azurite (local blob emulator) does not support managed identity; a special branch for `STORAGE_USE_AZURITE=true` uses the well-known Azurite connection string only in development.

## Alternatives considered

**Connection strings in Key Vault:** would keep connection strings out of code and CI, but they still need to be rotated and are transmitted at runtime. Adds an extra hop (KV read) on startup. Rejected in favor of passwordless.

**Service Principal with client secret:** similar to managed identity but requires creating and rotating a client secret. More setup with no benefit over UAMI when running on Azure. Rejected.

**Mix: managed identity for most, connection string for Cosmos (common pattern):** Cosmos DB managed identity requires SQL RBAC which is slightly more complex than key-based auth. Rejected — the complexity is worth the consistency of a fully passwordless setup.
