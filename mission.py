from typing import Dict, Optional

import airtable_client

from airtable_client import AirtableClient
from mission_status import MissionStatus

import pyairtable.formulas


class Fields:

    discord_channel_id_field = 'discord_channel_id'
    player_discord_id_field = 'player_discord_id'
    reviewer_discord_id_field = 'reviewer_discord_id'
    question_id_field = 'question_id'
    mission_status_field = 'mission_status'
    design_field = 'design'
    code_field = 'code'
        
    def __init__(self,
                 discord_channel_id: str,
                 player_discord_id: str,
                 reviewer_discord_id: Optional[str],
                 question_id: str,
                 mission_status: MissionStatus,
                 design: Optional[str],
                 code: Optional[str]):
                     self.discord_channel_id = discord_channel_id
                     self.player_discord_id = player_discord_id
                     self.reviewer_discord_id = reviewer_discord_id
                     self.question_id = question_id
                     self.mission_status = mission_status
                     self.design = design
                     self.code = code

    def to_dict(self):
        def optional_to_string(optional: Optional[str]):
            return str(optional) if optional != None else ''
            
        return {
            self.discord_channel_id_field: self.discord_channel_id,
            self.player_discord_id_field: self.player_discord_id,
            self.reviewer_discord_id_field: optional_to_string(self.reviewer_discord_id),
            self.question_id_field: self.question_id,
            self.mission_status_field: str(self.mission_status),
            self.design_field: optional_to_string(self.design),
            self.code_field: optional_to_string(self.code)}

    @classmethod
    def of_dict(cls, fields: Dict[str, str]):
        return cls(discord_channel_id = fields[cls.discord_channel_id_field],
                   player_discord_id = fields[cls.player_discord_id_field],
                   reviewer_discord_id = fields.get(cls.reviewer_discord_id_field, None),
                   question_id = fields[cls.question_id_field],
                   mission_status = MissionStatus.of_string(fields[cls.mission_status_field]),
                   design = fields.get(cls.design_field, None),
                   code = fields.get(cls.code_field, None))

    # CR hmir: pull this into a module [Immutable_dict] to deduplicate with other Fields modules
    def immutable_updates(self, updates):
        updated = self.to_dict()
        for key, value in updates.items():
            updated[key] = str(value)
        return self.of_dict(updated)

    def immutable_update(self, field, value):
        return self.immutable_updates({field: value})


class Mission:

    table_name = 'missions'

    def __init__(self, record_id: str, fields: Fields):
        self.record_id = record_id
        self.fields = fields

    @classmethod
    def __of_airtable_response(cls, response: airtable_client.Response):
        return cls(record_id = response.record_id, fields = Fields.of_dict(response.fields))

    @classmethod
    async def create(cls, fields: Fields, airtable_client: AirtableClient):
        response = await airtable_client.write_row(table_name = cls.table_name, fields = fields.to_dict())
        return cls.__of_airtable_response(response)

    @classmethod
    async def get(cls, discord_channel_id: str, airtable_client: AirtableClient):
        response = await airtable_client.get_row(
            table_name = cls.table_name,
            formula = pyairtable.formulas.match({Fields.discord_channel_id_field: discord_channel_id}))
        return cls.__of_airtable_response(response)

    @classmethod
    async def all_with_player(cls, player_discord_id: str, airtable_client: AirtableClient):
        responses = await airtable_client.get_all(
            table_name = cls.table_name, formula = {Fields.player_discord_id_field: player_discord_id})
        return [cls.__of_airtable_response(response) for response in responses]

    async def update(self, fields: Fields, airtable_client: AirtableClient):
        response = await airtable_client.update_row(
            table_name = self.table_name, record_id = self.record_id, fields = fields.to_dict())
        return self.__of_airtable_response(response)