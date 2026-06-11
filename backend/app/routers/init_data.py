"""初始化基础档案路由：业务合同、业务发票。"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import InitContract, InitInvoice
from app.auth import get_current_user

router = APIRouter()


# --- Contracts ---

@router.get("/contracts")
def list_contracts(company_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(InitContract).filter(
        InitContract.company_id == company_id
    ).order_by(InitContract.sign_date.desc()).all()


@router.post("/contracts")
def create_contract(data: dict, company_id: int = Query(...),
                    db: Session = Depends(get_db), user=Depends(get_current_user)):
    c = InitContract(company_id=company_id, **data)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@router.put("/contracts/{contract_id}")
def update_contract(contract_id: int, data: dict,
                    db: Session = Depends(get_db), user=Depends(get_current_user)):
    c = db.query(InitContract).filter(InitContract.id == contract_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="合同不存在")
    for k, v in data.items():
        setattr(c, k, v)
    db.commit()
    db.refresh(c)
    return c


@router.delete("/contracts/{contract_id}")
def delete_contract(contract_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    c = db.query(InitContract).filter(InitContract.id == contract_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="合同不存在")
    db.delete(c)
    db.commit()
    return {"ok": True}


# --- Invoices ---

@router.get("/invoices")
def list_invoices(company_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(InitInvoice).filter(
        InitInvoice.company_id == company_id
    ).order_by(InitInvoice.invoice_date.desc()).all()


@router.post("/invoices")
def create_invoice(data: dict, company_id: int = Query(...),
                   db: Session = Depends(get_db), user=Depends(get_current_user)):
    inv = InitInvoice(company_id=company_id, **data)
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return inv


@router.put("/invoices/{invoice_id}")
def update_invoice(invoice_id: int, data: dict,
                   db: Session = Depends(get_db), user=Depends(get_current_user)):
    inv = db.query(InitInvoice).filter(InitInvoice.id == invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="发票不存在")
    for k, v in data.items():
        setattr(inv, k, v)
    db.commit()
    db.refresh(inv)
    return inv


@router.delete("/invoices/{invoice_id}")
def delete_invoice(invoice_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    inv = db.query(InitInvoice).filter(InitInvoice.id == invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="发票不存在")
    db.delete(inv)
    db.commit()
    return {"ok": True}
