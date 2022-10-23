from discord_client import DiscordClient
import events
import slash_commands

import os


discord_client = DiscordClient(guild_id = os.environ['discord_guild_id'],
                               secret_token = os.environ['discord_secret_token'])

# ================================
# === register slash commands ====
# ================================
@discord_client.command_tree.command(name="new",
                                     description="Get a new question",
                                     guild=discord_client.guild)
async def register_new_command(interaction):
  await interaction.response.defer()
  return await slash_commands.new_command(interaction)

@discord_client.command_tree.command(name="submit",
                                     description="Submit",
                                     guild=discord_client.guild)
async def register_submit_command(interaction):
  await interaction.response.defer()
  return await slash_commands.submit_command(interaction)

@discord_client.command_tree.command(name="delete",
                                     description="dete",
                                     guild=discord_client.guild)
async def register_delete_command(interaction):
  await interaction.response.defer()
  return await slash_commands.delete_command(interaction)

# ================================
# === register events ============
# ================================
@discord_client.client.event
async def on_ready():
    # when this process connects to the discord server
    await discord_client.command_tree.sync(guild = discord_client.guild)
    print(f'We have logged in as {discord_client.client.user}')
  
@discord_client.client.event
async def on_member_join(member):
    return await events.on_member_join_event(member)

@discord_client.client.event
async def on_presence_update(before, after):
    return await events.on_presence_update_event(before, after)

discord_client.client.run(discord_client.secret_token)
