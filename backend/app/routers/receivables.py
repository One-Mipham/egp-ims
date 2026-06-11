"""应收账款管理 — 发票 CRUD + 收款 + 账龄 + 审计 + 凭证 + CSV."""
import csv as csv_mod
import io
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user
from app.models import Receivable, ReceivablePayment, Counterparty, Voucher, VoucherEntry, AuditLog, User
from app.schemas import (
    ReceivableCreate, ReceivableResponse,
    ReceivablePaymentCreate, ReceivablePaymentResponse,
)

router = APIRouter()


# ═══════════ 审计辅助 ═══════════

def _audit(db: Session, user: User, action: str, target_type: str, target_id: int | None = None, details: dict | None = None):
    db.add(AuditLog(
        company_id=getattr(user, 'company_id', 1),
        user_id=user.id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
        created_at=datetime.utcnow(),
    ))


# ═══════════ 凭证生成 ═══════════

def _generate_voucher(db: Session, company_id: int, user_id: int, vtype: str, summary: str, entries: list[dict]):
    vdate = datetime.utcnow().strftime("%Y-%m-%d")
    voucher_no = f"{vtype}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    voucher = Voucher(
        company_id=company_id,
        date=vdate,
        voucher_no=voucher_no,
        voucher_type=vtype,
        summary=summary,
        creator_id=user_id,
        status="posted",
    )
    db.add(voucher)
    db.flush()
    for e in entries:
        db.add(VoucherEntry(
            voucher_id=voucher.id,
            account_code=e["account_code"],
            debit=e.get("debit", 0),
            credit=e.get("credit", 0),
            description=e.get("description", ""),
        ))
    return voucher


# ═══════════ 应收发票 CRUD ═══════════

