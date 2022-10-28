import mission
import user

from airtable_client import AirtableClient
from discord_client import DiscordClient
from question import Question
from mission import Mission
from mission_status import MissionStatus
from rank import Rank
from user import User

import pyairtable.formulas


class State:

    def __init__(self, airtable_client: AirtableClient, discord_client: DiscordClient):
        self.airtable_client = airtable_client
        self.discord_client = discord_client

    async def sync_discord_role(self, for_user: User):
        return await self.discord_client.set_role(
            member_id = for_user.fields.discord_id, role_name = for_user.fields.rank.to_string_hum())

    async def first_unasked_question(self, for_user: User):
        existing_missions = await Mission.rows(
            formula = pyairtable.formulas.match({mission.Fields.player_discord_id_field: for_user.fields.discord_id}),
            airtable_client = self.airtable_client)
        
        questions_already_asked = set([existing_mission.fields.question_id for existing_mission in existing_missions])
        
        questions = await Question.rows(formula = None, airtable_client = self.airtable_client)
        
        for question in questions:
            if question.fields.question_id not in questions_already_asked:
                return question

        return None

    async def create_mission(self, player_discord_id: str):
        player = await User.row(
            formula = pyairtable.formulas.match({user.Fields.discord_id_field: player_discord_id}),
            airtable_client = self.airtable_client)
        
        mission_question = await self.first_unasked_question(player)
        if not mission_question:
            return None

        question_id = mission_question.fields.question_id
        mission_channel = await self.discord_client.create_private_channel(
            member_id = player_discord_id,
            channel_name = f"""{player.fields.discord_name}-{question_id}""")

        new_mission = await Mission.create(
            fields = mission.Fields(
                discord_channel_id = str(mission_channel.id),
                player_discord_id = player_discord_id,
                reviewer_discord_id = None,
                question_id = question_id,
                mission_status = MissionStatus(value = MissionStatus.design),
                design = None,
                code = None),
            airtable_client = self.airtable_client)

        await mission_channel.send(f"""Here's your mission: {mission_question.fields.leetcode_url}""")
        
        return (new_mission, mission_channel)

    async def create_user(self, discord_id: str, discord_name: str, rank: Rank):
        user_channel = await self.discord_client.create_private_channel(discord_id, channel_name = f"""{discord_name}-path""")
        discord_channel_id = str(user_channel.id)

        new_user = await User.create(
            fields = user.Fields(discord_id, discord_name, discord_channel_id, rank), airtable_client = self.airtable_client)

        await self.sync_discord_role(for_user = new_user)

        return (new_user, user_channel)