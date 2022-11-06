import discord

from state import State


class PlayerCommandHandler:
    def __init__(self, *, state: State):
        self.__state = state

    async def train_command(self, interaction: discord.Interaction):
        # create the mission
        mission_to_update, mission_channel = await self.__state.create_mission(
            player_discord_id=str(interaction.user.id)
        )
        mission_message = await interaction.followup.send(
            f"""Monarch Suriel has invited you to {mission_channel.mention}"""
        )
        mission_message.guild = self.__state.discord_client.guild_id

        # create the summary thread
        _ = await mission_message.create_thread(
            name=f"summary-{mission_to_update.fields.question_id}"
        )
