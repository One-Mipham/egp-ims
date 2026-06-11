# General Ledger (总账) Module Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the 6-feature General Ledger module with 2 new models, 1 router (16 endpoints), and 6 Vue components.

**Architecture:** New `gl.py` router under `/api/gl` prefix, 2 new models in models.py, schemas in schemas/__init__.py. Frontend uses 6 new components under `views/gl/`. Navigation integration redirects 3 overlapping routes to existing pages.

**Tech Stack:** FastAPI / SQLAlchemy / Pydantic (backend), Vue 3 / PrimeVue / Tailwind CSS (frontend)

---

## Task 1: Add AutoTransferTemplate and CustomQuery Models

**Files:**
- Modify: `backend/app/models.py` — append 2 models after line 1756

- [ ] **Step 1: Add models at end of models.py**

Append after the CarryForwardEntry class (line 1756):

```python

class AutoTransferTemplate(Base):
    """自动转账模板"""
    __tablename__ = "auto_transfer_templates"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    template_type = Column(String(20), nullable=False, default="fixed",
                           comment="fixed/ratio/balance")
    frequency = Column(String(20), nullable=False, default="manual",
                       comment="manual/monthly/quarterly/yearly")
    is_active = Column(Boolean, default=True)
    entries = Column(JSON, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("Company")


class CustomQuery(Base):
    """保存的自定义查询"""
    __tablename__ = "custom_queries"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    name = Column(String(100), nullable=False)
    query_type = Column(String(20), nullable=False,
                        comment="subject/aux/detail")
    filters = Column(JSON, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("Company")
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/models.py
git commit -m "feat: add AutoTransferTemplate and CustomQuery models for GL module"
```

---

## Task 2: Add GL Pydantic Schemas

**Files:**
- Modify: `backend/app/schemas/__init__.py` — append schemas after line 1293

- [ ] **Step 1: Add schemas at end of schemas/__init__.py**

Append after YearlyPeriodStatus (line 1293):

```python

# ── General Ledger (总账) Schemas ──


class AutoTransferEntrySchema(BaseModel):
    """自动转账模板分录"""
    account_code: str
    direction: str  # debit/credit
    formula: str
    summary: str = ""


class AutoTransferTemplateCreate(BaseModel):
    """创建自动转账模板"""
    company_id: int
    name: str
    description: Optional[str] = None
    template_type: str = "fixed"  # fixed/ratio/balance
    frequency: str = "manual"  # manual/monthly/quarterly/yearly
    is_active: bool = True
    entries: list[AutoTransferEntrySchema]


class AutoTransferTemplateUpdate(BaseModel):
    """更新自动转账模板"""
    name: Optional[str] = None
    description: Optional[str] = None
    template_type: Optional[str] = None
    frequency: Optional[str] = None
    is_active: Optional[bool] = None
    entries: Optional[list[AutoTransferEntrySchema]] = None


class AutoTransferTemplateResponse(BaseModel):
    """自动转账模板响应"""
    id: int
    company_id: int
    name: str
    description: Optional[str] = None
    template_type: str
    frequency: str
    is_active: bool
    entries: list[AutoTransferEntrySchema]
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class SubjectLedgerEntry(BaseModel):
    """科目账明细行"""
    date: str
    voucher_no: str
    summary: str
    debit: float
    credit: float
    balance: float


class SubjectLedgerResponse(BaseModel):
    """科目账查询响应"""
    account_code: str
    account_name: str
    beginning_balance: float
    direction: str
    entries: list[SubjectLedgerEntry]
    total_debit: float
    total_credit: float
    ending_balance: float


class AuxLedgerEntry(BaseModel):
    """辅助账明细行"""
    date: str
    voucher_no: str
    account_code: str
    account_name: str
    summary: str
    aux_name: str = ""
    debit: float
    credit: float
    balance: float


class AuxLedgerResponse(BaseModel):
    """辅助账查询响应"""
    aux_type: str
    aux_id: int
    aux_name: str
    beginning_balance: float
    direction: str
    entries: list[AuxLedgerEntry]
    total_debit: float
    total_credit: float
    ending_balance: float


class CustomQueryCreate(BaseModel):
    """保存自定义查询"""
    company_id: int
    name: str
    query_type: str  # subject/aux/detail
    filters: dict


class CustomQueryUpdate(BaseModel):
    """更新自定义查询"""
    name: Optional[str] = None
    filters: Optional[dict] = None


class CustomQueryResponse(BaseModel):
    """自定义查询响应"""
    id: int
    company_id: int
    name: str
    query_type: str
    filters: dict
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class CustomDetailColumn(BaseModel):
    """自定义明细表可用列"""
    field: str
    header: str


class CustomDetailQueryRequest(BaseModel):
    """自定义明细表查询请求"""
    columns: list[str] = []
    filters: dict = {}
    order_by: list[str] = []
    query_id: Optional[int] = None


class TransactionBalanceRow(BaseModel):
    """往来余额行"""
    counterparty_id: int
    counterparty_name: str
    beginning_balance: float
    direction: str
    current_debit: float
    current_credit: float
    ending_balance: float


class TransactionDetailEntry(BaseModel):
    """往来明细行"""
    date: str
    voucher_no: str
    account_code: str
    account_name: str
    summary: str
    debit: float
    credit: float
    balance: float


class TransactionDetailResponse(BaseModel):
    """往来单位明细响应"""
    counterparty_id: int
    counterparty_name: str
    beginning_balance: float
    direction: str
    entries: list[TransactionDetailEntry]
    total_debit: float
    total_credit: float
    ending_balance: float


class AgingBucket(BaseModel):
    """账龄区间"""
    range: str  # "0-30天"/"31-90天"/...
    amount: float


class AgingRow(BaseModel):
    """账龄分析行"""
    counterparty_id: int
    counterparty_name: str
    total_balance: float
    buckets: list[AgingBucket]
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/schemas/__init__.py
git commit -m "feat: add GL module Pydantic schemas"
```

---

## Task 3: Create GL Router — Auto-Transfer Endpoints

**Files:**
- Create: `backend/app/routers/gl.py`

- [ ] **Step 1: Create the router file with imports and auto-transfer CRUD**

```python
"""总账模块路由：自动转账、科目账、辅助账、自定义账、自定义明细表、往来管理。"""
from datetime import datetime, timezone, date
from io import StringIO
import csv

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import (
    User, Company, Account, Voucher, VoucherEntry,
    AccountingPeriod, Counterparty, Department, Person, Project,
    AutoTransferTemplate, CustomQuery,
)
from app.schemas import (
    AutoTransferTemplateCreate, AutoTransferTemplateUpdate,
    AutoTransferTemplateResponse,
    SubjectLedgerResponse, SubjectLedgerEntry,
    AuxLedgerResponse, AuxLedgerEntry,
    CustomQueryCreate, CustomQueryUpdate, CustomQueryResponse,
    CustomDetailColumn, CustomDetailQueryRequest,
    TransactionBalanceRow, TransactionDetailResponse,
    TransactionDetailEntry, AgingRow, AgingBucket,
)
from app.auth import get_current_user

router = APIRouter()


def _get_company(db: Session, company_id: int) -> Company:
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="公司不存在")
    return company


# ── 自动转账模板 ──


@router.get("/auto-transfer-templates", response_model=list[AutoTransferTemplateResponse])
def list_auto_transfer_templates(
    company_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return (
        db.query(AutoTransferTemplate)
        .filter(AutoTransferTemplate.company_id == company_id)
        .order_by(AutoTransferTemplate.created_at.desc())
        .all()
    )


@router.post("/auto-transfer-templates", response_model=AutoTransferTemplateResponse)
def create_auto_transfer_template(
    data: AutoTransferTemplateCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    obj = AutoTransferTemplate(
        company_id=data.company_id,
        name=data.name,
        description=data.description,
        template_type=data.template_type,
        frequency=data.frequency,
        is_active=data.is_active,
        entries=[e.model_dump() for e in data.entries],
        created_by=user.id,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.put("/auto-transfer-templates/{template_id}", response_model=AutoTransferTemplateResponse)
def update_auto_transfer_template(
    template_id: int,
    data: AutoTransferTemplateUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    obj = db.query(AutoTransferTemplate).filter(AutoTransferTemplate.id == template_id).first()
    if not obj:
        raise HTTPException(404, "模板不存在")
    if data.name is not None:
        obj.name = data.name
    if data.description is not None:
        obj.description = data.description
    if data.template_type is not None:
        obj.template_type = data.template_type
    if data.frequency is not None:
        obj.frequency = data.frequency
    if data.is_active is not None:
        obj.is_active = data.is_active
    if data.entries is not None:
        obj.entries = [e.model_dump() for e in data.entries]
    obj.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/auto-transfer-templates/{template_id}")
def delete_auto_transfer_template(
    template_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    obj = db.query(AutoTransferTemplate).filter(AutoTransferTemplate.id == template_id).first()
    if not obj:
        raise HTTPException(404, "模板不存在")
    db.delete(obj)
    db.commit()
    return {"detail": "已删除"}


@router.post("/auto-transfer-templates/{template_id}/execute")
def execute_auto_transfer(
    template_id: int,
    company_id: int,
    period: str = Query(..., description="执行期间 yyyy-MM"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """执行自动转账，生成凭证。"""
    template = db.query(AutoTransferTemplate).filter(
        AutoTransferTemplate.id == template_id,
        AutoTransferTemplate.company_id == company_id,
    ).first()
    if not template:
        raise HTTPException(404, "模板不存在")
    if not template.is_active:
        raise HTTPException(400, "模板已停用")
    if not template.entries:
        raise HTTPException(400, "模板没有分录定义")

    # Get all accounts for balance lookups
    account_codes_needed = [e["account_code"] for e in template.entries]
    accounts_map = {
        a.code: a
        for a in db.query(Account).filter(
            Account.company_id == company_id,
            Account.code.in_(account_codes_needed),
        ).all()
    }

    # Calculate amounts per entry
    voucher_entries = []
    for entry_def in template.entries:
        code = entry_def["account_code"]
        direction = entry_def["direction"]
        formula = entry_def["formula"]
        summary = entry_def.get("summary", "")

        # Calculate amount based on formula
        if template.template_type == "fixed":
            amount = float(formula)
        elif template.template_type == "ratio":
            # formula like "50%", calculate from account balance
            account = accounts_map.get(code)
            if not account:
                raise HTTPException(400, f"科目 {code} 不存在")
            balance = _get_account_balance(db, company_id, code, period)
            pct = float(formula.rstrip("%")) / 100.0
            amount = round(balance * pct, 2)
        elif template.template_type == "balance":
            # Take the full balance
            account = accounts_map.get(code)
            if not account:
                raise HTTPException(400, f"科目 {code} 不存在")
            amount = _get_account_balance(db, company_id, code, period)
        else:
            raise HTTPException(400, f"不支持的模板类型: {template.template_type}")

        if amount == 0:
            continue

        if direction == "debit":
            voucher_entries.append({
                "account_code": code,
                "debit": amount,
                "credit": 0,
                "description": summary,
            })
        else:
            voucher_entries.append({
                "account_code": code,
                "debit": 0,
                "credit": amount,
                "description": summary,
            })

    if not voucher_entries:
        raise HTTPException(400, "所有分录金额为零，无法生成凭证")

    # Create voucher
    voucher_no = f"转-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    voucher = Voucher(
        company_id=company_id,
        date=f"{period}-01",
        voucher_no=voucher_no,
        voucher_type="transfer",
        summary=template.name,
        creator_id=user.id,
        status="draft",
    )
    db.add(voucher)
    db.flush()

    # Create entries
    total_debit = sum(e["debit"] for e in voucher_entries)
    total_credit = sum(e["credit"] for e in voucher_entries)
    # Auto-balance: add rounding difference to the last entry
    if total_debit != total_credit:
        diff = round(total_debit - total_credit, 2)
        if voucher_entries[-1]["debit"] > 0:
            voucher_entries[-1]["debit"] = round(voucher_entries[-1]["debit"] - diff, 2)
        else:
            voucher_entries[-1]["credit"] = round(voucher_entries[-1]["credit"] + diff, 2)

    for entry_data in voucher_entries:
        db.add(VoucherEntry(
            voucher_id=voucher.id,
            account_code=entry_data["account_code"],
            debit=entry_data["debit"],
            credit=entry_data["credit"],
            description=entry_data.get("description", ""),
        ))

    db.commit()
    db.refresh(voucher)
    return {"ok": True, "voucher_id": voucher.id, "voucher_no": voucher_no}


def _get_account_balance(db: Session, company_id: int, account_code: str, period: str) -> float:
    """Get current balance for an account up to given period."""
    entries = (
        db.query(VoucherEntry)
        .join(Voucher, VoucherEntry.voucher_id == Voucher.id)
        .filter(
            Voucher.company_id == company_id,
            VoucherEntry.account_code == account_code,
            Voucher.date <= f"{period}-31",
            Voucher.status.in_(["posted", "closed"]),
        )
        .all()
    )
    total_debit = sum(e.debit for e in entries)
    total_credit = sum(e.credit for e in entries)

    account = db.query(Account).filter(
        Account.company_id == company_id, Account.code == account_code
    ).first()
    if account and account.balance_direction == "debit":
        return account.initial_balance + total_debit - total_credit
    else:
        return 0  # For revenue/expense accounts, balance depends on period
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/routers/gl.py
git commit -m "feat: add GL router auto-transfer endpoints (CRUD + execute)"
```

