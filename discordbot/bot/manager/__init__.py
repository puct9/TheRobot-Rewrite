import asyncio
from typing import TYPE_CHECKING, Any, Sequence

import discord

from ..routing import Endpoint

if TYPE_CHECKING:
    from .. import BotClient


@Endpoint(checkmark_react=False, require_transaction=True)
async def manage(
    self: "BotClient",
    message: discord.Message,
    groups: Sequence[str],
    transaction: Any,
) -> None:
    user, sentiment = await asyncio.gather(
        self.db.get_user(message.author.id, transaction=transaction),
        self.service.sentiment_analysis(message.content),
    )
    # Update user name e.g. "Puct#9551"
    user.name = f"{message.author.name}#{message.author.discriminator}"
    # Update user message history
    short_message = (
        message.content
        if len(message.content) <= 64
        else message.content[:61] + "..."
    )
    user.messages.append(short_message)
    if len(user.messages) >= 10:
        user.messages = user.messages[-10:]
    # Update user sentiment ratings
    user.sentiment.append(sentiment)
    # Message sentiment analysis
    if len(user.sentiment) >= 10:
        user.sentiment = user.sentiment[-10:]
    # There is a chance that changes are not properly pushed if messages are
    # sent too quickly. This issue may be addressed later.
    await user.commit(transaction=transaction)
    # Message censoring
    if user.censor_exempt:
        return
    for censor in await self.db.censor_list():
        if censor in message.content:
            await message.delete()
