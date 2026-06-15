import discord
from discord.ext import commands
import os
import config
import database

# Initialize database
database.setup_database()

class GuildBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Load cogs
        if not os.path.exists("cogs"):
            os.makedirs("cogs")
            
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py") and filename != "__init__.py":
                await self.load_extension(f"cogs.{filename[:-3]}")
        
        # Sync slash commands
        await self.tree.sync()

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("------")

if __name__ == "__main__":
    bot = GuildBot()
    if config.DISCORD_TOKEN:
        bot.run(config.DISCORD_TOKEN)
    else:
        print("Error: DISCORD_TOKEN not found in environment variables. Please check .env file.")
