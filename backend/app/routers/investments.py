"""投资管理路由：组合/持仓/交易/估值/收益 + 自动凭证生成。"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    Voucher,
    VoucherEntry,
    InvestmentPortfolio,
    InvestmentPosition,
    InvestmentTransaction,
    FairValueAdjustment,
    InvestmentIncome,
    AccountMapping,
    SecurityMaster,
    InvestmentFund,
    CapitalAccount,
    CapitalCall,
    FundDistribution,
    WaterfallConfig,
    RealEstateAsset,
    RealEstateValuation,
    InfraAsset,
    PrivateCredit,
    CreditPayment,
)
from app.schemas import (
    InvestmentPortfolioCreate,
    InvestmentPortfolioUpdate,
    InvestmentPortfolioResponse,
    InvestmentPositionCreate,
    InvestmentPositionUpdate,
    InvestmentPositionResponse,
    InvestmentTransactionCreate,
    InvestmentTransactionUpdate,
    InvestmentTransactionResponse,
    FairValueAdjustmentCreate,
    FairValueAdjustmentUpdate,
    FairValueAdjustmentResponse,
    InvestmentIncomeCreate,
    InvestmentIncomeUpdate,
    InvestmentIncomeResponse,
    AccountMappingResponse,
    SecurityMasterCreate,
    SecurityMasterUpdate,
    SecurityMasterResponse,
    InvestmentFundCreate,
    InvestmentFundUpdate,
    InvestmentFundResponse,
    CapitalAccountCreate,
    CapitalAccountUpdate,
    CapitalAccountResponse,
    CapitalCallCreate,
    CapitalCallUpdate,
    CapitalCallResponse,
    FundDistributionCreate,
    FundDistributionUpdate,
    FundDistributionResponse,
    WaterfallConfigCreate,
    WaterfallConfigUpdate,
    WaterfallConfigResponse,
    WaterfallCalculateRequest,
    RealEstateAssetCreate,
    RealEstateAssetUpdate,
    RealEstateAssetResponse,
    RealEstateValuationCreate,
    RealEstateValuationUpdate,
    RealEstateValuationResponse,
    InfraAssetCreate,
    InfraAssetUpdate,
    InfraAssetResponse,
    PrivateCreditCreate,
    PrivateCreditUpdate,
    PrivateCreditResponse,
    CreditPaymentCreate,
    CreditPaymentUpdate,
    CreditPaymentResponse,
)
from app.auth import get_current_user

router = APIRouter()


def _generate_invest_voucher(
    db: Session,
    company_id: int,
    txn_type: str,
    amount: float,
    account_code: str,
    txn_date: str,
    security_name: str,
    creator_id: int,
    investment_type: str = "",
) -> int:
    """根据 AccountMapping 自动生成会计凭证，返回 voucher_id。"""
    mapping = (
        db.query(AccountMapping)
        .filter(
            AccountMapping.transaction_type == txn_type,
            AccountMapping.investment_type == investment_type,
        )
        .first()
    )
    if not mapping:
        mapping = (
            db.query(AccountMapping)
            .filter(
                AccountMapping.transaction_type == txn_type,
                AccountMapping.investment_type.is_(None),
            )
            .first()
        )
    if not mapping:
        return None

    debit_code = mapping.debit_account_code
    credit_code = mapping.credit_account_code
    if "/" in debit_code:
        debit_code = account_code
    if "/" in credit_code:
        credit_code = account_code

    now = datetime.now(timezone.utc)
    month_str = now.strftime("%Y%m")
    count = (
        db.query(Voucher)
        .filter(
            Voucher.company_id == company_id,
            Voucher.date.startswith(now.strftime("%Y-%m")),
        )
        .count()
    )
    voucher_no = f"转字{month_str}-{count + 1:04d}"

    desc_tpl = mapping.description_template or "{type} {name}"
    summary = desc_tpl.replace("{type}", txn_type).replace("{name}", security_name)

    voucher = Voucher(
        company_id=company_id,
        date=txn_date,
        voucher_no=voucher_no,
        voucher_type="transfer",
        summary=summary,
        creator_id=creator_id,
        status="draft",
    )
    db.add(voucher)
    db.flush()

    db.add(
        VoucherEntry(
            voucher_id=voucher.id,
            account_code=debit_code,
            debit=amount,
            credit=0.0,
            description=summary,
        )
    )
    db.add(
        VoucherEntry(
            voucher_id=voucher.id,
            account_code=credit_code,
            debit=0.0,
            credit=amount,
            description=summary,
        )
    )
    db.flush()
    return voucher.id


# --- Portfolios ---


@router.get("/portfolios", response_model=list[InvestmentPortfolioResponse])
def list_portfolios(company_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return (
        db.query(InvestmentPortfolio)
        .filter(InvestmentPortfolio.company_id == company_id)
        .order_by(InvestmentPortfolio.name)
        .all()
    )


@router.post("/portfolios", response_model=InvestmentPortfolioResponse)
def create_portfolio(
    data: InvestmentPortfolioCreate,
    company_id: int = Query(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    p = InvestmentPortfolio(company_id=company_id, **data.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.put("/portfolios/{portfolio_id}", response_model=InvestmentPortfolioResponse)
def update_portfolio(
    portfolio_id: int, data: InvestmentPortfolioUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)
):
    p = db.query(InvestmentPortfolio).filter(InvestmentPortfolio.id == portfolio_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="组合不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(p, k, v)
    db.commit()
    db.refresh(p)
    return p


@router.delete("/portfolios/{portfolio_id}")
def delete_portfolio(portfolio_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    p = db.query(InvestmentPortfolio).filter(InvestmentPortfolio.id == portfolio_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="组合不存在")
    db.delete(p)
    db.commit()
    return {"ok": True}


# --- Positions ---


@router.get("/positions", response_model=list[InvestmentPositionResponse])
def list_positions(
    company_id: int,
    portfolio_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    q = db.query(InvestmentPosition).join(InvestmentPortfolio).filter(InvestmentPortfolio.company_id == company_id)
    if portfolio_id:
        q = q.filter(InvestmentPosition.portfolio_id == portfolio_id)
    return q.order_by(InvestmentPosition.security_name).all()


@router.post("/positions", response_model=InvestmentPositionResponse)
def create_position(
    data: InvestmentPositionCreate,
    company_id: int = Query(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    portfolio = (
        db.query(InvestmentPortfolio)
        .filter(
            InvestmentPortfolio.id == data.portfolio_id,
            InvestmentPortfolio.company_id == company_id,
        )
        .first()
    )
    if not portfolio:
        raise HTTPException(status_code=404, detail="投资组合不存在")
    pos = InvestmentPosition(**data.model_dump())
    db.add(pos)
    db.commit()
    db.refresh(pos)
    return pos


@router.put("/positions/{position_id}", response_model=InvestmentPositionResponse)
def update_position(
    position_id: int, data: InvestmentPositionUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)
):
    pos = db.query(InvestmentPosition).filter(InvestmentPosition.id == position_id).first()
    if not pos:
        raise HTTPException(status_code=404, detail="持仓不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(pos, k, v)
    db.commit()
    db.refresh(pos)
    return pos


@router.delete("/positions/{position_id}")
def delete_position(position_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    pos = db.query(InvestmentPosition).filter(InvestmentPosition.id == position_id).first()
    if not pos:
        raise HTTPException(status_code=404, detail="持仓不存在")
    db.delete(pos)
    db.commit()
    return {"ok": True}


# --- Transactions (with auto-voucher) ---


@router.get("/transactions", response_model=list[InvestmentTransactionResponse])
def list_transactions(
    company_id: int,
    position_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    q = (
        db.query(InvestmentTransaction)
        .join(InvestmentPosition)
        .join(InvestmentPortfolio)
        .filter(InvestmentPortfolio.company_id == company_id)
    )
    if position_id:
        q = q.filter(InvestmentTransaction.position_id == position_id)
    return q.order_by(InvestmentTransaction.transaction_date.desc()).all()


@router.post("/transactions", response_model=InvestmentTransactionResponse)
def create_transaction(
    data: InvestmentTransactionCreate,
    company_id: int = Query(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    pos = (
        db.query(InvestmentPosition)
        .join(InvestmentPortfolio)
        .filter(
            InvestmentPosition.id == data.position_id,
            InvestmentPortfolio.company_id == company_id,
        )
        .first()
    )
    if not pos:
        raise HTTPException(status_code=404, detail="持仓不存在")

    txn = InvestmentTransaction(**data.model_dump())
    db.add(txn)
    db.flush()

    portfolio = db.query(InvestmentPortfolio).filter(InvestmentPortfolio.id == pos.portfolio_id).first()
    voucher_id = _generate_invest_voucher(
        db=db,
        company_id=company_id,
        txn_type=data.transaction_type,
        amount=data.amount,
        account_code=pos.account_code,
        txn_date=data.transaction_date,
        security_name=pos.security_name,
        creator_id=user.id,
        investment_type=portfolio.investment_type if portfolio else "",
    )
    if voucher_id:
        txn.voucher_id = voucher_id
        db.flush()

    db.commit()
    db.refresh(txn)
    return txn


@router.put("/transactions/{transaction_id}", response_model=InvestmentTransactionResponse)
def update_transaction(
    transaction_id: int,
    data: InvestmentTransactionUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    txn = db.query(InvestmentTransaction).filter(InvestmentTransaction.id == transaction_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="交易不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(txn, k, v)
    db.flush()

    if txn.voucher_id:
        vch = db.query(Voucher).filter(Voucher.id == txn.voucher_id).first()
        if vch:
            vch.date = txn.transaction_date
            pos = db.query(InvestmentPosition).filter(InvestmentPosition.id == txn.position_id).first()
            if pos:
                vch.summary = f"{txn.transaction_type} {pos.security_name}"
                entries = db.query(VoucherEntry).filter(VoucherEntry.voucher_id == vch.id).all()
                for e in entries:
                    e.description = vch.summary
    db.commit()
    db.refresh(txn)
    return txn


@router.delete("/transactions/{transaction_id}")
def delete_transaction(transaction_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    txn = db.query(InvestmentTransaction).filter(InvestmentTransaction.id == transaction_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="交易不存在")
    if txn.voucher_id:
        db.query(VoucherEntry).filter(VoucherEntry.voucher_id == txn.voucher_id).delete()
        db.query(Voucher).filter(Voucher.id == txn.voucher_id).delete()
    db.delete(txn)
    db.commit()
    return {"ok": True}


# --- Fair Value Adjustments ---


@router.get("/adjustments", response_model=list[FairValueAdjustmentResponse])
def list_adjustments(
    company_id: int,
    position_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    q = (
        db.query(FairValueAdjustment)
        .join(InvestmentPosition)
        .join(InvestmentPortfolio)
        .filter(InvestmentPortfolio.company_id == company_id)
    )
    if position_id:
        q = q.filter(FairValueAdjustment.position_id == position_id)
    return q.order_by(FairValueAdjustment.adjustment_date.desc()).all()


@router.post("/adjustments", response_model=FairValueAdjustmentResponse)
def create_adjustment(
    data: FairValueAdjustmentCreate,
    company_id: int = Query(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    pos = (
        db.query(InvestmentPosition)
        .join(InvestmentPortfolio)
        .filter(
            InvestmentPosition.id == data.position_id,
            InvestmentPortfolio.company_id == company_id,
        )
        .first()
    )
    if not pos:
        raise HTTPException(status_code=404, detail="持仓不存在")

    adj = FairValueAdjustment(**data.model_dump())
    db.add(adj)
    db.flush()

    pos.fair_value = data.adjusted_value
    pos.fair_value_date = data.adjustment_date
    if data.change_amount != 0:
        pos.valuation_method = "market_price"

    txn_type = "fair_value_up" if data.change_amount > 0 else "fair_value_down"
    portfolio = db.query(InvestmentPortfolio).filter(InvestmentPortfolio.id == pos.portfolio_id).first()
    abs_change = abs(data.change_amount) if data.change_amount != 0 else 0.01
    voucher_id = _generate_invest_voucher(
        db=db,
        company_id=company_id,
        txn_type=txn_type,
        amount=abs_change,
        account_code=pos.account_code,
        txn_date=data.adjustment_date,
        security_name=pos.security_name,
        creator_id=user.id,
        investment_type=portfolio.investment_type if portfolio else "",
    )
    if voucher_id:
        adj.voucher_id = voucher_id
        db.flush()

    db.commit()
    db.refresh(adj)
    return adj


@router.put("/adjustments/{adjustment_id}", response_model=FairValueAdjustmentResponse)
def update_adjustment(
    adjustment_id: int, data: FairValueAdjustmentUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)
):
    adj = db.query(FairValueAdjustment).filter(FairValueAdjustment.id == adjustment_id).first()
    if not adj:
        raise HTTPException(status_code=404, detail="调整不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(adj, k, v)
    db.flush()

    pos = db.query(InvestmentPosition).filter(InvestmentPosition.id == adj.position_id).first()
    if pos and data.adjusted_value is not None:
        pos.fair_value = data.adjusted_value
    if pos and data.adjustment_date is not None:
        pos.fair_value_date = data.adjustment_date

    if adj.voucher_id and data.change_amount is not None and data.change_amount != 0:
        vch = db.query(Voucher).filter(Voucher.id == adj.voucher_id).first()
        if vch and pos:
            txn_type = "fair_value_up" if data.change_amount > 0 else "fair_value_down"
            vch.summary = f"{txn_type} {pos.security_name}"
            vch.date = adj.adjustment_date
            entries = db.query(VoucherEntry).filter(VoucherEntry.voucher_id == vch.id).all()
            abs_amt = abs(data.change_amount)
            for e in entries:
                e.description = vch.summary
                if e.debit > 0:
                    e.debit = abs_amt
                elif e.credit > 0:
                    e.credit = abs_amt
    db.commit()
    db.refresh(adj)
    return adj


@router.delete("/adjustments/{adjustment_id}")
def delete_adjustment(adjustment_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    adj = db.query(FairValueAdjustment).filter(FairValueAdjustment.id == adjustment_id).first()
    if not adj:
        raise HTTPException(status_code=404, detail="调整不存在")
    if adj.voucher_id:
        db.query(VoucherEntry).filter(VoucherEntry.voucher_id == adj.voucher_id).delete()
        db.query(Voucher).filter(Voucher.id == adj.voucher_id).delete()
    db.delete(adj)
    db.commit()
    return {"ok": True}


# --- Income ---


@router.get("/income", response_model=list[InvestmentIncomeResponse])
def list_income(
    company_id: int,
    position_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    q = db.query(InvestmentIncome).filter(InvestmentIncome.company_id == company_id)
    if position_id:
        q = q.filter(InvestmentIncome.position_id == position_id)
    return q.order_by(InvestmentIncome.income_date.desc()).all()


@router.post("/income", response_model=InvestmentIncomeResponse)
def create_income(
    data: InvestmentIncomeCreate,
    company_id: int = Query(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    inc = InvestmentIncome(company_id=company_id, **data.model_dump())
    db.add(inc)
    db.flush()

    if data.position_id:
        pos = db.query(InvestmentPosition).filter(InvestmentPosition.id == data.position_id).first()
        if pos:
            txn_map = {
                "dividend": "dividend",
                "interest": "interest",
                "realized_gain": "sell",
                "unrealized_gain": "fair_value_up",
            }
            txn_type = txn_map.get(data.income_type, "dividend")
            portfolio = db.query(InvestmentPortfolio).filter(InvestmentPortfolio.id == pos.portfolio_id).first()
            voucher_id = _generate_invest_voucher(
                db=db,
                company_id=company_id,
                txn_type=txn_type,
                amount=data.amount,
                account_code=pos.account_code,
                txn_date=data.income_date,
                security_name=pos.security_name,
                creator_id=user.id,
                investment_type=portfolio.investment_type if portfolio else "",
            )
            if voucher_id:
                inc.voucher_id = voucher_id
                db.flush()

    db.commit()
    db.refresh(inc)
    return inc


@router.put("/income/{income_id}", response_model=InvestmentIncomeResponse)
def update_income(
    income_id: int, data: InvestmentIncomeUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)
):
    inc = db.query(InvestmentIncome).filter(InvestmentIncome.id == income_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="收益记录不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(inc, k, v)
    db.flush()

    if inc.voucher_id:
        vch = db.query(Voucher).filter(Voucher.id == inc.voucher_id).first()
        if vch:
            vch.date = inc.income_date
            pos = (
                db.query(InvestmentPosition).filter(InvestmentPosition.id == inc.position_id).first()
                if inc.position_id
                else None
            )
            vch.summary = f"{inc.income_type} {pos.security_name if pos else ''}"
            entries = db.query(VoucherEntry).filter(VoucherEntry.voucher_id == vch.id).all()
            for e in entries:
                e.description = vch.summary
                if data.amount is not None:
                    if e.debit > 0:
                        e.debit = data.amount
                    elif e.credit > 0:
                        e.credit = data.amount
    db.commit()
    db.refresh(inc)
    return inc


@router.delete("/income/{income_id}")
def delete_income(income_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    inc = db.query(InvestmentIncome).filter(InvestmentIncome.id == income_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="收益记录不存在")
    if inc.voucher_id:
        db.query(VoucherEntry).filter(VoucherEntry.voucher_id == inc.voucher_id).delete()
        db.query(Voucher).filter(Voucher.id == inc.voucher_id).delete()
    db.delete(inc)
    db.commit()
    return {"ok": True}


# --- Account Mappings ---


@router.get("/mappings", response_model=list[AccountMappingResponse])
def list_mappings(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(AccountMapping).order_by(AccountMapping.transaction_type).all()


# --- Reports ---


@router.get("/reports/positions")
def report_positions(
    company_id: int,
    investment_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    q = db.query(InvestmentPosition).join(InvestmentPortfolio).filter(InvestmentPortfolio.company_id == company_id)
    if investment_type:
        q = q.filter(InvestmentPortfolio.investment_type == investment_type)

    positions = q.order_by(InvestmentPortfolio.name, InvestmentPosition.security_name).all()
    result = []
    for p in positions:
        portfolio = db.query(InvestmentPortfolio).filter(InvestmentPortfolio.id == p.portfolio_id).first()
        result.append(
            {
                "id": p.id,
                "portfolio_name": portfolio.name if portfolio else "",
                "investment_type": portfolio.investment_type if portfolio else "",
                "security_name": p.security_name,
                "security_code": p.security_code,
                "account_code": p.account_code,
                "quantity": p.quantity,
                "cost_amount": p.cost_amount,
                "fair_value": p.fair_value,
                "unrealized_gl": round(p.fair_value - p.cost_amount, 2),
                "unrealized_gl_pct": round((p.fair_value - p.cost_amount) / p.cost_amount * 100, 2)
                if p.cost_amount
                else 0,
                "status": p.status,
                "fair_value_date": p.fair_value_date,
            }
        )
    return result


@router.get("/reports/income")
def report_income(
    company_id: int,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    q = db.query(InvestmentIncome).filter(InvestmentIncome.company_id == company_id)
    if start_date:
        q = q.filter(InvestmentIncome.income_date >= start_date)
    if end_date:
        q = q.filter(InvestmentIncome.income_date <= end_date)
    incomes = q.order_by(InvestmentIncome.income_date.desc()).all()

    by_type = {}
    total = 0.0
    for inc in incomes:
        by_type[inc.income_type] = by_type.get(inc.income_type, 0.0) + inc.amount
        total += inc.amount

    return {
        "items": [
            {
                "id": inc.id,
                "income_type": inc.income_type,
                "income_date": inc.income_date,
                "amount": inc.amount,
                "position_id": inc.position_id,
                "notes": inc.notes,
                "voucher_id": inc.voucher_id,
            }
            for inc in incomes
        ],
        "summary_by_type": [{"income_type": k, "amount": round(v, 2)} for k, v in by_type.items()],
        "total": round(total, 2),
    }


@router.get("/reports/fair-value")
def report_fair_value(
    company_id: int,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    q = (
        db.query(FairValueAdjustment)
        .join(InvestmentPosition)
        .join(InvestmentPortfolio)
        .filter(InvestmentPortfolio.company_id == company_id)
    )
    if start_date:
        q = q.filter(FairValueAdjustment.adjustment_date >= start_date)
    if end_date:
        q = q.filter(FairValueAdjustment.adjustment_date <= end_date)
    adjustments = q.order_by(FairValueAdjustment.adjustment_date.desc()).all()

    total_change = sum(a.change_amount for a in adjustments)
    return {
        "items": [
            {
                "id": a.id,
                "position_id": a.position_id,
                "adjustment_date": a.adjustment_date,
                "previous_value": a.previous_value,
                "adjusted_value": a.adjusted_value,
                "change_amount": a.change_amount,
                "reason": a.reason,
            }
            for a in adjustments
        ],
        "total_change": round(total_change, 2),
    }


# --- Securities Master Data ---


@router.get("/securities", response_model=list[SecurityMasterResponse])
def list_securities(
    company_id: int,
    security_type: Optional[str] = Query(None),
    exchange: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    q = db.query(SecurityMaster).filter(SecurityMaster.company_id == company_id)
    if security_type:
        q = q.filter(SecurityMaster.security_type == security_type)
    if exchange:
        q = q.filter(SecurityMaster.exchange == exchange)
    return q.order_by(SecurityMaster.security_code).all()


@router.post("/securities", response_model=SecurityMasterResponse)
def create_security(
    data: SecurityMasterCreate,
    company_id: int = Query(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    s = SecurityMaster(company_id=company_id, **data.model_dump())
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


@router.put("/securities/{security_id}", response_model=SecurityMasterResponse)
def update_security(
    security_id: int, data: SecurityMasterUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)
):
    s = db.query(SecurityMaster).filter(SecurityMaster.id == security_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="证券不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(s, k, v)
    db.commit()
    db.refresh(s)
    return s


@router.delete("/securities/{security_id}")
def delete_security(security_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    s = db.query(SecurityMaster).filter(SecurityMaster.id == security_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="证券不存在")
    db.delete(s)
    db.commit()
    return {"ok": True}


# --- Fund Management ---


@router.get("/funds", response_model=list[InvestmentFundResponse])
def list_funds(company_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return (
        db.query(InvestmentFund)
        .filter(InvestmentFund.company_id == company_id)
        .order_by(InvestmentFund.fund_name)
        .all()
    )


@router.post("/funds", response_model=InvestmentFundResponse)
def create_fund(
    data: InvestmentFundCreate,
    company_id: int = Query(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    f = InvestmentFund(company_id=company_id, **data.model_dump())
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


@router.put("/funds/{fund_id}", response_model=InvestmentFundResponse)
def update_fund(
    fund_id: int, data: InvestmentFundUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)
):
    f = db.query(InvestmentFund).filter(InvestmentFund.id == fund_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="基金不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(f, k, v)
    db.commit()
    db.refresh(f)
    return f


@router.delete("/funds/{fund_id}")
def delete_fund(fund_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    f = db.query(InvestmentFund).filter(InvestmentFund.id == fund_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="基金不存在")
    db.delete(f)
    db.commit()
    return {"ok": True}


# --- Capital Accounts ---


@router.get("/funds/{fund_id}/capital-accounts", response_model=list[CapitalAccountResponse])
def list_capital_accounts(fund_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(CapitalAccount).filter(CapitalAccount.fund_id == fund_id).all()


@router.post("/funds/{fund_id}/capital-accounts", response_model=CapitalAccountResponse)
def create_capital_account(
    fund_id: int,
    data: CapitalAccountCreate,
    company_id: int = Query(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    fund = (
        db.query(InvestmentFund).filter(InvestmentFund.id == fund_id, InvestmentFund.company_id == company_id).first()
    )
    if not fund:
        raise HTTPException(status_code=404, detail="基金不存在")
    ca = CapitalAccount(fund_id=fund_id, company_id=company_id, **data.model_dump())
    db.add(ca)
    db.commit()
    db.refresh(ca)
    return ca


@router.put("/funds/{fund_id}/capital-accounts/{account_id}", response_model=CapitalAccountResponse)
def update_capital_account(
    fund_id: int,
    account_id: int,
    data: CapitalAccountUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    ca = db.query(CapitalAccount).filter(CapitalAccount.id == account_id, CapitalAccount.fund_id == fund_id).first()
    if not ca:
        raise HTTPException(status_code=404, detail="资本账户不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(ca, k, v)
    db.commit()
    db.refresh(ca)
    return ca


@router.delete("/funds/{fund_id}/capital-accounts/{account_id}")
def delete_capital_account(
    fund_id: int, account_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)
):
    ca = db.query(CapitalAccount).filter(CapitalAccount.id == account_id, CapitalAccount.fund_id == fund_id).first()
    if not ca:
        raise HTTPException(status_code=404, detail="资本账户不存在")
    db.delete(ca)
    db.commit()
    return {"ok": True}


# --- Capital Calls (with auto-voucher) ---


@router.get("/funds/{fund_id}/capital-calls", response_model=list[CapitalCallResponse])
def list_capital_calls(fund_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(CapitalCall).filter(CapitalCall.fund_id == fund_id).order_by(CapitalCall.call_date.desc()).all()


@router.post("/funds/{fund_id}/capital-calls", response_model=CapitalCallResponse)
def create_capital_call(
    fund_id: int,
    data: CapitalCallCreate,
    company_id: int = Query(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    fund = (
        db.query(InvestmentFund).filter(InvestmentFund.id == fund_id, InvestmentFund.company_id == company_id).first()
    )
    if not fund:
        raise HTTPException(status_code=404, detail="基金不存在")
    cc = CapitalCall(fund_id=fund_id, company_id=company_id, **data.model_dump())
    db.add(cc)
    db.flush()
    voucher_id = _generate_invest_voucher(
        db,
        company_id,
        "capital_call",
        cc.call_amount,
        "1511",
        cc.call_date,
        fund.fund_name if fund else "fund",
        user.id,
        fund.fund_type if fund else "",
    )
    if voucher_id:
        cc.voucher_id = voucher_id
    db.flush()
    db.commit()
    db.refresh(cc)
    return cc


@router.put("/funds/{fund_id}/capital-calls/{call_id}", response_model=CapitalCallResponse)
def update_capital_call(
    fund_id: int, call_id: int, data: CapitalCallUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)
):
    cc = db.query(CapitalCall).filter(CapitalCall.id == call_id, CapitalCall.fund_id == fund_id).first()
    if not cc:
        raise HTTPException(status_code=404, detail="资本召唤不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(cc, k, v)
    db.commit()
    db.refresh(cc)
    return cc


@router.delete("/funds/{fund_id}/capital-calls/{call_id}")
def delete_capital_call(fund_id: int, call_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    cc = db.query(CapitalCall).filter(CapitalCall.id == call_id, CapitalCall.fund_id == fund_id).first()
    if not cc:
        raise HTTPException(status_code=404, detail="资本召唤不存在")
    if cc.voucher_id:
        db.query(VoucherEntry).filter(VoucherEntry.voucher_id == cc.voucher_id).delete()
        db.query(Voucher).filter(Voucher.id == cc.voucher_id).delete()
    db.delete(cc)
    db.commit()
    return {"ok": True}


# --- Fund Distributions (with auto-voucher) ---


@router.get("/funds/{fund_id}/distributions", response_model=list[FundDistributionResponse])
def list_distributions(fund_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return (
        db.query(FundDistribution)
        .filter(FundDistribution.fund_id == fund_id)
        .order_by(FundDistribution.distribution_date.desc())
        .all()
    )


@router.post("/funds/{fund_id}/distributions", response_model=FundDistributionResponse)
def create_distribution(
    fund_id: int,
    data: FundDistributionCreate,
    company_id: int = Query(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    fund = (
        db.query(InvestmentFund).filter(InvestmentFund.id == fund_id, InvestmentFund.company_id == company_id).first()
    )
    if not fund:
        raise HTTPException(status_code=404, detail="基金不存在")
    fd = FundDistribution(fund_id=fund_id, company_id=company_id, **data.model_dump())
    db.add(fd)
    db.flush()
    voucher_id = _generate_invest_voucher(
        db,
        company_id,
        "distribution",
        fd.amount,
        "1511",
        fd.distribution_date,
        fund.fund_name if fund else "fund",
        user.id,
        fund.fund_type if fund else "",
    )
    if voucher_id:
        fd.voucher_id = voucher_id
    db.flush()
    db.commit()
    db.refresh(fd)
    return fd


@router.put("/funds/{fund_id}/distributions/{dist_id}", response_model=FundDistributionResponse)
def update_distribution(
    fund_id: int,
    dist_id: int,
    data: FundDistributionUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    fd = db.query(FundDistribution).filter(FundDistribution.id == dist_id, FundDistribution.fund_id == fund_id).first()
    if not fd:
        raise HTTPException(status_code=404, detail="分配记录不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(fd, k, v)
    db.commit()
    db.refresh(fd)
    return fd


@router.delete("/funds/{fund_id}/distributions/{dist_id}")
def delete_distribution(fund_id: int, dist_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    fd = db.query(FundDistribution).filter(FundDistribution.id == dist_id, FundDistribution.fund_id == fund_id).first()
    if not fd:
        raise HTTPException(status_code=404, detail="分配记录不存在")
    if fd.voucher_id:
        db.query(VoucherEntry).filter(VoucherEntry.voucher_id == fd.voucher_id).delete()
        db.query(Voucher).filter(Voucher.id == fd.voucher_id).delete()
    db.delete(fd)
    db.commit()
    return {"ok": True}


# --- Performance Analysis ---


@router.get("/reports/performance")
def report_performance(
    company_id: int,
    portfolio_id: Optional[int] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """计算 IRR / TWR / MOIC 按组合汇总。"""
    # Cash flows from transactions
    txn_q = (
        db.query(InvestmentTransaction)
        .join(InvestmentPosition)
        .join(InvestmentPortfolio)
        .filter(InvestmentPortfolio.company_id == company_id)
    )
    if portfolio_id:
        txn_q = txn_q.filter(InvestmentPortfolio.id == portfolio_id)
    if start_date:
        txn_q = txn_q.filter(InvestmentTransaction.transaction_date >= start_date)
    if end_date:
        txn_q = txn_q.filter(InvestmentTransaction.transaction_date <= end_date)
    transactions = txn_q.order_by(InvestmentTransaction.transaction_date).all()

    # Income
    inc_q = db.query(InvestmentIncome).filter(InvestmentIncome.company_id == company_id)
    if start_date:
        inc_q = inc_q.filter(InvestmentIncome.income_date >= start_date)
    if end_date:
        inc_q = inc_q.filter(InvestmentIncome.income_date <= end_date)
    incomes = inc_q.all()

    # Positions for current fair value
    pos_q = db.query(InvestmentPosition).join(InvestmentPortfolio).filter(InvestmentPortfolio.company_id == company_id)
    if portfolio_id:
        pos_q = pos_q.filter(InvestmentPortfolio.id == portfolio_id)
    positions = pos_q.all()

    total_cost = sum(t.amount for t in transactions if t.transaction_type == "buy") + sum(
        t.amount for t in transactions if t.transaction_type == "capital_call"
    )
    total_proceeds = sum(t.amount for t in transactions if t.transaction_type == "sell") + sum(
        t.amount for t in transactions if t.transaction_type == "distribution"
    )
    total_income = sum(i.amount for i in incomes)
    current_fv = sum(p.fair_value or 0 for p in positions)
    total_distributions = total_proceeds + total_income

    moic = round((current_fv + total_distributions) / total_cost, 4) if total_cost > 0 else 0

    # Build cash flows for IRR: investments negative, proceeds+income+current_fv positive
    cash_flows = []
    for t in sorted(transactions, key=lambda x: x.transaction_date):
        if t.transaction_type in ("buy", "capital_call"):
            cash_flows.append({"date": t.transaction_date, "amount": -t.amount, "label": t.transaction_type})
        elif t.transaction_type in ("sell", "distribution"):
            cash_flows.append({"date": t.transaction_date, "amount": t.amount, "label": t.transaction_type})
    for i in sorted(incomes, key=lambda x: x.income_date):
        cash_flows.append({"date": i.income_date, "amount": i.amount, "label": i.income_type})
    if current_fv > 0 and cash_flows:
        cash_flows.append({"date": end_date or "", "amount": current_fv, "label": "fair_value"})

    # Simple IRR via binary search
    def npv(rate, flows):
        return sum(f["amount"] / ((1 + rate) ** (i / 365.0)) for i, f in enumerate(flows))

    irr = 0.0
    if len(cash_flows) >= 2:
        lo, hi = -0.99, 5.0
        for _ in range(80):
            mid = (lo + hi) / 2
            if npv(mid, cash_flows) > 0:
                lo = mid
            else:
                hi = mid
        irr = round((lo + hi) / 2 * 100, 2)

    return {
        "total_cost": round(total_cost, 2),
        "total_proceeds": round(total_proceeds, 2),
        "total_income": round(total_income, 2),
        "current_fair_value": round(current_fv, 2),
        "moic": moic,
        "irr_pct": irr,
        "cash_flows": cash_flows,
        "position_count": len(positions),
    }


# --- Waterfall Distribution ---


@router.get("/waterfall-configs", response_model=list[WaterfallConfigResponse])
def list_waterfall_configs(company_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return (
        db.query(WaterfallConfig).filter(WaterfallConfig.company_id == company_id).order_by(WaterfallConfig.name).all()
    )


@router.post("/waterfall-configs", response_model=WaterfallConfigResponse)
def create_waterfall_config(
    data: WaterfallConfigCreate,
    company_id: int = Query(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    wc = WaterfallConfig(company_id=company_id, **data.model_dump())
    db.add(wc)
    db.commit()
    db.refresh(wc)
    return wc


@router.put("/waterfall-configs/{config_id}", response_model=WaterfallConfigResponse)
def update_waterfall_config(
    config_id: int, data: WaterfallConfigUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)
):
    wc = db.query(WaterfallConfig).filter(WaterfallConfig.id == config_id).first()
    if not wc:
        raise HTTPException(status_code=404, detail="瀑布配置不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(wc, k, v)
    db.commit()
    db.refresh(wc)
    return wc


@router.delete("/waterfall-configs/{config_id}")
def delete_waterfall_config(config_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    wc = db.query(WaterfallConfig).filter(WaterfallConfig.id == config_id).first()
    if not wc:
        raise HTTPException(status_code=404, detail="瀑布配置不存在")
    db.delete(wc)
    db.commit()
    return {"ok": True}


@router.post("/waterfall/calculate")
def calculate_waterfall(data: WaterfallCalculateRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """执行分配瀑布计算。"""
    wc = db.query(WaterfallConfig).filter(WaterfallConfig.id == data.config_id).first()
    if not wc:
        raise HTTPException(status_code=404, detail="瀑布配置不存在")

    tiers = sorted(wc.tiers, key=lambda t: t.get("order", 0))
    remaining = data.total_proceeds
    steps = []
    gp_total = 0.0
    lp_total = 0.0

    for tier in tiers:
        if remaining <= 0:
            break
        t = tier.get("type", "")
        gp_pct = tier.get("gp_share_pct", 0) / 100.0
        lp_pct = tier.get("lp_share_pct", 100) / 100.0

        allocated = min(remaining, remaining)  # all remaining goes through this tier
        if t == "return_of_capital":
            allocated = min(remaining, remaining)  # ROC just returns remaining to LP
            lp_share = allocated
            gp_share = 0.0
        elif t == "preferred_return":
            threshold = remaining * (tier.get("threshold_pct", 8) / 100.0)
            allocated = min(remaining, threshold)
            lp_share = allocated
            gp_share = 0.0
        elif t == "catch_up" or t == "carry":
            gp_share = allocated * gp_pct
            lp_share = allocated * lp_pct
        else:
            gp_share = allocated * gp_pct
            lp_share = allocated * lp_pct

        gp_share = round(gp_share, 2)
        lp_share = round(allocated - gp_share, 2)
        gp_total += gp_share
        lp_total += lp_share
        remaining -= allocated

        steps.append(
            {
                "order": tier.get("order"),
                "name": tier.get("name", ""),
                "type": t,
                "allocated": round(allocated, 2),
                "gp_share": gp_share,
                "lp_share": lp_share,
                "remaining": round(remaining, 2),
            }
        )

    return {
        "config_name": wc.name,
        "total_proceeds": data.total_proceeds,
        "steps": steps,
        "gp_total": round(gp_total, 2),
        "lp_total": round(lp_total, 2),
    }


# --- LP Investors (cross-fund aggregation) ---


@router.get("/lp-investors")
def list_lp_investors(company_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """跨基金汇总 LP 投资者列表。"""
    accounts = db.query(CapitalAccount).join(InvestmentFund).filter(InvestmentFund.company_id == company_id).all()

    investors: dict[int, dict] = {}
    for a in accounts:
        iid = a.investor_id
        if iid not in investors:
            investors[iid] = {"investor_id": iid, "fund_count": 0, "total_committed": 0, "total_called": 0, "funds": []}
        investors[iid]["fund_count"] += 1
        investors[iid]["total_committed"] += a.committed_capital or 0
        investors[iid]["total_called"] += a.called_capital or 0
        investors[iid]["funds"].append(
            {"fund_id": a.fund_id, "committed": a.committed_capital, "called": a.called_capital, "pct": a.ownership_pct}
        )

    # enrich with counterparty name
    from app.models import Counterparty

    result = []
    for iid, inv in investors.items():
        cp = db.query(Counterparty).filter(Counterparty.id == iid).first()
        result.append({**inv, "investor_name": cp.name if cp else f"#{iid}"})

    return sorted(result, key=lambda x: x["total_committed"], reverse=True)


@router.get("/lp-investors/{investor_id}/summary")
def lp_investor_summary(
    investor_id: int, company_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)
):
    """单 LP 汇总。"""
    accounts = (
        db.query(CapitalAccount)
        .join(InvestmentFund)
        .filter(InvestmentFund.company_id == company_id, CapitalAccount.investor_id == investor_id)
        .all()
    )

    funds_detail = []
    total_com = 0
    total_called = 0
    for a in accounts:
        fund = db.query(InvestmentFund).filter(InvestmentFund.id == a.fund_id).first()
        calls = db.query(CapitalCall).filter(CapitalCall.fund_id == a.fund_id).all()
        dists = db.query(FundDistribution).filter(FundDistribution.fund_id == a.fund_id).all()
        funds_detail.append(
            {
                "fund_name": fund.fund_name if fund else "",
                "committed": a.committed_capital,
                "called": a.called_capital,
                "pct": a.ownership_pct,
                "pending_calls": sum(c.call_amount for c in calls if c.status == "pending"),
                "total_distributions": sum(d.amount for d in dists),
            }
        )
        total_com += a.committed_capital or 0
        total_called += a.called_capital or 0

    from app.models import Counterparty

    cp = db.query(Counterparty).filter(Counterparty.id == investor_id).first()
    return {
        "investor_name": cp.name if cp else "",
        "fund_count": len(funds_detail),
        "total_committed": total_com,
        "total_called": total_called,
        "funds": funds_detail,
    }


# --- Real Estate Assets ---


@router.get("/real-estate", response_model=list[RealEstateAssetResponse])
def list_real_estate(
    company_id: int,
    property_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    q = db.query(RealEstateAsset).filter(RealEstateAsset.company_id == company_id)
    if property_type:
        q = q.filter(RealEstateAsset.property_type == property_type)
    return q.order_by(RealEstateAsset.property_name).all()


@router.post("/real-estate", response_model=RealEstateAssetResponse)
def create_real_estate(
    data: RealEstateAssetCreate,
    company_id: int = Query(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    a = RealEstateAsset(company_id=company_id, **data.model_dump())
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


@router.put("/real-estate/{asset_id}", response_model=RealEstateAssetResponse)
def update_real_estate(
    asset_id: int, data: RealEstateAssetUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)
):
    a = db.query(RealEstateAsset).filter(RealEstateAsset.id == asset_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="资产不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(a, k, v)
    db.commit()
    db.refresh(a)
    return a


@router.delete("/real-estate/{asset_id}")
def delete_real_estate(asset_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    a = db.query(RealEstateAsset).filter(RealEstateAsset.id == asset_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="资产不存在")
    db.delete(a)
    db.commit()
    return {"ok": True}


# RE Valuations
@router.get("/real-estate/{asset_id}/valuations", response_model=list[RealEstateValuationResponse])
def list_re_valuations(asset_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return (
        db.query(RealEstateValuation)
        .filter(RealEstateValuation.asset_id == asset_id)
        .order_by(RealEstateValuation.valuation_date.desc())
        .all()
    )


@router.post("/real-estate/{asset_id}/valuations", response_model=RealEstateValuationResponse)
def create_re_valuation(
    asset_id: int,
    data: RealEstateValuationCreate,
    company_id: int = Query(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    asset = (
        db.query(RealEstateAsset)
        .filter(RealEstateAsset.id == asset_id, RealEstateAsset.company_id == company_id)
        .first()
    )
    if not asset:
        raise HTTPException(status_code=404, detail="资产不存在")
    v = RealEstateValuation(asset_id=asset_id, company_id=company_id, **data.model_dump())
    db.add(v)
    db.flush()
    if asset:
        asset.current_value = data.value
        asset.valuation_date = data.valuation_date
    db.commit()
    db.refresh(v)
    return v


@router.put("/real-estate/{asset_id}/valuations/{val_id}", response_model=RealEstateValuationResponse)
def update_re_valuation(
    asset_id: int,
    val_id: int,
    data: RealEstateValuationUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    v = (
        db.query(RealEstateValuation)
        .filter(RealEstateValuation.id == val_id, RealEstateValuation.asset_id == asset_id)
        .first()
    )
    if not v:
        raise HTTPException(status_code=404, detail="估值记录不存在")
    for k, val in data.model_dump(exclude_unset=True).items():
        setattr(v, k, val)
    db.commit()
    db.refresh(v)
    return v


@router.delete("/real-estate/{asset_id}/valuations/{val_id}")
def delete_re_valuation(asset_id: int, val_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    v = (
        db.query(RealEstateValuation)
        .filter(RealEstateValuation.id == val_id, RealEstateValuation.asset_id == asset_id)
        .first()
    )
    if not v:
        raise HTTPException(status_code=404, detail="估值记录不存在")
    db.delete(v)
    db.commit()
    return {"ok": True}


# --- Infrastructure Assets ---


@router.get("/infrastructure", response_model=list[InfraAssetResponse])
def list_infrastructure(
    company_id: int,
    asset_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    q = db.query(InfraAsset).filter(InfraAsset.company_id == company_id)
    if asset_type:
        q = q.filter(InfraAsset.asset_type == asset_type)
    return q.order_by(InfraAsset.project_name).all()


@router.post("/infrastructure", response_model=InfraAssetResponse)
def create_infrastructure(
    data: InfraAssetCreate, company_id: int = Query(...), db: Session = Depends(get_db), user=Depends(get_current_user)
):
    a = InfraAsset(company_id=company_id, **data.model_dump())
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


@router.put("/infrastructure/{asset_id}", response_model=InfraAssetResponse)
def update_infrastructure(
    asset_id: int, data: InfraAssetUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)
):
    a = db.query(InfraAsset).filter(InfraAsset.id == asset_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="资产不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(a, k, v)
    db.commit()
    db.refresh(a)
    return a


@router.delete("/infrastructure/{asset_id}")
def delete_infrastructure(asset_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    a = db.query(InfraAsset).filter(InfraAsset.id == asset_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="资产不存在")
    db.delete(a)
    db.commit()
    return {"ok": True}


# --- Private Credit ---


@router.get("/private-credit", response_model=list[PrivateCreditResponse])
def list_private_credit(
    company_id: int, status: Optional[str] = Query(None), db: Session = Depends(get_db), user=Depends(get_current_user)
):
    q = db.query(PrivateCredit).filter(PrivateCredit.company_id == company_id)
    if status:
        q = q.filter(PrivateCredit.status == status)
    return q.order_by(PrivateCredit.borrower_name).all()


@router.post("/private-credit", response_model=PrivateCreditResponse)
def create_private_credit(
    data: PrivateCreditCreate,
    company_id: int = Query(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    c = PrivateCredit(company_id=company_id, **data.model_dump())
    c.outstanding_principal = data.principal_amount
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@router.put("/private-credit/{credit_id}", response_model=PrivateCreditResponse)
def update_private_credit(
    credit_id: int, data: PrivateCreditUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)
):
    c = db.query(PrivateCredit).filter(PrivateCredit.id == credit_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="信贷记录不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(c, k, v)
    db.commit()
    db.refresh(c)
    return c


@router.delete("/private-credit/{credit_id}")
def delete_private_credit(credit_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    c = db.query(PrivateCredit).filter(PrivateCredit.id == credit_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="信贷记录不存在")
    db.delete(c)
    db.commit()
    return {"ok": True}


# Credit Payments (with auto-voucher)
@router.get("/private-credit/{credit_id}/payments", response_model=list[CreditPaymentResponse])
def list_credit_payments(credit_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return (
        db.query(CreditPayment)
        .filter(CreditPayment.credit_id == credit_id)
        .order_by(CreditPayment.payment_date.desc())
        .all()
    )


@router.post("/private-credit/{credit_id}/payments", response_model=CreditPaymentResponse)
def create_credit_payment(
    credit_id: int,
    data: CreditPaymentCreate,
    company_id: int = Query(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    credit = (
        db.query(PrivateCredit).filter(PrivateCredit.id == credit_id, PrivateCredit.company_id == company_id).first()
    )
    if not credit:
        raise HTTPException(status_code=404, detail="信贷记录不存在")
    p = CreditPayment(credit_id=credit_id, company_id=company_id, **data.model_dump())
    db.add(p)
    db.flush()
    if credit:
        if data.payment_type == "principal":
            credit.outstanding_principal = max(0, (credit.outstanding_principal or 0) - data.amount)
        elif data.payment_type == "interest":
            credit.accrued_interest = max(0, (credit.accrued_interest or 0) - data.amount)
    # Auto-voucher: interest payment → Dr:6411(利息支出) Cr:1002(银行存款)
    if credit:
        summary = f"{data.payment_type} {credit.borrower_name} ¥{data.amount:,.0f}"
        now = datetime.now(timezone.utc)
        month_str = now.strftime("%Y%m")
        count = (
            db.query(Voucher)
            .filter(Voucher.company_id == company_id, Voucher.date.startswith(now.strftime("%Y-%m")))
            .count()
        )
        vch = Voucher(
            company_id=company_id,
            date=data.payment_date,
            voucher_no=f"转字{month_str}-{count + 1:04d}",
            voucher_type="transfer",
            summary=summary,
            creator_id=user.id,
            status="draft",
        )
        db.add(vch)
        db.flush()
        if data.payment_type == "interest":
            db.add(
                VoucherEntry(voucher_id=vch.id, account_code="6411", debit=data.amount, credit=0.0, description=summary)
            )
        else:
            db.add(
                VoucherEntry(
                    voucher_id=vch.id,
                    account_code=credit.collateral or "1221",
                    debit=data.amount,
                    credit=0.0,
                    description=summary,
                )
            )
        db.add(VoucherEntry(voucher_id=vch.id, account_code="1002", debit=0.0, credit=data.amount, description=summary))
        p.voucher_id = vch.id
        db.flush()
    db.commit()
    db.refresh(p)
    return p


@router.put("/private-credit/{credit_id}/payments/{payment_id}", response_model=CreditPaymentResponse)
def update_credit_payment(
    credit_id: int,
    payment_id: int,
    data: CreditPaymentUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    p = db.query(CreditPayment).filter(CreditPayment.id == payment_id, CreditPayment.credit_id == credit_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="还款记录不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(p, k, v)
    db.commit()
    db.refresh(p)
    return p


@router.delete("/private-credit/{credit_id}/payments/{payment_id}")
def delete_credit_payment(
    credit_id: int, payment_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)
):
    p = db.query(CreditPayment).filter(CreditPayment.id == payment_id, CreditPayment.credit_id == credit_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="还款记录不存在")
    if p.voucher_id:
        db.query(VoucherEntry).filter(VoucherEntry.voucher_id == p.voucher_id).delete()
        db.query(Voucher).filter(Voucher.id == p.voucher_id).delete()
    db.delete(p)
    db.commit()
    return {"ok": True}
