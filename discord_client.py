from typing import List

import discord


class DiscordClient:
    
    default_permissions = discord.Permissions(
        read_messages = True,
        send_messages = True,
        create_instant_invite = True,
        read_message_history = True,
        use_application_commands = True) 
    
    admin_permissions = discord.Permissions.all

    def __init__(self, guild_id: int, secret_token: str):
        self.client = discord.Client(intents = discord.Intents(messages=True,
                                                               guilds=True,
                                                               message_content=True,
                                                               members=True,
                                                               presences=True)) 
        self.guild_id = guild_id
        self.command_tree = discord.app_commands.CommandTree(self.client) 
        self.secret_token = secret_token

    async def __guild(self):
        return await self.client.fetch_guild(self.guild_id)

    async def members(self):
        guild = await self.__guild()
        members = [member async for member in guild.fetch_members(limit = None)]
        return members

    async def channels(self):
        guild = await self.__guild()
        return await guild.fetch_channels()

    async def create_private_channel(self, member_id: str, channel_name: str):
        guild = await self.__guild()
        member = await guild.fetch_member(member_id)
        permission_overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages = False),
            member: discord.PermissionOverwrite(read_messages = True)}
        return await guild.create_text_channel(channel_name, overwrites = permission_overwrites)

    @staticmethod
    def __get_role(role_name: str, roles: List[discord.Role]):
        for role in roles:
            if role.name == role_name:
                return role

    async def set_role(self, member_id: str, role_name: str):
        guild = await self.__guild()
        member = await guild.fetch_member(member_id)
        
        old_roles = [role for role in member.roles if role != guild.default_role]
        new_role = self.__get_role(role_name, roles = guild.roles)

        if new_role.id not in [role.id for role in old_roles]:
            await member.add_roles(new_role)
            
            if len(old_roles) > 0:
                await member.remove_roles(*old_roles)

        await member.edit(nick = f"""[{role_name}] {member.name}""")

        return None