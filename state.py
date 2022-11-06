from typing import FrozenSet, List

import discord
import pyairtable.formulas

import mission
import user
from airtable_client import AirtableClient
from discord_client import DiscordClient
from mission import Mission
from question import Question
from rank import Rank
from stage import Stage
from user import User
from utc_time import UtcTime


class State:
    def __init__(self, airtable_client: AirtableClient, discord_client: DiscordClient):
        self.airtable_client = airtable_client
        self.discord_client = discord_client

    async def first_unasked_question(self, for_user: User):
        existing_missions = await Mission.rows(
            formula=pyairtable.formulas.match(
                {mission.Fields.player_discord_id_field: for_user.fields.discord_id}
            ),
            airtable_client=self.airtable_client,
        )

        questions_already_asked = set(
            [existing_mission.fields.question_id for existing_mission in existing_missions]
        )

        questions = await Question.rows(formula=None, airtable_client=self.airtable_client)

        for question in questions:
            if question.fields.question_id not in questions_already_asked:
                return question

        return None

    async def create_mission(self, player_discord_id: str):
        player = await User.row(
            formula=pyairtable.formulas.match({user.Fields.discord_id_field: player_discord_id}),
            airtable_client=self.airtable_client,
        )

        mission_question = await self.first_unasked_question(player)
        if not mission_question:
            return None

        question_id = mission_question.fields.question_id
        mission_channel = await self.discord_client.create_private_channel(
            member_id=player_discord_id,
            channel_name=f"""{player.fields.discord_name}-{question_id}""",
        )

        now = UtcTime.now()

        new_mission = await Mission.create(
            fields=mission.Fields(
                discord_channel_id=str(mission_channel.id),
                review_discord_channel_id=None,
                player_discord_id=player_discord_id,
                reviewer_discord_id=None,
                question_id=question_id,
                stage=Stage(value=Stage.design),
                design=None,
                design_review=None,
                design_score=None,
                code=None,
                code_review=None,
                code_score=None,
                start_time=now,
                entered_stage_time=now,
            ),
            airtable_client=self.airtable_client,
        )

        discord_user = await self.discord_client.member(player_discord_id)
        _ = await DiscordClient.with_typing_time_determined_by_number_of_words(
            message=f"""Welcome to your training mission {discord_user.mention}!""",
            channel=mission_channel,
        )

        _ = await DiscordClient.with_typing_time_determined_by_number_of_words(
            message="Your mission instructions follow, read them carefully:",
            channel=mission_channel,
        )

        _ = await DiscordClient.with_typing_time_determined_by_number_of_words(
            message=f"""```{mission_question.fields.description}```""",
            channel=mission_channel,
        )

        _ = await DiscordClient.with_typing_time_determined_by_number_of_words(
            message=f"""Good luck, {discord_user.mention}, you'll need it...""",
            channel=mission_channel,
        )

        _ = await DiscordClient.with_typing_time_determined_by_number_of_words(
            message="Missions consist of two stages:",
            channel=mission_channel,
        )

        _ = await DiscordClient.with_typing_time_determined_by_number_of_words(
            message="""`Design`: *Describe how you plan to solve the question. Make sure to write this **in english** without getting too close to the code!*""",
            channel=mission_channel,
        )

        _ = await DiscordClient.with_typing_time_determined_by_number_of_words(
            message="""`Code`: *Implement the solution your described in the* `Design` *stage in the programming language of your choice.*""",
            channel=mission_channel,
        )

        _ = await DiscordClient.with_typing_time_determined_by_number_of_words(
            message="""Type `/submit` to send your work on a stage to Suriel for review. Only your most recent message will be used in your submission.""",
            channel=mission_channel,
        )

        return (new_mission, mission_channel)

    async def sync_discord_role(self, for_user: User):
        bot_discord_member = await self.discord_client.bot_member()
        bot_user = await User.row(
            formula=pyairtable.formulas.match(
                {user.Fields.discord_id_field: str(bot_discord_member.id)}
            ),
            airtable_client=self.airtable_client,
        )

        if for_user.fields.rank > bot_user.fields.rank:
            return None

        await self.discord_client.set_role(
            member_id=for_user.fields.discord_id,
            role_name=for_user.fields.rank.to_string_hum(),
        )
        return None

    @staticmethod
    def get_rank(discord_member: discord.Member):
        highest_rank = Rank(value=Rank.foundation)

        for role in discord_member.roles:
            active_rank = Rank.of_string_hum(role.name)
            if active_rank is not None and active_rank > highest_rank:
                highest_rank = active_rank

        return highest_rank

    async def create_user(self, discord_member: discord.Member):
        discord_id = str(discord_member.id)
        discord_name = discord_member.name
        user_channel = await self.discord_client.create_private_channel(
            discord_id, channel_name=f"""{discord_name}-path"""
        )

        discord_channel_id = str(user_channel.id)
        rank = self.get_rank(discord_member)

        new_user = await User.create(
            fields=user.Fields(discord_id, discord_name, discord_channel_id, rank),
            airtable_client=self.airtable_client,
        )

        await DiscordClient.with_typing_time_determined_by_number_of_words(
            message=f"""Suriel senses your weakness {discord_member.mention}""",
            channel=user_channel,
        )

        await DiscordClient.with_typing_time_determined_by_number_of_words(
            message="Suriel invites you to follow The Way",
            channel=user_channel,
        )

        await DiscordClient.with_typing_time_determined_by_number_of_words(
            message="While following your Path along The Way, you will be challenged to rise through the ranks:",
            channel=user_channel,
        )

        for rank_to_explain in Rank.all():
            rank_name = Rank.to_string_hum(rank_to_explain)
            rank_description = rank_to_explain.description()

            await DiscordClient.with_typing_time_determined_by_number_of_words(
                message=f"""`{rank_name}`: *{rank_description}*""",
                channel=user_channel,
            )

        await DiscordClient.with_typing_time_determined_by_number_of_words(
            message="Complete training missions to progress through the ranks",
            channel=user_channel,
        )

        await DiscordClient.with_typing_time_determined_by_number_of_words(
            message="Type `/train` to begin your first training mission",
            channel=user_channel,
        )

        await DiscordClient.with_typing_time_determined_by_number_of_words(
            message=f"""Ascend through the ranks {discord_member.mention}, a special prize waits for you at the end!""",
            channel=user_channel,
        )

        await self.sync_discord_role(for_user=new_user)

        return (new_user, user_channel)

    async def set_rank(self, for_user: User, rank: Rank):
        updated_user = await for_user.set_rank(rank, airtable_client=self.airtable_client)
        await self.sync_discord_role(for_user=updated_user)
        return updated_user

    async def delete_all_users(self) -> List[User]:
        users_to_delete = await User.rows(formula=None, airtable_client=self.airtable_client)
        _ = await User.delete_rows(users_to_delete, airtable_client=self.airtable_client)
        return users_to_delete

    async def delete_all_missions(self) -> List[Mission]:
        missions_to_delete = await Mission.rows(formula=None, airtable_client=self.airtable_client)
        _ = await Mission.delete_rows(missions_to_delete, airtable_client=self.airtable_client)
        return missions_to_delete

    async def delete_all_channels(
        self, except_for: FrozenSet[discord.TextChannel]
    ) -> List[discord.TextChannel]:
        channels_to_delete = await self.discord_client.channels()
        except_for = frozenset([channel.id for channel in except_for])
        channels_to_delete = [
            channel_to_delete
            for channel_to_delete in channels_to_delete
            if channel_to_delete.id not in except_for
        ]
        for channel_to_delete in channels_to_delete:
            _ = await channel_to_delete.delete()
        return channels_to_delete
