import os
import json

from aiohttp import web
import discord
from dotenv import load_dotenv
from datetime import datetime


load_dotenv()

TOKEN = os.environ.get("DISCORD_TOKEN")

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

start_times = {}

# --- ヘルスチェック用のWebサーバー設定 ---
async def health_check(request):
    return web.Response(text="OK", status=200)

async def start_server():
    app = web.Application()
    app.router.add_get("/healthz", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8000)
    await site.start()
    print("Health check server started on port 8000")

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    # ヘルスチェックサーバーの開始
    await start_server()
    await tree.sync()

@tree.command(name="start", description="もくもく学習を開始します")
async def start_command(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    user_name = str(interaction.user.name)

    if user_id not in start_times:
        start_times[user_id] = None

    if start_times[user_id] is not None:
        await interaction.response.send_message("既に /start を実行済みだよ")
        return

    # 開始時刻を保存
    start_times[user_id] = datetime.now()

    await interaction.response.send_message(f"{user_name} もくもく開始")

@tree.command(name="end", description="もくもく学習を終了します")
@app_commands.describe(task="今日やったことを書いてください")
async def end_command(interaction: discord.Interaction, task: str):
    user_id = str(interaction.user.id)
    user_name = str(interaction.user.name)

    if user_id not in start_times or start_times[user_id] is None:
        await interaction.response.send_message("先に /start を実行してね")
        return

    start_time = start_times[user_id]
    end_time = datetime.now()

    duration = end_time - start_time
    minutes = int(duration.total_seconds() // 60)

    # 終了したので開始時刻を消す
    start_times[user_id] = None

    hours = minutes // 60
    mins = minutes % 60

    await interaction.response.send_message(
        f"{user_name} もくもく終了\n今日の学習時間: {hours}時間{mins}分\n今日やったこと: {task}"
    )

client.run(TOKEN)
