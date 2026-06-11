# Investment Management Module — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the investment accounting module with 6 database tables, auto-voucher generation, and 5 frontend CRUD pages.

**Architecture:** Backend adds 6 SQLAlchemy models + Pydantic schemas + a FastAPI router that auto-generates accounting vouchers via AccountMapping rules. Frontend adds 5 Vue 3 pages using PrimeVue DataTable/Dialog patterns, updates router and menu. Existing `Account`, `Counterparty`, `Voucher`, `VoucherEntry` tables are reused.

**Tech Stack:** Python 3.12+ / FastAPI / SQLAlchemy / SQLite · Vue 3 / Vite / PrimeVue / Tailwind CSS / TypeScript

---

### Task 1: Add 6 investment models to models.py

**Files:**
- Modify: `backend/app/models.py` — append after the existing BudgetItem model (line ~261)

- [ ] **Step 1: Append InvestmentPortfolio, InvestmentPosition, InvestmentTransaction, FairValueAdjustment, InvestmentIncome, AccountMapping models**

Append the following after the last model (BudgetItem) in `backend/app/models.py`:

```python
class InvestmentPortfolio(Base):
    __tablename__ = "investment_portfolios"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    name = Column(String(200), nullable=False)
    investment_type = Column(String(20), nullable=False, default="general_equity")  # vc/pe/general_equity/secondary_market/alternative
    currency = Column(String(3), default="CNY")
    status = Column(String(16), default="active")  # active/closed/liquidated
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    positions = relationship("InvestmentPosition", back_populates="portfolio", cascade="all, delete-orphan")


class InvestmentPosition(Base):
    __tablename__ = "investment_positions"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("investment_portfolios.id"), nullable=False)
    account_code = Column(String(10), nullable=False)  # 1101/1501/1503/1511
    security_name = Column(String(200), nullable=False)
    security_code = Column(String(50), nullable=True)
    quantity = Column(Float, default=0.0)
    unit_cost = Column(Float, default=0.0)
    cost_amount = Column(Float, default=0.0)
    fair_value = Column(Float, default=0.0)
    fair_value_date = Column(String(10), nullable=True)
    valuation_method = Column(String(30), default="cost")  # market_price/cost/dcf/comparables
    counterparty_id = Column(Integer, ForeignKey("counterparties.id"), nullable=True)
    status = Column(String(16), default="active")  # active/exited/impaired
    created_at = Column(DateTime, default=datetime.utcnow)

    portfolio = relationship("InvestmentPortfolio", back_populates="positions")
    transactions = relationship("InvestmentTransaction", back_populates="position", cascade="all, delete-orphan")
    adjustments = relationship("FairValueAdjustment", back_populates="position", cascade="all, delete-orphan")


class InvestmentTransaction(Base):
    __tablename__ = "investment_transactions"

    id = Column(Integer, primary_key=True, index=True)
    position_id = Column(Integer, ForeignKey("investment_positions.id"), nullable=False)
    transaction_type = Column(String(20), nullable=False)  # buy/sell/capital_call/distribution/dividend/interest
    transaction_date = Column(String(10), nullable=False)
    quantity = Column(Float, default=0.0)
    price = Column(Float, default=0.0)
    amount = Column(Float, default=0.0)
    fee = Column(Float, default=0.0)
    voucher_id = Column(Integer, ForeignKey("vouchers.id"), nullable=True)
    counterparty_id = Column(Integer, ForeignKey("counterparties.id"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    position = relationship("InvestmentPosition", back_populates="transactions")


class FairValueAdjustment(Base):
    __tablename__ = "fair_value_adjustments"

    id = Column(Integer, primary_key=True, index=True)
    position_id = Column(Integer, ForeignKey("investment_positions.id"), nullable=False)
    adjustment_date = Column(String(10), nullable=False)
    previous_value = Column(Float, default=0.0)
    adjusted_value = Column(Float, default=0.0)
    change_amount = Column(Float, default=0.0)
    reason = Column(String(200), nullable=True)
    voucher_id = Column(Integer, ForeignKey("vouchers.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    position = relationship("InvestmentPosition", back_populates="adjustments")


class InvestmentIncome(Base):
    __tablename__ = "investment_incomes"

    id = Column(Integer, primary_key=True, index=True)
    position_id = Column(Integer, ForeignKey("investment_positions.id"), nullable=True)
    income_type = Column(String(20), nullable=False)  # dividend/interest/realized_gain/unrealized_gain/other
    income_date = Column(String(10), nullable=False)
    amount = Column(Float, default=0.0)
    voucher_id = Column(Integer, ForeignKey("vouchers.id"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AccountMapping(Base):
    __tablename__ = "account_mappings"

    id = Column(Integer, primary_key=True, index=True)
    transaction_type = Column(String(30), nullable=False)  # buy/sell/dividend/interest/fair_value_up/fair_value_down/capital_call/distribution
    investment_type = Column(String(20), nullable=True)  # NULL = applies to all
    debit_account_code = Column(String(10), nullable=False)
    credit_account_code = Column(String(10), nullable=False)
    description_template = Column(String(200), nullable=True)
```

- [ ] **Step 2: Verify models compile by running a Python import**

```bash
cd backend && uv run python -c "from app.models import InvestmentPortfolio, InvestmentPosition, InvestmentTransaction, FairValueAdjustment, InvestmentIncome, AccountMapping; print('Models OK')"
```
Expected: `Models OK`

- [ ] **Step 3: Commit**

```bash
git add backend/app/models.py
git commit --no-gpg-sign -m "feat: add 6 investment models to models.py

Add InvestmentPortfolio, InvestmentPosition, InvestmentTransaction,
FairValueAdjustment, InvestmentIncome, and AccountMapping models
with proper foreign keys and relationships."
```

---

### Task 2: Add investment Pydantic schemas to schemas.py

**Files:**
- Modify: `backend/app/schemas.py` — append after the last existing schema (CompanyUpdate, line ~279)

- [ ] **Step 1: Append investment request/response schemas**

Append to `backend/app/schemas.py`:

```python
from typing import Optional as TOptional  # avoid conflict with existing Optional import

class InvestmentPortfolioCreate(BaseModel):
    name: str
    investment_type: str = "general_equity"
    currency: str = "CNY"
    description: Optional[str] = None


class InvestmentPortfolioUpdate(BaseModel):
    name: Optional[str] = None
    investment_type: Optional[str] = None
    currency: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None


class InvestmentPortfolioResponse(BaseModel):
    id: int
    company_id: int
    name: str
    investment_type: str
    currency: str
    status: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class InvestmentPositionCreate(BaseModel):
    portfolio_id: int
    account_code: str
    security_name: str
    security_code: Optional[str] = None
    quantity: float = 0.0
    unit_cost: float = 0.0
    cost_amount: float = 0.0
    fair_value: float = 0.0
    fair_value_date: Optional[str] = None
    valuation_method: str = "cost"
    counterparty_id: Optional[int] = None


class InvestmentPositionUpdate(BaseModel):
    account_code: Optional[str] = None
    security_name: Optional[str] = None
    security_code: Optional[str] = None
    quantity: Optional[float] = None
    unit_cost: Optional[float] = None
    cost_amount: Optional[float] = None
    fair_value: Optional[float] = None
    fair_value_date: Optional[str] = None
    valuation_method: Optional[str] = None
    counterparty_id: Optional[int] = None
    status: Optional[str] = None


class InvestmentPositionResponse(BaseModel):
    id: int
    portfolio_id: int
    account_code: str
    security_name: str
    security_code: Optional[str] = None
    quantity: float
    unit_cost: float
    cost_amount: float
    fair_value: float
    fair_value_date: Optional[str] = None
    valuation_method: str
    counterparty_id: Optional[int] = None
    status: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class InvestmentTransactionCreate(BaseModel):
    position_id: int
    transaction_type: str
    transaction_date: str
    quantity: float = 0.0
    price: float = 0.0
    amount: float = 0.0
    fee: float = 0.0
    counterparty_id: Optional[int] = None
    notes: Optional[str] = None


class InvestmentTransactionResponse(BaseModel):
    id: int
    position_id: int
    transaction_type: str
    transaction_date: str
    quantity: float
    price: float
    amount: float
    fee: float
    voucher_id: Optional[int] = None
    counterparty_id: Optional[int] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class FairValueAdjustmentCreate(BaseModel):
    position_id: int
    adjustment_date: str
    previous_value: float = 0.0
    adjusted_value: float = 0.0
    change_amount: float = 0.0
    reason: Optional[str] = None


class FairValueAdjustmentResponse(BaseModel):
    id: int
    position_id: int
    adjustment_date: str
    previous_value: float
    adjusted_value: float
    change_amount: float
    reason: Optional[str] = None
    voucher_id: Optional[int] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class InvestmentIncomeCreate(BaseModel):
    position_id: Optional[int] = None
    income_type: str
    income_date: str
    amount: float = 0.0
    notes: Optional[str] = None


class InvestmentIncomeResponse(BaseModel):
    id: int
    position_id: Optional[int] = None
    income_type: str
    income_date: str
    amount: float
    voucher_id: Optional[int] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AccountMappingResponse(BaseModel):
    id: int
    transaction_type: str
    investment_type: Optional[str] = None
    debit_account_code: str
    credit_account_code: str
    description_template: Optional[str] = None

    model_config = {"from_attributes": True}
```

