import discord
import os
from pyairtable import Table
from discord import app_commands
from discord import Status
import random
import asyncio
import uuid
from pyairtable.formulas import match
from utils import inform_player_new_mission, create_channel, add_new_user

# setup airtable connection
airtable_api_key = os.environ["AIRTABLE_API_KEY"]
interviews_table = Table(airtable_api_key, 'app8xDpApplv8WrVJ', 'interview')
questions_table = Table(airtable_api_key, 'app8xDpApplv8WrVJ', 'questions')
users_table = Table(airtable_api_key, 'app8xDpApplv8WrVJ', 'users')
missions_table = Table(airtable_api_key, 'app8xDpApplv8WrVJ', 'missions')

async def new_command(interaction):
    player = interaction.user
    question = await utils.get_unasked_question(member)

    if not question:
        return await interaction.followup.send('Monarch Suriel has no new training for you')

    question_id = question['fields']['question_id']

    missions_table.create({
        'discord_channel_id': interaction.channel_id,
        'player_discord_id': player.id,
        'question_id': question_id,
        'status': 'design'
    })

    channel = await create_channel(member, channel_name=f'{player.mention}-{question_id}')
    leetcode_url = question['fields']['leetcode_url']
    await channel.send(f"Here's your question: {leetcode_url}")

    return await interaction.followup.send(f'Monarch Suriel has noticed {player.mention} and invites them to {channel.mention}')

async def submit_command(interaction):
    # CR hmir: only allow submit in mission channel
    # CR hmir: we probably wanna rename submit to fit the "mission"/"quest" theme
    
    return await interaction.followup.send("Handle submission")

async def delete_command(interaction):
  await interaction.channel.purge(limit=1000)
  return await interaction.followup.send('Deleted all messages')