---

## Task 4: Add Subject Ledger & Aux Ledger Endpoints to GL Router

**Files:**
- Modify: `backend/app/routers/gl.py` — append after auto-transfer endpoints

- [ ] **Step 1: Append subject ledger and aux ledger endpoints**

Append to `gl.py`:

```python

# ── 科目账 ──


@router.get("/subject-ledger", response_model=list[SubjectLedgerResponse])
def get_subject_ledger(
    company_id: int,
    start_period: str = Query(..., description="起始期间 yyyy-MM"),
    end_period: str = Query(..., description="截止期间 yyyy-MM"),
    account_code: str = Query(None, description="科目代码，支持模糊"),
    level: int = Query(None, description="科目级别过滤"),
    include_zero: bool = Query(False, description="包含无发生额科目"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """多科目汇总查询（总账）。"""
    query = db.query(Account).filter(Account.company_id == company_id, Account.is_active == True)
    if account_code:
        query = query.filter(Account.code.like(f"{account_code}%"))
    if level:
        query = query.filter(Account.level == level)

    accounts = query.order_by(Account.code).all()
    result = []
    for account in accounts:
        ledger = _build_ledger_for_account(db, company_id, account, start_period, end_period)
        if not include_zero and ledger.total_debit == 0 and ledger.total_credit == 0:
            continue
        result.append(ledger)
    return result


@router.get("/subject-ledger/{code}", response_model=SubjectLedgerResponse)
def get_single_subject_ledger(
    code: str,
    company_id: int,
    start_period: str = Query(...),
    end_period: str = Query(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """单科目明细查询（明细账）。"""
    account = db.query(Account).filter(
        Account.company_id == company_id, Account.code == code
    ).first()
    if not account:
        raise HTTPException(404, "科目不存在")
    return _build_ledger_for_account(db, company_id, account, start_period, end_period)


def _build_ledger_for_account(
    db: Session, company_id: int, account: Account,
    start_period: str, end_period: str,
) -> SubjectLedgerResponse:
    """构建单科目账数据。"""
    # Beginning balance: sum up to start_period
    beg_entries = (
        db.query(VoucherEntry)
        .join(Voucher, VoucherEntry.voucher_id == Voucher.id)
        .filter(
            Voucher.company_id == company_id,
            VoucherEntry.account_code == account.code,
            Voucher.date < f"{start_period}-01",
            Voucher.status.in_(["posted", "closed"]),
        )
        .all()
    )
    beg_debit = sum(e.debit for e in beg_entries)
    beg_credit = sum(e.credit for e in beg_entries)
    if account.balance_direction == "debit":
        beginning_balance = account.initial_balance + beg_debit - beg_credit
    else:
        beginning_balance = account.initial_balance + beg_credit - beg_debit

    # Current period entries
    period_entries = (
        db.query(VoucherEntry)
        .join(Voucher, VoucherEntry.voucher_id == Voucher.id)
        .filter(
            Voucher.company_id == company_id,
            VoucherEntry.account_code == account.code,
            Voucher.date >= f"{start_period}-01",
            Voucher.date <= f"{end_period}-31",
            Voucher.status.in_(["posted", "closed"]),
        )
        .order_by(Voucher.date, Voucher.voucher_no)
        .all()
    )

    running_balance = beginning_balance
    entries = []
    for e in period_entries:
        if account.balance_direction == "debit":
            running_balance = running_balance + e.debit - e.credit
        else:
            running_balance = running_balance + e.credit - e.debit
        entries.append(SubjectLedgerEntry(
            date=e.voucher.date,
            voucher_no=e.voucher.voucher_no,
            summary=e.voucher.summary,
            debit=e.debit,
            credit=e.credit,
            balance=round(running_balance, 2),
        ))

    total_debit = sum(e.debit for e in period_entries)
    total_credit = sum(e.credit for e in period_entries)

    if account.balance_direction == "debit":
        ending_balance = beginning_balance + total_debit - total_credit
    else:
        ending_balance = beginning_balance + total_credit - total_debit

    return SubjectLedgerResponse(
        account_code=account.code,
        account_name=account.name,
        beginning_balance=round(beginning_balance, 2),
        direction=account.balance_direction,
        entries=entries,
        total_debit=round(total_debit, 2),
        total_credit=round(total_credit, 2),
        ending_balance=round(ending_balance, 2),
    )


# ── 辅助账 ──


@router.get("/aux-ledger", response_model=AuxLedgerResponse)
def get_aux_ledger(
    company_id: int,
    aux_type: str = Query(..., description="department/person/counterparty/project"),
    aux_id: int = Query(...),
    start_period: str = Query(...),
    end_period: str = Query(...),
    account_code: str = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """辅助维度明细查询。"""
    if aux_type not in ("department", "person", "counterparty", "project"):
        raise HTTPException(400, "aux_type 必须是 department/person/counterparty/project")

    # Get aux object name
    aux_name = ""
    if aux_type == "department":
        obj = db.query(Department).filter(Department.id == aux_id).first()
    elif aux_type == "person":
        obj = db.query(Person).filter(Person.id == aux_id).first()
    elif aux_type == "counterparty":
        obj = db.query(Counterparty).filter(Counterparty.id == aux_id).first()
    elif aux_type == "project":
        obj = db.query(Project).filter(Project.id == aux_id).first()
    aux_name = obj.name if obj else "未知"

    # Filter column
    filter_col = {
        "department": VoucherEntry.department_id,
        "person": VoucherEntry.person_id,
        "counterparty": VoucherEntry.counterparty_id,
        "project": VoucherEntry.project_id,
    }[aux_type]

    # Beginning balance
    beg_query = (
        db.query(VoucherEntry)
        .join(Voucher, VoucherEntry.voucher_id == Voucher.id)
        .filter(
            Voucher.company_id == company_id,
            filter_col == aux_id,
            Voucher.date < f"{start_period}-01",
            Voucher.status.in_(["posted", "closed"]),
        )
    )
    if account_code:
        beg_query = beg_query.filter(VoucherEntry.account_code.like(f"{account_code}%"))
    beg_entries = beg_query.all()
    beg_debit = sum(e.debit for e in beg_entries)
    beg_credit = sum(e.credit for e in beg_entries)
    beginning_balance = beg_debit - beg_credit

    # Current period entries
    cur_query = (
        db.query(VoucherEntry)
        .join(Voucher, VoucherEntry.voucher_id == Voucher.id)
        .filter(
            Voucher.company_id == company_id,
            filter_col == aux_id,
            Voucher.date >= f"{start_period}-01",
            Voucher.date <= f"{end_period}-31",
            Voucher.status.in_(["posted", "closed"]),
        )
    )
    if account_code:
        cur_query = cur_query.filter(VoucherEntry.account_code.like(f"{account_code}%"))
    cur_entries = cur_query.order_by(Voucher.date, Voucher.voucher_no).all()

    # Get account names
    account_codes = list(set(e.account_code for e in cur_entries))
    account_map = {
        a.code: a.name
        for a in db.query(Account).filter(
            Account.company_id == company_id,
            Account.code.in_(account_codes),
        ).all()
    }

    running_balance = beginning_balance
    entries = []
    for e in cur_entries:
        running_balance = running_balance + e.debit - e.credit
        entries.append(AuxLedgerEntry(
            date=e.voucher.date,
            voucher_no=e.voucher.voucher_no,
            account_code=e.account_code,
            account_name=account_map.get(e.account_code, ""),
            summary=e.voucher.summary,
            aux_name=aux_name,
            debit=e.debit,
            credit=e.credit,
            balance=round(running_balance, 2),
        ))

    total_debit = sum(e.debit for e in cur_entries)
    total_credit = sum(e.credit for e in cur_entries)
    ending_balance = beginning_balance + total_debit - total_credit

    return AuxLedgerResponse(
        aux_type=aux_type,
        aux_id=aux_id,
        aux_name=aux_name,
        beginning_balance=round(beginning_balance, 2),
        direction="debit",
        entries=entries,
        total_debit=round(total_debit, 2),
        total_credit=round(total_credit, 2),
        ending_balance=round(ending_balance, 2),
    )
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/routers/gl.py
git commit -m "feat: add subject ledger and aux ledger endpoints to GL router"
```

---

