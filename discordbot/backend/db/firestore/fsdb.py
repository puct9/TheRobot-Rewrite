from typing import Any, Callable, Dict, List, Optional, Tuple

from google.cloud.firestore import (
    AsyncClient,
    AsyncCollectionReference,
    AsyncTransaction,
    Client,
    CollectionReference,
    async_transactional,
)

from ..bases import BaseDB, QuizBase, UserBase
from .caches import DocumentCache, IndexCache
from .dtypes import Quiz, User
from .fsms import FirestoreMessagingService


class FirestoreDB(BaseDB):
    def __init__(self, callback: Callable[[str, Any], None]) -> None:
        self.transactional = async_transactional

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

        # Messaging service
        self.messaging_service = FirestoreMessagingService(
            self.db_sync.collection("messaging"), self.callback
        )

    def transaction(self) -> Any:
        return self.db.transaction()

    async def censor_list(self) -> List[str]:
        return (await self.censor_cache.get_dict())["data"]

    async def get_user(
        self, user_id: int, *, transaction: AsyncTransaction = None
    ) -> UserBase:
        ref = self.users.document(str(user_id))
        data = (await ref.get(transaction=transaction)).to_dict()
        user = User(data, ref)
        if data is None:
            user.id = str(user_id)
            await user.create(transaction=transaction)
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

    async def get_quiz(self, subject: str, name: str) -> QuizBase:
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
