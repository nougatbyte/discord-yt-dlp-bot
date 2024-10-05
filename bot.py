import discord
from discord.ext import commands
import os
import subprocess
import asyncio
import re
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')  # Get token from environment variable
QUEUE_FILE = 'queue.txt'
TEMP_MP3 = 'downloaded_audio.mp3'

# Create the bot with intents
intents = discord.Intents.default()  # Default intents (no privileged events)
intents.message_content = True       # Enable reading messages content (required for text commands)
intents.voice_states = True          # Enable voice state events

# Initialize the bot with the command prefix and intents
bot = commands.Bot(command_prefix='!', intents=intents)

# Ensure queue file exists
if not os.path.exists(QUEUE_FILE):
    with open(QUEUE_FILE, 'w') as f:
        pass

# Function to download audio using yt-dlp
def download_audio(video_id: str):
    # Create directory for downloads if it doesn't exist
    directory = f'audio_files'
    os.makedirs(directory, exist_ok=True)

    # Define the path for the downloaded file
    file_path = os.path.join(directory, f'{video_id}.mp3')

    if os.path.exists(file_path):
        return file_path  # Return the path if it already exists
    
    # Download the audio file using yt-dlp
    url = f"https://www.youtube.com/watch?v={video_id}"
    command = ['yt-dlp', '-x', '--audio-format', 'mp3', '-o', file_path, url]
    subprocess.run(command)

    return file_path

# Read the current queue from the text file
def get_queue():
    with open(QUEUE_FILE, 'r') as f:
        return [line.strip() for line in f.readlines()]

# Add a video ID to the queue
def add_to_queue(video_id: str):
    with open(QUEUE_FILE, 'a') as f:
        f.write(f"{video_id}\n")

# Clear the queue file
def clear_queue():
    with open(QUEUE_FILE, 'w') as f:
        f.truncate()

# Remove the first entry from the queue (after playing)
def pop_queue():
    queue = get_queue()
    if queue:
        queue = queue[1:]  # Remove the first element
        with open(QUEUE_FILE, 'w') as f:
            for item in queue:
                f.write(f"{item}\n")

# Function to validate YouTube video ID format
def is_valid_youtube_id(video_id: str) -> bool:
    # YouTube ID regex (11 characters, alphanumeric and some symbols)
    return bool(re.match(r'^[a-zA-Z0-9_-]{11}$', video_id))

# Function to play the current queue
async def play_queue(interaction: discord.Interaction, voice_client):
    queue = get_queue()

    if not queue:
        await interaction.response.send_message("The playlist is empty!")
        return

    # Play songs from the queue
    for video_id in queue:
        now_playing_message = await interaction.channel.send(f"Now playing: https://www.youtube.com/watch?v={video_id}")
        
        # React with the loading emoji to indicate the download is in progress
        await now_playing_message.add_reaction('⏳')

        # Download the audio file
        audio_file_path = download_audio(video_id)

        # Remove the loading emoji after the download is complete
        await now_playing_message.clear_reaction('⏳')

        # Play the downloaded audio file
        voice_client.play(discord.FFmpegPCMAudio(audio_file_path), after=lambda e: print(f"Finished playing: {e}"))

        # Wait for the song to finish
        while voice_client.is_playing():
            await asyncio.sleep(1)

        # Pop the played song from the queue
        pop_queue()


# Command to add a song to the playlist
@bot.tree.command(name="add", description="Add a song to the playlist")
async def add(interaction: discord.Interaction, url: str):
    # Extract YouTube video ID from URL (assuming it's in the correct format)
    if "youtube.com/watch?v=" in url:
        video_id = url.split("watch?v=")[1][:11]  # Get the video ID and ensure length
    elif "youtu.be/" in url:
        video_id = url.split("youtu.be/")[1][:11]  # Get the video ID and ensure length
    else:
        await interaction.response.send_message("Invalid YouTube URL!")
        return
    
    # Validate the YouTube video ID
    if not is_valid_youtube_id(video_id):
        await interaction.response.send_message("Invalid YouTube ID format!")
        return
    
    # Add to the playlist (queue file)
    add_to_queue(video_id)
    await interaction.response.send_message(f"Added to queue: {url}")

# Command to play the current playlist
@bot.tree.command(name="play", description="Play the current playlist.")
async def play(interaction: discord.Interaction):
    # Ensure the user is in a voice channel
    if not interaction.user.voice:
        await interaction.response.send_message("You need to be in a voice channel to use this command!")
        return

    # Check if the bot is already in a voice channel
    voice_client = interaction.guild.voice_client
    if voice_client is not None:
        # If the bot is in a different channel, move it to the user's channel
        if voice_client.channel != interaction.user.voice.channel:
            await voice_client.move_to(interaction.user.voice.channel)
    else:
        # Join the user's voice channel
        voice_client = await interaction.user.voice.channel.connect()

    # Start playing the queue
    await play_queue(interaction, voice_client)

# Command to skip the current song
@bot.tree.command(name="skip", description="Skip the current song.")
async def skip(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.stop()
        await interaction.response.send_message("Skipped the current song.")
    else:
        await interaction.response.send_message("No song is currently playing.")

# Command to clear the playlist
@bot.tree.command(name="clear", description="Clear the playlist.")
async def clear(interaction: discord.Interaction):
    clear_queue()
    await interaction.response.send_message("Cleared the playlist.")

# Command to display the current queue
@bot.tree.command(name="queue", description="Display the current playlist.")
async def queue(interaction: discord.Interaction):
    queue = get_queue()
    if queue:
        await interaction.response.send_message(f"Current playlist:\n" + "\n".join([f"https://www.youtube.com/watch?v={vid}" for vid in queue]))
    else:
        await interaction.response.send_message("The playlist is empty!")

# Register commands with Discord
@bot.event
async def on_ready():
    await bot.tree.sync()  # Sync slash commands with Discord
    print(f'Logged in as {bot.user.name}')

# Run the bot
bot.run(TOKEN)
