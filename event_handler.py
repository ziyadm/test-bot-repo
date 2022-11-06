import discord

from slash_command import SlashCommand
from state import State


class EventHandler:
    def __init__(self, state: State):
        self.__state = state

    async def on_ready(self):
        guild = discord.Object(id=self.__state.discord_client.guild_id)

        commands = await self.__state.discord_client.command_tree.fetch_commands(guild=guild)

        # TODO: fix command permissioning when syncing command tree
        for command in commands:
            slash_command_to_permission = SlashCommand.of_string(command.name)
            if slash_command_to_permission is not None and slash_command_to_permission.admin_only():
                _ = await command.edit(
                    default_member_permissions=discord.Permissions(administrator=True)
                )

        all_reviews_channel = await self.__state.discord_client.all_reviews_channel()
        _ = await all_reviews_channel.send("Running bot")

        await self.__state.discord_client.command_tree.sync(guild=guild)

        print("Running bot")

    async def on_member_join(self, member: discord.Member):
        _new_user, _user_channel = await self.__state.create_user(discord_member=member)
