from typing import Dict

from airtable_client import AirtableClient


class Question:

    table_name = 'questions'

    def __init__(self, question_id: str, leetcode_url: str):
        self.question_id = question_id
        self.leetcode_url = leetcode_url

    @classmethod
    def __of_airtable_response(cls, airtable_response: Dict[str, str]):
        fields = airtable_response['fields']
                          
        return cls(question_id = fields['question_id'], leetcode_url = fields['leetcode_url'])

    @classmethod
    async def select(cls, airtable_client: AirtableClient, formula):
        table = airtable_client.table(table_name = cls.table_name)

        airtable_responses = None
        if formula == None:
            airtable_responses = table.all()
        else:
            airtable_responses = table.all(formula = formula)

        return [cls.__of_airtable_response(airtable_response) for airtable_response in airtable_responses]

    @classmethod
    async def all(cls, airtable_client: AirtableClient):
        return await cls.select(airtable_client = airtable_client, formula = None)