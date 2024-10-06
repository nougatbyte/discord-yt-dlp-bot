import discord
from discord.ext import commands, tasks
from mcstatus import JavaServer
import os

# Load environment variables
MINECRAFT_SERVER_IP = os.getenv("MINECRAFT_SERVER_IP")
MINECRAFT_SERVER_PORT = os.getenv("MINECRAFT_SERVER_PORT")
NOTIFICATION_CHANNEL_ID = int(os.getenv("NOTIFICATION_CHANNEL_ID"))  # Channel to send notifications

class MinecraftCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.server = JavaServer.lookup(f"{MINECRAFT_SERVER_IP}:{MINECRAFT_SERVER_PORT}")
        self.previous_player_count = None  # Store the previous player count
        self.check_server_status.start()  # Start the background task

    # Background task to periodically check server status
    @tasks.loop(seconds=120)
    async def check_server_status(self):
        try:
            status = self.server.status()
            current_player_count = status.players.online
            print(f"Server has {current_player_count} player(s) online")

            # Check if player count increased (someone joined)
            if self.previous_player_count is not None and current_player_count > self.previous_player_count:
                # Send a message to the specified channel
                channel = self.bot.get_channel(NOTIFICATION_CHANNEL_ID)
                if channel:
                    await channel.send(f"🔔 A new player has joined! There are now {current_player_count} player(s) online.")
            
            # Update previous player count
            self.previous_player_count = current_player_count

        except Exception as e:
            print(f"Failed to query Minecraft server: {e}")

    # Slash command to check server status manually
    @commands.Cog.listener()
    async def on_ready(self):
        guild = discord.Object(id=YOUR_GUILD_ID)  # Replace with your server's ID
        await self.bot.tree.sync(guild=guild)
        # Initialize player count when bot starts (without sending messages)
        try:
            status = self.server.status()
            self.previous_player_count = status.players.online
        except Exception as e:
            print(f"Failed to initialize player count: {e}")

    @discord.app_commands.command(name="mcstatus", description="Check Minecraft server status")
    async def mcstatus(self, interaction: discord.Interaction):
        try:
            status = self.server.status()
            await interaction.response.send_message(f"🟢 Server is online with {status.players.online} player(s).")
        except Exception as e:
            await interaction.response.send_message("🔴 Failed to query the server.")

# Function to add this cog to the bot
async def setup(bot):
    await bot.add_cog(MinecraftCog(bot))
