from copy import deepcopy
from typing import Any, Dict, List

from google.api_core.exceptions import NotFound
from google.cloud.firestore import AsyncClient, Client, DocumentReference

from ..bases import BaseDB, UserBase, QuizBase


class FirestoreDB(BaseDB):
    def __init__(self) -> None:
        self.db = AsyncClient()
        self.config = self.db.collection("config")
        self.config_censor = self.config.document("censor")
        self.users = self.db.collection("users")
        self.quiz_index = self.db.collection("quizzes").document("index")

        # First time setup
        db_sync = Client()
        sync_config = db_sync.collection("config")
        if sync_config.document("censor").get().to_dict() is None:
            sync_config.document("censor").create({"data": []})
        quiz_index = db_sync.collection("quizzes").document("index")
        if quiz_index.get().to_dict() is None:
            quiz_index.create({"subjects": []})

    async def censor_list(self) -> List[str]:
        data = await self.config_censor.get()
        return data.to_dict()["data"]

    async def get_user(self, user_id: int) -> "User":
        ref = self.users.document(str(user_id))
        data = (await ref.get()).to_dict()
        user = User(data, ref)
        if data is None:
            user.id = str(user_id)
            await user.create()
        return user

    async def quiz_subjects(self) -> List[str]:
        data = await self.quiz_index.get()
        return data.to_dict()["subjects"]

    async def quiz_list(self, subject: str) -> List[str]:
        quizzes = self.quiz_index.collection(subject).list_documents()
        return [doc.id async for doc in quizzes]

    async def get_quiz(self, subject: str, name: str) -> "QuizBase":
        data = await self.quiz_index.collection(subject).document(name).get()
        quiz = Quiz(data.to_dict())
        return quiz


class User(UserBase):
    def __init__(
        self, data_dict: Dict[str, Any], document: DocumentReference
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
