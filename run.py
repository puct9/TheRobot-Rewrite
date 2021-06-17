import os

from discordbot import BotClient
from discordbot.backend.db import FirestoreDB

if __name__ == "__main__":
    token = os.environ.get("discord_token")
    client = BotClient(FirestoreDB)
    client.run(token)
