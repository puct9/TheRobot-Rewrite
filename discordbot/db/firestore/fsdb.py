from copy import deepcopy
from typing import Any, Callable, Dict, List, Optional, Tuple

from google.api_core.exceptions import NotFound
from google.cloud.firestore import (
    AsyncClient,
    AsyncCollectionReference,
    AsyncDocumentReference,
    Client,
    CollectionReference,
)

from ..bases import BaseDB, UserBase, QuizBase
from .caches import DocumentCache, IndexCache


class FirestoreDB(BaseDB):
    def __init__(self, callback: Callable[[str, Any], None]) -> None:
        self.callback = callback
        self.db = AsyncClient()
        self.users = self.db.collection("users")
        self.quiz_index = self.db.collection("quizzes").document("index")

        # First time setup
        self.db_sync = Client()
        sync_config = self.db_sync.collection("config")
        if sync_config.document("censor").get().to_dict() is None:
            sync_config.document("censor").create({"data": []})
        self.quiz_index_sync = self.db_sync.collection("quizzes").document(
            "index"
        )
        if self.quiz_index_sync.get().to_dict() is None:
            self.quiz_index_sync.create({})

        # Quiz cache as calling .stream or .list_documents on a large
        # collection is extremely inefficient (Cloud read cost)
        self.quiz_cache: Dict[str, IndexCache] = {}

        # Censor document cache
        self.censor_cache = DocumentCache(
            self.db_sync.collection("config").document("censor"),
        )

        # Quiz index document cache
        self.quiz_index_cache = DocumentCache(self.quiz_index_sync)

    async def censor_list(self) -> List[str]:
        return (await self.censor_cache.get_dict())["data"]

    async def get_user(self, user_id: int) -> "User":
        ref = self.users.document(str(user_id))
        data = (await ref.get()).to_dict()
        user = User(data, ref)
        if data is None:
            user.id = str(user_id)
            await user.create()
        return user

    async def quiz_subjects(self) -> List[str]:
        return (await self.quiz_index_cache.get_dict())["subjects"]

    async def quiz_list(self, subject: str) -> List[str]:
        res = await self.get_quiz_collection_by_subject(subject)
        if res is None:
            return []
        coll, coll_sync = res
        # Don't let the cache take priority so live changes to /quizzes/index
        # are prioritised instead
        # Also use `coll.id` instead of `subject` because mappings in the index
        # are many-to-one
        if coll.id not in self.quiz_cache:
            self.quiz_cache[coll.id] = IndexCache(coll_sync)
        return await self.quiz_cache[coll.id].get_document_ids()

    async def get_quiz(self, subject: str, name: str) -> "QuizBase":
        coll, _ = await self.get_quiz_collection_by_subject(subject)
        if coll is None:
            return QuizBase()
        data = await coll.document(name).get()
        quiz = Quiz(data.to_dict())
        return quiz

    async def get_quiz_collection_by_subject(
        self, subject: str
    ) -> Optional[Tuple[AsyncCollectionReference, CollectionReference]]:
        coll = (await self.quiz_index_cache.get_dict()).get(subject)
        if coll is not None:
            return (
                self.quiz_index.collection(coll),
                self.quiz_index_sync.collection(coll),
            )


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