- [ ] **Step 2: Verify schemas compile**

```bash
cd backend && uv run python -c "from app.schemas import InvestmentPortfolioCreate, InvestmentPositionResponse, InvestmentTransactionCreate; print('Schemas OK')"
```
Expected: `Schemas OK`

- [ ] **Step 3: Commit**

```bash
git add backend/app/schemas.py
git commit --no-gpg-sign -m "feat: add investment Pydantic schemas

Add create/update/response schemas for all 6 investment models."
```

---

### Task 3: Create investments router with auto-voucher generation

**Files:**
- Create: `backend/app/routers/investments.py`

- [ ] **Step 1: Create the complete investments router**

Write `backend/app/routers/investments.py`:

```python
"""投资管理路由：组合/持仓/交易/估值/收益 + 自动凭证生成。"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    User, Voucher, VoucherEntry, Account,
    InvestmentPortfolio, InvestmentPosition, InvestmentTransaction,
    FairValueAdjustment, InvestmentIncome, AccountMapping,
)
from app.schemas import (
    InvestmentPortfolioCreate, InvestmentPortfolioUpdate, InvestmentPortfolioResponse,
    InvestmentPositionCreate, InvestmentPositionUpdate, InvestmentPositionResponse,
    InvestmentTransactionCreate, InvestmentTransactionResponse,
    FairValueAdjustmentCreate, FairValueAdjustmentResponse,
    InvestmentIncomeCreate, InvestmentIncomeResponse,
    AccountMappingResponse,
)
from app.auth import get_current_user

router = APIRouter()


def _generate_invest_voucher(db: Session, company_id: int, txn_type: str, amount: float,
                              account_code: str, txn_date: str, security_name: str,
                              creator_id: int, investment_type: str = "") -> int:
    """根据 AccountMapping 自动生成会计凭证，返回 voucher_id。"""
    # 查找科目映射规则（先精确匹配 investment_type，再回退到通用）
    mapping = db.query(AccountMapping).filter(
        AccountMapping.transaction_type == txn_type,
        AccountMapping.investment_type == investment_type,
    ).first()
    if not mapping:
        mapping = db.query(AccountMapping).filter(
            AccountMapping.transaction_type == txn_type,
            AccountMapping.investment_type.is_(None),
        ).first()
    if not mapping:
        return None  # 无映射规则，不生成凭证

    debit_code = mapping.debit_account_code
    credit_code = mapping.credit_account_code

    # 根据持仓科目确认借方/贷方科目（如果映射中有模糊科目如 1101/1503，优先用持仓科目）
    debit_code = account_code if debit_code.find("/") != -1 else debit_code
    credit_code = account_code if credit_code.find("/") != -1 else credit_code

    # 生成凭证字号
    now = datetime.now(timezone.utc)
    month_str = now.strftime("%Y%m")
    count = db.query(Voucher).filter(
        Voucher.company_id == company_id,
        Voucher.date.startswith(now.strftime("%Y-%m")),
    ).count()
    voucher_no = f"转字{month_str}-{count + 1:04d}"

    desc_tpl = (mapping.description_template or "{type} {name}")
    summary = desc_tpl.replace("{type}", txn_type).replace("{name}", security_name)

    voucher = Voucher(
        company_id=company_id, date=txn_date, voucher_no=voucher_no,
        voucher_type="transfer", summary=summary, creator_id=creator_id,
        status="draft",
    )
    db.add(voucher)
    db.flush()

    db.add(VoucherEntry(
        voucher_id=voucher.id, account_code=debit_code,
        debit=amount, credit=0.0,
        description=summary,
    ))
    db.add(VoucherEntry(
        voucher_id=voucher.id, account_code=credit_code,
        debit=0.0, credit=amount,
        description=summary,
    ))
    db.flush()
    return voucher.id


# --- Portfolios ---

@router.get("/portfolios", response_model=list[InvestmentPortfolioResponse])
def list_portfolios(company_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(InvestmentPortfolio).filter(
        InvestmentPortfolio.company_id == company_id
    ).order_by(InvestmentPortfolio.name).all()


@router.post("/portfolios", response_model=InvestmentPortfolioResponse)
def create_portfolio(data: InvestmentPortfolioCreate, company_id: int = Query(...),
                     db: Session = Depends(get_db), user=Depends(get_current_user)):
    p = InvestmentPortfolio(company_id=company_id, **data.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.put("/portfolios/{portfolio_id}", response_model=InvestmentPortfolioResponse)
def update_portfolio(portfolio_id: int, data: InvestmentPortfolioUpdate,
                     db: Session = Depends(get_db), user=Depends(get_current_user)):
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
def list_positions(company_id: int, portfolio_id: Optional[int] = Query(None),
                   db: Session = Depends(get_db), user=Depends(get_current_user)):
    q = db.query(InvestmentPosition).join(InvestmentPortfolio).filter(
        InvestmentPortfolio.company_id == company_id
    )
    if portfolio_id:
        q = q.filter(InvestmentPosition.portfolio_id == portfolio_id)
    return q.order_by(InvestmentPosition.security_name).all()


@router.post("/positions", response_model=InvestmentPositionResponse)
def create_position(data: InvestmentPositionCreate, company_id: int = Query(...),
                    db: Session = Depends(get_db), user=Depends(get_current_user)):
    # Verify portfolio belongs to company
    portfolio = db.query(InvestmentPortfolio).filter(
        InvestmentPortfolio.id == data.portfolio_id,
        InvestmentPortfolio.company_id == company_id,
    ).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="投资组合不存在")
    pos = InvestmentPosition(**data.model_dump())
    db.add(pos)
    db.commit()
    db.refresh(pos)
    return pos


@router.put("/positions/{position_id}", response_model=InvestmentPositionResponse)
def update_position(position_id: int, data: InvestmentPositionUpdate,
                    db: Session = Depends(get_db), user=Depends(get_current_user)):
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
def list_transactions(company_id: int, position_id: Optional[int] = Query(None),
                      db: Session = Depends(get_db), user=Depends(get_current_user)):
    q = db.query(InvestmentTransaction).join(InvestmentPosition).join(InvestmentPortfolio).filter(
        InvestmentPortfolio.company_id == company_id
    )
    if position_id:
        q = q.filter(InvestmentTransaction.position_id == position_id)
    return q.order_by(InvestmentTransaction.transaction_date.desc()).all()


@router.post("/transactions", response_model=InvestmentTransactionResponse)
def create_transaction(data: InvestmentTransactionCreate, company_id: int = Query(...),
                       db: Session = Depends(get_db), user=Depends(get_current_user)):
    pos = db.query(InvestmentPosition).join(InvestmentPortfolio).filter(
        InvestmentPosition.id == data.position_id,
        InvestmentPortfolio.company_id == company_id,
    ).first()
    if not pos:
        raise HTTPException(status_code=404, detail="持仓不存在")

    txn = InvestmentTransaction(**data.model_dump())
    db.add(txn)
    db.flush()

    # Auto-generate voucher
    portfolio = db.query(InvestmentPortfolio).filter(InvestmentPortfolio.id == pos.portfolio_id).first()
    voucher_id = _generate_invest_voucher(
        db=db, company_id=company_id, txn_type=data.transaction_type,
        amount=data.amount, account_code=pos.account_code,
        txn_date=data.transaction_date, security_name=pos.security_name,
        creator_id=user.id, investment_type=portfolio.investment_type if portfolio else "",
    )
    if voucher_id:
        txn.voucher_id = voucher_id
        db.flush()

    db.commit()
    db.refresh(txn)
    return txn


# --- Fair Value Adjustments ---

@router.get("/adjustments", response_model=list[FairValueAdjustmentResponse])
def list_adjustments(company_id: int, position_id: Optional[int] = Query(None),
                     db: Session = Depends(get_db), user=Depends(get_current_user)):
    q = db.query(FairValueAdjustment).join(InvestmentPosition).join(InvestmentPortfolio).filter(
        InvestmentPortfolio.company_id == company_id
    )
    if position_id:
        q = q.filter(FairValueAdjustment.position_id == position_id)
    return q.order_by(FairValueAdjustment.adjustment_date.desc()).all()


@router.post("/adjustments", response_model=FairValueAdjustmentResponse)
def create_adjustment(data: FairValueAdjustmentCreate, company_id: int = Query(...),
                      db: Session = Depends(get_db), user=Depends(get_current_user)):
    pos = db.query(InvestmentPosition).join(InvestmentPortfolio).filter(
        InvestmentPosition.id == data.position_id,
        InvestmentPortfolio.company_id == company_id,
    ).first()
    if not pos:
        raise HTTPException(status_code=404, detail="持仓不存在")

    adj = FairValueAdjustment(**data.model_dump())
    db.add(adj)
    db.flush()

    # Update position fair value
    pos.fair_value = data.adjusted_value
    pos.fair_value_date = data.adjustment_date
    if data.change_amount != 0:
        pos.valuation_method = "market_price"

    # Auto-generate voucher for fair value change
    txn_type = "fair_value_up" if data.change_amount > 0 else "fair_value_down"
    portfolio = db.query(InvestmentPortfolio).filter(InvestmentPortfolio.id == pos.portfolio_id).first()
    voucher_id = _generate_invest_voucher(
        db=db, company_id=company_id, txn_type=txn_type,
        amount=abs(data.change_amount), account_code=pos.account_code,
        txn_date=data.adjustment_date, security_name=pos.security_name,
        creator_id=user.id, investment_type=portfolio.investment_type if portfolio else "",
    )
    if voucher_id:
        adj.voucher_id = voucher_id
        db.flush()

    db.commit()
    db.refresh(adj)
    return adj


# --- Income ---

@router.get("/income", response_model=list[InvestmentIncomeResponse])
def list_income(company_id: int, position_id: Optional[int] = Query(None),
                db: Session = Depends(get_db), user=Depends(get_current_user)):
    q = db.query(InvestmentIncome)
    if position_id:
        q = q.filter(InvestmentIncome.position_id == position_id)
    else:
        q = q.outerjoin(InvestmentPosition).outerjoin(InvestmentPortfolio).filter(
            (InvestmentIncome.position_id.is_(None)) |
            (InvestmentPortfolio.company_id == company_id)
        )
    return q.order_by(InvestmentIncome.income_date.desc()).all()


@router.post("/income", response_model=InvestmentIncomeResponse)
def create_income(data: InvestmentIncomeCreate, company_id: int = Query(...),
                  db: Session = Depends(get_db), user=Depends(get_current_user)):
    inc = InvestmentIncome(**data.model_dump())
    db.add(inc)
    db.flush()

    # Auto-generate voucher if linked to a position
    if data.position_id:
        pos = db.query(InvestmentPosition).filter(InvestmentPosition.id == data.position_id).first()
        if pos:
            txn_map = {"dividend": "dividend", "interest": "interest",
                       "realized_gain": "sell", "unrealized_gain": "fair_value_up"}
            txn_type = txn_map.get(data.income_type, "dividend")
            portfolio = db.query(InvestmentPortfolio).filter(InvestmentPortfolio.id == pos.portfolio_id).first()
            voucher_id = _generate_invest_voucher(
                db=db, company_id=company_id, txn_type=txn_type,
                amount=data.amount, account_code=pos.account_code,
                txn_date=data.income_date, security_name=pos.security_name,
                creator_id=user.id, investment_type=portfolio.investment_type if portfolio else "",
            )
            if voucher_id:
                inc.voucher_id = voucher_id
                db.flush()

    db.commit()
    db.refresh(inc)
    return inc


# --- Account Mappings ---

@router.get("/mappings", response_model=list[AccountMappingResponse])
def list_mappings(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(AccountMapping).order_by(AccountMapping.transaction_type).all()


# --- Reports ---

@router.get("/reports/positions")
def report_positions(company_id: int, investment_type: Optional[str] = Query(None),
                     db: Session = Depends(get_db), user=Depends(get_current_user)):
    """持仓报告：按组合/类型汇总成本和公允价值。"""
    q = db.query(InvestmentPosition).join(InvestmentPortfolio).filter(
        InvestmentPortfolio.company_id == company_id
    )
    if investment_type:
        q = q.filter(InvestmentPortfolio.investment_type == investment_type)

    positions = q.order_by(InvestmentPortfolio.name, InvestmentPosition.security_name).all()
    result = []
    for p in positions:
        portfolio = db.query(InvestmentPortfolio).filter(InvestmentPortfolio.id == p.portfolio_id).first()
        result.append({
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
            "unrealized_gl_pct": round((p.fair_value - p.cost_amount) / p.cost_amount * 100, 2) if p.cost_amount else 0,
            "status": p.status,
            "fair_value_date": p.fair_value_date,
        })
    return result


@router.get("/reports/income")
def report_income(company_id: int, start_date: Optional[str] = Query(None),
                  end_date: Optional[str] = Query(None),
                  db: Session = Depends(get_db), user=Depends(get_current_user)):
    """收益报告：按收益类型汇总。"""
    q = db.query(InvestmentIncome)
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
        "items": [{"id": inc.id, "income_type": inc.income_type, "income_date": inc.income_date,
                   "amount": inc.amount, "position_id": inc.position_id, "notes": inc.notes,
                   "voucher_id": inc.voucher_id} for inc in incomes],
        "summary_by_type": [{"income_type": k, "amount": round(v, 2)} for k, v in by_type.items()],
        "total": round(total, 2),
    }


@router.get("/reports/fair-value")
def report_fair_value(company_id: int, start_date: Optional[str] = Query(None),
                      end_date: Optional[str] = Query(None),
                      db: Session = Depends(get_db), user=Depends(get_current_user)):
    """公允价值变动报告。"""
    q = db.query(FairValueAdjustment).join(InvestmentPosition).join(InvestmentPortfolio).filter(
        InvestmentPortfolio.company_id == company_id
    )
    if start_date:
        q = q.filter(FairValueAdjustment.adjustment_date >= start_date)
    if end_date:
        q = q.filter(FairValueAdjustment.adjustment_date <= end_date)
    adjustments = q.order_by(FairValueAdjustment.adjustment_date.desc()).all()

    total_change = sum(a.change_amount for a in adjustments)
    return {
        "items": [{"id": a.id, "position_id": a.position_id, "adjustment_date": a.adjustment_date,
                   "previous_value": a.previous_value, "adjusted_value": a.adjusted_value,
                   "change_amount": a.change_amount, "reason": a.reason} for a in adjustments],
        "total_change": round(total_change, 2),
    }
```

