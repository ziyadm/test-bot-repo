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

async def create_channel(member, **kwargs):
    overwrites = {
        member.guild.default_role:
        discord.PermissionOverwrite(read_messages=False),
        member.guild.me: discord.PermissionOverwrite(read_messages=True),
        member: discord.PermissionOverwrite(read_messages=True),
    }

    channel_name = kwargs['channel_name'] if 'channel_name'in kwargs else member.name
    return await member.guild.create_text_channel(channel_name, overwrites=overwrites)

async def add_new_user(member):
    users_table.create({
        'discord_id': str(member.id),
        'discord_name': member.name
    })

async def get_questions_already_asked(member):
    user = users_table.first(formula=match({'discord_id': member.id}))
    missions = missions_table.all(formula=match({"player_discord_id": user['fields']['discord_id']}))
    return [mission['fields']['question_id'] for mission in missions]
  
async def get_unasked_question(member):
    questions_already_asked = await get_questions_already_asked(member)

    # pick a random new question not previously seen
    for question in questions_table.all():
        if question['fields']['question_id'] not in questions_already_asked:
            return question
