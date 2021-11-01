import asyncio
import os
from typing import Any, List, Union

from gcloud.aio.storage import Storage

from ..bases import BaseStorage


class GCSBucket(BaseStorage):
    def __init__(self) -> None:
        self.bucket_name = os.environ.get("BUCKET_NAME")

    async def upload(
        self, path: Union[str, List[str]], data: Union[Any, List[Any]]
    ):
        if not path:
            return
        if (isinstance(path, list) and not isinstance(data, list)) or (
            not isinstance(path, list) and isinstance(data, list)
        ):
            raise TypeError(
                "Either none or both of path and data must be list"
            )
        async with Storage(
            service_file=os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        ) as client:
            if not isinstance(path, list):
                await client.upload(self.bucket_name, path, data)
            else:
                coros = []
                for p, d in zip(path, data):
                    coros.append(client.upload(self.bucket_name, p, d))
                await asyncio.gather(*coros)