- [ ] **Step 2: Verify router imports correctly**

```bash
cd backend && uv run python -c "from app.routers.investments import router; print('Router OK:', len(router.routes), 'routes')"
```
Expected: `Router OK: N routes`

- [ ] **Step 3: Commit**

```bash
git add backend/app/routers/investments.py
git commit --no-gpg-sign -m "feat: add investments router with auto-voucher generation

CRUD for portfolios, positions, transactions, adjustments, income.
Auto-generates accounting vouchers via AccountMapping rules.
Includes 3 report endpoints: positions, income, fair-value."
```

---

### Task 4: Register investments router in main.py

**Files:**
- Modify: `backend/app/main.py`

- [ ] **Step 1: Import and register the investments router**

In `backend/app/main.py`, add the import and include_router lines.

**Edit 1**: Add `investments` to the routers import (line 7):
```
from app.routers import auth, users, companies, departments, accounts, vouchers, templates, periods, reports, audit, prints, permissions, cockpit, counterparties, persons, projects, investments
```

**Edit 2**: Add the include_router line after the projects router (after line 36):
```python
app.include_router(investments.router, prefix="/api/investments", tags=["投资管理"])
```

- [ ] **Step 2: Verify app starts and tables are created**

```bash
cd backend && timeout 5 uv run uvicorn app.main:app --port 8000 2>&1 || true
```
Expected: App starts without import errors. Kill after 5 seconds.

- [ ] **Step 3: Commit**

```bash
git add backend/app/main.py
git commit --no-gpg-sign -m "feat: register investments router in main.py"
```

---

### Task 5: Add AccountMapping seed data

**Files:**
- Modify: `backend/app/seed.py`

- [ ] **Step 1: Add seed_account_mappings function and call it in main seed**

Append at the end of `backend/app/seed.py` (before any `if __name__ == "__main__"` block):

