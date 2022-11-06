import datetime

import discord

from discord_client import DiscordClient
from mission import Mission
from stage import Stage
from user import User


class Messenger:
    def __init__(self, *, discord_client: DiscordClient):
        self.__discord_client = discord_client

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
                name="-".join(
                    [
                        str(stage_submitted),
                        updated_mission.fields.discord_channel_id,
                        updated_mission.fields.question_id,
                    ]
                )
            )
            _ = await review_thread.send(f"""@everyone race to claim it!!""")
