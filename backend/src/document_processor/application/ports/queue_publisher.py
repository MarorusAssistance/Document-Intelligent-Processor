from __future__ import annotations

from typing import Any, Protocol


class QueuePublisher(Protocol):
    async def publish(self, queue: str, message: dict[str, Any]) -> None: ...
