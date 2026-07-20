"""数据库层配置（SQLAlchemy 2.x）。"""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import get_settings

settings = get_settings()
# 启动前/创建 engine 前确保 data/ 目录存在
settings.data_dir.mkdir(parents=True, exist_ok=True)

db_path = settings.data_dir / "app.db"
# SQLite 数据库 URL
SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """SQLAlchemy 2.0 声明性基类。"""
    pass


def init_db() -> None:
    """初始化数据库表。"""
    from app.models_orm import Base as OrmBase
    OrmBase.metadata.create_all(bind=engine)


def get_db():
    """FastAPI 数据库会话依赖。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
