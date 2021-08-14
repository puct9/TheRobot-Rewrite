import asyncio
from typing import TYPE_CHECKING, Sequence

import discord

from ..routing import Endpoint

if TYPE_CHECKING:
    from .. import BotClient


@Endpoint
async def manage(
    self: "BotClient", message: discord.Message, groups: Sequence[str]
) -> None:
    user, sentiment = await asyncio.gather(
        self.db.get_user(message.author.id),
        self.service.sentiment_analysis(message.content),
    )
    user.sentiment.append(sentiment)
    # Message sentiment analysis
    # There is a chance that changes are not properly pushed if messages are
    # sent too quickly. This issue may be addressed later.
    if len(user.sentiment) >= 10:
        user.sentiment = user.sentiment[-10:]
    await user.commit()
    # Message censoring
    if user.censor_exempt:
        return
    for censor in await self.db.censor_list():
        if censor in message.content:
            await message.delete()
