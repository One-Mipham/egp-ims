# 税务管理模块 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现完整税务管理模块——2张表(TaxDeclaration + TaxInvoice)、12个API端点、3个前端参数化组件覆盖18页。

**Architecture:** 统一 TaxDeclaration 模型通过 tax_type 区分 12 种类型(11税种+罚款)；独立 TaxInvoice 模型管理销项/进项发票；前端 3 个参数化 Vue 组件复用 bids 模块已验证模式。

**Tech Stack:** Python 3.12 / FastAPI / SQLAlchemy / Pydantic | Vue 3 / PrimeVue / TypeScript

---

### Task 1: Add TaxDeclaration and TaxInvoice models to models.py

**Files:**
- Modify: `backend/app/models.py` (append at end)

- [ ] **Step 1: Add TaxDeclaration model at end of models.py**

In `backend/app/models.py`, add after the last model class:

```python
class TaxDeclaration(Base):
    """税务申报记录 — 统一承载 11 税种 + 罚款滞纳金，tax_type 区分"""
    __tablename__ = "tax_declarations"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    tax_type = Column(String(30), nullable=False, index=True,
                     comment="vat/urban/education/local_edu/corporate_income/iit/stamp_duty/property_tax/land_use_tax/vehicle_tax/land_vat/penalty")
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    tax_base = Column(Float, nullable=True, comment="税基")
    tax_rate = Column(Float, nullable=True, comment="税率(%)")
    tax_amount = Column(Float, nullable=False, default=0.0)
    paid_amount = Column(Float, nullable=True, default=0.0)
    status = Column(String(20), nullable=False, default="pending",
                    comment="pending/filed/paid")
    declaration_date = Column(DateTime, nullable=True)
    payment_deadline = Column(DateTime, nullable=True)
    payment_date = Column(DateTime, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("Company")


class TaxInvoice(Base):
    """发票管理 — 销项/进项发票"""
    __tablename__ = "tax_invoices"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    invoice_type = Column(String(10), nullable=False, index=True,
                          comment="sales/purchase")
    invoice_number = Column(String(50), nullable=False)
    invoice_date = Column(DateTime, nullable=False)
    counterparty_id = Column(Integer, ForeignKey("counterparties.id"), nullable=True)
    amount = Column(Float, nullable=False, comment="不含税金额")
    tax_rate = Column(Float, nullable=False, comment="税率(%)")
    tax_amount = Column(Float, nullable=False, comment="税额")
    total_amount = Column(Float, nullable=False, comment="价税合计")
    category = Column(String(30), nullable=True, comment="商品/服务类别")
    status = Column(String(20), nullable=False, default="draft",
                    comment="draft/issued/verified")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("Company")
    counterparty = relationship("Counterparty")
```

- [ ] **Step 2: Verify models load without error**

