import numpy as np
from typing import TYPE_CHECKING, Sequence

import discord

from ..routing import Endpoint

if TYPE_CHECKING:
    from .. import BotClient


@Endpoint
async def manage(
    self: "BotClient", message: discord.Message, groups: Sequence[str]
) -> None:
    user = await self.db.get_user(message.author.id)
    # Message sentiment analysis
    # There is a chance that changes are not properly pushed if messages are
    # sent too quickly. This issue may be addressed later.
    user.sentiment.append(
        await self.service.sentiment_analysis(message.content)
    )
    if len(user.sentiment) >= 10:
        scores = np.clip(user.sentiment, -2, 2)
        if scores.mean() < 0:
            await message.channel.send("Remember to be nice :smiley:")
            user.sentiment = []
        elif scores.mean() > 0 and scores.min() >= 0:
            await message.add_reaction(chr(0x2B50))
            user.sentiment = []
        else:
            user.sentiment = user.sentiment[-10:]
    await user.commit()
    # Message censoring
    if user.censor_exempt:
        return
    for censor in await self.db.censor_list():
        if censor in message.content:
            await message.delete()
