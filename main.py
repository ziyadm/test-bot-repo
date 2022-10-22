import discord
import os
from slash_commands import new_command, submit_command, delete_command
from events import on_member_join_event, on_presence_update_event

# ================================
# === setup discord connection ===
# ================================
intents = discord.Intents(messages=True, guilds=True, message_content=True, members=True, presences=True)
discord_client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(discord_client)

# ================================
# === constants ==
# ================================
# discord server id
discord_guild = discord.Object(id=os.environ['discord_guild_id'])

# ================================
# === register slash commands ====
# ================================
@tree.command(name="new",
              description="Get a new question",
              guild=discord_guild)
async def register_new_command(interaction):
  await interaction.response.defer()
  return await new_command(interaction)

@tree.command(name="submit",
              description="Submit",
              guild=discord_guild)
async def register_submit_command(interaction):
  await interaction.response.defer()
  return await submit_command(interaction)

@tree.command(name="delete",
              description="dete",
              guild=discord_guild)
async def register_delete_command(interaction):
  await interaction.response.defer()
  return await delete_command(interaction)

# ================================
# === register events ============
# ================================
@discord_client.event
async def on_ready():
    # when this process connects to the discord server
    await tree.sync(guild=discord_guild)
    print(f'We have logged in as {discord_client.user}')
  
@discord_client.event
async def on_member_join(member):
    return await on_member_join_event(member)

@discord_client.event
async def on_presence_update(before, after):
    return await on_presence_update_event(before, after)

discord_client.run(os.environ['discord_secret_token'])
