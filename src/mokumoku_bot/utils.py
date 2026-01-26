import discord
from sqlalchemy import select
from sqlalchemy.orm import Session

from mokumoku_bot.discord_bot import END_CMD, START_CMD
from mokumoku_bot.model.history import History


async def init_history(sess: Session, token: str, channel_id: int):
    """historyテーブルの初期化処理"""
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
                    user_id = msg.interaction_metadata.user.id
                    user_name = msg.interaction_metadata.user.name
                else:
                    # 手動の場合
                    user_id = msg.author.id
                    user_name = msg.author.name

                histories += [
                    History(
                        user_id=user_id,
                        user_name=user_name,
                        cmd=cmd,
                        created_at=msg.created_at,
                    )
                ]

        sess.add_all(histories)
        sess.commit()


def get_all_histories(sess: Session):
    return list(sess.execute(select(History)).scalars().all())
