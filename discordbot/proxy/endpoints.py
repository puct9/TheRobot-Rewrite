from typing import Sequence

import discord

from ..routing import Endpoint


@Endpoint
async def proxy_embed(
    client: discord.Client, message: discord.Message, groups: Sequence[str]
) -> None:
    # Parse the message
    data = {
        "title": "",
        "url": "",
        "description": "",
        "colour": 0x09E0D8,
        "author_name": "",
        "author_url": "",
        "author_icon_url": "",
        "thumbnail": "",
        "fields": [],
        "footer": "",
        "null": "",
    }

    modes = {
        "t": "title",
        "u": "url",
        "d": "description",
        "c": "colour",
        "an": "author_name",
        "au": "author_url",
        "aiu": "author_icon_url",
        "tn": "thumbnail",
        "f": "fields",
        "fi": "fields",
        "fo": "footer",
        "n": "null",
    }

    current_mode = "n"
    dest = "null"
    current_data = ""
    for line in message.content.split("\n"):
        line: str
        line_words = line.split()
        line_start = line_words[0]
        for mode in modes:
            prefix = f".{mode}"
            if line_start == prefix:
                current_data = current_data.strip().strip("<>")
                if dest == "fields":
                    data["fields"].append((current_data, current_mode == "fi"))
                else:
                    data[dest] += current_data
                current_mode = mode
                current_data = ""
                line = " ".join(line_words[1:])
                break
        dest = modes[current_mode]
        current_data += "\n" + line
    if dest == "fields":
        data["fields"].append((current_data, current_mode == "fi"))
    else:
        data[dest] += current_data

    init_kwargs = {"url": data["url"], "description": data["description"]}
    embed = discord.Embed(
        title=data["title"],
        color=data["colour"],
        **{k: v for k, v in init_kwargs.items() if v},
    )
    if data["author_name"]:
        author_kwargs = {
            "name": data["author_name"],
            "url": data["author_url"],
            "icon_url": data["author_icon_url"],
        }
        embed.set_author(**{k: v for k, v in author_kwargs.items() if v})
    if data["thumbnail"]:
        embed.set_thumbnail(url=data["thumbnail"])
    for text, inline in data["fields"]:
        try:
            name, value = text.split(":")
        except ValueError:
            continue
        embed.add_field(name=name.strip(), value=value.strip(), inline=inline)
    if data["footer"]:
        embed.set_footer(text=data["footer"])
    await message.channel.send(embed=embed)
