import datetime
from typing import List

import discord
import pyairtable.formulas

import mission
import question
import user
from airtable_client import AirtableClient
from messenger import Messenger
from mission import Mission
from question import Question
from rank import Rank
from stage import Stage
from state import State
from user import User
from utc_time import UtcTime


class CommandHandler:
    def __init__(self, state: State):
        self.messenger = Messenger(discord_client=state.discord_client)
        self.state = state

    async def get_mission(self, field: mission.Fields, value: str):
        return await Mission.row(
            formula=pyairtable.formulas.match({field: value}),
            airtable_client=self.state.airtable_client,
        )

    async def update_summary_thread(self, mission_to_update, **kwargs):
        user_to_update = await User.row(
            formula=pyairtable.formulas.match(
                {
                    user.Fields.discord_id_field: mission_to_update.fields.player_discord_id
                }
            ),
            airtable_client=self.state.airtable_client,
        )
        user_path_channel = await self.state.discord_client.channel(
            user_to_update.fields.discord_channel_id
        )
        thread = list(
            filter(
                lambda thread: thread.name
                == f"summary-{mission_to_update.fields.question_id}",
                user_path_channel.threads,
            )
        )[0]
        # TODO: im pretty sure we want the updated missions time, not the copy
        # of the mission before we wrote the updates to the db. dont have time
        # to verify / fix this right now
        time_taken_to_complete_stage = mission_to_update.time_in_stage(
            now=UtcTime.now()
        )

        level_delta = kwargs.get("level_delta", None)
        levels_until_evolution = kwargs.get("levels_until_evolution", None)
        new_level = kwargs.get("new_level", None)
        evolving = kwargs.get("evolving", None)
        review_value = kwargs.get("review_value", None)
        score = kwargs.get("score", None)

        def get_completed_message():
            return f"""
Stage cleared.\n
Total time for stage: `{time_taken_to_complete_stage}`\n
Levels gained: `{level_delta}`\n
Current level: `{new_level}`\n
Evolved?: `{evolving}`\n
Levels until evolution: `{levels_until_evolution}`\n
        """

        def get_in_progress_message():
            return f"""
Suriel approved your `{mission_to_update.fields.stage.previous()}`.\n
Total time: `{time_taken_to_complete_stage}`\n
Suriel's feedback: `{review_value}`\n
Score: `{score}`
        """

        message = (
            get_completed_message()
            if CommandHandler.completing(mission_to_update)
            else get_in_progress_message()
        )
        await thread.send(message)

    async def time_command(self, interaction: discord.Interaction):
        for_mission = await self.get_mission(
            field=mission.Fields.discord_channel_id_field,
            value=str(interaction.channel.id),
        )
        # TODO: this time should depend on what stage theyre in, not just be 60
        # minutes
        time_remaining = max(
            datetime.timedelta(minutes=60)
            - for_mission.time_in_stage(now=UtcTime.now()),
            datetime.timedelta(seconds=0),
        )

        await interaction.followup.send(f"""{time_remaining} left.""")

    async def train_command(self, interaction: discord.Interaction):
        mission_to_update, mission_channel = await self.state.create_mission(
            player_discord_id=str(interaction.user.id)
        )

        mission_question = await Question.row(
            formula=pyairtable.formulas.match(
                {
                    question.Fields.question_id_field: mission_to_update.fields.question_id
                }
            ),
            airtable_client=self.state.airtable_client,
        )

        mission_message = await interaction.followup.send(
            f"""Monarch Suriel has invited you to {mission_channel.mention}"""
        )
        mission_message.guild = self.state.discord_client.guild_id

        # create the summary thread
        discord_user = await self.state.discord_client.member(str(interaction.user.id))
        _ = await mission_message.create_thread(
            name=f"summary-{mission_question.fields.question_id}"
        )

    async def review_command(self, interaction: discord.Interaction):
        mission_to_update = await self.get_mission(
            field=mission.Fields.review_discord_channel_id_field,
            value=str(interaction.channel_id),
        )

        if not CommandHandler.in_review(mission_to_update):
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
                }
            ),
            airtable_client=self.state.airtable_client,
        )

        response = "Sent review followups."

        question_channel = await self.state.discord_client.channel(
            mission_to_update.fields.discord_channel_id
        )

        user = await self.state.discord_client.member(
            mission_to_update.fields.player_discord_id
        )

        await question_channel.send(
            f"{user.mention} your work has been reviewed by Suriel\n\nSuriel's feedback: {review_value}"
        )
        return await interaction.followup.send(response)

    async def lgtm_command(self, interaction: discord.Interaction, score: float):
        mission_to_update = await self.get_mission(
            field=mission.Fields.review_discord_channel_id_field,
            value=str(interaction.channel_id),
        )

        if not CommandHandler.in_review(mission_to_update):
            return await interaction.followup.send("""LGTM already provided!""")

        review_field, review_value = await CommandHandler.get_review_value(
            mission_to_update, interaction
        )

        state_field = mission.Fields.stage_field
        state_value = mission_to_update.fields.stage.next()

        score_field = (
            mission.Fields.code_score_field
            if CommandHandler.completing(mission_to_update)
            else mission.Fields.design_score_field
        )

        await mission_to_update.update(
            fields=mission_to_update.fields.immutable_updates(
                {
                    review_field: review_value,
                    state_field: state_value,
                    score_field: score,
                    mission.Fields.review_discord_channel_id_field: "",
                    mission.Fields.reviewer_discord_id_field: "",
                }
            ),
            airtable_client=self.state.airtable_client,
        )

        response = (
            "Approved question."
            if CommandHandler.completing(mission_to_update)
            else "Approved design."
        )

        question_channel = await self.state.discord_client.channel(
            mission_to_update.fields.discord_channel_id
        )

        base_response_to_user = (
            "Suriel approved of your work! Suriel left you the following to help you along your path"
            if CommandHandler.completing(mission_to_update)
            else "Suriel approved your design. Continue along to coding."
        )
        response_to_user = (
            f"{base_response_to_user} \n Feedback: {review_value} \n Score: {score}"
        )

        # message user
        await question_channel.send(response_to_user)

        if CommandHandler.completing(mission_to_update):
            await self.handle_completing_question(mission_to_update, question_channel)
        else:
            # update thread
            await self.update_summary_thread(
                mission_to_update, review_value=review_value, score=score
            )

        return await interaction.followup.send(response)

    async def handle_completing_question(
        self, mission_to_update: mission.Mission, question_channel: discord.TextChannel
    ):
        (
            new_level,
            level_delta,
            levels_until_evolution,
            evolving,
            current_rank,
        ) = await CommandHandler.get_level_changes(
            self.state.airtable_client, mission_to_update
        )

        await question_channel.send(
            f"Your work has been recognized by Suriel.\n\nYou gained {level_delta} levels!\n\n"
        )

        if evolving:
            user_to_update = await User.row(
                formula=pyairtable.formulas.match(
                    {
                        user.Fields.discord_id_field: mission_to_update.fields.player_discord_id
                    }
                ),
                airtable_client=self.state.airtable_client,
            )

            await question_channel.send("Wait...what's happening?")
            await question_channel.send("Suriel is slightly impressed...")
            await question_channel.send("You are...EVOLVING!")
            await self.state.set_rank(for_user=user_to_update, rank=current_rank)
            await question_channel.send(
                "Suriel sees your strength - you have advanced to the next rank."
            )

        await question_channel.send(
            f"You are now a [{current_rank.capitalize()} lvl {new_level}].\n\nYou are now only {levels_until_evolution} levels from advancing to the next rank!"
        )

        # update thread
        await self.update_summary_thread(
            mission_to_update,
            evolving=evolving,
            level_delta=level_delta,
            levels_until_evolution=levels_until_evolution,
            new_level=new_level,
        )

    async def claim_command(self, interaction: discord.Interaction):
        question_discord_channel_id = str(interaction.channel.name.split("-")[1])
        mission_to_update = await self.get_mission(
            field=mission.Fields.discord_channel_id_field,
            value=question_discord_channel_id,
        )

        mission_to_update = await Mission.row(
            formula=pyairtable.formulas.match(
                {mission.Fields.discord_channel_id_field: question_discord_channel_id}
            ),
            airtable_client=self.state.airtable_client,
        )

        if not CommandHandler.in_review(mission_to_update):
            return await interaction.followup.send("""Review already claimed!""")

        user_to_update = await User.row(
            formula=pyairtable.formulas.match(
                {
                    user.Fields.discord_id_field: mission_to_update.fields.player_discord_id
                }
            ),
            airtable_client=self.state.airtable_client,
        )

        question_to_update = await Question.row(
            formula=pyairtable.formulas.match(
                {
                    question.Fields.question_id_field: mission_to_update.fields.question_id
                }
            ),
            airtable_client=self.state.airtable_client,
        )

        question_review_channel = await self.state.discord_client.create_private_channel(
            interaction.user.id,
            f"{mission_to_update.fields.stage.get_field()}-{mission_to_update.fields.question_id}-{user_to_update.fields.discord_name}",
        )
        design_stage = mission_to_update.fields.stage.has_value(
            Stage.design_review
        ) or mission_to_update.fields.stage.has_value(Stage.design)
        content_value = (
            mission_to_update.fields.design
            if design_stage
            else mission_to_update.fields.code
        )

        await question_review_channel.send(
            f"Question: {question_to_update.fields.leetcode_url}\n\nContent: {content_value}"
        )
        response = f"Review claimed: {question_review_channel.mention}"

        await mission_to_update.update(
            fields=mission_to_update.fields.immutable_updates(
                {
                    mission.Fields.review_discord_channel_id_field: str(
                        question_review_channel.id
                    ),
                    mission.Fields.reviewer_discord_id_field: interaction.user.id,
                }
            ),
            airtable_client=self.state.airtable_client,
        )

        return await interaction.followup.send(response)

    async def submit_command(self, interaction: discord.Interaction):
        mission_discord_channel_id = str(interaction.channel.id)
        mission_to_update = await self.get_mission(
            field=mission.Fields.discord_channel_id_field,
            value=mission_discord_channel_id,
        )

        if not (mission_to_update.fields.stage.players_turn()):
            await interaction.followup.send(
                """You've completed your objective, wait for Monarch Suriel's instructions!"""
            )
            return None

        mission_channel_messages = await self.state.discord_client.messages(
            channel_id=mission_discord_channel_id
        )
        if len(mission_channel_messages) == 0:
            return await interaction.followup.send(
                "Send your work as a message before running `/submit`"
            )

        player = await User.row(
            formula=pyairtable.formulas.match(
                {
                    user.Fields.discord_id_field: mission_to_update.fields.player_discord_id
                }
            ),
            airtable_client=self.state.airtable_client,
        )

        now = UtcTime.now()

        mission_updates = {
            mission.Fields.stage_field: mission_to_update.fields.stage.next(),
            mission.Fields.entered_stage_time_field: now,
        }

        stage_submitted = mission_to_update.fields.stage

        if stage_submitted.has_value(Stage.design):
            mission_updates[mission.Fields.design_field] = mission_channel_messages[
                0
            ].content
        elif stage_submitted.has_value(Stage.code):
            mission_updates[mission.Fields.code_field] = mission_channel_messages[
                0
            ].content
        else:
            raise Exception(
                f"""player attempted to submit a mission in review or completed (stage: {stage_submitted}), but we already filtered for this. is this a bug?"""
            )

        updated_mission = await mission_to_update.update(
            fields=mission_to_update.fields.immutable_updates(mission_updates),
            airtable_client=self.state.airtable_client,
        )

        _ = await self.messenger.player_submitted_stage(
            player,
            updated_mission,
            stage_submitted,
            time_taken=mission_to_update.time_in_stage(now),
        )

        # TODO: revert all state changes if theres any exceptions
        _ = await interaction.followup.send("Finished")

    async def set_rank(
        self, interaction: discord.Interaction, user_discord_name: str, rank: str
    ):
        user_to_update = await User.row(
            formula=pyairtable.formulas.match(
                {user.Fields.discord_name_field: user_discord_name}
            ),
            airtable_client=self.state.airtable_client,
        )

        await self.state.set_rank(for_user=user_to_update, rank=Rank.of_string(rank))

        return await interaction.followup.send(
            f"""Updated {user_discord_name}'s rank to {rank}"""
        )

    @staticmethod
    def completing(mission_to_update: mission.Mission):
        return mission_to_update.fields.stage.next().has_value(Stage.completed)

    @staticmethod
    def in_review(mission_to_update: mission.Mission):
        return mission_to_update.fields.stage.has_value(
            Stage.design_review
        ) or mission_to_update.fields.stage.has_value(Stage.code_review)

    @staticmethod
    async def get_level_changes(
        airtable_client: AirtableClient, mission_to_update: mission.Mission
    ):
        # steps:
        # - find previously completed missions
        # - we combine scores of the previous HOW_MANY_PREVIOUS_QUESTIONS_TO_SCORE completed missions
        #   to calculate a users level/rank
        # - if the user hasn't completed enough missions, we just add all scores up to get their level
        # - we calculate the score_delta (current level using newest mission - previous level not including
        #   current mission
        completed_missions = await mission_to_update.rows(
            formula=pyairtable.formulas.match(
                {
                    mission.Fields.player_discord_id_field: mission_to_update.fields.player_discord_id,
                    mission.Fields.stage_field: mission_to_update.fields.stage.next().get_field(),
                }
            ),
            airtable_client=airtable_client,
        )
        completed_missions.sort(key=lambda mission: mission.fields.entered_stage_time)

        # filter to just the scores from missions
        scores_from_completed_missions = list(
            map(
                lambda question: (
                    question.fields.design_score,
                    question.fields.code_score,
                ),
                completed_missions,
            )
        )
        not_enough_scores = (
            len(scores_from_completed_missions)
            < Mission.HOW_MANY_PREVIOUS_QUESTIONS_TO_SCORE
        )

        # calculate the existing level for the user
        previous_scores = (
            scores_from_completed_missions[:-1]
            if not_enough_scores
            else scores_from_completed_missions[
                -(Mission.HOW_MANY_PREVIOUS_QUESTIONS_TO_SCORE - 1) : -1
            ]
        )
        previous_level = int(CommandHandler.calculate_level(previous_scores))

        current_scores = [scores_from_completed_missions[-1]]
        current_level = None

        # calculate the new level for the user
        if not_enough_scores:
            current_level = int(
                CommandHandler.calculate_level(previous_scores + current_scores)
            )
        else:
            current_level = int(
                CommandHandler.calculate_level(previous_scores[1:] + current_scores)
            )

        # calculate what the level delta (what is the current level - previous level of the user)
        # players can't lose levels, so de-evolutions shouldn't be a problem
        level_delta = max(current_level - previous_level, 0)
        levels_until_evolution = ((int(current_level / 10) + 1) * 10) - current_level

        # fetch ranks and see if this user is evolving
        user_to_update = await User.row(
            formula=pyairtable.formulas.match(
                {
                    user.Fields.discord_id_field: mission_to_update.fields.player_discord_id
                }
            ),
            airtable_client=airtable_client,
        )
        previous_rank = user_to_update.fields.rank.get_rank_for_level(previous_level)
        current_rank = user_to_update.fields.rank.get_rank_for_level(current_level)
        evolving = True if previous_rank != current_rank else False

        return (
            current_level,
            level_delta,
            levels_until_evolution,
            evolving,
            current_rank,
        )

    @staticmethod
    def calculate_level(scores):
        aggregate_score = 0.0

        for score in scores:
            aggregate_score += score[0]
            aggregate_score += score[1]

        return aggregate_score

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
