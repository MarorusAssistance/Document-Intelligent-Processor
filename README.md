# Document Intelligent Processor

IDP (Intelligent Document Processing) para supply chain. Ingesta facturas y albaranes escaneados, extrae datos con Azure Document Intelligence, permite revisión humana (HITL) y empuja a ERP (Odoo / Business Central).

## Stack

Python 3.12 · uv · FastAPI · Pydantic v2 · structlog · Cosmos DB · Next.js 15 · Tailwind 4 + shadcn/ui · Bicep · Azure Container Apps

## Pre-requisitos

| Herramienta | Versión mínima | Notas |
|---|---|---|
| [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli) | ≥ 2.60 | `az --version` |
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) | ≥ 25 | con Docker Compose v2 |
| [uv](https://docs.astral.sh/uv/getting-started/installation/) | ≥ 0.4 | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| [Node.js](https://nodejs.org/) | 24 LTS | `node --version` |
| [pre-commit](https://pre-commit.com/#install) | ≥ 3.7 | `pip install pre-commit` |

## Bootstrap local (primera vez)

```bash
./scripts/bootstrap-local.sh
```

El script:
1. Comprueba pre-requisitos (`az`, `docker`, `uv`, `node`)
2. Hace `az login` si no hay sesión activa
3. Levanta Azurite + Odoo + odoo-db con `docker compose up -d`
4. Instala dependencias Python (`uv sync`)
5. Instala dependencias Node (`npm install` en `frontend/`)
6. Copia `.env.example → .env` (sin sobrescribir si ya existe)
7. Instala hooks de pre-commit

## Desarrollo día a día

```bash
make dev          # levanta backend (localhost:8000) + frontend (localhost:3000)
make test         # tests unitarios + integración
make lint         # ruff + mypy + prettier
make typecheck    # mypy --strict sobre el backend
```

## Endpoints principales

| Entorno | URL |
|---|---|
| Backend API | http://localhost:8000 |
| Health check | http://localhost:8000/health |
| OpenAPI docs | http://localhost:8000/docs |
| Frontend | http://localhost:3000 |
| Azurite (blob) | http://localhost:10000 |
| Odoo | http://localhost:8069 |

## Servicios docker-compose

```bash
docker compose up -d                    # Azurite + Odoo + odoo-db
docker compose --profile offline up -d  # + Cosmos emulator (CI / sin cuenta Azure)
docker compose down
```

## Comandos de infra

```bash
make infra-whatif   # preview cambios Bicep en Azure (dev)
make infra-deploy   # despliega entorno dev en Azure
```

## OpenAPI

```bash
make openapi-export  # exporta docs/api/openapi.json
```

El frontend regenera tipos TypeScript automáticamente durante el build:

```bash
cd frontend && npm run generate-types
```

## Estructura del repo

```
├── backend/        FastAPI + arquitectura hexagonal (uv)
├── frontend/       Next.js 15 + shadcn/ui
├── infra/          Bicep modular (Azure)
├── docs/           Specs de milestones, ADRs, runbooks
├── scripts/        Bootstrap y helpers
└── .github/        Workflows CI/CD
```

Spec del milestone activo: [M0-spec.md](M0-spec.md)
Reglas operativas para Claude Code: [CLAUDE.md](CLAUDE.md)
