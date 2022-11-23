import asyncio
import json
import time
from datetime import datetime, timezone
from io import BytesIO, StringIO
from typing import TYPE_CHECKING, Any, Sequence
from zipfile import ZIP_DEFLATED, ZipFile

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
    # Make sure messages are sorted by timestamp; timestamps are in ISO format
    # ISO format is YYYY-MM-DDTHH:MM:SS.mmmmmm+HH:MM. Time offsets are
    # identical for all messages in the list.
    # We can sort by timestamp lexicographically.
    user.messages.sort(key=lambda x: x["timestamp"])
    short_message = (
        message.content
        if len(message.content) <= 64
        else message.content[:61] + "..."
    )
    user.messages.append(
        {
            "id": str(message.id),
            "target": str(message.channel.id),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "content": short_message,
            "sentiment": sentiment,
            "attachments": [f.filename for f in message.attachments],
        },
    )
    if len(user.messages) > 10:
        user.messages = user.messages[-10:]
    await user.commit(transaction=transaction)

    # Download, then upload attachments to cloud storage
    download_coros = [attachment.read() for attachment in message.attachments]
    datas = await asyncio.gather(*download_coros)
    paths = [
        f"{message.author.id}/{message.id}/attachments"
        f"/{i}-{attachment.filename}"
        for i, attachment in enumerate(message.attachments)
    ]
    # Also upload the message itself
    paths.append(f"{message.author.id}/{message.id}/message.txt")
    datas.append(message.content.encode("utf-8"))
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
    json_file = discord.File(
        StringIO(data_str), f"data_{message.author.id}.json"
    )

    # Saved attachment data
    files = await self.storage.ls(f"{message.author.id}/")
    coros = [self.storage.read(path) for path in files]
    datas = await asyncio.gather(*coros)
    zip_data = BytesIO()
    with ZipFile(
        zip_data, "w", compression=ZIP_DEFLATED, compresslevel=5
    ) as fp:
        fp.writestr("data.json", data_str)
        for path, data in zip(files, datas):
            fp.writestr(path, data)

    if zip_data.getbuffer().nbytes < 1024 * 1024 * 8:
        zip_data.seek(0)
        await message.channel.send(
            "Here's your data",
            files=[
                json_file,
                discord.File(zip_data, f"data_{message.author.id}.zip"),
            ],
        )
        return

    # Upload archive to storage and point them to a download link
    # Include time to avoid serving cached copies
    fname = f"data_{message.author.id}_{int(time.time())}.zip"
    await self.storage.upload(fname, zip_data.getvalue(), public=True)
    public_url = self.storage.public_url(fname)
    await message.channel.send(
        "Here's your data. The archive was too big for Discord so here's a "
        f"download link (expires in 1 day). {public_url}",
        file=json_file,
    )
