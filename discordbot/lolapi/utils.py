import io
import os
from typing import List, Tuple, Union

import httpx
import numpy as np
from matplotlib import pyplot as plt
from pantheon import pantheon
from pantheon.utils.exceptions import NotFound

apikey = os.environ.get("rg_api_key")
regions = {
    "br": "br1",
    "eune": "eun1",
    "euw": "euw1",
    "jp": "jp1",
    "kr": "kr",
    "lan": "la1",
    "las": "la2",
    "na": "na1",
    "oce": "oc1",
    "tr": "tr1",
    "ru": "ru",
}
champs = {}

panths = {k: pantheon.Pantheon(v, apikey) for k, v in regions.items()}


async def get_champions(region):
    async with httpx.AsyncClient() as client:
        region_info = await client.get(
            f"https://ddragon.leagueoflegends.com/realms/{region}.json"
        )
        region_info = region_info.json()
        lang = "en_AU"  # region_info['l']
        ver = region_info["n"]["champion"]
        champdata = await client.get(
            f"https://ddragon.leagueoflegends.com/cdn/{ver}/data/{lang}/"
            "championFull.json"
        )
        champdata = champdata.json()["data"]
    for info in champdata.values():
        champs[int(info["key"])] = info["name"]


async def get_masteries(
    name: str, region: str
) -> Tuple[Union[bool, List[str]], Union[str, Union[str, List[int]]]]:
    if region.lower() not in regions:
        return False, "No such region"
    try:
        sid = await panths[region.lower()].getSummonerByName(name)
    except NotFound:
        return False, "No such summoner"
    res = await panths[region.lower()].getChampionMasteries(sid["id"])

    if any(info["championId"] not in champs for info in res):
        await get_champions(region.lower())
    cms = [
        (champs[info["championId"]], info["championPoints"]) for info in res
    ]
    names = [d[0] for d in cms[::-1]]
    points = [d[1] for d in cms[::-1]]
    return names, points


async def generate_visual(
    name: str, region: str
) -> Tuple[bool, Union[str, io.BytesIO]]:
    names, points = await get_masteries(name, region)
    if not names:
        return names, points

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
