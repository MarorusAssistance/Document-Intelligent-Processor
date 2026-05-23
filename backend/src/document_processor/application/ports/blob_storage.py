from __future__ import annotations

from typing import Protocol


class BlobStorage(Protocol):
    async def upload(self, container: str, blob_name: str, data: bytes, content_type: str) -> str:
        """Upload blob and return its URL."""
        ...

    async def download(self, container: str, blob_name: str) -> bytes: ...

    async def delete(self, container: str, blob_name: str) -> None: ...

    async def get_url(self, container: str, blob_name: str) -> str: ...
