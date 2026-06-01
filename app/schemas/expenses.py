"""费用报销 Pydantic Schema."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# ── 费用项目 ──

class ExpenseItemCreate(BaseModel):
    company_id: int
    code: str
    name: str
    parent_code: Optional[str] = None
    tax_rate: Optional[float] = None
    is_active: bool = True


class ExpenseItemResponse(BaseModel):
    id: int
    company_id: int
    code: str
    name: str
    parent_code: Optional[str] = None
    tax_rate: Optional[float] = None
    is_active: bool

    model_config = {"from_attributes": True}


# ── 费用标准 ──

class ExpensePolicyCreate(BaseModel):
    company_id: int
    expense_item_id: Optional[int] = None
    country: Optional[str] = None
    region: Optional[str] = None
    department_id: Optional[int] = None
    position_level: Optional[int] = None
    policy_type: str = "event"
    max_amount: float = 0.0
    currency: str = "CNY"
    effective_from: str
    effective_to: Optional[str] = None
    notes: Optional[str] = None


class ExpensePolicyResponse(BaseModel):
    id: int
    company_id: int
    expense_item_id: Optional[int] = None
    country: Optional[str] = None
    region: Optional[str] = None
    department_id: Optional[int] = None
    position_level: Optional[int] = None
    policy_type: str
    max_amount: float
    currency: str
    effective_from: str
    effective_to: Optional[str] = None
    notes: Optional[str] = None

    model_config = {"from_attributes": True}


# ── 报销单明细 ──

class ExpenseReportItemCreate(BaseModel):
    row_seq: int = 1
    expense_item_id: Optional[int] = None
    date: str
    amount: float
    description: Optional[str] = None
    receipt_count: int = 0


class ExpenseReportItemResponse(BaseModel):
    id: int
    report_id: int
    row_seq: int
    expense_item_id: Optional[int] = None
    date: str
    amount: float
    description: Optional[str] = None
    receipt_count: int
    policy_check: Optional[dict] = None

    model_config = {"from_attributes": True}


# ── 报销单 ──

class ExpenseReportCreate(BaseModel):
    company_id: int
    expense_date: str
    department_id: Optional[int] = None
    notes: Optional[str] = None
    items: list[ExpenseReportItemCreate]


class ExpenseReportUpdate(BaseModel):
    expense_date: Optional[str] = None
    department_id: Optional[int] = None
    notes: Optional[str] = None
    items: Optional[list[ExpenseReportItemCreate]] = None


class ExpenseReportResponse(BaseModel):
    id: int
    company_id: int
    report_no: str
    applicant_id: int
    department_id: Optional[int] = None
    expense_date: str
    total_amount: float
    loan_offset_amount: float
    net_payable: float
    status: str
    current_approver_id: Optional[int] = None
    approval_chain: Optional[list] = None
    policy_warnings: Optional[list] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── 借款单 ──

class ExpenseLoanCreate(BaseModel):
    company_id: int
    loan_date: str
    amount: float
    reason: Optional[str] = None
    department_id: Optional[int] = None
    expected_repay_date: Optional[str] = None
    notes: Optional[str] = None


class ExpenseLoanResponse(BaseModel):
    id: int
    company_id: int
    loan_no: str
    applicant_id: int
    department_id: Optional[int] = None
    loan_date: str
    amount: float
    repaid_amount: float
    reason: Optional[str] = None
    status: str
    expected_repay_date: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── 附件 ──

class ExpenseAttachmentResponse(BaseModel):
    id: int
    report_id: Optional[int] = None
    loan_id: Optional[int] = None
    file_name: str
    category: str
    doc_number: Optional[str] = None
    file_path: str
    file_size: int
    uploaded_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── 审批操作 ──

class ApprovalAction(BaseModel):
    comment: Optional[str] = None


# ── 还款操作 ──

class RepayAction(BaseModel):
    amount: float
    notes: Optional[str] = None