## Task 5: Add Custom Query, Custom Detail, and Transaction Endpoints to GL Router

**Files:**
- Modify: `backend/app/routers/gl.py` — append after aux ledger endpoints

- [ ] **Step 1: Append remaining endpoints**

Append to `gl.py`:

```python

# ── 自定义查询 ──


@router.get("/custom-queries", response_model=list[CustomQueryResponse])
def list_custom_queries(
    company_id: int,
    query_type: str = Query(None, description="subject/aux/detail"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(CustomQuery).filter(CustomQuery.company_id == company_id)
    if query_type:
        q = q.filter(CustomQuery.query_type == query_type)
    return q.order_by(CustomQuery.updated_at.desc()).all()


@router.post("/custom-queries", response_model=CustomQueryResponse)
def create_custom_query(
    data: CustomQueryCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    obj = CustomQuery(
        company_id=data.company_id,
        name=data.name,
        query_type=data.query_type,
        filters=data.filters,
        created_by=user.id,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.put("/custom-queries/{query_id}", response_model=CustomQueryResponse)
def update_custom_query(
    query_id: int,
    data: CustomQueryUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    obj = db.query(CustomQuery).filter(CustomQuery.id == query_id).first()
    if not obj:
        raise HTTPException(404, "查询不存在")
    if data.name is not None:
        obj.name = data.name
    if data.filters is not None:
        obj.filters = data.filters
    obj.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/custom-queries/{query_id}")
def delete_custom_query(
    query_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    obj = db.query(CustomQuery).filter(CustomQuery.id == query_id).first()
    if not obj:
        raise HTTPException(404, "查询不存在")
    db.delete(obj)
    db.commit()
    return {"detail": "已删除"}


@router.get("/custom-queries/{query_id}/execute")
def execute_custom_query(
    query_id: int,
    company_id: int,
    start_period: str = Query(...),
    end_period: str = Query(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """执行保存的查询，返回结果。"""
    obj = db.query(CustomQuery).filter(CustomQuery.id == query_id).first()
    if not obj:
        raise HTTPException(404, "查询不存在")

    filters = obj.filters
    filters.setdefault("start_period", start_period)
    filters.setdefault("end_period", end_period)

    if obj.query_type == "subject":
        return execute_subject_ledger_query(db, company_id, filters, user)
    elif obj.query_type == "aux":
        return execute_aux_ledger_query(db, company_id, filters, user)
    elif obj.query_type == "detail":
        return execute_custom_detail_query(db, company_id, filters, user)
    else:
        raise HTTPException(400, f"不支持的查询类型: {obj.query_type}")


def execute_subject_ledger_query(db, company_id, filters, user):
    """Execute a saved subject ledger query."""
    account_code = filters.get("account_code")
    level = filters.get("level")
    start_period = filters.get("start_period", "2024-01")
    end_period = filters.get("end_period", "2026-12")
    include_zero = filters.get("include_zero", False)

    query = db.query(Account).filter(Account.company_id == company_id, Account.is_active == True)
    if account_code:
        query = query.filter(Account.code.like(f"{account_code}%"))
    if level:
        query = query.filter(Account.level == level)

    accounts = query.order_by(Account.code).all()
    result = []
    for account in accounts:
        ledger = _build_ledger_for_account(db, company_id, account, start_period, end_period)
        if not include_zero and ledger.total_debit == 0 and ledger.total_credit == 0:
            continue
        result.append(ledger.model_dump())
    return result


def execute_aux_ledger_query(db, company_id, filters, user):
    """Execute a saved aux ledger query. Returns raw dict."""
    aux_type = filters["aux_type"]
    aux_id = filters["aux_id"]
    start_period = filters.get("start_period", "2024-01")
    end_period = filters.get("end_period", "2026-12")
    account_code = filters.get("account_code")

    # Import is at top level, just reuse logic here inline
    filter_col = {
        "department": VoucherEntry.department_id,
        "person": VoucherEntry.person_id,
        "counterparty": VoucherEntry.counterparty_id,
        "project": VoucherEntry.project_id,
    }[aux_type]

    cur_query = (
        db.query(VoucherEntry)
        .join(Voucher, VoucherEntry.voucher_id == Voucher.id)
        .filter(
            Voucher.company_id == company_id,
            filter_col == aux_id,
            Voucher.date >= f"{start_period}-01",
            Voucher.date <= f"{end_period}-31",
            Voucher.status.in_(["posted", "closed"]),
        )
    )
    if account_code:
        cur_query = cur_query.filter(VoucherEntry.account_code.like(f"{account_code}%"))

    entries = cur_query.order_by(Voucher.date, Voucher.voucher_no).all()
    return [
        {
            "date": e.voucher.date,
            "voucher_no": e.voucher.voucher_no,
            "account_code": e.account_code,
            "debit": e.debit,
            "credit": e.credit,
            "summary": e.voucher.summary,
        }
        for e in entries
    ]


# ── 自定义明细表 ──


@router.get("/custom-detail/columns", response_model=list[CustomDetailColumn])
def get_custom_detail_columns(
    user: User = Depends(get_current_user),
):
    """返回自定义明细表可用列。"""
    return [
        CustomDetailColumn(field="date", header="日期"),
        CustomDetailColumn(field="voucher_no", header="凭证号"),
        CustomDetailColumn(field="voucher_type", header="凭证类型"),
        CustomDetailColumn(field="account_code", header="科目代码"),
        CustomDetailColumn(field="account_name", header="科目名称"),
        CustomDetailColumn(field="summary", header="摘要"),
        CustomDetailColumn(field="debit", header="借方金额"),
        CustomDetailColumn(field="credit", header="贷方金额"),
        CustomDetailColumn(field="department_name", header="部门"),
        CustomDetailColumn(field="person_name", header="个人"),
        CustomDetailColumn(field="counterparty_name", header="往来单位"),
        CustomDetailColumn(field="project_name", header="项目"),
    ]


@router.post("/custom-detail/query")
def query_custom_detail(
    company_id: int,
    data: CustomDetailQueryRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """执行自定义明细表查询。"""
    return execute_custom_detail_query(db, company_id, data.filters, user)


def execute_custom_detail_query(db, company_id, filters, user):
    """Execute custom detail query from filters dict."""
    start_date = filters.get("start_date", "2024-01-01")
    end_date = filters.get("end_date", "2026-12-31")
    account_code = filters.get("account_code")

    query = (
        db.query(VoucherEntry)
        .join(Voucher, VoucherEntry.voucher_id == Voucher.id)
        .join(Account, (VoucherEntry.account_code == Account.code) & (Account.company_id == company_id), isouter=True)
        .join(Department, VoucherEntry.department_id == Department.id, isouter=True)
        .join(Person, VoucherEntry.person_id == Person.id, isouter=True)
        .join(Counterparty, VoucherEntry.counterparty_id == Counterparty.id, isouter=True)
        .join(Project, VoucherEntry.project_id == Project.id, isouter=True)
        .filter(
            Voucher.company_id == company_id,
            Voucher.date >= start_date,
            Voucher.date <= end_date,
            Voucher.status.in_(["posted", "closed"]),
        )
    )
    if account_code:
        query = query.filter(VoucherEntry.account_code.like(f"{account_code}%"))

    entries = query.order_by(Voucher.date, Voucher.voucher_no).all()
    return [
        {
            "date": e.voucher.date,
            "voucher_no": e.voucher.voucher_no,
            "voucher_type": e.voucher.voucher_type,
            "account_code": e.account_code,
            "account_name": e.account_name if hasattr(e, 'account_name') else "",
            "summary": e.voucher.summary,
            "debit": e.debit,
            "credit": e.credit,
            "department_name": e.department_name if hasattr(e, 'department_name') else "",
            "person_name": e.person_name if hasattr(e, 'person_name') else "",
            "counterparty_name": e.counterparty_name if hasattr(e, 'counterparty_name') else "",
            "project_name": e.project_name if hasattr(e, 'project_name') else "",
        }
        for e in entries
    ]


@router.get("/custom-detail/export")
def export_custom_detail(
    company_id: int,
    start_date: str = Query(default="2024-01-01"),
    end_date: str = Query(default="2026-12-31"),
    account_code: str = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """导出自定义明细为 CSV。"""
    filters = {
        "start_date": start_date,
        "end_date": end_date,
        "account_code": account_code,
    }
    rows = execute_custom_detail_query(db, company_id, filters, user)

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["日期", "凭证号", "凭证类型", "科目代码", "科目名称", "摘要", "借方金额", "贷方金额", "部门", "个人", "往来单位", "项目"])
    for r in rows:
        writer.writerow([
            r["date"], r["voucher_no"], r.get("voucher_type", ""),
            r["account_code"], r.get("account_name", ""), r["summary"],
            r["debit"], r["credit"],
            r.get("department_name", ""), r.get("person_name", ""),
            r.get("counterparty_name", ""), r.get("project_name", ""),
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=custom_detail.csv"},
    )


# ── 往来管理 ──


@router.get("/transactions/balance", response_model=list[TransactionBalanceRow])
def get_transaction_balances(
    company_id: int,
    start_period: str = Query(...),
    end_period: str = Query(...),
    account_code: str = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """往来单位余额汇总表。"""
    # Get all counterparties with entries in the period
    base_query = (
        db.query(VoucherEntry.counterparty_id)
        .join(Voucher, VoucherEntry.voucher_id == Voucher.id)
        .filter(
            Voucher.company_id == company_id,
            VoucherEntry.counterparty_id.isnot(None),
            Voucher.status.in_(["posted", "closed"]),
        )
        .distinct()
    )
    cp_ids = [r[0] for r in base_query.all()]
    if not cp_ids:
        return []

    counterparties = {
        cp.id: cp
        for cp in db.query(Counterparty).filter(Counterparty.id.in_(cp_ids)).all()
    }

    result = []
    for cp_id in cp_ids:
        cp = counterparties.get(cp_id)
        cp_name = cp.name if cp else "未知"

        # Beginning
        beg = (
            db.query(VoucherEntry)
            .join(Voucher, VoucherEntry.voucher_id == Voucher.id)
            .filter(
                Voucher.company_id == company_id,
                VoucherEntry.counterparty_id == cp_id,
                Voucher.date < f"{start_period}-01",
                Voucher.status.in_(["posted", "closed"]),
            )
        )
        if account_code:
            beg = beg.filter(VoucherEntry.account_code.like(f"{account_code}%"))
        beg_entries = beg.all()
        beg_debit = sum(e.debit for e in beg_entries)
        beg_credit = sum(e.credit for e in beg_entries)
        beginning_balance = beg_debit - beg_credit

        # Current
        cur = (
            db.query(VoucherEntry)
            .join(Voucher, VoucherEntry.voucher_id == Voucher.id)
            .filter(
                Voucher.company_id == company_id,
                VoucherEntry.counterparty_id == cp_id,
                Voucher.date >= f"{start_period}-01",
                Voucher.date <= f"{end_period}-31",
                Voucher.status.in_(["posted", "closed"]),
            )
        )
        if account_code:
            cur = cur.filter(VoucherEntry.account_code.like(f"{account_code}%"))
        cur_entries = cur.all()
        cur_debit = sum(e.debit for e in cur_entries)
        cur_credit = sum(e.credit for e in cur_entries)

        ending_balance = beginning_balance + cur_debit - cur_credit
        direction = "debit" if ending_balance >= 0 else "credit"

        result.append(TransactionBalanceRow(
            counterparty_id=cp_id,
            counterparty_name=cp_name,
            beginning_balance=round(beginning_balance, 2),
            direction=direction,
            current_debit=round(cur_debit, 2),
            current_credit=round(cur_credit, 2),
            ending_balance=round(abs(ending_balance), 2),
        ))

    return sorted(result, key=lambda r: abs(r.ending_balance), reverse=True)


@router.get("/transactions/{counterparty_id}", response_model=TransactionDetailResponse)
def get_transaction_detail(
    counterparty_id: int,
    company_id: int,
    start_period: str = Query(...),
    end_period: str = Query(...),
    account_code: str = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """单个往来单位明细。"""
    cp = db.query(Counterparty).filter(Counterparty.id == counterparty_id).first()
    cp_name = cp.name if cp else "未知"

    # Beginning balance
    beg = (
        db.query(VoucherEntry)
        .join(Voucher, VoucherEntry.voucher_id == Voucher.id)
        .filter(
            Voucher.company_id == company_id,
            VoucherEntry.counterparty_id == counterparty_id,
            Voucher.date < f"{start_period}-01",
            Voucher.status.in_(["posted", "closed"]),
        )
    )
    if account_code:
        beg = beg.filter(VoucherEntry.account_code.like(f"{account_code}%"))
    beg_entries = beg.all()
    beginning_balance = sum(e.debit for e in beg_entries) - sum(e.credit for e in beg_entries)

    # Current period entries
    cur = (
        db.query(VoucherEntry)
        .join(Voucher, VoucherEntry.voucher_id == Voucher.id)
        .filter(
            Voucher.company_id == company_id,
            VoucherEntry.counterparty_id == counterparty_id,
            Voucher.date >= f"{start_period}-01",
            Voucher.date <= f"{end_period}-31",
            Voucher.status.in_(["posted", "closed"]),
        )
    )
    if account_code:
        cur = cur.filter(VoucherEntry.account_code.like(f"{account_code}%"))
    cur_entries = cur.order_by(Voucher.date, Voucher.voucher_no).all()

    # Get account names
    acct_codes = list(set(e.account_code for e in cur_entries))
    acct_map = {
        a.code: a.name
        for a in db.query(Account).filter(
            Account.company_id == company_id,
            Account.code.in_(acct_codes),
        ).all()
    }

    running = beginning_balance
    entries = []
    for e in cur_entries:
        running = running + e.debit - e.credit
        entries.append(TransactionDetailEntry(
            date=e.voucher.date,
            voucher_no=e.voucher.voucher_no,
            account_code=e.account_code,
            account_name=acct_map.get(e.account_code, ""),
            summary=e.voucher.summary,
            debit=e.debit,
            credit=e.credit,
            balance=round(running, 2),
        ))

    total_debit = sum(e.debit for e in cur_entries)
    total_credit = sum(e.credit for e in cur_entries)
    ending = beginning_balance + total_debit - total_credit
    direction = "debit" if ending >= 0 else "credit"

    return TransactionDetailResponse(
        counterparty_id=counterparty_id,
        counterparty_name=cp_name,
        beginning_balance=round(beginning_balance, 2),
        direction=direction,
        entries=entries,
        total_debit=round(total_debit, 2),
        total_credit=round(total_credit, 2),
        ending_balance=round(abs(ending_balance), 2),
    )


@router.get("/transactions/aging", response_model=list[AgingRow])
def get_transaction_aging(
    company_id: int,
    end_period: str = Query(...),
    account_code: str = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """往来账龄分析。"""
    cp_ids = [
        r[0] for r in
        db.query(VoucherEntry.counterparty_id)
        .join(Voucher, VoucherEntry.voucher_id == Voucher.id)
        .filter(
            Voucher.company_id == company_id,
            VoucherEntry.counterparty_id.isnot(None),
            Voucher.status.in_(["posted", "closed"]),
        )
        .distinct()
        .all()
    ]
    if not cp_ids:
        return []

    counterparties = {
        cp.id: cp
        for cp in db.query(Counterparty).filter(Counterparty.id.in_(cp_ids)).all()
    }

    # Reference date: end of end_period
    ref_date_str = f"{end_period}-31"
    ref_date = date.fromisoformat(ref_date_str)

    buckets_def = [
        ("0-30天", 0, 30),
        ("31-90天", 31, 90),
        ("91-180天", 91, 180),
        ("181-365天", 181, 365),
        ("365天+", 366, 99999),
    ]

    result = []
    for cp_id in cp_ids:
        cp = counterparties.get(cp_id)
        cp_name = cp.name if cp else "未知"

        entries_query = (
            db.query(VoucherEntry)
            .join(Voucher, VoucherEntry.voucher_id == Voucher.id)
            .filter(
                Voucher.company_id == company_id,
                VoucherEntry.counterparty_id == cp_id,
                Voucher.date <= ref_date_str,
                Voucher.status.in_(["posted", "closed"]),
            )
        )
        if account_code:
            entries_query = entries_query.filter(VoucherEntry.account_code.like(f"{account_code}%"))
        entries = entries_query.all()

        buckets = []
        total_balance = 0
        for label, min_days, max_days in buckets_def:
            amount = 0.0
            for e in entries:
                e_date = date.fromisoformat(e.voucher.date)
                days = (ref_date - e_date).days
                if min_days <= days <= max_days:
                    amount += e.debit - e.credit
            buckets.append(AgingBucket(range=label, amount=round(amount, 2)))
            total_balance += amount

        result.append(AgingRow(
            counterparty_id=cp_id,
            counterparty_name=cp_name,
            total_balance=round(total_balance, 2),
            buckets=buckets,
        ))

    return sorted(result, key=lambda r: abs(r.total_balance), reverse=True)
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/routers/gl.py
git commit -m "feat: add custom query, custom detail, and transaction endpoints to GL router"
```

