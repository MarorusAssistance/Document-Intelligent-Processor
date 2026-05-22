from __future__ import annotations

import json
from typing import Any

from azure.identity.aio import DefaultAzureCredential
from azure.servicebus.aio import ServiceBusClient
from azure.servicebus import ServiceBusMessage


class ServiceBusQueuePublisher:
    def __init__(self, fully_qualified_namespace: str) -> None:
        self._namespace = fully_qualified_namespace
        self._credential = DefaultAzureCredential()

    async def publish(self, queue: str, message: dict[str, Any]) -> None:
        async with ServiceBusClient(
            fully_qualified_namespace=self._namespace,
            credential=self._credential,
        ) as client:
            async with client.get_queue_sender(queue_name=queue) as sender:
                await sender.send_messages(ServiceBusMessage(json.dumps(message)))
