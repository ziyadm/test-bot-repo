import discord


class DiscordClient:

    def __init__(self,
                 guild_id: str,
                 secret_token: str):
                     self.secret_token = secret_token
                     self.guild = discord.Object(id = guild_id)
                     self.client = discord.Client(intents = discord.Intents(messages=True,
                                                                            guilds=True,
                                                                            message_content=True,
                                                                            members=True,
                                                                            presences=True))
                     self.command_tree = discord.app_commands.CommandTree(self.client)

    # async def create_home_base(self,
    #                            discord_id: str,
    #                            discord_name: str):
    #                                roles = await self.discord_client.guild
    #                              overwrites = {
    #                                  member.guild.default_role: discord.PermissionOverwrite(read_messages = False),
    #                                  member: discord.PermissionOverwrite(read_messages=True)}
# 
    # channel_name = kwargs['channel_name'] if 'channel_name'in kwargs else member.name
    # return await member.guild.create_text_channel(channel_name, overwrites=overwrites)
        
        