```python
def seed_account_mappings():
    """预置投资交易→会计科目映射规则。"""
    from app.database import SessionLocal
    from app.models import AccountMapping

    db = SessionLocal()
    mappings = [
        ("buy", None, "1101", "1002", "{type} {name}"),
        ("sell", None, "1002", "1101", "{type} {name}"),
        ("dividend", None, "1002", "6111", "收到{name}分红"),
        ("interest", None, "1002", "6111", "收到{name}利息"),
        ("fair_value_up", None, "1101", "6101", "{name}公允价值上升"),
        ("fair_value_down", None, "6101", "1101", "{name}公允价值下降"),
        ("capital_call", None, "1511", "1002", "资本召唤-{name}"),
        ("distribution", None, "1002", "1511", "分配返还-{name}"),
    ]
    for txn_type, invest_type, debit, credit, desc_tpl in mappings:
        existing = db.query(AccountMapping).filter(
            AccountMapping.transaction_type == txn_type,
            AccountMapping.investment_type == invest_type,
        ).first()
        if not existing:
            db.add(AccountMapping(
                transaction_type=txn_type,
                investment_type=invest_type,
                debit_account_code=debit,
                credit_account_code=credit,
                description_template=desc_tpl,
            ))
    db.commit()
    db.close()
    print("AccountMapping seed completed")


if __name__ == "__main__":
    seed_all()
    seed_account_mappings()
```

- [ ] **Step 2: Run the seed and verify**

```bash
cd backend && uv run python -c "
from app.seed import seed_account_mappings
seed_account_mappings()
"
```
Expected: `AccountMapping seed completed`

- [ ] **Step 3: Verify mappings in database**

```bash
cd backend && uv run python -c "
from app.database import SessionLocal
from app.models import AccountMapping
db = SessionLocal()
for m in db.query(AccountMapping).all():
    print(f'{m.transaction_type}: {m.debit_account_code}/{m.credit_account_code} - {m.description_template}')
db.close()
"
```
Expected: 8 mapping rows printed.

- [ ] **Step 4: Commit**

```bash
git add backend/app/seed.py
git commit --no-gpg-sign -m "feat: add AccountMapping seed data with 8 default mappings"
```

---

### Task 6: Add investment API functions to frontend

**Files:**
- Modify: `frontend/src/api/index.ts` — append after the last API function (line ~126)

- [ ] **Step 1: Append investment API functions**

Append to `frontend/src/api/index.ts`:

```typescript
// Investment - Portfolios
export const listPortfolios = (companyId: number) =>
  api.get('/investments/portfolios', { params: { company_id: companyId } })
export const createPortfolio = (companyId: number, data: { name: string; investment_type: string; currency: string; description?: string }) =>
  api.post('/investments/portfolios', data, { params: { company_id: companyId } })
export const updatePortfolio = (portfolioId: number, data: Record<string, any>) =>
  api.put(`/investments/portfolios/${portfolioId}`, data)
export const deletePortfolio = (portfolioId: number) =>
  api.delete(`/investments/portfolios/${portfolioId}`)

// Investment - Positions
export const listPositions = (companyId: number, portfolioId?: number) =>
  api.get('/investments/positions', { params: { company_id: companyId, ...(portfolioId ? { portfolio_id: portfolioId } : {}) } })
export const createPosition = (companyId: number, data: any) =>
  api.post('/investments/positions', data, { params: { company_id: companyId } })
export const updatePosition = (positionId: number, data: any) =>
  api.put(`/investments/positions/${positionId}`, data)
export const deletePosition = (positionId: number) =>
  api.delete(`/investments/positions/${positionId}`)

// Investment - Transactions
export const listTransactions = (companyId: number, positionId?: number) =>
  api.get('/investments/transactions', { params: { company_id: companyId, ...(positionId ? { position_id: positionId } : {}) } })
export const createTransaction = (companyId: number, data: any) =>
  api.post('/investments/transactions', data, { params: { company_id: companyId } })

// Investment - Adjustments
export const listAdjustments = (companyId: number, positionId?: number) =>
  api.get('/investments/adjustments', { params: { company_id: companyId, ...(positionId ? { position_id: positionId } : {}) } })
export const createAdjustment = (companyId: number, data: any) =>
  api.post('/investments/adjustments', data, { params: { company_id: companyId } })

// Investment - Income
export const listInvestmentIncome = (companyId: number, positionId?: number) =>
  api.get('/investments/income', { params: { company_id: companyId, ...(positionId ? { position_id: positionId } : {}) } })
export const createInvestmentIncome = (companyId: number, data: any) =>
  api.post('/investments/income', data, { params: { company_id: companyId } })

// Investment - Reports
export const getPositionsReport = (companyId: number, investmentType?: string) =>
  api.get('/investments/reports/positions', { params: { company_id: companyId, ...(investmentType ? { investment_type: investmentType } : {}) } })
export const getIncomeReport = (companyId: number, startDate?: string, endDate?: string) =>
  api.get('/investments/reports/income', { params: { company_id: companyId, ...(startDate ? { start_date: startDate } : {}), ...(endDate ? { end_date: endDate } : {}) } })
export const getFairValueReport = (companyId: number, startDate?: string, endDate?: string) =>
  api.get('/investments/reports/fair-value', { params: { company_id: companyId, ...(startDate ? { start_date: startDate } : {}), ...(endDate ? { end_date: endDate } : {}) } })
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd frontend && npx vue-tsc --noEmit --skipLibCheck 2>&1 | tail -5
```
Expected: No new errors related to api/index.ts

- [ ] **Step 3: Commit**

```bash
git add frontend/src/api/index.ts
git commit --no-gpg-sign -m "feat: add investment API functions to frontend"
```

---

### Task 7: Update router and menu for investment module

**Files:**
- Modify: `frontend/src/router/index.ts` — replace placeholder investment routes
- Modify: `frontend/src/App.vue` — update investment menu items

- [ ] **Step 1: Replace placeholder investment routes with real component routes**

In `frontend/src/router/index.ts`, replace the 4 placeholder investment routes (lines 47-50) with:

```typescript
// 投资管理
{ path: '/finance/investments/portfolio', component: () => import('../views/InvestmentPortfolio.vue'), meta: { requiresAuth: true } },
{ path: '/finance/investments/positions', component: () => import('../views/InvestmentPositions.vue'), meta: { requiresAuth: true } },
{ path: '/finance/investments/transactions', component: () => import('../views/InvestmentTransactions.vue'), meta: { requiresAuth: true } },
{ path: '/finance/investments/income', component: () => import('../views/InvestmentIncome.vue'), meta: { requiresAuth: true } },
{ path: '/finance/investments/reports', component: () => import('../views/InvestmentReports.vue'), meta: { requiresAuth: true } },
```

**Step 1b**: Append 8 future expansion placeholder routes after the investment report route:

```typescript
// 投资管理 — 预留扩展路由（A/C方案）
{ path: '/finance/investments/funds', component: () => import('../views/PlaceholderPage.vue'), meta: { requiresAuth: true, pageTitle: '基金管理' } },
{ path: '/finance/investments/investors', component: () => import('../views/PlaceholderPage.vue'), meta: { requiresAuth: true, pageTitle: 'LP投资管理' } },
{ path: '/finance/investments/performance', component: () => import('../views/PlaceholderPage.vue'), meta: { requiresAuth: true, pageTitle: '绩效分析' } },
{ path: '/finance/investments/waterfall', component: () => import('../views/PlaceholderPage.vue'), meta: { requiresAuth: true, pageTitle: '分配瀑布' } },
{ path: '/finance/investments/securities', component: () => import('../views/PlaceholderPage.vue'), meta: { requiresAuth: true, pageTitle: '证券主数据' } },
{ path: '/finance/investments/real-estate', component: () => import('../views/PlaceholderPage.vue'), meta: { requiresAuth: true, pageTitle: '房地产资产' } },
{ path: '/finance/investments/infrastructure', component: () => import('../views/PlaceholderPage.vue'), meta: { requiresAuth: true, pageTitle: '基础设施资产' } },
{ path: '/finance/investments/private-credit', component: () => import('../views/PlaceholderPage.vue'), meta: { requiresAuth: true, pageTitle: '私募信贷资产' } },
```

- [ ] **Step 2: Update investment menu in App.vue**

In `frontend/src/App.vue`, replace the investment menu section (lines 94-103) with:

```typescript
{
  icon: 'pi pi-chart-line',
  title: '投资管理',
  items: [
    { label: '投资组合总览', icon: 'pi pi-globe', to: '/finance/investments/portfolio' },
    { label: '投资持仓', icon: 'pi pi-briefcase', to: '/finance/investments/positions' },
    { label: '投资交易', icon: 'pi pi-arrow-right-arrow-left', to: '/finance/investments/transactions' },
    { label: '投资收益', icon: 'pi pi-dollar', to: '/finance/investments/income' },
    { label: '投资报表', icon: 'pi pi-chart-bar', to: '/finance/investments/reports' },
  ],
},
```

