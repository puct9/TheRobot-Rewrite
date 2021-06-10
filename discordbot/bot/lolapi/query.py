import os
from typing import Dict, List, Tuple, Union

import httpx
from pantheon import pantheon
from pantheon.utils.exceptions import NotFound


class Summoner:
    def __init__(self, data: Dict[str, str], region: str) -> None:
        self.data = data
        self.id = data["id"]
        self.account_id = data["accountId"]
        self.puuid = data["puuid"]
        self.name = data["name"]
        self.profile_icon_id = data["profileIconId"]
        self.revision_date = data["revisionDate"]
        self.summoner_level = data["summonerLevel"]
        self.region = region

    def __getattr__(self, key: str) -> None:
        try:
            return super().__getattr__(self, key)
        except AttributeError as e:
            try:
                return self.data[key]
            except KeyError:
                raise e

    @property
    def profile_icon_url(self) -> str:
        return (
            f"https://ddragon.leagueoflegends.com/cdn/{API.game_version}/img/"
            f"profileicon/{self.profile_icon_id}.png"
        )

    async def get_masteries(self) -> Tuple[List[str], List[int]]:
        res = await API.get_panth(self.region).getChampionMasteries(self.id)
        if any(info["championId"] not in API.champions for info in res):
            await API.refresh_data(self.region)
        # Actually comes sorted from lowest to highest
        cms = [
            (API.champions[info["championId"]], info["championPoints"])
            for info in res
        ]
        names = [r[0] for r in cms[::-1]]
        points = [r[1] for r in cms[::-1]]
        return names, points


class LoLAPI:
    def __init__(self, key: str, regions: Dict[str, str]) -> None:
        self.key = key
        self.regions = regions
        self.panths = {
            k: pantheon.Pantheon(v, key) for k, v in regions.items()
        }
        self.game_version: str = ""
        self.champions: Dict[int, str] = {}
        self.champion_images: Dict[str, str] = {}

    def get_panth(self, region: str) -> pantheon.Pantheon:
        return self.panths[region.lower()]

    async def refresh_data(self, region: str) -> None:
        async with httpx.AsyncClient() as client:
            region_info = await client.get(
                f"https://ddragon.leagueoflegends.com/realms/{region}.json"
            )
            region_info = region_info.json()
            lang = "en_AU"  # region_info['l']
            ver = region_info["n"]["champion"]
            self.game_version = ver
            champdata = await client.get(
                f"https://ddragon.leagueoflegends.com/cdn/{ver}/data/{lang}/"
                "championFull.json"
            )
            champdata = champdata.json()["data"]
        for info in champdata.values():
            self.champions[int(info["key"])] = info["name"]
            self.champion_images[info["name"]] = info["image"]["full"]

    async def get_summoner_by_name(
        self, name: str, region: str
    ) -> Union[str, "Summoner"]:
        try:
            data = await self.get_panth(region).getSummonerByName(name)
        except KeyError:
            return "No such region"
        except NotFound:
            return "No such summoner"
        return Summoner(data, region.lower())


API = LoLAPI(
    os.environ.get("rg_api_key"),
    {
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
    },
)
