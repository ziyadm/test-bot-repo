from typing import Dict, Optional

import airtable_client

from airtable_client import AirtableClient
from discord_client import DiscordClient
from rank import Rank

import pyairtable.formulas


class Fields:

    discord_id_field = 'discord_id'
    discord_name_field = 'discord_name'
    rank_field = 'rank'

    def __init__(self, discord_id: str, discord_name: str, rank: Rank):
        self.discord_id = discord_id
        self.discord_name = discord_name
        self.rank = rank
        
    def to_dict(self):
        return {
            self.discord_id_field: self.discord_id,
            self.discord_name_field: self.discord_name,
            self.rank_field: str(self.rank)}

    @classmethod
    def of_dict(cls, fields: Dict[str, str]):
        return cls(discord_id = fields[cls.discord_id_field],
                   discord_name = fields[cls.discord_name_field],
                   rank = Rank.of_string(fields[cls.rank_field]))

    # CR hmir: pull this into a module [Immutable_dict] to deduplicate with other Fields modules
    def immutable_updates(self, updates):
        updated = self.to_dict()
        for key, value in updates.items():
            updated[key] = str(value)
        return self.of_dict(updated)

    def immutable_update(self, field, value):
        return self.immutable_updates({field: value})


class User:
    
    table_name = 'users'
    
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
    async def get(cls, discord_id: str, airtable_client: AirtableClient):
        response = await airtable_client.get_row(
            table_name = cls.table_name,
            formula = pyairtable.formulas.match({Fields.discord_id_field: discord_id}))
        return cls.__of_airtable_response(response)

    @classmethod
    async def get_by_discord_name(cls, discord_name: str, airtable_client: AirtableClient):
        response = await airtable_client.get_row(
            table_name = cls.table_name,
            formula = pyairtable.formulas.match({Fields.discord_name_field: discord_name}))
        return cls.__of_airtable_response(response)

    async def set_rank(self,
                       rank: Rank,
                       airtable_client: AirtableClient,
                       discord_client: DiscordClient):
        await airtable_client.update_row(
            table_name = self.table_name,
            record_id = self.record_id,
            fields = self.fields.immutable_update(field = Fields.rank_field, value = rank).to_dict())
                           
        role_name = ' '.join([word.capitalize() for word in str(rank).split('-')])
        await discord_client.set_role(member_id = self.fields.discord_id, role_name = role_name)