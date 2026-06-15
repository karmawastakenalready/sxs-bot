import discord
from discord.ext import commands
from discord import app_commands
import database
import config
import utils

class GuidesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    guide_group = app_commands.Group(name="guide", description="Guide management and retrieval")

    @guide_group.command(name="get", description="Get a guide for a specific topic")
    async def get_guide(self, interaction: discord.Interaction, topic: str):
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT url, description FROM guides WHERE topic COLLATE NOCASE = ?', (topic,))
        row = cursor.fetchone()
        conn.close()

        if row:
            url, desc = row
            embed = discord.Embed(title=f"Guide: {topic.capitalize()}", description=desc, url=url, color=discord.Color.gold())
            await interaction.response.send_message(embed=embed)
        else:
            msg = config.MESSAGES.get("guides", {}).get("not_found", "Guide not found for topic: `{topic}`.")
            await interaction.response.send_message(msg.format(topic=topic), ephemeral=True)

    @guide_group.command(name="list", description="List all available guide topics")
    async def list_guides(self, interaction: discord.Interaction):
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT topic FROM guides ORDER BY topic')
        topics = cursor.fetchall()
        conn.close()

        if not topics:
            await interaction.response.send_message("No guides available currently.", ephemeral=True)
            return

        topic_list = "\n".join([f"• {t[0]}" for t in topics])
        title = config.MESSAGES.get("guides", {}).get("list_title", "Available Guides")
        
        embed = discord.Embed(title=title, description=topic_list, color=discord.Color.gold())
        await interaction.response.send_message(embed=embed)

    @guide_group.command(name="add", description="Add or update a guide")
    async def add_guide(self, interaction: discord.Interaction, topic: str, url: str, description: str = ""):
        if not utils.has_permission(interaction, "manage_guides"):
            await interaction.response.send_message(config.MESSAGES.get("common", {}).get("error_no_permission", "No permission."), ephemeral=True)
            return

        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO guides (topic, url, description)
            VALUES (?, ?, ?)
            ON CONFLICT(topic) DO UPDATE SET url=excluded.url, description=excluded.description
        ''', (topic, url, description))
        conn.commit()
        conn.close()
        await interaction.response.send_message(f"Guide for `{topic}` has been saved.", ephemeral=True)

    @guide_group.command(name="remove", description="Remove a guide")
    async def remove_guide(self, interaction: discord.Interaction, topic: str):
        if not utils.has_permission(interaction, "manage_guides"):
            await interaction.response.send_message(config.MESSAGES.get("common", {}).get("error_no_permission", "No permission."), ephemeral=True)
            return

        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM guides WHERE topic COLLATE NOCASE = ?', (topic,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()

        if deleted:
            await interaction.response.send_message(f"Guide for `{topic}` has been removed.", ephemeral=True)
        else:
            await interaction.response.send_message(f"Guide `{topic}` not found.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(GuidesCog(bot))
