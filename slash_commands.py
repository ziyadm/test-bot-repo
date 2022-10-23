from airtable_client import AirtableClient
from mission import Mission
from mission_status import MissionStatus
import utils

import os

import discord
from pyairtable import Table


airtable_client = AirtableClient(api_key = os.environ['airtable_api_key'],
                                 base_id = os.environ['airtable_database_id'])

missions_table = Table(os.environ['airtable_api_key'],
                       os.environ['airtable_database_id'],
                       'missions')

async def new_command(interaction):
    player = interaction.user
    question = await utils.get_unasked_question(player)

    if not question:
        return await interaction.followup.send('Monarch Suriel has no new training for you')

    question_id = question['fields']['question_id']

    missions_table.create({
        'discord_channel_id': str(interaction.channel_id),
        'player_discord_id': str(player.id),
        'question_id': question_id,
        'status': 'design'
    })

    channel = await utils.create_channel(player, channel_name=f'{player.name}-{question_id}')
    leetcode_url = question['fields']['leetcode_url']
    await channel.send(f"Here's your question: {leetcode_url}")

    return await interaction.followup.send(f'Monarch Suriel has noticed {player.mention} and invites them to {channel.mention}')

async def submit_command(interaction):
    # CR hmir: only allow submit in mission channel
    # CR hmir: we probably wanna rename submit to fit the "mission"/"quest" theme
    mission = await Mission.get_one(airtable_client = airtable_client,
                                    discord_channel_id = str(interaction.channel_id))

    if not (mission.mission_status.is_design() or
            mission.mission_status.is_code()):
                # CR hmir: update text
                return await interaction.followup.send('Your mission depends on your teammates, wait for them!')

    channel = interaction.channel
    
    messages = [message async for message in channel.history() if message.type == discord.MessageType.default]
    if len(messages) == 0:
        # CR hmir: maybe we can frame missions as you having "minions" who you have to give instructions to to solve some problems you come across in your journey? follow up with ziyad
        return await interaction.followup.send('You need to instruct your minions!')

    last_message = messages[0].content
    print(last_message)
    
    return await interaction.followup.send("Handle submission")

async def delete_command(interaction):
  await interaction.channel.purge(limit=1000)
  return await interaction.followup.send('Deleted all messages')
