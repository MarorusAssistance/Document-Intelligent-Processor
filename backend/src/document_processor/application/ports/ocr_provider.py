from __future__ import annotations

from typing import Any, Protocol

# TODO(M1): define full OCR result type and complete this protocol


class OCRProvider(Protocol):
    async def analyze(self, blob_url: str, model_id: str) -> dict[str, Any]:
        """Submit a document for analysis and return the raw provider result."""
        ...
