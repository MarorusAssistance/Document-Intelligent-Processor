# M0 — Cimientos · Spec definitiva

**Proyecto:** Document Processor (IDP para supply chain)
**Milestone:** M0 — Cimientos
**Estado:** Closed — listo para implementación
**Última actualización:** 2026-05-20

---

## TL;DR — Decisiones clave

**Storage de metadatos:** Cosmos DB NoSQL API (free tier preferente, fallback a serverless). Se descarta Azure Table Storage por su pobre soporte a queries multi-campo, sin joins, y por hacer inmanejable la UI HITL de M2. El coste idle real es 0€ en free tier o céntimos en serverless, frente a los céntimos de Table Storage — la diferencia no justifica el dolor técnico.

**Arquitectura backend:** Hexagonal pragmática con cuatro capas (`domain`, `application`, `infrastructure`, `api`) sobre FastAPI + uv. El roadmap exige dos ERPs (Odoo M3, Business Central M5) y aislar la máquina de estados de Document — hex amortiza su sobrecoste (~15-20% más boilerplate) ya en M3.

**Modelo de datos:** 5 entidades en 2 containers. Container `documents` (PK `/clientId`) agrupa `Document`, `ExtractedField`, `Correction` y `PushAttempt` para habilitar transactional batch en HITL. Container `jobs` separado por patrón de acceso distinto. Entity-per-cell para líneas de factura desde M0 (no array-inline) — decisión que evita refactor en M3 y M4. `value` mutable + snapshot inmutable `ocrOriginal` para audit/retraining.

**API contract:** REST `/api/v1/...` (path versioning), errores RFC 7807 con `traceId`, paginación por cursor (continuation token de Cosmos), `Idempotency-Key` definida en M0 pero implementada en M6. Multi-tenancy por claim del JWT (Entra External ID), nunca en URL. DTOs separados del dominio, camelCase en JSON con `alias_generator`.

**Infra:** Bicep modular en West Europe, todo managed identity con tabla declarativa de role assignments — cero connection strings de recursos Azure. Service Bus Basic para dev. Container Apps con scale-to-zero, M0 ya despliega imagen hello-world para validar CI/CD end-to-end. Solo entorno `dev` en M0.

**Dev local:** docker-compose con Azurite (Storage) y Odoo Community. Cosmos cloud directo en dev local, emulator vNext solo en CI integration tests. Auth dev bypass gated por `ENVIRONMENT=development`.

**CI/CD:** GitHub Actions OIDC con federated credentials, trunk-based + Conventional Commits, ADRs por decisión no-obvia, mypy `--strict` desde día 1, structlog con JSON.

---

## 1. Objetivos

M0 no entrega funcionalidad de negocio. Entrega los cimientos sobre los que se construirán M1-M6.

Objetivos verificables:

1. Repositorio listo: estructura, configuración, tooling y CI/CD pasando en verde.
2. Infraestructura `dev` aprovisionada en Azure mediante Bicep, sin intervención manual.
3. Container App API desplegada con imagen placeholder, alcanzable y respondiendo `/health` 200.
4. Contrato OpenAPI completo (todos los endpoints M0-M3 definidos con DTOs, sin implementación de negocio).
5. Modelo de datos diseñado y documentado, con migraciones idempotentes para containers Cosmos.
6. Entorno de dev local funcional con un solo comando.
7. Gestión de secretos centralizada en Key Vault, accesible localmente vía `az login`.
8. Conjunto mínimo de tests (5) corriendo en CI.
9. ADRs escritos para todas las decisiones técnicas no-obvias listadas en este documento.

---

## 2. Scope

### In scope

- Monorepo: `/backend`, `/frontend`, `/infra`, `/docs`, `/scripts`, `/.github`.
- Backend FastAPI con arquitectura hexagonal: domain + application + infrastructure + api.
- Frontend Next.js scaffolding con shadcn/ui inicializado, sin features.
- Infraestructura Azure en Bicep modular: RG, Storage, Cosmos, Service Bus, Document Intelligence, Container Apps Environment, Container Apps (API), ACR, Key Vault, Log Analytics, App Insights, Managed Identities + role assignments.
- Modelo de datos: 5 entidades (`Document`, `ExtractedField`, `Correction`, `PushAttempt`, `Job`) implementadas como Pydantic models.
- Contrato OpenAPI completo con stubs que devuelven datos mock.
- `docker-compose.yml` con Azurite + Odoo + (perfil `offline`) Cosmos emulator.
- Key Vault para secretos reales (Odoo, Entra client secret). `.env.example` con resto de configuración.
- Pipelines CI/CD: `ci-backend`, `ci-frontend`, `ci-infra`, `cd-backend`, `cd-infra`, `pr-checks`.
- Convenciones: branches, commits (Conventional + commitlint), pre-commit hooks, naming, logging estructurado.
- ADRs (≥5).

### Out of scope (M0)

- Lógica de negocio: extracción real, mapeo a ERP, validaciones de dominio.
- Endpoints implementados (devuelven mock).
- Frontend funcional.
- Infraestructura `prod` (solo `dev`).
- Tests E2E.
- Hardening: WAF, private endpoints, custom domain, TLS cert.
- Observabilidad avanzada: dashboards, alertas, SLO/SLI.
- Backup strategy explícita (Cosmos free tier hace backup automático).

### Out of scope permanente del proyecto

Asistente conversacional, RAG, ML custom, modelos de forecasting, multitenancy con isolation a nivel infra (queda en nivel app), billing, dashboards analíticos.

---

## 3. Arquitectura general

### Vista de alto nivel

```
                    ┌─────────────────────────┐
                    │  Entra External ID      │
                    │  (OAuth/OIDC)           │
                    └────────────┬────────────┘
                                 │ JWT
                                 ▼
┌──────────────┐         ┌──────────────────┐
│  Next.js     │ ──────► │  FastAPI API     │ ──► Cosmos DB (documents, jobs)
│  Frontend    │  REST   │  (Container App) │ ──► Blob Storage (originals)
└──────────────┘         │                  │ ──► Service Bus (ocr-jobs queue)
                         │                  │ ──► Key Vault (secrets)
                         └────────┬─────────┘
                                  │ enqueue
                                  ▼
                         ┌──────────────────┐
                         │  Worker          │       M1+
                         │  (Container App) │ ──► Document Intelligence
                         └──────────────────┘ ──► Odoo / BC adapters (M3+)
```

