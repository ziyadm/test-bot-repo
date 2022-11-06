import discord
import pyairtable

import mission
import user
from messenger import Messenger
from mission import Mission
from stage import Stage
from state import State
from user import User
from utc_time import UtcTime


class PlayerCommandHandler:
    def __init__(self, *, state: State):
        self.messenger = Messenger(discord_client=state.discord_client)
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

    async def submit_command(self, interaction: discord.Interaction):
        mission_discord_channel_id = str(interaction.channel.id)
        mission_to_update = await Mission.row(
            formula=pyairtable.formulas.match(
                {mission.Fields.discord_channel_id_field: mission_discord_channel_id}
            ),
            airtable_client=self.__state.airtable_client,
        )

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
                "Send your work as a message before running `/submit`"
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

        _ = await self.messenger.player_submitted_stage(
            player,
            updated_mission,
            stage_submitted,
            time_taken=mission_to_update.time_in_stage(now),
        )

        # TODO: revert all state changes if theres any exceptions
        _ = await interaction.followup.send("Finished")
