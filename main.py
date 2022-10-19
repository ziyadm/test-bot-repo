import discord
import os
from pyairtable import Table

# setup discord connection
intents = discord.Intents(messages=True, guilds=True)
intents.message_content = True
discord_bot_client = discord.Client(intents=intents)

# setup airtable connection
airtable_api_key = os.environ["AIRTABLE_API_KEY"]
table = Table(airtable_api_key, 'app8xDpApplv8WrVJ', 'interview')
table.all()


@discord_bot_client.event
async def on_ready():
    print(f'We have logged in as {discord_bot_client.user}')


@discord_bot_client.event
async def on_message(message):
    # this processes each message sent in the discord
    # 1) it adds that message (author/content) into airtable
    # 2) it responds in discord with the same message (reversed)
    if message.author == discord_bot_client.user:
        return

    table.create({"name": message.author.name, "message": message.content})
    await message.channel.send(message.content[::-1])


discord_bot_client.run(os.getenv("TOKEN"))
