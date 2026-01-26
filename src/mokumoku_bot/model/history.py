import datetime as dt
from typing import Literal

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from mokumoku_bot.db.base import Base


class History(Base):
    __tablename__ = "history"

    user_id: Mapped[str] = mapped_column(String(19), primary_key=True)
    user_name: Mapped[str] = mapped_column(nullable=False)
    cmd: Mapped[Literal["start", "end"]] = mapped_column(primary_key=True)
    created_at: Mapped[dt.datetime] = mapped_column(primary_key=True)
