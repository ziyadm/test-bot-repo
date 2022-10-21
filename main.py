import discord
import os
from pyairtable import Table
from discord import app_commands
from discord import Status
import random
import asyncio
import uuid
from pyairtable.formulas import match

# setup discord connection
intents = discord.Intents(messages=True, guilds=True)
intents.message_content = True
intents.members = True
intents.presences = True
discord_client = discord.Client(intents=intents)
tree = app_commands.CommandTree(discord_client)

# setup airtable connection
airtable_api_key = os.environ["AIRTABLE_API_KEY"]
interviews_table = Table(airtable_api_key, 'app8xDpApplv8WrVJ', 'interview')
questions_table = Table(airtable_api_key, 'app8xDpApplv8WrVJ', 'questions')
users_table = Table(airtable_api_key, 'app8xDpApplv8WrVJ', 'users')
missions_table = Table(airtable_api_key, 'app8xDpApplv8WrVJ', 'missions')

# constants
GUILD_ID = 1032341469551415318  # discord server id

# bot commands
@tree.command(name="new",
              description="Get a new question",
              guild=discord.Object(id=GUILD_ID))
async def new_command(interaction):
    # tell user what is about to happen
    # await inform_player_new_mission(interaction)

    # pick a question and update database
    member = interaction.user
    random_question = random.choice(questions_table.all())

    find_reviewer_formula = match({"role": "reviewer"})
    random_reviewer = random.choice(users_table.all(formula=find_reviewer_formula))

    find_matching_player_formula = match({"discord_name": member.name, "discord_id": member.id})
    player = users_table.first(formula=find_matching_player_formula)
  
    print("Member: {}".format(member))
    print("Question: {}".format(random_question))
    print("Reviewer: {}".format(random_reviewer))
    print("Player: {}".format(player))
  
    missions_table.create({
        "mission_id": str(uuid.uuid4()),
        "player_id": player['fields']['user_id'],
        "reviewer_id": random_reviewer['fields']['user_id'],
        "question_id": random_question['fields']['question_id'],
        "step": "design", 
        "status": "new"
    })

    # create new channel for question and invite user
    question_name = random_question['fields']['link'].split('problems/')[-1].strip('/')
    print("Question Name: {}".format(question_name))
    question_channel = await create_channel(member, channel_name=question_name)
    
    # message in channel with new question details
    await question_channel.send("Here's your question: {}".format(
        random_question['fields']['link']))

    main_channel = interaction.channel
    to_send = f'Monarch Suriel has noticed {member.mention} and invites them to {question_channel.mention}'
    await main_channel.send(to_send)

@tree.command(name="submit",
              description="Submit",
              guild=discord.Object(id=GUILD_ID))
async def submit_command(interaction):
    await interaction.response.send_message("Handle submission")

# events
# when this process connects to the discord server
@discord_client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f'We have logged in as {discord_client.user}')

# when any message is sent in discord
@discord_client.event
async def on_message(message):
    # this processes each message sent in the discord
    # 1) it adds that message (author/content) into airtable
    # 2) it responds in discord with the same message (reversed)
    if message.author == discord_client.user:
        return

    interviews_table.create({
        "name": message.author.name,
        "message": message.content
    })
    await message.channel.send(message.content[::-1])

# when a new user joins the discord server
@discord_client.event
async def on_member_join(member):
    # add this user to airtable
    user = await add_new_user(member)
  
    # create a new channel for this new member
    new_channel = await create_channel(member, channel_name="{}-home".format(member.name))

    # send them a welcome message from the bot in their channel
    to_send = f'Suriel senses your weakness {member.mention}'
    await new_channel.send(to_send)

    await asyncio.sleep(2)

    to_send = 'Suriel invites you to train on the path.'
    await new_channel.send(to_send)

    await asyncio.sleep(2)
    to_send = 'Suriel suggests /new'
    await new_channel.send(to_send)

    # in #general, send the new member a message about their new channel
    to_send = f'Monarch Suriel has noticed {member.mention} and invites them to {new_channel.mention}'
    await member.guild.system_channel.send(to_send)

# when a user goes online/offline
@discord_client.event
async def on_presence_update(before, after):
    if before.status == Status.offline and after.status == Status.online:
        print(
            "Handle user going online. Message in their private room and ask to continue training."
        )
    else:
        print("Handle user going offline.")

# helper functions
async def inform_player_new_mission(interaction):
    member = interaction.user
    channel = interaction.channel
    to_send = f'Suriel acknowledges your choice {member.mention}'
    await interaction.response.send_message(to_send)

    await asyncio.sleep(1)

    to_send = 'Your path begins in 5...'
    await channel.send(to_send)
    await asyncio.sleep(500e-3)

    to_send = '4'
    await channel.send(to_send)
    await asyncio.sleep(500e-3)

    to_send = '3'
    await channel.send(to_send)
    await asyncio.sleep(500e-3)

    to_send = '2'
    await channel.send(to_send)
    await asyncio.sleep(500e-3)

    to_send = '1'
    await channel.send(to_send)
    await channel.purge(limit=6)

async def create_channel(member, **kwargs):
    overwrites = {
        member.guild.default_role:
        discord.PermissionOverwrite(read_messages=False),
        member.guild.me: discord.PermissionOverwrite(read_messages=True),
        member: discord.PermissionOverwrite(read_messages=True),
    }

    channel_name = kwargs['channel_name'] if 'channel_name'in kwargs else member.name

    return await member.guild.create_text_channel("{}".format(channel_name),
                                                  overwrites=overwrites)
async def add_new_user(member):
    users_table.create({
        "user_id": str(uuid.uuid4()),
        "discord_name": member.name,
        "discord_id": member.id,
        "role": "player"
    })


discord_client.run(os.getenv("TOKEN"))