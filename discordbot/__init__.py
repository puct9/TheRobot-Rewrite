import discord

from . import ai, chatwheel, chatfilter
from .routing import Pattern, RoutingList

DEFAUT_ROUTING = RoutingList(
    [
        Pattern(r"^\.vw ", chatwheel.PATTERNS),
        Pattern(r"\.ai ", ai.PATTERNS),
        Pattern(r".+", chatfilter.filter),
    ]
)


class BotClient(discord.Client):
    def __init__(self) -> None:
        super().__init__()

    async def on_ready(self) -> None:
        print(f"Logged on as {self.user}")

    async def on_message(self, message: discord.Message) -> None:
        if message.author == self.user:
            return

        if message.content == ".index":
            res = ""
            leaf_patterns = DEFAUT_ROUTING.generate_leaf_patterns()
            for leaf_pattern in leaf_patterns:
                res += (
                    f"{leaf_pattern.description}\n```re\n"
                    f"{leaf_pattern.match}```"
                )
            await message.channel.send(res)

        trace, endpoint, groups = DEFAUT_ROUTING.forward(message)
        if endpoint is None:
            return
        print(f"Message: {message.content}")
        print(
            "\n".join(
                f"{i}: {pattern.match}" for i, pattern in enumerate(trace)
            )
        )
        print("========================================")
        await endpoint(self, message, groups)
