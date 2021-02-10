import os

from discordbot import BotClient

if __name__ == '__main__':
    token = os.environ.get('discord_token')
    client = BotClient()
    client.run(token)
