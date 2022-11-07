import datetime
from typing import Optional, Union

import discord

from discord_client import DiscordClient
from mission import Mission
from question import Question
from rank import Rank
from slash_command import SlashCommand
from stage import Stage
from user import User


class Messenger:
    def __init__(
        self,
        *,
        discord_client: DiscordClient,
    ):
        self.__discord_client = discord_client

    @staticmethod
    def review_thread_name(*, for_mission: Mission, for_stage: Stage):
        return "-".join(
            [
                str(for_stage),
                for_mission.fields.discord_channel_id,
                for_mission.fields.question_id,
            ]
        )

    async def player_is_out_of_questions(self, *, player: User):
        player_discord_member = await self.__discord_client.member(
            member_id=player.fields.discord_id
        )
        path_channel = await self.__discord_client.channel(
            channel_id=player.fields.discord_channel_id
        )
        guild_owner = await self.__discord_client.guild_owner()
        _ = await self.__discord_client.with_typing_time_determined_by_number_of_words(
            message=f"""Congrats {player_discord_member.mention}!! You've done every training mission we have to offer!""",
            channel=path_channel,
        )
        _ = await self.__discord_client.with_typing_time_determined_by_number_of_words(
            message=f"""Your time to meet {guild_owner.mention} has finally come...""",
            channel=path_channel,
        )

    async def player_is_out_of_time_for_mission(self, *, mission_past_due: Mission):
        mission_channel = await self.__discord_client.channel(
            channel_id=mission_past_due.fields.discord_channel_id
        )
        _ = await self.__discord_client.with_typing_time_determined_by_number_of_words(
            "*Beep beep beep!*", mission_channel
        )
        # TODO: give the player our expected solution if they run out of time
        _ = await self.__discord_client.with_typing_time_determined_by_number_of_words(
            "**Times up!**", mission_channel
        )

    async def review_needs_to_be_claimed(self, for_mission: Mission):
        all_reviews_channel = await self.__discord_client.all_reviews_channel()
        unclaimed_review_thread = list(
            filter(
                lambda thread: thread.name
                == self.review_thread_name(
                    for_mission=for_mission,
                    for_stage=for_mission.fields.stage.previous(),
                ),
                all_reviews_channel.threads,
            )
        )[0]
        _ = await unclaimed_review_thread.send("@everyone ping! race to claim this!!")

    async def reviewer_needs_to_review(self, for_mission: Mission):
        review_channel = await self.__discord_client.channel(
            channel_id=for_mission.fields.review_discord_channel_id
        )
        reviewer_discord_member = await self.__discord_client.member(
            member_id=for_mission.fields.reviewer_discord_id
        )
        _ = await review_channel.send(
            f"""{reviewer_discord_member.mention} dont leave them hanging, review this!!"""
        )

    async def command_cannot_be_run_here(
        self,
        where_to_follow_up: discord.Webhook,
        expected_location: Optional[Union[discord.Thread, discord.TextChannel]],
        suggested_command: Optional[SlashCommand],
    ):
        if expected_location is None:
            _ = await where_to_follow_up.send(("This command can't be used in this channel!"))
        else:
            _ = await where_to_follow_up.send(
                (f"""This command can only be used in {expected_location.mention}!""")
            )
        if suggested_command:
            suggested_command = await self.__discord_client.slash_command(suggested_command)
            _ = await where_to_follow_up.send(
                f"""Did you mean to try {suggested_command.mention}?"""
            )

    async def player_started_training_mission(
        self, player: User, training_mission: Mission, mission_question: Question
    ):
        discord_member = await self.__discord_client.member(member_id=player.fields.discord_id)
        mission_channel = await self.__discord_client.channel(
            channel_id=training_mission.fields.discord_channel_id
        )
        path_channel = await self.__discord_client.channel(
            channel_id=player.fields.discord_channel_id
        )
        mission_summary_thread_message = await path_channel.send(
            f"""Your training mission awaits you...head to {mission_channel.mention} to begin!"""
        )
        _ = await mission_summary_thread_message.create_thread(
            name=f"summary-{training_mission.fields.question_id}"
        )

        _ = await DiscordClient.with_typing_time_determined_by_number_of_words(
            message=f"""Welcome to your training mission {discord_member.mention}!""",
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
            message=f"""Good luck, {discord_member.mention}, you'll need it...""",
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

    async def welcome_new_discord_member(
        self, *, discord_member: discord.Member, path_channel: discord.TextChannel
    ):
        _ = await DiscordClient.with_typing_time_determined_by_number_of_words(
            message=f"""Suriel senses your weakness {discord_member.mention}""",
            channel=path_channel,
        )

        _ = await DiscordClient.with_typing_time_determined_by_number_of_words(
            message="Suriel invites you to follow The Way",
            channel=path_channel,
        )

        _ = await DiscordClient.with_typing_time_determined_by_number_of_words(
            message="While following your Path along The Way, you will be challenged to rise through the ranks:",
            channel=path_channel,
        )

        for rank_to_explain in Rank.all():
            rank_name = Rank.to_string_hum(rank_to_explain)
            rank_description = rank_to_explain.description()

            _ = await DiscordClient.with_typing_time_determined_by_number_of_words(
                message=f"""`{rank_name}`: *{rank_description}*""",
                channel=path_channel,
            )

        _ = await DiscordClient.with_typing_time_determined_by_number_of_words(
            message="Complete training missions to progress through the ranks",
            channel=path_channel,
        )

        _ = await DiscordClient.with_typing_time_determined_by_number_of_words(
            message="Type `/train` to begin your first training mission",
            channel=path_channel,
        )

        _ = await DiscordClient.with_typing_time_determined_by_number_of_words(
            message=f"""Ascend through the ranks {discord_member.mention}, a special prize waits for you at the end!""",
            channel=path_channel,
        )

    async def player_submitted_stage(
        self,
        player: User,
        updated_mission: Mission,
        stage_submitted: Stage,
        time_taken: datetime.timedelta,
    ):
        player_path_channel = await self.__discord_client.channel(
            channel_id=player.fields.discord_channel_id
        )
        mission_channel = await self.__discord_client.channel(
            channel_id=updated_mission.fields.discord_channel_id
        )

        if not stage_submitted.players_turn():
            raise Exception(
                "cant send messages for player submitting stage {stage_submitted} as its not their turn. this should already have been filtered out, is this a bug?"
            )

        _ = await self.__discord_client.with_typing_time_determined_by_number_of_words(
            message=f"""Only {time_taken}...not bad!""",
            channel=mission_channel,
        )
        _ = await self.__discord_client.with_typing_time_determined_by_number_of_words(
            message=f"I've sent your {stage_submitted} to Suriel for approval.",
            channel=mission_channel,
        )
        _ = await self.__discord_client.with_typing_time_determined_by_number_of_words(
            message=f"""Head back to {player_path_channel.mention} to continue training.""",
            channel=mission_channel,
        )

        if updated_mission.fields.review_discord_channel_id is not None:
            mission_review_channel = await self.__discord_client.channel(
                channel_id=updated_mission.fields.review_discord_channel_id
            )
            reviewer_discord_member = await self.__discord_client.member(
                member_id=updated_mission.fields.reviewer_discord_id
            )
            _ = await mission_review_channel.send(
                f"""{player.fields.discord_name} has revised and resubmitted their work. {reviewer_discord_member.mention} please review."""
            )
            _ = await mission_review_channel.send("New submission:")

            player_submission = None
            if stage_submitted.has_value(Stage.design):
                player_submission = updated_mission.fields.design
            else:
                player_submission = updated_mission.fields.code
            _ = await mission_review_channel.send(f"""```{player_submission}```""")
        else:
            all_reviews_channel = await self.__discord_client.all_reviews_channel()
            review_message = await all_reviews_channel.send(
                f"""{player.fields.discord_name} has submitted {stage_submitted} for {updated_mission.fields.question_id}"""
            )
            review_thread = await review_message.create_thread(
                name=self.review_thread_name(for_mission=updated_mission, for_stage=stage_submitted)
            )
            _ = await review_thread.send("""@everyone race to claim it!!""")
