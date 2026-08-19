"""Tasks 路由：CRUD + 预览。"""
import csv
import io
import json
import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from auth import require_admin
from db import get_db
from models import (
    CreateShareRequest,
    CreateTaskRequest,
    DiffTask,
    ShareLink,
    ShareLinkResponse,
    TaskDetail,
    TaskSummary,
)
from diff_engine import diff

router = APIRouter(prefix="/api", tags=["tasks"])
ADMIN_DEPENDENCIES = [Depends(require_admin)]


def _get_active_task_or_404(task_id: str, db: Session) -> DiffTask:
    task = db.query(DiffTask).filter_by(id=task_id).first()
    if not task or (task.expires_at and task.expires_at <= datetime.utcnow()):
        raise HTTPException(status_code=404, detail="Task not found")
    return task


def _csv_safe(value: str | None) -> str:
    """避免 Excel/LibreOffice 把用户输入作为公式执行。"""
    value = "" if value is None else str(value)
    if value.lstrip(" \t\r").startswith(("=", "+", "-", "@")):
        return f"'{value}"
    return value


@router.post("/tasks", response_model=TaskDetail, status_code=201, dependencies=ADMIN_DEPENDENCIES)
def create_task(req: CreateTaskRequest, db: Session = Depends(get_db)):
    """创建对比任务：执行 diff + 存 DB + 返回结果。"""
    result = diff(req.column_a, req.column_b, req.mode, req.options.model_dump())

    task = DiffTask(
        title=req.title,
        mode=req.mode,
        column_a=req.column_a,
        column_b=req.column_b,
        options=req.options.model_dump_json(),
        result_meta=json.dumps(result["summary"]),
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    return _to_detail(task, result)


@router.get("/tasks", response_model=list[TaskSummary], dependencies=ADMIN_DEPENDENCIES)
def list_tasks(db: Session = Depends(get_db), limit: int = Query(50, ge=1, le=100)):
    """列出所有任务（按时间倒序）。"""
    tasks = (
        db.query(DiffTask)
        .filter(DiffTask.expires_at > datetime.utcnow())
        .order_by(DiffTask.created_at.desc())
        .limit(limit)
        .all()
    )
    share_tokens = {
        task_id: token
        for task_id, token in db.query(ShareLink.task_id, ShareLink.access_token)
        .filter(ShareLink.task_id.in_([task.id for task in tasks]))
        .all()
    } if tasks else {}
    return [
        TaskSummary(
            id=t.id,
            title=t.title,
            mode=t.mode,
            result_meta=json.loads(t.result_meta) if t.result_meta else None,
            created_at=t.created_at,
            share_token=share_tokens.get(t.id),
        )
        for t in tasks
    ]


@router.get("/tasks/{task_id}", response_model=TaskDetail, dependencies=ADMIN_DEPENDENCIES)
def get_task(task_id: str, db: Session = Depends(get_db)):
    """获取任务详情 + 重新执行 diff（保证结果与当前数据一致）。"""
    task = _get_active_task_or_404(task_id, db)

    options = json.loads(task.options) if task.options else {}
    result = diff(task.column_a, task.column_b, task.mode, options)
    return _to_detail(task, result)


@router.get("/tasks/{task_id}/export", dependencies=ADMIN_DEPENDENCIES)
def export_task_csv(task_id: str, db: Session = Depends(get_db)):
    """导出对比结果为 CSV（流式响应）。"""
    task = _get_active_task_or_404(task_id, db)

    options = json.loads(task.options) if task.options else {}
    result = diff(task.column_a, task.column_b, task.mode, options)

    def csv_gen():
        yield "\ufeff"
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["#", "A", "B", "status"])
        for i, row in enumerate(result["rows"], 1):
            writer.writerow([i, _csv_safe(row.get("a")), _csv_safe(row.get("b")), row["status"]])
        yield buf.getvalue()

    headers = {
        "Content-Disposition": f'attachment; filename="diff-{task_id}.csv"',
        "Content-Type": "text/csv; charset=utf-8",
    }
    return StreamingResponse(csv_gen(), headers=headers)


@router.delete("/tasks/{task_id}", status_code=204, dependencies=ADMIN_DEPENDENCIES)
def delete_task(task_id: str, db: Session = Depends(get_db)):
    """删除任务（级联删除分享链接）。"""
    task = _get_active_task_or_404(task_id, db)
    db.delete(task)
    db.commit()
    return None


@router.post("/preview", response_model=dict)
def preview_diff(req: CreateTaskRequest):
    """实时预览：不存 DB，只返回 diff 结果（用于前端实时调试）。"""
    return diff(req.column_a, req.column_b, req.mode, req.options.model_dump())


@router.get("/tasks/{task_id}/share", response_model=ShareLinkResponse, dependencies=ADMIN_DEPENDENCIES)
def get_share(task_id: str, db: Session = Depends(get_db)):
    """获取任务当前有效的分享链接信息。"""
    _get_active_task_or_404(task_id, db)
    link = db.query(ShareLink).filter_by(task_id=task_id).first()
    if not link or link.expires_at <= datetime.utcnow():
        raise HTTPException(status_code=404, detail="Share link not found")
    return _to_share_response(link)


@router.post("/tasks/{task_id}/share", response_model=ShareLinkResponse, dependencies=ADMIN_DEPENDENCIES)
def create_share(
    task_id: str,
    req: CreateShareRequest | None = None,
    db: Session = Depends(get_db),
):
    """生成在指定天数后失效的高熵只读分享链接。"""
    task = _get_active_task_or_404(task_id, db)
    req = req or CreateShareRequest()

    # 已存在的有效链接保持不变；过期链接会被替换。
    existing = db.query(ShareLink).filter_by(task_id=task_id).first()
    if existing and existing.expires_at > datetime.utcnow():
        return _to_share_response(existing)
    if existing:
        db.delete(existing)
        db.flush()

    expires_at = min(task.expires_at, datetime.utcnow() + timedelta(days=req.expires_in_days))

    for _ in range(5):
        token = secrets.token_urlsafe(16)
        if db.query(ShareLink).filter_by(access_token=token).first():
            continue
        link = ShareLink(task_id=task_id, access_token=token, permission="view", expires_at=expires_at)
        db.add(link)
        try:
            db.commit()
            return _to_share_response(link)
        except IntegrityError:
            db.rollback()
    raise HTTPException(status_code=503, detail="Could not create share link")


@router.delete("/tasks/{task_id}/share", status_code=204, dependencies=ADMIN_DEPENDENCIES)
def revoke_share(task_id: str, db: Session = Depends(get_db)):
    """撤销任务的当前分享链接。可重复调用。"""
    _get_active_task_or_404(task_id, db)
    db.query(ShareLink).filter_by(task_id=task_id).delete(synchronize_session=False)
    db.commit()
    return None


def _to_detail(task: DiffTask, result: dict) -> TaskDetail:
    """把 ORM 对象 + diff 结果转为 TaskDetail。"""
    return TaskDetail(
        id=task.id,
        title=task.title,
        mode=task.mode,
        column_a=task.column_a.splitlines(),
        column_b=task.column_b.splitlines(),
        options=json.loads(task.options) if task.options else {},
        result_meta=result["summary"],
        diff_result=result,
        created_at=task.created_at,
        share_token=None,  # 单独接口获取
    )


def _to_share_response(link: ShareLink) -> ShareLinkResponse:
    return ShareLinkResponse(token=link.access_token, permission=link.permission, expires_at=link.expires_at)
