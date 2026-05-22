from __future__ import annotations

from typing import Any, Protocol

# TODO(M3): define full ERP push types and complete this protocol


class ERPAdapter(Protocol):
    async def push(self, client_id: str, document_id: str, payload: dict[str, Any]) -> str:
        """Push document data to the ERP and return the external reference."""
        ...
