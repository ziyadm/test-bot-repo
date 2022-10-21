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

    to_send = f'Monarch Suriel has noticed {member.mention} and invites them to {question_channel.mention}'
    return await interaction.followup.send(to_send)

async def submit_command(interaction):
    return await interaction.followup.send("Handle submission")

async def delete_command(interaction):
  await interaction.channel.purge(limit=1000)
  return await interaction.followup.send('Deleted all messages')
