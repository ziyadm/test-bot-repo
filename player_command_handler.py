import datetime

import discord
import pyairtable

import mission
import user
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

        if str(interaction.channel.id) != player.fields.discord_channel_id:
            _ = await self.__state.messenger.command_cannot_be_run_here(
                where_to_follow_up=interaction.followup,
                suggested_command=SlashCommand(SlashCommand.submit),
            )
            return None

        training_mission = await self.__state.create_mission(
            player_discord_id=player_discord_id,
            channel=interaction.channel,
            where_to_follow_up=interaction.followup,
        )
        if training_mission is None:
            _ = await self.__state.messenger.player_is_out_of_questions(player=player)

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

            player = await User.row(
                formula=pyairtable.formulas.match(
                    {user.Fields.discord_id_field: mission_to_update.fields.player_discord_id}
                ),
                airtable_client=self.__state.airtable_client,
            )

            now = UtcTime.now()
            time_field = f"{mission_to_update.fields.stage}_completion_time"

            mission_updates = {
                mission.Fields.stage_field: mission_to_update.fields.stage.next(),
                mission.Fields.entered_stage_time_field: now,
                time_field: now,
            }

            stage_submitted = mission_to_update.fields.stage
            if not stage_submitted.has_value(Stage.design) and not stage_submitted.has_value(
                Stage.code
            ):
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
                channel=interaction.channel,
                where_to_follow_up=interaction.followup,
            )

            # TODO: revert all state changes if theres any exceptions

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

    async def give_up_command(self, interaction: discord.Interaction):
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
            await self.__state.give_up_mission(
                for_mission, interaction.channel, interaction.followup
            )
