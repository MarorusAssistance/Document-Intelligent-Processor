# backend/CLAUDE.md

Backend-specific rules. See repo root `CLAUDE.md` first.

## Layout

```
src/document_processor/
├── domain/          PURE. Zero infra imports. Domain models, state machine, value objects.
├── application/     Use cases + Protocols in application/ports/.
├── infrastructure/  Adapters implementing the Protocols. Knows about Azure SDKs.
└── api/             FastAPI routers, DTOs, middleware. v1/ subdir.
```

Detailed structure in `../docs/milestones/M0-spec.md` §3.

## Hard rules

- `domain/` imports nothing from `azure.*`, `fastapi`, `httpx`. Must be runnable in isolation.
- Use cases depend on `Protocol` from `application/ports/`, never on concrete adapters.
- DTOs in `api/v1/dto/` are distinct from domain models. Map via `api/v1/dto/mappers.py` (pure functions).
- `async def` everywhere. Cosmos client is `azure.cosmos.aio.CosmosClient`. Sync client is forbidden.
- JSON ↔ Python field naming via `alias_generator=to_camel`. JSON is camelCase, Python is snake_case.
- IDs are ULIDs with type prefix (`doc_`, `field_`, `correction_`, `push_`, `job_`, `client_`).
- Timestamps ISO 8601 UTC, field name ends in `At`.
- Money as `{ amount: string, currency: ISO_4217 }`. Amount is **string** in JSON to preserve Decimal precision. Never float.

## Forbidden

- `print()` for diagnostics — use `structlog`.
- `import logging` — use `structlog`.
- f-string log messages — use `log.info("event_name", key=value, ...)`.
- Mutating `ExtractedField.ocrOriginal` — permanent snapshot.
- Changing `ExtractedField.value` without a `Correction` entity in the same transactional batch.
- `clientId` from path, body, or header — comes from JWT claim only.
- Mocking SDKs in unit tests — use fakes that implement Protocols.

## Testing

- Unit tests: `tests/unit/` — no Azure SDK, no network. Fakes via Protocols.
- Integration: `tests/integration/` — against Azurite + Cosmos emulator vNext.
- `pytest-asyncio` for async tests.

## Config

Pydantic `BaseSettings` in `config.py`. Reads from env vars. Secrets resolved at startup from Key Vault via `DefaultAzureCredential`.
