from typing import Callable

import discord

from mission import Mission
from state import State
from user import User


class AdminCommandHandler:
    def __init__(self, *, state: State):
        self.__state = state

    async def wipe_state(
        self,
        *,
        interaction: discord.Interaction,
        users: bool,
        missions: bool,
        channels: bool,
        threads: bool,
        all_reviews_channel_messages: bool,
    ):
        all_reviews_channel = await self.__state.discord_client.all_reviews_channel()

        if users:
            _ = await all_reviews_channel.send(f"""deleting all users""")
            users_deleted = await self.__state.delete_all_users()
            users_deleted = len(users_deleted)
            _ = await all_reviews_channel.send(f"""deleted {users_deleted} users""")

        if missions:
            _ = await all_reviews_channel.send(f"""deleting all missions""")
            missions_deleted = await self.__state.delete_all_missions()
            missions_deleted = len(missions_deleted)
            _ = await all_reviews_channel.send(
                f"""deleted {missions_deleted} missions"""
            )

        if channels:
            _ = await all_reviews_channel.send(f"""deleting all channels""")
            channels_deleted = await self.__state.delete_all_channels(
                except_for=frozenset([all_reviews_channel])
            )
            channels_deleted = len(channels_deleted)
            _ = await all_reviews_channel.send(
                f"""deleted {channels_deleted} channels"""
            )

        if threads:
            _ = await all_reviews_channel.send(f"""deleting all threads""")
            threads_to_delete = all_reviews_channel.threads
            for thread_to_delete in threads_to_delete:
                _ = await thread_to_delete.delete()
            threads_deleted = len(threads_to_delete)
            _ = await all_reviews_channel.send(f"""deleted {threads_deleted} threads""")

        if all_reviews_channel_messages:
            _ = await all_reviews_channel.purge(limit=None)
