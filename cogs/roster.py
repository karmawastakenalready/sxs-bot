import discord
from discord.ext import commands
from discord import app_commands
import database
import config

async def update_roster_message(bot: commands.Bot, guild_id: int):
    conn = database.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT roster_channel_id, roster_message_id FROM guild_config WHERE guild_id = ?', (str(guild_id),))
    row = cursor.fetchone()
    if not row or not row[0]:
        conn.close()
        return
        
    channel_id, message_id = row
    
    cursor.execute('SELECT ingame_username, game_class FROM users ORDER BY game_class, ingame_username')
    users = cursor.fetchall()
    
    roster_dict = {}
    for username, game_class in users:
        if game_class not in roster_dict:
            roster_dict[game_class] = []
        roster_dict[game_class].append(username)

    title = config.MESSAGES.get("roster", {}).get("embed_title", "Guild Roster")
    desc = config.MESSAGES.get("roster", {}).get("embed_description", "Total Members: {total_members}").format(total_members=len(users))
    
    embed = discord.Embed(title=title, description=desc, color=discord.Color.blue())
    for game_class, members in roster_dict.items():
        embed.add_field(name=f"{game_class} ({len(members)})", value="\n".join(members), inline=False)

    guild = bot.get_guild(guild_id)
    if not guild:
        conn.close()
        return
        
    channel = guild.get_channel(int(channel_id))
    if not channel:
        conn.close()
        return

    message_sent = False
    if message_id:
        try:
            msg_obj = await channel.fetch_message(int(message_id))
            await msg_obj.edit(embed=embed)
            message_sent = True
        except discord.NotFound:
            pass
            
    if not message_sent:
        try:
            new_msg = await channel.send(embed=embed)
            cursor.execute('''
                UPDATE guild_config 
                SET roster_message_id = ? 
                WHERE guild_id = ?
            ''', (str(new_msg.id), str(guild_id)))
            conn.commit()
        except discord.Forbidden:
            pass

    conn.close()

class RosterCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="roster", description="Show the guild roster grouped by class")
    async def roster(self, interaction: discord.Interaction):
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT ingame_username, game_class FROM users ORDER BY game_class, ingame_username')
        users = cursor.fetchall()
        conn.close()

        if not users:
            await interaction.response.send_message("The roster is currently empty.", ephemeral=True)
            return

        roster_dict = {}
        for username, game_class in users:
            if game_class not in roster_dict:
                roster_dict[game_class] = []
            roster_dict[game_class].append(username)

        title = config.MESSAGES.get("roster", {}).get("embed_title", "Guild Roster")
        desc = config.MESSAGES.get("roster", {}).get("embed_description", "Total Members: {total_members}").format(total_members=len(users))
        
        embed = discord.Embed(title=title, description=desc, color=discord.Color.blue())
        for game_class, members in roster_dict.items():
            embed.add_field(name=f"{game_class} ({len(members)})", value="\n".join(members), inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="comp", description="Show the breakdown of classes in the guild")
    async def comp(self, interaction: discord.Interaction):
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT game_class, COUNT(*) FROM users GROUP BY game_class')
        comp_data = cursor.fetchall()
        conn.close()

        if not comp_data:
            await interaction.response.send_message("The roster is currently empty.", ephemeral=True)
            return

        title = config.MESSAGES.get("roster", {}).get("comp_title", "Guild Class Composition")
        embed = discord.Embed(title=title, color=discord.Color.green())
        
        for game_class, count in comp_data:
            embed.add_field(name=game_class, value=str(count), inline=True)

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(RosterCog(bot))
