"""门禁管理 — 人员出入记录 API Router"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models import User, AccessRecord

router = APIRouter()


@router.get("/")
def list_records(
    company_id: int = Query(...),
    direction: str | None = Query(None),
    person_name: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """列出出入记录，支持筛选和分页。"""
    q = db.query(AccessRecord).filter(AccessRecord.company_id == company_id)
    if direction:
        q = q.filter(AccessRecord.direction == direction)
    if person_name:
        q = q.filter(AccessRecord.person_name.contains(person_name))
    total = q.count()
    records = q.order_by(AccessRecord.record_time.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "records": [
            {
                "id": r.id,
                "person_name": r.person_name,
                "department": r.department,
                "phone": r.phone,
                "direction": r.direction,
                "access_point": r.access_point,
                "reason": r.reason,
                "record_time": r.record_time.isoformat() if r.record_time else None,
                "notes": r.notes,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in records
        ],
    }


@router.post("/")
def create_record(
    company_id: int = Query(...),
    person_name: str = Query(...),
    direction: str = Query("entry"),
    department: str = Query(None),
    phone: str = Query(None),
    access_point: str = Query(None),
    reason: str = Query(None),
    notes: str = Query(None),
    record_time: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """登记出入记录。"""
    rt = datetime.fromisoformat(record_time) if record_time else datetime.utcnow()
    record = AccessRecord(
        company_id=company_id,
        person_name=person_name,
        department=department,
        phone=phone,
        direction=direction,
        access_point=access_point,
        reason=reason,
        record_time=rt,
        notes=notes,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return {"ok": True, "id": record.id}


@router.delete("/{record_id}")
def delete_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除出入记录。"""
    record = db.query(AccessRecord).filter(AccessRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(record)
    db.commit()
    return {"ok": True}
