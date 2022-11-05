from typing import Optional

import discord
import pyairtable.formulas

import airtable_client
import user
from airtable_client import AirtableClient
from mission_status import MissionStatus
from record import Record
from user import User


class Fields(Record):
    discord_channel_id: str
    review_discord_channel_id: Optional[str]
    player_discord_id: str
    reviewer_discord_id: Optional[str]
    question_id: str
    mission_status: MissionStatus
    design: Optional[str]
    design_review: Optional[str]
    design_score: Optional[float]
    code: Optional[str]
    code_review: Optional[str]
    code_score: Optional[float]
    # TODO: use a [Utc_time] module for these
    created_ts: Optional[str]
    last_updated_ts: Optional[str]


class Mission:

    HOW_MANY_PREVIOUS_QUESTIONS_TO_SCORE = 5
    table_name = "missions"

    def __init__(self, record_id: str, fields: Fields):
        self.record_id = record_id
        self.fields = fields

    @classmethod
    def __of_airtable_response(cls, response: airtable_client.Response):
        return cls(
            record_id=response.record_id,
            fields=Fields.of_json_serialized_dict(response.fields),
        )

    @classmethod
    async def create(cls, fields: Fields, airtable_client: AirtableClient):
        response = await airtable_client.write_row(
            table_name=cls.table_name, fields=fields.to_json_serialized_dict()
        )
        return cls.__of_airtable_response(response)

    @classmethod
    async def row(cls, formula: Optional[str], airtable_client: AirtableClient):
        response = await airtable_client.row(table_name=cls.table_name, formula=formula)
        return cls.__of_airtable_response(response)

    @classmethod
    async def rows(cls, formula: Optional[str], airtable_client: AirtableClient):
        responses = await airtable_client.rows(
            table_name=cls.table_name, formula=formula
        )
        return [cls.__of_airtable_response(response) for response in responses]

    @classmethod
    async def delete_rows(cls, missions_to_delete, airtable_client: AirtableClient):
        await airtable_client.delete_rows(
            table_name=cls.table_name,
            record_ids=[
                mission_to_delete.record_id for mission_to_delete in missions_to_delete
            ],
        )
        return None

    def completing(self):
        return self.fields.mission_status.next().has_value(MissionStatus.completed)

    def in_review(self):
        return self.fields.mission_status.has_value(
            MissionStatus.design_review
        ) or self.fields.mission_status.has_value(MissionStatus.code_review)

    def get_review_field(self):
        return (
            Fields.field().design_review
            if self.fields.mission_status.has_value(MissionStatus.design_review)
            else Fields.field().code_review
        )

    def get_content_field(self):
        design_stage = self.fields.mission_status.has_value(
            MissionStatus.design_review
        ) or self.fields.mission_status.has_value(MissionStatus.design)
        return Fields.field().design if design_stage else Fields.field().code

    def get_content_value(self):
        design_stage = self.fields.mission_status.has_value(
            MissionStatus.design_review
        ) or self.fields.mission_status.has_value(MissionStatus.design)
        return self.fields.design if design_stage else self.fields.code

    async def get_review_values(self, interaction: discord.Interaction):
        review_field = self.get_review_field()
        messages = await Mission.get_messages(interaction)
        review_value = messages[0].content
        return review_field, review_value

    async def update(self, fields: Fields, airtable_client: AirtableClient):
        response = await airtable_client.update_row(
            table_name=self.table_name,
            record_id=self.record_id,
            fields=fields.to_dict(),
        )
        return self.__of_airtable_response(response)

    def calculate_level(self, scores):
        aggregate_score = 0.0

        for score in scores:
            aggregate_score += score[0]
            aggregate_score += score[1]

        return aggregate_score

    async def get_level_changes(self, airtable_client: AirtableClient):
        # steps:
        # - find previously completed missions
        # - we combine scores of the previous HOW_MANY_PREVIOUS_QUESTIONS_TO_SCORE completed missions
        #   to calculate a users level/rank
        # - if the user hasn't completed enough missions, we just add all scores up to get their level
        # - we calculate the score_delta (current level using newest mission - previous level not including
        #   current mission
        completed_missions = await self.rows(
            formula=pyairtable.formulas.match(
                {
                    Fields.field().player_discord_id: self.fields.player_discord_id,
                    Fields.field()
                    .mission_status: self.fields.mission_status.next()
                    .get_field(),
                }
            ),
            airtable_client=airtable_client,
        )
        completed_missions.sort(key=lambda mission: mission.fields.last_updated_ts)

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
        previous_level = int(self.calculate_level(previous_scores))

        current_scores = [scores_from_completed_missions[-1]]
        current_level = None

        # calculate the new level for the user
        if not_enough_scores:
            current_level = int(self.calculate_level(previous_scores + current_scores))
        else:
            current_level = int(
                self.calculate_level(previous_scores[1:] + current_scores)
            )

        # calculate what the level delta (what is the current level - previous level of the user)
        # players can't lose levels, so de-evolutions shouldn't be a problem
        level_delta = max(current_level - previous_level, 0)
        levels_until_evolution = ((int(current_level / 10) + 1) * 10) - current_level

        # fetch ranks and see if this user is evolving
        user_to_update = await User.row(
            formula=pyairtable.formulas.match(
                {user.Fields.field().discord_id: self.fields.player_discord_id}
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
    async def get_messages(interaction: discord.Interaction):
        return [
            message
            async for message in interaction.channel.history()
            if message.type == discord.MessageType.default
        ]
