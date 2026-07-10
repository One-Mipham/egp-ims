"""协同办公 — 内部待办任务 API Router"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models import User, TodoTask

router = APIRouter()


@router.get("/")
def list_tasks(
    company_id: int = Query(...),
    status: str | None = Query(None),
    priority: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """列出待办任务，可按状态和优先级筛选。"""
    q = db.query(TodoTask).filter(TodoTask.company_id == company_id)
    if status:
        q = q.filter(TodoTask.status == status)
    if priority:
        q = q.filter(TodoTask.priority == priority)
    tasks = q.order_by(TodoTask.created_at.desc()).all()
    return {
        "tasks": [
            {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "status": t.status,
                "priority": t.priority,
                "due_date": t.due_date,
                "created_by": t.created_by,
                "completed_at": t.completed_at.isoformat() if t.completed_at else None,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in tasks
        ]
    }


@router.post("/")
def create_task(
    company_id: int = Query(...),
    title: str = Query(...),
    description: str = Query(None),
    priority: str = Query("medium"),
    due_date: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建新待办任务。"""
    task = TodoTask(
        company_id=company_id,
        created_by=current_user.id,
        title=title,
        description=description,
        priority=priority,
        due_date=due_date,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return {"ok": True, "id": task.id}


@router.put("/{task_id}")
def update_task(
    task_id: int,
    title: str = Query(None),
    description: str = Query(None),
    status: str = Query(None),
    priority: str = Query(None),
    due_date: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新待办任务。"""
    task = db.query(TodoTask).filter(TodoTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if title is not None:
        task.title = title
    if description is not None:
        task.description = description
    if status is not None:
        task.status = status
        if status == "completed":
            task.completed_at = datetime.utcnow()
    if priority is not None:
        task.priority = priority
    if due_date is not None:
        task.due_date = due_date
    task.updated_at = datetime.utcnow()
    db.commit()
    return {"ok": True}


@router.delete("/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除待办任务。"""
    task = db.query(TodoTask).filter(TodoTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    db.delete(task)
    db.commit()
    return {"ok": True}
