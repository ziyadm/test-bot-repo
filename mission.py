from mission_status import MissionStatus

from typing import Optional


class Mission:

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