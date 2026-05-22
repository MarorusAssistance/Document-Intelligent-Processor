# M0 — Cimientos · Tareas

**Milestone:** M0 — Cimientos
**Spec:** [M0-spec.md](M0-spec.md)
**Estado:** En progreso

---

## Progreso general

| Área | Tareas | Completadas |
|---|---|---|
| 1. Root / Repo setup | 6 | 6 |
| 2. Backend: Scaffolding | 3 | 3 |
| 3. Backend: Dominio | 7 | 7 |
| 4. Backend: Application layer | 7 | 7 |
| 5. Backend: Infrastructure adapters | 10 | 0 |
| 6. Backend: API layer | 19 | 0 |
| 7. Backend: Tests | 6 | 0 |
| 8. Frontend: Scaffolding | 9 | 0 |
| 9. Infraestructura Bicep | 15 | 0 |
| 10. Scripts raíz | 2 | 0 |
| 11. GitHub Actions CI/CD | 6 | 0 |
| 12. ADRs | 9 | 0 |
| **Total** | **99** | **23** |

---

## Orden de implementación

```
Bloque A — Base (sin dependencias externas)
  Área 1 → Área 2 → Área 3

Bloque B — Backend core (depende de A)
  Área 4 → Área 5 → Área 6

Bloque C — Validación (depende de B)
  Área 7

Bloque D — Paralelo a B y C
  Área 8 (Frontend)
  Área 9 → Área 10 → Área 11 (Infra + Scripts + CI/CD)

Bloque E — Al final
  Área 12 (ADRs)
```

---

## ÁREA 1 — Root / Repo setup

- [x] **1.1** Crear `.gitignore` (Python, Node, Bicep, .env, __pycache__, .venv, node_modules)
- [x] **1.2** Crear `.editorconfig`
- [x] **1.3** Actualizar `README.md` con instrucciones de bootstrap funcionales (pre-requisitos, `./scripts/bootstrap-local.sh`, `make dev`, endpoints)
- [x] **1.4** Crear `Makefile` con targets: `bootstrap`, `dev`, `test`, `lint`, `typecheck`, `openapi-export`, `infra-whatif`, `infra-deploy`, `clean`
- [x] **1.5** Crear `docker-compose.yml` — servicios: `azurite`, `odoo`, `odoo-db`, `cosmos-emulator` (profile `offline`)
- [x] **1.6** Crear `.pre-commit-config.yaml` — hooks: trailing-whitespace, end-of-file-fixer, check-yaml, check-toml, check-added-large-files, check-merge-conflict, detect-private-key, ruff, ruff-format, mypy, prettier, markdownlint, bicep format

---

## ÁREA 2 — Backend: Scaffolding

- [x] **2.1** Crear `backend/pyproject.toml` (uv, Python 3.12; deps: fastapi, pydantic-settings, structlog, azure-cosmos, azure-storage-blob, azure-servicebus, azure-keyvault-secrets, azure-ai-documentintelligence, azure-identity, opentelemetry-sdk, python-ulid; dev: ruff, mypy, pytest, pytest-cov, httpx)
- [x] **2.2** Crear `backend/Dockerfile` (multi-stage, uv, src/ layout, usuario no-root)
- [x] **2.3** Crear `backend/.env.example` con todas las vars del spec

---

## ÁREA 3 — Backend: Dominio (`domain/`)

- [x] **3.1** `domain/documents/value_objects.py` — `Money`, `BoundingBox`, `FieldKey`
- [x] **3.2** `domain/documents/models.py` — `Document`, `ExtractedField`, `Correction`, `PushAttempt` (ULIDs con prefijo, timestamps UTC, enums snake_case, Money como objeto)
- [x] **3.3** `domain/documents/state_machine.py` — transiciones válidas (`uploaded→processing→extracted→pending_review→approved→pushing→pushed`, `pending_review↔rejected`, `*→failed`); levanta `InvalidTransition` en transición inválida
- [x] **3.4** `domain/documents/field_schemas/invoice.py` — enum cerrado de fieldKeys canónicos (invoice_number, vendor_name, vendor_tax_id, invoice_date, due_date, total_amount, tax_amount, line_description, line_quantity, line_unit_price, line_amount, etc.)
- [x] **3.5** `domain/documents/field_schemas/delivery_note.py` — placeholder con TODO (M4)
- [x] **3.6** `domain/jobs/models.py` — `Job` con jobKind enum, status, payload/result tipados con discriminated union, retry fields
- [x] **3.7** `domain/jobs/retry_policy.py` — backoff exponencial (30s, 2m, 8m, 32m, 2h → dead_letter)

