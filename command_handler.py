import mission

from airtable_client import AirtableClient
from discord_client import DiscordClient
from mission import Mission
from mission_status import MissionStatus
from question import Question
from rank import Rank
from user import User

import discord


class CommandHandler:

    def __init__(self, airtable_client: AirtableClient, discord_client: DiscordClient):
        self.airtable_client = airtable_client
        self.discord_client = discord_client

    async def get_first_unasked_question(self, user: User):
        missions = await Mission.all_with_player(
            player_discord_id = user.fields.discord_id,
            airtable_client = self.airtable_client)
        questions_already_asked = set([mission.fields.question_id for mission in missions])
        questions = await Question.all(airtable_client = self.airtable_client)
        for question in questions:
            if question.fields.question_id not in questions_already_asked:
                return question

    async def new_command(self, interaction: discord.Interaction):
        player_discord_id = str(interaction.user.id)
        player = await User.get(
            discord_id = player_discord_id, airtable_client = self.airtable_client)
        question = await self.get_first_unasked_question(player)

        if not question:
            return await interaction.followup.send('Monarch Suriel has no new training for you')

        question_id = question.fields.question_id
        
        mission_channel = await self.discord_client.create_private_channel(
            member_id = player_discord_id,
            channel_name = f"""{player.fields.discord_name}-{question_id}""")

        mission_fields = mission.Fields(
            discord_channel_id = str(mission_channel.id),
            player_discord_id = player_discord_id,
            reviewer_discord_id = None,
            question_id = question_id,
            mission_status = MissionStatus(value = MissionStatus.design),
            design = None,
            code = None)

        await Mission.create(fields = mission_fields, airtable_client = self.airtable_client)
        await mission_channel.send(f"""Here's your mission: {question.fields.leetcode_url}""")
        return await interaction.followup.send(
            f"""Monarch Suriel has invited you to {mission_channel.mention}""")

    async def submit_command(self, interaction: discord.Interaction):
        # CR hmir: only allow submit in mission channel
        # CR hmir: we probably wanna rename submit to fit the "mission"/"quest" theme
        mission_to_update = await Mission.get(
            discord_channel_id = str(interaction.channel_id),
            airtable_client = self.airtable_client)
    
        if not (mission_to_update.fields.mission_status.has_value(MissionStatus.design) or
                mission_to_update.fields.mission_status.has_value(MissionStatus.code)):
                    return await interaction.followup.send(
                        """You've completed your objective, wait for Monarch Suriel's instructions!""")
    
        messages = [
            message async for message in interaction.channel.history()
            if message.type == discord.MessageType.default]
        
        if len(messages) == 0:
            # CR hmir: maybe we can frame missions as you having "minions" who you have to give instructions to to solve some problems you come across in your journey?
            # alternatively it could be framed as being a world of machines and you need to make the machines do what you want. i think theres a pretty popular recent game thats similar to this
            # follow up with ziyad
            return await interaction.followup.send('You need to instruct your minions!')
        
        field_to_submit_contents_for = None
        response = None
        if mission_to_update.fields.mission_status.has_value(MissionStatus.design):
            field_to_submit_contents_for = mission.Fields.design_field
            response = """Planning is half the battle! We've sent your plan to Monarch Suriel for approval. Check back in about 30 minutes to find out your next objective."""
        elif mission_to_update.fields.mission_status.has_value(MissionStatus.code):
            field_to_submit_contents_for = mission.Fields.code_field
            response = """Monarch Suriel will be pleased! We've sent your instructions to Him for approval. Once they're approved, they'll be sent directly to your minions on the frontlines!"""
            
        updated_mission_fields = mission_to_update.fields.immutable_updates({
            mission.Fields.mission_status_field: mission_to_update.fields.mission_status.next(),
            field_to_submit_contents_for: messages[0].content})
        await mission_to_update.update(
            fields = updated_mission_fields, airtable_client = self.airtable_client)
        return await interaction.followup.send(response)

    async def set_rank(self, interaction: discord.Interaction, user_discord_name: str, rank: str):
        user_to_update = await User.get_by_discord_name(
            discord_name = user_discord_name, airtable_client = self.airtable_client)
        await user_to_update.set_rank(
            rank = Rank.of_string(rank),
            airtable_client = self.airtable_client,
            discord_client = self.discord_client)
        return await interaction.followup.send(f"""Updated {user_discord_name}'s rank to {rank}""")