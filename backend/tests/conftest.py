from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from document_processor.config import Settings
from document_processor.domain.documents.models import Document
from document_processor.domain.jobs.models import Job

# ── In-memory fakes ───────────────────────────────────────────────────────────


class FakeDocumentsRepository:
    def __init__(self) -> None:
        self._store: dict[str, Document] = {}

    async def get(self, client_id: str, document_id: str) -> Document | None:
        doc = self._store.get(document_id)
        if doc is None or doc.client_id != client_id:
            return None
        return doc

    async def list(
        self,
        client_id: str,
        limit: int = 20,
        cursor: str | None = None,
    ) -> tuple[list[Document], str | None]:
        items = [d for d in self._store.values() if d.client_id == client_id]
        return items[:limit], None

    async def save(self, document: Document) -> None:
        self._store[document.id] = document

    async def delete(self, client_id: str, document_id: str) -> None:
        self._store.pop(document_id, None)


class FakeJobsRepository:
    def __init__(self) -> None:
        self._store: dict[str, Job] = {}

    async def get(self, client_id: str, job_id: str) -> Job | None:
        job = self._store.get(job_id)
        if job is None or job.client_id != client_id:
            return None
        return job

    async def list(
        self,
        client_id: str,
        limit: int = 20,
        cursor: str | None = None,
    ) -> tuple[list[Job], str | None]:
        items = [j for j in self._store.values() if j.client_id == client_id]
        return items[:limit], None

    async def save(self, job: Job) -> None:
        self._store[job.id] = job


class FakeBlobStorage:
    def __init__(self) -> None:
        self._blobs: dict[str, bytes] = {}

    async def upload(self, container: str, blob_name: str, data: bytes, content_type: str) -> str:
        key = f"{container}/{blob_name}"
        self._blobs[key] = data
        return f"https://fake-storage/{key}"

    async def download(self, container: str, blob_name: str) -> bytes:
        return self._blobs.get(f"{container}/{blob_name}", b"")

    async def delete(self, container: str, blob_name: str) -> None:
        self._blobs.pop(f"{container}/{blob_name}", None)

    async def get_url(self, container: str, blob_name: str, expiry_seconds: int = 3600) -> str:
        return f"https://fake-storage/{container}/{blob_name}?sas=fake"

    async def aclose(self) -> None:
        pass


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def fake_documents_repo() -> FakeDocumentsRepository:
    return FakeDocumentsRepository()


@pytest.fixture
def fake_jobs_repo() -> FakeJobsRepository:
    return FakeJobsRepository()


@pytest.fixture
def fake_blob_storage() -> FakeBlobStorage:
    return FakeBlobStorage()


@pytest.fixture
def dev_settings() -> Settings:
    return Settings(
        environment="development",
        auth_dev_bypass=True,
        auth_dev_client_id="client_test",
        cosmos_endpoint="https://localhost:8081",
        storage_account_url="http://127.0.0.1:10000/devstoreaccount1",
    )


@pytest.fixture
async def test_client(
    fake_documents_repo: FakeDocumentsRepository,
    fake_jobs_repo: FakeJobsRepository,
    fake_blob_storage: FakeBlobStorage,
    dev_settings: Settings,
) -> AsyncIterator[AsyncClient]:
    from collections.abc import AsyncIterator as _AI
    from contextlib import asynccontextmanager

    from fastapi import FastAPI
    from fastapi.exceptions import HTTPException, RequestValidationError

    from document_processor.api.middleware.access_log import AccessLogMiddleware
    from document_processor.api.middleware.auth import AuthMiddleware
    from document_processor.api.middleware.request_id import RequestIdMiddleware
    from document_processor.api.v1.exception_handlers import (
        http_exception_handler,
        request_validation_handler,
        unhandled_exception_handler,
    )
    from document_processor.api.v1.routers import corrections, documents, health, jobs
    from document_processor.logging_config import configure_logging

    configure_logging(log_level="WARNING", json_logs=False)

    @asynccontextmanager
    async def _null_lifespan(app: FastAPI) -> _AI[None]:
        yield

    app = FastAPI(lifespan=_null_lifespan)
    app.state.settings = dev_settings
    app.state.documents_repo = fake_documents_repo
    app.state.jobs_repo = fake_jobs_repo
    app.state.blob_storage = fake_blob_storage

    app.add_middleware(AccessLogMiddleware)
    app.add_middleware(AuthMiddleware)
    app.add_middleware(RequestIdMiddleware)
    app.add_exception_handler(HTTPException, http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, request_validation_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_exception_handler)
    app.include_router(health.router)
    app.include_router(documents.router)
    app.include_router(corrections.router)
    app.include_router(jobs.router)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


# ── Domain helpers ────────────────────────────────────────────────────────────


def make_document(**overrides: Any) -> Document:  # noqa: ANN401
    now = datetime.now(UTC)
    from document_processor.domain.documents.models import (
        DocumentKind,
        DocumentSource,
    )

    defaults: dict[str, Any] = {
        "client_id": "client_test",
        "document_kind": DocumentKind.invoice,
        "source": DocumentSource(
            blob_url="https://fake/blob.pdf",
            filename="invoice.pdf",
            mime_type="application/pdf",
            size_bytes=1024,
            sha256="abc123",
            uploaded_at=now,
            uploaded_by="client_test",
        ),
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(overrides)
    return Document(**defaults)