```bash
cd backend && uv run python -c "from app.models import TaxDeclaration, TaxInvoice; print('OK')"
```
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add backend/app/models.py
git commit -m "feat: add TaxDeclaration and TaxInvoice models"
```

---

### Task 2: Add tax Pydantic schemas

**Files:**
- Create: `backend/app/schemas/taxes.py`

- [ ] **Step 1: Create schemas/taxes.py**

```python
"""税务管理 Pydantic Schema."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


TAX_TYPES = [
    "vat", "urban", "education", "local_edu", "corporate_income",
    "iit", "stamp_duty", "property_tax", "land_use_tax",
    "vehicle_tax", "land_vat", "penalty",
]

TAX_TYPE_LABELS = {
    "vat": "增值税", "urban": "城市维护建设税", "education": "教育费附加",
    "local_edu": "地方教育附加", "corporate_income": "企业所得税",
    "iit": "个人所得税代扣代缴", "stamp_duty": "印花税",
    "property_tax": "房产税", "land_use_tax": "土地使用税",
    "vehicle_tax": "车船税", "land_vat": "土地增值税", "penalty": "罚款与滞纳金",
}

DECLARATION_STATUSES = ["pending", "filed", "paid"]
INVOICE_TYPES = ["sales", "purchase"]
INVOICE_STATUSES = ["draft", "issued", "verified"]


# ── TaxDeclaration CRUD ──

class TaxDeclarationCreate(BaseModel):
    company_id: int
    tax_type: str
    period_start: str
    period_end: str
    tax_base: Optional[float] = None
    tax_rate: Optional[float] = None
    tax_amount: float = 0.0
    paid_amount: Optional[float] = None
    status: str = "pending"
    declaration_date: Optional[str] = None
    payment_deadline: Optional[str] = None
    payment_date: Optional[str] = None
    notes: Optional[str] = None


class TaxDeclarationUpdate(BaseModel):
    tax_type: Optional[str] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    tax_base: Optional[float] = None
    tax_rate: Optional[float] = None
    tax_amount: Optional[float] = None
    paid_amount: Optional[float] = None
    status: Optional[str] = None
    declaration_date: Optional[str] = None
    payment_deadline: Optional[str] = None
    payment_date: Optional[str] = None
    notes: Optional[str] = None


class TaxDeclarationResponse(BaseModel):
    id: int
    company_id: int
    tax_type: str
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    tax_base: Optional[float] = None
    tax_rate: Optional[float] = None
    tax_amount: Optional[float] = None
    paid_amount: Optional[float] = None
    status: Optional[str] = None
    declaration_date: Optional[datetime] = None
    payment_deadline: Optional[datetime] = None
    payment_date: Optional[datetime] = None
    created_by: Optional[int] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TaxDeclarationSummary(BaseModel):
    tax_type: str
    label: str
    count: int
    total_tax_amount: float
    total_paid_amount: float
    total_unpaid_amount: float


# ── TaxInvoice CRUD ──

class TaxInvoiceCreate(BaseModel):
    company_id: int
    invoice_type: str
    invoice_number: str
    invoice_date: str
    counterparty_id: Optional[int] = None
    amount: float
    tax_rate: float
    tax_amount: float
    total_amount: float
    category: Optional[str] = None
    status: str = "draft"
    notes: Optional[str] = None


class TaxInvoiceUpdate(BaseModel):
    invoice_type: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    counterparty_id: Optional[int] = None
    amount: Optional[float] = None
    tax_rate: Optional[float] = None
    tax_amount: Optional[float] = None
    total_amount: Optional[float] = None
    category: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class TaxInvoiceResponse(BaseModel):
    id: int
    company_id: int
    invoice_type: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[datetime] = None
    counterparty_id: Optional[int] = None
    amount: Optional[float] = None
    tax_rate: Optional[float] = None
    tax_amount: Optional[float] = None
    total_amount: Optional[float] = None
    category: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TaxInvoiceSummary(BaseModel):
    invoice_type: Optional[str] = None
    month: Optional[str] = None
    count: int
    total_amount: float
    total_tax_amount: float
    total_with_tax: float
```

- [ ] **Step 2: Verify schemas import**

```bash
cd backend && uv run python -c "from app.schemas.taxes import TaxDeclarationCreate, TaxInvoiceCreate; print('OK')"
```
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add backend/app/schemas/taxes.py
git commit -m "feat: add tax management Pydantic schemas"
```

---

### Task 3: Add tax router with 12 endpoints

**Files:**
- Create: `backend/app/routers/taxes.py`

- [ ] **Step 1: Create routers/taxes.py**

```python
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
```

- [ ] **Step 2: Verify router imports**

```bash
cd backend && uv run python -c "from app.routers.taxes import router; print(len(router.routes))"
```
Expected: `12`

- [ ] **Step 3: Commit**

```bash
git add backend/app/routers/taxes.py
git commit -m "feat: add tax management router with 12 endpoints"
```

---

### Task 4: Register router and seed default tax data

**Files:**
- Modify: `backend/app/main.py`
- Modify: `backend/app/seed.py`

- [ ] **Step 1: Register router in main.py**

In `backend/app/main.py`, add the import:

```python
from app.routers import auth, users, companies, departments, accounts, vouchers, templates, periods, reports, audit, prints, permissions, cockpit, counterparties, persons, projects, investments, init_data, hr, fixed_assets, receivables, payables, inventory_trade, admin, servers, kb, expenses, contracts, bids, budget, board, taxes
```

Add router registration after the board router:

```python
app.include_router(taxes.router, prefix="/api/taxes", tags=["税务管理"])
```

- [ ] **Step 2: Verify backend starts**

```bash
cd backend && timeout 5 uv run uvicorn app.main:app --port 8001 2>&1 || true
```
Expected: App starts without import errors

- [ ] **Step 3: Commit**

```bash
git add backend/app/main.py
git commit -m "feat: register tax router at /api/taxes"
```

---

### Task 5: Add frontend taxes API

**Files:**
- Create: `frontend/src/api/taxes.ts`

- [ ] **Step 1: Create api/taxes.ts**

```typescript
import api from './index'

// ── TaxDeclaration CRUD ──

export interface TaxDeclarationParams {
  company_id: number
  tax_type?: string
  status?: string
  period_start?: string
  period_end?: string
}

export const listDeclarations = (params: TaxDeclarationParams) =>
  api.get('/taxes/declarations', { params })

export const getDeclaration = (id: number) =>
  api.get(`/taxes/declarations/${id}`)

export const createDeclaration = (data: Record<string, any>) =>
  api.post('/taxes/declarations', data)

export const updateDeclaration = (id: number, data: Record<string, any>) =>
  api.put(`/taxes/declarations/${id}`, data)

export const deleteDeclaration = (id: number) =>
  api.delete(`/taxes/declarations/${id}`)

export const getDeclarationsSummary = (params: {
  company_id: number
  period_start?: string
  period_end?: string
}) => api.get('/taxes/declarations/summary', { params })


// ── TaxInvoice CRUD ──

export interface TaxInvoiceParams {
  company_id: number
  invoice_type?: string
  status?: string
  counterparty_id?: number
  date_from?: string
  date_to?: string
}

export const listInvoices = (params: TaxInvoiceParams) =>
  api.get('/taxes/invoices', { params })

export const getInvoice = (id: number) =>
  api.get(`/taxes/invoices/${id}`)

export const createInvoice = (data: Record<string, any>) =>
  api.post('/taxes/invoices', data)

export const updateInvoice = (id: number, data: Record<string, any>) =>
  api.put(`/taxes/invoices/${id}`, data)

export const deleteInvoice = (id: number) =>
  api.delete(`/taxes/invoices/${id}`)

export const getInvoicesSummary = (params: {
  company_id: number
  invoice_type?: string
  date_from?: string
  date_to?: string
}) => api.get('/taxes/invoices/summary', { params })
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/api/taxes.ts
git commit -m "feat: add frontend taxes API module"
```

---

### Task 6: Build TaxInvoiceList.vue (covers 3 invoice pages)

**Files:**
- Create: `frontend/src/views/TaxInvoiceList.vue`

- [ ] **Step 1: Create TaxInvoiceList.vue**

The component reads `route.path` to determine mode: `sales`, `purchase`, or `query`. In `query` mode, shows cross-type search.

```vue
<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import Calendar from 'primevue/calendar'
import {
  listInvoices, createInvoice, updateInvoice, deleteInvoice,
  listCounterparties,
} from '@/api'

const route = useRoute()
const companyId = computed(() => parseInt(localStorage.getItem('companyId') || '1'))

const mode = computed(() => {
  const p = route.path
  if (p.includes('/sales')) return 'sales'
  if (p.includes('/purchase')) return 'purchase'
  return 'query'
})

const modeLabel = computed(() => {
  if (mode.value === 'sales') return '销项发票'
  if (mode.value === 'purchase') return '进项发票'
  return '发票查询统计'
})

const items = ref<any[]>([])
const loading = ref(false)
const showDialog = ref(false)
const editingId = ref<number | null>(null)
const search = ref('')
const dateFrom = ref<string | null>(null)
const dateTo = ref<string | null>(null)
const counterparties = ref<any[]>([])

const statusOptions = ['draft', 'issued', 'verified']
const statusLabels: Record<string, string> = { draft: '草稿', issued: '已开票', verified: '已核验' }

const emptyForm = () => ({
  company_id: companyId.value,
  invoice_type: mode.value === 'sales' ? 'sales' : 'purchase',
  invoice_number: '',
  invoice_date: new Date().toISOString().slice(0, 10),
  counterparty_id: null as number | null,
  amount: 0,
  tax_rate: 13,
  tax_amount: 0,
  total_amount: 0,
  category: '',
  status: 'draft',
  notes: '',
})
const form = ref(emptyForm())

watch(() => [form.value.amount, form.value.tax_rate], () => {
  const amt = Number(form.value.amount) || 0
  const rate = Number(form.value.tax_rate) || 0
  form.value.tax_amount = Math.round(amt * rate) / 100
  form.value.total_amount = amt + form.value.tax_amount
})

function getFilters() {
  const params: any = { company_id: companyId.value }
  if (mode.value === 'sales') params.invoice_type = 'sales'
  if (mode.value === 'purchase') params.invoice_type = 'purchase'
  if (dateFrom.value) params.date_from = dateFrom.value
  if (dateTo.value) params.date_to = dateTo.value
  return params
}

async function load() {
  loading.value = true
  try {
    const res = await listInvoices(getFilters())
    items.value = res.data
  } finally { loading.value = false }
}

async function loadCounterparties() {
  try {
    const res = await listCounterparties(companyId.value)
    counterparties.value = res.data
  } catch {}
}

const filteredItems = computed(() => {
  if (!search.value) return items.value
  const q = search.value.toLowerCase()
  return items.value.filter((i: any) =>
    (i.invoice_number || '').toLowerCase().includes(q) ||
    (i.category || '').toLowerCase().includes(q)
  )
})

function openAdd() {
  editingId.value = null
  form.value = emptyForm()
  if (mode.value === 'query') form.value.invoice_type = 'sales'
  loadCounterparties()
  showDialog.value = true
}

function openEdit(row: any) {
  editingId.value = row.id
  form.value = {
    company_id: row.company_id,
    invoice_type: row.invoice_type,
    invoice_number: row.invoice_number,
    invoice_date: row.invoice_date?.slice(0, 10) || '',
    counterparty_id: row.counterparty_id,
    amount: row.amount,
    tax_rate: row.tax_rate,
    tax_amount: row.tax_amount,
    total_amount: row.total_amount,
    category: row.category || '',
    status: row.status,
    notes: row.notes || '',
  }
  loadCounterparties()
  showDialog.value = true
}

async function handleSave() {
  if (!form.value.invoice_number) return
  try {
    if (editingId.value) {
      await updateInvoice(editingId.value, form.value)
    } else {
      await createInvoice(form.value)
    }
    showDialog.value = false
    await load()
  } catch (e: any) {
    alert(e.response?.data?.detail || '保存失败')
  }
}

async function handleDelete(id: number) {
  if (!confirm('确认删除该发票记录？')) return
  try {
    await deleteInvoice(id)
    await load()
  } catch (e: any) {
    alert(e.response?.data?.detail || '删除失败')
  }
}

function getCounterpartyName(id: number | null) {
  if (!id) return ''
  const cp = counterparties.value.find((c: any) => c.id === id)
  return cp?.name || ''
}

onMounted(load)
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-lg font-bold text-zinc-700">{{ modeLabel }}</h2>
      <div class="flex gap-2">
        <InputText v-model="search" placeholder="搜索发票号/类别..." class="w-56" />
        <Calendar v-model="dateFrom" placeholder="起始日期" showIcon class="w-36" @value-change="load" />
        <Calendar v-model="dateTo" placeholder="截止日期" showIcon class="w-36" @value-change="load" />
        <Button label="查询" icon="pi pi-search" severity="secondary" @click="load" />
        <Button v-if="mode !== 'query'" label="新增" icon="pi pi-plus" @click="openAdd" />
      </div>
    </div>

    <div class="bg-white rounded-sm border border-stone-200 overflow-x-auto">
      <DataTable :value="filteredItems" :loading="loading" stripedRows paginator :rows="15" class="shadow-sm">
        <Column header="序号" style="width:60px">
          <template #body="{ index }">{{ index + 1 }}</template>
        </Column>
        <Column field="invoice_number" header="发票号码" style="width:150px" />
        <Column field="invoice_date" header="开票日期" style="width:110px">
          <template #body="{ data }">{{ data.invoice_date?.slice(0, 10) }}</template>
        </Column>
        <Column v-if="mode === 'query'" field="invoice_type" header="类型" style="width:80px">
          <template #body="{ data }">{{ data.invoice_type === 'sales' ? '销项' : '进项' }}</template>
        </Column>
        <Column header="对方单位" style="width:160px">
          <template #body="{ data }">{{ getCounterpartyName(data.counterparty_id) || '-' }}</template>
        </Column>
        <Column field="amount" header="金额（不含税）" style="width:130px">
          <template #body="{ data }">¥{{ Number(data.amount || 0).toLocaleString() }}</template>
        </Column>
        <Column field="tax_rate" header="税率" style="width:70px">
          <template #body="{ data }">{{ data.tax_rate }}%</template>
        </Column>
        <Column field="tax_amount" header="税额" style="width:110px">
          <template #body="{ data }">¥{{ Number(data.tax_amount || 0).toLocaleString() }}</template>
        </Column>
        <Column field="total_amount" header="价税合计" style="width:130px">
          <template #body="{ data }">¥{{ Number(data.total_amount || 0).toLocaleString() }}</template>
        </Column>
        <Column field="category" header="类别" style="width:90px" />
        <Column field="status" header="状态" style="width:80px">
          <template #body="{ data }">{{ statusLabels[data.status] || data.status }}</template>
        </Column>
        <Column header="操作" style="width:130px">
          <template #body="{ data }">
            <Button label="编辑" text severity="info" size="small" @click="openEdit(data)" />
            <Button label="删除" text severity="danger" size="small" @click="handleDelete(data.id)" />
          </template>
        </Column>
      </DataTable>
    </div>

    <Dialog v-model:visible="showDialog" :header="editingId ? '编辑发票' : '新增发票'" :style="{ width: '780px' }">
      <div class="flex flex-col gap-4 py-4">
        <div class="flex gap-4">
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">发票类型</label>
            <Select v-model="form.invoice_type" :options="[
              { label: '销项发票', value: 'sales' },
              { label: '进项发票', value: 'purchase' },
            ]" optionLabel="label" optionValue="value" class="w-full" />
          </div>
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">发票号码 *</label>
            <InputText v-model="form.invoice_number" class="w-full" />
          </div>
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">开票日期</label>
            <Calendar v-model="form.invoice_date" class="w-full" />
          </div>
        </div>
        <div class="flex gap-4">
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">对方单位</label>
            <Select v-model="form.counterparty_id" :options="counterparties"
              optionLabel="name" optionValue="id" showClear filter
              placeholder="选择往来单位" class="w-full" />
          </div>
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">商品/服务类别</label>
            <InputText v-model="form.category" class="w-full" placeholder="如：咨询/软件/货物" />
          </div>
        </div>
        <div class="flex gap-4">
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">金额（不含税）</label>
            <InputText v-model.number="form.amount" type="number" class="w-full" />
          </div>
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">税率（%）</label>
            <InputText v-model.number="form.tax_rate" type="number" class="w-full" />
          </div>
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">税额（自动）</label>
            <InputText :modelValue="form.tax_amount" disabled class="w-full bg-stone-50" />
          </div>
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">价税合计（自动）</label>
            <InputText :modelValue="form.total_amount" disabled class="w-full bg-stone-50" />
          </div>
        </div>
        <div class="flex gap-4">
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">状态</label>
            <Select v-model="form.status" :options="[
              { label: '草稿', value: 'draft' },
              { label: '已开票', value: 'issued' },
              { label: '已核验', value: 'verified' },
            ]" optionLabel="label" optionValue="value" class="w-full" />
          </div>
          <div class="flex-[2]">
            <label class="block text-xs text-zinc-500 mb-1">备注</label>
            <InputText v-model="form.notes" class="w-full" />
          </div>
        </div>
        <div>
          <Button label="保存" icon="pi pi-check" @click="handleSave" />
        </div>
      </div>
    </Dialog>
  </div>
</template>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/TaxInvoiceList.vue
git commit -m "feat: add TaxInvoiceList.vue covering sales/purchase/query modes"
```

---

### Task 7: Build TaxDeclarationList.vue (covers 12 tax type pages)

**Files:**
- Create: `frontend/src/views/TaxDeclarationList.vue`

- [ ] **Step 1: Create TaxDeclarationList.vue**

```vue
<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import Calendar from 'primevue/calendar'
import {
  listDeclarations, createDeclaration, updateDeclaration, deleteDeclaration,
} from '@/api/taxes'

const route = useRoute()
const companyId = computed(() => parseInt(localStorage.getItem('companyId') || '1'))

const taxTypeMap: Record<string, string> = {
  vat: '增值税',
  urban: '城市维护建设税',
  education: '教育费附加',
  local_edu: '地方教育附加',
  corporate_income: '企业所得税',
  iit: '个人所得税代扣代缴',
  stamp_duty: '印花税',
  property_tax: '房产税',
  land_use_tax: '土地使用税',
  vehicle_tax: '车船税',
  land_vat: '土地增值税',
  penalty: '罚款与滞纳金',
}

// Extract taxType from URL path
const taxType = computed(() => {
  const p = route.path
  if (p.includes('/surcharge/urban')) return 'urban'
  if (p.includes('/surcharge/education')) return 'education'
  if (p.includes('/surcharge/local-edu')) return 'local_edu'
  if (p.includes('/corporate-income')) return 'corporate_income'
  if (p.includes('/iit')) return 'iit'
  if (p.includes('/stamp-duty')) return 'stamp_duty'
  if (p.includes('/property-tax')) return 'property_tax'
  if (p.includes('/land-use-tax')) return 'land_use_tax'
  if (p.includes('/vehicle-tax')) return 'vehicle_tax'
  if (p.includes('/land-vat')) return 'land_vat'
  if (p.includes('/penalty')) return 'penalty'
  if (p.includes('/vat')) return 'vat'
  return route.params.taxType as string || 'vat'
})

const pageTitle = computed(() => taxTypeMap[taxType.value] || taxType.value)
const isPenalty = computed(() => taxType.value === 'penalty')

const items = ref<any[]>([])
const loading = ref(false)
const showDialog = ref(false)
const editingId = ref<number | null>(null)
const search = ref('')

const statusOptions = [
  { label: '待申报', value: 'pending' },
  { label: '已申报', value: 'filed' },
  { label: '已缴纳', value: 'paid' },
]

const emptyForm = () => ({
  company_id: companyId.value,
  tax_type: taxType.value,
  period_start: new Date().toISOString().slice(0, 10),
  period_end: new Date().toISOString().slice(0, 10),
  tax_base: null as number | null,
  tax_rate: null as number | null,
  tax_amount: 0,
  paid_amount: 0,
  status: 'pending',
  declaration_date: null as string | null,
  payment_deadline: null as string | null,
  payment_date: null as string | null,
  notes: '',
})
const form = ref(emptyForm())

async function load() {
  loading.value = true
  try {
    const res = await listDeclarations({
      company_id: companyId.value,
      tax_type: taxType.value,
    })
    items.value = res.data
  } finally { loading.value = false }
}

const filteredItems = computed(() => {
  if (!search.value) return items.value
  const q = search.value.toLowerCase()
  return items.value.filter((i: any) =>
    (i.notes || '').toLowerCase().includes(q)
  )
})

function openAdd() {
  editingId.value = null
  form.value = emptyForm()
  showDialog.value = true
}

function openEdit(row: any) {
  editingId.value = row.id
  form.value = {
    company_id: row.company_id,
    tax_type: row.tax_type,
    period_start: row.period_start?.slice(0, 10) || '',
    period_end: row.period_end?.slice(0, 10) || '',
    tax_base: row.tax_base,
    tax_rate: row.tax_rate,
    tax_amount: row.tax_amount || 0,
    paid_amount: row.paid_amount || 0,
    status: row.status,
    declaration_date: row.declaration_date?.slice(0, 10) || null,
    payment_deadline: row.payment_deadline?.slice(0, 10) || null,
    payment_date: row.payment_date?.slice(0, 10) || null,
    notes: row.notes || '',
  }
  showDialog.value = true
}

async function handleSave() {
  if (!form.value.tax_type) return
  try {
    if (editingId.value) {
      await updateDeclaration(editingId.value, form.value)
    } else {
      await createDeclaration(form.value)
    }
    showDialog.value = false
    await load()
  } catch (e: any) {
    alert(e.response?.data?.detail || '保存失败')
  }
}

async function handleDelete(id: number) {
  if (!confirm('确认删除该申报记录？')) return
  try {
    await deleteDeclaration(id)
    await load()
  } catch (e: any) {
    alert(e.response?.data?.detail || '删除失败')
  }
}

onMounted(load)
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-lg font-bold text-zinc-700">{{ pageTitle }}</h2>
      <div class="flex gap-2">
        <InputText v-model="search" placeholder="搜索备注..." class="w-48" />
        <Button label="查询" icon="pi pi-search" severity="secondary" @click="load" />
        <Button label="新增" icon="pi pi-plus" @click="openAdd" />
      </div>
    </div>

    <div class="bg-white rounded-sm border border-stone-200 overflow-x-auto">
      <DataTable :value="filteredItems" :loading="loading" stripedRows paginator :rows="15" class="shadow-sm">
        <Column header="序号" style="width:60px">
          <template #body="{ index }">{{ index + 1 }}</template>
        </Column>
        <Column header="计税期间" style="width:200px">
          <template #body="{ data }">
            {{ data.period_start?.slice(0, 10) || '-' }} ~ {{ data.period_end?.slice(0, 10) || '-' }}
          </template>
        </Column>
        <Column v-if="!isPenalty" field="tax_base" header="税基" style="width:120px">
          <template #body="{ data }">
            {{ data.tax_base != null ? `¥${Number(data.tax_base).toLocaleString()}` : '-' }}
          </template>
        </Column>
        <Column v-if="!isPenalty" field="tax_rate" header="税率" style="width:70px">
          <template #body="{ data }">
            {{ data.tax_rate != null ? `${data.tax_rate}%` : '-' }}
          </template>
        </Column>
        <Column field="tax_amount" header="税额" style="width:120px">
          <template #body="{ data }">¥{{ Number(data.tax_amount || 0).toLocaleString() }}</template>
        </Column>
        <Column field="paid_amount" header="已缴金额" style="width:120px">
          <template #body="{ data }">¥{{ Number(data.paid_amount || 0).toLocaleString() }}</template>
        </Column>
        <Column header="未缴金额" style="width:120px">
          <template #body="{ data }">
            ¥{{ (Number(data.tax_amount || 0) - Number(data.paid_amount || 0)).toLocaleString() }}
          </template>
        </Column>
        <Column field="status" header="状态" style="width:80px">
          <template #body="{ data }">
            <span :class="{
              'text-amber-600': data.status === 'pending',
              'text-blue-600': data.status === 'filed',
              'text-green-600': data.status === 'paid',
            }">
              {{ data.status === 'pending' ? '待申报' : data.status === 'filed' ? '已申报' : '已缴纳' }}
            </span>
          </template>
        </Column>
        <Column header="申报日期" style="width:110px">
          <template #body="{ data }">{{ data.declaration_date?.slice(0, 10) || '-' }}</template>
        </Column>
        <Column header="缴纳日期" style="width:110px">
          <template #body="{ data }">{{ data.payment_date?.slice(0, 10) || '-' }}</template>
        </Column>
        <Column header="操作" style="width:130px">
          <template #body="{ data }">
            <Button label="编辑" text severity="info" size="small" @click="openEdit(data)" />
            <Button label="删除" text severity="danger" size="small" @click="handleDelete(data.id)" />
          </template>
        </Column>
      </DataTable>
    </div>

    <Dialog v-model:visible="showDialog" :header="editingId ? '编辑申报记录' : '新增申报记录'" :style="{ width: '780px' }">
      <div class="flex flex-col gap-4 py-4">
        <div class="flex gap-4">
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">计税期间 *</label>
            <div class="flex gap-2 items-center">
              <Calendar v-model="form.period_start" class="flex-1" placeholder="起" />
              <span class="text-zinc-400">~</span>
              <Calendar v-model="form.period_end" class="flex-1" placeholder="止" />
            </div>
          </div>
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">状态</label>
            <Select v-model="form.status" :options="statusOptions"
              optionLabel="label" optionValue="value" class="w-full" />
          </div>
        </div>
        <div v-if="!isPenalty" class="flex gap-4">
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">税基（计税依据）</label>
            <InputText v-model.number="form.tax_base" type="number" class="w-full" />
          </div>
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">税率（%）</label>
            <InputText v-model.number="form.tax_rate" type="number" class="w-full" />
          </div>
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">税额 *</label>
            <InputText v-model.number="form.tax_amount" type="number" class="w-full" />
          </div>
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">已缴金额</label>
            <InputText v-model.number="form.paid_amount" type="number" class="w-full" />
          </div>
        </div>
        <div v-else class="flex gap-4">
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">罚款金额 *</label>
            <InputText v-model.number="form.tax_amount" type="number" class="w-full" />
          </div>
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">已缴金额</label>
            <InputText v-model.number="form.paid_amount" type="number" class="w-full" />
          </div>
        </div>
        <div class="flex gap-4">
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">申报日期</label>
            <Calendar v-model="form.declaration_date" class="w-full" />
          </div>
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">缴纳截止日</label>
            <Calendar v-model="form.payment_deadline" class="w-full" />
          </div>
          <div class="flex-1">
            <label class="block text-xs text-zinc-500 mb-1">实际缴纳日</label>
            <Calendar v-model="form.payment_date" class="w-full" />
          </div>
        </div>
        <div>
          <label class="block text-xs text-zinc-500 mb-1">备注</label>
          <InputText v-model="form.notes" class="w-full" />
        </div>
        <div>
          <Button label="保存" icon="pi pi-check" @click="handleSave" />
        </div>
      </div>
    </Dialog>
  </div>
</template>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/TaxDeclarationList.vue
git commit -m "feat: add TaxDeclarationList.vue covering 12 tax types with shared component"
```

---

### Task 8: Build TaxReport.vue (covers 3 report pages)

**Files:**
- Create: `frontend/src/views/TaxReport.vue`

- [ ] **Step 1: Create TaxReport.vue**

```vue
<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import Button from 'primevue/button'
import Calendar from 'primevue/calendar'
import { getDeclarationsSummary } from '@/api/taxes'

const route = useRoute()
const companyId = computed(() => parseInt(localStorage.getItem('companyId') || '1'))

const reportType = computed(() => {
  const p = route.path
  if (p.includes('/vat')) return 'vat'
  if (p.includes('/cit')) return 'cit'
  return 'other'
})

const title = computed(() => {
  if (reportType.value === 'vat') return '增值税申报表'
  if (reportType.value === 'cit') return '所得税申报表'
  return '其他税种申报汇总'
})

const summaries = ref<any[]>([])
const loading = ref(false)
const periodStart = ref<string | null>(null)
const periodEnd = ref<string | null>(null)

async function load() {
  loading.value = true
  try {
    const params: any = { company_id: companyId.value }
    if (periodStart.value) params.period_start = periodStart.value
    if (periodEnd.value) params.period_end = periodEnd.value
    const res = await getDeclarationsSummary(params)
    let data = res.data

    if (reportType.value === 'vat') {
      data = data.filter((s: any) => s.tax_type === 'vat')
    } else if (reportType.value === 'cit') {
      data = data.filter((s: any) => s.tax_type === 'corporate_income')
    }

    summaries.value = data
  } finally { loading.value = false }
}

onMounted(load)
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-lg font-bold text-zinc-700">{{ title }}</h2>
      <div class="flex gap-2">
        <Calendar v-model="periodStart" placeholder="期间起" showIcon class="w-36" />
        <Calendar v-model="periodEnd" placeholder="期间止" showIcon class="w-36" />
        <Button label="查询" icon="pi pi-search" severity="secondary" @click="load" />
      </div>
    </div>

    <div class="grid grid-cols-3 gap-4 mb-4" v-if="!loading">
      <div class="bg-white rounded-sm border border-stone-200 p-4">
        <div class="text-sm text-zinc-500 mb-1">本期应缴</div>
        <div class="text-2xl font-bold text-amber-600">
          ¥{{ summaries.reduce((s, i) => s + Number(i.total_tax_amount || 0), 0).toLocaleString() }}
        </div>
      </div>
      <div class="bg-white rounded-sm border border-stone-200 p-4">
        <div class="text-sm text-zinc-500 mb-1">本期已缴</div>
        <div class="text-2xl font-bold text-green-600">
          ¥{{ summaries.reduce((s, i) => s + Number(i.total_paid_amount || 0), 0).toLocaleString() }}
        </div>
      </div>
      <div class="bg-white rounded-sm border border-stone-200 p-4">
        <div class="text-sm text-zinc-500 mb-1">本期未缴</div>
        <div class="text-2xl font-bold text-red-600">
          ¥{{ summaries.reduce((s, i) => s + Number(i.total_unpaid_amount || 0), 0).toLocaleString() }}
        </div>
      </div>
    </div>

    <div class="bg-white rounded-sm border border-stone-200 overflow-x-auto">
      <table class="w-full text-sm">
        <thead class="bg-stone-50 border-b border-stone-200">
          <tr>
            <th class="text-left px-4 py-3 text-zinc-600 font-medium">税种</th>
            <th class="text-right px-4 py-3 text-zinc-600 font-medium">记录数</th>
            <th class="text-right px-4 py-3 text-zinc-600 font-medium">应缴金额</th>
            <th class="text-right px-4 py-3 text-zinc-600 font-medium">已缴金额</th>
            <th class="text-right px-4 py-3 text-zinc-600 font-medium">未缴金额</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="s in summaries" :key="s.tax_type" class="border-b border-stone-100">
            <td class="px-4 py-3 font-medium text-zinc-800">{{ s.label }}</td>
            <td class="px-4 py-3 text-right text-zinc-600">{{ s.count }}</td>
            <td class="px-4 py-3 text-right text-amber-600">¥{{ Number(s.total_tax_amount || 0).toLocaleString() }}</td>
            <td class="px-4 py-3 text-right text-green-600">¥{{ Number(s.total_paid_amount || 0).toLocaleString() }}</td>
            <td class="px-4 py-3 text-right text-red-600">¥{{ Number(s.total_unpaid_amount || 0).toLocaleString() }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/TaxReport.vue
git commit -m "feat: add TaxReport.vue with summary cards for VAT/CIT/other reports"
```

---

### Task 9: Replace 18 placeholder routes with 3 parameterized routes

**Files:**
- Modify: `frontend/src/router/index.ts`

- [ ] **Step 1: Replace all tax placeholder routes**

In `frontend/src/router/index.ts`, replace the 18 placeholder tax routes (keep the existing `TaxCustomers.vue` route):

```typescript
  // 税务管理 (keep existing TaxCustomers route)
  { path: '/finance/tax/customers', component: () => import('../views/TaxCustomers.vue'), meta: { requiresAuth: true, pageTitle: '客户信息维护' } },
  // 发票管理 — single component, 3 modes
  { path: '/finance/tax/invoice/sales', component: () => import('../views/TaxInvoiceList.vue'), meta: { requiresAuth: true, pageTitle: '销项发票' } },
  { path: '/finance/tax/invoice/purchase', component: () => import('../views/TaxInvoiceList.vue'), meta: { requiresAuth: true, pageTitle: '进项发票' } },
  { path: '/finance/tax/invoice/query', component: () => import('../views/TaxInvoiceList.vue'), meta: { requiresAuth: true, pageTitle: '发票查询统计' } },
  // 税种管理 — single component, 12 modes (11 taxes + penalty)
  { path: '/finance/tax/vat', component: () => import('../views/TaxDeclarationList.vue'), meta: { requiresAuth: true, pageTitle: '增值税管理' } },
  { path: '/finance/tax/surcharge/urban', component: () => import('../views/TaxDeclarationList.vue'), meta: { requiresAuth: true, pageTitle: '城市维护建设税' } },
  { path: '/finance/tax/surcharge/education', component: () => import('../views/TaxDeclarationList.vue'), meta: { requiresAuth: true, pageTitle: '教育费附加' } },
  { path: '/finance/tax/surcharge/local-edu', component: () => import('../views/TaxDeclarationList.vue'), meta: { requiresAuth: true, pageTitle: '地方教育附加' } },
  { path: '/finance/tax/corporate-income', component: () => import('../views/TaxDeclarationList.vue'), meta: { requiresAuth: true, pageTitle: '企业所得税' } },
  { path: '/finance/tax/iit', component: () => import('../views/TaxDeclarationList.vue'), meta: { requiresAuth: true, pageTitle: '个人所得税代扣代缴' } },
  { path: '/finance/tax/stamp-duty', component: () => import('../views/TaxDeclarationList.vue'), meta: { requiresAuth: true, pageTitle: '印花税' } },
  { path: '/finance/tax/property-tax', component: () => import('../views/TaxDeclarationList.vue'), meta: { requiresAuth: true, pageTitle: '房产税' } },
  { path: '/finance/tax/land-use-tax', component: () => import('../views/TaxDeclarationList.vue'), meta: { requiresAuth: true, pageTitle: '土地使用税' } },
  { path: '/finance/tax/vehicle-tax', component: () => import('../views/TaxDeclarationList.vue'), meta: { requiresAuth: true, pageTitle: '车船税' } },
  { path: '/finance/tax/land-vat', component: () => import('../views/TaxDeclarationList.vue'), meta: { requiresAuth: true, pageTitle: '土地增值税' } },
  { path: '/finance/tax/penalty', component: () => import('../views/TaxDeclarationList.vue'), meta: { requiresAuth: true, pageTitle: '罚款与滞纳金' } },
  // 申报表 — single component, 3 modes
  { path: '/finance/tax/reports/vat', component: () => import('../views/TaxReport.vue'), meta: { requiresAuth: true, pageTitle: '增值税申报表' } },
  { path: '/finance/tax/reports/cit', component: () => import('../views/TaxReport.vue'), meta: { requiresAuth: true, pageTitle: '所得税申报表' } },
  { path: '/finance/tax/reports/other', component: () => import('../views/TaxReport.vue'), meta: { requiresAuth: true, pageTitle: '其他税种申报汇总' } },
```

- [ ] **Step 2: Verify frontend builds**

```bash
cd frontend && npx vue-tsc --noEmit 2>&1 | head -30
```
Expected: No new errors related to tax files

- [ ] **Step 3: Commit**

```bash
git add frontend/src/router/index.ts
git commit -m "feat: replace 18 tax placeholders with 3 parameterized components"
```

---

### Task 10: Add backend tests

**Files:**
- Create: `backend/tests/test_taxes.py`

- [ ] **Step 1: Create test_taxes.py**

```python
"""税务管理端点测试."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

