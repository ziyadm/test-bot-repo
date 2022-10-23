from airtable_client import AirtableClient
from mission import Mission
from mission_status import MissionStatus
import utils

import os

import discord


airtable_client = AirtableClient(api_key = os.environ['airtable_api_key'],
                                 base_id = os.environ['airtable_database_id'])

async def new_command(interaction):
    player = interaction.user
    question = await utils.get_unasked_question(player)

    if not question:
        return await interaction.followup.send('Monarch Suriel has no new training for you')

    channel = await utils.create_channel(player, channel_name=f'{player.name}-{question.question_id}')

    await Mission.create(airtable_client = airtable_client,
                         discord_channel_id = str(channel.id),
                         player_discord_id = str(player.id),
                         reviewer_discord_id = None,
                         question_id = question.question_id,
                         mission_status = MissionStatus.design(),
                         design = None,
                         code = None)

    await channel.send(f"""Here's your question: {question.leetcode_url}""")

    return await interaction.followup.send(f'Monarch Suriel has noticed {player.mention} and invites them to {channel.mention}')

async def submit_command(interaction):
    # CR hmir: only allow submit in mission channel
    # CR hmir: we probably wanna rename submit to fit the "mission"/"quest" theme
    mission = await Mission.get(airtable_client = airtable_client,
                                discord_channel_id = str(interaction.channel_id))

    if not (mission.mission_status.is_design() or
            mission.mission_status.is_code()):
                return await interaction.followup.send("""You've completed your objective, wait for Monarch Suriel's instructions!""")

    channel = interaction.channel
    
    messages = [message async for message in channel.history() if message.type == discord.MessageType.default]
    if len(messages) == 0:
        # CR hmir: maybe we can frame missions as you having "minions" who you have to give instructions to to solve some problems you come across in your journey?
        # alternatively it could be framed as being a world of machines and you need to make the machines do what you want. i think theres a pretty popular recent game thats similar to this
        # follow up with ziyad
        return await interaction.followup.send('You need to instruct your minions!')

    if mission.mission_status.is_design():
        await Mission.update(airtable_client = airtable_client,
                             record_id = mission.record_id,
                             design = messages[0].content,
                             mission_status = MissionStatus.design_review())
        return await interaction.followup.send("""Planning is half the battle! We've sent your plan to Monarch Suriel for approval. Check back in about 30 minutes to find out your next objective.""")
    else:
        await Mission.update(airtable_client = airtable_client,
                             record_id = mission.record_id,
                             code = messages[0].content,
                             mission_status = MissionStatus.code_review())
        return await interaction.followup.send("""Monarch Suriel will be pleased! We've sent your instructions to Him for approval. Once they're approved, they'll be sent directly to your minions on the frontlines!""")
        

async def delete_command(interaction):
  await interaction.channel.purge(limit=1000)
  return await interaction.followup.send('Deleted all messages')