---

## ÁREA 4 — Backend: Application layer

- [x] **4.1** `application/ports/documents_repository.py` — `Protocol` (get, list, save, delete)
- [x] **4.2** `application/ports/jobs_repository.py` — `Protocol`
- [x] **4.3** `application/ports/blob_storage.py` — `Protocol` (upload, download, delete, get_url)
- [x] **4.4** `application/ports/queue_publisher.py` — `Protocol` (publish)
- [x] **4.5** `application/ports/ocr_provider.py` — `Protocol` placeholder (M1)
- [x] **4.6** `application/ports/erp_adapter.py` — `Protocol` placeholder (M3)
- [x] **4.7** Use cases stub: `upload_document.py`, `apply_correction.py`, `approve_document.py`, `list_documents.py`, `get_document.py`, `enqueue_extraction.py`, `process_extraction_job.py`

---

## ÁREA 5 — Backend: Infrastructure adapters

- [ ] **5.1** `infrastructure/persistence/cosmos_client.py` — `DefaultAzureCredential`, config desde Settings
- [ ] **5.2** `infrastructure/persistence/cosmos_documents_repository.py` — implementa `DocumentsRepository` Protocol, maneja `_etag` para concurrencia optimista, expone `ConcurrencyError`
- [ ] **5.3** `infrastructure/persistence/cosmos_jobs_repository.py` — implementa `JobsRepository` Protocol
- [ ] **5.4** `infrastructure/blob/azure_blob_storage.py` — implementa `BlobStorage` Protocol; rama Azurite si `STORAGE_USE_AZURITE=true`
- [ ] **5.5** `infrastructure/queue/service_bus_publisher.py` — implementa `QueuePublisher` Protocol
- [ ] **5.6** `infrastructure/ocr/azure_document_intelligence.py` — stub que implementa `OCRProvider` (M1 lo completa)
- [ ] **5.7** `infrastructure/erp/odoo/` — carpeta vacía con `TODO.md` (M3)
- [ ] **5.8** `infrastructure/erp/business_central/` — carpeta vacía con `TODO.md` (M5)
- [ ] **5.9** `infrastructure/auth/entra_external_id.py` — valida Bearer JWT, extrae `clientId` del claim
- [ ] **5.10** `infrastructure/observability/app_insights.py` — OpenTelemetry exporter a App Insights; logs como `customDimensions`

---

## ÁREA 6 — Backend: API layer

- [ ] **6.1** `api/v1/dto/_base.py` — `CamelCaseModel` con `alias_generator=to_camel`
- [ ] **6.2** `api/v1/dto/errors.py` — `ProblemDetails` RFC 7807 (type, title, status, detail, instance, traceId, code, errors[])
- [ ] **6.3** `api/v1/dto/pagination.py` — `PaginatedResponse[T]` (items, pagination: limit, nextCursor, hasMore)
- [ ] **6.4** `api/v1/dto/documents.py` — `DocumentResponse`, `DocumentListItem`, `CreateDocumentRequest`, `PatchDocumentStatusRequest`
- [ ] **6.5** `api/v1/dto/corrections.py` — `CorrectionResponse`, `CreateCorrectionRequest`, `ExtractedFieldResponse`
- [ ] **6.6** `api/v1/dto/jobs.py` — `JobResponse`, `JobListItem`
- [ ] **6.7** `api/v1/dto/mappers.py` — `document_to_response()`, `field_to_response()`, `correction_to_response()`, `job_to_response()`
- [ ] **6.8** `api/v1/routers/health.py` — `GET /health` (200), `GET /health/ready` (200), `GET /api/v1/version`
- [ ] **6.9** `api/v1/routers/documents.py` — todos los endpoints de documents con mock data tipado: `POST /documents`, `GET /documents`, `GET /documents/{id}`, `PATCH /documents/{id}/status`, `DELETE /documents/{id}`
- [ ] **6.10** `api/v1/routers/corrections.py` — `GET /documents/{id}/fields`, `GET /documents/{id}/fields/{fid}`, `POST /documents/{id}/fields/{fid}/corrections`, `GET /documents/{id}/fields/{fid}/corrections`
- [ ] **6.11** `api/v1/routers/jobs.py` — `GET /jobs`, `GET /jobs/{id}`, `POST /jobs/{id}/retry`; placeholder `POST /documents/{id}/push-attempts`, `GET /documents/{id}/push-attempts`; placeholder `POST /webhooks/erp/{targetErp}`
- [ ] **6.12** `api/v1/dependencies.py` — `get_current_client_id()`, inyección de repos y adapters
- [ ] **6.13** `api/v1/exception_handlers.py` — handler global → ProblemDetails con traceId (W3C traceparent)
- [ ] **6.14** `api/middleware/auth.py` — Bearer JWT; dev bypass solo si `AUTH_DEV_BYPASS=true` AND `ENVIRONMENT=development`
- [ ] **6.15** `api/middleware/request_id.py` — genera/propaga `requestId` + `traceId` en contextvars
- [ ] **6.16** `api/middleware/access_log.py` — log estructurado por request (method, path, status, latency_ms)
- [ ] **6.17** `main.py` — FastAPI app con lifespan, registra routers, middlewares y exception handlers
- [ ] **6.18** `config.py` — `Settings` (Pydantic BaseSettings) con todas las env vars
- [ ] **6.19** `logging_config.py` — structlog JSON (prod) + ConsoleRenderer con colores (dev); contextvars: traceId, requestId, clientId, userId, documentId, jobId

