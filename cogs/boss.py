import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import database
import config

class BossCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="bossdone", description="Mark yourself as having completed the guild boss today")
    async def bossdone(self, interaction: discord.Interaction):
        conn = database.get_connection()
        cursor = conn.cursor()
        
        # Check if linked
        cursor.execute('SELECT ingame_username FROM users WHERE discord_id = ?', (str(interaction.user.id),))
        user_row = cursor.fetchone()
        if not user_row:
            msg = config.MESSAGES.get("common", {}).get("error_not_linked", "Not linked.")
            await interaction.response.send_message(msg, ephemeral=True)
            conn.close()
            return

        today = datetime.utcnow().date().isoformat()
        cursor.execute('''
            INSERT INTO boss_tracker (discord_id, date_completed)
            VALUES (?, ?)
            ON CONFLICT(discord_id) DO UPDATE SET date_completed=excluded.date_completed
        ''', (str(interaction.user.id), today))
        conn.commit()
        conn.close()

        msg = config.MESSAGES.get("boss", {}).get("mark_done", "Marked done!")
        await interaction.response.send_message(msg, ephemeral=True)

    @app_commands.command(name="bossstatus", description="Show who has completed the guild boss today")
    async def bossstatus(self, interaction: discord.Interaction):
        conn = database.get_connection()
        cursor = conn.cursor()
        
        today = datetime.utcnow().date().isoformat()
        
        # Get all linked users
        cursor.execute('SELECT discord_id, ingame_username FROM users')
        all_users = cursor.fetchall()
        
        # Get users who completed today
        cursor.execute('SELECT discord_id FROM boss_tracker WHERE date_completed = ?', (today,))
        done_ids = {row[0] for row in cursor.fetchall()}
        conn.close()

        done_users = []
        pending_users = []

        for discord_id, username in all_users:
            if discord_id in done_ids:
                done_users.append(username)
            else:
                pending_users.append(username)

        title = config.MESSAGES.get("boss", {}).get("status_title", "Guild Boss Status")
        
        done_format = config.MESSAGES.get("boss", {}).get("done_list", "**Completed ({done_count}):**\n{done_members}")
        pending_format = config.MESSAGES.get("boss", {}).get("pending_list", "**Pending ({pending_count}):**\n{pending_members}")

        done_text = done_format.format(done_count=len(done_users), done_members=", ".join(done_users) or "None")
        pending_text = pending_format.format(pending_count=len(pending_users), pending_members=", ".join(pending_users) or "None")

        embed = discord.Embed(title=title, description=f"{done_text}\n\n{pending_text}", color=discord.Color.red())
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(BossCog(bot))
