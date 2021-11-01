from typing import Any, List, Union


class BaseStorage:
    async def upload(
        self, path: Union[str, List[str]], data: Union[Any, List[Any]]
    ):
        pass