M0 solo despliega API (con imagen hello-world). Worker se añade en M1.

### Estructura del monorepo

```
document-processor/
├── backend/                    # FastAPI + uv
├── frontend/                   # Next.js 15 + shadcn/ui
├── infra/                      # Bicep modular
├── docs/                       # Specs, ADRs, runbooks
├── scripts/                    # Bootstrap, seeds, helpers
├── .github/workflows/          # CI/CD
├── docker-compose.yml          # Dev local (Azurite + Odoo)
├── Makefile                    # Comandos día-a-día
├── .editorconfig
├── .pre-commit-config.yaml
├── .gitignore
├── README.md
├── CLAUDE.md                   # Contexto para Claude Code
└── LICENSE
```

Sin tooling de monorepo (no Turborepo, Nx, ni workspaces). Para 1 paquete Python + 1 app JS, la sobrecarga no compensa. El contrato entre backend y frontend es OpenAPI; frontend genera tipos TS con `openapi-typescript` durante el build. Cero `shared/`.

### Backend — Arquitectura hexagonal pragmática

```
backend/
├── pyproject.toml
├── uv.lock
├── Dockerfile
├── src/
│   └── document_processor/
│       ├── main.py                       # FastAPI app, lifespan
│       ├── config.py                     # Pydantic Settings
│       ├── logging_config.py             # structlog setup
│       │
│       ├── domain/                       # PURO. Sin Azure, sin FastAPI.
│       │   ├── documents/
│       │   │   ├── models.py             # Document, ExtractedField, Correction, PushAttempt
│       │   │   ├── state_machine.py
│       │   │   ├── value_objects.py      # Money, BoundingBox, FieldKey
│       │   │   └── field_schemas/
│       │   │       ├── invoice.py        # Schema canónico M1
│       │   │       └── delivery_note.py  # Placeholder M4
│       │   └── jobs/
│       │       ├── models.py
│       │       └── retry_policy.py
│       │
│       ├── application/                  # Use cases + ports
│       │   ├── documents/
│       │   │   ├── upload_document.py
│       │   │   ├── apply_correction.py
│       │   │   ├── approve_document.py
│       │   │   ├── list_documents.py
│       │   │   └── get_document.py
│       │   ├── jobs/
│       │   │   ├── enqueue_extraction.py
│       │   │   └── process_extraction_job.py
│       │   └── ports/                    # Protocols
│       │       ├── documents_repository.py
│       │       ├── jobs_repository.py
│       │       ├── blob_storage.py
│       │       ├── queue_publisher.py
│       │       ├── ocr_provider.py
│       │       └── erp_adapter.py
│       │
│       ├── infrastructure/               # Adapters. Conocen Azure.
│       │   ├── persistence/
│       │   │   ├── cosmos_client.py
│       │   │   ├── cosmos_documents_repository.py
│       │   │   └── cosmos_jobs_repository.py
│       │   ├── blob/
│       │   │   └── azure_blob_storage.py
│       │   ├── queue/
│       │   │   └── service_bus_publisher.py
│       │   ├── ocr/
│       │   │   └── azure_document_intelligence.py
│       │   ├── erp/
│       │   │   ├── odoo/                 # M3
│       │   │   └── business_central/     # M5 — carpeta vacía con TODO.md
│       │   ├── auth/
│       │   │   └── entra_external_id.py
│       │   └── observability/
│       │       └── app_insights.py
│       │
│       └── api/
│           ├── v1/
│           │   ├── routers/
│           │   │   ├── documents.py
│           │   │   ├── corrections.py
│           │   │   ├── jobs.py
│           │   │   └── health.py
│           │   ├── dto/
│           │   │   ├── _base.py          # CamelCaseModel
│           │   │   ├── documents.py
│           │   │   ├── corrections.py
│           │   │   ├── jobs.py
│           │   │   ├── errors.py         # ProblemDetails RFC 7807
│           │   │   ├── pagination.py
│           │   │   └── mappers.py
│           │   ├── dependencies.py
│           │   └── exception_handlers.py
│           └── middleware/
│               ├── auth.py
│               ├── request_id.py
│               └── access_log.py
│
└── tests/
    ├── unit/
    ├── integration/
    └── conftest.py
```

Convenciones:

- **`src/` layout** estándar moderno de Python packaging (evita imports accidentales).
- **DTO ≠ Domain models**. Domain es la verdad interna; DTOs son el contrato HTTP. Duplicación deliberada para versionado.
- **`application/ports/`** contiene `Protocol` de Python. Use cases dependen de Protocols; tests inyectan fakes.
- **`infrastructure/erp/business_central/`** existe vacío desde M0 con `TODO.md` — marca dónde va a vivir el segundo adapter.
- **uv** como package manager.

### Frontend

```
frontend/
├── package.json
├── tsconfig.json
├── next.config.mjs
├── tailwind.config.ts
├── components.json                       # shadcn config
├── Dockerfile
├── src/
│   ├── app/                              # Next.js App Router
│   │   ├── (auth)/                       # Route group con layout protegido
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   └── globals.css
│   ├── components/
│   │   ├── ui/                           # shadcn primitives
│   │   └── features/
│   ├── lib/
│   │   ├── api-client.ts                 # Cliente HTTP tipado
│   │   ├── auth.ts                       # MSAL para Entra External ID
│   │   ├── env.ts                        # Validación env con zod
│   │   └── utils.ts
│   ├── types/
│   │   └── api.generated.ts              # Generado desde OpenAPI (gitignored)
│   └── hooks/
└── public/
```

- App Router (no Pages Router).
- Tipos API regenerados en `npm run build` desde OpenAPI export.
- Sin BFF inicial; calls directos al FastAPI.
- `env.ts` valida env vars con zod en boot.

---

## 4. Modelo de datos

### Containers

```
Cosmos DB account: cosno-docproc-dev-weu
Database: docproc

documents (PK: /clientId)
├── Document
├── ExtractedField
├── Correction
└── PushAttempt

jobs (PK: /clientId)
└── Job
```

