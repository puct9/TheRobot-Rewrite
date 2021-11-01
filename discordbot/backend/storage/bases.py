from typing import Any, List, Union


class BaseStorage:
    async def ls(self, prefix: str) -> List[str]:
        pass

    async def read(self, path: str) -> bytes:
        pass

    async def upload(
        self, path: Union[str, List[str]], data: Union[Any, List[Any]]
    ):
        pass
