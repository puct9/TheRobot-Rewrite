import asyncio
from copy import deepcopy
from typing import Any, Dict, List, Optional, Set, Tuple

from google.api_core.exceptions import NotFound
from google.cloud.firestore import (
    AsyncClient,
    AsyncCollectionReference,
    AsyncDocumentReference,
    Client,
    CollectionReference,
    DocumentReference,
    DocumentSnapshot,
)

from ..bases import BaseDB, UserBase, QuizBase


class IndexCache:
    """
    Cache for Firestore clients, automatically maintaining a list of document
    ids under a collection in an efficient manner by implementing a snapshot
    listener. It is recommended by Google to avoid too many snapshot listeners.
    This does not maintain a record of the actual data stored in the documents
    to reduce memory cost.
    """

    def __init__(
        self,
        collection_ref_sync: CollectionReference,
    ) -> None:
        # Do not update immediately - load lazily
        # If we are never called, we can potentially avoid many reads
        # If we are called and there are few documents, we don't use many reads
        # either
        self.ref = collection_ref
        self.ref_sync = collection_ref_sync
        self.client = Client()
        self.loaded = False
        self._index: Set[str] = set()

    def __del__(self) -> None:
        # Not sure if required but literally nothing to lose from this
        if hasattr(self, "watch"):
            self.watch.unsubscribe()

    async def get_document_ids(self) -> List[str]:
        if self.loaded:
            return list(self._index)
        # Start listening for updates
        self.watch = self.ref_sync.on_snapshot(self.on_snapshot)
        # Wait for the first on_snapshot call to complete. The first call will
        # contain all documents.
        while not self.loaded:
            await asyncio.sleep(0.1)
        return list(self._index)

    def on_snapshot(
        self, col_snapshot: Any, changes: Any, read_time: Any
    ) -> None:
        for change in changes:
            if change.type.name == "ADDED":
                self._index.add(change.document.id)
            if change.type.name == "REMOVED":
                try:
                    self._index.remove(change.document.id)
                except KeyError:
                    pass
        self.loaded = True


class DocumentCache:
    """
    Cache for a single document by implementing a snapshot listener. It is
    recommended by Google to avoid too many snapshot listeners.
    """

    def __init__(
        self,
        document_ref_sync: DocumentReference,
    ) -> None:
        self.ref_sync = document_ref_sync
        self.client = Client()
        self._data: Dict[str, Any] = {}
        # Nothing to gain from loading lazily
        self.watch = self.ref_sync.on_snapshot(self.on_snapshot)

    def __del__(self) -> None:
        self.watch.unsubscribe()

    async def get_dict(self) -> Optional[Dict[str, Any]]:
        # Make this a coroutine for consistency
        return deepcopy(self._data)

    def on_snapshot(
        self, doc_snapshot: DocumentSnapshot, changes: Any, read_time: Any
    ):
        # For some reasaon `doc_snapshot` can be a list [doc_snapshot]
        if isinstance(doc_snapshot, list):
            doc_snapshot = doc_snapshot[0]
        self._data = doc_snapshot.to_dict()


class FirestoreDB(BaseDB):
    def __init__(self) -> None:
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
