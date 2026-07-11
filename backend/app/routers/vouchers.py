"""凭证管理路由：创建/编辑/审核/记账/反记账。"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Voucher, VoucherEntry, BankSettlement, AccountingPeriod, AuditLog, Company, VoucherSequence
from app.schemas import VoucherCreate, VoucherUpdate, VoucherResponse, ReverseVoucherRequest
from app.auth import get_current_user
from app.permissions import (
    check_voucher_create,
    check_voucher_update,
    check_voucher_approve,
    check_voucher_post,
    check_voucher_reverse,
)
import contextlib

router = APIRouter()


def _check_period_open(db: Session, company_id: int, date_str: str):
    """检查凭证日期所在期间是否已关帐。关帐期间禁止新增/修改/审核/记账。"""
    period_str = date_str[:7]  # yyyy-MM-dd → yyyy-MM
    closed = (
        db.query(AccountingPeriod)
        .filter(
            AccountingPeriod.company_id == company_id,
            AccountingPeriod.period == period_str,
            AccountingPeriod.is_closed,
        )
        .first()
    )
    if closed:
        raise HTTPException(
            status_code=400,
            detail=f"会计期间 {period_str} 已关帐，禁止修改该期间的凭证。如需操作请先反结账。",
        )


def _get_company(db: Session, company_id: int) -> Company:
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="公司不存在")
    return company


def _generate_voucher_no(db: Session, company_id: int, voucher_type: str, date_str: str) -> str:
    """生成凭证字号：收字/付字/转字 + 年月 + 流水号。

    使用专用序列表 VoucherSequence 确保：
    - 每月每类型独立递增，只增不减
    - 删除的凭证号留空，永不递补
    - 用户不可手动修改凭证号
    """
    prefix_map = {"receipt": "收字", "payment": "付字", "transfer": "转字"}
    prefix = prefix_map.get(voucher_type, "转字")
    period = date_str[:7]  # 2026-07-03 → 2026-07
    month_str = period.replace("-", "")  # 202607

    seq_row = (
        db.query(VoucherSequence)
        .filter(
            VoucherSequence.company_id == company_id,
            VoucherSequence.voucher_type == voucher_type,
            VoucherSequence.period == period,
        )
        .first()
    )
    if seq_row:
        seq_row.last_seq += 1
    else:
        # 新月份/新类型的第一张凭证：先检查当月是否已有凭证（兼容历史数据）
        existing_max = (
            db.query(Voucher)
            .filter(
                Voucher.company_id == company_id,
                Voucher.voucher_type == voucher_type,
                Voucher.date.startswith(period),
            )
            .order_by(Voucher.id.desc())
            .first()
        )
        start_seq = 0
        if existing_max and existing_max.voucher_no:
            with contextlib.suppress(ValueError, IndexError):
                start_seq = int(existing_max.voucher_no.rsplit("-", 1)[-1])
        seq_row = VoucherSequence(
            company_id=company_id,
            voucher_type=voucher_type,
            period=period,
            last_seq=start_seq + 1,
        )
        db.add(seq_row)
    db.flush()
    return f"{prefix}{month_str}-{seq_row.last_seq:04d}"


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

    _check_period_open(db, data.company_id, data.date)

    total_debit = sum(e.debit for e in data.entries)
    total_credit = sum(e.credit for e in data.entries)
    if abs(total_debit - total_credit) > 0.005:
        raise HTTPException(status_code=400, detail="借贷不平衡")

    voucher = Voucher(
        company_id=data.company_id,
        date=data.date,
        voucher_no=_generate_voucher_no(db, data.company_id, data.voucher_type, data.date),
        voucher_type=data.voucher_type,
        summary=data.summary,
        creator_id=user.id,
    )
    db.add(voucher)
    db.flush()

    for entry in data.entries:
        e = VoucherEntry(
            voucher_id=voucher.id,
            account_code=entry.account_code,
            department_id=entry.department_id,
            counterparty_id=entry.counterparty_id,
            person_id=entry.person_id,
            project_id=entry.project_id,
            debit=entry.debit,
            credit=entry.credit,
            description=entry.description,
        )
        db.add(e)
        db.flush()
        if entry.settlements:
            for s in entry.settlements:
                db.add(
                    BankSettlement(
                        voucher_entry_id=e.id,
                        seq=s.seq,
                        settlement_method=s.settlement_method,
                        account_name=s.account_name,
                        instrument_no=s.instrument_no,
                        instrument_date=s.instrument_date,
                        direction=s.direction,
                        amount=s.amount,
                    )
                )

    db.commit()
    db.refresh(voucher)
    return voucher


@router.put("/{voucher_id}", response_model=VoucherResponse)
def update_voucher(
    voucher_id: int, data: VoucherUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
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

    # 在日期更新后检查关帐锁定（防止将凭证改到已关帐月份）
    _check_period_open(db, voucher.company_id, voucher.date)

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
            e = VoucherEntry(
                voucher_id=voucher_id,
                account_code=entry.account_code,
                department_id=entry.department_id,
                counterparty_id=entry.counterparty_id,
                person_id=entry.person_id,
                project_id=entry.project_id,
                debit=entry.debit,
                credit=entry.credit,
                description=entry.description,
            )
            db.add(e)
            db.flush()
            if entry.settlements:
                for s in entry.settlements:
                    db.add(
                        BankSettlement(
                            voucher_entry_id=e.id,
                            seq=s.seq,
                            settlement_method=s.settlement_method,
                            account_name=s.account_name,
                            instrument_no=s.instrument_no,
                            instrument_date=s.instrument_date,
                            direction=s.direction,
                            amount=s.amount,
                        )
                    )

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

    _check_period_open(db, voucher.company_id, voucher.date)

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

    _check_period_open(db, voucher.company_id, voucher.date)

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
def reverse_voucher(
    voucher_id: int, req: ReverseVoucherRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
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
    period = (
        db.query(AccountingPeriod)
        .filter(
            AccountingPeriod.company_id == voucher.company_id,
            AccountingPeriod.period == period_str,
            AccountingPeriod.is_closed,
        )
        .first()
    )
    if period:
        raise HTTPException(status_code=400, detail="该期间已结账，需先反结账")

    voucher.status = "reversed"
    voucher.reversed_by = user.id
    voucher.reversed_at = datetime.now(timezone.utc)
    voucher.reverse_reason = req.reason

    db.add(
        AuditLog(
            company_id=voucher.company_id,
            user_id=user.id,
            action="reverse_post",
            target_type="voucher",
            target_id=voucher_id,
            reason=req.reason,
        )
    )
    db.commit()
    db.refresh(voucher)
    return voucher


@router.post("/{voucher_id}/unpost", response_model=VoucherResponse)
def unpost_voucher(voucher_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """取消记账：将已记账凭证回退到审核通过/草稿状态。"""
    voucher = db.query(Voucher).filter(Voucher.id == voucher_id).first()
    if not voucher:
        raise HTTPException(status_code=404, detail="凭证不存在")
    if voucher.status != "posted":
        raise HTTPException(status_code=400, detail="只能取消已记账凭证")

    _check_period_open(db, voucher.company_id, voucher.date)

    company = _get_company(db, voucher.company_id)
    err = check_voucher_reverse(user, company)
    if err:
        raise HTTPException(status_code=403, detail=err)

    # 回到审批前状态（若跳过审批则为草稿）
    new_status = "draft" if voucher.approved_by is None else "approved"
    voucher.status = new_status
    voucher.posted_by = None
    voucher.posted_at = None

    db.add(
        AuditLog(
            company_id=voucher.company_id,
            user_id=user.id,
            action="unpost_voucher",
            target_type="voucher",
            target_id=voucher_id,
            reason="取消记账",
        )
    )
    db.commit()
    db.refresh(voucher)
    return voucher


@router.post("/{voucher_id}/unapprove", response_model=VoucherResponse)
def unapprove_voucher(voucher_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """取消审核：将已审核凭证回退到草稿状态。"""
    voucher = db.query(Voucher).filter(Voucher.id == voucher_id).first()
    if not voucher:
        raise HTTPException(status_code=404, detail="凭证不存在")
    if voucher.status != "approved":
        raise HTTPException(status_code=400, detail="只能取消已审核凭证")

    _check_period_open(db, voucher.company_id, voucher.date)

    company = _get_company(db, voucher.company_id)
    err = check_voucher_approve(user, company, voucher.creator_id)
    if err:
        raise HTTPException(status_code=403, detail=err)

    voucher.status = "draft"
    voucher.approved_by = None
    voucher.approved_at = None

    db.add(
        AuditLog(
            company_id=voucher.company_id,
            user_id=user.id,
            action="unapprove_voucher",
            target_type="voucher",
            target_id=voucher_id,
            reason="取消审核",
        )
    )
    db.commit()
    db.refresh(voucher)
    return voucher


@router.post("/{voucher_id}/unreverse", response_model=VoucherResponse)
def unreverse_voucher(voucher_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """取消冲销：将已冲销凭证恢复为已记账状态。"""
    voucher = db.query(Voucher).filter(Voucher.id == voucher_id).first()
    if not voucher:
        raise HTTPException(status_code=404, detail="凭证不存在")
    if voucher.status != "reversed":
        raise HTTPException(status_code=400, detail="只能取消已冲销凭证")

    _check_period_open(db, voucher.company_id, voucher.date)

    company = _get_company(db, voucher.company_id)
    err = check_voucher_reverse(user, company)
    if err:
        raise HTTPException(status_code=403, detail=err)

    voucher.status = "posted"
    voucher.reversed_by = None
    voucher.reversed_at = None
    voucher.reverse_reason = None

    db.add(
        AuditLog(
            company_id=voucher.company_id,
            user_id=user.id,
            action="unreverse_voucher",
            target_type="voucher",
            target_id=voucher_id,
            reason="取消冲销",
        )
    )
    db.commit()
    db.refresh(voucher)
    return voucher


# ── 历史凭证批量导入 ──


@router.post("/batch-import")
def batch_import_vouchers(
    data: list[VoucherCreate],
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """批量导入历史凭证（跳过关帐检查和借贷平衡校验）。"""
    if not data:
        raise HTTPException(status_code=400, detail="导入数据为空")

    data[0].company_id
    imported = 0
    for item in data:
        voucher = Voucher(
            company_id=item.company_id,
            date=item.date,
            voucher_no=item.voucher_no or _generate_voucher_no(db, item.company_id, item.voucher_type, item.date),
            voucher_type=item.voucher_type,
            summary=item.summary,
            creator_id=user.id,
            status="posted",
        )
        db.add(voucher)
        db.flush()
        for entry in item.entries:
            e = VoucherEntry(
                voucher_id=voucher.id,
                account_code=entry.account_code,
                debit=entry.debit,
                credit=entry.credit,
                description=entry.description,
            )
            db.add(e)
        imported += 1

    db.commit()
    return {"imported": imported, "message": f"成功导入 {imported} 张历史凭证"}


@router.get("/archive")
def list_archive_vouchers(
    company_id: int,
    year: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """查询某年度的所有凭证（含历史导入）。"""
    vouchers = (
        db.query(Voucher)
        .filter(
            Voucher.company_id == company_id,
            Voucher.date >= f"{year}-01-01",
            Voucher.date <= f"{year}-12-31",
        )
        .order_by(Voucher.date)
        .all()
    )
    result = []
    for v in vouchers:
        entries = db.query(VoucherEntry).filter(VoucherEntry.voucher_id == v.id).all()
        total_debit = sum(e.debit for e in entries)
        result.append(
            {
                "id": v.id,
                "date": v.date,
                "voucher_no": v.voucher_no,
                "voucher_type": v.voucher_type,
                "summary": v.summary,
                "status": v.status,
                "total_debit": total_debit,
                "entry_count": len(entries),
            }
        )
    return result
