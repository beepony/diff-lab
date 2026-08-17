"""Tasks 路由：CRUD + 预览。"""
import csv
import io
import json
import secrets
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from db import get_db
from models import DiffTask, ShareLink, CreateTaskRequest, TaskSummary, TaskDetail
from diff_engine import diff

router = APIRouter(prefix="/api", tags=["tasks"])


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
def list_tasks(db: Session = Depends(get_db), limit: int = 50):
    """列出所有任务（按时间倒序）。"""
    tasks = db.query(DiffTask).order_by(DiffTask.created_at.desc()).limit(limit).all()
    return [
        TaskSummary(
            id=t.id,
            title=t.title,
            mode=t.mode,
            result_meta=json.loads(t.result_meta) if t.result_meta else None,
            created_at=t.created_at,
            share_token=db.query(ShareLink).filter_by(task_id=t.id).first().access_token
            if db.query(ShareLink).filter_by(task_id=t.id).first() else None,
        )
        for t in tasks
    ]


@router.get("/tasks/{task_id}", response_model=TaskDetail)
def get_task(task_id: str, db: Session = Depends(get_db)):
    """获取任务详情 + 重新执行 diff（保证结果与当前数据一致）。"""
    task = db.query(DiffTask).filter_by(id=task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    options = json.loads(task.options) if task.options else {}
    result = diff(task.column_a, task.column_b, task.mode, options)
    return _to_detail(task, result)


@router.get("/tasks/{task_id}/export")
def export_task_csv(task_id: str, db: Session = Depends(get_db)):
    """导出对比结果为 CSV（流式响应）。"""
    task = db.query(DiffTask).filter_by(id=task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    options = json.loads(task.options) if task.options else {}
    result = diff(task.column_a, task.column_b, task.mode, options)

    def csv_gen():
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["#", "A", "B", "status"])
        for i, row in enumerate(result["rows"], 1):
            writer.writerow([i, row.get("a") or "", row.get("b") or "", row["status"]])
        yield buf.getvalue()

    headers = {
        "Content-Disposition": f'attachment; filename="diff-{task_id}.csv"',
        "Content-Type": "text/csv; charset=utf-8",
    }
    return StreamingResponse(csv_gen(), headers=headers)


@router.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: str, db: Session = Depends(get_db)):
    """删除任务（级联删除分享链接）。"""
    task = db.query(DiffTask).filter_by(id=task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return None


@router.post("/preview", response_model=dict)
def preview_diff(req: CreateTaskRequest):
    """实时预览：不存 DB，只返回 diff 结果（用于前端实时调试）。"""
    return diff(req.column_a, req.column_b, req.mode, req.options.model_dump())


@router.post("/tasks/{task_id}/share", response_model=dict)
def create_share(task_id: str, db: Session = Depends(get_db)):
    """生成分享链接：8 位随机 token，permission=view。"""
    task = db.query(DiffTask).filter_by(id=task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # 已存在则返回
    existing = db.query(ShareLink).filter_by(task_id=task_id).first()
    if existing:
        return {"token": existing.access_token, "permission": existing.permission}

    token = secrets.token_urlsafe(6)[:8]  # 8 位 base64
    link = ShareLink(task_id=task_id, access_token=token, permission="view")
    db.add(link)
    db.commit()
    return {"token": token, "permission": "view"}


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