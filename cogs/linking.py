import discord
from discord.ext import commands
from discord import app_commands
from discord.app_commands import Choice
import database
import config
from cogs.roster import update_roster_message

CLASS_ROLES = {
    "Duelist": 1515878498450018354,
    "Knight": 1515878622802481223,
    "Sorcerer": 1515878672031285308,
    "Sage": 1515878789526327426
}

async def update_user_roles(interaction: discord.Interaction, new_class: str = None):
    if not isinstance(interaction.user, discord.Member) or not interaction.guild:
        return
        
    roles_to_remove = []
    role_to_add = None
    
    for class_name, role_id in CLASS_ROLES.items():
        role = interaction.guild.get_role(role_id)
        if not role:
            continue
            
        if class_name == new_class:
            role_to_add = role
        elif role in interaction.user.roles:
            roles_to_remove.append(role)
            
    try:
        if roles_to_remove:
            await interaction.user.remove_roles(*roles_to_remove)
        if role_to_add and role_to_add not in interaction.user.roles:
            await interaction.user.add_roles(role_to_add)
    except discord.Forbidden:
        pass

class LinkingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="link", description="Link your Discord account to your in-game username and class")
    @app_commands.choices(game_class=[
        Choice(name="Duelist", value="Duelist"),
        Choice(name="Knight", value="Knight"),
        Choice(name="Sorcerer", value="Sorcerer"),
        Choice(name="Sage", value="Sage")
    ])
    async def link(self, interaction: discord.Interaction, ingame_username: str, game_class: Choice[str]):
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (discord_id, ingame_username, game_class)
            VALUES (?, ?, ?)
            ON CONFLICT(discord_id) DO UPDATE SET 
                ingame_username=excluded.ingame_username,
                game_class=excluded.game_class
        ''', (str(interaction.user.id), ingame_username, game_class.value))
        conn.commit()
        conn.close()

        msg = config.MESSAGES.get("linking", {}).get("link_success", "Linked as {username} ({class_name})")
        await interaction.response.send_message(msg.format(username=ingame_username, class_name=game_class.value), ephemeral=True)
        
        await update_user_roles(interaction, game_class.value)
        
        if interaction.guild_id:
            await update_roster_message(self.bot, interaction.guild_id)

    @app_commands.command(name="unlink", description="Remove your linked in-game info")
    async def unlink(self, interaction: discord.Interaction):
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users WHERE discord_id = ?', (str(interaction.user.id),))
        conn.commit()
        conn.close()

        msg = config.MESSAGES.get("linking", {}).get("unlink_success", "Unlinked.")
        await interaction.response.send_message(msg, ephemeral=True)
        
        await update_user_roles(interaction, None)
        
        if interaction.guild_id:
            await update_roster_message(self.bot, interaction.guild_id)

    @app_commands.command(name="whoami", description="Check your currently linked info")
    async def whoami(self, interaction: discord.Interaction):
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT ingame_username, game_class FROM users WHERE discord_id = ?', (str(interaction.user.id),))
        row = cursor.fetchone()
        conn.close()

        if row:
            msg = config.MESSAGES.get("linking", {}).get("whoami_info", "You are {username} ({class_name})")
            await interaction.response.send_message(msg.format(username=row[0], class_name=row[1]), ephemeral=True)
        else:
            msg = config.MESSAGES.get("common", {}).get("error_not_linked", "Not linked.")
            await interaction.response.send_message(msg, ephemeral=True)

    @app_commands.command(name="lookup", description="Look up someone else's linked info")
    @app_commands.default_permissions(manage_messages=True)
    async def lookup(self, interaction: discord.Interaction, user: discord.Member):
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT ingame_username, game_class FROM users WHERE discord_id = ?', (str(user.id),))
        row = cursor.fetchone()
        conn.close()

        if row:
            msg = config.MESSAGES.get("linking", {}).get("lookup_info", "{user_id} is {username} ({class_name})")
            await interaction.response.send_message(msg.format(user_id=user.id, username=row[0], class_name=row[1]), ephemeral=True)
        else:
            msg = config.MESSAGES.get("linking", {}).get("lookup_fail", "{user_id} is not linked")
            await interaction.response.send_message(msg.format(user_id=user.id), ephemeral=True)

async def setup(bot):
    await bot.add_cog(LinkingCog(bot))
