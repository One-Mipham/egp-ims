"""合同管理路由."""

import os
import shutil
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.auth import get_current_user
from app.models import Contract, Department, User
from app.schemas.contracts import (
    CONTRACT_CATEGORIES,
    LEGAL_BASIS_OPTIONS,
    ContractCreate,
    ContractUpdate,
    ContractResponse,
    ContractStatsResponse,
)

router = APIRouter()


def _generate_contract_no(company_id: int, db: Session) -> str:
    today = date.today().strftime("%Y%m%d")
    count = (
        db.query(Contract)
        .filter(
            Contract.company_id == company_id,
            Contract.contract_no.like(f"CT-{today}-%"),
        )
        .count()
    )
    return f"CT-{today}-{count + 1:03d}"


# ── 权限辅助 ──

PERMITTED_ROLES = {"finance_manager", "finance_director", "super_admin"}


def _can_view_all(user: User) -> bool:
    return user.role in PERMITTED_ROLES


def _apply_permission_filter(q, user: User):
    """非授权角色只能查看自己经办/审核/批准的合同."""
    if _can_view_all(user):
        return q
    return q.filter(
        (Contract.owner_id == user.id) | (Contract.reviewer_id == user.id) | (Contract.approver_id == user.id)
    )


def _check_single_permission(contract: Contract, user: User):
    """检查单条合同权限，无权限则抛 404."""
    if _can_view_all(user):
        return
    if contract.owner_id == user.id:
        return
    if contract.reviewer_id == user.id:
        return
    if contract.approver_id == user.id:
        return
    raise HTTPException(status_code=404, detail="合同不存在")


# ── 合同 CRUD ──


@router.get("", response_model=list[ContractResponse])
def list_contracts(
    company_id: int = Query(...),
    contract_type: str | None = Query(None),
    contract_category: str | None = Query(None),
    department_id: int | None = Query(None),
    status: str | None = Query(None),
    search: str | None = Query(None, description="搜索合同号/事由/对方名称"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    q = db.query(Contract).filter(Contract.company_id == company_id)
    q = _apply_permission_filter(q, user)
    if contract_type:
        q = q.filter(Contract.contract_type == contract_type)
    if contract_category:
        q = q.filter(Contract.contract_category == contract_category)
    if department_id:
        q = q.filter(Contract.department_id == department_id)
    if status:
        q = q.filter(Contract.status == status)
    if search:
        like = f"%{search}%"
        q = q.filter(
            Contract.contract_no.like(like)
            | Contract.contract_name.like(like)
            | Contract.subject.like(like)
            | Contract.party_a.like(like)
            | Contract.party_b.like(like)
        )
    return q.order_by(Contract.id.desc()).all()


@router.get("/categories", response_model=list[str])
def get_categories(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """返回预设类别 + 已使用过的自定义类别."""
    used = db.query(Contract.contract_category).distinct().all()
    custom = [r[0] for r in used if r[0] and r[0] not in CONTRACT_CATEGORIES]
    return CONTRACT_CATEGORIES + sorted(custom)


@router.get("/legal-basis", response_model=list[str])
def get_legal_basis(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """返回法律依据选项."""
    return LEGAL_BASIS_OPTIONS


# ── 统计（必须在 /{contract_id} 之前注册） ──


@router.get("/stats", response_model=ContractStatsResponse)
def get_stats(
    company_id: int = Query(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    base = db.query(Contract).filter(Contract.company_id == company_id)
    total_count = base.count()
    total_amount = base.with_entities(func.coalesce(func.sum(Contract.amount), 0)).scalar()

    def _group(col):
        rows = base.with_entities(col, func.count(), func.coalesce(func.sum(Contract.amount), 0)).group_by(col).all()
        return {r[0] or "未分类": {"count": r[1], "amount": round(r[2], 2)} for r in rows}

    by_type = _group(Contract.contract_type)
    by_category = _group(Contract.contract_category)
    by_status = base.with_entities(Contract.status, func.count()).group_by(Contract.status).all()
    by_status = {r[0]: r[1] for r in by_status}

    # 按部门
    dept_rows = (
        base.with_entities(Department.name, func.count(), func.coalesce(func.sum(Contract.amount), 0))
        .outerjoin(Department, Contract.department_id == Department.id)
        .group_by(Department.name)
        .all()
    )
    by_department = {r[0] or "未分配": {"count": r[1], "amount": round(r[2], 2)} for r in dept_rows}

    return ContractStatsResponse(
        total_count=total_count,
        total_amount=round(total_amount, 2),
        by_type=by_type,
        by_category=by_category,
        by_department=by_department,
        by_status=by_status,
    )


# ── 单条 CRUD ──


@router.get("/{contract_id}", response_model=ContractResponse)
def get_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    c = db.query(Contract).filter(Contract.id == contract_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="合同不存在")
    _check_single_permission(c, user)
    return c


@router.post("", response_model=ContractResponse)
def create_contract(
    data: ContractCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    c = Contract(**data.model_dump())
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@router.put("/{contract_id}", response_model=ContractResponse)
def update_contract(
    contract_id: int,
    data: ContractUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    c = db.query(Contract).filter(Contract.id == contract_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="合同不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(c, k, v)
    db.commit()
    db.refresh(c)
    return c


@router.delete("/{contract_id}")
def delete_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    c = db.query(Contract).filter(Contract.id == contract_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="合同不存在")
    db.delete(c)
    db.commit()
    return {"ok": True}


# ── 审批流程（非强制） ──


@router.post("/{contract_id}/review")
def review_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    c = db.query(Contract).filter(Contract.id == contract_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="合同不存在")
    c.reviewer_id = user.id
    c.reviewed_at = datetime.utcnow()
    db.commit()
    return {"ok": True, "reviewed": True}


@router.post("/{contract_id}/approve")
def approve_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    c = db.query(Contract).filter(Contract.id == contract_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="合同不存在")
    c.approver_id = user.id
    c.approved_at = datetime.utcnow()
    c.status = "active"
    db.commit()
    return {"ok": True, "approved": True}


@router.post("/{contract_id}/seal")
def seal_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    c = db.query(Contract).filter(Contract.id == contract_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="合同不存在")
    c.sealer_id = user.id
    c.sealed_at = datetime.utcnow()
    db.commit()
    return {"ok": True, "sealed": True}


# ── 扫描件上传 ──

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "contracts")


@router.post("/{contract_id}/scan")
def upload_scan(
    contract_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    c = db.query(Contract).filter(Contract.id == contract_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="合同不存在")
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(file.filename or "scan.pdf")[1] or ".pdf"
    safe_name = f"contract_{contract_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{ext}"
    dest = os.path.join(UPLOAD_DIR, safe_name)
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    c.scan_file_path = f"uploads/contracts/{safe_name}"
    c.archived_at = datetime.utcnow()
    db.commit()
    db.refresh(c)
    return {"ok": True, "scan_file_path": c.scan_file_path}


# ── 闭环确认 ──


@router.post("/{contract_id}/closure-confirm")
def confirm_closure(
    contract_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    c = db.query(Contract).filter(Contract.id == contract_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="合同不存在")
    c.closure_confirmed = True
    c.closure_confirmed_at = datetime.utcnow()
    c.closure_confirmed_by = user.id
    c.status = "completed"
    db.commit()
    db.refresh(c)
    return {"ok": True, "closure_confirmed": True}
