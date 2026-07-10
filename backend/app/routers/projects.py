"""项目管理路由 — 支持研发项目、临时项目组、产品等。"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.models import Project
from app.schemas import ProjectResponse
from app.auth import get_current_user

router = APIRouter()

PROJECT_TYPES = [
    {"label": "产品开发", "value": "product"},
    {"label": "技术平台", "value": "platform"},
    {"label": "预研项目", "value": "research"},
    {"label": "临时项目组", "value": "temp"},
]
STATUSES = [
    {"label": "进行中", "value": "active"},
    {"label": "暂停", "value": "paused"},
    {"label": "已完结", "value": "completed"},
    {"label": "已资本化", "value": "capitalized"},
]


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    project_type: Optional[str] = None
    status: Optional[str] = None
    department_id: Optional[int] = None
    manager: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    budget: Optional[float] = None


@router.get("/", response_model=list[ProjectResponse])
def list_projects(company_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(Project).filter(Project.company_id == company_id, Project.is_active).order_by(Project.code).all()


@router.get("/types")
def project_types():
    return PROJECT_TYPES


@router.get("/statuses")
def project_statuses():
    return STATUSES


@router.post("/", response_model=ProjectResponse)
def create_project(company_id: int, data: ProjectUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    import random

    code = str(random.randint(1000, 9999))
    while db.query(Project).filter(Project.company_id == company_id, Project.code == code).first():
        code = str(random.randint(1000, 9999))
    p = Project(company_id=company_id, code=code, name=data.name or "", project_type=data.project_type or "product")
    for field in ["status", "department_id", "manager", "start_date", "end_date", "budget"]:
        val = getattr(data, field, None)
        if val is not None:
            setattr(p, field, val)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(project_id: int, data: ProjectUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="项目不存在")
    for field in ["name", "project_type", "status", "department_id", "manager", "start_date", "end_date", "budget"]:
        val = getattr(data, field, None)
        if val is not None:
            setattr(p, field, val)
    db.commit()
    db.refresh(p)
    return p


@router.delete("/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="项目不存在")
    p.is_active = False
    db.commit()
    return {"ok": True}
