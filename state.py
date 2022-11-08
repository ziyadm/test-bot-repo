import datetime
from typing import FrozenSet, List

import discord
import pyairtable.formulas

import mission
import user
from airtable_client import AirtableClient
from constants import Constants
from discord_client import DiscordClient
from messenger import Messenger
from mission import Mission
from question import Question
from rank import Rank
from stage import Stage
from user import User
from utc_time import UtcTime


class State:
    def __init__(self, airtable_client: AirtableClient, discord_client: DiscordClient):
        self.airtable_client = airtable_client
        self.discord_client = discord_client
        self.messenger = Messenger(discord_client=discord_client)

    async def first_unasked_question(self, for_user: User):
        existing_missions = await Mission.rows(
            formula=pyairtable.formulas.match(
                {mission.Fields.player_discord_id_field: for_user.fields.discord_id}
            ),
            airtable_client=self.airtable_client,
        )

        questions_already_asked = set(
            [existing_mission.fields.question_id for existing_mission in existing_missions]
        )

        questions = await Question.rows(formula=None, airtable_client=self.airtable_client)

        for question in questions:
            if question.fields.question_id not in questions_already_asked:
                return question

        return None

    async def create_mission(self, player_discord_id: str):
        player = await User.row(
            formula=pyairtable.formulas.match({user.Fields.discord_id_field: player_discord_id}),
            airtable_client=self.airtable_client,
        )

        mission_question = await self.first_unasked_question(player)
        if not mission_question:
            return None

        question_id = mission_question.fields.question_id
        mission_channel = await self.discord_client.create_private_channel(
            member_id=player_discord_id,
            channel_name=f"""{player.fields.discord_name}-{question_id}""",
        )

        now = UtcTime.now()

        training_mission = await Mission.create(
            fields=mission.Fields(
                discord_channel_id=str(mission_channel.id),
                review_discord_channel_id=None,
                player_discord_id=player_discord_id,
                reviewer_discord_id=None,
                question_id=question_id,
                stage=Stage(value=Stage.design),
                design=None,
                design_review=None,
                design_score=None,
                code=None,
                code_review=None,
                code_score=None,
                start_time=now,
                entered_stage_time=now,
                design_completion_time=now,
                design_review_completion_time=now,
                code_completion_time=now,
                code_review_completion_time=now,
            ),
            airtable_client=self.airtable_client,
        )

        _ = await self.messenger.player_started_training_mission(
            player=player,
            training_mission=training_mission,
            mission_question=mission_question,
        )

        return (training_mission, mission_channel)

    async def sync_discord_role(self, for_user: User):
        bot_discord_member = await self.discord_client.bot_member()
        bot_user = await User.row(
            formula=pyairtable.formulas.match(
                {user.Fields.discord_id_field: str(bot_discord_member.id)}
            ),
            airtable_client=self.airtable_client,
        )

        if for_user.fields.rank >= bot_user.fields.rank:
            return None

        await self.discord_client.set_role(
            member_id=for_user.fields.discord_id,
            role_name=for_user.fields.rank.to_string_hum(),
        )
        return None

    @staticmethod
    def get_rank(discord_member: discord.Member):
        highest_rank = Rank(value=Rank.foundation)

        for role in discord_member.roles:
            active_rank = Rank.of_string_hum(role.name)
            if active_rank is not None and active_rank > highest_rank:
                highest_rank = active_rank

        return highest_rank

    async def create_user(self, discord_member: discord.Member):
        discord_id = str(discord_member.id)
        discord_name = discord_member.name
        path_channel = await self.discord_client.create_private_channel(
            discord_id, channel_name=f"""{discord_name}-path"""
        )

        new_user = await User.create(
            fields=user.Fields(
                discord_id,
                discord_name,
                discord_channel_id=str(path_channel.id),
                rank=self.get_rank(discord_member),
            ),
            airtable_client=self.airtable_client,
        )

        _ = await self.sync_discord_role(for_user=new_user)

        _ = await self.messenger.welcome_new_discord_member(
            discord_member=discord_member, path_channel=path_channel
        )

        return (new_user, path_channel)

    async def set_rank(self, for_user: User, rank: Rank):
        updated_user = await for_user.set_rank(rank, airtable_client=self.airtable_client)
        await self.sync_discord_role(for_user=updated_user)
        return updated_user

    async def delete_all_users(self) -> List[User]:
        users_to_delete = await User.rows(formula=None, airtable_client=self.airtable_client)
        _ = await User.delete_rows(users_to_delete, airtable_client=self.airtable_client)
        return users_to_delete

    async def delete_all_missions(self) -> List[Mission]:
        missions_to_delete = await Mission.rows(formula=None, airtable_client=self.airtable_client)
        _ = await Mission.delete_rows(missions_to_delete, airtable_client=self.airtable_client)
        return missions_to_delete

    async def delete_all_channels(
        self, except_for: FrozenSet[discord.TextChannel]
    ) -> List[discord.TextChannel]:
        channels_to_delete = await self.discord_client.channels()
        except_for = frozenset([channel.id for channel in except_for])
        channels_to_delete = [
            channel_to_delete
            for channel_to_delete in channels_to_delete
            if channel_to_delete.id not in except_for
        ]
        for channel_to_delete in channels_to_delete:
            _ = await channel_to_delete.delete()
        return channels_to_delete

    async def enforce_time_limits(self):
        print("enforcing time limits")
        all_missions = await Mission.rows(formula=None, airtable_client=self.airtable_client)

        now = UtcTime.now()

        for mission_to_check in all_missions:
            time_in_stage = mission_to_check.time_in_stage(now)

            if (
                mission_to_check.fields.stage.has_value(Stage.design)
                and time_in_stage >= datetime.timedelta(minutes=Constants.DESIGN_TIME_LIMIT_MINUTES)
            ) or (
                mission_to_check.fields.stage.has_value(Stage.code)
                and time_in_stage >= datetime.timedelta(minutes=Constants.CODE_TIME_LIMIT_MINUTES)
            ):
                _ = await self.messenger.player_is_out_of_time_for_mission(
                    mission_past_due=mission_to_check
                )
            elif (
                mission_to_check.fields.stage.in_review()
                and mission_to_check.fields.reviewer_discord_id is None
                and time_in_stage >= datetime.timedelta(minutes=Constants.REVIEW_TIME_LIMIT_MINUTES)
            ):
                _ = await self.messenger.review_needs_to_be_claimed(for_mission=mission_to_check)
            elif mission_to_check.fields.stage.in_review() and time_in_stage >= datetime.timedelta(
                minutes=20
            ):
                _ = await self.messenger.reviewer_needs_to_review(for_mission=mission_to_check)

    async def get_level_changes(self, for_mission):
        # steps:
        # - find previously completed missions
        # - we combine scores of the previous HOW_MANY_PREVIOUS_QUESTIONS_TO_SCORE completed missions
        #   to calculate a users level/rank
        # - if the user hasn't completed enough missions, we just add all scores up to get their level
        # - we calculate the score_delta (current level using newest mission - previous level not including
        #   current mission
        completed_missions = await Mission.rows(
            formula=pyairtable.formulas.match(
                {
                    mission.Fields.player_discord_id_field: for_mission.fields.player_discord_id,
                    mission.Fields.stage_field: str(for_mission.fields.stage),
                }
            ),
            airtable_client=self.airtable_client,
        )
        completed_missions.sort(key=lambda mission: mission.fields.code_review_completion_time)

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
            len(scores_from_completed_missions) <= Mission.HOW_MANY_PREVIOUS_QUESTIONS_TO_SCORE
        )

        # calculate the existing level for the user
        previous_scores = (
            scores_from_completed_missions[:-1]
            if not_enough_scores
            else scores_from_completed_missions[
                -(Mission.HOW_MANY_PREVIOUS_QUESTIONS_TO_SCORE + 1) : -1
            ]
        )
        previous_level = int(State.calculate_level(previous_scores))

        current_scores = [scores_from_completed_missions[-1]]
        current_level = None

        # calculate the new level for the user
        if not_enough_scores:
            current_level = int(State.calculate_level(previous_scores + current_scores))
        else:
            current_level = int(State.calculate_level(previous_scores[1:] + current_scores))

        # calculate what the level delta (what is the current level - previous level of the user)
        level_delta = current_level - previous_level
        levels_until_evolution = ((int(current_level / 10) + 1) * 10) - current_level

        # fetch ranks and see if this user is evolving
        user_to_update = await User.row(
            formula=pyairtable.formulas.match(
                {user.Fields.discord_id_field: for_mission.fields.player_discord_id}
            ),
            airtable_client=self.airtable_client,
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
