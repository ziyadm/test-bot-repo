from airtable_client import AirtableClient
from discord_client import DiscordClient
from command_handler import CommandHandler
from event_handler import EventHandler

import discord
import os


airtable_api_key = os.environ['airtable_api_key']
airtable_database_id = os.environ['airtable_database_id']
discord_guild_id = int(os.environ['discord_guild_id'])
discord_secret_token = os.environ['discord_secret_token']

airtable_client = AirtableClient(api_key = airtable_api_key, base_id = airtable_database_id)
discord_client = DiscordClient(guild_id = discord_guild_id, secret_token = discord_secret_token)
command_handler = CommandHandler(airtable_client, discord_client)
event_handler = EventHandler(airtable_client, discord_client)

guild = discord.Object(id = discord_guild_id)

@discord_client.command_tree.command(name="new", description="Get a new question", guild=guild)
async def register_new_command(interaction: discord.Interaction):
    await interaction.response.defer()
    return await command_handler.new_command(interaction)

@discord_client.command_tree.command(
    name="submit", description="Attempt to complete the current stage of a mission", guild=guild)
async def register_submit_command(interaction: discord.Interaction):
  await interaction.response.defer()
  return await command_handler.submit_command(interaction)

@discord_client.command_tree.command(
    name = 'set_rank', description = """Set a user's rank""", guild = guild)
async def register_set_rank_command(interaction: discord.Interaction, user_discord_name: str, rank: str):
    await interaction.response.defer()
    return await command_handler.set_rank(
        interaction = interaction, user_discord_name = user_discord_name, rank = rank)

@discord_client.client.event
async def on_ready():
    return await event_handler.on_ready()
    
@discord_client.client.event
async def on_member_join(member):
    return await event_handler.on_member_join(member)

discord_client.client.run(discord_client.secret_token)