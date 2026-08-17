"""Share 路由：通过 token 访问任务。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db import get_db
from models import ShareLink, DiffTask, TaskDetail
from diff_engine import diff
import json

router = APIRouter(prefix="/api/share", tags=["share"])


@router.get("/{token}", response_model=TaskDetail)
def access_by_token(token: str, db: Session = Depends(get_db)):
    """通过分享 token 访问任务（只读）。"""
    link = db.query(ShareLink).filter_by(access_token=token).first()
    if not link:
        raise HTTPException(status_code=404, detail="Invalid share token")

    task = db.query(DiffTask).filter_by(id=link.task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    options = json.loads(task.options) if task.options else {}
    result = diff(task.column_a, task.column_b, task.mode, options)

    return TaskDetail(
        id=task.id,
        title=task.title,
        mode=task.mode,
        column_a=task.column_a.splitlines(),
        column_b=task.column_b.splitlines(),
        options=options,
        result_meta=result["summary"],
        diff_result=result,
        created_at=task.created_at,
        share_token=token,
    )