---

## Task 6: Register GL Router in Main.py

**Files:**
- Modify: `backend/app/main.py` — add import and router registration

- [ ] **Step 1: Add import and register router**

Add `gl` to the routers import (line 6) and add the router registration:

```python
# In the import line (line 6), add 	gl,
from app.routers import auth, users, companies, departments, accounts, vouchers, templates, periods, reports, audit, prints, permissions, cockpit, counterparties, persons, projects, investments, init_data, hr, fixed_assets, receivables, payables, inventory_trade, admin, servers, kb, expenses, contracts, bids, budget, board, taxes, gl

# After the taxes router line (after line 49), add:
app.include_router(gl.router, prefix="/api/gl", tags=["总账"])
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/main.py
git commit -m "feat: register /api/gl router in main.py"
```

---

## Task 7: Update Frontend Routes

**Files:**
- Modify: `frontend/src/router/index.ts` — replace 11 placeholder routes

- [ ] **Step 1: Replace GL placeholder routes with real routes**

Replace lines 9-19 (the 11 placeholder routes):

```typescript
  // 总账模块
  { path: '/finance/gl/journal', redirect: '/finance/vouchers' },
  { path: '/finance/gl/journal-reverse', redirect: '/finance/vouchers' },
  { path: '/finance/gl/voucher-review', redirect: '/finance/vouchers' },
  { path: '/finance/gl/auto-transfer', component: () => import('../views/gl/AutoTransfer.vue'), meta: { requiresAuth: true, pageTitle: '自动转账' } },
  { path: '/finance/gl/subject-ledger', component: () => import('../views/gl/SubjectLedger.vue'), meta: { requiresAuth: true, pageTitle: '科目账' } },
  { path: '/finance/gl/aux-ledger', component: () => import('../views/gl/AuxLedger.vue'), meta: { requiresAuth: true, pageTitle: '辅助账' } },
  { path: '/finance/gl/custom-ledger', component: () => import('../views/gl/CustomLedger.vue'), meta: { requiresAuth: true, pageTitle: '自定义账' } },
  { path: '/finance/gl/custom-detail', component: () => import('../views/gl/CustomDetail.vue'), meta: { requiresAuth: true, pageTitle: '自定义明细表' } },
  { path: '/finance/gl/transactions', component: () => import('../views/gl/Transactions.vue'), meta: { requiresAuth: true, pageTitle: '往来管理' } },
  { path: '/finance/gl/cashflow', redirect: '/finance/reports' },
  { path: '/finance/gl/print-books', redirect: '/finance/print' },
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/router/index.ts
git commit -m "feat: update GL routes — 4 redirects + 6 new component routes"
```

---

## Task 8: Update Menu Config

**Files:**
- Modify: `frontend/src/config/menuConfig.ts` — simplify GL menu

- [ ] **Step 1: Replace GL menu section (lines 252-266)**

Replace with:

```typescript
        label: '11.2 总账',
        icon: 'pi pi-file-edit',
        children: [
          { label: '凭证', to: '/finance/vouchers' },
          { label: '自动转账', to: '/finance/gl/auto-transfer' },
          { label: '科目账', to: '/finance/gl/subject-ledger' },
          { label: '辅助账', to: '/finance/gl/aux-ledger' },
          { label: '自定义账', to: '/finance/gl/custom-ledger' },
          { label: '自定义明细表', to: '/finance/gl/custom-detail' },
          { label: '往来管理', to: '/finance/gl/transactions' },
          { label: '现金流量', to: '/finance/reports' },
          { label: '账簿打印', to: '/finance/print' },
          { label: '初始化导航', to: '/finance/init' },
        ],
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/config/menuConfig.ts
git commit -m "feat: simplify GL menu — remove duplicate items, add new routes"
```

---

## Task 9: Add GL API Functions

**Files:**
- Modify: `frontend/src/api/index.ts` — append GL API functions

- [ ] **Step 1: Append GL API functions to api/index.ts**

Append after the last export:

