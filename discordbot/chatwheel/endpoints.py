import os
from typing import Optional, Tuple

import discord

from ..routing import Endpoint


def get_voice_client_by_guild(
    client: discord.Client, guild: discord.Guild
) -> Optional[discord.VoiceClient]:
    for voice_client in client.voice_clients:
        if voice_client.guild == guild:
            return voice_client


@Endpoint
async def join_user(
    client: discord.Client, message: discord.Message, groups: Tuple[str]
) -> None:
    # Make a connection
    author = message.author
    if isinstance(author, discord.Member) and author.voice is not None:
        await author.voice.channel.connect()
    else:
        return  # Nothing we can do


@Endpoint
async def leave_user(
    client: discord.Client, message: discord.Message, groups: Tuple[str]
) -> None:
    voice_client = get_voice_client_by_guild(client, message.guild)
    if voice_client is not None:
        await voice_client.disconnect()


@Endpoint
async def play_audio(
    client: discord.Client, message: discord.Message, groups: Tuple[str]
) -> None:
    # Detect if we have an active voice client on the server. If so, simply
    # play the audio and don't worry about switching channels. This is for
    # support for webhook integrations. Server members can still change the
    # channel of the bot by using the `.vw j` command.

    voice_client = get_voice_client_by_guild(client, message.guild)
    if voice_client is None:
        # Make a connection
        author = message.author
        if isinstance(author, discord.Member) and author.voice is not None:
            voice_client = await author.voice.channel.connect()
        else:
            return  # Nothing we can do

    fnames = {
        "next-level-play": "Misc_soundboard_next_level.mp3.mpeg",
        "ni-qi-bu-qi": "Misc_soundboard_ni_qi_bu_qi.mp3.mpeg",
        "disaster": "Misc_soundboard_disastah.mp3.mpeg",
        "lakad-matataaag": "Misc_soundboard_ta_daaaa.mp3.mpeg",
        "easy-money": "Misc_soundboard_easiest_money.mp3.mpeg",
        "dui-you-ne": "Misc_soundboard_duiyou_ne.mp3.mpeg",
        "absolutely-perfect": "Misc_soundboard_absolutely_perfect.mp3.mpeg",
        "piao-liang": "Misc_soundboard_piao_liang.mp3.mpeg",
        "ceeeb": "Misc_soundboard_ceeeb_start.mp3.mpeg",
        "cooking-boom": "Misc_soundboard_whats_cooking.mp3.mpeg",
        "no-chill": "Misc_soundboard_no_chill.mp3.mpeg",
        "gan-ma-ne-xiong-di": "Misc_soundboard_gan_ma_ne_xiong_di.mp3.mpeg",
        "xqc-wa-ching": "XQC_Lux_waching.mp3",
        "xqc-aaa-pow": "XQC_Lux_aaapow.mp3",
        "what-a-save": "What_A_Save.mp3",
    }
    fname = os.path.join(
        os.path.dirname(__file__), "audio", fnames.get(groups[0])
    )
    voice_client.play(discord.FFmpegOpusAudio(fname))
