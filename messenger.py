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
        mission_discord_channel = await self.__discord_client.channel(
            channel_id=updated_mission.fields.discord_channel_id
        )

        if not stage_submitted.players_turn():
            raise Exception(
                "cant send messages for player submitting stage {stage_submitted} as its not their turn. this should already have been filtered out, is this a bug?"
            )

        if stage_submitted.has_value(Stage.design):
            await self.__discord_client.with_typing_time_determined_by_number_of_words(
                message=f"""Only {time_taken}...not bad!""",
                channel=mission_discord_channel,
            )
            await self.__discord_client.with_typing_time_determined_by_number_of_words(
                message="I've sent your plan to Suriel for approval.",
                channel=mission_discord_channel,
            )
            await self.__discord_client.with_typing_time_determined_by_number_of_words(
                message=f"""Head back to {player_path_channel.mention} to continue training.""",
                channel=mission_discord_channel,
            )
        elif stage_submitted.has_value(Stage.code):
            raise NotImplementedError("TODO: handle submitting code")
