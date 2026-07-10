"""凭证模板路由。"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import VoucherTemplate, User
from app.auth import get_current_user

router = APIRouter()


@router.get("/")
def list_templates(company_id: int = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q = db.query(VoucherTemplate)
    if company_id:
        q = q.filter(VoucherTemplate.company_id == company_id).filter(VoucherTemplate.type == "user_defined")
    # 始终包含内置模板
    q = q.filter((VoucherTemplate.company_id == company_id) | (VoucherTemplate.company_id is None))
    return q.all()


@router.post("/")
def create_template(name: str, entries: dict, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    t = VoucherTemplate(name=name, type="user_defined", entries=entries, user_id=user.id)
    db.add(t)
    db.commit()
    db.refresh(t)
    return {"id": t.id, "name": t.name}