```typescript

// ═══════════ 总账模块 ═══════════

// Auto-transfer templates
export const listAutoTransferTemplates = (companyId: number) =>
  api.get('/gl/auto-transfer-templates', { params: { company_id: companyId } })
export const createAutoTransferTemplate = (data: any) =>
  api.post('/gl/auto-transfer-templates', data)
export const updateAutoTransferTemplate = (id: number, data: any) =>
  api.put(`/gl/auto-transfer-templates/${id}`, data)
export const deleteAutoTransferTemplate = (id: number) =>
  api.delete(`/gl/auto-transfer-templates/${id}`)
export const executeAutoTransfer = (id: number, companyId: number, period: string) =>
  api.post(`/gl/auto-transfer-templates/${id}/execute`, null, { params: { company_id: companyId, period } })

// Subject ledger
export const getSubjectLedger = (companyId: number, start_period: string, end_period: string, params?: { account_code?: string; level?: number; include_zero?: boolean }) =>
  api.get('/gl/subject-ledger', { params: { company_id: companyId, start_period, end_period, ...params } })
export const getSingleSubjectLedger = (companyId: number, code: string, start_period: string, end_period: string) =>
  api.get(`/gl/subject-ledger/${code}`, { params: { company_id: companyId, start_period, end_period } })

// Aux ledger
export const getAuxLedger = (companyId: number, aux_type: string, aux_id: number, start_period: string, end_period: string, account_code?: string) =>
  api.get('/gl/aux-ledger', { params: { company_id: companyId, aux_type, aux_id, start_period, end_period, ...(account_code ? { account_code } : {}) } })

// Custom queries
export const listCustomQueries = (companyId: number, query_type?: string) =>
  api.get('/gl/custom-queries', { params: { company_id: companyId, ...(query_type ? { query_type } : {}) } })
export const createCustomQuery = (data: any) =>
  api.post('/gl/custom-queries', data)
export const updateCustomQuery = (id: number, data: any) =>
  api.put(`/gl/custom-queries/${id}`, data)
export const deleteCustomQuery = (id: number) =>
  api.delete(`/gl/custom-queries/${id}`)
export const executeCustomQuery = (id: number, companyId: number, start_period: string, end_period: string) =>
  api.get(`/gl/custom-queries/${id}/execute`, { params: { company_id: companyId, start_period, end_period } })

// Custom detail
export const getCustomDetailColumns = () =>
  api.get('/gl/custom-detail/columns')
export const queryCustomDetail = (companyId: number, data: any) =>
  api.post('/gl/custom-detail/query', data, { params: { company_id: companyId } })
export const exportCustomDetail = (companyId: number, start_date: string, end_date: string, account_code?: string) =>
  api.get('/gl/custom-detail/export', { params: { company_id: companyId, start_date, end_date, ...(account_code ? { account_code } : {}) }, responseType: 'blob' })

// Transactions
export const getTransactionBalances = (companyId: number, start_period: string, end_period: string, account_code?: string) =>
  api.get('/gl/transactions/balance', { params: { company_id: companyId, start_period, end_period, ...(account_code ? { account_code } : {}) } })
export const getTransactionDetail = (companyId: number, counterpartyId: number, start_period: string, end_period: string, account_code?: string) =>
  api.get(`/gl/transactions/${counterpartyId}`, { params: { company_id: companyId, start_period, end_period, ...(account_code ? { account_code } : {}) } })
export const getTransactionAging = (companyId: number, end_period: string, account_code?: string) =>
  api.get('/gl/transactions/aging', { params: { company_id: companyId, end_period, ...(account_code ? { account_code } : {}) } })
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/api/index.ts
git commit -m "feat: add GL module API functions"
```

---

## Task 10: Create AutoTransfer Vue Component

**Files:**
- Create: `frontend/src/views/gl/AutoTransfer.vue`

- [ ] **Step 1: Create the directory and component**

```bash
mkdir -p frontend/src/views/gl
```

Then create `frontend/src/views/gl/AutoTransfer.vue`:

```vue
<template>
  <div class="p-4">
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-xl font-bold">自动转账模板</h2>
      <Button label="新建模板" icon="pi pi-plus" @click="openCreate" />
    </div>

    <DataTable :value="templates" stripedRows class="mb-4">
      <Column field="name" header="模板名称" />
      <Column field="template_type" header="类型">
        <template #body="{ data }">
          <Tag :value="typeLabel(data.template_type)" :severity="data.template_type === 'fixed' ? 'info' : data.template_type === 'ratio' ? 'warn' : 'success'" />
        </template>
      </Column>
      <Column field="frequency" header="频率">
        <template #body="{ data }">
          {{ freqLabel(data.frequency) }}
        </template>
      </Column>
      <Column field="entries" header="分录数">
        <template #body="{ data }">
          {{ data.entries?.length || 0 }}
        </template>
      </Column>
      <Column field="is_active" header="启用">
        <template #body="{ data }">
          <i :class="data.is_active ? 'pi pi-check text-green-500' : 'pi pi-times text-gray-400'" />
        </template>
      </Column>
      <Column header="操作" style="width: 16rem">
        <template #body="{ data }">
          <div class="flex gap-2">
            <Button icon="pi pi-play" severity="success" size="small" label="执行" @click="execute(data)" :disabled="!data.is_active" />
            <Button icon="pi pi-pencil" severity="info" size="small" @click="openEdit(data)" />
            <Button icon="pi pi-trash" severity="danger" size="small" @click="confirmDelete(data)" />
          </div>
        </template>
      </Column>
    </DataTable>

    <!-- Create/Edit Dialog -->
    <Dialog v-model:visible="dialogVisible" :header="isEditing ? '编辑模板' : '新建模板'" :modal="true" :style="{ width: '700px' }">
      <div class="flex flex-col gap-3">
        <div class="flex gap-3">
          <div class="flex-1">
            <label class="block text-sm mb-1">模板名称</label>
            <InputText v-model="form.name" class="w-full" />
          </div>
          <div>
            <label class="block text-sm mb-1">频率</label>
            <Dropdown v-model="form.frequency" :options="frequencyOptions" optionLabel="label" optionValue="value" />
          </div>
        </div>
        <div>
          <label class="block text-sm mb-1">类型</label>
          <div class="flex gap-2">
            <SelectButton v-model="form.template_type" :options="typeOptions" optionLabel="label" optionValue="value" />
          </div>
        </div>
        <div>
          <label class="block text-sm mb-1">说明</label>
          <Textarea v-model="form.description" rows="2" class="w-full" />
        </div>
        <div>
          <div class="flex justify-between items-center mb-2">
            <label class="text-sm font-medium">分录定义</label>
            <Button icon="pi pi-plus" size="small" severity="secondary" label="添加分录" @click="addEntry" />
          </div>
          <DataTable :value="form.entries" size="small">
            <Column header="科目代码" style="width: 8rem">
              <template #body="{ data, index }">
                <InputText v-model="data.account_code" size="small" class="w-full" />
              </template>
            </Column>
            <Column header="方向" style="width: 5rem">
              <template #body="{ data, index }">
                <Dropdown v-model="data.direction" :options="['debit','credit']" size="small">
                  <template #value="slotProps">
                    {{ slotProps.value === 'debit' ? '借' : '贷' }}
                  </template>
                  <template #option="slotProps">
                    {{ slotProps.option === 'debit' ? '借方' : '贷方' }}
                  </template>
                </Dropdown>
              </template>
            </Column>
            <Column header="公式" style="width: 7rem">
              <template #body="{ data, index }">
                <InputText v-model="data.formula" size="small" class="w-full" :placeholder="form.template_type === 'fixed' ? '金额' : '百分比/余额'" />
              </template>
            </Column>
            <Column header="摘要">
              <template #body="{ data, index }">
                <InputText v-model="data.summary" size="small" class="w-full" />
              </template>
            </Column>
            <Column header="" style="width: 3rem">
              <template #body="{ index }">
                <Button icon="pi pi-times" severity="danger" size="small" text rounded @click="removeEntry(index)" />
              </template>
            </Column>
          </DataTable>
        </div>
        <div class="flex items-center gap-2">
          <Checkbox v-model="form.is_active" :binary="true" inputId="is_active" />
          <label for="is_active">启用</label>
        </div>
      </div>
      <template #footer>
        <Button label="取消" severity="secondary" @click="dialogVisible = false" />
        <Button label="保存" @click="save" />
      </template>
    </Dialog>

    <!-- Execute Dialog -->
    <Dialog v-model:visible="execDialogVisible" header="执行自动转账" :modal="true" :style="{ width: '400px' }">
      <div class="flex flex-col gap-3">
        <p>执行模板: <strong>{{ execTarget?.name }}</strong></p>
        <div>
          <label class="block text-sm mb-1">执行期间</label>
          <InputText v-model="execPeriod" placeholder="yyyy-MM" />
        </div>
      </div>
      <template #footer>
        <Button label="取消" severity="secondary" @click="execDialogVisible = false" />
        <Button label="执行" severity="success" @click="confirmExecute" />
      </template>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useToast } from 'primevue/usetoast'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Dropdown from 'primevue/dropdown'
import SelectButton from 'primevue/selectbutton'
import Checkbox from 'primevue/checkbox'
import Tag from 'primevue/tag'
import {
  listAutoTransferTemplates,
  createAutoTransferTemplate,
  updateAutoTransferTemplate,
  deleteAutoTransferTemplate,
  executeAutoTransfer,
} from '../../api'

const toast = useToast()

const companyId = Number(localStorage.getItem('company_id') || '1')

const templates = ref<any[]>([])
const dialogVisible = ref(false)
const isEditing = ref(false)
const editingId = ref<number | null>(null)
const execDialogVisible = ref(false)
const execTarget = ref<any>(null)
const execPeriod = ref('')

const frequencyOptions = [
  { label: '手动', value: 'manual' },
  { label: '每月', value: 'monthly' },
  { label: '每季', value: 'quarterly' },
  { label: '每年', value: 'yearly' },
]

const typeOptions = [
  { label: '固定金额', value: 'fixed' },
  { label: '按比例', value: 'ratio' },
  { label: '余额结转', value: 'balance' },
]

const defaultEntry = { account_code: '', direction: 'credit', formula: '', summary: '' }

const form = ref({
  company_id: companyId,
  name: '',
  description: '',
  template_type: 'fixed',
  frequency: 'manual',
  is_active: true,
  entries: [{ ...defaultEntry }] as any[],
})

function typeLabel(t: string) {
  const m: Record<string, string> = { fixed: '固定金额', ratio: '按比例', balance: '余额结转' }
  return m[t] || t
}

function freqLabel(f: string) {
  const m: Record<string, string> = { manual: '手动', monthly: '每月', quarterly: '每季', yearly: '每年' }
  return m[f] || f
}

async function load() {
  const { data } = await listAutoTransferTemplates(companyId)
  templates.value = data
}

function openCreate() {
  isEditing.value = false
  editingId.value = null
  form.value = {
    company_id: companyId,
    name: '',
    description: '',
    template_type: 'fixed',
    frequency: 'manual',
    is_active: true,
    entries: [{ ...defaultEntry }],
  }
  dialogVisible.value = true
}

function openEdit(t: any) {
  isEditing.value = true
  editingId.value = t.id
  form.value = {
    company_id: companyId,
    name: t.name,
    description: t.description || '',
    template_type: t.template_type,
    frequency: t.frequency,
    is_active: t.is_active,
    entries: (t.entries || []).map((e: any) => ({ ...e })),
  }
  dialogVisible.value = true
}

function addEntry() {
  form.value.entries.push({ ...defaultEntry })
}

function removeEntry(index: number) {
  form.value.entries.splice(index, 1)
}

async function save() {
  try {
    if (isEditing.value && editingId.value) {
      await updateAutoTransferTemplate(editingId.value, {
        name: form.value.name,
        description: form.value.description,
        template_type: form.value.template_type,
        frequency: form.value.frequency,
        is_active: form.value.is_active,
        entries: form.value.entries,
      })
      toast.add({ severity: 'success', summary: '已更新', life: 3000 })
    } else {
      await createAutoTransferTemplate({
        company_id: companyId,
        name: form.value.name,
        description: form.value.description,
        template_type: form.value.template_type,
        frequency: form.value.frequency,
        is_active: form.value.is_active,
        entries: form.value.entries,
      })
      toast.add({ severity: 'success', summary: '已创建', life: 3000 })
    }
    dialogVisible.value = false
    await load()
  } catch (err: any) {
    toast.add({ severity: 'error', summary: '保存失败', detail: err.response?.data?.detail || '', life: 5000 })
  }
}

async function confirmDelete(t: any) {
  if (!confirm(`确定删除模板 "${t.name}" 吗？`)) return
  await deleteAutoTransferTemplate(t.id)
  toast.add({ severity: 'success', summary: '已删除', life: 3000 })
  await load()
}

function execute(t: any) {
  execTarget.value = t
  execPeriod.value = new Date().toISOString().slice(0, 7)
  execDialogVisible.value = true
}

async function confirmExecute() {
  if (!execTarget.value) return
  try {
    const { data } = await executeAutoTransfer(execTarget.value.id, companyId, execPeriod.value)
    toast.add({ severity: 'success', summary: '转账已执行', detail: `凭证号: ${data.voucher_no}`, life: 5000 })
    execDialogVisible.value = false
  } catch (err: any) {
    toast.add({ severity: 'error', summary: '执行失败', detail: err.response?.data?.detail || '', life: 5000 })
  }
}

onMounted(load)
</script>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/gl/AutoTransfer.vue
git commit -m "feat: add AutoTransfer Vue component - template CRUD + execute"
```

