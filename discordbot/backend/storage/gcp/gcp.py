import asyncio
import os
from typing import Any, List, Union

from gcloud.aio.storage import Storage

from ..bases import BaseStorage


class GCSBucket(BaseStorage):
    def __init__(self) -> None:
        self.client = Storage(
            service_file=os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        )
        self.bucket = self.client.get_bucket(os.environ.get("BUCKET_NAME"))

    @property
    def bucket_name(self) -> str:
        return self.bucket.name

    async def ls(self, prefix: str) -> List[str]:
        return await self.bucket.list_blobs(prefix)

    async def read(self, path: str) -> bytes:
        return await self.client.download(self.bucket_name, path)

    async def upload(
        self, path: Union[str, List[str]], data: Union[Any, List[Any]]
    ) -> None:
        if not path:
            return
        if (isinstance(path, list) and not isinstance(data, list)) or (
            not isinstance(path, list) and isinstance(data, list)
        ):
            raise TypeError(
                "Either none or both of path and data must be list"
            )
        if not isinstance(path, list):
            await self.client.upload(self.bucket_name, path, data)
        else:
            coros = []
            for p, d in zip(path, data):
                coros.append(self.client.upload(self.bucket_name, p, d))
            await asyncio.gather(*coros)
