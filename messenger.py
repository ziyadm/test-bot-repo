import datetime
from typing import Optional, Union

import discord

from discord_client import DiscordClient
from mission import Mission
from question import Question
from slash_command import SlashCommand
from stage import Stage
from user import User


class Messenger:

    command_acknowledged_by_suriel = "✅"

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

    # reviewer functions
    async def mission_rejected(
        self,
        player: User,
        player_channel: discord.TextChannel,
        review_channel: discord.TextChannel,
    ):
        _ = await player_channel.send(f"{player.mention} your work has been reviewed by Suriel\n\n")

        submit_command = await self.__discord_client.slash_command(
            SlashCommand(SlashCommand.submit)
        )
        await player_channel.send(
            f"Review the feedback and then use {submit_command.mention} once you've updated your work"
        )

        await review_channel.send("Sent review followups.")

    async def mission_approved(
        self,
        player: discord.Member,
        updated_mission: Mission,
        player_question_channel: discord.TextChannel,
        reviewer_question_channel: discord.TextChannel,
        player_path_channel: discord.TextChannel,
        score: float,
    ):
        # message reviewer
        response_to_reviewer = (
            "Approved question."
            if updated_mission.fields.stage.has_value(Stage.completed)
            else "Approved design."
        )
        await reviewer_question_channel.send(response_to_reviewer)

        # message player
        base_response_to_player = (
            "You completed this mission.\n"
            if updated_mission.fields.stage.has_value(Stage.completed)
            else "You completed the `Design` stage.\n"
        )

        submit_command = await self.__discord_client.slash_command(
            SlashCommand(SlashCommand.submit)
        )
        submit_next_step = (
            f"Head back to the doc and paste your code there\n\nThen use {submit_command.mention}"
        )
        next_step_for_player = (
            f"Head back to {player_path_channel.mention} to continue training."
            if updated_mission.fields.stage.has_value(Stage.completed)
            else submit_next_step
        )

        response_to_user = f"{player.mention} {base_response_to_player}\nScore: `{score}`\n\n{next_step_for_player}"

        await self.__discord_client.with_typing_time_determined_by_number_of_words(
            message=response_to_user,
            channel=player_question_channel,
            slowness_factor=3.0,
        )

    async def review_was_claimed(
        self,
        for_mission: Mission,
        for_question: Question,
        question_review_channel: discord.TextChannel,
        claim_review_thread: discord.TextChannel,
    ):
        player_submission = (
            for_mission.fields.design
            if for_mission.fields.stage.in_design()
            else for_mission.fields.code
        )

        await question_review_channel.send(
            f"Question: `{for_question.fields.description}`\nPlayer Submission: `{player_submission}`"
        )
        await claim_review_thread.send(f"Review claimed: {question_review_channel.mention}")

    # system functions
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

    async def player_is_out_of_time_for_mission(
        self, *, mission_past_due: Mission, expected_solution: str
    ):
        mission_channel = await self.__discord_client.channel(
            channel_id=mission_past_due.fields.discord_channel_id
        )
        _ = await self.__discord_client.with_typing_time_determined_by_number_of_words(
            "*Beep beep beep!*",
            mission_channel,
        )
        _ = await self.__discord_client.with_typing_time_determined_by_number_of_words(
            "**Times up!**", mission_channel
        )
        _ = await self.__discord_client.with_typing_time_determined_by_number_of_words(
            "Here's our solution:", mission_channel
        )
        _ = await self.__discord_client.with_typing_time_determined_by_number_of_words(
            f"""```{expected_solution}```""",
            mission_channel,
        )
        _ = await self.__discord_client.with_typing_time_determined_by_number_of_words(
            "We've added some more time to your timer, read and understand this solution then try to rewrite it yourself and submit!",
            mission_channel,
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

    # player functions
    async def player_completed_stage(
        self,
        user_to_update: User,
        question_channel: discord.TextChannel,
        path_channel: discord.TextChannel,
        set_rank_callback,
        **kwargs,
    ):
        level_delta = kwargs.get("level_delta", None)
        levels_until_evolution = kwargs.get("levels_until_evolution", None)
        current_rank = kwargs.get("current_rank", None)
        new_level = kwargs.get("new_level", None)
        evolving = kwargs.get("evolving", None)

        lost_levels = False
        if level_delta < 0:
            lost_levels = True

        level_change_blurb = "Sadly, you lost " if lost_levels else "You gained "

        await question_channel.send(
            f"Your work has been recognized by Suriel.\n\n{level_change_blurb} {level_delta} levels!\n\n"
        )

        if evolving:
            await question_channel.send("Wait...what's happening?")
            impressed_or_not = "not" if lost_levels else "slightly"
            await question_channel.send(f"Suriel is {impressed_or_not} impressed...")
            evolution_prefix = "DE-" if lost_levels else ""
            await question_channel.send(f"You are...{evolution_prefix}EVOLVING!")
            await set_rank_callback(for_user=user_to_update, rank=current_rank)
            await question_channel.send(
                "Suriel sees your strength - you have advanced to the next rank."
            )

        await question_channel.send(
            f"You are now a [{current_rank.capitalize()} lvl {new_level}].\n\nYou are now only {levels_until_evolution} levels from advancing to the next rank!"
        )

        ping_user_message = await path_channel.send("@everyone")
        await ping_user_message.delete()

    async def get_time_for_mission(
        self, time_remaining: str, where_to_follow_up: discord.TextChannel
    ):
        await where_to_follow_up.send(f"""{time_remaining} left.""")

    async def player_gave_up(
        self,
        player: discord.Member,
        mission_given_up: Mission,
        question: Question,
        where_to_follow_up: discord.TextChannel,
    ):
        # TODO: interaction.followup is weird
        # - it can't be used correctly with DiscordClient.with_.....
        # - we need to send a message directly to it
        await where_to_follow_up.send(
            f"""{player.mention} it is wise to pick your battles carefully...\n\n**study the solution well**: `{question.fields.code_solution}`"""
        )

    async def player_started_training_mission(
        self,
        player: discord.Member,
        channel: discord.TextChannel,
        where_to_follow_up: discord.TextChannel,
        guild_id: int,
        question_id: str,
        link: str,
    ):
        message = await where_to_follow_up.send(f"""Your mission awaits: {link}""")

        # There's a bug in discord.py that the owner won't fix.
        # https://github.com/Rapptz/discord.py/issues/9008
        message.guild = guild_id
        message_thread = await message.create_thread(name=f"{question_id}")
        await message_thread.add_user(player)

        _ = await DiscordClient.with_typing_time_determined_by_number_of_words(
            message="1) read the problem",
            channel=message_thread,
            slowness_factor=3.0,
        )
        _ = await DiscordClient.with_typing_time_determined_by_number_of_words(
            message="2) add a section for your design where you **EXPLAIN your solution in english**...",
            channel=message_thread,
            slowness_factor=3.0,
        )
        _ = await DiscordClient.with_typing_time_determined_by_number_of_words(
            message="...like you would *explain it to a coworker*...",
            channel=message_thread,
            slowness_factor=3.0,
        )
        submit_command = await self.__discord_client.slash_command(
            SlashCommand(SlashCommand.submit)
        )
        _ = await DiscordClient.with_typing_time_determined_by_number_of_words(
            message=f"3) type {submit_command.mention} to have your work reviewed",
            channel=message_thread,
            slowness_factor=3.0,
        )
        _ = await DiscordClient.with_typing_time_determined_by_number_of_words(
            message="...",
            channel=message_thread,
            slowness_factor=3.0,
        )
        _ = await DiscordClient.with_typing_time_determined_by_number_of_words(
            message="...**GO**...time is ticking...",
            channel=message_thread,
            slowness_factor=3.0,
        )

        return message_thread

    async def welcome_new_discord_member(
        self, *, discord_member: discord.Member, path_channel: discord.TextChannel
    ):
        _ = await DiscordClient.with_typing_time_determined_by_number_of_words(
            message=f"""Ascend through the ranks {discord_member.mention}, a special prize waits for you at the end...""",
            channel=path_channel,
        )

        train_command = await self.__discord_client.slash_command(SlashCommand(SlashCommand.train))
        await path_channel.send(f"Type {train_command.mention} to begin...")

    async def player_submitted_stage(
        self,
        player: User,
        updated_mission: Mission,
        stage_submitted: Stage,
        time_taken: datetime.timedelta,
        channel: discord.TextChannel,
        where_to_follow_up: discord.TextChannel,
    ):
        player_path_channel = await self.__discord_client.channel(
            channel_id=player.fields.discord_channel_id
        )

        if not stage_submitted.players_turn():
            raise Exception(
                "cant send messages for player submitting stage {stage_submitted} as its not their turn. this should already have been filtered out, is this a bug?"
            )

        await where_to_follow_up.send(f"""Only {time_taken}...not bad!""")
        _ = await self.__discord_client.with_typing_time_determined_by_number_of_words(
            message=f"Suriel is reviewing your {stage_submitted}",
            channel=channel,
        )
        _ = await self.__discord_client.with_typing_time_determined_by_number_of_words(
            message=f"""Head to {player_path_channel.mention} to continue training.""",
            channel=channel,
        )

        ping_user_message = await player_path_channel.send("@everyone")
        await ping_user_message.delete()

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
            # 2022-11-07 prointerviewschool: using @everyone in a thread only
            # pings everyone who is already in the thread, which is only people
            # who have been added manually by @mention or who have messaged in
            # the thread already. so we add all reviewers by @mentioning them
            # and then immediately deleting the message
            for reviewer in all_reviews_channel.members:
                message_to_add_reviewer_to_thread = await review_thread.send(
                    f"""{reviewer.mention}"""
                )
                _ = await message_to_add_reviewer_to_thread.delete()
            _ = await review_thread.send("""@everyone race to claim it!!""")
