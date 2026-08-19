"""SQLite 单文件数据库连接 + 自动建表。"""
import os
from datetime import datetime
from pathlib import Path
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import sessionmaker, declarative_base

# DB 文件位置：优先用环境变量（Docker），否则 backend/diff_lab.db（本地开发）
DB_PATH = Path(os.environ.get("DIFF_LAB_DB", Path(__file__).parent / "diff_lab.db"))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
DATABASE_URL = f"sqlite:///{DB_PATH}"
SQLITE_BUSY_TIMEOUT_MS = int(os.environ.get("DIFF_LAB_SQLITE_BUSY_TIMEOUT_MS", "5000"))

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite 多线程支持
    pool_pre_ping=True,
    echo=False,  # True 时打印 SQL，生产关闭
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


@event.listens_for(engine, "connect")
def configure_sqlite_connection(dbapi_connection, _):
    """为每个 SQLite 连接启用并发和数据完整性相关设置。"""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.execute("PRAGMA journal_mode = WAL")
    cursor.execute("PRAGMA synchronous = NORMAL")
    cursor.execute(f"PRAGMA busy_timeout = {SQLITE_BUSY_TIMEOUT_MS}")
    cursor.close()


def _run_migrations():
    config = Config(str(Path(__file__).with_name("alembic.ini")))
    config.set_main_option("sqlalchemy.url", DATABASE_URL)
    command.upgrade(config, "head")


def init_db():
    """升级数据库结构，并清理过期任务。"""
    from models import DiffTask, ShareLink  # noqa: F401  确保模型在迁移/清理时可用
    _run_migrations()
    with SessionLocal() as db:
        expired_task_ids = select(DiffTask.id).where(DiffTask.expires_at <= datetime.utcnow())
        db.query(ShareLink).filter(ShareLink.task_id.in_(expired_task_ids)).delete(synchronize_session=False)
        db.query(DiffTask).filter(DiffTask.expires_at <= datetime.utcnow()).delete(synchronize_session=False)
        db.commit()


def get_db():
    """FastAPI 依赖注入：每个请求一个 session。"""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