---

## ÁREA 7 — Backend: Tests (mínimo 5)

- [ ] **7.1** `tests/conftest.py` — fixtures: test client, fake repos, fake blob storage
- [ ] **7.2** `tests/integration/api/test_health.py` — `GET /health` → 200
- [ ] **7.3** `tests/integration/persistence/test_cosmos_smoke.py` — contra emulator: crear container, insertar, leer, borrar
- [ ] **7.4** `tests/unit/domain/test_state_machine.py` — transiciones válidas e inválidas
- [ ] **7.5** `tests/unit/domain/test_field_schemas.py` — carga schema canónico invoice sin errores
- [ ] **7.6** `tests/unit/api/test_dto_mapping.py` — `Document → DocumentResponse`

---

## ÁREA 8 — Frontend: Scaffolding

- [ ] **8.1** Inicializar Next.js 15 con App Router, TypeScript strict, Tailwind (`npx create-next-app`)
- [ ] **8.2** Inicializar shadcn/ui (`npx shadcn@latest init`)
- [ ] **8.3** Instalar y configurar MSAL (`@azure/msal-browser`, `@azure/msal-react`) en `lib/auth.ts`
- [ ] **8.4** Crear `lib/env.ts` — validación de env vars con zod en boot
- [ ] **8.5** Crear `lib/api-client.ts` — cliente HTTP tipado apuntando al backend
- [ ] **8.6** Crear route group `(auth)/` con layout protegido vacío
- [ ] **8.7** Configurar `npm run generate-types` — `openapi-typescript` desde `docs/api/openapi.json` → `types/api.generated.ts` (gitignored)
- [ ] **8.8** Crear `frontend/Dockerfile` (multi-stage, Node 24 LTS)
- [ ] **8.9** Crear `frontend/.env.example` (NEXT_PUBLIC_API_URL, Azure Entra config)

---

## ÁREA 9 — Infraestructura Bicep

- [ ] **9.1** `infra/main.bicep` — targetScope=subscription, crea RG inline, orquesta módulos
- [ ] **9.2** `infra/parameters/dev.bicepparam` — valores dev (westeurope, enableFreeTier=true, básico para que `prod.bicepparam` solo cambie valores)
- [ ] **9.3** `infra/modules/naming.bicep` — outputs de todos los nombres según convención CAF (`{abbr}-{baseName}-{env}-{region}`)
- [ ] **9.4** `infra/modules/monitoring.bicep` — Log Analytics workspace + Application Insights workspace-based (desplegar primero)
- [ ] **9.5** `infra/modules/storage.bicep` — Storage Account Standard LRS + blob containers `originals` y `dlq`
- [ ] **9.6** `infra/modules/cosmos.bicep` — Account (free tier / fallback serverless) + DB `docproc` + containers `documents` + `jobs` (PK `/clientId`)
- [ ] **9.7** `infra/modules/service-bus.bicep` — Namespace Basic + queue `ocr-extraction-jobs`
- [ ] **9.8** `infra/modules/document-intelligence.bicep` — FormRecognizer F0
- [ ] **9.9** `infra/modules/key-vault.bicep` — Standard, RBAC mode; secreto dummy `test-secret`
- [ ] **9.10** `infra/modules/container-registry.bicep` — ACR Basic
- [ ] **9.11** `infra/modules/container-apps-env.bicep` — CAE Consumption conectado a Log Analytics
- [ ] **9.12** `infra/modules/container-app-api.bicep` — min=0, max=3, imagen `mcr.microsoft.com/azuredocs/containerapps-helloworld:latest`, UAMI asignada, secretRef a KV
- [ ] **9.13** `infra/modules/identity.bicep` — 2 UAMIs (api, worker) + tabla declarativa con los 11 role assignments del spec
- [ ] **9.14** `infra/scripts/bootstrap.sh` — setup one-time federated credential OIDC (App Registration ↔ GitHub)
- [ ] **9.15** `infra/scripts/deploy.sh` — `az deployment sub create` para env dev

