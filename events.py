from airtable_client import AirtableClient
from rank import Rank
from user import User
import utils

import asyncio
import os

import discord

# CR hmir: pull airtable client stuff into main and pass it around
airtable_client = AirtableClient(api_key = os.environ['airtable_api_key'],
                                 base_id = os.environ['airtable_database_id'])

# when a new user joins the discord server
async def on_member_join_event(member):
    user = await User.create(airtable_client = airtable_client,
                             discord_id = str(member.id),
                             discord_name = member.name,
                             rank = Rank(value = Rank.foundation))
    
    overwrites = {
        member.guild.default_role:
        discord.PermissionOverwrite(read_messages=False),
        member.guild.me: discord.PermissionOverwrite(read_messages=True),
        member: discord.PermissionOverwrite(read_messages=True),
    }

    channel = await member.guild.create_text_channel(channel_name, overwrites=overwrites)
    # create a new channel for this new member
    new_channel = await utils.create_channel(member, channel_name="{}-home".format(member.name))

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
    if before.status == discord.Status.offline and after.status == discord.Status.online:
        print(
            "Handle user going online. Message in their private room and ask to continue training."
        )
    else:
        print("Handle user going offline.")
      
