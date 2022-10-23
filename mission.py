from typing import Dict, List, Optional

from airtable_client import AirtableClient
from mission_status import MissionStatus

import pyairtable


class Mission:

    table_name = 'missions'

    def __init__(self,
                 record_id: str,
                 discord_channel_id: str,
                 player_discord_id: str,
                 reviewer_discord_id: Optional[str],
                 question_id: str,
                 mission_status: MissionStatus,
                 design: Optional[str],
                 code: Optional[str]):
                     self.record_id = record_id
                     self.discord_channel_id = discord_channel_id
                     self.player_discord_id = player_discord_id
                     self.reviewer_discord_id = reviewer_discord_id
                     self.question_id = question_id
                     self.mission_status = mission_status
                     self.design = design
                     self.code = code

    @classmethod
    def of_airtable_response(cls,
                             airtable_response: Dict[str, str]):
        fields = airtable_response['fields']
                          
        return cls(record_id = airtable_response['id'],
                   discord_channel_id = fields['discord_channel_id'],
                   player_discord_id = fields['player_discord_id'],
                   reviewer_discord_id = fields.get('reviewer_discord_id',
                                                    None),
                   question_id = fields['question_id'],
                   mission_status = MissionStatus.of_string(fields['mission_status']),
                   design = fields.get('design',
                                       None),
                   code = fields.get('code',
                                     None))

    # CR hmir: can we deduplicate this and [Question.select]
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
                  discord_channel_id: str):
                      all_with_matching_discord_channel_id = await cls.select(airtable_client = airtable_client,
                                                                              formula = pyairtable.formulas.match({
                                                                                  'discord_channel_id': discord_channel_id}))
                      
                      if len(all_with_matching_discord_channel_id) != 1:
                          return None
                      
                      return all_with_matching_discord_channel_id[0]

    @classmethod
    async def all_for_player(cls,
                             airtable_client: AirtableClient,
                             player_discord_id: str):
                     return await cls.select(airtable_client = airtable_client,
                                             formula = pyairtable.formulas.match({
                                                 'player_discord_id': player_discord_id}))

    @classmethod
    async def create(cls,
                     airtable_client: AirtableClient,
                     discord_channel_id: str,
                     player_discord_id: str,
                     reviewer_discord_id: Optional[str],
                     question_id: str,
                     mission_status: MissionStatus,
                     design: Optional[str],
                     code: Optional[str]):
                         def optional_to_string(optional: Optional[str]):
                             return str(optional) if optional != None else ''
                             
                         return cls.of_airtable_response(airtable_response = airtable_client \
                                                             .table(table_name = cls.table_name) \
                                                             .create({
                                                                 'discord_channel_id': discord_channel_id,
                                                                 'player_discord_id': player_discord_id,
                                                                 'reviewer_discord_id': optional_to_string(reviewer_discord_id),
                                                                 'question_id': question_id,
                                                                 'mission_status': str(mission_status),
                                                                 'design': optional_to_string(design),
                                                                 'code': optional_to_string(code)}))

    @classmethod
    async def update(cls,
                     airtable_client: AirtableClient,
                     record_id: str,
                     reviewer_discord_id: Optional[str] = None,
                     mission_status: Optional[MissionStatus] = None,
                     design: Optional[str] = None,
                     code: Optional[str] = None):
                         fields = [
                             ('reviewer_discord_id', reviewer_discord_id),
                             ('mission_status', mission_status),
                             ('design', design),
                             ('code', code)]

                         airtable_client \
                             .table(table_name = cls.table_name) \
                             .update(record_id,
                                     fields = {field: str(new_value) for
                                               (field, new_value) in fields if new_value})