from typing import List

import discord
import pyairtable.formulas

import mission
import question
import user
from mission import Mission
from mission_status import MissionStatus
from question import Question
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
        current_user = await User.row(
            formula=pyairtable.formulas.match(
                {
                    user.Fields.discord_id_field: mission_to_update.fields.player_discord_id
                }
            ),
            airtable_client=self.state.airtable_client,
        )
        user_path_channel = await self.state.discord_client.client.fetch_channel(
            current_user.fields.discord_channel_id
        )

        reviewer_user = await self.state.discord_client.client.fetch_user(
            mission_to_update.fields.reviewer_discord_id
        )

        player_user = await self.state.discord_client.client.fetch_user(
            mission_to_update.fields.player_discord_id
        )

        await user_path_channel.send(
            f"{player_user.mention}\n\nType `/train` to continue..."
        )

        content_field = mission_to_update.get_content_field()
        response = f"""Planning is half the battle! We've sent your plan to Suriel for approval. Head back to {user_path_channel.mention} to continue training."""

        next_field = mission_to_update.fields.mission_status.next().get_field()
        if mission_to_update.fields.to_dict()[next_field]:
            # review is not new: it is a revision and we need to update the original reviewer
            original_review_channel = (
                await self.state.discord_client.client.fetch_channel(
                    mission_to_update.fields.review_discord_channel_id
                )
            )
            await original_review_channel.send(
                f"{reviewer_user.mention} the player has revised their work and resubmitted. Please review.\n\nContent: {messages[0].content}"
            )
        else:
            # review is new, we need to ping the reviews channel for this mission
            review_channel = await self.state.discord_client.review_channel()
            review_message = await review_channel.send(
                f"@everyone Ready for review: {interaction.channel.mention}"
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

    async def train_command(self, interaction: discord.Interaction):
        mission_to_update, mission_channel = await self.state.create_mission(
            player_discord_id=str(interaction.user.id)
        )

        mission_question = await Question.row(
            formula=pyairtable.formulas.match(
                {
                    question.Fields.question_id_field: mission_to_update.fields.question_id
                }
            ),
            airtable_client=self.state.airtable_client,
        )

        mission_message = await interaction.followup.send(
            f"""Monarch Suriel has invited you to {mission_channel.mention}"""
        )
        mission_message.guild = self.state.discord_client.guild_id

        # create the summary thread
        discord_user = await self.state.discord_client.client.fetch_user(
            str(interaction.user.id)
        )
        _ = await mission_message.create_thread(
            name=f"summary-{mission_question.fields.question_id}"
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

        user = await self.state.discord_client.client.fetch_user(
            mission_to_update.fields.player_discord_id
        )

        await question_channel.send(
            f"{user.mention} your work has been reviewed by Suriel\n\nSuriel's feedback: {review_value}"
        )
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

        base_response_to_user = (
            "Suriel approved of your work! Suriel left you the following to help you along your path"
            if mission_to_update.completing()
            else "Suriel approved your design. Continue along to coding."
        )
        response_to_user = (
            f"{base_response_to_user} \n Feedback: {review_value} \n Score: {score}"
        )

        await question_channel.send(response_to_user)
        if mission_to_update.completing():
            await self.handle_completing_question(mission_to_update, question_channel)
        return await interaction.followup.send(response)

    async def handle_completing_question(
        self, mission_to_update: mission.Mission, question_channel: discord.TextChannel
    ):
        (
            new_level,
            level_delta,
            levels_until_evolution,
            evolving,
            current_rank,
        ) = await mission_to_update.get_level_changes(self.state.airtable_client)

        await question_channel.send(
            f"Your work has been recognized by Suriel.\n\nYou gained {level_delta} levels!\n\n"
        )

        if evolving:
            user_to_update = await User.row(
                formula=pyairtable.formulas.match(
                    {
                        user.Fields.discord_id_field: mission_to_update.fields.player_discord_id
                    }
                ),
                airtable_client=self.state.airtable_client,
            )

            await question_channel.send("Wait...what's happening?")
            await question_channel.send("Suriel is slightly impressed...")
            await question_channel.send("You are...EVOLVING!")
            await self.state.set_rank(for_user=user_to_update, rank=current_rank)
            await question_channel.send(
                "Suriel sees your strength - you have advanced to the next rank."
            )

        await question_channel.send(
            f"You are now a [{current_rank.capitalize()} lvl {new_level}].\n\nYou are now only {levels_until_evolution} levels from advancing to the next rank!"
        )

    async def claim_command(self, interaction: discord.Interaction):
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

        user_to_update = await User.row(
            formula=pyairtable.formulas.match(
                {
                    user.Fields.discord_id_field: mission_to_update.fields.player_discord_id
                }
            ),
            airtable_client=self.state.airtable_client,
        )

        question_to_update = await Question.row(
            formula=pyairtable.formulas.match(
                {
                    question.Fields.question_id_field: mission_to_update.fields.question_id
                }
            ),
            airtable_client=self.state.airtable_client,
        )

        question_review_channel = await self.state.discord_client.create_private_channel(
            interaction.user.id,
            f"{mission_to_update.fields.mission_status.get_field()}-{mission_to_update.fields.question_id}-{user_to_update.fields.discord_name}",
        )
        content_field = mission_to_update.get_content_field()

        await question_review_channel.send(
            f"Question: {question_to_update.fields.leetcode_url}\n\nContent: {content_field}"
        )
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
            return await interaction.followup.send(
                "Send your work as a message before running `/submit`"
            )

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

    async def delete_inactive_channels(self, users_in_db: List[User]):
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
            active_user_channels
            + active_mission_channels
            + [self.state.discord_client.review_channel_id]
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
        bot_discord_id = str(self.state.discord_client.client.user.id)
        bot_discord_member = await self.state.discord_client.get_member(
            member_id=bot_discord_id
        )

        user_ids_in_db = [user_in_db.fields.discord_id for user_in_db in users_in_db]

        if bot_discord_id not in user_ids_in_db:
            _, bot_user = await self.state.create_user(
                discord_member=bot_discord_member
            )
            user_ids_in_db = [bot_discord_id] + user_ids_in_db

        synced_users = []
        for user_to_sync in users_in_discord:
            discord_id = str(user_to_sync.id)
            if discord_id not in user_ids_in_db:
                new_user, _user_channel = await self.state.create_user(
                    discord_member=user_to_sync
                )

                synced_users.append(new_user)

        return synced_users

    async def sync_db_and_discord(self, interaction: discord.Interaction):
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
        deleted_channels = await self.delete_inactive_channels(users_in_db=users_in_db)
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