Dos containers, cinco tipos de entidad. Discriminator `type` distingue dentro del container. En free tier Cosmos los containers comparten 1000 RU/s — más que suficiente.

### `Document`

```json
{
  "id": "doc_01HQXR4V9NM3KQYPB8TXY7WJ2A",
  "type": "Document",
  "clientId": "client_acme",
  "documentKind": "invoice",
  "status": "pending_review",
  "statusHistory": [
    { "from": null, "to": "uploaded", "at": "2026-05-19T10:30:00Z", "by": "user_juan@acme.com", "reason": null },
    { "from": "uploaded", "to": "processing", "at": "2026-05-19T10:30:05Z", "by": "system", "reason": null },
    { "from": "processing", "to": "extracted", "at": "2026-05-19T10:30:18Z", "by": "system", "reason": null },
    { "from": "extracted", "to": "pending_review", "at": "2026-05-19T10:30:18Z", "by": "system", "reason": null }
  ],
  "archivedAt": null,
  "source": {
    "blobUrl": "https://stdocprocdevweu001.blob.core.windows.net/originals/client_acme/doc_01HQ....pdf",
    "filename": "factura-2026-001234.pdf",
    "mimeType": "application/pdf",
    "sizeBytes": 245678,
    "pageCount": 2,
    "sha256": "ab12cd34...",
    "uploadedAt": "2026-05-19T10:30:00Z",
    "uploadedBy": "user_juan@acme.com"
  },
  "extraction": {
    "provider": "azure_document_intelligence",
    "modelId": "prebuilt-invoice",
    "modelVersion": "2024-11-30",
    "startedAt": "2026-05-19T10:30:05Z",
    "completedAt": "2026-05-19T10:30:18Z",
    "overallConfidence": 0.94,
    "jobId": "job_01HQXR5..."
  },
  "review": {
    "assignedTo": null,
    "reviewedBy": null,
    "reviewedAt": null,
    "correctionCount": 0
  },
  "push": {
    "targetErp": null,
    "lastAttemptId": null,
    "successfulAttemptId": null,
    "externalRef": null,
    "pushedAt": null
  },
  "createdAt": "2026-05-19T10:30:00Z",
  "updatedAt": "2026-05-19T10:30:18Z"
}
```

**Máquina de estados:**

```
uploaded → processing → extracted → pending_review ─┬─► approved → pushing → pushed
                                                    └─► rejected (terminal, reversible)
                     └─► failed (terminal, recoverable con retry)
```

Transición `rejected → pending_review` permitida. `assignedTo` definido pero no expuesto en API en M0. `archivedAt` es ortogonal al status (soft delete sin cambiar máquina).

### `ExtractedField`

```json
{
  "id": "field_01HQXR5K2P...",
  "type": "ExtractedField",
  "clientId": "client_acme",
  "documentId": "doc_01HQXR4V9NM3KQYPB8TXY7WJ2A",

  "fieldKey": "invoice_number",
  "fieldLabel": "Invoice Number",
  "fieldGroup": "header",
  "lineItemIndex": null,

  "value": "F-2026/001235",
  "dataType": "string",

  "ocrOriginal": {
    "raw": "F-2026/001234",
    "normalized": "F-2026/001234",
    "confidence": 0.96
  },

  "location": {
    "pageNumber": 1,
    "boundingBox": { "x": 0.45, "y": 0.12, "w": 0.20, "h": 0.03 }
  },

  "isCorrected": true,
  "correctionCount": 1,
  "lastCorrectionAt": "2026-05-19T10:45:22Z",
  "lastCorrectedBy": "user_juan@acme.com",

  "createdAt": "2026-05-19T10:30:18Z",
  "updatedAt": "2026-05-19T10:45:22Z"
}
```

**Reglas:**

- `value` es mutable y siempre refleja el estado vigente. `ocrOriginal` es snapshot único e inmutable del OCR — nunca se toca.
- `dataType`: `"string" | "number" | "date" | "money"`. Money es objeto `{ amount: "1234.56", currency: "EUR" }` con `amount` como string para preservar Decimal precision; date es ISO 8601 string.
- `fieldGroup`: `"header" | "line_item" | "footer"`. Cuando `fieldGroup="line_item"`, `lineItemIndex` es int ≥ 0; en otro caso `null`.
- **Entity-per-cell** desde M0: cada celda de línea de factura es un `ExtractedField` propio con su `lineItemIndex` y `fieldKey` (`line_description`, `line_quantity`, `line_unit_price`, `line_amount`, etc.). Sin arrays anidados.
- `fieldKey` viene de un schema interno canónico (enum cerrado en `domain/documents/field_schemas/invoice.py`). Doc Intelligence devuelve `InvoiceId`, `VendorName`, etc. — un mapper traduce a las claves canónicas.

### `Correction`

```json
{
  "id": "correction_01HQXR8M...",
  "type": "Correction",
  "clientId": "client_acme",
  "documentId": "doc_01HQXR4V9NM3KQYPB8TXY7WJ2A",
  "fieldId": "field_01HQXR5K2P...",

  "previousValue": "F-2026/001234",
  "newValue": "F-2026/001235",
  "reason": null,

  "correctedBy": "user_juan@acme.com",
  "correctedAt": "2026-05-19T10:45:22Z"
}
```

- Append-only. Múltiples correcciones del mismo campo = múltiples entidades.
- Aplicar corrección = transactional batch (mismo `clientId` partition): crear `Correction` + actualizar `ExtractedField.value` y contadores en una sola operación atómica.
- `correctedBy` siempre del token JWT, nunca del request body.
- `reason` opcional, nullable.

### `PushAttempt`

```json
{
  "id": "push_01HQXR9...",
  "type": "PushAttempt",
  "clientId": "client_acme",
  "documentId": "doc_01HQ...",
  "jobId": "job_01HQ...",

  "targetErp": "odoo",
  "targetEndpoint": "POST /api/v1/account.move",
  "idempotencyKey": "client_acme:doc_01HQ:attempt_3",

  "attemptNumber": 3,
  "status": "failed",

  "request": {
    "bodyPreview": "...",
    "bodySizeBytes": 4521,
    "sanitizedHeaders": { "content-type": "application/json" }
  },
  "response": {
    "statusCode": 500,
    "bodyPreview": "...",
    "bodySizeBytes": 312,
    "latencyMs": 1432
  },

  "errorCategory": "transient",
  "errorMessage": "Connection timeout after 30s",

  "externalRef": null,

  "startedAt": "...",
  "completedAt": "..."
}
```

