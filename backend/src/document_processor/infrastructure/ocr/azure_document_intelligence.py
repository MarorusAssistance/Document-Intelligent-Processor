from __future__ import annotations

from typing import Any

from azure.ai.documentintelligence.aio import DocumentIntelligenceClient
from azure.identity.aio import DefaultAzureCredential


class AzureDocumentIntelligenceProvider:
    """Stub OCR provider. Full implementation in M1."""

    def __init__(self, endpoint: str) -> None:
        self._client = DocumentIntelligenceClient(
            endpoint=endpoint,
            credential=DefaultAzureCredential(),
        )

    async def analyze(self, blob_url: str, model_id: str) -> dict[str, Any]:
        # TODO(M1): implement full analysis, polling, and result mapping
        raise NotImplementedError("OCR extraction is implemented in M1")

    async def aclose(self) -> None:
        await self._client.close()
