"""税务管理 Pydantic Schema."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


TAX_TYPES = [
    "vat",
    "urban",
    "education",
    "local_edu",
    "corporate_income",
    "iit",
    "stamp_duty",
    "property_tax",
    "land_use_tax",
    "vehicle_tax",
    "land_vat",
    "penalty",
]

TAX_TYPE_LABELS = {
    "vat": "增值税",
    "urban": "城市维护建设税",
    "education": "教育费附加",
    "local_edu": "地方教育附加",
    "corporate_income": "企业所得税",
    "iit": "个人所得税代扣代缴",
    "stamp_duty": "印花税",
    "property_tax": "房产税",
    "land_use_tax": "土地使用税",
    "vehicle_tax": "车船税",
    "land_vat": "土地增值税",
    "penalty": "罚款与滞纳金",
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