- `errorCategory`: `"transient" | "permanent" | "auth" | "validation" | "not_found" | "rate_limited"`. Solo `transient` y `rate_limited` reintentan.
- `bodyPreview` truncado a 2KB. Body completo no se persiste (M6 podría enviar a blob).
- `sanitizedHeaders` excluye auth tokens y cookies.
- `idempotencyKey` formato `{clientId}:{documentId}:attempt_{n}`.

### `Job`

```json
{
  "id": "job_01HQXR5...",
  "type": "Job",
  "clientId": "client_acme",
  "documentId": "doc_01HQ...",

  "jobKind": "ocr_extract",
  "status": "running",

  "payload": {
    "modelId": "prebuilt-invoice",
    "modelVersion": "2024-11-30",
    "blobUrl": "https://..."
  },
  "result": null,

  "attemptNumber": 1,
  "maxAttempts": 5,
  "nextRetryAt": null,

  "lastError": null,

  "createdAt": "...",
  "startedAt": "...",
  "completedAt": null,
  "durationMs": null
}
```

- `jobKind`: `"ocr_extract" | "push_to_erp" | "classify_document"`.
- `payload` y `result` son `dict` libres en Cosmos; en código tipados con discriminated union (Pydantic).
- Source of truth de "qué worker está procesando" = Service Bus message lock. Cosmos solo guarda estado.
- Backoff exponencial default: 30s, 2m, 8m, 32m, 2h. Después → status `dead_letter`.

### Convenciones transversales del modelo

- **IDs:** ULIDs con prefijo de tipo (`doc_`, `field_`, `correction_`, `push_`, `job_`, `client_`). Lexicográficamente ordenables por tiempo.
- **Timestamps:** ISO 8601 UTC con sufijo `Z`. Campo siempre termina en `At` (`createdAt`, `pushedAt`).
- **Money:** objeto `{ amount: string, currency: ISO_4217 }`. Amount como string para Decimal precision; nunca float en wire format.
- **Enums:** lowercase snake_case (`"pending_review"`, `"odoo"`, `"transient"`).
- **`updatedAt`** se actualiza en cada write desde repository layer, no desde use case.
- **Optimistic concurrency:** Cosmos `_etag` automático. Repositorios lo manejan transparentemente, exponen `ConcurrencyError` al application layer.

---

## 5. API contract

### Convenciones

- **Versionado:** path (`/api/v1/...`). `v1` cubre M1-M5.
- **Errores:** RFC 7807 `application/problem+json`.
- **Paginación:** cursor opaco (continuation token Cosmos en base64).
- **Auth:** Bearer JWT de Entra External ID. `clientId` siempre del claim, jamás del path/body.
- **Idempotency-Key:** header opcional en POSTs de mutación, definido pero no validado en M0 (impl en M6).
- **Naming:** JSON en camelCase, Python en snake_case (Pydantic `alias_generator=to_camel`).
- **Content-Type por defecto:** `application/json`. Excepción: `POST /documents` acepta `multipart/form-data`.

### Formato de error (RFC 7807)

```json
{
  "type": "https://docs.docproc.example.com/errors/document-not-found",
  "title": "Document not found",
  "status": 404,
  "detail": "Document 'doc_01HQ...' does not exist in client 'client_acme'",
  "instance": "/api/v1/documents/doc_01HQ...",
  "traceId": "00-abc123def456...-01",
  "code": "DOCUMENT_NOT_FOUND",
  "errors": [
    { "field": "documentKind", "code": "INVALID_VALUE", "message": "Must be one of [invoice, delivery_note]" }
  ]
}
```

`code` machine-readable independiente del status HTTP. `traceId` = W3C traceparent, conecta con App Insights.

### Paginación

```http
GET /api/v1/documents?limit=20&cursor=eyJyaWQiOiJhYmMxMjMifQ==
```

```json
{
  "items": [ ... ],
  "pagination": {
    "limit": 20,
    "nextCursor": "eyJyaWQiOiJkZWY0NTYifQ==",
    "hasMore": true
  }
}
```

`limit` default 20, max 100. No se incluye `total` (caro en Cosmos); endpoint `/count` separado si UI lo necesita en M2+.

### Inventario de endpoints (M0-M3)

```
# Health
GET    /health
GET    /health/ready
GET    /api/v1/version

# Documents (M1 partial, M2 full)
POST   /api/v1/documents                                  # multipart upload
GET    /api/v1/documents                                  # list, filters, cursor pagination
GET    /api/v1/documents/{documentId}
PATCH  /api/v1/documents/{documentId}/status              # transition (approve|reject|reset)
DELETE /api/v1/documents/{documentId}                     # soft delete (archivedAt)

# Extracted fields & corrections (M2)
GET    /api/v1/documents/{documentId}/fields
GET    /api/v1/documents/{documentId}/fields/{fieldId}
POST   /api/v1/documents/{documentId}/fields/{fieldId}/corrections
GET    /api/v1/documents/{documentId}/fields/{fieldId}/corrections

# Jobs (M1 partial)
GET    /api/v1/jobs
GET    /api/v1/jobs/{jobId}
POST   /api/v1/jobs/{jobId}/retry

# Push attempts (M3)
GET    /api/v1/documents/{documentId}/push-attempts
POST   /api/v1/documents/{documentId}/push

# Webhooks (M3+, placeholder M0)
POST   /api/v1/webhooks/erp/{targetErp}
```

Filtros estándar en `GET /documents`: `status` (multi-valor), `documentKind`, `createdAfter`, `createdBefore`, `assignedTo`, `q` (búsqueda libre, M2+).

### Approach M0

Code-first. Todos los routers y DTOs definidos con signaturas completas. Handlers devuelven **datos mock tipados** (no `NotImplementedError`) para que el frontend pueda integrar contra él desde el día uno. OpenAPI se exporta en CI a `docs/api/openapi.json`.

### Dev auth bypass

