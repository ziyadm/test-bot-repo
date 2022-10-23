from airtable_client import AirtableClient
from mission import Mission
from question import Question 

import os

import discord
from pyairtable import Table
from pyairtable.formulas import match


# ================================
# === setup airtable connection ==
# ================================
airtable_api_key = os.environ['airtable_api_key']
airtable_database_id = os.environ['airtable_database_id']

# CR hmir: pull airtable client stuff into main and pass it around
airtable_client = AirtableClient(api_key = airtable_api_key,
                                 base_id = airtable_database_id)

questions_table = Table(airtable_api_key, airtable_database_id, 'questions')
users_table = Table(airtable_api_key, airtable_database_id, 'users')
missions_table = Table(airtable_api_key, airtable_database_id, 'missions')

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
    missions = await Mission.all_for_player(airtable_client = airtable_client,
                                            player_discord_id = user['fields']['discord_id'])
    return [mission.question_id for mission in missions]
  
async def get_unasked_question(member):
    questions_already_asked = await get_questions_already_asked(member)

    questions = await Question.all(airtable_client = airtable_client)

    for question in questions:
        if question.question_id not in questions_already_asked:
            return question