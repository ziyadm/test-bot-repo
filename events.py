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


# when a new user joins the discord server
async def on_member_join_event(member):
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
async def on_presence_update_event(before, after):
    if before.status == Status.offline and after.status == Status.online:
        print(
            "Handle user going online. Message in their private room and ask to continue training."
        )
    else:
        print("Handle user going offline.")
      
