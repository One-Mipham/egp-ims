"""审计日志路由。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AuditLog, User
from app.schemas import AuditLogResponse
from app.auth import get_current_user

router = APIRouter()


@router.get("/", response_model=list[AuditLogResponse])
def list_logs(company_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return (
        db.query(AuditLog)
        .filter(AuditLog.company_id == company_id)
        .order_by(AuditLog.created_at.desc())
        .all()
    )