HEADERS = {"Authorization": "Bearer test"}


def test_list_declarations_empty():
    """列表查询 — 无数据"""
    # This test verifies the endpoint is registered and returns 401 without auth
    resp = client.get("/api/taxes/declarations?company_id=1")
    assert resp.status_code == 401


def test_list_invoices_empty():
    """发票列表 — 无数据"""
    resp = client.get("/api/taxes/invoices?company_id=1")
    assert resp.status_code == 401


def test_declaration_crud_unauthorized():
    """申报 CRUD — 无认证拒绝"""
    resp = client.post("/api/taxes/declarations", json={
        "company_id": 1, "tax_type": "vat",
        "period_start": "2026-01-01", "period_end": "2026-01-31",
        "tax_amount": 1000.0, "status": "pending",
    })
    assert resp.status_code == 401

    resp = client.get("/api/taxes/declarations/1")
    assert resp.status_code == 401

    resp = client.put("/api/taxes/declarations/1", json={"tax_amount": 2000.0})
    assert resp.status_code == 401

    resp = client.delete("/api/taxes/declarations/1")
    assert resp.status_code == 401


def test_invoice_crud_unauthorized():
    """发票 CRUD — 无认证拒绝"""
    resp = client.post("/api/taxes/invoices", json={
        "company_id": 1, "invoice_type": "sales",
        "invoice_number": "INV-001", "invoice_date": "2026-01-15",
        "amount": 10000.0, "tax_rate": 13.0,
        "tax_amount": 1300.0, "total_amount": 11300.0,
    })
    assert resp.status_code == 401

    resp = client.get("/api/taxes/invoices/1")
    assert resp.status_code == 401

    resp = client.put("/api/taxes/invoices/1", json={"amount": 20000.0})
    assert resp.status_code == 401

    resp = client.delete("/api/taxes/invoices/1")
    assert resp.status_code == 401


