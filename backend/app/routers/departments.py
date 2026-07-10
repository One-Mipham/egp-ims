"""部门管理路由。"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Department
from app.schemas import DepartmentCreate, DepartmentUpdate, DepartmentResponse
from app.auth import get_current_user

router = APIRouter()


@router.get("/", response_model=list[DepartmentResponse])
def list_departments(company_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(Department).filter(Department.company_id == company_id).order_by(Department.code).all()


@router.post("/", response_model=DepartmentResponse)
def create_department(data: DepartmentCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    dept = Department(
        company_id=data.company_id,
        name=data.name,
        code=data.code,
        manager=data.manager,
        parent_id=data.parent_id,
    )
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept


@router.put("/{dept_id}", response_model=DepartmentResponse)
def update_department(
    dept_id: int, data: DepartmentUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)
):
    """修改部门信息。"""
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="部门不存在")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(dept, field, value)
    from datetime import datetime

    dept.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(dept)
    return dept


@router.post("/bulk-import")
def bulk_import_departments(
    company_id: int, rows: list[dict], db: Session = Depends(get_db), user=Depends(get_current_user)
):
    """批量导入部门。每行: {code, name, manager?, parent_id?, is_active?}"""
    imported = 0
    errors = []
    for i, row in enumerate(rows):
        code = row.get("code", "").strip()
        name = row.get("name", "").strip()
        if not code or not name:
            errors.append(f"第{i + 1}行缺少编码或名称")
            continue
        manager = row.get("manager", "").strip() or None
        parent_id = row.get("parent_id") or None
        parent_id = int(parent_id.strip()) if isinstance(parent_id, str) and parent_id.strip() else None
        is_active = row.get("is_active", True)
        if isinstance(is_active, str):
            is_active = is_active.lower() not in ("否", "停用", "false", "0", "no")
        existing = db.query(Department).filter(Department.company_id == company_id, Department.code == code).first()
        if existing:
            existing.name = name
            existing.manager = manager
            existing.is_active = is_active
            if parent_id is not None:
                existing.parent_id = parent_id
        else:
            dept = Department(
                company_id=company_id, code=code, name=name, manager=manager, is_active=is_active, parent_id=parent_id
            )
            db.add(dept)
        imported += 1
    db.commit()
    return {"imported": imported, "errors": errors}


@router.delete("/{dept_id}")
def delete_department(dept_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="部门不存在")
    dept.is_active = False
    db.commit()
    return {"ok": True}
