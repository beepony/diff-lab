"""SQLAlchemy 模型 + Pydantic Schema。"""
from datetime import datetime, timedelta
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional, Literal
import uuid

from db import Base


MAX_COLUMN_LINES = 1000
MAX_COLUMN_CHARS = 100_000


# ============ SQLAlchemy ORM 模型 ============

class DiffTask(Base):
    """对比任务表。"""
    __tablename__ = "diff_tasks"

    id = Column(String, primary_key=True, default=lambda: uuid.uuid4().hex[:12])
    title = Column(String, nullable=False)
    mode = Column(String, nullable=False)  # find_diff | vlookup | intersect
    column_a = Column(Text, nullable=False)
    column_b = Column(Text, nullable=False)
    column_a_meta = Column(Text, nullable=True)  # 大数据指纹 JSON
    column_b_meta = Column(Text, nullable=True)
    options = Column(Text, nullable=True)  # JSON 字符串
    result_meta = Column(Text, nullable=True)  # JSON: {match, fuzzy, diff, duration_ms}
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False, default=lambda: datetime.utcnow() + timedelta(days=90))

    share_links = relationship("ShareLink", back_populates="task", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_diff_tasks_expires_created", "expires_at", "created_at"),
    )


class ShareLink(Base):
    """分享链接表（实现 1A 无登录分享）。"""
    __tablename__ = "share_links"

    task_id = Column(String, ForeignKey("diff_tasks.id", ondelete="CASCADE"), primary_key=True)
    access_token = Column(String, primary_key=True, unique=True, index=True)
    permission = Column(String, default="view")  # view | edit
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)

    task = relationship("DiffTask", back_populates="share_links")


# ============ Pydantic Schema（API 入参/出参） ============

class DiffOptions(BaseModel):
    """对比选项。"""
    ignore_case: bool = False
    trim: bool = False
    skip_empty: bool = True


class CreateTaskRequest(BaseModel):
    """创建任务入参。"""
    title: str = Field(..., min_length=1, max_length=200)
    mode: Literal["find_diff", "vlookup", "intersect"]
    column_a: str = Field(..., max_length=MAX_COLUMN_CHARS, description="A 列原始文本（每行一个值）")
    column_b: str = Field(..., max_length=MAX_COLUMN_CHARS, description="B 列原始文本")
    options: DiffOptions = Field(default_factory=DiffOptions)

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("title must contain non-whitespace characters")
        return value

    @field_validator("column_a", "column_b")
    @classmethod
    def enforce_column_line_limit(cls, value: str) -> str:
        if len(value.splitlines()) > MAX_COLUMN_LINES:
            raise ValueError(f"column must contain at most {MAX_COLUMN_LINES} lines")
        return value


class TaskSummary(BaseModel):
    """任务列表（首页历史用，不含完整数据）。"""
    id: str
    title: str
    mode: str
    result_meta: Optional[dict] = None
    created_at: datetime
    column_a_count: int
    column_b_count: int
    share_token: Optional[str] = None  # 是否已分享

    model_config = ConfigDict(from_attributes=True)


class TaskDetail(BaseModel):
    """任务详情（含完整数据和对比结果）。"""
    id: str
    title: str
    mode: str
    column_a: list[str]
    column_b: list[str]
    options: dict
    result_meta: dict
    diff_result: dict  # 实际 diff 输出
    created_at: datetime
    share_token: Optional[str] = None


class CreateShareRequest(BaseModel):
    """创建分享链接的可选参数。"""
    expires_in_days: int = Field(default=7, ge=1, le=90)


class ShareLinkResponse(BaseModel):
    token: str
    permission: str
    expires_at: datetime
