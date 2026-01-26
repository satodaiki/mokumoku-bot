import datetime as dt
import os
from typing import Dict

import discord
from dotenv import load_dotenv
from sqlalchemy import desc, select

from mokumoku_bot.db.conn import get_db_session
from mokumoku_bot.model.history import History

load_dotenv()

TOKEN = os.environ["DISCORD_TOKEN"]
CHANNEL_ID = int(os.environ["DISCORD_CHANNEL_ID"])
START_CMD = "start"
END_CMD = "end"

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

# インメモリデータ
start_times: Dict[str, dt.datetime | None] = {}


def init_start_times():
    """各ユーザーの状態を初期化"""
    with get_db_session() as sess:
        # 各ユーザーごとの最新のレコードを取得
        results = (
            sess.execute(
                select(History)
                .distinct(History.user_id)
                .order_by(History.user_id, desc(History.created_at))
            )
            .scalars()
            .all()
        )

    for result in results:
        if result.cmd == START_CMD:
            start_times[result.user_id] = result.created_at
        elif result.cmd == END_CMD:
            start_times[result.user_id] = None


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    await tree.sync()

    # ユーザーの状態を初期化
    init_start_times()


@tree.command(name=START_CMD, description="もくもく学習を開始します")
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

    # DBにレコードを追加
    with get_db_session() as sess:
        sess.add(
            History(
                user_id=user_id,
                user_name=user_name,
                cmd=START_CMD,
                created_at=interaction.created_at,
            )
        )
        sess.commit()

    await interaction.response.send_message(f"{user_name} もくもく開始")


@tree.command(name=END_CMD, description="もくもく学習を終了します")
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

    # DBにレコードを追加
    with get_db_session() as sess:
        sess.add(
            History(
                user_id=user_id,
                user_name=user_name,
                cmd=END_CMD,
                created_at=interaction.created_at,
            )
        )
        sess.commit()

    hours = minutes // 60
    mins = minutes % 60

    await interaction.response.send_message(
        f"{user_name} もくもく終了\n今日の学習時間: {hours}時間{mins}分\n今日やったこと: {task}"
    )
