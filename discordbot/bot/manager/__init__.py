import asyncio
import json
from io import BytesIO, StringIO
from typing import TYPE_CHECKING, Any, Sequence
from zipfile import ZipFile

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
    user.messages.append(
        {
            "id": str(message.id),
            "target": str(message.channel.id),
            "content": short_message,
            "attachments": [f.filename for f in message.attachments],
        }
    )
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

    # Download, then upload attachments to cloud storage
    paths = []
    download_coros = []
    for attachment in message.attachments:
        paths.append(f"{message.author.id}/{message.id}/{attachment.filename}")
        download_coros.append(attachment.read())
    datas = await asyncio.gather(*download_coros)
    await self.storage.upload(paths, datas)

    # Message censoring
    if user.censor_exempt:
        return
    for censor in await self.db.censor_list():
        if censor in message.content:
            await message.delete()


@Endpoint()
async def user_data(
    self: "BotClient",
    message: discord.Message,
    groups: Sequence[str],
) -> None:
    # General user data
    user = await self.db.get_user(message.author.id)
    data_str = json.dumps(user._data, indent=4)

    # Saved attachment data
    files = await self.storage.ls(f"{message.author.id}/")
    coros = [self.storage.read(path) for path in files]
    datas = await asyncio.gather(*coros)
    zip_data = BytesIO()
    with ZipFile(zip_data, "w") as fp:
        fp.writestr("data.json", data_str)
        for path, data in zip(files, datas):
            fp.writestr(path, data)
    zip_data.seek(0)

    await message.channel.send(
        "Here's your data",
        files=[
            discord.File(StringIO(data_str), f"data_{message.author.id}.json"),
            discord.File(zip_data, f"data_{message.author.id}.zip"),
        ],
    )
