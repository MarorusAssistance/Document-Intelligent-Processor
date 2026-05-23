from __future__ import annotations

from azure.identity.aio import DefaultAzureCredential
from azure.storage.blob.aio import BlobServiceClient

_AZURITE_CONNECTION_STRING = (
    "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;"
    "AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tBh2r6ZlQHWA==;"
    "BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;"
)


class AzureBlobStorage:
    def __init__(self, account_url: str, use_azurite: bool = False) -> None:
        if use_azurite:
            self._client = BlobServiceClient.from_connection_string(_AZURITE_CONNECTION_STRING)
        else:
            self._client = BlobServiceClient(
                account_url=account_url,
                credential=DefaultAzureCredential(),
            )

    async def upload(
        self,
        container: str,
        blob_name: str,
        data: bytes,
        content_type: str,
    ) -> str:
        blob_client = self._client.get_blob_client(container=container, blob=blob_name)
        await blob_client.upload_blob(
            data,
            overwrite=True,
            content_settings={"content_type": content_type},  # type: ignore[arg-type]
        )
        return blob_client.url

    async def download(self, container: str, blob_name: str) -> bytes:
        blob_client = self._client.get_blob_client(container=container, blob=blob_name)
        stream = await blob_client.download_blob()
        return await stream.readall()

    async def delete(self, container: str, blob_name: str) -> None:
        blob_client = self._client.get_blob_client(container=container, blob=blob_name)
        await blob_client.delete_blob(delete_snapshots="include")

    async def get_url(self, container: str, blob_name: str) -> str:
        return self._client.get_blob_client(container=container, blob=blob_name).url

    async def aclose(self) -> None:
        await self._client.close()
