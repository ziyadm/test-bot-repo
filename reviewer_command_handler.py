import discord
import pyairtable

import mission
import question
import user
from mission import Mission
from question import Question
from stage import Stage
from state import State
from user import User
from utc_time import UtcTime


class ReviewerCommandHandler:
    def __init__(self, *, state: State):
        self.__state = state

    async def claim_command(self, interaction: discord.Interaction):
        try:
            # TODO: store thread id in mission row so we can look up by it
            question_discord_channel_id = str(interaction.channel.name.split("-")[1])
            mission_to_update = await Mission.row(
                formula=pyairtable.formulas.match(
                    {mission.Fields.discord_channel_id_field: question_discord_channel_id}
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
            if not mission_to_update.fields.stage.in_review():
                return await interaction.followup.send("""Review already claimed!""")

            user_to_update = await User.row(
                formula=pyairtable.formulas.match(
                    {user.Fields.discord_id_field: mission_to_update.fields.player_discord_id}
                ),
                airtable_client=self.__state.airtable_client,
            )

            question_to_update = await Question.row(
                formula=pyairtable.formulas.match(
                    {question.Fields.question_id_field: mission_to_update.fields.question_id}
                ),
                airtable_client=self.__state.airtable_client,
            )

            question_review_channel = await self.__state.discord_client.create_private_channel(
                interaction.user.id,
                f"{mission_to_update.fields.stage}-{mission_to_update.fields.question_id}-{user_to_update.fields.discord_name}",
            )

            await mission_to_update.update(
                fields=mission_to_update.fields.immutable_updates(
                    {
                        mission.Fields.review_discord_channel_id_field: str(
                            question_review_channel.id
                        ),
                        mission.Fields.reviewer_discord_id_field: interaction.user.id,
                    }
                ),
                airtable_client=self.__state.airtable_client,
            )

            await self.__state.messenger.review_was_claimed(
                mission_to_update, question_to_update, question_review_channel, interaction.channel
            )
            return await interaction.followup.send("Finished")

    async def approve_command(self, interaction: discord.Interaction, score: float):
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
            if not mission_to_update.fields.stage.in_review():
                return await interaction.followup.send("""Approval already provided!""")

            # 1) update mission to reflect review values/scores
            review_field, review_value = await ReviewerCommandHandler.get_review_value(
                mission_to_update, interaction
            )

            state_field = mission.Fields.stage_field
            state_value = mission_to_update.fields.stage.next()

            score_field = (
                mission.Fields.code_score_field
                if mission_to_update.fields.stage.in_code()
                else mission.Fields.design_score_field
            )

            updated_mission = await mission_to_update.update(
                fields=mission_to_update.fields.immutable_updates(
                    {
                        review_field: review_value,
                        state_field: state_value,
                        score_field: score,
                        mission.Fields.entered_stage_time_field: UtcTime.now(),
                        mission.Fields.review_discord_channel_id_field: "",
                        mission.Fields.reviewer_discord_id_field: "",
                    }
                ),
                airtable_client=self.__state.airtable_client,
            )

            # 2) tell the player about the review values/scores
            question_channel = await self.__state.discord_client.channel(
                updated_mission.fields.discord_channel_id
            )

            await self.__state.messenger.mission_approved(
                updated_mission, question_channel, interaction.channel, review_value, score
            )

            # 3) update the summary thread
            # note: when updating the summary thread for the stage
            # we want the previous (not newly updated) mission
            user_to_update = await User.row(
                formula=pyairtable.formulas.match(
                    {user.Fields.discord_id_field: mission_to_update.fields.player_discord_id}
                ),
                airtable_client=self.__state.airtable_client,
            )
            await self.__state.messenger.update_summary_thread(
                mission_to_update, user_to_update, review_value=review_value, score=score
            )

            # 4) tell player about level changes
            if updated_mission.fields.stage.has_value(Stage.completed):
                (
                    new_level,
                    level_delta,
                    levels_until_evolution,
                    evolving,
                    current_rank,
                ) = await self.__state.get_level_changes(updated_mission)

                # TODO talk to hani about how to handle setting rank here
                # is just nicer to evolve them immediately after sending the message
                # instead of before
                await self.__state.messenger.player_completed_stage(
                    user_to_update,
                    question_channel,
                    self.__state.set_rank,
                    evolving=evolving,
                    current_rank=current_rank,
                    level_delta=level_delta,
                    new_level=new_level,
                    levels_until_evolution=levels_until_evolution,
                )

                # update summary thread about clearing the stage thread
                await self.__state.messenger.update_summary_thread(
                    updated_mission,
                    user_to_update,
                    evolving=evolving,
                    level_delta=level_delta,
                    levels_until_evolution=levels_until_evolution,
                    new_level=new_level,
                )

            return await interaction.followup.send("Finished")

    async def reject_command(self, interaction: discord.Interaction):
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
            if not mission_to_update.fields.stage.in_review():
                return await interaction.followup.send("""Review already completed!""")

            review_field, review_value = await ReviewerCommandHandler.get_review_value(
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

            question_channel = await self.__state.discord_client.channel(
                mission_to_update.fields.discord_channel_id
            )

            player = await self.__state.discord_client.member(
                mission_to_update.fields.player_discord_id
            )

            await self.__state.messenger.mission_rejected(
                player, question_channel, interaction.followup, review_value
            )

    @staticmethod
    async def get_review_value(
        mission_to_update: mission.Mission, interaction: discord.Interaction
    ):
        review_field = (
            mission.Fields.design_review_field
            if mission_to_update.fields.stage.has_value(Stage.design_review)
            else mission.Fields.code_review_field
        )
        messages = [
            message
            async for message in interaction.channel.history()
            if message.type == discord.MessageType.default
        ]
        review_value = messages[0].content
        return review_field, review_value
