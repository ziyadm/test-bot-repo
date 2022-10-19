from airtable_client import AirtableClient
from discord_client import DiscordClient
from command_handler import CommandHandler
from event_handler import EventHandler
from dotenv import load_dotenv
from state import State

import discord
import os


load_dotenv()
airtable_api_key = os.environ["airtable_api_key"]
airtable_database_id = os.environ["airtable_database_id"]
discord_guild_id = int(os.environ["discord_guild_id"])
discord_secret_token = os.environ["discord_secret_token"]

airtable_client = AirtableClient(api_key=airtable_api_key, base_id=airtable_database_id)
discord_client = DiscordClient(
    guild_id=discord_guild_id, secret_token=discord_secret_token
)
state = State(airtable_client, discord_client)
command_handler = CommandHandler(state)
event_handler = EventHandler(state)

guild = discord.Object(id=discord_guild_id)


@discord_client.command_tree.command(
    name="new", description="Get a new question", guild=guild
)
async def register_new_command(interaction: discord.Interaction):
    await interaction.response.defer()
    return await command_handler.new_command(interaction)


@discord_client.command_tree.command(
    name="review", description="Review a mission", guild=guild
)
async def register_review_command(interaction: discord.Interaction):
    await interaction.response.defer()
    return await command_handler.review_command(interaction)


@discord_client.command_tree.command(
    name="submit",
    description="Attempt to complete the current stage of a mission",
    guild=guild,
)
async def register_submit_command(interaction: discord.Interaction):
    await interaction.response.defer()
    return await command_handler.submit_command(interaction)


# TODO prointerviewschool: permissions for this command
@discord_client.command_tree.command(
    name="set_rank", description="""Set a user's rank""", guild=guild
)
async def register_set_rank_command(
    interaction: discord.Interaction, user_discord_name: str, rank: str
):
    await interaction.response.defer()
    return await command_handler.set_rank(
        interaction=interaction, user_discord_name=user_discord_name, rank=rank
    )


# TODO prointerviewschool: permissions for this command
# TODO ziyadm: filter out monarchs (higher rank than bot)
@discord_client.command_tree.command(
    name="clean_up_state", description="""Clean up the db and discord""", guild=guild
)
async def register_clean_up_state_command(interaction: discord.Interaction):
    await interaction.response.defer()
    return await command_handler.clean_up_state(interaction)


@discord_client.client.event
async def on_ready():
    return await event_handler.on_ready()


@discord_client.client.event
async def on_member_join(member):
    return await event_handler.on_member_join(member)


discord_client.client.run(discord_client.secret_token)
