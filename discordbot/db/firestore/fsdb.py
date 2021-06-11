from typing import List
from google.cloud.firestore import AsyncClient, Client

from ..bases import BaseDB


class FirestoreDB(BaseDB):
    def __init__(self) -> None:
        self.db = AsyncClient()
        self.config = self.db.collection("config")
        self.config_censor = self.config.document("censor")
        self.config_exempt = self.config.document("exempt")

        # First time setup
        db_sync = Client()
        sync_config = db_sync.collection("config")
        if sync_config.document("censor").get().to_dict() is None:
            sync_config.document("censor").create({"data": []})
        if sync_config.document("exempt").get().to_dict() is None:
            sync_config.document("exempt").create({})

    async def censor_list(self) -> List[str]:
        data = await self.config_censor.get()
        return data.to_dict()["data"]

    async def is_censor_exempt(self, user_id: int) -> bool:
        data = await self.config_exempt.get()
        return data.to_dict().get(str(user_id), False)
