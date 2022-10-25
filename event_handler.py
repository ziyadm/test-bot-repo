import user

from airtable_client import AirtableClient
from discord_client import DiscordClient
from rank import Rank
from user import User

import discord


class EventHandler:

    def __init__(self, airtable_client: AirtableClient, discord_client: DiscordClient):
        self.airtable_client = airtable_client
        self.discord_client = discord_client

    async def on_ready(self):
        # CR hmir: sync roles from ranks
        await self.discord_client.command_tree.sync(
            guild = discord.Object(id = self.discord_client.guild_id))
        print(f'Logged in as {self.discord_client.client.user}')

    async def on_member_join(self, member):
        member_id = str(member.id) 
        member_name = member.name
        rank = Rank(value = Rank.foundation)
        player_fields = user.Fields(discord_id = member_id, discord_name = member_name, rank = rank)
        player = await User.create(fields = player_fields, airtable_client = self.airtable_client)
        path_channel = await self.discord_client.create_private_channel(
            member_id,
            channel_name = f"""{member_name}-path""")
        
        await player.set_rank(
            rank,
            airtable_client = self.airtable_client,
            discord_client = self.discord_client)

        # CR hmir: make this send the full game instructions and about the roles
        return await path_channel.send(
            f"""Suriel senses your weakness {member.mention}""")