@router.get("/invoices", response_model=list[ReceivableResponse])
def list_receivables(
    company_id: int,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    status: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(Receivable).filter(Receivable.company_id == company_id)
    if status:
        q = q.filter(Receivable.status == status)
    if start_date:
        q = q.filter(Receivable.invoice_date >= start_date)
    if end_date:
        q = q.filter(Receivable.invoice_date <= end_date)
    if search:
        pattern = f"%{search}%"
        q = q.filter(
            (Receivable.customer_name.ilike(pattern)) |
            (Receivable.invoice_no.ilike(pattern))
        )
    return q.order_by(Receivable.id.desc()).offset(offset).limit(limit).all()


@router.get("/invoices/csv")
def export_receivables_csv(
    company_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """导出应收发票为 CSV"""
    items = db.query(Receivable).filter(Receivable.company_id == company_id).order_by(Receivable.id.desc()).all()
    output = io.StringIO()
    writer = csv_mod.writer(output)
    writer.writerow(["客户名称", "发票号", "发票日期", "金额", "已收金额", "余额", "到期日", "账龄(天)", "状态", "备注"])
    for i in items:
        writer.writerow([i.customer_name, i.invoice_no, i.invoice_date or "", i.amount, i.received_amount, i.balance, i.due_date or "", i.aging_days, i.status, i.notes or ""])
    output.seek(0)
    return StreamingResponse(io.BytesIO(output.getvalue().encode('utf-8-sig')), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=receivables.csv"})


@router.post("/invoices", response_model=ReceivableResponse)
def create_receivable(data: ReceivableCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="金额必须大于0")
    aging = 0
    if data.due_date:
        try:
            due = date.fromisoformat(data.due_date)
            aging = max(0, (date.today() - due).days)
        except ValueError:
            pass
    item = Receivable(**data.model_dump(), balance=data.amount, aging_days=aging)
    db.add(item)
    db.commit()
    db.refresh(item)
    _audit(db, user, "create", "receivable", item.id, {"customer": item.customer_name, "invoice_no": item.invoice_no, "amount": item.amount})
    db.commit()
    return item


@router.put("/invoices/{inv_id}", response_model=ReceivableResponse)
def update_receivable(inv_id: int, data: ReceivableCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(Receivable).filter(Receivable.id == inv_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="应收记录不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(item, k, v)
    item.balance = item.amount - item.received_amount
    if data.due_date:
        try:
            item.aging_days = max(0, (date.today() - date.fromisoformat(data.due_date)).days)
        except ValueError:
            pass
    _audit(db, user, "update", "receivable", item.id, {"customer": item.customer_name, "invoice_no": item.invoice_no})
    db.commit()
    db.refresh(item)
    return item


@router.delete("/invoices/{inv_id}")
def delete_receivable(inv_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(Receivable).filter(Receivable.id == inv_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="应收记录不存在")
    _audit(db, user, "delete", "receivable", item.id, {"customer": item.customer_name, "invoice_no": item.invoice_no})
    db.delete(item)
    db.commit()
    return {"ok": True}


# ═══════════ 批量操作 ═══════════

class BatchDeleteRequest(BaseModel):
    ids: list[int]

@router.post("/invoices/batch-delete")
def batch_delete_receivables(data: BatchDeleteRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    count = db.query(Receivable).filter(Receivable.id.in_(data.ids)).delete(synchronize_session=False)
    _audit(db, user, "batch_delete", "receivable", None, {"deleted_count": count, "ids": data.ids})
    db.commit()
    return {"deleted": count}


# ═══════════ 收款管理 ═══════════

@router.get("/payments", response_model=list[ReceivablePaymentResponse])
def list_payments(
    company_id: int,
    receivable_id: int | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(ReceivablePayment).filter(ReceivablePayment.company_id == company_id)
    if receivable_id:
        q = q.filter(ReceivablePayment.receivable_id == receivable_id)
    return q.order_by(ReceivablePayment.payment_date.desc()).offset(offset).limit(limit).all()


@router.post("/payments", response_model=ReceivablePaymentResponse)
def create_payment(data: ReceivablePaymentCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="收款金额必须大于0")
    inv = db.query(Receivable).filter(Receivable.id == data.receivable_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="应收记录不存在")
    if data.amount > inv.balance:
        raise HTTPException(status_code=400, detail=f"收款金额({data.amount})超过余额({inv.balance})")
    item = ReceivablePayment(**data.model_dump())
    db.add(item)
    inv.received_amount += data.amount
    inv.balance = inv.amount - inv.received_amount
    inv.status = "已收款" if inv.balance <= 0 else ("部分收款" if inv.received_amount > 0 else "未收款")
    # 自动生成会计凭证：借记银行存款 / 贷记应收账款
    _generate_voucher(db, inv.company_id, user.id, "receipt", f"收款 {inv.customer_name} {inv.invoice_no} 金额{data.amount}", [
        {"account_code": "1002", "debit": data.amount, "credit": 0, "description": f"银行存款 收{inv.customer_name}"},
        {"account_code": "1122", "debit": 0, "credit": data.amount, "description": f"应收账款 {inv.customer_name} {inv.invoice_no}"},
    ])
    _audit(db, user, "payment", "receivable", inv.id, {"amount": data.amount, "method": data.payment_method, "customer": inv.customer_name})
    db.commit()
    db.refresh(item)
    return item


# ═══════════ 仪表板摘要 ═══════════

@router.get("/summary")
def receivables_summary(company_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    items = db.query(Receivable).filter(Receivable.company_id == company_id, Receivable.balance > 0).all()
    total_ar = sum(i.balance for i in items)
    today = date.today()
    buckets = {"current": 0, "1_30": 0, "31_60": 0, "61_90": 0, "over_90": 0}
    for i in items:
        ad = i.aging_days
        if ad <= 0: buckets["current"] += i.balance
        elif ad <= 30: buckets["1_30"] += i.balance
        elif ad <= 60: buckets["31_60"] += i.balance
        elif ad <= 90: buckets["61_90"] += i.balance
        else: buckets["over_90"] += i.balance
    return {
        "total_ar": total_ar,
        "invoice_count": len(items),
        "aging_buckets": buckets,
        "bad_debt_count": len([i for i in items if i.status == "坏账"]),
        "bad_debt_amount": sum(i.balance for i in items if i.status == "坏账"),
    }


# ═══════════ 往来单位数据列表 ═══════════

@router.get("/counterparties")
def list_counterparties(company_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Counterparty).filter(
        Counterparty.company_id == company_id,
        Counterparty.is_active == True,
    ).order_by(Counterparty.code).all()
