from typing import TYPE_CHECKING, Any, Sequence

import discord

from ..routing import Endpoint

if TYPE_CHECKING:
    from .. import BotClient


@Endpoint(require_transaction=True)
async def edit_counter(
    self: "BotClient",
    message: discord.Message,
    groups: Sequence[str],
    transaction: Any,
) -> None:
    name, mode = groups
    counter = await self.db.get_counter(name, transaction=transaction)
    if mode == "+":
        counter.value += 1
    elif mode == "-":
        if counter.value > 0:
            counter.value -= 1
        else:
            await message.channel.send(
                "Counter is already 0, cannot decrement."
            )
            return
    await counter.commit(transaction=transaction)
    await message.channel.send(
        f'Counter "{counter.name}" is now at {counter.value}.'
    )
