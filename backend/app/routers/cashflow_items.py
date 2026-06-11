"""现金流量表项目映射管理路由。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import CashFlowItem
from app.schemas import CashFlowItemCreate, CashFlowItemUpdate, CashFlowItemResponse
from app.auth import get_current_user

router = APIRouter()


@router.get("/", response_model=list[CashFlowItemResponse])
def list_cashflow_items(company_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """列出某公司的全部现金流量项目映射。"""
    return db.query(CashFlowItem).filter(
        CashFlowItem.company_id == company_id
    ).order_by(CashFlowItem.code).all()


@router.post("/", response_model=CashFlowItemResponse)
def create_cashflow_item(data: CashFlowItemCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """新增现金流量项目映射。"""
    existing = db.query(CashFlowItem).filter(
        CashFlowItem.company_id == data.company_id,
        CashFlowItem.code == data.code,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"项目编码 {data.code} 已存在")

    item = CashFlowItem(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{item_id}", response_model=CashFlowItemResponse)
def update_cashflow_item(item_id: int, data: CashFlowItemUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """更新现金流量项目映射（如修改对方科目范围）。"""
    item = db.query(CashFlowItem).filter(CashFlowItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="项目不存在")

    updates = data.model_dump(exclude_unset=True)
    for key, val in updates.items():
        setattr(item, key, val)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}")
def delete_cashflow_item(item_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """删除现金流量项目映射。"""
    item = db.query(CashFlowItem).filter(CashFlowItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="项目不存在")
    db.delete(item)
    db.commit()
    return {"ok": True}


@router.post("/seed-defaults")
def seed_default_items(company_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """为指定公司重置/补齐国标预设的现金流量项目映射。"""
    from app.seed import seed_cashflow_items
    seed_cashflow_items(db, company_id)
    return {"ok": True, "message": "已补齐国标预设项目"}