---

## ÁREA 10 — Scripts raíz

- [ ] **10.1** `scripts/bootstrap-local.sh` — checks (az, docker, uv), `az login`, `docker compose up -d azurite odoo odoo-db`, `uv sync`, `npm install`, `cp -n .env.example .env`
- [ ] **10.2** `scripts/export_openapi.py` — arranca FastAPI app, exporta OpenAPI a `docs/api/openapi.json`

---

## ÁREA 11 — GitHub Actions CI/CD

- [ ] **11.1** `.github/workflows/ci-backend.yml` — trigger: PR + push main (paths: `backend/**`); pasos: checkout, uv (con cache), uv sync, ruff check, ruff format --check, mypy --strict, pytest unit, pytest integration (services: Azurite + Cosmos emulator vNext), export OpenAPI, upload artifact
- [ ] **11.2** `.github/workflows/ci-frontend.yml` — trigger: PR + push main (paths: `frontend/**`); pasos: npm ci, typecheck, build
- [ ] **11.3** `.github/workflows/ci-infra.yml` — trigger: PR (paths: `infra/**`); pasos: bicep lint, az deployment sub what-if
- [ ] **11.4** `.github/workflows/cd-backend.yml` — trigger: push main; pasos: OIDC login, acr login, docker build + push ACR (tag sha + latest), az containerapp update; single-revision mode
- [ ] **11.5** `.github/workflows/cd-infra.yml` — trigger: workflow_dispatch; az deployment sub create dev
- [ ] **11.6** `.github/workflows/pr-checks.yml` — commitlint (Conventional Commits + scopes cerrados), openapi diff, branch naming (`feat/M{n}-*`)

---

## ÁREA 12 — ADRs

Los 9 ADRs obligatorios en `docs/architecture/adrs/`. Plantilla: Contexto / Decisión / Consecuencias / Alternativas consideradas.

- [ ] **12.1** `0001-cosmos-db-over-table-storage.md`
- [ ] **12.2** `0002-hexagonal-architecture-over-layered.md`
- [ ] **12.3** `0003-entity-per-cell-for-line-items.md`
- [ ] **12.4** `0004-value-mutable-with-ocr-original-snapshot.md`
- [ ] **12.5** `0005-managed-identity-no-connection-strings.md`
- [ ] **12.6** `0006-cursor-pagination-with-cosmos-continuation-token.md`
- [ ] **12.7** `0007-idempotency-key-defined-impl-deferred.md`
- [ ] **12.8** `0008-cosmos-cloud-for-dev-emulator-for-ci.md`
- [ ] **12.9** `0009-rfc-7807-problem-json-errors.md`

---

## Criterios de aceptación

| # | Criterio | Estado |
|---|---|---|
| AC-1 | Repo con estructura completa; `README.md` con instrucciones funcionales | ☐ |
| AC-2 | `./scripts/bootstrap-local.sh` corre limpio en Mac/Linux sin errores | ☐ |
| AC-3 | `make dev` → `GET http://localhost:8000/health` → 200 | ☐ |
| AC-4 | `docker compose up -d` → Azurite + Odoo → `http://localhost:8069` accesible | ☐ |
| AC-5 | Bicep `dev` desplegado en Azure: todos los recursos `Succeeded`, RBAC correcto | ☐ |
| AC-6 | Container App API responde 200 a `/health` desde URL pública (imagen hello-world) | ☐ |
| AC-7 | Push a `main` → `cd-backend.yml` verde → ACR con imagen → CA actualizado | ☐ |
| AC-8 | OpenAPI exportado: todos los endpoints M0-M3 con DTOs y stubs mock | ☐ |
| AC-9 | `npm run generate-types` genera `api.generated.ts` y frontend compila sin errores | ☐ |
| AC-10 | 5 tests mínimos pasando en `ci-backend.yml` | ☐ |
| AC-11 | Pre-commit hooks instalados y ejecutándose en cada commit local | ☐ |
| AC-12 | Conventional Commits validados por commitlint en PR | ☐ |
| AC-13 | 9 ADRs escritos en `docs/architecture/adrs/` | ☐ |
| AC-14 | KV con secreto `test-secret` leíble desde CA vía managed identity | ☐ |
| AC-15 | Logs JSON → App Insights; query Kusto `traces \| where customDimensions.event_name == "app_started"` devuelve resultados | ☐ |
