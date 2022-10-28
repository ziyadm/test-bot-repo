from typing import List

import mission
import user

from mission import Mission
from mission_status import MissionStatus
from rank import Rank
from state import State
from user import User

import discord
import pyairtable.formulas


class CommandHandler:

    def __init__(self, state: State):
        self.state = state

    async def new_command(self, interaction: discord.Interaction):
        _, mission_channel = await self.state.create_mission(player_discord_id = str(interaction.user.id))
        
        return await interaction.followup.send(
            f"""Monarch Suriel has invited you to {mission_channel.mention}""")

    async def submit_command(self, interaction: discord.Interaction):
        # CR hmir: only allow submit in mission channel
        # CR hmir: we probably wanna rename submit to fit the "mission"/"quest" theme
        mission_to_update = await Mission.row(
            formula = pyairtable.formulas.match({
                mission.Fields.discord_channel_id_field: str(interaction.channel_id)}),
            airtable_client = self.state.airtable_client)
    
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
            
        await mission_to_update.update(
            fields = mission_to_update.fields.immutable_updates({
                mission.Fields.mission_status_field: mission_to_update.fields.mission_status.next(),
                field_to_submit_contents_for: messages[0].content}),
            airtable_client = self.state.airtable_client)
        
        return await interaction.followup.send(response)

    async def set_rank(self, interaction: discord.Interaction, user_discord_name: str, rank: str):
        user_to_update = await User.row(
            formula = pyairtable.formulas.match({user.Fields.discord_name_field: user_discord_name}),
            airtable_client = self.state.airtable_client)

        await self.state.set_rank(for_user = user_to_update, rank = Rank.of_string(rank))
        
        return await interaction.followup.send(f"""Updated {user_discord_name}'s rank to {rank}""")

    async def delete_users_who_arent_in_discord(self, users_in_discord: List[discord.Member], users_in_db: List[User]):
        user_ids_in_discord = [str(user_in_discord.id) for user_in_discord in users_in_discord]
        
        users_to_delete = []
        for user_to_delete in users_in_db:
            if user_to_delete.fields.discord_id not in user_ids_in_discord:
                users_to_delete.append(user_to_delete)

        await User.delete_rows(users_to_delete, airtable_client = self.state.airtable_client)
                                                    
        return users_to_delete

    async def delete_missions_with_players_who_arent_in_discord(self, users_in_discord: List[discord.Member]):
        user_ids_in_discord = [str(user_in_discord.id) for user_in_discord in users_in_discord]
        missions_in_db = await Mission.rows(formula = None, airtable_client = self.state.airtable_client)
        
        missions_to_delete = []
        for mission_to_delete in missions_in_db:
            if mission_to_delete.fields.player_discord_id not in user_ids_in_discord:
                missions_to_delete.append(mission_to_delete)

        await Mission.delete_rows(missions_to_delete, airtable_client = self.state.airtable_client)

        return missions_to_delete

    async def delete_inactive_channels(self, reviewers_channel_id: str, users_in_db: List[User]):
        active_user_channels = [user_in_db.fields.discord_channel_id for user_in_db in users_in_db]
        
        missions = await Mission.rows(formula = None, airtable_client = self.state.airtable_client)
        active_mission_channels = [mission.fields.discord_channel_id for mission in missions]

        active_channels = set(active_user_channels + active_mission_channels + [reviewers_channel_id])

        channels = await self.state.discord_client.channels()
        
        deleted_channels = []
        for channel in channels:
            if str(channel.id) not in active_channels:
                deleted_channels.append(channel)
                await channel.delete()

        return deleted_channels

    async def sync_discord_users_to_db(self, users_in_discord: List[discord.Member], users_in_db: List[User]):
        user_ids_in_db = [user_in_db.fields.discord_id for user_in_db in users_in_db]
        
        synced_users = []
        for user_to_sync in users_in_discord:
            discord_id = str(user_to_sync.id)
            if discord_id not in user_ids_in_db:
                highest_rank_held_by_user = Rank(value = Rank.foundation)
                
                for role in user_to_sync.roles:
                    rank_held_by_user = Rank.of_string_hum(role.name)
                    if rank_held_by_user != None and rank_held_by_user > highest_rank_held_by_user:
                        highest_rank_held_by_user = rank_held_by_user

                new_user, _ = await self.state.create_user(
                    discord_id, discord_name = user_to_sync.name, rank = highest_rank_held_by_user)

                synced_users.append(new_user)

        return synced_users

    async def clean_up_state(self, interaction: discord.Interaction):
        users_in_discord = await self.state.discord_client.members()
        users_in_db = await User.rows(formula = None, airtable_client = self.state.airtable_client)
        
        await interaction.channel.send('Deleting users who arent in discord')
        deleted_users = await self.delete_users_who_arent_in_discord(users_in_discord, users_in_db)
        deleted_users = ', '.join([deleted_user.fields.discord_name for deleted_user in deleted_users])
        if len(deleted_users) > 0:
            await interaction.channel.send(f"""Deleted users: {deleted_users}""")

        await interaction.channel.send('Deleting missions with players who arent in discord')
        deleted_missions = await self.delete_missions_with_players_who_arent_in_discord(users_in_discord)
        deleted_missions = ', '.join(
            [deleted_mission.fields.discord_channel_id for deleted_mission in deleted_missions])
        if len(deleted_missions) > 0:
            await interaction.channel.send(f"""Deleted missions: {deleted_missions}""")

        await interaction.channel.send('Deleting inactive channels')
        deleted_channels = await self.delete_inactive_channels(
            reviewers_channel_id = str(interaction.channel.id), users_in_db = users_in_db)
        deleted_channels = ', '.join([str(deleted_channel.id) for deleted_channel in deleted_channels])
        if len(deleted_channels) > 0:
            await interaction.channel.send(f"""Deleted inactive channels: {deleted_channels}""")

        await interaction.channel.send('Syncing discord users to db')
        synced_users = await self.sync_discord_users_to_db(users_in_discord, users_in_db)
        synced_users = ', '.join(
            [synced_user.fields.discord_name for synced_user in synced_users])
        if len(deleted_channels) > 0:
            await interaction.channel.send(f"""Synced discord users: {synced_users}""")

        return await interaction.followup.send(f"""Finished""")