Solo si `ENVIRONMENT=development`:

```http
X-Dev-Bypass-Auth: true
X-Dev-Client-Id: client_local_dev
```

El middleware respeta estos headers únicamente con `AUTH_DEV_BYPASS=true` Y `ENVIRONMENT=development`. En cualquier otro caso se ignoran.

---

## 6. Infraestructura (Bicep)

### Convención de naming

```
{abbreviation}-{baseName}-{env}-{region}-{instance?}
```

Ejemplos:

```
rg-docproc-dev-weu                      Resource Group
stdocprocdevweu001                      Storage Account (sin guiones, max 24)
cosno-docproc-dev-weu                   Cosmos DB
sb-docproc-dev-weu                      Service Bus namespace
cog-docproc-dev-weu                     Document Intelligence
kv-docproc-dev-weu                      Key Vault
cae-docproc-dev-weu                     Container Apps Environment
ca-docproc-api-dev-weu                  Container App API
cr docprocdevweu                        ACR (sin guiones)
appi-docproc-dev-weu                    Application Insights
log-docproc-dev-weu                     Log Analytics
id-docproc-api-dev-weu                  User-Assigned Managed Identity (API)
id-docproc-worker-dev-weu               UAMI Worker (M1+)
```

Abreviaturas siguen Microsoft CAF. Región `weu` = West Europe. `naming.bicep` centraliza outputs.

### Estructura de módulos

```
infra/
├── main.bicep                         # targetScope=subscription, crea RG inline
├── parameters/
│   └── dev.bicepparam
├── modules/
│   ├── naming.bicep                   # outputs nombres
│   ├── monitoring.bicep               # Log Analytics + App Insights (primero)
│   ├── storage.bicep                  # Storage + blob containers
│   ├── cosmos.bicep                   # Account + DB + containers (documents, jobs)
│   ├── service-bus.bicep              # Namespace Basic + queue ocr-extraction-jobs
│   ├── document-intelligence.bicep    # Cognitive Services FormRecognizer F0
│   ├── key-vault.bicep                # RBAC mode
│   ├── container-registry.bicep       # ACR Basic
│   ├── container-apps-env.bicep       # CAE conectado a Log Analytics
│   ├── container-app-api.bicep        # CA con imagen hello-world
│   └── identity.bicep                 # UAMIs + tabla declarativa de role assignments
└── scripts/
    ├── bootstrap.sh
    └── deploy.sh
```

### Recursos M0

| Recurso | Tier | Notas |
|---|---|---|
| Resource Group | — | `rg-docproc-dev-weu` |
| Storage Account | Standard LRS | Containers: `originals`, `dlq` |
| Cosmos DB | Free tier (fallback Serverless) | DB `docproc`, containers `documents` + `jobs`, ambos PK `/clientId` |
| Service Bus | Basic | Queue `ocr-extraction-jobs` |
| Document Intelligence | F0 (free) | 500 págs/mes |
| Key Vault | Standard, RBAC mode | Secretos Odoo + Entra client secret |
| Container Apps Environment | Consumption | Conectado a Log Analytics |
| Container App API | min=0, max=3 | Imagen `mcr.microsoft.com/azuredocs/containerapps-helloworld:latest` |
| ACR | Basic | Imágenes propias M1+ |
| Log Analytics | Pay-as-you-go | Workspace |
| Application Insights | Workspace-based | Conectado a Log Analytics |
| UAMI (api) | — | Roles: ver tabla `identity.bicep` |
| UAMI (worker) | — | Definida en M0, asignada a CA en M1 |

### Identity y RBAC (tabla declarativa en `identity.bicep`)

| Identity | Recurso | Rol |
|---|---|---|
| api | Cosmos DB | Cosmos DB Built-in Data Contributor |
| api | Storage Blob | Storage Blob Data Contributor |
| api | Service Bus | Azure Service Bus Data Sender |
| api | Key Vault | Key Vault Secrets User |
| api | Application Insights | Monitoring Metrics Publisher |
| worker | Cosmos DB | Cosmos DB Built-in Data Contributor |
| worker | Storage Blob | Storage Blob Data Reader |
| worker | Service Bus | Azure Service Bus Data Receiver |
| worker | Document Intelligence | Cognitive Services User |
| worker | Key Vault | Key Vault Secrets User |
| worker | Application Insights | Monitoring Metrics Publisher |

Cero connection strings de recursos Azure. En código: `DefaultAzureCredential()`.

### Qué va a Key Vault, qué no

**Key Vault (secretos reales):**

- `odoo-api-key`
- `entra-external-id-client-secret`
- (M5) `bc-client-secret`

**Env vars (identificadores, no secretos):**

- Todos los `*_ENDPOINT`, `*_URL`, IDs de tenant/subscription/client de Azure
- Nombres de queue, database, containers
- Flags de configuración (`AUTH_DEV_BYPASS`, `LOG_LEVEL`, etc.)

Container App lee de Key Vault con `secretRef` apuntando a `keyVaultUrl` + identity. Cero connection string de KV en código.

### Lo que NO se aprovisiona en M0

- Custom domain + TLS (M6)
- Private endpoints / VNet (M6)
- Diagnostic settings con archive a Storage (M6)
- Backup explícito (Cosmos free tier hace backup continuo cada 4h por defecto)
- Front Door / App Gateway (nunca)
- Multi-region (nunca)
- Worker Container App (M1)
- Entorno `prod` (M0 solo `dev`; `prod` en M6 con hardening)

---

## 7. Dev local

### `docker-compose.yml`

```yaml
services:
  azurite:
    image: mcr.microsoft.com/azure-storage/azurite:latest
    container_name: docproc-azurite
    ports: ["10000:10000", "10001:10001", "10002:10002"]
    volumes: [azurite-data:/data]
    command: "azurite --blobHost 0.0.0.0 --queueHost 0.0.0.0 --tableHost 0.0.0.0 -l /data"

  odoo:
    image: odoo:17
    container_name: docproc-odoo
    depends_on: [odoo-db]
    ports: ["8069:8069"]
    environment: [HOST=odoo-db, USER=odoo, PASSWORD=odoo]
    volumes: [odoo-data:/var/lib/odoo]

  odoo-db:
    image: postgres:16
    container_name: docproc-odoo-db
    environment:
      POSTGRES_USER: odoo
      POSTGRES_PASSWORD: odoo
      POSTGRES_DB: postgres
    volumes: [odoo-db-data:/var/lib/postgresql/data]

  cosmos-emulator:
    image: mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator:vnext-preview
    container_name: docproc-cosmos
    ports: ["8081:8081", "1234:1234"]
    command: ["--protocol", "http"]
    profiles: ["offline"]

volumes:
  azurite-data:
  odoo-data:
  odoo-db-data:
```

