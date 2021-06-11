import io
from typing import TYPE_CHECKING, Sequence

import discord

from ..routing import Endpoint
from .utils import generate_embed, generate_visual

if TYPE_CHECKING:
    from .. import BotClient


@Endpoint
async def lol_masteries(
    self: "BotClient", message: discord.Message, groups: Sequence[str]
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


@Endpoint
async def lol_profile(
    self: "BotClient", message: discord.Message, groups: Sequence[str]
) -> None:
    region = groups[0]
    user_name = groups[1]
    success, embed = await generate_embed(user_name, region)
    if not success:
        await message.channel.send(embed)
        return
    await message.channel.send(embed=embed)
