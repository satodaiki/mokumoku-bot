import datetime as dt
import re
from zoneinfo import ZoneInfo


def parse_start_time(
    input_str: str, base_time_utc: dt.datetime, tz_name: str = "Asia/Tokyo"
) -> dt.datetime:
    """ユーザーが入力した時間指定文字列をパースし、対応するUTCのdatetimeを返す。

    引数:
        input_str: ユーザーの入力文字列。例: "10m", "1h", "19:00", "2026-07-03 19:00"
        base_time_utc: 基準となる現在時刻（UTC, タイムゾーン情報あり）
        tz_name: ユーザーのタイムゾーン（デフォルト: "Asia/Tokyo"）

    戻り値:
        パースされた日時のUTC datetime（タイムゾーン情報あり）

    例外:
        ValueError: パースに失敗した場合、または未来の時刻が指定された場合
    """
    tz = ZoneInfo(tz_name)
    base_time_local = base_time_utc.astimezone(tz)

    input_str = input_str.strip()

    # 1. 相対時間 (例: "10m", "1h", "2d")
    relative_pattern = re.compile(r"^(\d+)([mhd])$")
    match = relative_pattern.match(input_str)
    if match:
        val = int(match.group(1))
        unit = match.group(2)
        if unit == "m":
            delta = dt.timedelta(minutes=val)
        elif unit == "h":
            delta = dt.timedelta(hours=val)
        elif unit == "d":
            delta = dt.timedelta(days=val)
        else:
            raise ValueError(f"無効な単位です: {unit}")

        result_local = base_time_local - delta
        return result_local.astimezone(dt.timezone.utc)

    # 2. 時刻のみ (例: "19:00", "09:30")
    time_pattern = re.compile(r"^(\d{1,2}):(\d{2})$")
    match = time_pattern.match(input_str)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError("時刻の指定が範囲外です")

        # 今日のその時刻を作成
        result_local = base_time_local.replace(
            hour=hour, minute=minute, second=0, microsecond=0
        )

        # もし未来の時刻になってしまったら、昨日のその時刻とする
        if result_local > base_time_local:
            result_local -= dt.timedelta(days=1)

        return result_local.astimezone(dt.timezone.utc)

    # 3. 日付と時刻 (例: "2026-07-03 19:00", "07-03 19:00")
    # YYYY-MM-DD HH:MM
    datetime_pattern1 = re.compile(
        r"^(\d{4})-(\d{2})-(\d{2})\s+(\d{1,2}):(\d{2})$"
    )
    match = datetime_pattern1.match(input_str)
    if match:
        year = int(match.group(1))
        month = int(match.group(2))
        day = int(match.group(3))
        hour = int(match.group(4))
        minute = int(match.group(5))
        try:
            result_local = dt.datetime(year, month, day, hour, minute, tzinfo=tz)
        except ValueError as e:
            raise ValueError(f"日付の指定が正しくありません: {e}")

        if result_local > base_time_local:
            raise ValueError("未来の時刻は指定できません")

        return result_local.astimezone(dt.timezone.utc)

    # MM-DD HH:MM (年の省略)
    datetime_pattern2 = re.compile(r"^(\d{2})-(\d{2})\s+(\d{1,2}):(\d{2})$")
    match = datetime_pattern2.match(input_str)
    if match:
        month = int(match.group(1))
        day = int(match.group(2))
        hour = int(match.group(3))
        minute = int(match.group(4))

        # 今日の年を補完して日付時刻を作成
        try:
            result_local = dt.datetime(
                base_time_local.year, month, day, hour, minute, tzinfo=tz
            )
        except ValueError as e:
            raise ValueError(f"日付の指定が正しくありません: {e}")

        # もし未来の時刻になってしまったら、去年のその日付時刻とする
        if result_local > base_time_local:
            try:
                result_local = dt.datetime(
                    base_time_local.year - 1, month, day, hour, minute, tzinfo=tz
                )
            except ValueError as e:
                raise ValueError(f"昨年の日付に変換できませんでした: {e}")

        return result_local.astimezone(dt.timezone.utc)

    raise ValueError(
        "時間の指定形式が正しくありません。 (例: 30m, 1h, 19:00, 2026-07-03 19:00)"
    )
