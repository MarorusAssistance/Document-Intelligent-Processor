from __future__ import annotations

from azure.cosmos.aio import CosmosClient
from azure.identity.aio import DefaultAzureCredential


def build_cosmos_client(endpoint: str) -> CosmosClient:
    """Build an async Cosmos DB client using DefaultAzureCredential.

    Caller is responsible for closing the client (use as async context manager
    or call await client.close() in the app lifespan shutdown hook).
    """
    credential = DefaultAzureCredential()
    return CosmosClient(url=endpoint, credential=credential)
