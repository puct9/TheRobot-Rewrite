import io
from typing import Sequence

import discord

from ..routing import Endpoint
from .utils import generate_visual


@Endpoint
async def lol_masteries(
    client: discord.Client, message: discord.Message, groups: Sequence[str]
) -> None:
    region = groups[0]
    user_name = groups[1]
    success, image_bytes = await generate_visual(user_name, region)
    if not success:
        await message.channel.send(image_bytes)
        return
    await message.channel.send(
        file=discord.File(
            io.BytesIO(image_bytes.getvalue()), filename="masteries.png"
        )
    )