- Default `docker compose up` arranca Azurite + Odoo.
- Cosmos emulator detrás de profile `offline`: `docker compose --profile offline up`.
- Odoo arranca desde M0 aunque su uso real sea M3.

### Estrategia de servicios

| Recurso | Dev local |
|---|---|
| Storage Blob | Azurite (docker-compose) |
| Cosmos DB | Cloud directo (free tier dev environment) |
| Service Bus | Cloud directo |
| Document Intelligence | Cloud directo |
| Key Vault | Cloud directo (resuelto vía `az login`) |
| Entra External ID | Cloud directo |
| Odoo | docker-compose |

Cosmos cloud directo en dev porque el coste es 0€ y el emulator vNext es preview con features no-op. Para CI integration tests sí se usa el emulator (service container en GitHub Actions).

### `.env.example`

```bash
ENVIRONMENT=development
LOG_LEVEL=DEBUG

# Azure Cloud dev environment
AZURE_TENANT_ID=
AZURE_SUBSCRIPTION_ID=
COSMOS_ENDPOINT=https://cosno-docproc-dev-weu.documents.azure.com:443/
COSMOS_DATABASE=docproc
SERVICE_BUS_NAMESPACE=sb-docproc-dev-weu.servicebus.windows.net
SERVICE_BUS_QUEUE_OCR=ocr-extraction-jobs
DOC_INTELLIGENCE_ENDPOINT=https://cog-docproc-dev-weu.cognitiveservices.azure.com/
KEY_VAULT_URL=https://kv-docproc-dev-weu.vault.azure.net/
APPLICATION_INSIGHTS_CONNECTION_STRING=

# Storage: Azurite local override
STORAGE_ACCOUNT_URL=http://127.0.0.1:10000/devstoreaccount1
STORAGE_USE_AZURITE=true

# Odoo local
ODOO_URL=http://localhost:8069
ODOO_DB=docproc
ODOO_USERNAME=admin

# Auth bypass dev
AUTH_DEV_BYPASS=true
AUTH_DEV_CLIENT_ID=client_local_dev
```

- `STORAGE_USE_AZURITE=true` activa connection string conocida de Azurite (no soporta managed identity).
- Secretos reales (Odoo API key, Entra secret) leídos en runtime de Key Vault vía `DefaultAzureCredential` con tu `az login`.

### Bootstrap

`scripts/bootstrap-local.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

command -v az >/dev/null || { echo "Install Azure CLI"; exit 1; }
command -v docker >/dev/null || { echo "Install Docker"; exit 1; }
command -v uv >/dev/null || { echo "Install uv"; exit 1; }

az account show >/dev/null 2>&1 || az login

docker compose up -d azurite odoo odoo-db

cd backend && uv sync && cd ..
cd frontend && npm install && cd ..

cp -n .env.example .env || true

echo "Done. Run 'make dev' to start services."
```

`Makefile` en raíz con targets: `bootstrap`, `dev`, `test`, `lint`, `typecheck`, `openapi-export`, `infra-whatif`, `infra-deploy`, `clean`.

---

## 8. CI/CD

### Workflows

```
.github/workflows/
├── ci-backend.yml      # PR + push main, paths: backend/**
├── ci-frontend.yml     # PR + push main, paths: frontend/**
├── ci-infra.yml        # PR, paths: infra/**, bicep lint + what-if
├── cd-backend.yml      # push main, build + push ACR + update CA
├── cd-infra.yml        # workflow_dispatch manual, deploy bicep dev
└── pr-checks.yml       # commitlint, openapi diff, branch naming
```

### Auth Azure desde GitHub Actions

OIDC con federated credentials. Cero secrets de SP en GitHub Variables/Secrets.

Setup one-time: App Registration en Entra ↔ federated credential apuntando a `repo:<usuario>/docproc:environment:dev`. Vars en GH:

```
AZURE_CLIENT_ID
AZURE_TENANT_ID
AZURE_SUBSCRIPTION_ID
```

### `ci-backend.yml` — pasos

1. Checkout
2. Setup uv (con cache)
3. `uv sync --all-extras`
4. `ruff check` + `ruff format --check`
5. `mypy --strict src/`
6. `pytest tests/unit/` con `--cov=src --cov-report=xml`
7. `pytest tests/integration/` con services container: Azurite + Cosmos emulator vNext
8. Export OpenAPI (`python scripts/export_openapi.py`)
9. Upload OpenAPI artifact

Coverage NO se enforce con threshold en M0 (poco código). Threshold (≥70%) se añade en M6.

### `cd-backend.yml` — pasos

1. Checkout
2. `azure/login@v2` con OIDC
3. `az acr login`
4. Build image, tag con `${{ github.sha }}` + `latest`
5. Push a ACR
6. `az containerapp update --image ...`

Single-revision mode. Blue/green a M6.

### Tests mínimos en M0 (5)

| Test | Path | Valida |
|---|---|---|
| `test_health.py` | `tests/integration/api/` | `GET /health` → 200 |
| `test_cosmos_smoke.py` | `tests/integration/persistence/` | Crear container, insertar, leer, borrar contra emulator |
| `test_state_machine.py` | `tests/unit/domain/` | Transiciones válidas/inválidas |
| `test_field_schemas.py` | `tests/unit/domain/` | Carga schema canónico invoice sin errores |
| `test_dto_mapping.py` | `tests/unit/api/` | `Document → DocumentResponse` |

---

## 9. Convenciones

### Branches & commits

Trunk-based light. `main` siempre verde. Feature branches `feat/M{n}-{descripcion}`, vida corta. PRs obligatorios (incluso solo-dev). Squash merge default.

**Conventional Commits enforced** con commitlint en CI.

