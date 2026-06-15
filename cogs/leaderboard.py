import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import database
import config

class LeaderboardCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def parse_power(self, power_str: str) -> int:
        power_str = power_str.upper().replace(',', '').strip()
        multiplier = 1
        if power_str.endswith('K'):
            multiplier = 1000
            power_str = power_str[:-1]
        elif power_str.endswith('M'):
            multiplier = 1000000
            power_str = power_str[:-1]
        elif power_str.endswith('B'):
            multiplier = 1000000000
            power_str = power_str[:-1]
            
        try:
            return int(float(power_str) * multiplier)
        except ValueError:
            return 0

    @app_commands.command(name="power", description="Set your current power level")
    async def power(self, interaction: discord.Interaction, amount: str):
        power_int = self.parse_power(amount)
        if power_int <= 0:
            await interaction.response.send_message("Invalid power level format. Use numbers optionally with K/M/B (e.g. 1.5M).", ephemeral=True)
            return

        conn = database.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT ingame_username FROM users WHERE discord_id = ?', (str(interaction.user.id),))
        if not cursor.fetchone():
            msg = config.MESSAGES.get("common", {}).get("error_not_linked", "Not linked.")
            await interaction.response.send_message(msg, ephemeral=True)
            conn.close()
            return

        now = datetime.utcnow().isoformat()
        cursor.execute('''
            UPDATE users 
            SET power = ?, power_updated_at = ?
            WHERE discord_id = ?
        ''', (power_int, now, str(interaction.user.id)))
        conn.commit()
        conn.close()

        msg = config.MESSAGES.get("leaderboard", {}).get("set_success", "Power level set to **{power}**.").format(power=f"{power_int:,}")
        await interaction.response.send_message(msg, ephemeral=True)

    @app_commands.command(name="leaderboard", description="Show the guild power leaderboard")
    async def leaderboard(self, interaction: discord.Interaction):
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT ingame_username, game_class, power, power_updated_at 
            FROM users 
            WHERE power > 0 
            ORDER BY power DESC 
            LIMIT 25
        ''')
        users = cursor.fetchall()
        conn.close()

        if not users:
            await interaction.response.send_message("No power levels recorded yet.", ephemeral=True)
            return

        title = config.MESSAGES.get("leaderboard", {}).get("board_title", "Guild Power Leaderboard")
        embed = discord.Embed(title=title, color=discord.Color.purple())
        
        board_text = ""
        for i, (username, game_class, power, updated_at) in enumerate(users, 1):
            date_str = ""
            if updated_at:
                try:
                    dt = datetime.fromisoformat(updated_at)
                    days_ago = (datetime.utcnow() - dt).days
                    if days_ago > 3:
                        date_str = f" *(stale: {days_ago}d ago)*"
                except Exception:
                    pass
            
            board_text += f"**{i}. {username}** ({game_class}) - {power:,}{date_str}\n"

        embed.description = board_text
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(LeaderboardCog(bot))
