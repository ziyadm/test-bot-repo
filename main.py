import discord
import os
from pyairtable import Table
from discord import app_commands
import random


# setup discord connection
intents = discord.Intents(messages=True, guilds=True)
intents.message_content = True
discord_bot_client = discord.Client(intents=intents)
tree = app_commands.CommandTree(discord_bot_client)


# setup airtable connection
airtable_api_key = os.environ["AIRTABLE_API_KEY"]
interview_table = Table(airtable_api_key, 'app8xDpApplv8WrVJ', 'interview')
question_table = Table(airtable_api_key, 'app8xDpApplv8WrVJ', 'questions')

# constants
GUILD_ID = 1032341469551415318 # discord server id

@discord_bot_client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f'We have logged in as {discord_bot_client.user}')


@discord_bot_client.event
async def on_message(message):
    # this processes each message sent in the discord
    # 1) it adds that message (author/content) into airtable
    # 2) it responds in discord with the same message (reversed)
    if message.author == discord_bot_client.user:
        return

    interview_table.create({"name": message.author.name, "message": message.content})
    await message.channel.send(message.content[::-1])


@tree.command(name = "new", description = "Get a new question", guild=discord.Object(id=GUILD_ID))
async def new_command(interaction):
    random_question = random.choice(question_table.all())
    await interaction.response.send_message("Here's your question: {}".format(random_question['fields']['link']))


discord_bot_client.run(os.getenv("TOKEN"))
