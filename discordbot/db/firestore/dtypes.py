from copy import deepcopy
from typing import Any, Dict

from google.api_core.exceptions import NotFound
from google.cloud.firestore import AsyncDocumentReference

from ..bases import QuizBase, UserBase


class User(UserBase):
    def __init__(
        self, data_dict: Dict[str, Any], document: AsyncDocumentReference
    ) -> None:
        super().__init__()
        data_dict = data_dict or {}
        self._data.update(data_dict)
        self._orig = deepcopy(data_dict)
        self._document = document

    async def commit(self) -> None:
        try:
            # Update diffs
            diffs = {}
            for k, v in self._data.items():
                if k not in self._orig or self._orig[k] != self._data[k]:
                    diffs[k] = v
            if diffs:
                await self._document.update(diffs)
        except NotFound:
            await self.create()

    async def create(self) -> None:
        await self._document.set(self._data)


class Quiz(QuizBase):
    def __init__(self, data_dict: Dict[str, Any]) -> None:
        super().__init__()
        data_dict = data_dict or {}
        self._data.update(data_dict)
