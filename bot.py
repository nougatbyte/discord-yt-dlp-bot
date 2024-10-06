import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Initialize the bot with command prefix and intents
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    await bot.load_extension("cogs.youtube")  # YouTube bot
    #await bot.load_extension("cogs.minecraft")  # Minecraft bot
    await bot.tree.sync()  # Sync slash commands with Discord
    print(f'Logged in as {bot.user.name}')
    print(f"Slash commands available: {bot.tree.get_commands()}")

# Run the bot
bot.run(TOKEN)
