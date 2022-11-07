import datetime

import discord
import pyairtable.formulas

import mission
from constants import Constants
from mission import Mission
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
            time_limit_minutes = Constants.STAGE_TIME_LIMIT_MINUTES
            if for_mission.fields.stage.in_review():
                time_limit_minutes = Constants.REVIEW_TIME_LIMIT_MINUTES
            elif for_mission.fields.stage.in_code():
                time_limit_minutes = Constants.CODE_TIME_LIMIT_MINUTES

            time_remaining = max(
                datetime.timedelta(minutes=time_limit_minutes)
                - for_mission.time_in_stage(now=UtcTime.now()),
                datetime.timedelta(seconds=0),
            )

            _ = await interaction.followup.send(f"""{time_remaining} left.""")