---

## Task 11: Create SubjectLedger Vue Component

**Files:**
- Create: `frontend/src/views/gl/SubjectLedger.vue`

- [ ] **Step 1: Create the component**

```vue
<template>
  <div class="p-4">
    <h2 class="text-xl font-bold mb-4">科目账</h2>

    <!-- Filters -->
    <div class="flex gap-3 items-end mb-4 flex-wrap">
      <div>
        <label class="block text-sm mb-1">科目代码</label>
        <InputText v-model="filters.account_code" placeholder="如 1001 或 660" />
      </div>
      <div>
        <label class="block text-sm mb-1">级别</label>
        <Dropdown v-model="filters.level" :options="[null,1,2,3,4]" optionLabel="label" class="w-24">
          <template #value="slotProps">
            {{ slotProps.value ? slotProps.value + '级' : '全部' }}
          </template>
          <template #option="slotProps">
            {{ slotProps.option ? slotProps.option + '级' : '全部' }}
          </template>
        </Dropdown>
      </div>
      <div>
        <label class="block text-sm mb-1">起始期间</label>
        <InputText v-model="filters.start_period" placeholder="yyyy-MM" />
      </div>
      <div>
        <label class="block text-sm mb-1">截止期间</label>
        <InputText v-model="filters.end_period" placeholder="yyyy-MM" />
      </div>
      <div class="flex items-center gap-2">
        <Checkbox v-model="filters.include_zero" :binary="true" inputId="include_zero" />
        <label for="include_zero">含无发生额</label>
      </div>
      <Button label="查询" icon="pi pi-search" @click="search" />
    </div>

    <!-- Results -->
    <Accordion :activeIndex="activeIndex" v-if="results.length">
      <AccordionTab v-for="(item, i) in results" :key="i">
        <template #header>
          <div class="flex justify-between w-full pr-4">
            <span><strong>{{ item.account_code }}</strong> {{ item.account_name }}</span>
            <span class="text-sm">期初: {{ item.beginning_balance.toLocaleString() }} | 借: {{ item.total_debit.toLocaleString() }} | 贷: {{ item.total_credit.toLocaleString() }} | 期末: {{ item.ending_balance.toLocaleString() }}</span>
          </div>
        </template>
        <DataTable :value="item.entries" size="small" stripedRows>
          <Column field="date" header="日期" style="width:7rem" />
          <Column field="voucher_no" header="凭证号" style="width:7rem" />
          <Column field="summary" header="摘要" />
          <Column field="debit" header="借方" style="width:8rem">
            <template #body="{ data }">{{ data.debit ? data.debit.toLocaleString() : '' }}</template>
          </Column>
          <Column field="credit" header="贷方" style="width:8rem">
            <template #body="{ data }">{{ data.credit ? data.credit.toLocaleString() : '' }}</template>
          </Column>
          <Column field="balance" header="余额" style="width:8rem">
            <template #body="{ data }">{{ data.balance.toLocaleString() }}</template>
          </Column>
        </DataTable>
      </AccordionTab>
    </Accordion>
    <div v-else-if="searched" class="text-center text-gray-400 py-8">无查询结果</div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useToast } from 'primevue/usetoast'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import Button from 'primevue/button'
import Checkbox from 'primevue/checkbox'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Accordion from 'primevue/accordion'
import AccordionTab from 'primevue/accordiontab'
import { getSubjectLedger } from '../../api'

const toast = useToast()
const companyId = Number(localStorage.getItem('company_id') || '1')
const now = new Date()
const defaultPeriod = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`

const filters = ref({
  account_code: '',
  level: null as number | null,
  start_period: defaultPeriod,
  end_period: defaultPeriod,
  include_zero: false,
})

const results = ref<any[]>([])
const searched = ref(false)
const activeIndex = ref<number | null>(null)

async function search() {
  try {
    const { data } = await getSubjectLedger(companyId, filters.value.start_period, filters.value.end_period, {
      account_code: filters.value.account_code || undefined,
      level: filters.value.level || undefined,
      include_zero: filters.value.include_zero,
    })
    results.value = data
    searched.value = true
    activeIndex.value = 0
  } catch (err: any) {
    toast.add({ severity: 'error', summary: '查询失败', detail: err.response?.data?.detail || '', life: 5000 })
  }
}
</script>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/gl/SubjectLedger.vue
git commit -m "feat: add SubjectLedger Vue component - account filter + ledger display"
```

---

## Task 12: Create AuxLedger Vue Component

**Files:**
- Create: `frontend/src/views/gl/AuxLedger.vue`

- [ ] **Step 1: Create the component**

```vue
<template>
  <div class="p-4">
    <h2 class="text-xl font-bold mb-4">辅助账</h2>

    <!-- Filters -->
    <div class="flex gap-3 items-end mb-4 flex-wrap">
      <div>
        <label class="block text-sm mb-1">辅助维度</label>
        <SelectButton v-model="filters.aux_type" :options="auxTypeOptions" optionLabel="label" optionValue="value" />
      </div>
      <div>
        <label class="block text-sm mb-1">{{ auxLabel }}</label>
        <Dropdown v-model="filters.aux_id" :options="auxObjects" optionLabel="name" optionValue="id" :filter="true" placeholder="选择对象" class="w-48" />
      </div>
      <div>
        <label class="block text-sm mb-1">科目代码(可选)</label>
        <InputText v-model="filters.account_code" placeholder="如 660" />
      </div>
      <div>
        <label class="block text-sm mb-1">起始期间</label>
        <InputText v-model="filters.start_period" placeholder="yyyy-MM" />
      </div>
      <div>
        <label class="block text-sm mb-1">截止期间</label>
        <InputText v-model="filters.end_period" placeholder="yyyy-MM" />
      </div>
      <Button label="查询" icon="pi pi-search" @click="search" />
    </div>

    <!-- Results -->
    <div v-if="result">
      <div class="bg-gray-50 p-3 rounded mb-3">
        <strong>{{ result.aux_name }}</strong> | 期初: {{ result.beginning_balance?.toLocaleString() }} | 借方: {{ result.total_debit?.toLocaleString() }} | 贷方: {{ result.total_credit?.toLocaleString() }} | 期末: {{ result.ending_balance?.toLocaleString() }}
      </div>
      <DataTable :value="result.entries" stripedRows>
        <Column field="date" header="日期" style="width:7rem" />
        <Column field="voucher_no" header="凭证号" style="width:7rem" />
        <Column field="account_code" header="科目" style="width:6rem" />
        <Column field="account_name" header="科目名称" style="width:8rem" />
        <Column field="summary" header="摘要" />
        <Column field="debit" header="借方" style="width:8rem">
          <template #body="{ data }">{{ data.debit ? data.debit.toLocaleString() : '' }}</template>
        </Column>
        <Column field="credit" header="贷方" style="width:8rem">
          <template #body="{ data }">{{ data.credit ? data.credit.toLocaleString() : '' }}</template>
        </Column>
        <Column field="balance" header="余额" style="width:8rem">
          <template #body="{ data }">{{ data.balance?.toLocaleString() }}</template>
        </Column>
      </DataTable>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useToast } from 'primevue/usetoast'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import SelectButton from 'primevue/selectbutton'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import { getAuxLedger } from '../../api'
import { listDepartments, listPersons, listCounterparties, listProjects } from '../../api'

const toast = useToast()
const companyId = Number(localStorage.getItem('company_id') || '1')
const now = new Date()
const defaultPeriod = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`

const auxTypeOptions = [
  { label: '部门', value: 'department' },
  { label: '个人', value: 'person' },
  { label: '往来单位', value: 'counterparty' },
  { label: '项目', value: 'project' },
]

const filters = ref({
  aux_type: 'department' as string,
  aux_id: null as number | null,
  account_code: '',
  start_period: defaultPeriod,
  end_period: defaultPeriod,
})

const auxObjects = ref<any[]>([])
const result = ref<any>(null)

const auxLabel = computed(() => {
  const m: Record<string, string> = { department: '部门', person: '个人', counterparty: '往来单位', project: '项目' }
  return m[filters.value.aux_type] || ''
})

async function loadAuxObjects() {
  try {
    const type = filters.value.aux_type
    if (type === 'department') {
      const { data } = await listDepartments(companyId)
      auxObjects.value = data
    } else if (type === 'person') {
      const { data } = await listPersons(companyId)
      auxObjects.value = data
    } else if (type === 'counterparty') {
      const { data } = await listCounterparties(companyId)
      auxObjects.value = data
    } else if (type === 'project') {
      const { data } = await listProjects(companyId)
      auxObjects.value = data
    }
  } catch (err) {
    auxObjects.value = []
  }
}

loadAuxObjects()

async function search() {
  if (!filters.value.aux_id) {
    toast.add({ severity: 'warn', summary: '请选择辅助核算对象', life: 3000 })
    return
  }
  try {
    const { data } = await getAuxLedger(
      companyId, filters.value.aux_type, filters.value.aux_id,
      filters.value.start_period, filters.value.end_period,
      filters.value.account_code || undefined,
    )
    result.value = data
  } catch (err: any) {
    toast.add({ severity: 'error', summary: '查询失败', detail: err.response?.data?.detail || '', life: 5000 })
  }
}
</script>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/gl/AuxLedger.vue
git commit -m "feat: add AuxLedger Vue component - dimension tabs + object filter"
```

