from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

import structlog
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
from document_processor.config import get_settings
from document_processor.logging_config import configure_logging

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(log_level=settings.log_level, json_logs=settings.environment != "development")

    logger.info("startup", environment=settings.environment)

    from document_processor.infrastructure.persistence.cosmos_documents_repository import (
        CosmosDocumentsRepository,
    )
    from document_processor.infrastructure.persistence.cosmos_jobs_repository import (
        CosmosJobsRepository,
    )
    from document_processor.infrastructure.blob.azure_blob_storage import AzureBlobStorage

    from azure.cosmos.aio import CosmosClient
    from azure.identity.aio import DefaultAzureCredential

    credential = DefaultAzureCredential()
    cosmos_client = CosmosClient(url=settings.cosmos_endpoint, credential=credential)
    db = cosmos_client.get_database_client(settings.cosmos_database)

    docs_container = db.get_container_client("documents")
    jobs_container = db.get_container_client("jobs")

    blob_storage = AzureBlobStorage(
        account_url=settings.storage_account_url,
        use_azurite=settings.storage_use_azurite,
    )

    app.state.settings = settings
    app.state.documents_repo = CosmosDocumentsRepository(docs_container)
    app.state.jobs_repo = CosmosJobsRepository(jobs_container)
    app.state.blob_storage = blob_storage

    if settings.application_insights_connection_string:
        from document_processor.infrastructure.observability.app_insights import (
            configure_telemetry,
        )

        configure_telemetry(settings.application_insights_connection_string)

    yield

    logger.info("shutdown")
    await blob_storage.aclose()
    await cosmos_client.close()
    await credential.close()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Document Intelligent Processor",
        version="0.1.0",
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        openapi_url="/openapi.json" if settings.is_development else None,
        lifespan=lifespan,
    )

    # Middleware — registered in reverse order (last added = outermost)
    app.add_middleware(AccessLogMiddleware)
    app.add_middleware(AuthMiddleware)
    app.add_middleware(RequestIdMiddleware)

    # Exception handlers
    app.add_exception_handler(HTTPException, http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, request_validation_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_exception_handler)

    # Routers
    app.include_router(health.router)
    app.include_router(documents.router)
    app.include_router(corrections.router)
    app.include_router(jobs.router)

    return app


app = create_app()
