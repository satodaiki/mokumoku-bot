import os
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.environ["DATABASE_URL"]

# The engine should be a singleton instance in your application
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # 接続を使用する直前に「生きてるか」確認する
)

# The sessionmaker/factory is also a singleton
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# For web applications, consider using a dependency injection system
# to manage the lifecycle of each session instance per request
@contextmanager
def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
