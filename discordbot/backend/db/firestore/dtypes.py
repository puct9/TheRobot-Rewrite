from copy import deepcopy
from typing import Any, Dict

from google.api_core.exceptions import NotFound
from google.cloud.firestore import AsyncDocumentReference, AsyncTransaction

from ..bases import BaseDataModel, CounterBase, MessageBase, QuizBase, UserBase


class CommitManager:
    def __init__(
        self, data: BaseDataModel, document: AsyncDocumentReference
    ) -> None:
        self.data = data
        self._orig = deepcopy(data._data)
        self.document = document

    async def commit(self, *, transaction: AsyncTransaction = None) -> None:
        try:
            # Update diffs
            diffs = {}
            for k, v in self.data._data.items():
                if k not in self._orig or self._orig[k] != v:
                    diffs[k] = v
            if diffs:
                if transaction is not None:
                    # No await here
                    transaction.update(self.document, diffs)
                else:
                    await self.document.update(diffs)
        except NotFound:
            await self.create()

    async def create(
        self, *, transaction: AsyncDocumentReference = None
    ) -> None:
        if transaction is not None:
            # No await here
            transaction.set(self.document, self.data._data)
        else:
            await self.document.set(self.data._data)


class User(UserBase):
    def __init__(
        self, data_dict: Dict[str, Any], document: AsyncDocumentReference
    ) -> None:
        super().__init__()
        data_dict = data_dict or {}
        self._data.update(data_dict)
        self.cm = CommitManager(self, document)

    async def commit(self, *, transaction: AsyncTransaction = None) -> None:
        await self.cm.commit(transaction=transaction)

    async def create(self, *, transaction: AsyncTransaction = None) -> None:
        await self.cm.create(transaction=transaction)


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


class Counter(CounterBase):
    def __init__(
        self, data_dict: Dict[str, Any], document: AsyncDocumentReference
    ) -> None:
        super().__init__()
        data_dict = data_dict or {}
        self._data.update(data_dict)
        self.cm = CommitManager(self, document)

    async def commit(self, *, transaction: AsyncTransaction = None) -> None:
        await self.cm.commit(transaction=transaction)

    async def create(self, *, transaction: AsyncTransaction = None) -> None:
        await self.cm.create(transaction=transaction)
