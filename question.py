from typing import Dict, List, Optional

import airtable_client
from airtable_client import AirtableClient
from record import Record


class Fields(Record):
    question_id: str
    description: str
    tags: List[str]
    leetcode_url: str


class Question:

    table_name = "questions"

    def __init__(self, record_id: str, fields: Fields):
        self.record_id = record_id
        self.fields = fields

    @classmethod
    async def create_many(
        cls, all_fields: List[Fields], airtable_client: AirtableClient
    ):
        responses = await airtable_client.write_rows(
            table_name=cls.table_name,
            all_fields=[fields.to_json_serialized_dict() for fields in all_fields],
        )
        return [cls.__of_airtable_response(response) for response in responses]

    @classmethod
    def __of_airtable_response(cls, response: airtable_client.Response):
        return cls(
            record_id=response.record_id,
            fields=Fields.of_json_serialized_dict(response.fields),
        )

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
