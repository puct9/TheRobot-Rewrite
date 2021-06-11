import discord

from ..db import BaseDB
from . import chatfilter, chatwheel, lolapi, proxy
from .routing import Pattern, RoutingList

DEFAULT_ROUTING = RoutingList(
    [
        Pattern(r"^\.vw ", chatwheel.PATTERNS),
        Pattern(r"^\.lol ", lolapi.PATTERNS),
        Pattern(r"\.proxy ", proxy.PATTERNS),
        Pattern(r".+", chatfilter.filter),
    ]
)


class BotClient(discord.Client):
    def __init__(self, db: BaseDB = None) -> None:
        super().__init__()
        self.db = db or BaseDB()

    async def on_ready(self) -> None:
        print(f"Logged on as {self.user}")

    async def on_message(self, message: discord.Message) -> None:
        if message.author == self.user:
            return

        if message.content == ".index":
            res = ""
            leaf_patterns = DEFAULT_ROUTING.generate_leaf_patterns()
            for leaf_pattern in leaf_patterns:
                res += (
                    f"{leaf_pattern.description}\n```re\n"
                    f"{leaf_pattern.match}```"
                )
            await message.channel.send(res)

        trace, endpoint, groups = DEFAULT_ROUTING.forward(message)
        if endpoint is None:
            return
        print(f"Message: {message.content}")
        print(f"Author: {message.author.name} ({message.author.id})")
        print(
            "\n".join(
                f"{i}: {pattern.match}" for i, pattern in enumerate(trace)
            )
        )
        print(f"-> {endpoint.func.__module__}.{endpoint.func.__name__}")
        print("========================================")
        await endpoint(self, message, groups)