def test_summary_endpoints():
    """汇总端点 — 端点可用"""
    resp = client.get("/api/taxes/declarations/summary?company_id=1")
    assert resp.status_code == 401

    resp = client.get("/api/taxes/invoices/summary?company_id=1")
    assert resp.status_code == 401


def test_all_12_endpoints_registered():
    """验证 12 个端点已注册"""
    routes = [r.path for r in app.routes if hasattr(r, "path")]
    tax_routes = [r for r in routes if "/api/taxes" in r]

    expected = [
        "/api/taxes/declarations",
        "/api/taxes/declarations/summary",
        "/api/taxes/declarations/{declaration_id}",
        "/api/taxes/invoices",
        "/api/taxes/invoices/summary",
        "/api/taxes/invoices/{invoice_id}",
    ]
    for path in expected:
        assert path in tax_routes, f"Missing route: {path}"
```

- [ ] **Step 2: Run tests**

```bash
cd backend && uv run pytest tests/test_taxes.py -v
```
Expected: All tests pass

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_taxes.py
git commit -m "test: add tax management endpoint tests"
```

---

### Task 11: End-to-end verification

**Files:** None (verification only)

- [ ] **Step 1: Start backend and verify API docs show tax endpoints**

```bash
cd backend && uv run uvicorn app.main:app --port 8000 &
sleep 3
curl -s http://localhost:8000/docs | grep -o "税务管理" || echo "check /docs manually"
```
Expected: Tax management tag visible in Swagger docs

- [ ] **Step 2: Start frontend dev server and verify routes load**

```bash
cd frontend && npm run dev &
sleep 3
```
Verify in browser that all 19 tax menu items navigate to non-placeholder pages.

- [ ] **Step 3: Manual CRUD smoke test**

Login as admin/admin123 (Company 1):
1. Navigate to 销项发票 → add a test invoice → verify it appears in list
2. Navigate to 增值税管理 → add a test declaration → verify it appears
3. Navigate to 发票查询统计 → verify cross-type listing works
4. Navigate to 增值税申报表 → verify summary cards show totals
5. Navigate to 罚款与滞纳金 → verify penalty-specific form (no tax_base/tax_rate fields)
```