---

## Task 13: Create CustomLedger Vue Component

**Files:**
- Create: `frontend/src/views/gl/CustomLedger.vue`

- [ ] **Step 1: Create the component**

```vue
<template>
  <div class="p-4">
    <h2 class="text-xl font-bold mb-4">自定义账</h2>

    <div class="grid grid-cols-3 gap-4">
      <!-- Left: Saved Queries -->
      <div class="col-span-1">
        <div class="flex justify-between items-center mb-2">
          <h3 class="font-semibold">已保存查询</h3>
          <span class="text-xs text-gray-500">({{ queries.length }})</span>
        </div>
        <div class="border rounded p-2 space-y-1" style="min-height: 200px">
          <div v-for="q in queries" :key="q.id"
               class="p-2 rounded cursor-pointer hover:bg-blue-50"
               :class="{ 'bg-blue-100': selectedQuery?.id === q.id }"
               @click="selectQuery(q)">
            <div class="text-sm font-medium">{{ q.name }}</div>
            <div class="text-xs text-gray-500">{{ typeLabel(q.query_type) }}</div>
          </div>
          <div v-if="!queries.length" class="text-center text-gray-400 py-4">暂无保存的查询</div>
        </div>
        <div class="flex gap-2 mt-2">
          <Button label="保存当前" icon="pi pi-save" size="small" @click="openSave" />
          <Button label="删除选中" icon="pi pi-trash" size="small" severity="danger" :disabled="!selectedQuery" @click="confirmDelete" />
        </div>
      </div>

      <!-- Right: Query Builder + Results -->
      <div class="col-span-2">
        <!-- Query Builder -->
        <div class="border rounded p-3 mb-3">
          <div class="flex gap-2 items-end flex-wrap">
            <div>
              <label class="text-xs block mb-1">查询类型</label>
              <Dropdown v-model="queryForm.query_type" :options="queryTypeOptions" optionLabel="label" optionValue="value" class="w-32" />
            </div>
            <div v-if="queryForm.query_type === 'subject'">
              <label class="text-xs block mb-1">科目代码</label>
              <InputText v-model="queryForm.filters.account_code" size="small" placeholder="如 660" class="w-32" />
            </div>
            <div v-if="queryForm.query_type === 'aux'">
              <label class="text-xs block mb-1">维度</label>
              <Dropdown v-model="queryForm.filters.aux_type" :options="auxTypes" optionLabel="label" optionValue="value" size="small" class="w-28" />
            </div>
            <div v-if="queryForm.query_type === 'aux'">
              <label class="text-xs block mb-1">对象ID</label>
              <InputText v-model="queryForm.filters.aux_id" size="small" type="number" class="w-20" />
            </div>
            <div>
              <label class="text-xs block mb-1">起始期间</label>
              <InputText v-model="queryForm.filters.start_period" size="small" placeholder="yyyy-MM" class="w-28" />
            </div>
            <div>
              <label class="text-xs block mb-1">截止期间</label>
              <InputText v-model="queryForm.filters.end_period" size="small" placeholder="yyyy-MM" class="w-28" />
            </div>
            <Button label="执行" icon="pi pi-play" size="small" @click="runQuery" />
          </div>
        </div>

        <!-- Results -->
        <DataTable v-if="results.length" :value="results" stripedRows size="small" class="mb-3">
          <Column v-for="col in resultColumns" :key="col.field" :field="col.field" :header="col.header" />
        </DataTable>
        <div v-else-if="ran" class="text-center text-gray-400 py-4">无结果</div>
      </div>
    </div>

    <!-- Save Dialog -->
    <Dialog v-model:visible="saveVisible" header="保存查询" :modal="true" :style="{ width: '400px' }">
      <div>
        <label class="block text-sm mb-1">查询名称</label>
        <InputText v-model="saveName" class="w-full" />
      </div>
      <template #footer>
        <Button label="取消" severity="secondary" @click="saveVisible = false" />
        <Button label="保存" @click="doSave" />
      </template>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useToast } from 'primevue/usetoast'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import {
  listCustomQueries, createCustomQuery, deleteCustomQuery, executeCustomQuery,
  getSubjectLedger, getAuxLedger,
} from '../../api'

const toast = useToast()
const companyId = Number(localStorage.getItem('company_id') || '1')
const now = new Date()
const defaultPeriod = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`

const queries = ref<any[]>([])
const selectedQuery = ref<any>(null)
const results = ref<any[]>([])
const ran = ref(false)

const queryTypeOptions = [
  { label: '科目账', value: 'subject' },
  { label: '辅助账', value: 'aux' },
  { label: '明细表', value: 'detail' },
]

const auxTypes = [
  { label: '部门', value: 'department' },
  { label: '个人', value: 'person' },
  { label: '往来单位', value: 'counterparty' },
  { label: '项目', value: 'project' },
]

const queryForm = ref({
  query_type: 'subject' as string,
  filters: {
    account_code: '',
    aux_type: 'department',
    aux_id: null as number | null,
    start_period: defaultPeriod,
    end_period: defaultPeriod,
    include_zero: false,
  },
})

const saveVisible = ref(false)
const saveName = ref('')

const resultColumns = computed(() => {
  if (!results.value.length) return []
  return Object.keys(results.value[0]).map(k => ({ field: k, header: k }))
})

function typeLabel(t: string) {
  const m: Record<string, string> = { subject: '科目账', aux: '辅助账', detail: '明细表' }
  return m[t] || t
}

async function loadQueries() {
  const { data } = await listCustomQueries(companyId)
  queries.value = data
}

function selectQuery(q: any) {
  selectedQuery.value = q
  queryForm.value.query_type = q.query_type
  if (q.filters) {
    queryForm.value.filters = { ...queryForm.value.filters, ...q.filters }
  }
  runQuery()
}

async function runQuery() {
  try {
    ran.value = true
    if (selectedQuery.value) {
      const { data } = await executeCustomQuery(
        selectedQuery.value.id, companyId,
        queryForm.value.filters.start_period,
        queryForm.value.filters.end_period,
      )
      results.value = Array.isArray(data) ? data : []
    } else if (queryForm.value.query_type === 'subject') {
      const { data } = await getSubjectLedger(
        companyId,
        queryForm.value.filters.start_period,
        queryForm.value.filters.end_period,
        { account_code: queryForm.value.filters.account_code || undefined },
      )
      results.value = data
    } else if (queryForm.value.query_type === 'aux') {
      if (!queryForm.value.filters.aux_id) {
        toast.add({ severity: 'warn', summary: '请输入对象ID', life: 3000 })
        return
      }
      const { data } = await getAuxLedger(
        companyId,
        queryForm.value.filters.aux_type,
        queryForm.value.filters.aux_id,
        queryForm.value.filters.start_period,
        queryForm.value.filters.end_period,
      )
      results.value = data.entries || []
    }
  } catch (err: any) {
    toast.add({ severity: 'error', summary: '查询失败', detail: err.response?.data?.detail || '', life: 5000 })
  }
}

function openSave() {
  saveName.value = ''
  saveVisible.value = true
}

async function doSave() {
  await createCustomQuery({
    company_id: companyId,
    name: saveName.value,
    query_type: queryForm.value.query_type,
    filters: queryForm.value.filters,
  })
  toast.add({ severity: 'success', summary: '已保存', life: 3000 })
  saveVisible.value = false
  await loadQueries()
}

async function confirmDelete() {
  if (!selectedQuery.value) return
  if (!confirm(`确定删除 "${selectedQuery.value.name}" 吗？`)) return
  await deleteCustomQuery(selectedQuery.value.id)
  toast.add({ severity: 'success', summary: '已删除', life: 3000 })
  selectedQuery.value = null
  await loadQueries()
}

onMounted(loadQueries)
</script>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/gl/CustomLedger.vue
git commit -m "feat: add CustomLedger Vue component - save/load/execute queries"
```

---

## Task 14: Create CustomDetail Vue Component

**Files:**
- Create: `frontend/src/views/gl/CustomDetail.vue`

- [ ] **Step 1: Create the component**

```vue
<template>
  <div class="p-4">
    <h2 class="text-xl font-bold mb-4">自定义明细表</h2>

    <!-- Column picker + Filters -->
    <div class="border rounded p-3 mb-4">
      <div class="flex gap-2 items-end flex-wrap mb-3">
        <div>
          <label class="text-xs block mb-1">起始日期</label>
          <InputText v-model="filters.start_date" size="small" placeholder="yyyy-MM-dd" class="w-32" />
        </div>
        <div>
          <label class="text-xs block mb-1">截止日期</label>
          <InputText v-model="filters.end_date" size="small" placeholder="yyyy-MM-dd" class="w-32" />
        </div>
        <div>
          <label class="text-xs block mb-1">科目代码</label>
          <InputText v-model="filters.account_code" size="small" placeholder="如 660" class="w-28" />
        </div>
        <Button label="查询" icon="pi pi-search" size="small" @click="search" />
        <Button label="导出CSV" icon="pi pi-download" size="small" severity="secondary" @click="exportCsv" />
      </div>
      <div>
        <label class="text-xs block mb-1">选择列</label>
        <div class="flex flex-wrap gap-1">
          <Chip v-for="col in columns" :key="col.field"
                :class="{ 'bg-blue-100': selectedCols.includes(col.field) }"
                :label="col.header"
                class="cursor-pointer"
                @click="toggleCol(col.field)" />
        </div>
      </div>
    </div>

    <!-- Results -->
    <DataTable :value="results" stripedRows size="small" class="mb-4" scrollable scrollHeight="600px">
      <Column v-for="col in visibleCols" :key="col.field" :field="col.field" :header="col.header" style="min-width: 6rem" />
    </DataTable>
    <div class="text-sm text-gray-500">{{ results.length }} 条记录</div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useToast } from 'primevue/usetoast'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import Chip from 'primevue/chip'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import { getCustomDetailColumns, queryCustomDetail, exportCustomDetail } from '../../api'

const toast = useToast()
const companyId = Number(localStorage.getItem('company_id') || '1')
const now = new Date()

const columns = ref<{ field: string; header: string }[]>([])
const selectedCols = ref<string[]>([
  'date', 'voucher_no', 'account_code', 'account_name', 'summary', 'debit', 'credit',
])

