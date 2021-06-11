from typing import List


class BaseDB:
    async def censor_list(self) -> List[str]:
        return []

    async def is_censor_exempt(self, user_id: int) -> bool:
        return False
