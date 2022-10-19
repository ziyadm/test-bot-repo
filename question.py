from typing import Dict, Optional

import airtable_client

from airtable_client import AirtableClient


class Fields:

    question_id_field = "question_id"
    leetcode_url_field = "leetcode_url"

    def __init__(self, question_id: str, leetcode_url: str):
        self.question_id = question_id
        self.leetcode_url = leetcode_url

    @classmethod
    def of_dict(cls, fields: Dict[str, str]):
        return cls(
            question_id=fields[cls.question_id_field],
            leetcode_url=fields[cls.leetcode_url_field],
        )


class Question:

    table_name = "questions"

    def __init__(self, record_id: str, fields: Fields):
        self.record_id = record_id
        self.fields = fields

    @classmethod
    def __of_airtable_response(cls, response: airtable_client.Response):
        return cls(record_id=response.record_id, fields=Fields.of_dict(response.fields))

    @classmethod
    async def rows(cls, formula: Optional[str], airtable_client: AirtableClient):
        responses = await airtable_client.rows(
            table_name=cls.table_name, formula=formula
        )
        return [cls.__of_airtable_response(response) for response in responses]
