from typing import List

import discord
import pyairtable.formulas

import mission
import user
from mission import Mission
from mission_status import MissionStatus
from rank import Rank
from state import State
from user import User


class CommandHandler:
    def __init__(self, state: State):
        self.state = state

    async def get_mission(self, field: mission.Fields, value: str):
        return await Mission.row(
            formula=pyairtable.formulas.match({field: value}),
            airtable_client=self.state.airtable_client,
        )

    async def handle_submission(self, interaction, mission_to_update, messages):
        content_field = mission_to_update.get_content_field()
        response = """Planning is half the battle! We've sent your plan to Monarch Suriel for approval. Check back in about 30 minutes to find out your next objective."""

        next_field = mission_to_update.fields.mission_status.next().get_field()
        if mission_to_update.fields.to_dict()[next_field]:
            # review is not new: it is a revision and we need to update the original reviewer
            original_review_channel = (
                await self.state.discord_client.client.fetch_channel(
                    mission_to_update.fields.review_discord_channel_id
                )
            )
            await original_review_channel.send(
                f"Followup for review: {messages[0].content}"
            )
        else:
            # review is new, we need to ping the reviews channel for this mission
            review_channel = await self.state.discord_client.review_channel()
            review_message = await review_channel.send(
                f"Ready for review: {interaction.channel.mention}"
            )
            _ = await review_message.create_thread(
                name=f"review-{interaction.channel.mention}"
            )

        await mission_to_update.update(
            fields=mission_to_update.fields.immutable_updates(
                {
                    mission.Fields.mission_status_field: mission_to_update.fields.mission_status.next(),
                    content_field: messages[0].content,
                }
            ),
            airtable_client=self.state.airtable_client,
        )

        return response

    async def new_command(self, interaction: discord.Interaction):
        _, mission_channel = await self.state.create_mission(
            player_discord_id=str(interaction.user.id)
        )

        return await interaction.followup.send(
            f"""Monarch Suriel has invited you to {mission_channel.mention}"""
        )

    async def review_command(self, interaction: discord.Interaction):
        mission_to_update = await self.get_mission(
            field=mission.Fields.review_discord_channel_id_field,
            value=str(interaction.channel_id),
        )

        if not mission_to_update.in_review():
            return await interaction.followup.send("""Review already completed!""")

        review_field, review_value = await mission_to_update.get_review_values(
            interaction
        )

        state_field = mission.Fields.mission_status_field
        state_value = mission_to_update.fields.mission_status.previous()

        await mission_to_update.update(
            fields=mission_to_update.fields.immutable_updates(
                {
                    review_field: review_value,
                    state_field: state_value,
                }
            ),
            airtable_client=self.state.airtable_client,
        )

        response = "Sent review followups."

        question_channel = await self.state.discord_client.client.fetch_channel(
            mission_to_update.fields.discord_channel_id
        )

        await question_channel.send(f"Feedback: {review_value}")
        return await interaction.followup.send(response)

    async def lgtm_command(self, interaction: discord.Interaction, score: float):
        mission_to_update = await self.get_mission(
            field=mission.Fields.review_discord_channel_id_field,
            value=str(interaction.channel_id),
        )

        if not mission_to_update.in_review():
            return await interaction.followup.send("""LGTM already provided!""")

        review_field, review_value = await mission_to_update.get_review_values(
            interaction
        )

        state_field = mission.Fields.mission_status_field
        state_value = mission_to_update.fields.mission_status.next()

        score_field = (
            mission.Fields.code_score_field
            if mission_to_update.completing()
            else mission.Fields.design_score_field
        )

        await mission_to_update.update(
            fields=mission_to_update.fields.immutable_updates(
                {
                    review_field: review_value,
                    state_field: state_value,
                    score_field: score,
                }
            ),
            airtable_client=self.state.airtable_client,
        )

        response = (
            "Approved question."
            if mission_to_update.completing()
            else "Approved design."
        )

        question_channel = await self.state.discord_client.client.fetch_channel(
            mission_to_update.fields.discord_channel_id
        )

        # TODO add hook to calculate updated score and update rank if necessary
        # if mission_to_update.completing()

        base_response_to_user = (
            "Suriel approved of your work! Suriel left you the following to help you along your path"
            if mission_to_update.completing()
            else "Suriel approved your design. Continue along to coding."
        )
        response_to_user = (
            f"{base_response_to_user} \n Feedback: {review_value} \n Score: {score}"
        )

        await question_channel.send(response_to_user)
        return await interaction.followup.send(response)

    async def claim_command(self, interaction: discord.Interaction):
        # TODO ziyadm: only allow in mission channel -> maybe decorator for commands that limit
        question_discord_channel_id = str(interaction.channel.name.split("review-")[-1])
        mission_to_update = await self.get_mission(
            field=mission.Fields.discord_channel_id_field,
            value=question_discord_channel_id,
        )

        mission_to_update = await Mission.row(
            formula=pyairtable.formulas.match(
                {mission.Fields.discord_channel_id_field: question_discord_channel_id}
            ),
            airtable_client=self.state.airtable_client,
        )

        if not mission_to_update.in_review():
            return await interaction.followup.send("""Review already claimed!""")

        question_review_channel = (
            await self.state.discord_client.create_private_channel(
                interaction.user.id, f"review-{mission_to_update.fields.question_id}"
            )
        )
        content_field = mission_to_update.get_content_field()

        await question_review_channel.send(content_field)
        response = f"Review claimed: {question_review_channel.mention}"

        await mission_to_update.update(
            fields=mission_to_update.fields.immutable_updates(
                {
                    mission.Fields.review_discord_channel_id_field: str(
                        question_review_channel.id
                    ),
                    mission.Fields.reviewer_discord_id_field: interaction.user.id,
                }
            ),
            airtable_client=self.state.airtable_client,
        )

        return await interaction.followup.send(response)

    async def submit_command(self, interaction: discord.Interaction):
        # TODO prointerviewschool: only allow submit in mission channel
        # TODO prointerviewschool: we probably wanna rename submit to fit the "mission"/"quest" theme
        mission_to_update = await self.get_mission(
            field=mission.Fields.discord_channel_id_field,
            value=str(interaction.channel.id),
        )

        if not (
            mission_to_update.fields.mission_status.has_value(MissionStatus.design)
            or mission_to_update.fields.mission_status.has_value(MissionStatus.code)
        ):
            return await interaction.followup.send(
                """You've completed your objective, wait for Monarch Suriel's instructions!"""
            )

        messages = await Mission.get_messages(interaction)
        if len(messages) == 0:
            # TODO prointerviewschool: maybe we can frame missions as you having "minions" who you have to give instructions to to solve some problems you come across in your journey?
            # alternatively it could be framed as being a world of machines and you need to make the machines do what you want. i think theres a pretty popular recent game thats similar to this
            # follow up with ziyad
            return await interaction.followup.send("You need to instruct your minions!")

        response = await self.handle_submission(
            interaction, mission_to_update, messages
        )

        return await interaction.followup.send(response)

    async def set_rank(
        self, interaction: discord.Interaction, user_discord_name: str, rank: str
    ):
        user_to_update = await User.row(
            formula=pyairtable.formulas.match(
                {user.Fields.discord_name_field: user_discord_name}
            ),
            airtable_client=self.state.airtable_client,
        )

        await self.state.set_rank(for_user=user_to_update, rank=Rank.of_string(rank))

        return await interaction.followup.send(
            f"""Updated {user_discord_name}'s rank to {rank}"""
        )

    async def delete_users_who_arent_in_discord(
        self, users_in_discord: List[discord.Member], users_in_db: List[User]
    ):
        user_ids_in_discord = [
            str(user_in_discord.id) for user_in_discord in users_in_discord
        ]

        users_to_delete = []
        for user_to_delete in users_in_db:
            if user_to_delete.fields.discord_id not in user_ids_in_discord:
                users_to_delete.append(user_to_delete)

        await User.delete_rows(
            users_to_delete, airtable_client=self.state.airtable_client
        )

        return users_to_delete

    async def delete_missions_with_players_who_arent_in_discord(
        self, users_in_discord: List[discord.Member]
    ):
        user_ids_in_discord = [
            str(user_in_discord.id) for user_in_discord in users_in_discord
        ]
        missions_in_db = await Mission.rows(
            formula=None, airtable_client=self.state.airtable_client
        )

        missions_to_delete = []
        for mission_to_delete in missions_in_db:
            if mission_to_delete.fields.player_discord_id not in user_ids_in_discord:
                missions_to_delete.append(mission_to_delete)

        await Mission.delete_rows(
            missions_to_delete, airtable_client=self.state.airtable_client
        )

        return missions_to_delete

    async def delete_inactive_channels(
        self, reviewers_channel_id: str, users_in_db: List[User]
    ):
        active_user_channels = [
            user_in_db.fields.discord_channel_id for user_in_db in users_in_db
        ]

        missions = await Mission.rows(
            formula=None, airtable_client=self.state.airtable_client
        )
        active_mission_channels = [
            mission.fields.discord_channel_id for mission in missions
        ]

        active_channels = set(
            active_user_channels + active_mission_channels + [reviewers_channel_id]
        )

        channels = await self.state.discord_client.channels()

        deleted_channels = []
        for channel in channels:
            if str(channel.id) not in active_channels:
                deleted_channels.append(channel)
                await channel.delete()

        return deleted_channels

    async def sync_discord_users_to_db(
        self, users_in_discord: List[discord.Member], users_in_db: List[User]
    ):
        user_ids_in_db = [user_in_db.fields.discord_id for user_in_db in users_in_db]

        synced_users = []
        for user_to_sync in users_in_discord:
            discord_id = str(user_to_sync.id)
            if discord_id not in user_ids_in_db:
                highest_rank_held_by_user = Rank(value=Rank.foundation)

                for role in user_to_sync.roles:
                    rank_held_by_user = Rank.of_string_hum(role.name)
                    if (
                        rank_held_by_user is not None
                        and rank_held_by_user > highest_rank_held_by_user
                    ):
                        highest_rank_held_by_user = rank_held_by_user

                new_user, _ = await self.state.create_user(
                    discord_id,
                    discord_name=user_to_sync.name,
                    rank=highest_rank_held_by_user,
                )

                synced_users.append(new_user)

        return synced_users

    # TODO prointerviewschool: dont do anything with anyone with a higher rank than the bot
    # TODO prointerviewschool: dont delete the review channel
    async def clean_up_state(self, interaction: discord.Interaction):
        users_in_discord = await self.state.discord_client.members()
        users_in_db = await User.rows(
            formula=None, airtable_client=self.state.airtable_client
        )

        await interaction.channel.send("Deleting users who arent in discord")
        deleted_users = await self.delete_users_who_arent_in_discord(
            users_in_discord, users_in_db
        )
        deleted_users = ", ".join(
            [deleted_user.fields.discord_name for deleted_user in deleted_users]
        )
        if len(deleted_users) > 0:
            await interaction.channel.send(f"""Deleted users: {deleted_users}""")

        await interaction.channel.send(
            "Deleting missions with players who arent in discord"
        )
        deleted_missions = await self.delete_missions_with_players_who_arent_in_discord(
            users_in_discord
        )
        deleted_missions = ", ".join(
            [
                deleted_mission.fields.discord_channel_id
                for deleted_mission in deleted_missions
            ]
        )
        if len(deleted_missions) > 0:
            await interaction.channel.send(f"""Deleted missions: {deleted_missions}""")

        await interaction.channel.send("Deleting inactive channels")
        deleted_channels = await self.delete_inactive_channels(
            reviewers_channel_id=str(interaction.channel.id), users_in_db=users_in_db
        )
        deleted_channels = ", ".join(
            [str(deleted_channel.id) for deleted_channel in deleted_channels]
        )
        if len(deleted_channels) > 0:
            await interaction.channel.send(
                f"""Deleted inactive channels: {deleted_channels}"""
            )

        await interaction.channel.send("Syncing discord users to db")
        synced_users = await self.sync_discord_users_to_db(
            users_in_discord, users_in_db
        )
        synced_users = ", ".join(
            [synced_user.fields.discord_name for synced_user in synced_users]
        )
        if len(deleted_channels) > 0:
            await interaction.channel.send(f"""Synced discord users: {synced_users}""")

        return await interaction.followup.send("""Finished""")
