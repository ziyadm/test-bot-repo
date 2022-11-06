import discord

from state import State


class EventHandler:
    def __init__(self, state: State):
        self.__state = state

    async def on_ready(self):
        await self.__state.discord_client.command_tree.sync(
            guild=discord.Object(id=self.__state.discord_client.guild_id)
        )
        all_reviews_channel = await self.__state.discord_client.all_reviews_channel()
        _ = await all_reviews_channel.send("Running bot")
        print("Running bot")

    async def on_member_join(self, member: discord.Member):
        _new_user, _user_channel = await self.__state.create_user(discord_member=member)
