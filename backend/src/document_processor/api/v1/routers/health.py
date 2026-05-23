from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter

from document_processor.api.v1.dto._base import CamelCaseModel

router = APIRouter(tags=["health"])


class HealthResponse(CamelCaseModel):
    status: str
    timestamp: datetime


class VersionResponse(CamelCaseModel):
    version: str
    environment: str


@router.get("/health", response_model=HealthResponse)
async def health_live() -> HealthResponse:
    return HealthResponse(status="ok", timestamp=datetime.now(UTC))


@router.get("/health/ready", response_model=HealthResponse)
async def health_ready() -> HealthResponse:
    return HealthResponse(status="ok", timestamp=datetime.now(UTC))


@router.get("/api/v1/version", response_model=VersionResponse)
async def version() -> VersionResponse:
    from document_processor.config import get_settings

    settings = get_settings()
    return VersionResponse(version="0.1.0", environment=settings.environment)