- [ ] **Step 3: Verify frontend compiles**

```bash
cd frontend && npx vue-tsc --noEmit --skipLibCheck 2>&1 | head -20
```
Expected: No critical errors (note: new .vue files don't exist yet, so errors about missing components are expected).

- [ ] **Step 4: Commit**

```bash
git add frontend/src/router/index.ts frontend/src/App.vue
git commit --no-gpg-sign -m "feat: update router and menu for investment module

Replace 4 placeholder routes with 5 real component routes.
Add 8 future expansion placeholder routes for full investment mgmt.
Update sidebar menu with new investment item structure."
```

---

### Task 8: Create InvestmentPortfolio.vue page

**Files:**
- Create: `frontend/src/views/InvestmentPortfolio.vue`

- [ ] **Step 1: Create the portfolio management page**

Write `frontend/src/views/InvestmentPortfolio.vue`:

```vue
<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import Textarea from 'primevue/textarea'
import Tag from 'primevue/tag'
import { listPortfolios, createPortfolio, updatePortfolio, deletePortfolio } from '@/api'

const portfolios = ref<any[]>([])
const loading = ref(false)
const saving = ref(false)
const showDialog = ref(false)
const editingId = ref<number | null>(null)
const companyId = computed(() => parseInt(localStorage.getItem('companyId') || '1'))

const INVEST_TYPES = [
  { label: '风险投资 VC', value: 'vc' },
  { label: '私募股权 PE', value: 'pe' },
  { label: '一般股权投资', value: 'general_equity' },
  { label: '二级市场投资', value: 'secondary_market' },
  { label: '另类资产', value: 'alternative' },
]

const TYPE_LABELS: Record<string, string> = {
  vc: 'VC', pe: 'PE', general_equity: '一般股权', secondary_market: '二级市场', alternative: '另类资产',
}

const STATUS_LABELS: Record<string, string> = {
  active: '活跃', closed: '已关闭', liquidated: '已清算',
}

const STATUS_SEVERITY: Record<string, string> = {
  active: 'success', closed: 'warning', liquidated: 'danger',
}

const emptyForm = () => ({ name: '', investment_type: 'general_equity', currency: 'CNY', description: '' })
const form = ref(emptyForm())

async function load() {
  loading.value = true
  try {
    const res = await listPortfolios(companyId.value)
    portfolios.value = res.data
  } finally { loading.value = false }
}

function openAdd() {
  editingId.value = null
  form.value = emptyForm()
  showDialog.value = true
}

function openEdit(row: any) {
  editingId.value = row.id
  form.value = { name: row.name, investment_type: row.investment_type, currency: row.currency, description: row.description || '' }
  showDialog.value = true
}

async function handleSave() {
  if (!form.value.name) return
  saving.value = true
  try {
    if (editingId.value) {
      await updatePortfolio(editingId.value, form.value)
    } else {
      await createPortfolio(companyId.value, form.value)
    }
    showDialog.value = false
    await load()
  } catch (e: any) {
    alert(e.response?.data?.detail || '保存失败')
  } finally { saving.value = false }
}

async function handleDelete(id: number) {
  if (!confirm('确认删除该投资组合？组合下的持仓也会被删除。')) return
  try {
    await deletePortfolio(id)
    await load()
  } catch (e: any) { alert(e.response?.data?.detail || '删除失败') }
}

onMounted(load)
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-lg font-semibold text-zinc-700">投资组合总览</h2>
      <Button label="新增组合" icon="pi pi-plus" @click="openAdd" />
    </div>

    <DataTable :value="portfolios" :loading="loading" stripedRows size="small" paginator :rows="10">
      <Column field="name" header="组合名称" sortable />
      <Column field="investment_type" header="投资类型" sortable>
        <template #body="{ data }">
          <Tag :value="TYPE_LABELS[data.investment_type] || data.investment_type" />
        </template>
      </Column>
      <Column field="currency" header="币种" sortable style="width:80px" />
      <Column field="status" header="状态" sortable style="width:100px">
        <template #body="{ data }">
          <Tag :value="STATUS_LABELS[data.status] || data.status" :severity="STATUS_SEVERITY[data.status] || 'info'" />
        </template>
      </Column>
      <Column field="description" header="备注" />
      <Column header="操作" style="width:140px">
        <template #body="{ data }">
          <div class="flex gap-1">
            <Button icon="pi pi-pencil" text size="small" @click="openEdit(data)" />
            <Button icon="pi pi-trash" text severity="danger" size="small" @click="handleDelete(data.id)" />
          </div>
        </template>
      </Column>
    </DataTable>

    <Dialog v-model:visible="showDialog" :header="editingId ? '编辑组合' : '新增组合'" :modal="true" class="w-[450px]">
      <div class="flex flex-col gap-3">
        <div><label class="block text-sm mb-1">组合名称 *</label><InputText v-model="form.name" class="w-full" /></div>
        <div><label class="block text-sm mb-1">投资类型</label><Dropdown v-model="form.investment_type" :options="INVEST_TYPES" optionLabel="label" optionValue="value" class="w-full" /></div>
        <div><label class="block text-sm mb-1">币种</label><Dropdown v-model="form.currency" :options="[{label:'CNY',value:'CNY'},{label:'USD',value:'USD'},{label:'HKD',value:'HKD'}]" optionLabel="label" optionValue="value" class="w-full" /></div>
        <div><label class="block text-sm mb-1">备注</label><Textarea v-model="form.description" rows="2" class="w-full" /></div>
      </div>
      <template #footer>
        <Button label="取消" text @click="showDialog = false" />
        <Button label="保存" :loading="saving" @click="handleSave" />
      </template>
    </Dialog>
  </div>
</template>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/InvestmentPortfolio.vue
git commit --no-gpg-sign -m "feat: add InvestmentPortfolio page with CRUD"
```

---

### Task 9: Create InvestmentPositions.vue page

**Files:**
- Create: `frontend/src/views/InvestmentPositions.vue`

- [ ] **Step 1: Create the positions management page**

Write `frontend/src/views/InvestmentPositions.vue`:

```vue
<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Dropdown from 'primevue/dropdown'
import Tag from 'primevue/tag'
import { listPortfolios, listPositions, listAccounts, listCounterparties, createPosition, updatePosition, deletePosition } from '@/api'

const portfolios = ref<any[]>([])
const accounts = ref<any[]>([])
const counterparties = ref<any[]>([])
const positions = ref<any[]>([])
const filterPortfolio = ref<number | null>(null)
const loading = ref(false)
const saving = ref(false)
const showDialog = ref(false)
const editingId = ref<number | null>(null)
const companyId = computed(() => parseInt(localStorage.getItem('companyId') || '1'))

const ACCOUNT_OPTIONS = computed(() =>
  accounts.value.filter((a: any) => ['1101','1501','1503','1511'].some(c => a.code.startsWith(c)))
    .map((a: any) => ({ label: `${a.code} ${a.name}`, value: a.code }))
)

const STATUS_LABELS: Record<string, string> = { active: '活跃', exited: '已退出', impaired: '已减值' }
const emptyForm = () => ({
  portfolio_id: filterPortfolio.value || null, account_code: '', security_name: '',
  security_code: '', quantity: 0, unit_cost: 0, cost_amount: 0, fair_value: 0,
  fair_value_date: '', valuation_method: 'cost', counterparty_id: null,
})
const form = ref(emptyForm())

async function load() {
  loading.value = true
  try {
    const [pRes, aRes, cRes, posRes] = await Promise.all([
      listPortfolios(companyId.value),
      listAccounts(companyId.value),
      listCounterparties(companyId.value),
      listPositions(companyId.value, filterPortfolio.value || undefined),
    ])
    portfolios.value = pRes.data
    accounts.value = aRes.data
    counterparties.value = cRes.data
    positions.value = posRes.data
  } finally { loading.value = false }
}

function openAdd() {
  editingId.value = null
  form.value = emptyForm()
  showDialog.value = true
}

function openEdit(row: any) {
  editingId.value = row.id
  form.value = {
    portfolio_id: row.portfolio_id, account_code: row.account_code,
    security_name: row.security_name, security_code: row.security_code || '',
    quantity: row.quantity, unit_cost: row.unit_cost, cost_amount: row.cost_amount,
    fair_value: row.fair_value, fair_value_date: row.fair_value_date || '',
    valuation_method: row.valuation_method, counterparty_id: row.counterparty_id,
  }
  showDialog.value = true
}

async function handleSave() {
  if (!form.value.security_name || !form.value.account_code) return
  saving.value = true
  try {
    if (editingId.value) {
      await updatePosition(editingId.value, form.value)
    } else {
      await createPosition(companyId.value, form.value)
    }
    showDialog.value = false
    await load()
  } catch (e: any) {
    alert(e.response?.data?.detail || '保存失败')
  } finally { saving.value = false }
}

async function handleDelete(id: number) {
  if (!confirm('确认删除该持仓？')) return
  try {
    await deletePosition(id)
    await load()
  } catch (e: any) { alert(e.response?.data?.detail || '删除失败') }
}

function onFilterChange() {
  load()
}

onMounted(load)
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-4">
      <div class="flex gap-2 items-center">
        <h2 class="text-lg font-semibold text-zinc-700">投资持仓</h2>
        <Dropdown v-model="filterPortfolio" :options="portfolios" optionLabel="name" optionValue="id"
                  placeholder="全部组合" class="w-48" @change="onFilterChange" showClear />
      </div>
      <Button label="新增持仓" icon="pi pi-plus" @click="openAdd" />
    </div>

    <DataTable :value="positions" :loading="loading" stripedRows size="small" paginator :rows="10">
      <Column field="security_name" header="标的名称" sortable />
      <Column field="security_code" header="代码" sortable style="width:100px" />
      <Column field="account_code" header="科目" sortable style="width:100px" />
      <Column field="quantity" header="数量" sortable style="width:100px">
        <template #body="{ data }">{{ data.quantity.toLocaleString() }}</template>
      </Column>
      <Column field="cost_amount" header="成本" sortable style="width:120px">
        <template #body="{ data }">{{ data.cost_amount.toLocaleString() }}</template>
      </Column>
      <Column field="fair_value" header="公允价值" sortable style="width:120px">
        <template #body="{ data }">{{ data.fair_value.toLocaleString() }}</template>
      </Column>
      <Column header="未实现损益" style="width:120px">
        <template #body="{ data }">
          <span :class="data.fair_value - data.cost_amount >= 0 ? 'text-green-600' : 'text-red-600'">
            {{ (data.fair_value - data.cost_amount).toLocaleString() }}
          </span>
        </template>
      </Column>
      <Column field="status" header="状态" sortable style="width:80px">
        <template #body="{ data }">
          <Tag :value="STATUS_LABELS[data.status] || data.status"
               :severity="data.status === 'active' ? 'success' : data.status === 'exited' ? 'warning' : 'danger'" />
        </template>
      </Column>
      <Column header="操作" style="width:140px">
        <template #body="{ data }">
          <div class="flex gap-1">
            <Button icon="pi pi-pencil" text size="small" @click="openEdit(data)" />
            <Button icon="pi pi-trash" text severity="danger" size="small" @click="handleDelete(data.id)" />
          </div>
        </template>
      </Column>
    </DataTable>

    <Dialog v-model:visible="showDialog" :header="editingId ? '编辑持仓' : '新增持仓'" :modal="true" class="w-[500px]">
      <div class="flex flex-col gap-3">
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-sm mb-1">所属组合</label>
            <Dropdown v-model="form.portfolio_id" :options="portfolios" optionLabel="name" optionValue="id" class="w-full" />
          </div>
          <div>
            <label class="block text-sm mb-1">会计科目 *</label>
            <Dropdown v-model="form.account_code" :options="ACCOUNT_OPTIONS" optionLabel="label" optionValue="value" class="w-full" filter />
          </div>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div><label class="block text-sm mb-1">标的名称 *</label><InputText v-model="form.security_name" class="w-full" /></div>
          <div><label class="block text-sm mb-1">代码</label><InputText v-model="form.security_code" class="w-full" /></div>
        </div>
        <div class="grid grid-cols-3 gap-3">
          <div><label class="block text-sm mb-1">数量</label><InputNumber v-model="form.quantity" class="w-full" /></div>
          <div><label class="block text-sm mb-1">单位成本</label><InputNumber v-model="form.unit_cost" class="w-full" /></div>
          <div><label class="block text-sm mb-1">成本总额</label><InputNumber v-model="form.cost_amount" class="w-full" /></div>
        </div>
        <div class="grid grid-cols-3 gap-3">
          <div><label class="block text-sm mb-1">公允价值</label><InputNumber v-model="form.fair_value" class="w-full" /></div>
          <div><label class="block text-sm mb-1">估值日期</label><InputText v-model="form.fair_value_date" class="w-full" /></div>
          <div>
            <label class="block text-sm mb-1">估值方法</label>
            <Dropdown v-model="form.valuation_method" :options="[{label:'市价',value:'market_price'},{label:'成本',value:'cost'},{label:'DCF',value:'dcf'},{label:'可比',value:'comparables'}]" optionLabel="label" optionValue="value" class="w-full" />
          </div>
        </div>
        <div><label class="block text-sm mb-1">被投资方</label><Dropdown v-model="form.counterparty_id" :options="counterparties" optionLabel="name" optionValue="id" class="w-full" showClear /></div>
      </div>
      <template #footer>
        <Button label="取消" text @click="showDialog = false" />
        <Button label="保存" :loading="saving" @click="handleSave" />
      </template>
    </Dialog>
  </div>
</template>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/InvestmentPositions.vue
git commit --no-gpg-sign -m "feat: add InvestmentPositions page with CRUD"
```

---

### Task 10: Create InvestmentTransactions.vue page

**Files:**
- Create: `frontend/src/views/InvestmentTransactions.vue`

- [ ] **Step 1: Create the transactions page**

Write `frontend/src/views/InvestmentTransactions.vue`:

```vue
<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Dropdown from 'primevue/dropdown'
import Textarea from 'primevue/textarea'
import Tag from 'primevue/tag'
import { listPositions, listTransactions, createTransaction } from '@/api'

const positions = ref<any[]>([])
const transactions = ref<any[]>([])
const filterPosition = ref<number | null>(null)
const loading = ref(false)
const saving = ref(false)
const showDialog = ref(false)
const showVoucherId = ref<number | null>(null)
const companyId = computed(() => parseInt(localStorage.getItem('companyId') || '1'))

const TXN_TYPES = [
  { label: '买入', value: 'buy' },
  { label: '卖出', value: 'sell' },
  { label: '资本召唤', value: 'capital_call' },
  { label: '分配返还', value: 'distribution' },
  { label: '分红', value: 'dividend' },
  { label: '利息', value: 'interest' },
]

const TYPE_LABELS: Record<string, string> = {
  buy: '买入', sell: '卖出', capital_call: '资本召唤', distribution: '分配返还', dividend: '分红', interest: '利息',
}

const emptyForm = () => ({
  position_id: filterPosition.value || null, transaction_type: 'buy', transaction_date: '',
  quantity: 0, price: 0, amount: 0, fee: 0, counterparty_id: null, notes: '',
})
const form = ref(emptyForm())

async function load() {
  loading.value = true
  try {
    const [posRes, txnRes] = await Promise.all([
      listPositions(companyId.value),
      listTransactions(companyId.value, filterPosition.value || undefined),
    ])
    positions.value = posRes.data
    transactions.value = txnRes.data
  } finally { loading.value = false }
}

function getPositionName(posId: number) {
  const pos = positions.value.find((p: any) => p.id === posId)
  return pos ? `${pos.security_name} (${pos.account_code})` : `#${posId}`
}

