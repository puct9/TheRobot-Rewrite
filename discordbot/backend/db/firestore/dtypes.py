from copy import deepcopy
from typing import Any, Dict

from google.api_core.exceptions import NotFound
from google.cloud.firestore import AsyncDocumentReference, AsyncTransaction

from ..bases import MessageBase, QuizBase, UserBase


class User(UserBase):
    def __init__(
        self, data_dict: Dict[str, Any], document: AsyncDocumentReference
    ) -> None:
        super().__init__()
        data_dict = data_dict or {}
        self._data.update(data_dict)
        self._orig = deepcopy(data_dict)
        self._document = document

    async def commit(self, *, transaction: AsyncTransaction = None) -> None:
        try:
            # Update diffs
            diffs = {}
            for k, v in self._data.items():
                if k not in self._orig or self._orig[k] != self._data[k]:
                    diffs[k] = v
            if diffs:
                if transaction is not None:
                    # No await here
                    transaction.update(self._document, diffs)
                else:
                    await self._document.update(diffs)
        except NotFound:
            await self.create()

    async def create(self, *, transaction: AsyncTransaction = None) -> None:
        if transaction is not None:
            # Also no await here
            transaction.set(self._document, self._data)
        else:
            await self._document.set(self._data)


class Quiz(QuizBase):
    def __init__(self, data_dict: Dict[str, Any]) -> None:
        super().__init__()
        data_dict = data_dict or {}
        self._data.update(data_dict)


class Message(MessageBase):
    def __init__(self, data_dict: Dict[str, Any]) -> None:
        super().__init__()
        data_dict = data_dict or {}
        self._data.update(data_dict)
