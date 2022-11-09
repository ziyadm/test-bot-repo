import datetime

import discord
import pyairtable.formulas

import mission
from mission import Mission
from stage import Stage
from state import State
from utc_time import UtcTime


class CommandHandler:
    def __init__(self, state: State):
        self.__state = state

    async def time_command(self, interaction: discord.Interaction):
        try:
            for_mission = await Mission.row(
                formula=pyairtable.formulas.match(
                    {mission.Fields.discord_channel_id_field: str(interaction.channel.id)}
                ),
                airtable_client=self.__state.airtable_client,
            )
        except Exception:
            _ = await self.__state.messenger.command_cannot_be_run_here(
                where_to_follow_up=interaction.followup,
                expected_location=None,
                suggested_command=None,
            )
            return None
        else:
            if not for_mission.fields.stage.players_turn():
                guild_owner = await self.__state.discord_client.guild_owner()
                _ = await interaction.followup.send(
                    f"""You've done everything you can so far, wait for further instructions from {guild_owner.display_name}!"""
                )
                return None

            if for_mission.fields.stage.has_value(Stage.design):
                time_limit = self.__state.design_time_limit
            else:
                time_limit = self.__state.code_time_limit

            time_remaining = max(
                time_limit - for_mission.time_in_stage(now=UtcTime.now()),
                datetime.timedelta(seconds=0),
            )

            _ = await interaction.followup.send(f"""{time_remaining} left.""")
