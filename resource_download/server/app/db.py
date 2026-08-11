"""数据库层配置（SQLAlchemy 2.x）。"""

from __future__ import annotations

from sqlalchemy import create_engine, inspect, text
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


SCHEMA_VERSION = 1


def _sqlite_column_default(column) -> str | None:
    """Choose a safe SQL default when adding a non-null legacy column."""
    if column.nullable:
        return None
    type_name = str(column.type).upper()
    if "BOOL" in type_name:
        return "1"
    if any(token in type_name for token in ("INT", "NUMERIC", "REAL", "FLOAT")):
        return "0"
    if "DATE" in type_name or "TIME" in type_name:
        return "CURRENT_TIMESTAMP"
    return "''"


def _migrate_schema(metadata) -> None:
    """Apply additive, idempotent migrations for older RD databases."""
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE IF NOT EXISTS schema_migrations "
                "(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
            )
        )
        inspector = inspect(conn)
        for table in metadata.tables.values():
            if table.name not in inspector.get_table_names():
                continue
            existing = {str(item["name"]) for item in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name in existing or column.primary_key:
                    continue
                type_sql = column.type.compile(dialect=engine.dialect)
                statement = f'ALTER TABLE "{table.name}" ADD COLUMN "{column.name}" {type_sql}'
                default = _sqlite_column_default(column)
                if default is not None:
                    statement += f" DEFAULT {default}"
                conn.execute(text(statement))
        conn.execute(
            text("INSERT OR IGNORE INTO schema_migrations(version) VALUES (:version)"),
            {"version": SCHEMA_VERSION},
        )


def init_db() -> None:
    """初始化数据库表。"""
    from app.models_orm import Base as OrmBase
    OrmBase.metadata.create_all(bind=engine)
    _migrate_schema(OrmBase.metadata)


def get_db():
    """FastAPI 数据库会话依赖。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
