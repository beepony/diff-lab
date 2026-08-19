"""Tasks 路由：CRUD + 预览。"""
import csv
import io
import json
import secrets
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from db import get_db
from models import DiffTask, ShareLink, CreateTaskRequest, TaskSummary, TaskDetail
from diff_engine import diff

router = APIRouter(prefix="/api", tags=["tasks"])


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


@router.post("/tasks", response_model=TaskDetail, status_code=201)
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


@router.get("/tasks", response_model=list[TaskSummary])
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


@router.get("/tasks/{task_id}", response_model=TaskDetail)
def get_task(task_id: str, db: Session = Depends(get_db)):
    """获取任务详情 + 重新执行 diff（保证结果与当前数据一致）。"""
    task = _get_active_task_or_404(task_id, db)

    options = json.loads(task.options) if task.options else {}
    result = diff(task.column_a, task.column_b, task.mode, options)
    return _to_detail(task, result)


@router.get("/tasks/{task_id}/export")
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


@router.delete("/tasks/{task_id}", status_code=204)
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


@router.post("/tasks/{task_id}/share", response_model=dict)
def create_share(task_id: str, db: Session = Depends(get_db)):
    """生成分享链接：高熵随机 token，permission=view。"""
    task = _get_active_task_or_404(task_id, db)

    # 已存在则返回
    existing = db.query(ShareLink).filter_by(task_id=task_id).first()
    if existing:
        return {"token": existing.access_token, "permission": existing.permission}

    for _ in range(5):
        token = secrets.token_urlsafe(16)
        if db.query(ShareLink).filter_by(access_token=token).first():
            continue
        link = ShareLink(task_id=task_id, access_token=token, permission="view")
        db.add(link)
        try:
            db.commit()
            return {"token": token, "permission": "view"}
        except IntegrityError:
            db.rollback()
    raise HTTPException(status_code=503, detail="Could not create share link")


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
