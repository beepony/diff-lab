"""SQLite 单文件数据库连接 + 自动建表。"""
import os
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, declarative_base

# DB 文件位置：优先用环境变量（Docker），否则 backend/diff_lab.db（本地开发）
DB_PATH = Path(os.environ.get("DIFF_LAB_DB", Path(__file__).parent / "diff_lab.db"))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite 多线程支持
    echo=False,  # True 时打印 SQL，生产关闭
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db():
    """首次启动时创建所有表。幂等，可重复调用。"""
    from models import DiffTask, ShareLink  # noqa: F401  防止循环引用
    Base.metadata.create_all(bind=engine)
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
    finally:
        db.close()
