import os

from discordbot import BotClient
from discordbot.backend.db import FirestoreDB
from discordbot.backend.services import GCPService
from discordbot.backend.storage import GCSBucket

if __name__ == "__main__":
    token = os.environ.get("discord_token")
    client = BotClient(FirestoreDB, GCPService, GCSBucket)
    client.run(token)
