from rank import Rank
from state import State

import discord


class EventHandler:
    def __init__(self, state: State):
        self.state = state

    async def on_ready(self):
        # TODO prointerviewschool: sync roles from ranks
        await self.state.discord_client.command_tree.sync(
            guild=discord.Object(id=self.state.discord_client.guild_id)
        )
        print(f"Logged in as {self.state.discord_client.client.user}")

    async def on_member_join(self, member: discord.Member):
        _, user_channel = await self.state.create_user(
            discord_id=str(member.id),
            discord_name=member.name,
            rank=Rank(value=Rank.foundation),
        )

        # TODO prointerviewschool: make this send the full game instructions and about the roles
        await user_channel.send(f"""Suriel senses your weakness {member.mention}""")

        return None
