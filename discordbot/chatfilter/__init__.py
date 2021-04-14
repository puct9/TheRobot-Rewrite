from typing import Sequence

import discord

from ..routing import Endpoint

DISALLOWED = ["tenor"]


@Endpoint
async def filter(
    client: discord.Client, message: discord.Message, groups: Sequence[str]
) -> None:
    for disallowed in DISALLOWED:
        if disallowed in message.content:
            await message.delete()
