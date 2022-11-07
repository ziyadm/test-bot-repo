import discord
import pyairtable

import mission
import user
from constants import Constants
from mission import Mission
from slash_command import SlashCommand
from stage import Stage
from state import State
from user import User
from utc_time import UtcTime


class PlayerCommandHandler:
    def __init__(self, *, state: State):
        self.__state = state

    async def train_command(self, interaction: discord.Interaction):
        player_discord_id = str(interaction.user.id)
        player = await User.row(
            formula=pyairtable.formulas.match({user.Fields.discord_id_field: player_discord_id}),
            airtable_client=self.__state.airtable_client,
        )

        path_channel = await self.__state.discord_client.channel(
            channel_id=player.fields.discord_channel_id
        )
        if str(interaction.channel.id) != player.fields.discord_channel_id:
            _ = await self.__state.messenger.command_cannot_be_run_here(
                where_to_follow_up=interaction.followup,
                expected_location=path_channel,
                suggested_command=SlashCommand(SlashCommand.submit),
            )
            return None

        training_mission_and_channel = await self.__state.create_mission(
            player_discord_id=player_discord_id
        )
        if training_mission_and_channel is None:
            _ = await self.__state.messenger.player_is_out_of_questions(player=player)

        _ = await interaction.followup.send(Constants.COMMAND_ACKNOWLEDGED_BY_SURIEL)

    async def submit_command(self, interaction: discord.Interaction):
        mission_discord_channel_id = str(interaction.channel.id)
        try:
            mission_to_update = await Mission.row(
                formula=pyairtable.formulas.match(
                    {mission.Fields.discord_channel_id_field: mission_discord_channel_id}
                ),
                airtable_client=self.__state.airtable_client,
            )
        except Exception:
            _ = await self.__state.messenger.command_cannot_be_run_here(
                where_to_follow_up=interaction.followup,
                expected_location=None,
                suggested_command=SlashCommand(SlashCommand.train),
            )
            return None
        else:
            if not (mission_to_update.fields.stage.players_turn()):
                await interaction.followup.send(
                    """You've completed your objective, wait for Monarch Suriel's instructions!"""
                )
                return None

            mission_channel_messages = await self.__state.discord_client.messages(
                channel_id=mission_discord_channel_id
            )
            if len(mission_channel_messages) == 0:
                return await interaction.followup.send(
                    "Send your work as a message before running this command"
                )

            player = await User.row(
                formula=pyairtable.formulas.match(
                    {user.Fields.discord_id_field: mission_to_update.fields.player_discord_id}
                ),
                airtable_client=self.__state.airtable_client,
            )

            now = UtcTime.now()

            mission_updates = {
                mission.Fields.stage_field: mission_to_update.fields.stage.next(),
                mission.Fields.entered_stage_time_field: now,
            }

            stage_submitted = mission_to_update.fields.stage

            if stage_submitted.has_value(Stage.design):
                mission_updates[mission.Fields.design_field] = mission_channel_messages[0].content
            elif stage_submitted.has_value(Stage.code):
                mission_updates[mission.Fields.code_field] = mission_channel_messages[0].content
            else:
                raise Exception(
                    f"""player attempted to submit a mission in review or completed (stage: {stage_submitted}), but we already filtered for this. is this a bug?"""
                )

            updated_mission = await mission_to_update.update(
                fields=mission_to_update.fields.immutable_updates(mission_updates),
                airtable_client=self.__state.airtable_client,
            )

            _ = await self.__state.messenger.player_submitted_stage(
                player,
                updated_mission,
                stage_submitted,
                time_taken=mission_to_update.time_in_stage(now),
            )

            # TODO: revert all state changes if theres any exceptions
            _ = await interaction.followup.send(Constants.COMMAND_ACKNOWLEDGED_BY_SURIEL)
