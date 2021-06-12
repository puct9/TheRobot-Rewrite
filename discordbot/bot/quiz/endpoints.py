import asyncio
import random
import time
from typing import TYPE_CHECKING, Sequence

import discord

from ..routing import Endpoint

if TYPE_CHECKING:
    from .. import BotClient


@Endpoint
async def quiz_subject_random(
    self: "BotClient", message: discord.Message, groups: Sequence[str]
) -> None:
    # 0x01F1E6 is the unicode for 'A' regional indicator
    regional_indicator_base = 0x01F1E6
    character_emojis = [
        chr(v)
        for v in range(regional_indicator_base, regional_indicator_base + 26)
    ]
    validate_symbol = chr(0x2611)  # U+2611 Check mark
    subject = groups[0]
    quizzes = await self.db.quiz_list(subject)
    if not quizzes:
        await message.channel.send(
            "The subject cannot be found or there are no questions"
        )
        return
    quiz = await self.db.get_quiz(subject, random.choice(quizzes))
    embed = discord.Embed(title="Question", description=quiz.question)
    if not quiz.ordered:
        random.shuffle(quiz.options)
    for i, option in enumerate(quiz.options):
        embed.add_field(
            name=character_emojis[i],
            value=option["answer"],
            inline=False,
        )
    footer = "Select " + ("one" if quiz.required_correct == 1 else "multiple")
    embed.set_footer(text=footer)
    emb_msg = await message.channel.send(embed=embed)
    # Add reactions for user to click on
    for i, _ in enumerate(quiz.options):
        await emb_msg.add_reaction(character_emojis[i])
    await emb_msg.add_reaction(validate_symbol)  # Check mark

    # Poll every few seconds to see if a user has answered (with timeout)
    delay = 0
    quiz_timeout = 60
    refresh_delay = 1
    for _ in range((quiz_timeout - 1) // refresh_delay + 1):
        # 1 - delay so we don't count the time of awaiting the message
        await asyncio.sleep(1 - delay)
        delay = time.time()
        emb_msg = await message.channel.fetch_message(emb_msg.id)
        stop_poll = False
        for reaction in emb_msg.reactions:
            emoji = reaction.emoji
            stop_poll = emoji == validate_symbol and reaction.count > 1
        if stop_poll:
            break
        delay = time.time() - delay

    # Validate answer
    responses = [False] * len(quiz.options)
    for reaction in emb_msg.reactions:
        emoji = reaction.emoji
        idx = ord(emoji) - regional_indicator_base
        if 0 <= idx < len(quiz.options):
            responses[idx] = reaction.count > 1
    if not any(responses):
        await message.channel.send("Out of time!")
        return
    n_correct = 0
    correct_responses = [option["correct"] for option in quiz.options]
    for expected, response in zip(correct_responses, responses):
        n_correct += expected and response
        if not expected and response:  # User chose a wrong answer
            n_correct = -1
            break

    # Ending message
    emojis = [
        character_emojis[i] for i, c in enumerate(correct_responses) if c
    ]
    if n_correct >= quiz.required_correct:
        await message.channel.send("That's right! Good job.")
    elif quiz.required_correct == 1:
        if len(emojis) > 1:
            answers = "either " + " or ".join(emojis)
        else:
            answers = emojis[0]
        await message.channel.send(
            f"That's wrong! The right answer is {answers}"
        )
    else:  # multiple answers required questions
        answers = " and ".join(emojis)
        await message.channel.send(
            f"That's wrong! The right answer is {answers}"
        )
