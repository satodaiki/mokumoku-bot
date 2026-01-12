import discord
import os
import json
from discord import app_commands
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

TOKEN = os.environ.get("DISCORD_TOKEN")

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

DATA_FILE = "record.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

study_data = load_data()

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    await tree.sync()

@tree.command(name="start", description="もくもく学習を開始します")
async def start_command(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    user_name = str(interaction.user.name)

    if user_id not in study_data or study_data[user_id].get("start") is not None:
        await interaction.response.send_message("既に /start を実行済みだよ")

    # 開始時刻を保存
    study_data[user_id] = {
        "start": datetime.now().isoformat(),
        "name": user_name
    }
    save_data(study_data)

    await interaction.response.send_message(f"{user_name} もくもく開始")

@tree.command(name="end", description="もくもく学習を終了します")
@app_commands.describe(task="今日やったことを書いてください")
async def end_command(interaction: discord.Interaction, task: str):
    user_id = str(interaction.user.id)
    user_name = str(interaction.user.name)

    if user_id not in study_data or study_data[user_id].get("start") is None:
        await interaction.response.send_message("先に /start を実行してね")
        return

    start_time = datetime.fromisoformat(study_data[user_id]["start"])
    end_time = datetime.now()

    duration = end_time - start_time
    minutes = int(duration.total_seconds() // 60)

    # 終了したので開始時刻を消す
    study_data[user_id]["start"] = None
    save_data(study_data)

    hours = minutes // 60
    mins = minutes % 60

    await interaction.response.send_message(
        f"{user_name} もくもく終了\n今日の学習時間: {hours}時間{mins}分\n今日やったこと: {task}"
    )

client.run(TOKEN)