function openAdd() {
  form.value = emptyForm()
  showDialog.value = true
}

async function handleSave() {
  if (!form.value.position_id || !form.value.transaction_date || !form.value.amount) return
  saving.value = true
  try {
    const res = await createTransaction(companyId.value, form.value)
    showDialog.value = false
    showVoucherId.value = res.data.voucher_id
    await load()
  } catch (e: any) {
    alert(e.response?.data?.detail || '保存失败')
  } finally { saving.value = false }
}

function onFilterChange() {
  load()
}

onMounted(load)
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-4">
      <div class="flex gap-2 items-center">
        <h2 class="text-lg font-semibold text-zinc-700">投资交易</h2>
        <Dropdown v-model="filterPosition" :options="positions" optionLabel="security_name" optionValue="id"
                  placeholder="全部持仓" class="w-48" @change="onFilterChange" showClear />
      </div>
      <Button label="新增交易" icon="pi pi-plus" @click="openAdd" />
    </div>

    <!-- Auto-voucher notification -->
    <div v-if="showVoucherId" class="mb-3 p-2 bg-green-50 border border-green-200 rounded text-sm flex justify-between items-center">
      <span><i class="pi pi-check-circle text-green-600 mr-1" /> 交易已保存，自动生成凭证 #{{ showVoucherId }}</span>
      <Button icon="pi pi-times" text size="small" @click="showVoucherId = null" />
    </div>

    <DataTable :value="transactions" :loading="loading" stripedRows size="small" paginator :rows="10">
      <Column field="transaction_date" header="日期" sortable style="width:100px" />
      <Column header="持仓" sortable style="width:160px">
        <template #body="{ data }">{{ getPositionName(data.position_id) }}</template>
      </Column>
      <Column field="transaction_type" header="类型" sortable style="width:100px">
        <template #body="{ data }">
          <Tag :value="TYPE_LABELS[data.transaction_type] || data.transaction_type"
               :severity="data.transaction_type === 'buy' ? 'info' : data.transaction_type === 'sell' ? 'warn' : 'success'" />
        </template>
      </Column>
      <Column field="quantity" header="数量" sortable style="width:100px">
        <template #body="{ data }">{{ data.quantity.toLocaleString() }}</template>
      </Column>
      <Column field="price" header="价格" sortable style="width:100px">
        <template #body="{ data }">{{ data.price.toLocaleString() }}</template>
      </Column>
      <Column field="amount" header="金额" sortable style="width:120px">
        <template #body="{ data }">{{ data.amount.toLocaleString() }}</template>
      </Column>
      <Column field="voucher_id" header="凭证号" sortable style="width:80px">
        <template #body="{ data }">
          <span v-if="data.voucher_id" class="text-blue-600">#{{ data.voucher_id }}</span>
          <span v-else class="text-zinc-400">-</span>
        </template>
      </Column>
      <Column field="notes" header="备注" />
    </DataTable>

    <Dialog v-model:visible="showDialog" header="新增交易（自动生成凭证）" :modal="true" class="w-[500px]">
      <div class="flex flex-col gap-3">
        <div>
          <label class="block text-sm mb-1">持仓 *</label>
          <Dropdown v-model="form.position_id" :options="positions" optionLabel="security_name" optionValue="id" class="w-full" filter />
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-sm mb-1">交易类型 *</label>
            <Dropdown v-model="form.transaction_type" :options="TXN_TYPES" optionLabel="label" optionValue="value" class="w-full" />
          </div>
          <div><label class="block text-sm mb-1">交易日期 *</label><InputText v-model="form.transaction_date" class="w-full" placeholder="YYYY-MM-DD" /></div>
        </div>
        <div class="grid grid-cols-3 gap-3">
          <div><label class="block text-sm mb-1">数量</label><InputNumber v-model="form.quantity" class="w-full" /></div>
          <div><label class="block text-sm mb-1">价格</label><InputNumber v-model="form.price" class="w-full" /></div>
          <div><label class="block text-sm mb-1">手续费</label><InputNumber v-model="form.fee" class="w-full" /></div>
        </div>
        <div><label class="block text-sm mb-1">金额 *</label><InputNumber v-model="form.amount" class="w-full" /></div>
        <div><label class="block text-sm mb-1">备注</label><Textarea v-model="form.notes" rows="2" class="w-full" /></div>
        <p class="text-xs text-zinc-400"><i class="pi pi-info-circle mr-1" /> 保存后将自动生成会计凭证</p>
      </div>
      <template #footer>
        <Button label="取消" text @click="showDialog = false" />
        <Button label="保存并生成凭证" :loading="saving" @click="handleSave" />
      </template>
    </Dialog>
  </div>
