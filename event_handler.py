import discord

from state import State


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
        _new_user, _user_channel = await self.state.create_user(discord_member=member)

        return None
