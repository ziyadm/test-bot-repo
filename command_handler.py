import datetime

import discord
import pyairtable.formulas

import mission
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
            # TODO: this time should depend on what stage theyre in, not just be 60
            # minutes
            time_remaining = max(
                datetime.timedelta(minutes=60) - for_mission.time_in_stage(now=UtcTime.now()),
                datetime.timedelta(seconds=0),
            )

            _ = await interaction.followup.send(f"""{time_remaining} left.""")

    async def review_command(self, interaction: discord.Interaction):
        try:
            mission_to_update = await Mission.row(
                formula=pyairtable.formulas.match(
                    {mission.Fields.review_discord_channel_id_field: str(interaction.channel.id)}
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
            if not mission_to_update.stage.in_review():
                return await interaction.followup.send("""Review already completed!""")

            review_field, review_value = await CommandHandler.get_review_value(
                mission_to_update, interaction
            )

            state_field = mission.Fields.stage_field
            state_value = mission_to_update.fields.stage.previous()

            await mission_to_update.update(
                fields=mission_to_update.fields.immutable_updates(
                    {
                        review_field: review_value,
                        state_field: state_value,
                        mission.Fields.entered_stage_time_field: UtcTime.now(),
                    }
                ),
                airtable_client=self.__state.airtable_client,
            )

            response = "Sent review followups."

            question_channel = await self.__state.discord_client.channel(
                mission_to_update.fields.discord_channel_id
            )

            player = await self.__state.discord_client.member(
                mission_to_update.fields.player_discord_id
            )

            _ = await question_channel.send(
                f"{player.mention} your work has been reviewed by Suriel\n\nSuriel's feedback: {review_value}"
            )
            _ = await interaction.followup.send(response)
