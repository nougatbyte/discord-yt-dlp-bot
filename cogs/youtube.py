import discord
from discord.ext import commands
import os
import subprocess
import re
import asyncio

QUEUE_FILE = 'queue.txt'

class YouTubeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Ensure queue file exists
        if not os.path.exists(QUEUE_FILE):
            with open(QUEUE_FILE, 'w') as f:
                pass

    # Function to download audio using yt-dlp
    def download_audio(self, video_id: str):
        directory = 'audio_files'
        os.makedirs(directory, exist_ok=True)
        file_path = os.path.join(directory, f'{video_id}.mp3')

        if os.path.exists(file_path):
            return file_path

        url = f"https://www.youtube.com/watch?v={video_id}"
        command = ['yt-dlp', '-x', '--audio-format', 'mp3', '-o', file_path, url]
        subprocess.run(command)

        return file_path

    def get_queue(self):
        with open(QUEUE_FILE, 'r') as f:
            return [line.strip() for line in f.readlines()]

    def add_to_queue(self, video_id: str):
        with open(QUEUE_FILE, 'a') as f:
            f.write(f"{video_id}\n")

    def clear_queue(self):
        with open(QUEUE_FILE, 'w') as f:
            f.truncate()

    def pop_queue(self):
        queue = self.get_queue()
        if queue:
            queue = queue[1:]
            with open(QUEUE_FILE, 'w') as f:
                for item in queue:
                    f.write(f"{item}\n")

    def is_valid_youtube_id(self, video_id: str) -> bool:
        return bool(re.match(r'^[a-zA-Z0-9_-]{11}$', video_id))

    async def play_queue(self, interaction: discord.Interaction, voice_client):
        queue = self.get_queue()
        if not queue:
            await interaction.response.send_message("The playlist is empty!")
            return

        for video_id in queue:
            now_playing_message = await interaction.channel.send(f"Now playing: https://www.youtube.com/watch?v={video_id}")
            await now_playing_message.add_reaction('⏳')

            audio_file_path = self.download_audio(video_id)
            await now_playing_message.clear_reaction('⏳')

            voice_client.play(discord.FFmpegPCMAudio(audio_file_path), after=lambda e: print(f"Finished playing: {e}"))
            while voice_client.is_playing():
                await asyncio.sleep(1)

            self.pop_queue()

    # Slash command to add a song to the playlist
    @discord.app_commands.command(name="add", description="Add a YouTube song to the playlist")
    async def add(self, interaction: discord.Interaction, url: str):
        if "youtube.com/watch?v=" in url:
            video_id = url.split("watch?v=")[1][:11]
        elif "youtu.be/" in url:
            video_id = url.split("youtu.be/")[1][:11]
        else:
            await interaction.response.send_message("Invalid YouTube URL!")
            return

        if not self.is_valid_youtube_id(video_id):
            await interaction.response.send_message("Invalid YouTube ID format!")
            return

        self.add_to_queue(video_id)
        await interaction.response.send_message(f"Added to queue: {url}")

    @discord.app_commands.command(name="play", description="Play the YouTube playlist in your voice channel")
    async def play(self, interaction: discord.Interaction):
        if not interaction.user.voice:
            await interaction.response.send_message("You need to be in a voice channel to use this command!")
            return

        voice_client = interaction.guild.voice_client
        if voice_client is None:
            voice_client = await interaction.user.voice.channel.connect()

        await self.play_queue(interaction, voice_client)

    @discord.app_commands.command(name="skip", description="Skip the current song")
    async def skip(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.is_playing():
            voice_client.stop()
            await interaction.response.send_message("Skipped the current song.")
        else:
            await interaction.response.send_message("No song is currently playing.")

    @discord.app_commands.command(name="clear", description="Clear the playlist")
    async def clear(self, interaction: discord.Interaction):
        self.clear_queue()
        await interaction.response.send_message("Cleared the playlist.")

    @discord.app_commands.command(name="queue", description="Show the current playlist")
    async def queue(self, interaction: discord.Interaction):
        queue = self.get_queue()
        if queue:
            await interaction.response.send_message(f"Current playlist:\n" + "\n".join([f"https://www.youtube.com/watch?v={vid}" for vid in queue]))
        else:
            await interaction.response.send_message("The playlist is empty!")

    # Sync commands on ready
    @commands.Cog.listener()
    async def on_ready(self):
        guild = discord.Object(id=YOUR_GUILD_ID)  # Replace with your guild/server ID
        await self.bot.tree.sync(guild=guild)

# Setup function to add the cog to the bot
async def setup(bot):
    await bot.add_cog(YouTubeCog(bot))
