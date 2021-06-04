import io
import urllib.parse
from typing import Any, Dict, Tuple, Union

import discord
import numpy as np
from matplotlib import pyplot as plt

from .query import API


async def generate_visual(
    name: str, region: str
) -> Tuple[bool, Union[str, io.BytesIO]]:
    summoner = await API.get_summoner_by_name(name, region)
    if isinstance(summoner, str):
        return False, summoner
    names, points = await summoner.get_masteries()

    fig, ax = plt.subplots()

    plt.barh(np.arange(len(names)), points)
    plt.yticks(np.arange(len(names)), names)
    plt.xlabel("Mastery Points")
    plt.title(f"Champion Mastery Points for {name}")

    fig_size = plt.gcf().get_size_inches()
    scale_factor = len(names) / 25
    plt.gcf().set_size_inches(fig_size[0], fig_size[1] * max(1, scale_factor))

    fig.tight_layout()

    image_bytes = io.BytesIO()
    plt.savefig(image_bytes, format="png")

    return True, image_bytes


async def generate_embed(name: str, region: str) -> discord.Embed:
    summoner = await API.get_summoner_by_name(name, region)
    if isinstance(summoner, str):
        return False, summoner
    names, points = await summoner.get_masteries()

    # Sort decreasing
    names = names[::-1]
    points = points[::-1]
    url_arg = urllib.parse.urlencode({"userName": name})
    points_sum = sum(points)
    embed = discord.Embed(
        title="Player profile",
        url=f"https://{region.lower()}.op.gg/summoner/{url_arg}",
        description=f"{name}\nMastery points: {points_sum}",
    )
    embed.set_thumbnail(url=summoner.profile_icon_url)
    if names:
        embed.set_author(
            name=summoner.name,
            icon_url=(
                f"https://ddragon.leagueoflegends.com/cdn/{API.game_version}/"
                f"img/champion/{API.champion_images[names[0]]}"
            ),
        )
    else:
        embed.set_author(name=summoner.name)
    for n, p in zip(names[:3], points[:3]):
        embed.add_field(
            name=n, value=f"{p}\n({(p / points_sum * 100):.1f}%)", inline=True
        )
    return True, embed


async def get_game_info(
    name: str, region: str
) -> Tuple[bool, Union[str, Dict[str, Any]]]:
    summoner = await API.get_summoner_by_name(name, region)
    if isinstance(summoner, str):
        return False, summoner
    # TODO for another day
