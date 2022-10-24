import discord


class DiscordClient:

    def __init__(self, guild_id: int, secret_token: str):
        self.client = discord.Client(intents = discord.Intents(messages=True,
                                                               guilds=True,
                                                               message_content=True,
                                                               members=True,
                                                               presences=True)) 
        self.guild_id = guild_id
        self.command_tree = discord.app_commands.CommandTree(self.client) 
        self.secret_token = secret_token

    @staticmethod
    async def __create_channel(member: discord.Member, channel_name: str):
        return await member.guild.create_text_channel(channel_name,
                                                      overwrites = {member.guild.default_role: discord.PermissionOverwrite(read_messages = False),
                                                                    member: discord.PermissionOverwrite(read_messages = True)})

    async def create_path_channel(self, member: discord.Member):
        return await self.__create_channel(member = member, channel_name = f'{member.name}s-path')
        
    async def create_mission_channel(self, member: discord.Member, question_id: str):
        return await self.__create_channel(member = member, channel_name = f'{member.name}-{question_id}')