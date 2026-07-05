import datetime as dt

import discord
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from mokumoku_bot.discord_bot import END_CMD, START_CMD
from mokumoku_bot.model.history import History

# interaction.created_at と Bot 投稿メッセージの msg.created_at は
# Discord 側で 1秒前後ズレるため、これより広めの窓で同一イベント判定する
DEDUP_WINDOW = dt.timedelta(seconds=5)


def _to_aware_utc(d: dt.datetime) -> dt.datetime:
    """DB から取得した naive な UTC 时刻に tzinfo を付与する"""
    if d.tzinfo is None:
        return d.replace(tzinfo=dt.timezone.utc)
    return d.astimezone(dt.timezone.utc)


async def init_history(sess: Session, token: str, channel_id: int):
    """historyテーブルの初期化処理"""
    # 既存レコードを先に取得し、Bot 経由で既に書き込まれた
    # 同一イベント（interaction 時刻ベース）の再取り込みを弾く
    existing = list(
        sess.execute(
            select(History.user_id, History.cmd, History.created_at)
        ).all()
    )

    # ここでClientを毎回作ることで、現在のループに紐付ける
    intents = discord.Intents.default()
    temp_client = discord.Client(intents=intents)

    async with temp_client:
        # バックグラウンドでログイン処理
        await temp_client.login(token)
        # チャンネル取得
        channel = await temp_client.fetch_channel(channel_id)

        # Historyオブジェクトの作成
        histories = []
        if isinstance(channel, discord.TextChannel):
            async for msg in channel.history(limit=None, oldest_first=True):
                if "開始" in msg.content:
                    cmd = START_CMD
                elif "終了" in msg.content:
                    cmd = END_CMD
                else:
                    continue

                user_id = ""
                user_name = ""

                if msg.author.bot and msg.interaction_metadata is None:
                    print("Botのユーザー発信元が分かりませんでした")
                    continue
                elif msg.author.bot and msg.interaction_metadata is not None:
                    # ボットの場合
                    user_id = str(msg.interaction_metadata.user.id)
                    user_name = msg.interaction_metadata.user.name
                else:
                    # 手動の場合
                    user_id = str(msg.author.id)
                    user_name = msg.author.name

                created_at = msg.created_at

                # Bot が /start /end 受信時に DB へ直接書き込み済みの場合、
                # interaction.created_at と msg.created_at は 1秒前後ズレるため
                # 主キーでは重複を弾けない。取り込み前に (user_id, cmd) が一致し
                # created_at が ±5秒以内 に入る既存レコードがあればスキップする
                if any(
                    e.user_id == user_id
                    and e.cmd == cmd
                    and abs(_to_aware_utc(e.created_at) - created_at)
                    <= DEDUP_WINDOW
                    for e in existing
                ):
                    continue

                histories += [
                    {
                        "user_id": user_id,
                        "user_name": user_name,
                        "cmd": cmd,
                        "created_at": created_at,
                    }
                ]

        if not histories:
            return

        # insert 文の作成
        stmt = insert(History).values(histories)

        # 主キーが衝突した場合は「何もしない」
        # index_elements にはモデルで primary_key=True にしたカラム名を指定
        stmt = stmt.on_conflict_do_nothing(
            index_elements=["user_id", "cmd", "created_at"]
        )
        sess.execute(stmt)
        sess.commit()


def get_all_histories(sess: Session):
    return list(sess.execute(select(History)).scalars().all())
