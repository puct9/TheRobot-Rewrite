from typing import TYPE_CHECKING, Sequence

import discord

from ..routing import Endpoint

if TYPE_CHECKING:
    from .. import BotClient


@Endpoint
async def filter(
    self: "BotClient", message: discord.Message, groups: Sequence[str]
) -> None:
    user = await self.db.get_user(message.author.id)
    if user.censor_exempt:
        return
    disallowed = await self.db.censor_list()
    for censor in disallowed:
        if censor in message.content:
            await message.delete()
