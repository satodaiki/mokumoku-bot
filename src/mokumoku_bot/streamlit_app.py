import asyncio
import os
from typing import List

import pandas as pd
import plotly.express as px
import pytz
import streamlit as st
from dotenv import load_dotenv

from mokumoku_bot.db.conn import get_db_session
from mokumoku_bot.discord_bot import END_CMD, START_CMD
from mokumoku_bot.model.history import History
from mokumoku_bot.utils import get_all_histories, init_history

load_dotenv()

TOKEN = os.environ["DISCORD_TOKEN"]
CHANNEL_ID = int(os.environ["DISCORD_CHANNEL_ID"])


def aggregate_time_intervals(
    data: List[History],
):
    """datetime型のデータから稼働時間を集計"""
    last_start_dict = {}
    intervals = []

    for d in data:
        action, key, time = d.cmd, d.user_name, d.created_at

        # 時間をUTC -> JSTにノーマライズ
        time = pytz.timezone("Asia/Tokyo").normalize(pytz.UTC.localize(time))

        if action == START_CMD:
            last_start_dict[key] = time

        elif action == END_CMD:
            if key in last_start_dict:
                start_time = last_start_dict.pop(key)
                duration = (time - start_time).total_seconds() / 3600  # 時間単位

                # --- データの齟齬対策 ---
                # 1回の作業が24時間を超える場合は、押し忘れとみなして除外（または警告）
                if 0 < duration < 24:
                    intervals.append(
                        {
                            "key": key,
                            "start": start_time,
                            "end": time,
                            "duration_hours": duration,
                            "date": start_time.date(),
                            "month": start_time.strftime("%Y-%m"),
                        }
                    )
                else:
                    # ここでログを出したり、異常値としてスキップ
                    print(f"異常な継続時間を検知し除外: {key} ({duration:.1f} hours)")

    return intervals


# Streamlitアプリ
st.set_page_config(page_title="稼働時間トラッカー", layout="wide")

st.title("📊 稼働時間トラッカー")

if st.button("更新 🔄"):
    with get_db_session() as sess:
        asyncio.run(init_history(sess, TOKEN, CHANNEL_ID))
        st.cache_data.clear()  # キャッシュを削除
        st.rerun()  # スクリプトを再実行（画面更新）

with get_db_session() as sess:
    data = get_all_histories(sess)

intervals = aggregate_time_intervals(data)
df = pd.DataFrame(intervals)

# データが存在する場合のみ表示
if not df.empty:
    # 日毎の集計
    daily_stats = df.groupby("date")["duration_hours"].sum().reset_index()
    daily_stats.columns = ["日付", "稼働時間"]

    # 棒グラフ
    fig_bar = px.bar(daily_stats, x="日付", y="稼働時間", title="日毎の稼働時間")
    st.plotly_chart(fig_bar, use_container_width=True)

    # ユーザーごとの棒グラフ
    user_list = sorted(df["key"].unique())
    user_tabs = st.tabs([f"👤 {u}" for u in user_list])
    for tab, user_name in zip(user_tabs, user_list):
        with tab:
            st.subheader(f"{user_name} さんの活動分析")

            user_df = df.sort_values("start", ascending=False)[df["key"] == user_name]

            # 指標を横並びで表示
            col1, col2, col3 = st.columns(3)
            total_h = user_df["duration_hours"].sum()
            avg_h = user_df["duration_hours"].mean()
            count = len(user_df)

            col1.metric("総稼働時間", f"{total_h:.1f} 時間")
            col2.metric("平均稼働時間", f"{avg_h:.1f} 時間")
            col3.metric("もくもく回数", f"{count} 回")

            st.write("### 📈 月別・日別の稼働推移")

            # 月別と日別を切り替えて表示できるようにラジオボタンを設置
            view_mode = st.radio(
                f"表示単位 ({user_name})",
                ["日別", "月別"],
                horizontal=True,
                key=f"radio_{user_name}",
            )

            if view_mode == "日別":
                user_daily = (
                    user_df.groupby("date")["duration_hours"].sum().reset_index()
                )
                fig_daily = px.line(
                    user_daily,
                    x="date",
                    y="duration_hours",
                    markers=True,
                    title=f"{user_name} さんの稼働推移",
                    labels={"duration_hours": "時間(h)", "date": "日付"},
                )
                st.plotly_chart(fig_daily, use_container_width=True)
            else:
                user_monthly = (
                    user_df.groupby("month")["duration_hours"]
                    .agg(["sum", "mean", "count"])
                    .reset_index()
                )
                user_monthly.columns = ["month", "total_h", "avg_h", "count"]

                m_tab1, m_tab2, m_tab3 = st.tabs(["合計時間", "平均時間", "回数"])

                with m_tab1:
                    fig_monthly_sum = px.bar(
                        user_monthly,
                        x="month",
                        y="total_h",
                        text_auto=True,  # 棒グラフの上に数値を表示
                        title=f"{user_name} さんの月別合計稼働時間",
                        labels={"total_h": "合計時間(h)", "month": "年月"},
                    )
                    fig_monthly_sum.update_xaxes(
                        type="category"
                    )  # 年月を文字列として等間隔に表示
                    st.plotly_chart(fig_monthly_sum, use_container_width=True)

                with m_tab2:
                    fig_monthly_avg = px.line(
                        user_monthly,
                        x="month",
                        y="avg_h",
                        markers=True,
                        text=[f"{v:.2f}h" for v in user_monthly["avg_h"]],
                        title=f"{user_name} さんの月別平均稼働時間",
                        labels={"avg_h": "平均時間(h)", "month": "年月"},
                    )
                    fig_monthly_avg.update_traces(textposition="top center")
                    fig_monthly_avg.update_xaxes(
                        type="category"
                    )  # 年月を文字列として等間隔に表示
                    st.plotly_chart(fig_monthly_avg, use_container_width=True)

                with m_tab3:
                    fig_monthly_cnt = px.bar(
                        user_monthly,
                        x="month",
                        y="count",
                        text_auto=True,  # 棒グラフの上に数値を表示
                        title=f"{user_name} さんの月別稼働回数",
                        labels={"count": "回数", "month": "年月"},
                    )
                    fig_monthly_cnt.update_xaxes(
                        type="category"
                    )  # 年月を文字列として等間隔に表示
                    st.plotly_chart(fig_monthly_cnt, use_container_width=True)

    # タイムライン
    st.subheader("稼働タイムライン")
    st.dataframe(df)
else:
    st.write("データが存在しません")
