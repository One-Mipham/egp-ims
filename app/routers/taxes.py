"""税务管理 — 申报 + 发票."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.auth import get_current_user
from app.models import User, TaxDeclaration, TaxInvoice
from app.schemas.taxes import (
    TaxDeclarationCreate, TaxDeclarationUpdate, TaxDeclarationResponse, TaxDeclarationSummary,
    TaxInvoiceCreate, TaxInvoiceUpdate, TaxInvoiceResponse, TaxInvoiceSummary,
    TAX_TYPE_LABELS,
)

router = APIRouter()


# ── TaxDeclaration CRUD ──

@router.get("/declarations", response_model=list[TaxDeclarationResponse])
def list_declarations(
    tax_type: str | None = Query(None),
    status: str | None = Query(None),
    company_id: int = Query(...),
    period_start: str | None = Query(None),
    period_end: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(TaxDeclaration).filter(TaxDeclaration.company_id == company_id)
    if tax_type:
        q = q.filter(TaxDeclaration.tax_type == tax_type)
    if status:
        q = q.filter(TaxDeclaration.status == status)
    if period_start:
        q = q.filter(TaxDeclaration.period_start >= datetime.fromisoformat(period_start))
    if period_end:
        q = q.filter(TaxDeclaration.period_end <= datetime.fromisoformat(period_end))
    return q.order_by(TaxDeclaration.period_start.desc()).all()


@router.get("/declarations/summary", response_model=list[TaxDeclarationSummary])
def declarations_summary(
    company_id: int = Query(...),
    period_start: str | None = Query(None),
    period_end: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    results = db.query(
        TaxDeclaration.tax_type,
        func.count(TaxDeclaration.id).label("count"),
        func.coalesce(func.sum(TaxDeclaration.tax_amount), 0.0).label("total_tax"),
        func.coalesce(func.sum(TaxDeclaration.paid_amount), 0.0).label("total_paid"),
    ).filter(TaxDeclaration.company_id == company_id)

    if period_start:
        results = results.filter(TaxDeclaration.period_start >= datetime.fromisoformat(period_start))
    if period_end:
        results = results.filter(TaxDeclaration.period_end <= datetime.fromisoformat(period_end))

    results = results.group_by(TaxDeclaration.tax_type).all()

    return [
        TaxDeclarationSummary(
            tax_type=row.tax_type,
            label=TAX_TYPE_LABELS.get(row.tax_type, row.tax_type),
            count=row.count,
            total_tax_amount=float(row.total_tax),
            total_paid_amount=float(row.total_paid),
            total_unpaid_amount=float(row.total_tax - row.total_paid),
        )
        for row in results
    ]


@router.get("/declarations/{declaration_id}", response_model=TaxDeclarationResponse)
def get_declaration(
    declaration_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    obj = db.query(TaxDeclaration).filter(TaxDeclaration.id == declaration_id).first()
    if not obj:
        raise HTTPException(404, "申报记录未找到")
    return obj


@router.post("/declarations", response_model=TaxDeclarationResponse)
def create_declaration(
    data: TaxDeclarationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    obj = TaxDeclaration(
        company_id=data.company_id,
        tax_type=data.tax_type,
        period_start=datetime.fromisoformat(data.period_start) if data.period_start else None,
        period_end=datetime.fromisoformat(data.period_end) if data.period_end else None,
        tax_base=data.tax_base,
        tax_rate=data.tax_rate,
        tax_amount=data.tax_amount,
        paid_amount=data.paid_amount or 0.0,
        status=data.status,
        declaration_date=datetime.fromisoformat(data.declaration_date) if data.declaration_date else None,
        payment_deadline=datetime.fromisoformat(data.payment_deadline) if data.payment_deadline else None,
        payment_date=datetime.fromisoformat(data.payment_date) if data.payment_date else None,
        created_by=current_user.id,
        notes=data.notes,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.put("/declarations/{declaration_id}", response_model=TaxDeclarationResponse)
def update_declaration(
    declaration_id: int,
    data: TaxDeclarationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    obj = db.query(TaxDeclaration).filter(TaxDeclaration.id == declaration_id).first()
    if not obj:
        raise HTTPException(404, "申报记录未找到")
    for field, value in data.model_dump(exclude_unset=True).items():
        if field.startswith("period_") or field in ("declaration_date", "payment_deadline", "payment_date"):
            if value is not None:
                setattr(obj, field, datetime.fromisoformat(value))
        else:
            setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/declarations/{declaration_id}")
def delete_declaration(
    declaration_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    obj = db.query(TaxDeclaration).filter(TaxDeclaration.id == declaration_id).first()
    if not obj:
        raise HTTPException(404, "申报记录未找到")
    db.delete(obj)
    db.commit()
    return {"detail": "已删除"}


# ── TaxInvoice CRUD ──

@router.get("/invoices", response_model=list[TaxInvoiceResponse])
def list_invoices(
    invoice_type: str | None = Query(None),
    status: str | None = Query(None),
    company_id: int = Query(...),
    counterparty_id: int | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(TaxInvoice).filter(TaxInvoice.company_id == company_id)
    if invoice_type:
        q = q.filter(TaxInvoice.invoice_type == invoice_type)
    if status:
        q = q.filter(TaxInvoice.status == status)
    if counterparty_id:
        q = q.filter(TaxInvoice.counterparty_id == counterparty_id)
    if date_from:
        q = q.filter(TaxInvoice.invoice_date >= datetime.fromisoformat(date_from))
    if date_to:
        q = q.filter(TaxInvoice.invoice_date <= datetime.fromisoformat(date_to))
    return q.order_by(TaxInvoice.invoice_date.desc()).all()


@router.get("/invoices/summary", response_model=list[TaxInvoiceSummary])
def invoices_summary(
    company_id: int = Query(...),
    invoice_type: str | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(
        TaxInvoice.invoice_type,
        func.strftime("%Y-%m", TaxInvoice.invoice_date).label("month"),
        func.count(TaxInvoice.id).label("count"),
        func.coalesce(func.sum(TaxInvoice.amount), 0.0).label("total_amount"),
        func.coalesce(func.sum(TaxInvoice.tax_amount), 0.0).label("total_tax"),
        func.coalesce(func.sum(TaxInvoice.total_amount), 0.0).label("total_with_tax"),
    ).filter(TaxInvoice.company_id == company_id)

    if invoice_type:
        q = q.filter(TaxInvoice.invoice_type == invoice_type)
    if date_from:
        q = q.filter(TaxInvoice.invoice_date >= datetime.fromisoformat(date_from))
    if date_to:
        q = q.filter(TaxInvoice.invoice_date <= datetime.fromisoformat(date_to))

    q = q.group_by(TaxInvoice.invoice_type, func.strftime("%Y-%m", TaxInvoice.invoice_date))

    return [
        TaxInvoiceSummary(
            invoice_type=row.invoice_type,
            month=row.month,
            count=row.count,
            total_amount=float(row.total_amount),
            total_tax_amount=float(row.total_tax),
            total_with_tax=float(row.total_with_tax),
        )
        for row in q.all()
    ]


@router.get("/invoices/{invoice_id}", response_model=TaxInvoiceResponse)
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    obj = db.query(TaxInvoice).filter(TaxInvoice.id == invoice_id).first()
    if not obj:
        raise HTTPException(404, "发票记录未找到")
    return obj


@router.post("/invoices", response_model=TaxInvoiceResponse)
def create_invoice(
    data: TaxInvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    obj = TaxInvoice(
        company_id=data.company_id,
        invoice_type=data.invoice_type,
        invoice_number=data.invoice_number,
        invoice_date=datetime.fromisoformat(data.invoice_date),
        counterparty_id=data.counterparty_id,
        amount=data.amount,
        tax_rate=data.tax_rate,
        tax_amount=data.tax_amount,
        total_amount=data.total_amount,
        category=data.category,
        status=data.status,
        notes=data.notes,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.put("/invoices/{invoice_id}", response_model=TaxInvoiceResponse)
def update_invoice(
    invoice_id: int,
    data: TaxInvoiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    obj = db.query(TaxInvoice).filter(TaxInvoice.id == invoice_id).first()
    if not obj:
        raise HTTPException(404, "发票记录未找到")
    for field, value in data.model_dump(exclude_unset=True).items():
        if field == "invoice_date" and value is not None:
            setattr(obj, field, datetime.fromisoformat(value))
        else:
            setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/invoices/{invoice_id}")
def delete_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    obj = db.query(TaxInvoice).filter(TaxInvoice.id == invoice_id).first()
    if not obj:
        raise HTTPException(404, "发票记录未找到")
    db.delete(obj)
    db.commit()
    return {"detail": "已删除"}
