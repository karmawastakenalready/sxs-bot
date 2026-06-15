import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime
import database
import config

class RemindersCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_reminders.start()

    def cog_unload(self):
        self.check_reminders.cancel()

    reminders_group = app_commands.Group(name="reminders", description="Daily reminder preferences")

    @reminders_group.command(name="subscribe", description="Toggle daily reset DM reminders")
    async def subscribe(self, interaction: discord.Interaction):
        conn = database.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT dm_reminders FROM users WHERE discord_id = ?', (str(interaction.user.id),))
        row = cursor.fetchone()
        
        if not row:
            msg = config.MESSAGES.get("common", {}).get("error_not_linked", "Not linked.")
            await interaction.response.send_message(msg, ephemeral=True)
            conn.close()
            return
            
        current_status = row[0]
        new_status = 1 if current_status == 0 else 0
        
        cursor.execute('UPDATE users SET dm_reminders = ? WHERE discord_id = ?', (new_status, str(interaction.user.id)))
        conn.commit()
        conn.close()
        
        if new_status == 1:
            await interaction.response.send_message("You are now subscribed to daily reset DM reminders!", ephemeral=True)
        else:
            await interaction.response.send_message("You have unsubscribed from daily reset DM reminders.", ephemeral=True)

    @tasks.loop(minutes=1)
    async def check_reminders(self):
        now = datetime.utcnow()
        current_time_str = now.strftime("%H:%M")

        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT guild_id, reminder_channel_id, reset_time FROM guild_config')
        configs = cursor.fetchall()

        msg_text = config.MESSAGES.get("reminders", {}).get("daily_checklist", "**Daily Reset Checklist**")

        for guild_id, channel_id, reset_time in configs:
            if not reset_time:
                reset_time = "00:00"

            if current_time_str == reset_time:
                cursor.execute('DELETE FROM boss_tracker')
                conn.commit()

                if channel_id:
                    guild = self.bot.get_guild(int(guild_id))
                    if guild:
                        channel = guild.get_channel(int(channel_id))
                        if channel:
                            try:
                                await channel.send(msg_text)
                            except discord.Forbidden:
                                print(f"Cannot send message to {channel.name} in {guild.name}")

        reset_triggered = any(c[2] == current_time_str or (not c[2] and current_time_str == "00:00") for c in configs)
        
        if reset_triggered:
            cursor.execute('SELECT discord_id FROM users WHERE dm_reminders = 1')
            dm_users = cursor.fetchall()
            for (u_id,) in dm_users:
                user = self.bot.get_user(int(u_id))
                if user:
                    try:
                        await user.send(msg_text)
                    except discord.Forbidden:
                        pass

        conn.close()

    @check_reminders.before_loop
    async def before_check_reminders(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(RemindersCog(bot))
