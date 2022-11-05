from typing import Dict, Optional

import airtable_client
from airtable_client import AirtableClient
from rank import Rank
from record import Record


class Fields(Record):
    discord_id: str
    discord_name: str
    discord_channel_id: str
    rank: Rank


class User:

    table_name = "users"

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
    async def delete_rows(cls, users_to_delete, airtable_client: AirtableClient):
        await airtable_client.delete_rows(
            table_name=cls.table_name,
            record_ids=[user_to_delete.record_id for user_to_delete in users_to_delete],
        )
        return None

    async def set_rank(self, rank: Rank, airtable_client: AirtableClient):
        response = await airtable_client.update_row(
            table_name=self.table_name,
            record_id=self.record_id,
            fields=self.fields.update(
                {Fields.field().rank: rank}
            ).to_json_serialized_dict(),
        )

        return self.__of_airtable_response(response)


class Test:
    @classmethod
    def run_roundtrip(cls, test_fields):
        assert (
            Fields.of_json_serialized_dict(test_fields.to_json_serialized_dict())
            == test_fields
        )

    @classmethod
    def roundtrip_fields(cls):
        cls.run_roundtrip(
            Fields(
                discord_id="123123124124",
                discord_name="test-discord-name",
                discord_channel_id="1231241",
                rank=Rank(Rank.copper),
            )
        )

    @classmethod
    def run_all_roundtrip(cls):
        cls.roundtrip_fields()

    @classmethod
    def run_all(cls):
        cls.run_all_roundtrip()


Test.run_all()
