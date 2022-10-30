from typing import Dict, Optional

import discord

import airtable_client
from airtable_client import AirtableClient
from mission_status import MissionStatus


class Fields:

    discord_channel_id_field = "discord_channel_id"
    review_discord_channel_id_field = "review_discord_channel_id"
    player_discord_id_field = "player_discord_id"
    reviewer_discord_id_field = "reviewer_discord_id"
    question_id_field = "question_id"
    mission_status_field = "mission_status"
    design_field = "design"
    design_review_field = "design_review"
    design_score_field = "design_score"
    code_field = "code"
    code_review_field = "code_review"
    code_score_field = "code_score"

    def __init__(
        self,
        discord_channel_id: str,
        review_discord_channel_id: Optional[str],
        player_discord_id: str,
        reviewer_discord_id: Optional[str],
        question_id: str,
        mission_status: MissionStatus,
        design: Optional[str],
        design_review: Optional[str],
        design_score: Optional[float],
        code: Optional[str],
        code_review: Optional[str],
        code_score: Optional[float],
    ):
        self.discord_channel_id = discord_channel_id
        self.review_discord_channel_id = review_discord_channel_id
        self.player_discord_id = player_discord_id
        self.reviewer_discord_id = reviewer_discord_id
        self.question_id = question_id
        self.mission_status = mission_status
        self.design = design
        self.design_review = design_review
        self.design_score = design_score
        self.code = code
        self.code_review = code_review
        self.code_score = code_score

    def to_dict(self):
        def optional_to_string(optional: Optional[str]):
            return str(optional) if optional is not None else ""

        def optional_to_float(optional: Optional[float]):
            return optional if optional is not None else 0.0

        return {
            self.discord_channel_id_field: self.discord_channel_id,
            self.review_discord_channel_id_field: optional_to_string(
                self.review_discord_channel_id
            ),
            self.player_discord_id_field: self.player_discord_id,
            self.reviewer_discord_id_field: optional_to_string(
                self.reviewer_discord_id
            ),
            self.question_id_field: self.question_id,
            self.mission_status_field: str(self.mission_status),
            self.design_field: optional_to_string(self.design),
            self.design_review_field: optional_to_string(self.design_review),
            self.design_score_field: optional_to_float(self.design_score),
            self.code_field: optional_to_string(self.code),
            self.code_review_field: optional_to_string(self.code_review),
            self.code_score_field: optional_to_float(self.code_score),
        }

    @classmethod
    def of_dict(cls, fields: Dict[str, str]):
        return cls(
            discord_channel_id=fields[cls.discord_channel_id_field],
            review_discord_channel_id=fields.get(
                cls.review_discord_channel_id_field, None
            ),
            player_discord_id=fields[cls.player_discord_id_field],
            reviewer_discord_id=fields.get(cls.reviewer_discord_id_field, None),
            question_id=fields[cls.question_id_field],
            mission_status=MissionStatus.of_string(fields[cls.mission_status_field]),
            design=fields.get(cls.design_field, None),
            design_review=fields.get(cls.design_review_field, None),
            design_score=fields.get(cls.design_score_field, None),
            code=fields.get(cls.code_field, None),
            code_review=fields.get(cls.code_review_field, None),
            code_score=fields.get(cls.code_score_field, None),
        )

    def immutable_updates(self, updates):
        updated = self.to_dict()
        for key, value in updates.items():
            if type(value) is float:
                updated[key] = float(value)
            else:
                updated[key] = str(value)
        return self.of_dict(updated)

    def immutable_update(self, field, value):
        return self.immutable_updates({field: value})


class Mission:

    table_name = "missions"

    def __init__(self, record_id: str, fields: Fields):
        self.record_id = record_id
        self.fields = fields

    @classmethod
    def __of_airtable_response(cls, response: airtable_client.Response):
        return cls(record_id=response.record_id, fields=Fields.of_dict(response.fields))

    @classmethod
    async def create(cls, fields: Fields, airtable_client: AirtableClient):
        response = await airtable_client.write_row(
            table_name=cls.table_name, fields=fields.to_dict()
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
            Fields.design_review_field
            if self.fields.mission_status.has_value(MissionStatus.design_review)
            else Fields.code_review_field
        )

    def get_content_field(self):
        design_stage = self.fields.mission_status.has_value(
            MissionStatus.design_review
        ) or self.fields.mission_status.has_value(MissionStatus.design)
        return Fields.design_field if design_stage else Fields.code_field

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

    @staticmethod
    async def get_messages(interaction: discord.Interaction):
        return [
            message
            async for message in interaction.channel.history()
            if message.type == discord.MessageType.default
        ]
