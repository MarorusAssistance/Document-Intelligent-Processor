from __future__ import annotations

"""Smoke test against the local Cosmos DB emulator.

Requires the emulator running on https://localhost:8081.
Skip automatically when the endpoint is unreachable.
Run explicitly with:  pytest -m cosmos_emulator
"""

import os

import pytest

COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT", "https://localhost:8081")
COSMOS_KEY = os.getenv(
    "COSMOS_KEY",
    # Well-known emulator master key
    "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==",
)

pytestmark = pytest.mark.cosmos_emulator


@pytest.fixture
async def cosmos_container():  # type: ignore[no-untyped-def]
    azure_cosmos = pytest.importorskip("azure.cosmos.aio")
    CosmosClient = azure_cosmos.CosmosClient  # noqa: N806

    async with CosmosClient(COSMOS_ENDPOINT, credential=COSMOS_KEY) as client:
        try:
            db = await client.create_database_if_not_exists("docproc-test")
            container = await db.create_container_if_not_exists(
                id="smoke-test",
                partition_key={"paths": ["/clientId"], "kind": "Hash"},
            )
            yield container
        finally:
            try:
                await client.delete_database("docproc-test")
            except Exception:
                pass


@pytest.mark.asyncio
async def test_cosmos_crud(cosmos_container) -> None:  # type: ignore[no-untyped-def]
    item = {"id": "smoke-1", "clientId": "client_test", "value": "hello"}

    await cosmos_container.upsert_item(item)

    read = await cosmos_container.read_item(item="smoke-1", partition_key="client_test")
    assert read["value"] == "hello"

    await cosmos_container.delete_item(item="smoke-1", partition_key="client_test")

    from azure.cosmos.exceptions import CosmosResourceNotFoundError

    with pytest.raises(CosmosResourceNotFoundError):
        await cosmos_container.read_item(item="smoke-1", partition_key="client_test")
