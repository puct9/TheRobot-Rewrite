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
        self.public_bucket = self.client.get_bucket(
            os.environ.get("PUBLIC_BUCKET_NAME")
        )

    @property
    def bucket_name(self) -> str:
        return self.bucket.name

    @property
    def public_bucket_name(self) -> str:
        return self.public_bucket.name

    async def ls(self, prefix: str) -> List[str]:
        return await self.bucket.list_blobs(prefix)

    async def read(self, path: str) -> bytes:
        return await self.client.download(self.bucket_name, path)

    async def upload(
        self,
        path: Union[str, List[str]],
        data: Union[Any, List[Any]],
        *,
        public: bool = False,
    ) -> None:
        if not path:
            return
        if (isinstance(path, list) and not isinstance(data, list)) or (
            not isinstance(path, list) and isinstance(data, list)
        ):
            raise TypeError(
                "Either none or both of path and data must be list"
            )
        dest = self.bucket_name if not public else self.public_bucket_name
        if not isinstance(path, list):
            await self.client.upload(dest, path, data)
        else:
            coros = []
            for p, d in zip(path, data):
                coros.append(self.client.upload(dest, p, d))
            await asyncio.gather(*coros)

    def public_url(self, path: str) -> str:
        return (
            f"https://{self.public_bucket_name}.storage.googleapis.com/{path}"
        )
