import datetime as dt
from zoneinfo import ZoneInfo

import pytest

from mokumoku_bot.time_parser import parse_start_time


@pytest.fixture
def base_time_utc():
    # 2026-07-03 23:20:00 JST (UTC 14:20:00)
    return dt.datetime(2026, 7, 3, 14, 20, 0, tzinfo=dt.timezone.utc)


def test_parse_relative_time(base_time_utc):
    # 30分前 -> 2026-07-03 22:50:00 JST (UTC 13:50:00)
    result = parse_start_time("30m", base_time_utc)
    expected = dt.datetime(2026, 7, 3, 13, 50, 0, tzinfo=dt.timezone.utc)
    assert result == expected

    # 2時間前 -> 2026-07-03 21:20:00 JST (UTC 12:20:00)
    result = parse_start_time("2h", base_time_utc)
    expected = dt.datetime(2026, 7, 3, 12, 20, 0, tzinfo=dt.timezone.utc)
    assert result == expected

    # 1日前 -> 2026-07-02 23:20:00 JST (UTC 14:20:00 - 1 day)
    result = parse_start_time("1d", base_time_utc)
    expected = dt.datetime(2026, 7, 2, 14, 20, 0, tzinfo=dt.timezone.utc)
    assert result == expected


def test_parse_time_only(base_time_utc):
    # 今日の19:00 -> 2026-07-03 19:00:00 JST (UTC 10:00:00)
    result = parse_start_time("19:00", base_time_utc)
    expected = dt.datetime(2026, 7, 3, 10, 0, 0, tzinfo=dt.timezone.utc)
    assert result == expected

    # 今日の23:19 -> 2026-07-03 23:19:00 JST (UTC 14:19:00)
    result = parse_start_time("23:19", base_time_utc)
    expected = dt.datetime(2026, 7, 3, 14, 19, 0, tzinfo=dt.timezone.utc)
    assert result == expected

    # 未来の時刻を指定した場合: 23:50 -> 基準が23:20なので昨日の23:50になる
    # 昨日の23:50 -> 2026-07-02 23:50:00 JST (UTC 14:50:00)
    result = parse_start_time("23:50", base_time_utc)
    expected = dt.datetime(2026, 7, 2, 14, 50, 0, tzinfo=dt.timezone.utc)
    assert result == expected


def test_parse_datetime(base_time_utc):
    # フル日時 -> 2026-07-03 15:00:00 JST (UTC 06:00:00)
    result = parse_start_time("2026-07-03 15:00", base_time_utc)
    expected = dt.datetime(2026, 7, 3, 6, 0, 0, tzinfo=dt.timezone.utc)
    assert result == expected

    # 月日時刻 (今年の日付) -> 2026-07-02 18:00:00 JST (UTC 09:00:00)
    result = parse_start_time("07-02 18:00", base_time_utc)
    expected = dt.datetime(2026, 7, 2, 9, 0, 0, tzinfo=dt.timezone.utc)
    assert result == expected

    # 月日時刻 (未来を指定 -> 昨年に補完される)
    # 07-04 18:00 (基準は07-03) -> 2025-07-04 18:00:00 JST (UTC 09:00:00 - 1 yearish)
    result = parse_start_time("07-04 18:00", base_time_utc)
    expected = dt.datetime(2025, 7, 4, 9, 0, 0, tzinfo=dt.timezone.utc)
    assert result == expected


def test_parse_invalid_format(base_time_utc):
    with pytest.raises(ValueError):
        parse_start_time("invalid", base_time_utc)

    with pytest.raises(ValueError):
        # 未来の日時指定 (YYYY-MM-DD HH:MM は未来の場合エラー)
        parse_start_time("2026-07-04 12:00", base_time_utc)

    with pytest.raises(ValueError):
        # 存在しない日付
        parse_start_time("02-30 12:00", base_time_utc)

    with pytest.raises(ValueError):
        # 存在しない時刻
        parse_start_time("25:00", base_time_utc)