</template>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/InvestmentTransactions.vue
git commit --no-gpg-sign -m "feat: add InvestmentTransactions page with auto-voucher preview"
```

---

### Task 11: Create InvestmentIncome.vue page

**Files:**
- Create: `frontend/src/views/InvestmentIncome.vue`

- [ ] **Step 1: Create the income tracking page**

Write `frontend/src/views/InvestmentIncome.vue`:

```vue
<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Dropdown from 'primevue/dropdown'
import Textarea from 'primevue/textarea'
import Tag from 'primevue/tag'
import { listPositions, listInvestmentIncome, createInvestmentIncome } from '@/api'

const positions = ref<any[]>([])
const incomes = ref<any[]>([])
const loading = ref(false)
const saving = ref(false)
const showDialog = ref(false)
const companyId = computed(() => parseInt(localStorage.getItem('companyId') || '1'))

const INCOME_TYPES = [
  { label: '分红', value: 'dividend' },
  { label: '利息', value: 'interest' },
  { label: '已实现收益', value: 'realized_gain' },
  { label: '未实现收益', value: 'unrealized_gain' },
  { label: '其他', value: 'other' },
]
const TYPE_LABELS: Record<string, string> = {
  dividend: '分红', interest: '利息', realized_gain: '已实现收益', unrealized_gain: '未实现收益', other: '其他',
}

const emptyForm = () => ({
  position_id: null as number | null, income_type: 'dividend', income_date: '', amount: 0, notes: '',
})
const form = ref(emptyForm())

async function load() {
  loading.value = true
  try {
    const [posRes, incRes] = await Promise.all([
      listPositions(companyId.value),
      listInvestmentIncome(companyId.value),
    ])
    positions.value = posRes.data
    incomes.value = incRes.data
  } finally { loading.value = false }
}

function getPositionName(posId: number | null) {
  if (!posId) return '-'
  const pos = positions.value.find((p: any) => p.id === posId)
  return pos ? pos.security_name : `#${posId}`
}

function openAdd() {
  form.value = emptyForm()
  showDialog.value = true
}

async function handleSave() {
  if (!form.value.income_date || form.value.amount <= 0) return
  saving.value = true
  try {
    await createInvestmentIncome(companyId.value, form.value)
    showDialog.value = false
    await load()
  } catch (e: any) { alert(e.response?.data?.detail || '保存失败') }
  finally { saving.value = false }
}

onMounted(load)
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-lg font-semibold text-zinc-700">投资收益</h2>
      <Button label="新增收益" icon="pi pi-plus" @click="openAdd" />
    </div>

    <DataTable :value="incomes" :loading="loading" stripedRows size="small" paginator :rows="10">
      <Column field="income_date" header="日期" sortable style="width:100px" />
      <Column header="相关持仓" sortable style="width:150px">
        <template #body="{ data }">{{ getPositionName(data.position_id) }}</template>
      </Column>
      <Column field="income_type" header="类型" sortable style="width:120px">
        <template #body="{ data }">
          <Tag :value="TYPE_LABELS[data.income_type] || data.income_type"
               :severity="data.income_type === 'dividend' ? 'info' : 'success'" />
        </template>
      </Column>
      <Column field="amount" header="金额" sortable style="width:120px">
        <template #body="{ data }">{{ data.amount.toLocaleString() }}</template>
      </Column>
      <Column field="voucher_id" header="凭证号" sortable style="width:80px">
        <template #body="{ data }">
          <span v-if="data.voucher_id" class="text-blue-600">#{{ data.voucher_id }}</span>
          <span v-else class="text-zinc-400">-</span>
        </template>
      </Column>
      <Column field="notes" header="备注" />
    </DataTable>

    <Dialog v-model:visible="showDialog" header="新增收益" :modal="true" class="w-[450px]">
      <div class="flex flex-col gap-3">
        <div>
          <label class="block text-sm mb-1">相关持仓</label>
          <Dropdown v-model="form.position_id" :options="positions" optionLabel="security_name" optionValue="id" class="w-full" showClear />
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-sm mb-1">收益类型 *</label>
            <Dropdown v-model="form.income_type" :options="INCOME_TYPES" optionLabel="label" optionValue="value" class="w-full" />
          </div>
          <div><label class="block text-sm mb-1">日期 *</label><InputText v-model="form.income_date" class="w-full" placeholder="YYYY-MM-DD" /></div>
        </div>
        <div><label class="block text-sm mb-1">金额 *</label><InputNumber v-model="form.amount" class="w-full" /></div>
        <div><label class="block text-sm mb-1">备注</label><Textarea v-model="form.notes" rows="2" class="w-full" /></div>
      </div>
      <template #footer>
        <Button label="取消" text @click="showDialog = false" />
        <Button label="保存" :loading="saving" @click="handleSave" />
      </template>
    </Dialog>
  </div>
</template>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/InvestmentIncome.vue
git commit --no-gpg-sign -m "feat: add InvestmentIncome page with CRUD"
```

---

### Task 12: Create InvestmentReports.vue page

**Files:**
- Create: `frontend/src/views/InvestmentReports.vue`

- [ ] **Step 1: Create the investment reports page**

Write `frontend/src/views/InvestmentReports.vue`:

```vue
<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dropdown from 'primevue/dropdown'
import InputText from 'primevue/inputtext'
import Card from 'primevue/card'
import Tag from 'primevue/tag'
import { getPositionsReport, getIncomeReport, getFairValueReport } from '@/api'

const activeReport = ref<'positions' | 'income' | 'fair_value'>('positions')
const typeFilter = ref<string | null>(null)
const startDate = ref('')
const endDate = ref('')
const loading = ref(false)
const positionsData = ref<any[]>([])
const incomeData = ref<any>({ items: [], summary_by_type: [], total: 0 })
const fairValueData = ref<any>({ items: [], total_change: 0 })
const companyId = computed(() => parseInt(localStorage.getItem('companyId') || '1'))

