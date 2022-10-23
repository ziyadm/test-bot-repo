from airtable_client import AirtableClient
from mission import Mission
from question import Question 
from user import User

import os

import discord


# CR hmir: pull airtable client stuff into main and pass it around
airtable_client = AirtableClient(api_key = os.environ['airtable_api_key'],
                                 base_id = os.environ['airtable_database_id'])

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
    return await User.create(airtable_client = airtable_client,
                             discord_id = str(member.id),
                             discord_name = member.name)

async def get_unasked_question(member):
    user = await User.get(airtable_client = airtable_client,
                          discord_id = str(member.id))
    missions = await Mission.all_for_player(airtable_client = airtable_client,
                                            player_discord_id = user.discord_id)
    questions_already_asked = set([mission.question_id for mission in missions])
    questions = await Question.all(airtable_client = airtable_client)
    for question in questions:
        if question.question_id not in questions_already_asked:
            return question