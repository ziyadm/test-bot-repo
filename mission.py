from typing import Optional

from airtable_client import AirtableClient
from mission_status import MissionStatus


import pyairtable


class Mission:

    table_name = 'missions'

    def __init__(self,
                 discord_channel_id: str,
                 player_discord_id: str,
                 reviewer_discord_id: Optional[str],
                 question_id: str,
                 mission_status: MissionStatus):
                     self.discord_channel_id = discord_channel_id
                     self.player_discord_id = player_discord_id
                     self.reviewer_discord_id = reviewer_discord_id
                     self.question_id = question_id
                     self.mission_status = mission_status


    @staticmethod
    async def get_one(airtable_client: AirtableClient,
                      discord_channel_id: str):
                          table = airtable_client.table(table_name = Mission.table_name)
                          response = table.all(formula = pyairtable.formulas.match({
                              'discord_channel_id': discord_channel_id}))
                          
                          if len(response) != 1:
                              return None
    
                          response = response[0]['fields']
                              
                          return Mission(discord_channel_id = discord_channel_id,
                                         player_discord_id = response['player_discord_id'],
                                         reviewer_discord_id = response.get('reviewer_discord_id',
                                                                            None),
                                         question_id = response['question_id'],
                                         mission_status = MissionStatus.of_string(response['mission_status']))