import discord
import os
from pyairtable import Table
from discord import app_commands
from discord import Status
import random
import asyncio
import uuid
from pyairtable.formulas import match

# ================================
# === setup airtable connection ==
# ================================
airtable_api_key = os.environ["AIRTABLE_API_KEY"]
interviews_table = Table(airtable_api_key, 'app8xDpApplv8WrVJ', 'interview')
questions_table = Table(airtable_api_key, 'app8xDpApplv8WrVJ', 'questions')
users_table = Table(airtable_api_key, 'app8xDpApplv8WrVJ', 'users')
missions_table = Table(airtable_api_key, 'app8xDpApplv8WrVJ', 'missions')

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