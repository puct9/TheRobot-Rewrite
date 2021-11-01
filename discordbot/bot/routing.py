import asyncio
import re
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Generator,
    List,
    Match,
    Tuple,
    Union,
)

import discord

if TYPE_CHECKING:
    from . import BotClient


class _EndpointCallable:
    def __init__(self, func: Callable, name: str) -> None:
        self.func = func
        self.name = name

    async def __call__(self, *args: Any, **kwargs: Any) -> None:
        await self.func(*args, **kwargs)


class Endpoint:
    def __init__(
        self,
        *,
        checkmark_react: bool = True,
        require_transaction: bool = False,
    ) -> None:
        self.checkmark_react = checkmark_react
        self.require_transaction = require_transaction

    def __call__(
        self, func: Callable[["BotClient", discord.Message, Tuple[str]], Any]
    ) -> _EndpointCallable:
        # This should get called immediately if it is being used as a decorator
        # Save the func to this object for easy access (e.g. access its name)
        self.func = func

        async def wrapped(
            client: "BotClient", message: discord.Message, groups: Tuple[str]
        ) -> None:
            # This section here gives us a chance to insert some middleware
            # Let's react with a check mark to signal to the user their query
            # is being processed.
            check_mark = chr(0x2611)  # U+2611 Check mark
            if self.checkmark_react:
                await message.add_reaction(check_mark)

            try:
                if not self.require_transaction:
                    await self.func(client, message, groups)

                else:
                    # Transactional endpoints take an extra transaction object
                    transaction = client.db.transaction()

                    @client.db.transactional
                    async def transaction_fn(t):
                        await self.func(client, message, groups, t)

                    await transaction_fn(transaction)

            except Exception as e:
                # We broke, so remove the check mark and put a cross
                coros = [message.add_reaction(chr(0x274C))]  # Cross
                if self.checkmark_react:
                    coros.append(
                        message.remove_reaction(check_mark, client.user)
                    )
                await asyncio.gather(
                    message.remove_reaction(check_mark),
                    message.add_reaction(chr(0x274C)),
                )
                raise e

            # Remove the check mark at the end of it all else it gets annoying
            if self.checkmark_react:
                await message.remove_reaction(check_mark, client.user)

        return _EndpointCallable(wrapped, f"{func.__module__}.{func.__name__}")


class Pattern:
    def __init__(
        self,
        match: str,
        to: Union[_EndpointCallable, "RoutingList"],
        description: str = "No description",
    ) -> None:
        self.match = match
        self.to = to
        self.description = description

    def do_match(self, content: str) -> Match[str]:
        return re.match(self.match, content)


class RoutingList:
    def __init__(self, patterns: List[Pattern]) -> None:
        self.patterns = patterns

    def forward(
        self, message: discord.Message
    ) -> Tuple[List[Pattern], _EndpointCallable, Tuple[str]]:
        for pattern in self.patterns:
            pattern_match = pattern.do_match(message.content)
            if pattern_match is None:
                continue
            next_routing = pattern.to
            if isinstance(next_routing, _EndpointCallable):
                return [pattern], next_routing, pattern_match.groups()
            elif isinstance(next_routing, RoutingList):
                res = next_routing.forward(message)
                return [pattern] + res[0], res[1], res[2]
            else:
                raise TypeError(
                    f"Object {next_routing} is neither an "
                    "_EndpointCallable nor a RoutingList"
                )
        return [], None, None

    def generate_leaf_patterns(self) -> Generator[Pattern, None, None]:
        for pattern in self.patterns:
            if isinstance(pattern.to, _EndpointCallable):
                yield pattern
            if isinstance(pattern.to, RoutingList):
                yield from pattern.to.generate_leaf_patterns()
