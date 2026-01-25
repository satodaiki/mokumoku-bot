import asyncio
import datetime as dt
import os
from typing import List, Literal

import discord
import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

from mokumoku_bot.discord_bot import END_CMD, START_CMD

load_dotenv()

TOKEN = os.environ["DISCORD_TOKEN"]
CHANNEL_ID = int(os.environ["DISCORD_CHANNEL_ID"])


async def fetch_messages_once():
    """Streamlitから呼び出すための、ログイン〜取得〜ログアウトを完結させる関数"""
    # ここでClientを毎回作ることで、現在のループに紐付ける
    intents = discord.Intents.default()
    temp_client = discord.Client(intents=intents)

    async with temp_client:
        # バックグラウンドでログイン処理
        await temp_client.login(TOKEN)
        # チャンネル取得
        channel = await temp_client.fetch_channel(CHANNEL_ID)

        messages = []
        if isinstance(channel, discord.TextChannel):
            async for message in channel.history(limit=None):
                messages.append(message)

        messages.reverse()
        return messages


def convert_bot_messages_to_time_intervals(messages: List[discord.Message]):
    results = []
    for msg in messages:
        if "開始" in msg.content:
            cmd = START_CMD
        elif "終了" in msg.content:
            cmd = END_CMD
        else:
            continue

        user_name = ""

        if msg.author.bot and msg.interaction_metadata is None:
            print("Botのユーザー発信元が分かりませんでした")
            continue
        elif msg.author.bot and msg.interaction_metadata is not None:
            # ボットの場合
            user_name = msg.interaction_metadata.user.name
        else:
            # 手動の場合
            user_name = msg.author.name

        results.append(
            (
                cmd,
                user_name,
                msg.created_at,
            )
        )
    return results


def aggregate_time_intervals(
    data: List[tuple[Literal["start", "end"], str, dt.datetime]],
):
    """datetime型のデータから稼働時間を集計"""
    start_times = {}
    intervals = []

    for action, key, time in data:
        if action == "start":
            if key not in start_times:
                start_times[key] = []
            start_times[key].append(time)

        elif action == "end":
            if key in start_times and start_times[key]:
                start_time = start_times[key].pop(0)
                duration = (time - start_time).total_seconds() / 3600  # 時間単位

                intervals.append(
                    {
                        "key": key,
                        "start": start_time,
                        "end": time,
                        "duration_hours": duration,
                        "date": start_time.date(),
                    }
                )

    return intervals


# Streamlitアプリ
st.set_page_config(page_title="稼働時間トラッカー", layout="wide")

st.title("📊 稼働時間トラッカー")


messages = asyncio.run(fetch_messages_once())
data = convert_bot_messages_to_time_intervals(messages)

intervals = aggregate_time_intervals(data)
df = pd.DataFrame(intervals)

# 日毎の集計
daily_stats = df.groupby("date")["duration_hours"].sum().reset_index()
daily_stats.columns = ["日付", "稼働時間"]

# 棒グラフ
fig_bar = px.bar(daily_stats, x="日付", y="稼働時間", title="日毎の稼働時間")
fig_bar = px.bar(daily_stats, x="日付", y="稼働時間", title="日毎の稼働時間")
st.plotly_chart(fig_bar, use_container_width=True)

# タイムライン
st.subheader("稼働タイムライン")
st.dataframe(df)