Tipos: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `perf`, `ci`, `build`.

Scopes cerrados (validados): `documents`, `corrections`, `jobs`, `extraction`, `erp`, `auth`, `cosmos`, `blob`, `service-bus`, `api`, `infra`, `ci`, `deps`, `frontend`, `docs`, `adr`.

Ejemplos:

```
feat(documents): add upload endpoint
fix(cosmos): handle 429 on transactional batch
chore(deps): bump pydantic to 2.9
docs(adr): add ADR 0005 for upload strategy
```

### Pre-commit hooks (`.pre-commit-config.yaml`)

- `trailing-whitespace`, `end-of-file-fixer`, `check-yaml`, `check-toml`
- `check-added-large-files` (max 500KB)
- `check-merge-conflict`, `detect-private-key`
- `ruff` (lint + autofix) + `ruff-format` — solo `backend/`
- `mypy --strict` (local hook, backend/)
- `prettier` — solo `frontend/`
- `markdownlint` — solo `docs/`
- `bicep format`

### Naming

**Python:** snake_case (vars/funcs/módulos), PascalCase (clases), UPPER_SNAKE (constantes). Módulos en plural para agregados (`documents/`). Use cases como verbos (`upload_document.py`). Ports con sufijo (`DocumentsRepository`, `OCRProvider`). Adapters con prefijo de tecnología (`CosmosDocumentsRepository`, `OdooERPAdapter`).

**JSON:** camelCase. Timestamps `*At` ISO 8601 UTC. IDs con prefijo (`doc_`, `field_`, …). Enums lowercase_snake. Money como objeto con amount string.

**TypeScript:** camelCase (vars/funcs), PascalCase (components/types), kebab-case (filenames).

**Bicep:** camelCase. Recursos con nombres descriptivos.

### Logging estructurado

`structlog`. JSON renderer en producción, ConsoleRenderer con colores en dev.

Cada log es un dict, no string formateado:

```python
log.info("document_uploaded", document_id=doc_id, size_bytes=size, mime_type=mime)
```

**Contextvars propagadas en todo request:** `traceId`, `requestId`, `clientId`, `userId`, `documentId` (cuando aplica), `jobId` (workers).

**Event names** en snake_case con verbo en pasado: `document_uploaded`, `correction_applied`, `push_attempted`, `cosmos_query_executed`.

**Niveles:**

- DEBUG: solo dev (request bodies, query plans)
- INFO: eventos de negocio
- WARNING: degradaciones recuperables
- ERROR: fallos con stack

**Sin PII en logs.** No filename completo, no contenido extraído.

**Middleware HTTP** inyecta `requestId` + `traceId` + `clientId` en contextvars al inicio del request. App Insights via OpenTelemetry exporter — logs van como `customDimensions`, queries Kusto triviales por documento.

### ADRs

Obligatorios para decisiones no-obvias. Plantilla: Contexto / Decisión / Consecuencias / Alternativas consideradas. Mínimo a escribir en M0:

```
docs/architecture/adrs/
├── 0001-cosmos-db-over-table-storage.md
├── 0002-hexagonal-architecture-over-layered.md
├── 0003-entity-per-cell-for-line-items.md
├── 0004-value-mutable-with-ocr-original-snapshot.md
├── 0005-managed-identity-no-connection-strings.md
├── 0006-cursor-pagination-with-cosmos-continuation-token.md
├── 0007-idempotency-key-defined-impl-deferred.md
├── 0008-cosmos-cloud-for-dev-emulator-for-ci.md
└── 0009-rfc-7807-problem-json-errors.md
```

---

## 10. Criterios de aceptación

M0 está cerrado cuando se cumplen TODOS:

1. ☐ Repo creado con la estructura del documento, `README.md` con instrucciones de bootstrap funcionales.
2. ☐ `./scripts/bootstrap-local.sh` corre limpio en una máquina nueva (Mac/Linux) y termina sin errores.
3. ☐ `make dev` levanta backend + frontend localmente; `/health` responde 200 desde `http://localhost:8000/health`.
4. ☐ `docker compose up -d` levanta Azurite + Odoo; Odoo UI accesible en `http://localhost:8069`.
5. ☐ Bicep `dev` desplegado en Azure: TODOS los recursos en estado `Succeeded`, RBAC asignado correctamente.
6. ☐ Container App API responde 200 a `/health` desde su URL pública (con imagen hello-world).
7. ☐ Push a `main` ejecuta `cd-backend.yml`, build & push a ACR exitoso, Container App actualizado.
8. ☐ OpenAPI exportado: todos los endpoints M0-M3 definidos con DTOs y stubs mock funcionales.
9. ☐ Frontend genera `types/api.generated.ts` desde el OpenAPI y compila sin errores.
10. ☐ 5 tests mínimos definidos pasando en CI (`ci-backend.yml` verde).
11. ☐ Pre-commit hooks instalados y ejecutándose en cada commit local.
12. ☐ Conventional Commits validados por commitlint en PR.
13. ☐ ADRs (mínimo 9) escritos en `docs/architecture/adrs/`.
14. ☐ Key Vault con al menos un secreto dummy (`test-secret`), leíble desde Container App vía managed identity (test desde shell).
15. ☐ Logging estructurado JSON activo, logs llegan a App Insights, query Kusto `traces | where customDimensions.event_name == "app_started"` devuelve resultados.

---

## 11. Edge cases

### Modelo de datos

- **Sha256 duplicado en upload:** `POST /documents` devuelve `409 Conflict` con body apuntando al `documentId` existente. Cliente decide si reintentar con override (header `X-Override-Duplicate: true` → nuevo Document con su propio ID).
- **Documento con 0 fields extraídos:** válido. Document pasa a `pending_review` con `extraction.overallConfidence = 0`. UI muestra mensaje "no fields detected".
- **Document item > 2MB en Cosmos:** mitigado por entity-per-cell (líneas no van inline). Si pese a todo se acerca, `extraction.warnings: ["item_size_warning"]` se añade y se loguea WARNING.
- **Corrección concurrente al mismo field:** Cosmos `_etag` enforce optimistic concurrency. Segunda corrección recibe 412 PreconditionFailed → API responde 409 con problema RFC 7807 `code: CONCURRENT_MODIFICATION`. UI re-fetcha y reintenta.
- **Transición de status inválida:** state machine en `domain/` levanta `InvalidTransition`. API responde 409 con `code: INVALID_STATUS_TRANSITION` y `errors: [{field: "status", code: "INVALID_TRANSITION", message: "Cannot transition from 'pushed' to 'pending_review'"}]`.

