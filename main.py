import discord
import os
from discord import app_commands
from dotenv import load_dotenv

if os.getenv("RAILWAY_ENVIRONMENT") is None:
    load_dotenv()

if os.getenv("DISABLE_BOT") == "true":
    print("Bot is disabled in this environment.")
    exit()

TOKEN = os.environ.get("DISCORD_TOKEN")

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    await tree.sync()  # コマンドをDiscordに同期

@tree.command(name="start", description="もくもく学習を開始します")
async def start_command(interaction: discord.Interaction):
    await interaction.response.send_message("もくもく開始")

@tree.command(name="rest", description="もくもく学習を休憩します")
async def start_command(interaction: discord.Interaction):
    await interaction.response.send_message("もくもく休憩")

@tree.command(name="restart", description="もくもく学習を再開します")
async def start_command(interaction: discord.Interaction):
    await interaction.response.send_message("もくもく再開")

@tree.command(name="end", description="もくもく学習を終了します")
async def start_command(interaction: discord.Interaction):
    await interaction.response.send_message("もくもく終了")

client.run(TOKEN)