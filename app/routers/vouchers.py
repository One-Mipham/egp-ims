"""凭证管理路由：创建/编辑/审核/记账/反记账。"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Voucher, VoucherEntry, BankSettlement, AccountingPeriod, AuditLog, Company
from app.schemas import VoucherCreate, VoucherUpdate, VoucherResponse, VoucherEntryResponse, ReverseVoucherRequest
from app.auth import get_current_user
from app.permissions import (
    check_voucher_create, check_voucher_update, check_voucher_approve,
    check_voucher_post, check_voucher_reverse,
)

router = APIRouter()


def _get_company(db: Session, company_id: int) -> Company:
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="公司不存在")
    return company


def _generate_voucher_no(db: Session, company_id: int, voucher_type: str) -> str:
    """生成凭证字号：收字/付字/转字 + 年月 + 流水号。"""
    prefix_map = {"receipt": "收字", "payment": "付字", "transfer": "转字"}
    prefix = prefix_map.get(voucher_type, "转字")
    now = datetime.now(timezone.utc)
    month_str = now.strftime("%Y%m")
    count = db.query(Voucher).filter(
        Voucher.company_id == company_id,
        Voucher.date.startswith(now.strftime("%Y-%m")),
    ).count()
    return f"{prefix}{month_str}-{count + 1:04d}"


@router.get("/", response_model=list[VoucherResponse])
def list_vouchers(
    company_id: int,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    voucher_no: Optional[str] = Query(None),
    voucher_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(Voucher).filter(Voucher.company_id == company_id)
    if start_date:
        q = q.filter(Voucher.date >= start_date)
    if end_date:
        q = q.filter(Voucher.date <= end_date)
    if voucher_no:
        q = q.filter(Voucher.voucher_no.contains(voucher_no))
    if voucher_type:
        q = q.filter(Voucher.voucher_type == voucher_type)
    if status:
        q = q.filter(Voucher.status == status)
    return q.order_by(Voucher.date.desc()).all()


@router.post("/", response_model=VoucherResponse)
def create_voucher(data: VoucherCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    company = _get_company(db, data.company_id)
    err = check_voucher_create(user, company)
    if err:
        raise HTTPException(status_code=403, detail=err)

    total_debit = sum(e.debit for e in data.entries)
    total_credit = sum(e.credit for e in data.entries)
    if abs(total_debit - total_credit) > 0.005:
        raise HTTPException(status_code=400, detail="借贷不平衡")

    voucher = Voucher(
        company_id=data.company_id, date=data.date, voucher_no=_generate_voucher_no(db, data.company_id, data.voucher_type),
        voucher_type=data.voucher_type, summary=data.summary, creator_id=user.id,
    )
    db.add(voucher)
    db.flush()

    for entry in data.entries:
        e = VoucherEntry(voucher_id=voucher.id, account_code=entry.account_code, department_id=entry.department_id, counterparty_id=entry.counterparty_id, person_id=entry.person_id, project_id=entry.project_id, debit=entry.debit, credit=entry.credit, description=entry.description)
        db.add(e)
        db.flush()
        if entry.settlements:
            for s in entry.settlements:
                db.add(BankSettlement(voucher_entry_id=e.id, seq=s.seq, settlement_method=s.settlement_method, account_name=s.account_name, instrument_no=s.instrument_no, instrument_date=s.instrument_date, direction=s.direction, amount=s.amount))

    db.commit()
    db.refresh(voucher)
    return voucher


@router.put("/{voucher_id}", response_model=VoucherResponse)
def update_voucher(voucher_id: int, data: VoucherUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    voucher = db.query(Voucher).filter(Voucher.id == voucher_id).first()
    if not voucher:
        raise HTTPException(status_code=404, detail="凭证不存在")
    if voucher.status != "draft":
        raise HTTPException(status_code=400, detail="只能修改草稿状态凭证")

    company = _get_company(db, voucher.company_id)
    err = check_voucher_update(user, company, voucher.creator_id)
    if err:
        raise HTTPException(status_code=403, detail=err)

    if data.summary:
        voucher.summary = data.summary
    if data.date:
        voucher.date = data.date
    if data.voucher_type:
        voucher.voucher_type = data.voucher_type

    if data.entries is not None:
        total_debit = sum(e.debit for e in data.entries)
        total_credit = sum(e.credit for e in data.entries)
        if abs(total_debit - total_credit) > 0.005:
            raise HTTPException(status_code=400, detail="借贷不平衡")
        # 先删银行结算明细（query.delete 不触发级联），再删分录
        old_entries = db.query(VoucherEntry).filter(VoucherEntry.voucher_id == voucher_id).all()
        for oe in old_entries:
            db.query(BankSettlement).filter(BankSettlement.voucher_entry_id == oe.id).delete()
        db.query(VoucherEntry).filter(VoucherEntry.voucher_id == voucher_id).delete()
        for entry in data.entries:
            e = VoucherEntry(voucher_id=voucher_id, account_code=entry.account_code, department_id=entry.department_id, counterparty_id=entry.counterparty_id, person_id=entry.person_id, project_id=entry.project_id, debit=entry.debit, credit=entry.credit, description=entry.description)
            db.add(e)
            db.flush()
            if entry.settlements:
                for s in entry.settlements:
                    db.add(BankSettlement(voucher_entry_id=e.id, seq=s.seq, settlement_method=s.settlement_method, account_name=s.account_name, instrument_no=s.instrument_no, instrument_date=s.instrument_date, direction=s.direction, amount=s.amount))

    db.commit()
    db.refresh(voucher)
    return voucher


@router.post("/{voucher_id}/approve", response_model=VoucherResponse)
def approve_voucher(voucher_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """审核凭证。"""
    voucher = db.query(Voucher).filter(Voucher.id == voucher_id).first()
    if not voucher:
        raise HTTPException(status_code=404, detail="凭证不存在")
    if voucher.status != "draft":
        raise HTTPException(status_code=400, detail="凭证状态不可审核")

    company = _get_company(db, voucher.company_id)
    err = check_voucher_approve(user, company, voucher.creator_id)
    if err:
        raise HTTPException(status_code=403, detail=err)

    voucher.status = "approved"
    voucher.approved_by = user.id
    voucher.approved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(voucher)
    return voucher


@router.post("/{voucher_id}/post", response_model=VoucherResponse)
def post_voucher(voucher_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """记账：影响科目余额。"""
    voucher = db.query(Voucher).filter(Voucher.id == voucher_id).first()
    if not voucher:
        raise HTTPException(status_code=404, detail="凭证不存在")
    if voucher.status not in ("draft", "approved"):
        raise HTTPException(status_code=400, detail="凭证状态不可记账")

    company = _get_company(db, voucher.company_id)
    err = check_voucher_post(user, company)
    if err:
        raise HTTPException(status_code=403, detail=err)

    voucher.status = "posted"
    voucher.posted_by = user.id
    voucher.posted_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(voucher)
    return voucher


@router.post("/{voucher_id}/reverse", response_model=VoucherResponse)
def reverse_voucher(voucher_id: int, req: ReverseVoucherRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """反记账：需填写原因。"""
    voucher = db.query(Voucher).filter(Voucher.id == voucher_id).first()
    if not voucher:
        raise HTTPException(status_code=404, detail="凭证不存在")
    if voucher.status != "posted":
        raise HTTPException(status_code=400, detail="只能反记账已记账凭证")

    company = _get_company(db, voucher.company_id)
    err = check_voucher_reverse(user, company)
    if err:
        raise HTTPException(status_code=403, detail=err)

    # 检查是否已结账
    period_str = voucher.date[:7]
    period = db.query(AccountingPeriod).filter(
        AccountingPeriod.company_id == voucher.company_id,
        AccountingPeriod.period == period_str,
        AccountingPeriod.is_closed == True,
    ).first()
    if period:
        raise HTTPException(status_code=400, detail="该期间已结账，需先反结账")

    voucher.status = "reversed"
    voucher.reversed_by = user.id
    voucher.reversed_at = datetime.now(timezone.utc)
    voucher.reverse_reason = req.reason

    db.add(AuditLog(company_id=voucher.company_id, user_id=user.id, action="reverse_post", target_type="voucher", target_id=voucher_id, reason=req.reason))
    db.commit()
    db.refresh(voucher)
    return voucher