### API

- **Cursor inválido:** 400 `code: INVALID_PAGINATION_CURSOR`. Cliente debe empezar paginación de cero.
- **Limit fuera de rango (1-100):** 400 `code: INVALID_PAGINATION_LIMIT`.
- **Token JWT expirado:** 401 `code: TOKEN_EXPIRED`. Cliente refresca y reintenta.
- **`clientId` del token no autorizado al endpoint:** 403 `code: FORBIDDEN`. Sin detalles.
- **Multipart sin file:** 422 `code: VALIDATION_FAILED` con `errors: [{field: "file", code: "REQUIRED"}]`.
- **MIME no soportado en upload:** 415 `code: UNSUPPORTED_MEDIA_TYPE`. Lista de soportados: `application/pdf`, `image/png`, `image/jpeg`.
- **Tamaño de file > 20MB:** 413 `code: PAYLOAD_TOO_LARGE`.

### Infra & dev local

- **Cosmos free tier no disponible:** Bicep param `enableFreeTier` cae a `false`, deploy a serverless. Coste real <1€/mes.
- **West Europe sin capacidad para Cosmos free tier:** fallback manual a `northeurope`. Documentado en ADR 0001.
- **Azurite no responde:** healthcheck en `make dev` falla con mensaje claro `Azurite not running, run 'docker compose up -d azurite'`.
- **`az login` expirado durante dev local:** error de `DefaultAzureCredential` propagado con mensaje accionable.
- **Service Bus queue no existe:** Bicep la crea; en local no usamos Service Bus emulado, los integration tests usan el emulator vNext.

### CI/CD

- **OIDC federated credential mal configurada:** `azure/login` falla con error claro. Documentado en `infra/README.md` con setup paso a paso.
- **ACR push falla por permisos:** UAMI del GitHub Action necesita `AcrPush` sobre el ACR. Definido en `identity.bicep`.
- **Container App update timeout:** retry manual con `workflow_dispatch`.

---

## 12. Riesgos conocidos y mitigaciones

| # | Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|---|
| R1 | Cosmos free tier consumido en otra cuenta de la suscripción | Media | Bajo | Param Bicep + fallback a serverless. Coste céntimos. |
| R2 | Cosmos emulator vNext (preview) tiene features no-op que pasan silenciosas | Media | Medio | Emulator solo en CI (no en dev). Tests integration smoke validan operaciones críticas. |
| R3 | Document Intelligence F0 (500 págs/mes) se agota en demo en vivo | Baja | Medio | Bicep parametriza tier; upgrade a S0 = 1 línea, sin redeploy de app. |
| R4 | Service Bus Basic no soporta sessions | Baja | Bajo | M3+: si necesitamos ordering por documento, upgrade a Standard (~$10/mes). Probabilidad baja porque jobs son independientes. |
| R5 | `Idempotency-Key` definida pero no implementada → cliente asume garantía que no hay | Media | Medio | Documentar explícitamente en OpenAPI description del header: "RESERVED. Not yet enforced. Plan: M6." |
| R6 | West Europe sin capacidad ocasional para Cosmos free tier | Baja | Bajo | Probar `northeurope` como fallback documentado. |
| R7 | Drift entre OpenAPI exported y types TS generados si CI no corre | Media | Bajo | Job PR `pr-checks.yml` valida que OpenAPI y types están sincronizados. |
| R8 | Solo entorno `dev` en M0 → al llegar M6 (hardening prod), descubrir que Bicep no parametriza correctamente | Media | Medio | Estructurar `dev.bicepparam` desde M0 para que `prod.bicepparam` solo cambie valores (tier, region, scaling). Revisar en M0 si los nombres permiten sustitución directa. |
| R9 | Managed identity para Cosmos data plane requiere role assignment con CLI específico — provisioning timing puede fallar | Media | Bajo | Bicep usa `dependsOn` explícito. Si falla en primer deploy, re-run del workflow lo arregla (role assignment es idempotente). |
| R10 | docker-compose Odoo arranca lento (~2 min primera vez) | Alta | Bajo | Profile separado opcional `--profile erp` si en M0-M2 no se usa. Por defecto sí arranca (decisión: comodidad). |
| R11 | Auth dev bypass se queda activo en deployment cloud por accidente | Baja | Alto | Doble gate: requiere `AUTH_DEV_BYPASS=true` AND `ENVIRONMENT=development`. CI valida que en CD el env var `ENVIRONMENT=production`. |
| R12 | Frontend en M0 es solo scaffolding → al llegar M2 descubrir que falta routing/auth setup | Media | Bajo | Scaffolding M0 incluye MSAL setup, route groups `(auth)`, layout protegido, aunque las páginas estén vacías. |

---

## 13. Apéndice: comandos clave

```bash
# Bootstrap inicial
./scripts/bootstrap-local.sh

# Dev día a día
make dev                          # backend + frontend
make test                         # unit + integration
make lint                         # ruff + mypy + prettier
make openapi-export               # export OpenAPI a docs/api/openapi.json

# Infra
make infra-whatif                 # az deployment sub what-if
make infra-deploy                 # az deployment sub create (solo dev)

# Cosmos data
make cosmos-seed                  # opcional: seed con datos dummy

# Limpieza
make clean                        # baja containers, limpia volúmenes locales
```

---

## 14. Hand-off a M1

M1 entra con:

- Repo y CI/CD en verde
- Infra `dev` corriendo
- Modelo de datos persistible (Cosmos containers creados, repositorios Cosmos implementados con tests integration)
- Contratos API definidos (handlers responden mock; M1 los implementa)
- Worker NO desplegado (M1 lo añade)

M1 implementa: walking skeleton end-to-end del flujo de extracción de invoice. `POST /documents` → Blob → Service Bus → Worker → Document Intelligence → Cosmos → status `pending_review`. Sin UI, sin push a ERP.
