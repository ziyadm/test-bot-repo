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
        guild = discord.Object(id = self.discord_client.guild_id)
        await self.discord_client.command_tree.sync(guild = guild)
        print(f'Logged in as {self.discord_client.client.user}')

    async def on_member_join(self, member):
        await User.create(airtable_client = self.airtable_client,
                          discord_id = str(member.id),
                          discord_name = member.name,
                          rank = Rank(value = Rank.foundation))
        path_channel = await self.discord_client.create_path_channel(member)
        return await path_channel.send(f'Suriel senses your weakness {member.mention}')