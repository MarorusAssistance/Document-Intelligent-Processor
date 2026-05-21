# infra/CLAUDE.md

Infra-specific rules. See repo root `CLAUDE.md` first.

## Stack

Bicep modular · Azure CLI · OIDC federated credentials from GitHub Actions.

## Layout

```
infra/
├── main.bicep              targetScope=subscription, creates RG inline.
├── parameters/dev.bicepparam
├── modules/                naming, monitoring, storage, cosmos, service-bus,
│                           document-intelligence, key-vault, container-registry,
│                           container-apps-env, container-app-api, identity.
└── scripts/                bootstrap.sh, deploy.sh
```

Resource details in `../docs/milestones/M0-spec.md` §6.

## Hard rules

- **No connection strings** for Azure resources. Managed identity + RBAC.
- Role assignments centralized in `modules/identity.bicep` as a declarative table. Never scatter them across modules.
- Naming convention from `modules/naming.bicep`. Never hardcode resource names.
- Region: `westeurope` (`weu`). All resources colocated.
- M0: only `dev` environment. `prod` parameters file lives in M6.
- Cosmos: free tier preferred, fallback to serverless via param.
- Service Bus: Basic tier in dev.
- Document Intelligence: F0 (free).
- Container Apps: `minReplicas: 0` (scale to zero).

## Workflow

1. Edit module.
2. `make infra-whatif` to preview.
3. Review diff in detail before applying.
4. `make infra-deploy` only after reviewing what-if.

## Forbidden

- Hardcoding subscription IDs, tenant IDs, or principal IDs in modules. Use params.
- `enableRbacAuthorization: false` on Key Vault. RBAC mode only.
- Public access on Key Vault without IP allowlist (dev: allow Azure services + your IP).
- Creating role assignments outside `identity.bicep`.
- Deploying directly from a developer machine to anything other than `dev`. CD pipeline owns the deploy.
