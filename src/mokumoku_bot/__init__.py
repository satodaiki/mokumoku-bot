import datetime as dt
import os
from typing import Dict, List

import discord
from aiohttp import web
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.environ["DISCORD_TOKEN"]
CHANNEL_ID = int(os.environ["DISCORD_CHANNEL_ID"])
START_CMD = "start"
END_CMD = "end"

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

start_times: Dict[str, dt.datetime | None] = {}


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


async def get_bot_messages() -> List[discord.Message]:
    """もくもくBotが送ったすべてのメッセージを取得"""
    messages = []
    channel = client.get_channel(CHANNEL_ID)

    if channel is None:
        print("チャンネルが存在しません")
        return []

    if not isinstance(channel, discord.TextChannel):
        print("テキストチャンネル以外は受け付けません")
        return []

    async for message in channel.history(limit=None):
        # ボットのメッセージのみ抽出
        if message.author.bot and client.user and message.author.id == client.user.id:
            messages.append(message)

    # そのままだと最新のメッセージがリストの一番最初に入っているため
    # 最新のメッセージをリストの一番最後にする
    messages.reverse()

    return messages


def init_start_times(messages: List[discord.Message]):
    """各ユーザーの状態を初期化

    DB導入次第、不要になる予定
    """
    for msg in messages:
        if msg.interaction and msg.interaction.name == START_CMD:
            start_times[str(msg.interaction.user.id)] = msg.created_at
        elif msg.interaction and msg.interaction.name == END_CMD:
            start_times[str(msg.interaction.user.id)] = None


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    # ヘルスチェックサーバーの開始
    await start_server()
    await tree.sync()

    messages = await get_bot_messages()
    init_start_times(messages)


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
    start_times[user_id] = interaction.created_at

    await interaction.response.send_message(f"{user_name} もくもく開始")


@tree.command(name="end", description="もくもく学習を終了します")
@discord.app_commands.describe(task="今日やったことを書いてください")
async def end_command(interaction: discord.Interaction, task: str):
    user_id = str(interaction.user.id)
    user_name = str(interaction.user.name)

    if user_id not in start_times:
        await interaction.response.send_message("先に /start を実行してね")
        return

    start_time = start_times[user_id]
    if start_time is None:
        await interaction.response.send_message("先に /start を実行してね")
        return

    assert start_time is not None
    end_time = dt.datetime.now(tz=dt.timezone.utc)

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