const filters = ref({
  start_date: `${now.getFullYear()}-01-01`,
  end_date: `${now.getFullYear()}-12-31`,
  account_code: '',
})

const results = ref<any[]>([])

const visibleCols = computed(() =>
  columns.value.filter(c => selectedCols.value.includes(c.field))
)

function toggleCol(field: string) {
  const idx = selectedCols.value.indexOf(field)
  if (idx >= 0) {
    selectedCols.value.splice(idx, 1)
  } else {
    selectedCols.value.push(field)
  }
}

async function search() {
  try {
    const { data } = await queryCustomDetail(companyId, {
      columns: selectedCols.value,
      filters: filters.value,
      order_by: ['date', 'voucher_no'],
    })
    results.value = data
  } catch (err: any) {
    toast.add({ severity: 'error', summary: '查询失败', detail: err.response?.data?.detail || '', life: 5000 })
  }
}

async function exportCsv() {
  try {
    const res = await exportCustomDetail(
      companyId,
      filters.value.start_date,
      filters.value.end_date,
      filters.value.account_code || undefined,
    )
    const blob = new Blob([res.data], { type: 'text/csv;charset=utf-8' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'custom_detail.csv'
    a.click()
    window.URL.revokeObjectURL(url)
  } catch (err: any) {
    toast.add({ severity: 'error', summary: '导出失败', detail: err.response?.data?.detail || '', life: 5000 })
  }
}

onMounted(async () => {
  const { data } = await getCustomDetailColumns()
  columns.value = data
})
</script>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/gl/CustomDetail.vue
git commit -m "feat: add CustomDetail Vue component - column picker + filter + export"
```

---

## Task 15: Create Transactions Vue Component

**Files:**
- Create: `frontend/src/views/gl/Transactions.vue`

- [ ] **Step 1: Create the component**

```vue
<template>
  <div class="p-4">
    <h2 class="text-xl font-bold mb-4">往来管理</h2>

    <TabView v-model:activeIndex="activeTab">
      <!-- Tab 1: Balance Summary -->
      <TabPanel header="余额汇总">
        <div class="flex gap-2 items-end mb-3">
          <div>
            <label class="text-xs block mb-1">起始期间</label>
            <InputText v-model="filters.start_period" size="small" placeholder="yyyy-MM" class="w-32" />
          </div>
          <div>
            <label class="text-xs block mb-1">截止期间</label>
            <InputText v-model="filters.end_period" size="small" placeholder="yyyy-MM" class="w-32" />
          </div>
          <div>
            <label class="text-xs block mb-1">科目代码</label>
            <InputText v-model="filters.account_code" size="small" placeholder="如 1122" class="w-28" />
          </div>
          <Button label="查询" icon="pi pi-search" size="small" @click="loadBalances" />
        </div>
        <DataTable :value="balances" stripedRows @row-click="drillDown">
          <Column field="counterparty_name" header="往来单位" />
          <Column field="beginning_balance" header="期初余额" style="width:8rem">
            <template #body="{ data }">{{ data.beginning_balance.toLocaleString() }}</template>
          </Column>
          <Column field="current_debit" header="本期借方" style="width:8rem">
            <template #body="{ data }">{{ data.current_debit.toLocaleString() }}</template>
          </Column>
          <Column field="current_credit" header="本期贷方" style="width:8rem">
            <template #body="{ data }">{{ data.current_credit.toLocaleString() }}</template>
          </Column>
          <Column field="ending_balance" header="期末余额" style="width:8rem">
            <template #body="{ data }">
              <span :class="data.direction === 'debit' ? 'text-blue-600' : 'text-red-600'">
                {{ data.direction === 'debit' ? '借' : '贷' }} {{ data.ending_balance.toLocaleString() }}
              </span>
            </template>
          </Column>
        </DataTable>
      </TabPanel>

      <!-- Tab 2: Detail -->
      <TabPanel header="往来明细">
        <div class="flex gap-2 items-end mb-3">
          <div>
            <label class="text-xs block mb-1">往来单位</label>
            <Dropdown v-model="detailFilters.counterparty_id" :options="balanceOptions" optionLabel="counterparty_name" optionValue="counterparty_id" filter placeholder="选择" class="w-48" />
          </div>
          <div>
            <label class="text-xs block mb-1">起始期间</label>
            <InputText v-model="detailFilters.start_period" size="small" class="w-28" />
          </div>
          <div>
            <label class="text-xs block mb-1">截止期间</label>
            <InputText v-model="detailFilters.end_period" size="small" class="w-28" />
          </div>
          <Button label="查询" icon="pi pi-search" size="small" @click="loadDetail" :disabled="!detailFilters.counterparty_id" />
        </div>
        <DataTable v-if="detail" :value="detail.entries" stripedRows size="small">
          <Column field="date" header="日期" style="width:7rem" />
          <Column field="voucher_no" header="凭证号" style="width:7rem" />
          <Column field="account_code" header="科目" style="width:6rem" />
          <Column field="account_name" header="科目名称" style="width:8rem" />
          <Column field="summary" header="摘要" />
          <Column field="debit" header="借方" style="width:8rem">
            <template #body="{ data }">{{ data.debit ? data.debit.toLocaleString() : '' }}</template>
          </Column>
          <Column field="credit" header="贷方" style="width:8rem">
            <template #body="{ data }">{{ data.credit ? data.credit.toLocaleString() : '' }}</template>
          </Column>
          <Column field="balance" header="余额" style="width:8rem">
            <template #body="{ data }">{{ data.balance.toLocaleString() }}</template>
          </Column>
        </DataTable>
      </TabPanel>

      <!-- Tab 3: Aging -->
      <TabPanel header="账龄分析">
        <div class="flex gap-2 items-end mb-3">
          <div>
            <label class="text-xs block mb-1">截止期间</label>
            <InputText v-model="agingFilters.end_period" size="small" class="w-32" />
          </div>
          <Button label="查询" icon="pi pi-search" size="small" @click="loadAging" />
        </div>
        <DataTable :value="aging" stripedRows>
          <Column field="counterparty_name" header="往来单位" />
          <Column field="total_balance" header="总余额" style="width:8rem">
            <template #body="{ data }">{{ data.total_balance.toLocaleString() }}</template>
          </Column>
          <Column v-for="b in agingBuckets" :key="b" :field="'bucket_' + b" :header="b" style="width:7rem">
            <template #body="{ data }">
              {{ data.buckets?.find((x: any) => x.range === b)?.amount?.toLocaleString() || '' }}
            </template>
          </Column>
        </DataTable>
      </TabPanel>
    </TabView>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useToast } from 'primevue/usetoast'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import Dropdown from 'primevue/dropdown'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import TabView from 'primevue/tabview'
import TabPanel from 'primevue/tabpanel'
import { getTransactionBalances, getTransactionDetail, getTransactionAging } from '../../api'

const toast = useToast()
const companyId = Number(localStorage.getItem('company_id') || '1')
const now = new Date()
const defaultPeriod = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`

const activeTab = ref(0)
const agingBuckets = ['0-30天', '31-90天', '91-180天', '181-365天', '365天+']

const filters = ref({
  start_period: defaultPeriod,
  end_period: defaultPeriod,
  account_code: '',
})

const balances = ref<any[]>([])
const detail = ref<any>(null)
const aging = ref<any[]>([])

const detailFilters = ref({
  counterparty_id: null as number | null,
  start_period: defaultPeriod,
  end_period: defaultPeriod,
})

const agingFilters = ref({
  end_period: defaultPeriod,
})

const balanceOptions = computed(() =>
  balances.value.map(b => ({ counterparty_id: b.counterparty_id, counterparty_name: b.counterparty_name }))
)

async function loadBalances() {
  try {
    const { data } = await getTransactionBalances(
      companyId, filters.value.start_period, filters.value.end_period,
      filters.value.account_code || undefined,
    )
    balances.value = data
  } catch (err: any) {
    toast.add({ severity: 'error', summary: '查询失败', detail: err.response?.data?.detail || '', life: 5000 })
  }
}

function drillDown(e: any) {
  detailFilters.value.counterparty_id = e.data.counterparty_id
  activeTab.value = 1
  loadDetail()
}

async function loadDetail() {
  if (!detailFilters.value.counterparty_id) return
  try {
    const { data } = await getTransactionDetail(
      companyId, detailFilters.value.counterparty_id,
      detailFilters.value.start_period, detailFilters.value.end_period,
    )
    detail.value = data
  } catch (err: any) {
    toast.add({ severity: 'error', summary: '查询失败', detail: err.response?.data?.detail || '', life: 5000 })
  }
}

async function loadAging() {
  try {
    const { data } = await getTransactionAging(companyId, agingFilters.value.end_period)
    aging.value = data
  } catch (err: any) {
    toast.add({ severity: 'error', summary: '查询失败', detail: err.response?.data?.detail || '', life: 5000 })
  }
}

loadBalances()
</script>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/gl/Transactions.vue
git commit -m "feat: add Transactions Vue component - balance/detail/aging tabs"
```

---

## Task 16: Verify Backend Starts and Endpoints Respond

**Files:**
- Verify: all backend changes

- [ ] **Step 1: Start backend and test a few endpoints**

```bash
cd backend && uv run uvicorn app.main:app --reload --port 8000 &
sleep 3
# Test health
curl -s http://localhost:8000/api/health | head -1
# Expected: {"status":"ok"}
```

- [ ] **Step 2: Test auto-transfer list endpoint (requires auth)**

First register/login to get a token, then test:

```bash
# This step verifies the router is registered correctly
curl -s "http://localhost:8000/api/gl/auto-transfer-templates?company_id=1" -H "Authorization: Bearer <token>" | head -1
# Expected: [] (empty array) or valid JSON
```

- [ ] **Step 3: Verify frontend compiles**

```bash
cd frontend && npm run build 2>&1 | tail -5
# Expected: no errors
```

- [ ] **Step 4: Commit**

```bash
# No code changes, just verification — skip commit or commit verification notes
```

---

## Task 17: Run Full Integration Verification

**Files:**
- None

- [ ] **Step 1: Start both services and verify menu renders**

```bash
# Start backend
cd backend && uv run uvicorn app.main:app --port 8000 &
# Start frontend
cd frontend && npm run dev -- --port 5173 &
```

- [ ] **Step 2: Manual check**

Open browser to `http://localhost:5173/finance` and navigate to:
1. 总账 → 自动转账 — create a template, execute it
2. 总账 → 科目账 — search with filters
3. 总账 → 辅助账 — select dimension and query
4. 总账 → 自定义账 — save and load a query
5. 总账 → 自定义明细表 — select columns, query, export
6. 总账 → 往来管理 — balance → click drill-down → aging analysis

- [ ] **Step 3: Final commit if needed**

```bash
git status
# Commit any remaining changes
```
