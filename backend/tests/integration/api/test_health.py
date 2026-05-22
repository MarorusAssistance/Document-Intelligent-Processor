from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_live(test_client: AsyncClient) -> None:
    response = await test_client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "timestamp" in body


@pytest.mark.asyncio
async def test_health_ready(test_client: AsyncClient) -> None:
    response = await test_client.get("/health/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_version(test_client: AsyncClient) -> None:
    response = await test_client.get("/api/v1/version")
    assert response.status_code == 200
    body = response.json()
    assert "version" in body
    assert body["environment"] == "development"
