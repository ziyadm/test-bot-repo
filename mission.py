from typing import Optional

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


    @staticmethod
    async def get_one(airtable_client: AirtableClient,
                      discord_channel_id: str):
                          table = airtable_client.table(table_name = Mission.table_name)
                          response = table.all(formula = pyairtable.formulas.match({
                              'discord_channel_id': discord_channel_id}))
                          
                          if len(response) != 1:
                              return None

                          response = response[0]
                          fields = response['fields']
                          
                          return Mission(record_id = response['id'],
                                         discord_channel_id = discord_channel_id,
                                         player_discord_id = fields['player_discord_id'],
                                         reviewer_discord_id = fields.get('reviewer_discord_id',
                                                                            None),
                                         question_id = fields['question_id'],
                                         mission_status = MissionStatus.of_string(fields['mission_status']),
                                         design = fields.get('design',
                                                               None),
                                         code = fields.get('code',
                                                             None))

    @staticmethod
    async def update(airtable_client: AirtableClient,
                     record_id: str,
                     reviewer_discord_id: Optional[str] = None,
                     mission_status: Optional[MissionStatus] = None,
                     design: Optional[str] = None,
                     code: Optional[str] = None):
                         table = airtable_client.table(table_name = Mission.table_name)
                         fields = [
                             ('reviewer_discord_id', reviewer_discord_id),
                             ('mission_status', mission_status),
                             ('design', design),
                             ('code', code)]

                         table.update(record_id,
                                      fields = {
                                          field: str(new_value) for
                                          (field, new_value) in
                                          fields if new_value})