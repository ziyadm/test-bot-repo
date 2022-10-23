from typing import Dict

from airtable_client import AirtableClient

import pyairtable


class User:

    table_name = 'users'

    def __init__(self,
                 discord_id: str,
                 discord_name: str):
                     self.discord_id = discord_id
                     self.discord_name = discord_name

    @classmethod
    def of_airtable_response(cls,
                             airtable_response: Dict[str, str]):
                                 fields = airtable_response['fields']

                                 return cls(discord_id = fields['discord_id'],
                                            discord_name = fields['discord_name'])

    @classmethod
    async def select(cls,
                     airtable_client: AirtableClient,
                     formula):
                         table = airtable_client.table(table_name = cls.table_name)

                         airtable_responses = None
                         if formula == None:
                             airtable_responses = table.all()
                         else:
                             airtable_responses = table.all(formula = formula)

                         return [cls.of_airtable_response(airtable_response) for airtable_response in airtable_responses]

    @classmethod
    async def one(cls,
                  airtable_client: AirtableClient,
                  discord_id: str):
                      all_with_matching_discord_id = await cls.select(airtable_client = airtable_client,
                                                                      formula = pyairtable.formulas.match({
                                                                          'discord_id': discord_id}))
                      
                      if len(all_with_matching_discord_id) != 1:
                          return None
                      
                      return all_with_matching_discord_id[0]

    @classmethod
    async def create(cls,
                     airtable_client: AirtableClient,
                     discord_id: str,
                     discord_name: str):
                         return cls.of_airtable_response(airtable_response = airtable_client \
                                                             .table(table_name = cls.table_name) \
                                                             .create({
                                                                 'discord_id': discord_id,
                                                                 'discord_name': discord_name}))