const INVEST_TYPES = [
  { label: '全部类型', value: null },
  { label: 'VC', value: 'vc' },
  { label: 'PE', value: 'pe' },
  { label: '一般股权', value: 'general_equity' },
  { label: '二级市场', value: 'secondary_market' },
  { label: '另类资产', value: 'alternative' },
]

async function loadPositions() {
  loading.value = true
  try {
    const res = await getPositionsReport(companyId.value, typeFilter.value || undefined)
    positionsData.value = res.data
  } finally { loading.value = false }
}

async function loadIncome() {
  loading.value = true
  try {
    const res = await getIncomeReport(companyId.value, startDate.value || undefined, endDate.value || undefined)
    incomeData.value = res.data
  } finally { loading.value = false }
}

async function loadFairValue() {
  loading.value = true
  try {
    const res = await getFairValueReport(companyId.value, startDate.value || undefined, endDate.value || undefined)
    fairValueData.value = res.data
  } finally { loading.value = false }
}

function switchReport(r: 'positions' | 'income' | 'fair_value') {
  activeReport.value = r
  if (r === 'positions') loadPositions()
  else if (r === 'income') loadIncome()
  else loadFairValue()
}

onMounted(() => loadPositions())
</script>

<template>
  <div>
    <div class="flex gap-2 mb-4">
      <Button :label="'持仓报告'" :outlined="activeReport !== 'positions'" @click="switchReport('positions')" size="small" />
      <Button :label="'收益报告'" :outlined="activeReport !== 'income'" @click="switchReport('income')" size="small" />
      <Button :label="'公允价值变动'" :outlined="activeReport !== 'fair_value'" @click="switchReport('fair_value')" size="small" />
    </div>

    <!-- Positions Report -->
    <div v-if="activeReport === 'positions'">
      <div class="flex gap-2 items-center mb-3">
        <Dropdown v-model="typeFilter" :options="INVEST_TYPES" optionLabel="label" optionValue="value"
                  class="w-40" @change="loadPositions" />
        <Button label="刷新" icon="pi pi-refresh" text size="small" @click="loadPositions" />
      </div>

      <DataTable :value="positionsData" :loading="loading" stripedRows size="small">
        <Column field="portfolio_name" header="组合" sortable />
        <Column field="investment_type" header="类型" sortable style="width:80px">
          <template #body="{ data }">
            <Tag :value="data.investment_type" />
          </template>
        </Column>
        <Column field="security_name" header="标的" sortable />
        <Column field="account_code" header="科目" sortable style="width:80px" />
        <Column field="cost_amount" header="成本" sortable style="width:120px">
          <template #body="{ data }">{{ data.cost_amount.toLocaleString() }}</template>
        </Column>
        <Column field="fair_value" header="公允价值" sortable style="width:120px">
          <template #body="{ data }">{{ data.fair_value.toLocaleString() }}</template>
        </Column>
        <Column header="未实现损益" sortable style="width:140px">
          <template #body="{ data }">
            <div class="flex items-center gap-1">
              <span :class="data.unrealized_gl >= 0 ? 'text-green-600' : 'text-red-600'">
                {{ data.unrealized_gl.toLocaleString() }}
              </span>
              <span class="text-xs" :class="data.unrealized_gl_pct >= 0 ? 'text-green-500' : 'text-red-500'">
                ({{ data.unrealized_gl_pct }}%)
              </span>
            </div>
          </template>
        </Column>
        <Column field="fair_value_date" header="估值日" sortable style="width:100px" />
      </DataTable>
    </div>

    <!-- Income Report -->
    <div v-if="activeReport === 'income'">
      <div class="flex gap-2 items-center mb-3">
        <InputText v-model="startDate" placeholder="开始日期 YYYY-MM-DD" class="w-40" />
        <InputText v-model="endDate" placeholder="结束日期" class="w-40" />
        <Button label="查询" icon="pi pi-search" size="small" @click="loadIncome" />
      </div>

      <div class="grid grid-cols-4 gap-3 mb-3">
        <Card v-for="s in incomeData.summary_by_type" :key="s.income_type">
          <template #content>
            <div class="text-center">
              <div class="text-xs text-zinc-500">{{ s.income_type }}</div>
              <div class="text-lg font-semibold">{{ s.amount.toLocaleString() }}</div>
            </div>
          </template>
        </Card>
        <Card>
          <template #content>
            <div class="text-center">
              <div class="text-xs text-zinc-500">合计</div>
              <div class="text-lg font-semibold" :class="incomeData.total >= 0 ? 'text-green-600' : 'text-red-600'">
                {{ incomeData.total.toLocaleString() }}
              </div>
            </div>
          </template>
        </Card>
      </div>

      <DataTable :value="incomeData.items" :loading="loading" stripedRows size="small">
        <Column field="income_date" header="日期" sortable style="width:100px" />
        <Column field="income_type" header="类型" sortable style="width:120px" />
        <Column field="amount" header="金额" sortable style="width:120px">
          <template #body="{ data }">{{ data.amount.toLocaleString() }}</template>
        </Column>
        <Column field="notes" header="备注" />
      </DataTable>
    </div>

    <!-- Fair Value Report -->
    <div v-if="activeReport === 'fair_value'">
      <div class="flex gap-2 items-center mb-3">
        <InputText v-model="startDate" placeholder="开始日期" class="w-40" />
        <InputText v-model="endDate" placeholder="结束日期" class="w-40" />
        <Button label="查询" icon="pi pi-search" size="small" @click="loadFairValue" />
        <span class="ml-auto text-sm">
          总变动:
          <span :class="fairValueData.total_change >= 0 ? 'text-green-600' : 'text-red-600'" class="font-semibold">
            {{ fairValueData.total_change.toLocaleString() }}
          </span>
        </span>
      </div>

      <DataTable :value="fairValueData.items" :loading="loading" stripedRows size="small">
        <Column field="adjustment_date" header="日期" sortable style="width:100px" />
        <Column field="previous_value" header="调整前" sortable style="width:120px">
          <template #body="{ data }">{{ data.previous_value.toLocaleString() }}</template>
        </Column>
        <Column field="adjusted_value" header="调整后" sortable style="width:120px">
          <template #body="{ data }">{{ data.adjusted_value.toLocaleString() }}</template>
        </Column>
        <Column field="change_amount" header="变动额" sortable style="width:120px">
          <template #body="{ data }">
            <span :class="data.change_amount >= 0 ? 'text-green-600' : 'text-red-600'">
              {{ data.change_amount.toLocaleString() }}
            </span>
          </template>
        </Column>
        <Column field="reason" header="原因" />
      </DataTable>
    </div>
  </div>
</template>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/InvestmentReports.vue
git commit --no-gpg-sign -m "feat: add InvestmentReports page with 3 report views"
```

---

### Task 13: End-to-end verification

**Files:** None (verification only)

- [ ] **Step 1: Start backend and verify API**

```bash
cd backend && uv run uvicorn app.main:app --reload --port 8000 &
sleep 3
# Test endpoints
curl -s http://localhost:8000/api/health | python -m json.tool
curl -s -H "Authorization: Bearer $(curl -s -X POST http://localhost:8000/api/auth/login -H 'Content-Type: application/json' -d '{"username":"admin","password":"admin123","company_id":1,"period":"2026-05"}' | python -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')" "http://localhost:8000/api/investments/portfolios?company_id=1" | python -m json.tool
curl -s -H "Authorization: Bearer $(...)" "http://localhost:8000/api/investments/mappings" | python -m json.tool
```

Expected: Health OK, portfolios returns [], mappings returns 8 rows.

- [ ] **Step 2: Start frontend and verify pages load**

```bash
cd frontend && npm run dev &
sleep 5
# Open http://localhost:5173/finance/login in browser
# Login with admin/admin123
# Navigate to 投资管理 → 投资组合总览
# Verify all 5 pages render without errors
```

Expected: All pages load, CRUD operations work, auto-voucher ID shown after transaction creation.

- [ ] **Step 3: Verify auto-voucher in existing voucher list**

Navigate to `/finance/vouchers` and confirm that investment-generated vouchers appear in the list with correct debit/credit entries.

- [ ] **Step 4: Final commit if any fixes**

```bash
git status
# If any fixes were made, commit them
git add -A
git commit --no-gpg-sign -m "chore: final fixes from end-to-end verification"
```
```

---

*Plan complete. 13 tasks covering models, schemas, router, seed data, API functions, router/menu updates, and 5 Vue pages.*
