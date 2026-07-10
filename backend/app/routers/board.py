"""董事办 — API 路由."""

from datetime import date, datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models import BoardFiling, BoardShareholder
from app.schemas.board import (
    BoardFilingCreate,
    BoardFilingUpdate,
    BoardFilingResponse,
    BoardShareholderCreate,
    BoardShareholderUpdate,
    BoardShareholderResponse,
    BoardCockpitResponse,
    CockpitLight,
)

router = APIRouter()


# ═══════════ 驾驶舱红绿灯 ═══════════


def _compute_light(filings: list, today: date) -> str:
    """判定红绿灯：有逾期 → red；7天内截止 → yellow；无逾期无待提交 → green"""
    has_pending = False
    for f in filings:
        if f.status in ("已完成", "已提交", "已反馈"):
            continue
        if f.deadline:
            try:
                dl = date.fromisoformat(f.deadline)
                if dl < today:
                    return "red"
                if dl <= today + timedelta(days=7):
                    return "yellow"
            except ValueError:
                pass
        has_pending = True
    if has_pending:
        return "green"  # 有pending但deadline还很远
    return "green"


@router.get("/cockpit-lights", response_model=BoardCockpitResponse)
def cockpit_lights(company_id: int = Query(...), db: Session = Depends(get_db), user=Depends(get_current_user)):
    today = date.today()
    lights = []

    # 证监会/局规定文件
    csrc = (
        db.query(BoardFiling)
        .filter(
            BoardFiling.company_id == company_id,
            BoardFiling.doc_type == "filing",
            BoardFiling.doc_subtype == "csrc",
        )
        .all()
    )
    lights.append(CockpitLight(label="证监会/局规定文件", status=_compute_light(csrc, today)))

    # 交易所规定文件
    exchange = (
        db.query(BoardFiling)
        .filter(
            BoardFiling.company_id == company_id,
            BoardFiling.doc_type == "filing",
            BoardFiling.doc_subtype == "exchange",
        )
        .all()
    )
    lights.append(CockpitLight(label="交易所规定文件", status=_compute_light(exchange, today)))

    # 股东大会法律文件
    shareholder_filing = (
        db.query(BoardFiling)
        .filter(
            BoardFiling.company_id == company_id,
            BoardFiling.doc_type == "filing",
            BoardFiling.doc_subtype == "shareholder",
        )
        .all()
    )
    lights.append(CockpitLight(label="股东大会法律文件", status=_compute_light(shareholder_filing, today)))

    # 财务部门报备文件
    finance = (
        db.query(BoardFiling)
        .filter(
            BoardFiling.company_id == company_id,
            BoardFiling.doc_type == "filing",
            BoardFiling.doc_subtype == "finance",
        )
        .all()
    )
    lights.append(CockpitLight(label="财务部门报备文件", status=_compute_light(finance, today)))

    # 内部报批事项
    approvals = (
        db.query(BoardFiling)
        .filter(
            BoardFiling.company_id == company_id,
            BoardFiling.doc_type == "approval",
        )
        .all()
    )
    has_unfinished = any(a.status not in ("已完成",) for a in approvals) if approvals else False
    approvals_status = "yellow" if has_unfinished else "green"
    if not approvals:
        approvals_status = "green"
    lights.append(CockpitLight(label="内部报批事项", status=approvals_status))

    # 档案完整度
    archives = (
        db.query(BoardFiling)
        .filter(
            BoardFiling.company_id == company_id,
            BoardFiling.doc_type == "archive",
        )
        .all()
    )
    recent = (
        [a for a in archives if a.updated_at and a.updated_at.date() >= today - timedelta(days=30)] if archives else []
    )
    archive_status = "green" if recent else ("yellow" if archives else "green")
    lights.append(CockpitLight(label="档案完整度", status=archive_status))

    return BoardCockpitResponse(lights=lights)


# ═══════════ BoardFiling CRUD ═══════════


@router.get("/filings", response_model=List[BoardFilingResponse])
def list_filings(
    company_id: int = Query(...),
    doc_type: str = Query(None),
    doc_subtype: str = Query(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    q = db.query(BoardFiling).filter(BoardFiling.company_id == company_id)
    if doc_type:
        q = q.filter(BoardFiling.doc_type == doc_type)
    if doc_subtype:
        q = q.filter(BoardFiling.doc_subtype == doc_subtype)
    return q.order_by(BoardFiling.updated_at.desc()).all()


@router.get("/filings/{filing_id}", response_model=BoardFilingResponse)
def get_filing(filing_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    obj = db.query(BoardFiling).filter(BoardFiling.id == filing_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="记录不存在")
    return obj


@router.post("/filings", response_model=BoardFilingResponse)
def create_filing(data: BoardFilingCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    obj = BoardFiling(**data.model_dump(), created_by=user.id)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.put("/filings/{filing_id}", response_model=BoardFilingResponse)
def update_filing(
    filing_id: int, data: BoardFilingUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)
):
    obj = db.query(BoardFiling).filter(BoardFiling.id == filing_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="记录不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/filings/{filing_id}")
def delete_filing(filing_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    obj = db.query(BoardFiling).filter(BoardFiling.id == filing_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(obj)
    db.commit()
    return {"ok": True}


@router.post("/filings/upsert", response_model=BoardFilingResponse)
def upsert_filing(data: BoardFilingCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Policy 视图使用的 upsert — 按 company_id + doc_type + doc_subtype + title 去重"""
    existing = (
        db.query(BoardFiling)
        .filter(
            BoardFiling.company_id == data.company_id,
            BoardFiling.doc_type == data.doc_type,
            BoardFiling.title == data.title,
        )
        .first()
    )
    if existing:
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(existing, k, v)
        existing.updated_at = datetime.utcnow()
    else:
        existing = BoardFiling(**data.model_dump(), created_by=user.id)
        db.add(existing)
    db.commit()
    db.refresh(existing)
    return existing


# ═══════════ BoardShareholder CRUD ═══════════


@router.get("/shareholders", response_model=List[BoardShareholderResponse])
def list_shareholders(company_id: int = Query(...), db: Session = Depends(get_db), user=Depends(get_current_user)):
    return (
        db.query(BoardShareholder)
        .filter(
            BoardShareholder.company_id == company_id,
        )
        .order_by(BoardShareholder.share_ratio.desc())
        .all()
    )


@router.post("/shareholders", response_model=BoardShareholderResponse)
def create_shareholder(data: BoardShareholderCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    obj = BoardShareholder(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.put("/shareholders/{shareholder_id}", response_model=BoardShareholderResponse)
def update_shareholder(
    shareholder_id: int, data: BoardShareholderUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)
):
    obj = db.query(BoardShareholder).filter(BoardShareholder.id == shareholder_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="记录不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/shareholders/{shareholder_id}")
def delete_shareholder(shareholder_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    obj = db.query(BoardShareholder).filter(BoardShareholder.id == shareholder_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(obj)
    db.commit()
    return {"ok": True}
