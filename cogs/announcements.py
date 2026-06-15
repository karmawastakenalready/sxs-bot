import discord
from discord.ext import commands
from discord import app_commands
import database
import config
import utils

class AnnouncementsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    announcement_group = app_commands.Group(name="announcement", description="Guild announcement management")

    @announcement_group.command(name="set", description="Set or update the guild announcement")
    async def set_announcement(self, interaction: discord.Interaction, text: str):
        if not utils.has_permission(interaction, "manage_announcements"):
            msg = config.MESSAGES.get("common", {}).get("error_no_permission", "No permission.")
            await interaction.response.send_message(msg, ephemeral=True)
            return

        conn = database.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT announcement_channel_id, announcement_message_id FROM guild_config WHERE guild_id = ?', (str(interaction.guild_id),))
        row = cursor.fetchone()
        
        channel_id = row[0] if row else None
        message_id = row[1] if row else None

        title = config.MESSAGES.get("announcements", {}).get("current_title", "Guild Announcement")
        embed = discord.Embed(title=title, description=text, color=discord.Color.blue())

        channel = None
        if channel_id:
            channel = interaction.guild.get_channel(int(channel_id))
            
        if channel:
            message_sent = False
            if message_id:
                try:
                    msg_obj = await channel.fetch_message(int(message_id))
                    await msg_obj.edit(embed=embed)
                    message_sent = True
                except discord.NotFound:
                    pass
            
            if not message_sent:
                new_msg = await channel.send(embed=embed)
                message_id = str(new_msg.id)
                cursor.execute('''
                    INSERT INTO guild_config (guild_id, announcement_message_id)
                    VALUES (?, ?)
                    ON CONFLICT(guild_id) DO UPDATE SET announcement_message_id=excluded.announcement_message_id
                ''', (str(interaction.guild_id), message_id))

        cursor.execute('''
            INSERT INTO guild_config (guild_id, announcement_text)
            VALUES (?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET announcement_text=excluded.announcement_text
        ''', (str(interaction.guild_id), text))
        
        conn.commit()
        conn.close()

        msg = config.MESSAGES.get("announcements", {}).get("set_success", "Announcement updated.")
        await interaction.response.send_message(msg, ephemeral=True)

    @announcement_group.command(name="view", description="View the current guild announcement")
    async def view_announcement(self, interaction: discord.Interaction):
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT announcement_text FROM guild_config WHERE guild_id = ?', (str(interaction.guild_id),))
        row = cursor.fetchone()
        conn.close()

        text = row[0] if row and row[0] else "No announcement set."
        title = config.MESSAGES.get("announcements", {}).get("current_title", "Guild Announcement")
        
        embed = discord.Embed(title=title, description=text, color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(AnnouncementsCog(bot))
