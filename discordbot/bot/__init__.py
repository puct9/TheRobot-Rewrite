import asyncio
import traceback
from typing import Any, Dict, List, Tuple, Type

import discord
import discord.ext.tasks

from ..db import BaseDB
from . import chatfilter, chatwheel, lolapi, proxy, quiz
from .routing import Pattern, RoutingList

DEFAULT_ROUTING = RoutingList(
    [
        Pattern(r"^\.vw ", chatwheel.PATTERNS),
        Pattern(r"^\.lol ", lolapi.PATTERNS),
        Pattern(r"^\.proxy ", proxy.PATTERNS),
        Pattern(r"^\.quiz", quiz.PATTERNS),
        Pattern(r".+", chatfilter.filter),
    ]
)


class BotClient(discord.Client):
    def __init__(self, db_type: Type[BaseDB] = BaseDB) -> None:
        super().__init__()
        self.db = db_type(self.db_callback)
        self.db_callback_buffer: List[Tuple[str, Dict[str, Any]]] = []
        self.ready = False
        self.run_db_callbacks.start()

    async def on_ready(self) -> None:
        print(f"Logged on as {self.user}\n{'=' * 79}")
        self.ready = True

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
        print(f"Channel: {message.channel.id}")
        print(f"Author: {message.author.name} ({message.author.id})")
        print(
            "\n".join(
                f"{i}: {pattern.match}" for i, pattern in enumerate(trace)
            )
        )
        print(f"-> {endpoint.func.__module__}.{endpoint.func.__name__}")
        print("=" * 79)
        try:
            await endpoint(self, message, groups)
        except Exception:
            traceback.print_exc()

    @discord.ext.tasks.loop(seconds=0.5)
    async def run_db_callbacks(self) -> None:
        if not self.ready:
            return
        if self.db_callback_buffer:
            try:
                await self.db_callback_async(*self.db_callback_buffer.pop())
            except Exception as e:
                print(f"DB Callback failed on {e}")

    def db_callback(self, event: str, data: Dict[str, Any]) -> None:
        # Important note: this method can be called from other threads!
        self.db_callback_buffer.append((event, data))

    async def db_callback_async(
        self, event: str, data: Dict[str, Any]
    ) -> None:
        while not self.ready:
            await asyncio.sleep(0.1)
        print(f"DB Callback: {event}")
        print(f"Data: {data}")
        # This is just a PoC for now
        if event == "message":
            target: str = data["target"]
            content: str = data["content"]
            channel = await self.fetch_channel(int(target))
            await channel.send(content)
        print("=" * 79)
