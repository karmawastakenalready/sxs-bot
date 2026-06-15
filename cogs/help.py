import discord
from discord.ext import commands
from discord import app_commands

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="List all available guild commands")
    async def help_command(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Sword x Staff Bot Commands",
            description="Here are all the commands you can use in the server:",
            color=discord.Color.blurple()
        )

        linking_cmds = (
            "`/link <username> <class>` - Link your account to the roster\n"
            "`/unlink` - Remove your account from the roster\n"
            "`/whoami` - Check your current linked info"
        )
        embed.add_field(name="Linking", value=linking_cmds, inline=False)

        roster_cmds = (
            "`/roster` - View the guild roster grouped by class\n"
            "`/comp` - View the guild's class composition breakdown"
        )
        embed.add_field(name="Roster", value=roster_cmds, inline=False)

        boss_cmds = (
            "`/bossdone` - Mark yourself as having run the guild boss today\n"
            "`/bossstatus` - See who has (and hasn't) run the boss today"
        )
        embed.add_field(name="Boss Tracker", value=boss_cmds, inline=False)

        power_cmds = (
            "`/power <amount>` - Update your current power level (e.g. 1.5M)\n"
            "`/leaderboard` - View the guild power leaderboard"
        )
        embed.add_field(name="Power", value=power_cmds, inline=False)

        misc_cmds = (
            "`/guide get <topic>` - Get a guide for a specific topic\n"
            "`/guide list` - See all available guides\n"
            "`/announcement view` - Read the current guild announcement\n"
            "`/reminders subscribe` - Toggle daily reset checklists in your DMs"
        )
        embed.add_field(name="Misc", value=misc_cmds, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(HelpCog(bot))
