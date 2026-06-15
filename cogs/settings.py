import discord
from discord.ext import commands
from discord import app_commands
from discord.app_commands import Choice
import database
import utils

class SettingsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    settings_group = app_commands.Group(name="settings", description="Guild configuration settings", default_permissions=discord.Permissions(administrator=True))
    permission_group = app_commands.Group(name="permission", description="Manage role permissions", parent=settings_group)

    @permission_group.command(name="add", description="Grant a permission to a role")
    @app_commands.choices(permission=[
        Choice(name="Manage Guides", value="manage_guides"),
        Choice(name="Manage Announcements", value="manage_announcements")
    ])
    async def add_permission(self, interaction: discord.Interaction, role: discord.Role, permission: Choice[str]):
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO role_permissions (guild_id, role_id, permission)
            VALUES (?, ?, ?)
        ''', (str(interaction.guild_id), str(role.id), permission.value))
        conn.commit()
        conn.close()
        await interaction.response.send_message(f"Granted `{permission.value}` to {role.mention}.", ephemeral=True)

    @permission_group.command(name="remove", description="Revoke a permission from a role")
    @app_commands.choices(permission=[
        Choice(name="Manage Guides", value="manage_guides"),
        Choice(name="Manage Announcements", value="manage_announcements")
    ])
    async def remove_permission(self, interaction: discord.Interaction, role: discord.Role, permission: Choice[str]):
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM role_permissions
            WHERE guild_id = ? AND role_id = ? AND permission = ?
        ''', (str(interaction.guild_id), str(role.id), permission.value))
        conn.commit()
        conn.close()
        await interaction.response.send_message(f"Revoked `{permission.value}` from {role.mention}.", ephemeral=True)

    @settings_group.command(name="reminder_channel", description="Set the channel for daily reset reminders")
    async def set_reminder_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO guild_config (guild_id, reminder_channel_id)
            VALUES (?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET reminder_channel_id=excluded.reminder_channel_id
        ''', (str(interaction.guild_id), str(channel.id)))
        conn.commit()
        conn.close()
        await interaction.response.send_message(f"Reminder channel set to {channel.mention}.", ephemeral=True)

    @settings_group.command(name="roster_channel", description="Set the channel for the live roster")
    async def set_roster_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO guild_config (guild_id, roster_channel_id)
            VALUES (?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET roster_channel_id=excluded.roster_channel_id
        ''', (str(interaction.guild_id), str(channel.id)))
        conn.commit()
        conn.close()
        await interaction.response.send_message(f"Roster channel set to {channel.mention}.", ephemeral=True)

    @settings_group.command(name="announcement_channel", description="Set the channel for guild announcements")
    async def set_announcement_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO guild_config (guild_id, announcement_channel_id)
            VALUES (?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET announcement_channel_id=excluded.announcement_channel_id
        ''', (str(interaction.guild_id), str(channel.id)))
        conn.commit()
        conn.close()
        await interaction.response.send_message(f"Announcement channel set to {channel.mention}.", ephemeral=True)

    @settings_group.command(name="reset_time", description="Set the daily reset time (HH:MM UTC)")
    async def set_reset_time(self, interaction: discord.Interaction, time_utc: str):
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO guild_config (guild_id, reset_time)
            VALUES (?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET reset_time=excluded.reset_time
        ''', (str(interaction.guild_id), time_utc))
        conn.commit()
        conn.close()
        await interaction.response.send_message(f"Reset time set to {time_utc} UTC.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(SettingsCog(bot))
