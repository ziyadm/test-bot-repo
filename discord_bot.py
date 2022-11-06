import os

import discord
import dotenv

from admin_command_handler import AdminCommandHandler
from airtable_client import AirtableClient
from command_handler import CommandHandler
from discord_client import DiscordClient
from event_handler import EventHandler
from state import State

dotenv.load_dotenv()
airtable_api_key = os.environ["airtable_api_key"]
airtable_database_id = os.environ["airtable_database_id"]
discord_guild_id = int(os.environ["discord_guild_id"])
discord_secret_token = os.environ["discord_secret_token"]

# TODO: update env variable name to match
discord_all_reviews_channel_id = os.environ["discord_all_reviews_channel_id"]

airtable_client = AirtableClient(api_key=airtable_api_key, base_id=airtable_database_id)
discord_client = DiscordClient(
    guild_id=discord_guild_id,
    secret_token=discord_secret_token,
    all_reviews_channel_id=discord_all_reviews_channel_id,
)
state = State(airtable_client, discord_client)
admin_command_handler = AdminCommandHandler(state=state)
command_handler = CommandHandler(state)
event_handler = EventHandler(state)

guild = discord.Object(id=discord_guild_id)


@discord_client.command_tree.command(
    name="time", description="[PLAYER] How much time remains?", guild=guild
)
async def register_time_command(interaction: discord.Interaction):
    await interaction.response.defer()
    return await command_handler.time_command(interaction)


@discord_client.command_tree.command(
    name="train", description="[PLAYER] Enter the training realm", guild=guild
)
async def register_train_command(interaction: discord.Interaction):
    await interaction.response.defer()
    return await command_handler.train_command(interaction)


@discord_client.command_tree.command(
    name="claim", description="[REVIEWER] Claim review of a mission", guild=guild
)
async def register_claim_command(interaction: discord.Interaction):
    await interaction.response.defer()
    return await command_handler.claim_command(interaction)


@discord_client.command_tree.command(
    name="review", description="[PLAYER] Submit review of a mission", guild=guild
)
async def register_review_command(interaction: discord.Interaction):
    await interaction.response.defer()
    return await command_handler.review_command(interaction)


@discord_client.command_tree.command(
    name="lgtm", description="[REVIEWER] Approve a mission", guild=guild
)
async def register_lgtm_command(interaction: discord.Interaction, score: float):
    await interaction.response.defer()
    return await command_handler.lgtm_command(interaction, score)


@discord_client.command_tree.command(
    name="submit",
    description="[PLAYER] Attempt to complete the current stage of a mission",
    guild=guild,
)
async def register_submit_command(interaction: discord.Interaction):
    await interaction.response.defer()
    return await command_handler.submit_command(interaction)


@discord_client.command_tree.command(
    name="set_rank", description="[ADMIN] Set a user's rank", guild=guild
)
async def register_set_rank_command(
    interaction: discord.Interaction, user_discord_name: str, rank: str
):
    await interaction.response.defer()
    return await command_handler.set_rank(
        interaction=interaction, user_discord_name=user_discord_name, rank=rank
    )


@discord_client.command_tree.command(
    name="wipe_state", description="[ADMIN] Wipe everything from the state", guild=guild
)
async def register_wipe_state_command(
    interaction: discord.Interaction,
    users: bool = True,
    missions: bool = True,
    channels: bool = True,
    threads: bool = True,
    all_reviews_channel_messages: bool = True,
):
    await interaction.response.defer()
    return await admin_command_handler.wipe_state(
        interaction=interaction,
        users=users,
        missions=missions,
        channels=channels,
        threads=threads,
        all_reviews_channel_messages=all_reviews_channel_messages,
    )


@discord_client.client.event
async def on_ready():
    return await event_handler.on_ready()


@discord_client.client.event
async def on_member_join(member):
    return await event_handler.on_member_join(member)


discord_client.client.run(discord_client.secret_token)
