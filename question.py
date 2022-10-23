from typing import Dict

from airtable_client import AirtableClient


class Question:

    table_name = 'questions'

    def __init__(self,
                 question_id: str,
                 leetcode_url: str):
                     self.question_id = question_id
                     self.leetcode_url = leetcode_url

    @classmethod
    def of_airtable_response(cls,
                             airtable_response: Dict[str, str]):
        fields = airtable_response['fields']
                          
        return cls(question_id = fields['question_id'],
                   leetcode_url = fields['leetcode_url'])

    @classmethod
    async def all(cls,
                  airtable_client: AirtableClient):
                      airtable_response = airtable_client \
                                              .table(table_name = cls.table_name) \
                                              .all()

                      return [cls.of_airtable_response(question_response) for question_response in airtable_response]