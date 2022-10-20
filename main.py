import discord
import os
from pyairtable import Table
from discord import app_commands
from discord import Status
import random

# setup discord connection
intents = discord.Intents(messages=True, guilds=True)
intents.message_content = True
intents.members = True
intents.presences = True
discord_bot_client = discord.Client(intents=intents)
tree = app_commands.CommandTree(discord_bot_client)

# setup airtable connection
airtable_api_key = os.environ["AIRTABLE_API_KEY"]
interview_table = Table(airtable_api_key, 'app8xDpApplv8WrVJ', 'interview')
question_table = Table(airtable_api_key, 'app8xDpApplv8WrVJ', 'questions')

# constants
GUILD_ID = 1032341469551415318  # discord server id


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

    interview_table.create({
        "name": message.author.name,
        "message": message.content
    })
    await message.channel.send(message.content[::-1])


@tree.command(name="new",
              description="Get a new question",
              guild=discord.Object(id=GUILD_ID))
async def new_command(interaction):
    random_question = random.choice(question_table.all())
    await interaction.response.send_message("Here's your question: {}".format(
        random_question['fields']['link']))


@tree.command(name="submit",
              description="Submit",
              guild=discord.Object(id=GUILD_ID))
async def submit_command(interaction):
    await interaction.response.send_message("Handle submission")


@discord_bot_client.event
async def on_member_join(member):
    # create a new channel for this new member
    new_channel = await create_channel(member)

    # send them a welcome message from the bot in their channel
    to_send = f'Suriel senses your weakness {member.mention} \n Suriel invites you to /train.'
    await new_channel.send(to_send)

    # in #general, send the new member a message about their new channel
    to_send = f'Monarch Suriel has noticed {member.mention} and invites them to {new_channel.mention}'
    await member.guild.system_channel.send(to_send)


@discord_bot_client.event
async def on_presence_update(before, after):
    if before.status == Status.offline and after.status == Status.online:
        print(
            "Handle user going online. Message in their private room and ask to continue training."
        )
    else:
        print("Handle user going offline.")


async def create_channel(member):
    overwrites = {
        member.guild.default_role:
        discord.PermissionOverwrite(read_messages=False),
        member.guild.me: discord.PermissionOverwrite(read_messages=True),
        member: discord.PermissionOverwrite(read_messages=True),
    }

    return await member.guild.create_text_channel("{}".format(member.name),
                                                  overwrites=overwrites)


discord_bot_client.run(os.getenv("TOKEN"))
