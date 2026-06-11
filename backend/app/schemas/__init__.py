"""Pydantic 校验 Schema."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: str = "accountant"


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    username: str
    password: str
    company_id: Optional[int] = None
    period: Optional[str] = None
    is_admin: bool = False


class Token(BaseModel):
    access_token: str
    token_type: str


class CompanyCreate(BaseModel):
    name: str
    short_name: Optional[str] = None
    industry: str = "consulting"
    internal_control_mode: str = "standard"
    currency: str = "CNY"


class CompanyResponse(BaseModel):
    id: int
    name: str
    short_name: Optional[str]
    industry: str
    internal_control_mode: str
    currency: str
    fiscal_year_start: str
    tax_number: Optional[str]
    english_name: Optional[str]
    english_short_name: Optional[str]
    tax_region: Optional[str]
    website: Optional[str]
    email: Optional[str]
    address: Optional[str]
    phone: Optional[str]
    contact_person: Optional[str]
    created_at: Optional[datetime]

    model_config = {"from_attributes": True}


class DepartmentCreate(BaseModel):
    company_id: int
    name: str
    code: str
    manager: Optional[str] = None


class DepartmentResponse(BaseModel):
    id: int
    company_id: int
    name: str
    code: str
    is_active: bool
    manager: Optional[str]

    model_config = {"from_attributes": True}


class AccountCreate(BaseModel):
    company_id: int
    code: str
    name: str
    level: int
    parent_code: Optional[str] = None
    category: str
    balance_direction: str
    initial_balance: float = 0.0


class AccountResponse(BaseModel):
    id: int
    company_id: int
    code: str
    name: str
    level: int
    parent_code: Optional[str]
    category: str
    balance_direction: str
    initial_balance: Optional[float] = 0.0
    is_system: bool
    is_active: bool
    aux_dept: int = 0
    aux_person: int = 0
    aux_counterparty: int = 0
    aux_project: int = 0

    model_config = {"from_attributes": True}


class CounterpartyResponse(BaseModel):
    id: int
    company_id: int
    code: str
    name: str
    short_name: Optional[str] = None
    category: Optional[str] = None
    tax_number: Optional[str] = None
    bank_account: Optional[str] = None
    bank_name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    contact_person: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    zip_code: Optional[str] = None
    is_active: bool
    category_code: Optional[str] = None

    model_config = {"from_attributes": True}


class PersonResponse(BaseModel):
    id: int
    company_id: int
    code: str
    name: str
    department_code: Optional[str] = None
    is_active: bool

    model_config = {"from_attributes": True}


class BankSettlementSchema(BaseModel):
    seq: int
    settlement_method: str
    account_name: Optional[str] = None
    instrument_no: Optional[str] = None
    instrument_date: Optional[str] = None
    direction: str = "debit"
    amount: float = 0.0


class BankSettlementResponse(BaseModel):
    id: int
    voucher_entry_id: int
    seq: int
    settlement_method: str
    account_name: Optional[str] = None
    instrument_no: Optional[str] = None
    instrument_date: Optional[str] = None
    direction: str
    amount: float

    model_config = {"from_attributes": True}


class VoucherEntrySchema(BaseModel):
    account_code: str
    department_id: Optional[int] = None
    counterparty_id: Optional[int] = None
    person_id: Optional[int] = None
    project_id: Optional[int] = None
    debit: float = 0.0
    credit: float = 0.0
    description: Optional[str] = None
    settlements: Optional[list[BankSettlementSchema]] = None


class ProjectResponse(BaseModel):
    id: int
    company_id: int
    code: str
    name: str
    project_type: str = "product"
    status: str = "active"
    department_id: Optional[int] = None
    manager: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    budget: float = 0.0
    is_active: bool

    model_config = {"from_attributes": True}


class VoucherCreate(BaseModel):
    company_id: int
    date: str
    voucher_type: str  # receipt/payment/transfer
    summary: str
    entries: list[VoucherEntrySchema]


class VoucherUpdate(BaseModel):
    summary: Optional[str] = None
    date: Optional[str] = None
    voucher_type: Optional[str] = None
    entries: Optional[list[VoucherEntrySchema]] = None


class VoucherEntryResponse(BaseModel):
    id: int
    voucher_id: int
    account_code: str
    department_id: Optional[int] = None
    counterparty_id: Optional[int] = None
    person_id: Optional[int] = None
    project_id: Optional[int] = None
    debit: float
    credit: float
    description: Optional[str] = None
    settlements: list[BankSettlementResponse] = []

    model_config = {"from_attributes": True}


class VoucherResponse(BaseModel):
    id: int
    company_id: int
    date: str
    voucher_no: str
    voucher_type: str
    summary: str
    creator_id: int
    status: str
    created_at: Optional[datetime]
    approved_by: Optional[int]
    approved_at: Optional[datetime]
    posted_by: Optional[int]
    posted_at: Optional[datetime]
    entries: list[VoucherEntryResponse] = []

    model_config = {"from_attributes": True}


class ReverseVoucherRequest(BaseModel):
    reason: str


class ClosePeriodRequest(BaseModel):
    company_id: int
    period: str
    reason: Optional[str] = None


class PeriodResponse(BaseModel):
    id: int
    company_id: int
    period: str
    is_closed: bool
    closed_status: str

    model_config = {"from_attributes": True}


class AuditLogResponse(BaseModel):
    id: int
    company_id: int
    user_id: int
    action: str
    target_type: str
    target_id: Optional[int]
    reason: Optional[str]
    details: Optional[dict]
    created_at: Optional[datetime]

    model_config = {"from_attributes": True}


class UserPermissionSchema(BaseModel):
    user_id: int
    company_id: int
    voucher_create: bool = True
    voucher_edit: bool = True
    voucher_delete: bool = False
    voucher_post: bool = True
    voucher_reverse: bool = False
    period_close: bool = False
    period_unclose: bool = False
    view_detail_ledger: bool = True
    view_general_ledger: bool = True
    view_reports: bool = True


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    short_name: Optional[str] = None
    industry: Optional[str] = None
    internal_control_mode: Optional[str] = None
    currency: Optional[str] = None
    fiscal_year_start: Optional[str] = None
    tax_number: Optional[str] = None
    english_name: Optional[str] = None
    english_short_name: Optional[str] = None
    tax_region: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    contact_person: Optional[str] = None


# --- Investment Schemas ---

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


class InvestmentTransactionUpdate(BaseModel):
    position_id: Optional[int] = None
    transaction_type: Optional[str] = None
    transaction_date: Optional[str] = None
    quantity: Optional[float] = None
    price: Optional[float] = None
    amount: Optional[float] = None
    fee: Optional[float] = None
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


class FairValueAdjustmentUpdate(BaseModel):
    position_id: Optional[int] = None
    adjustment_date: Optional[str] = None
    previous_value: Optional[float] = None
    adjusted_value: Optional[float] = None
    change_amount: Optional[float] = None
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


class InvestmentIncomeUpdate(BaseModel):
    position_id: Optional[int] = None
    income_type: Optional[str] = None
    income_date: Optional[str] = None
    amount: Optional[float] = None
    notes: Optional[str] = None


class InvestmentIncomeResponse(BaseModel):
    id: int
    company_id: int
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


# ═══════════════════════════════════════════
# 证券主数据
# ═══════════════════════════════════════════

class SecurityMasterCreate(BaseModel):
    security_code: str
    security_name: str
    security_type: str = "equity"
    exchange: Optional[str] = None
    currency: str = "CNY"
    isin_code: Optional[str] = None

class SecurityMasterUpdate(BaseModel):
    security_code: Optional[str] = None
    security_name: Optional[str] = None
    security_type: Optional[str] = None
    exchange: Optional[str] = None
    currency: Optional[str] = None
    isin_code: Optional[str] = None
    status: Optional[str] = None

class SecurityMasterResponse(BaseModel):
    id: int
    company_id: int
    security_code: str
    security_name: str
    security_type: str
    exchange: Optional[str] = None
    currency: str
    isin_code: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ═══════════ 基金管理 ═══════════

class InvestmentFundCreate(BaseModel):
    fund_name: str
    fund_type: str = "private_fund"
    management_company: Optional[str] = None
    inception_date: Optional[str] = None
    currency: str = "CNY"
    total_commitment: float = 0.0
    portfolio_id: Optional[int] = None

class InvestmentFundUpdate(BaseModel):
    fund_name: Optional[str] = None
    fund_type: Optional[str] = None
    management_company: Optional[str] = None
    inception_date: Optional[str] = None
    currency: Optional[str] = None
    total_commitment: Optional[float] = None
    portfolio_id: Optional[int] = None
    status: Optional[str] = None

class InvestmentFundResponse(BaseModel):
    id: int; company_id: int; fund_name: str; fund_type: str
    management_company: Optional[str] = None; inception_date: Optional[str] = None
    currency: str; total_commitment: float; portfolio_id: Optional[int] = None
    status: str; created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class CapitalAccountCreate(BaseModel):
    investor_id: int
    committed_capital: float = 0.0
    called_capital: float = 0.0
    ownership_pct: float = 0.0

class CapitalAccountUpdate(BaseModel):
    investor_id: Optional[int] = None
    committed_capital: Optional[float] = None
    called_capital: Optional[float] = None
    ownership_pct: Optional[float] = None

class CapitalAccountResponse(BaseModel):
    id: int; company_id: int; fund_id: int; investor_id: int
    committed_capital: float; called_capital: float; ownership_pct: float
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class CapitalCallCreate(BaseModel):
    call_date: str; call_amount: float = 0.0; due_date: Optional[str] = None; notes: Optional[str] = None

class CapitalCallUpdate(BaseModel):
    call_date: Optional[str] = None; call_amount: Optional[float] = None
    due_date: Optional[str] = None; status: Optional[str] = None; notes: Optional[str] = None

class CapitalCallResponse(BaseModel):
    id: int; company_id: int; fund_id: int; call_date: str; call_amount: float
    due_date: Optional[str] = None; status: str; notes: Optional[str] = None
    voucher_id: Optional[int] = None; created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class FundDistributionCreate(BaseModel):
    distribution_date: str; amount: float = 0.0
    distribution_type: str = "income"; notes: Optional[str] = None

class FundDistributionUpdate(BaseModel):
    distribution_date: Optional[str] = None; amount: Optional[float] = None
    distribution_type: Optional[str] = None; notes: Optional[str] = None

class FundDistributionResponse(BaseModel):
    id: int; company_id: int; fund_id: int; distribution_date: str; amount: float
    distribution_type: str; notes: Optional[str] = None
    voucher_id: Optional[int] = None; created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


# ═══════════ 分配瀑布 ═══════════

class WaterfallConfigCreate(BaseModel):
    name: str
    portfolio_id: Optional[int] = None
    tiers: list = []

class WaterfallConfigUpdate(BaseModel):
    name: Optional[str] = None
    portfolio_id: Optional[int] = None
    tiers: Optional[list] = None

class WaterfallConfigResponse(BaseModel):
    id: int; company_id: int; name: str
    portfolio_id: Optional[int] = None; tiers: list
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class WaterfallCalculateRequest(BaseModel):
    config_id: int
    total_proceeds: float = 0.0  # 待分配总收益


# ═══════════ 房地产资产 ═══════════

class RealEstateAssetCreate(BaseModel):
    property_name: str; property_type: str = "commercial"; location: Optional[str] = None
    acquisition_date: Optional[str] = None; acquisition_cost: float = 0.0
    current_value: float = 0.0; valuation_date: Optional[str] = None
    area_sqm: float = 0.0; occupancy_pct: float = 0.0; annual_rental_income: float = 0.0
    portfolio_id: Optional[int] = None

class RealEstateAssetUpdate(BaseModel):
    property_name: Optional[str] = None; property_type: Optional[str] = None
    location: Optional[str] = None; acquisition_date: Optional[str] = None
    acquisition_cost: Optional[float] = None; current_value: Optional[float] = None
    valuation_date: Optional[str] = None; area_sqm: Optional[float] = None
    occupancy_pct: Optional[float] = None; annual_rental_income: Optional[float] = None
    portfolio_id: Optional[int] = None; status: Optional[str] = None

class RealEstateAssetResponse(BaseModel):
    id: int; company_id: int; property_name: str; property_type: str
    location: Optional[str] = None; acquisition_date: Optional[str] = None
    acquisition_cost: float; current_value: float; valuation_date: Optional[str] = None
    area_sqm: float; occupancy_pct: float; annual_rental_income: float
    portfolio_id: Optional[int] = None; status: str; created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class RealEstateValuationCreate(BaseModel):
    valuation_date: str; value: float = 0.0
    valuation_method: str = "comparable"; appraiser: Optional[str] = None; notes: Optional[str] = None

class RealEstateValuationUpdate(BaseModel):
    valuation_date: Optional[str] = None; value: Optional[float] = None
    valuation_method: Optional[str] = None; appraiser: Optional[str] = None; notes: Optional[str] = None

class RealEstateValuationResponse(BaseModel):
    id: int; company_id: int; asset_id: int; valuation_date: str; value: float
    valuation_method: str; appraiser: Optional[str] = None; notes: Optional[str] = None
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

# ═══════════ 基础设施资产 ═══════════

class InfraAssetCreate(BaseModel):
    project_name: str; asset_type: str = "energy"; location: Optional[str] = None
    investment_date: Optional[str] = None; investment_amount: float = 0.0
    current_value: float = 0.0; valuation_date: Optional[str] = None
    annual_revenue: float = 0.0; concession_expiry: Optional[str] = None
    portfolio_id: Optional[int] = None

class InfraAssetUpdate(BaseModel):
    project_name: Optional[str] = None; asset_type: Optional[str] = None
    location: Optional[str] = None; investment_date: Optional[str] = None
    investment_amount: Optional[float] = None; current_value: Optional[float] = None
    valuation_date: Optional[str] = None; annual_revenue: Optional[float] = None
    concession_expiry: Optional[str] = None; portfolio_id: Optional[int] = None; status: Optional[str] = None

class InfraAssetResponse(BaseModel):
    id: int; company_id: int; project_name: str; asset_type: str
    location: Optional[str] = None; investment_date: Optional[str] = None
    investment_amount: float; current_value: float; valuation_date: Optional[str] = None
    annual_revenue: float; concession_expiry: Optional[str] = None
    portfolio_id: Optional[int] = None; status: str; created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

# ═══════════ 私募信贷资产 ═══════════

class PrivateCreditCreate(BaseModel):
    borrower_name: str; instrument_type: str = "senior_secured"
    principal_amount: float = 0.0; interest_rate: float = 0.0
    origination_date: Optional[str] = None; maturity_date: Optional[str] = None
    outstanding_principal: float = 0.0; accrued_interest: float = 0.0
    credit_rating: Optional[str] = None; collateral: Optional[str] = None
    counterparty_id: Optional[int] = None

class PrivateCreditUpdate(BaseModel):
    borrower_name: Optional[str] = None; instrument_type: Optional[str] = None
    principal_amount: Optional[float] = None; interest_rate: Optional[float] = None
    origination_date: Optional[str] = None; maturity_date: Optional[str] = None
    outstanding_principal: Optional[float] = None; accrued_interest: Optional[float] = None
    credit_rating: Optional[str] = None; collateral: Optional[str] = None
    counterparty_id: Optional[int] = None; status: Optional[str] = None

class PrivateCreditResponse(BaseModel):
    id: int; company_id: int; borrower_name: str; instrument_type: str
    principal_amount: float; interest_rate: float
    origination_date: Optional[str] = None; maturity_date: Optional[str] = None
    outstanding_principal: float; accrued_interest: float
    credit_rating: Optional[str] = None; collateral: Optional[str] = None
    counterparty_id: Optional[int] = None; status: str; created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class CreditPaymentCreate(BaseModel):
    payment_date: str; payment_type: str = "interest"; amount: float = 0.0

class CreditPaymentUpdate(BaseModel):
    payment_date: Optional[str] = None; payment_type: Optional[str] = None; amount: Optional[float] = None

class CreditPaymentResponse(BaseModel):
    id: int; company_id: int; credit_id: int; payment_date: str; payment_type: str
    amount: float; voucher_id: Optional[int] = None; created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════
# 人力资源管理模块
# ═══════════════════════════════════════════

class HrPolicyCreate(BaseModel):
    company_id: int
    title: str
    content: Optional[str] = None

class HrPolicyResponse(BaseModel):
    id: int; company_id: int; title: str; content: Optional[str] = None
    updated_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class HrPositionCreate(BaseModel):
    company_id: int
    name: str
    level: int
    sort_order: Optional[int] = None

class HrPositionResponse(BaseModel):
    id: int; company_id: int; name: str; level: int
    sort_order: Optional[int] = None; is_active: bool = True
    model_config = {"from_attributes": True}

class HrEmployeeCreate(BaseModel):
    company_id: int
    employee_code: str; name: str
    gender: Optional[str] = None; birth_date: Optional[str] = None
    id_card: Optional[str] = None; passport: Optional[str] = None
    native_place: Optional[str] = None; graduate_school: Optional[str] = None
    graduate_date: Optional[str] = None; major: Optional[str] = None
    career_history: Optional[str] = None; expertise: Optional[str] = None
    mobile: Optional[str] = None; personal_email: Optional[str] = None
    company_email: Optional[str] = None; emergency_contact: Optional[str] = None
    home_address: Optional[str] = None
    nationality: Optional[str] = None; political_party: Optional[str] = None
    religion: Optional[str] = None; professional_associations: Optional[str] = None
    certifications: Optional[str] = None
    position_id: Optional[int] = None; department_id: Optional[int] = None
    status: Optional[str] = "在职"; hire_date: Optional[str] = None

class HrEmployeeResponse(BaseModel):
    id: int; company_id: int; employee_code: str; name: str
    gender: Optional[str] = None; birth_date: Optional[str] = None
    id_card: Optional[str] = None; passport: Optional[str] = None
    native_place: Optional[str] = None; graduate_school: Optional[str] = None
    graduate_date: Optional[str] = None; major: Optional[str] = None
    career_history: Optional[str] = None; expertise: Optional[str] = None
    mobile: Optional[str] = None; personal_email: Optional[str] = None
    company_email: Optional[str] = None; emergency_contact: Optional[str] = None
    home_address: Optional[str] = None
    nationality: Optional[str] = None; political_party: Optional[str] = None
    religion: Optional[str] = None; professional_associations: Optional[str] = None
    certifications: Optional[str] = None
    position_id: Optional[int] = None; department_id: Optional[int] = None
    status: str = "在职"; hire_date: Optional[str] = None
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class HrTrainingCreate(BaseModel):
    company_id: int; employee_id: int; training_name: str
    training_date: Optional[str] = None; provider: Optional[str] = None
    cost: Optional[float] = None; status: Optional[str] = "计划中"
    notes: Optional[str] = None

class HrTrainingResponse(BaseModel):
    id: int; company_id: int; employee_id: int; training_name: str
    training_date: Optional[str] = None; provider: Optional[str] = None
    cost: Optional[float] = None; status: str = "计划中"
    notes: Optional[str] = None
    model_config = {"from_attributes": True}

class HrEvaluationCreate(BaseModel):
    company_id: int; employee_id: int
    period: Optional[str] = None; score: Optional[float] = None
    grade: Optional[str] = None; evaluator: Optional[str] = None
    notes: Optional[str] = None

class HrEvaluationResponse(BaseModel):
    id: int; company_id: int; employee_id: int
    period: Optional[str] = None; score: Optional[float] = None
    grade: Optional[str] = None; evaluator: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class HrSalaryCreate(BaseModel):
    company_id: int; employee_id: int; year_month: str
    base_salary: Optional[float] = 0; bonus: Optional[float] = 0
    allowance: Optional[float] = 0; deduction: Optional[float] = 0
    net_salary: Optional[float] = 0; notes: Optional[str] = None

class HrSalaryResponse(BaseModel):
    id: int; company_id: int; employee_id: int; year_month: str
    base_salary: float = 0; bonus: float = 0; allowance: float = 0
    deduction: float = 0; net_salary: float = 0
    notes: Optional[str] = None
    model_config = {"from_attributes": True}

class HrRewardPunishmentCreate(BaseModel):
    company_id: int; employee_id: int; type: str
    date: Optional[str] = None; description: Optional[str] = None
    amount: Optional[float] = None; approved_by: Optional[str] = None

class HrRewardPunishmentResponse(BaseModel):
    id: int; company_id: int; employee_id: int; type: str
    date: Optional[str] = None; description: Optional[str] = None
    amount: Optional[float] = None; approved_by: Optional[str] = None
    model_config = {"from_attributes": True}

class HrOffboardingCreate(BaseModel):
    company_id: int; employee_id: int
    apply_date: Optional[str] = None; last_day: Optional[str] = None
    reason: Optional[str] = None; handover_to: Optional[str] = None
    status: Optional[str] = "申请"; notes: Optional[str] = None

class HrOffboardingResponse(BaseModel):
    id: int; company_id: int; employee_id: int
    apply_date: Optional[str] = None; last_day: Optional[str] = None
    reason: Optional[str] = None; handover_to: Optional[str] = None
    status: str = "申请"; notes: Optional[str] = None
    model_config = {"from_attributes": True}

class HrBudgetCreate(BaseModel):
    company_id: int; year: int
    department_id: Optional[int] = None
    headcount_planned: Optional[int] = 0; headcount_actual: Optional[int] = 0
    salary_budget: Optional[float] = 0; training_budget: Optional[float] = 0
    recruitment_budget: Optional[float] = 0; total_budget: Optional[float] = 0
    notes: Optional[str] = None

class HrBudgetResponse(BaseModel):
    id: int; company_id: int; year: int
    department_id: Optional[int] = None
    headcount_planned: int = 0; headcount_actual: int = 0
    salary_budget: float = 0; training_budget: float = 0
    recruitment_budget: float = 0; total_budget: float = 0
    notes: Optional[str] = None
    model_config = {"from_attributes": True}


# ═══════════ 固定资产管理 ═══════════

class FixedAssetCreate(BaseModel):
    company_id: int
    asset_code: str
    name: str
    category: str = "设备"
    acquisition_date: Optional[str] = None
    original_value: float = 0
    residual_value: float = 0
    useful_life: int = 5
    depreciation_method: str = "直线法"
    monthly_depreciation: float = 0
    status: str = "使用中"
    location: Optional[str] = None
    department_id: Optional[int] = None
    notes: Optional[str] = None

class FixedAssetResponse(BaseModel):
    id: int; company_id: int; asset_code: str; name: str; category: str
    acquisition_date: Optional[str] = None
    original_value: float; residual_value: float; useful_life: int
    depreciation_method: str; monthly_depreciation: float
    accumulated_depreciation: float; net_value: float; status: str
    location: Optional[str] = None; department_id: Optional[int] = None
    disposal_date: Optional[str] = None
    disposal_proceeds: Optional[float] = None
    disposal_gain_loss: Optional[float] = None
    disposal_reason: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None; updated_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class FixedAssetUpdate(BaseModel):
    asset_code: Optional[str] = None
    name: Optional[str] = None
    category: Optional[str] = None
    acquisition_date: Optional[str] = None
    original_value: Optional[float] = None
    residual_value: Optional[float] = None
    useful_life: Optional[int] = None
    depreciation_method: Optional[str] = None
    monthly_depreciation: Optional[float] = None
    status: Optional[str] = None
    location: Optional[str] = None
    department_id: Optional[int] = None
    notes: Optional[str] = None

class FixedAssetDispose(BaseModel):
    disposal_date: str
    disposal_proceeds: float = 0
    disposal_reason: Optional[str] = None
    status: str  # "已处置" or "报废"

class BatchDepreciationRequest(BaseModel):
    company_id: int
    period: str
    asset_ids: Optional[list[int]] = None

class FixedAssetDepreciationCreate(BaseModel):
    company_id: int; fixed_asset_id: int; period: str
    depreciation_amount: float = 0

class FixedAssetDepreciationResponse(BaseModel):
    id: int; company_id: int; fixed_asset_id: int; period: str
    depreciation_amount: float; accumulated_before: float; accumulated_after: float
    created_at: Optional[datetime] = None; updated_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


# ═══════════ 应收账款管理 ═══════════

class ReceivableCreate(BaseModel):
    company_id: int; customer_name: str; invoice_no: str
    invoice_date: Optional[str] = None; amount: float = 0
    due_date: Optional[str] = None; notes: Optional[str] = None

class ReceivableResponse(BaseModel):
    id: int; company_id: int; customer_name: str; invoice_no: str
    invoice_date: Optional[str] = None; amount: float; received_amount: float
    balance: float; due_date: Optional[str] = None; aging_days: int; status: str
    notes: Optional[str] = None
    created_at: Optional[datetime] = None; updated_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class ReceivablePaymentCreate(BaseModel):
    company_id: int; receivable_id: int; payment_date: str
    amount: float = 0; payment_method: Optional[str] = None
    notes: Optional[str] = None

class ReceivablePaymentResponse(BaseModel):
    id: int; company_id: int; receivable_id: int; payment_date: str
    amount: float; payment_method: Optional[str] = None
    notes: Optional[str] = None; created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


# ═══════════ 应付账款管理 ═══════════

class PayableCreate(BaseModel):
    company_id: int; supplier_name: str; invoice_no: str
    invoice_date: Optional[str] = None; amount: float = 0
    due_date: Optional[str] = None; notes: Optional[str] = None

class PayableResponse(BaseModel):
    id: int; company_id: int; supplier_name: str; invoice_no: str
    invoice_date: Optional[str] = None; amount: float; paid_amount: float
    balance: float; due_date: Optional[str] = None; aging_days: int; status: str
    notes: Optional[str] = None
    created_at: Optional[datetime] = None; updated_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class PayablePaymentCreate(BaseModel):
    company_id: int; payable_id: int; payment_date: str
    amount: float = 0; payment_method: Optional[str] = None
    notes: Optional[str] = None

class PayablePaymentResponse(BaseModel):
    id: int; company_id: int; payable_id: int; payment_date: str
    amount: float; payment_method: Optional[str] = None
    notes: Optional[str] = None; created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


# ═══════════ 进销存管理 ═══════════

class InvPurchaseCreate(BaseModel):
    company_id: int; order_no: str; supplier_name: str
    order_date: Optional[str] = None; product_name: str
    quantity: float = 0; unit: str = "个"; unit_price: float = 0
    total_amount: float = 0; status: str = "待入库"
    notes: Optional[str] = None

class InvPurchaseResponse(BaseModel):
    id: int; company_id: int; order_no: str; supplier_name: str
    order_date: Optional[str] = None; product_name: str
    quantity: float; unit: str; unit_price: float; total_amount: float
    status: str; notes: Optional[str] = None
    created_at: Optional[datetime] = None; updated_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class InvSaleCreate(BaseModel):
    company_id: int; order_no: str; customer_name: str
    order_date: Optional[str] = None; product_name: str
    quantity: float = 0; unit: str = "个"; unit_price: float = 0
    total_amount: float = 0; cost_amount: float = 0
    status: str = "待出库"; notes: Optional[str] = None

class InvSaleResponse(BaseModel):
    id: int; company_id: int; order_no: str; customer_name: str
    order_date: Optional[str] = None; product_name: str
    quantity: float; unit: str; unit_price: float; total_amount: float
    cost_amount: float; profit: float; status: str
    notes: Optional[str] = None
    created_at: Optional[datetime] = None; updated_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class InvStockCreate(BaseModel):
    company_id: int; product_code: str; product_name: str
    category: Optional[str] = None; quantity: float = 0
    unit: str = "个"; unit_cost: float = 0; total_cost: float = 0
    warehouse: Optional[str] = None; min_stock: float = 0; max_stock: float = 0
    notes: Optional[str] = None

class InvStockResponse(BaseModel):
    id: int; company_id: int; product_code: str; product_name: str
    category: Optional[str] = None; quantity: float; unit: str
    unit_cost: float; total_cost: float; warehouse: Optional[str] = None
    min_stock: float; max_stock: float; notes: Optional[str] = None
    created_at: Optional[datetime] = None; updated_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


# ═══════════ 进销存主数据 ═══════════

class WarehouseCreate(BaseModel):
    company_id: int; code: str; name: str
    manager_code: Optional[str] = None; manager_name: Optional[str] = None
    address: Optional[str] = None; notes: Optional[str] = None

class WarehouseResponse(BaseModel):
    id: int; company_id: int; code: str; name: str
    manager_code: Optional[str] = None; manager_name: Optional[str] = None
    address: Optional[str] = None; notes: Optional[str] = None
    is_active: bool
    model_config = {"from_attributes": True}

class InventoryCreate(BaseModel):
    company_id: int; code: str; name: str
    category_code: Optional[str] = None; specs: Optional[str] = None
    unit: Optional[str] = None; unit_group: Optional[str] = None
    tax_rate: float = 0.0

class InventoryResponse(BaseModel):
    id: int; company_id: int; code: str; name: str
    category_code: Optional[str] = None; specs: Optional[str] = None
    unit: Optional[str] = None; unit_group: Optional[str] = None
    tax_rate: float; is_active: bool
    model_config = {"from_attributes": True}

class InventoryCategoryCreate(BaseModel):
    company_id: int; code: str; name: str
    parent_code: Optional[str] = None; auto_create_project: bool = False

class InventoryCategoryResponse(BaseModel):
    id: int; company_id: int; code: str; name: str
    parent_code: Optional[str] = None; auto_create_project: bool
    model_config = {"from_attributes": True}

class UnitOfMeasureCreate(BaseModel):
    company_id: int; group_name: str; unit_name: str
    is_primary: bool = False; conversion_type: Optional[str] = None
    conversion_rate: Optional[float] = None; notes: Optional[str] = None

class UnitOfMeasureResponse(BaseModel):
    id: int; company_id: int; group_name: str; unit_name: str
    is_primary: bool; conversion_type: Optional[str] = None
    conversion_rate: Optional[float] = None; notes: Optional[str] = None
    model_config = {"from_attributes": True}


# ── 行政综合管理系统 Schemas ──

class ApprovalRecordCreate(BaseModel):
    company_id: int; target_type: str; target_id: int; step: int
    approver_id: Optional[int] = None; approver_name: Optional[str] = None
    status: str = "pending"; comment: Optional[str] = None

class ApprovalRecordUpdate(BaseModel):
    approver_id: Optional[int] = None; approver_name: Optional[str] = None
    status: Optional[str] = None; comment: Optional[str] = None

class ApprovalRecordResponse(BaseModel):
    id: int; company_id: int; target_type: str; target_id: int; step: int
    approver_id: Optional[int] = None; approver_name: Optional[str] = None
    status: str; comment: Optional[str] = None
    created_at: Optional[datetime] = None; updated_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class SubmitApprovalRequest(BaseModel):
    approver_ids: list[int]

class ApprovalAction(BaseModel):
    comment: Optional[str] = None

class BypassAction(BaseModel):
    reason: str  # 必填，强制跳过原因

class AdminDocumentCreate(BaseModel):
    company_id: int; title: str; document_number: str
    issuing_department: str; recipient_departments: Optional[str] = None
    priority: str = "普通"; content: Optional[str] = None
    attachment_path: Optional[str] = None; issuance_date: Optional[str] = None
    applicant_id: int; applicant_name: str

class AdminDocumentUpdate(BaseModel):
    title: Optional[str] = None; document_number: Optional[str] = None
    issuing_department: Optional[str] = None; recipient_departments: Optional[str] = None
    priority: Optional[str] = None; content: Optional[str] = None
    attachment_path: Optional[str] = None; issuance_date: Optional[str] = None

class AdminDocumentResponse(BaseModel):
    id: int; company_id: int; title: str; document_number: str
    issuing_department: str; recipient_departments: Optional[str] = None
    priority: str; content: Optional[str] = None
    attachment_path: Optional[str] = None; issuance_date: Optional[str] = None
    applicant_id: int; applicant_name: str; status: str
    submit_date: Optional[str] = None
    created_at: Optional[datetime] = None; updated_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class VehicleSupplierCreate(BaseModel):
    company_id: int; name: str; contact_person: Optional[str] = None
    contact_phone: Optional[str] = None; brands_carried: Optional[str] = None
    notes: Optional[str] = None

class VehicleSupplierUpdate(BaseModel):
    name: Optional[str] = None; contact_person: Optional[str] = None
    contact_phone: Optional[str] = None; brands_carried: Optional[str] = None
    notes: Optional[str] = None

class VehicleSupplierResponse(BaseModel):
    id: int; company_id: int; name: str; contact_person: Optional[str] = None
    contact_phone: Optional[str] = None; brands_carried: Optional[str] = None
    notes: Optional[str] = None; created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class VehiclePurchaseCreate(BaseModel):
    company_id: int; applicant: str; department: str
    vehicle_brand: str; vehicle_model: str; configuration: Optional[str] = None
    estimated_price: float = 0; supplier_name: Optional[str] = None
    supplier_contact: Optional[str] = None; reason: Optional[str] = None

class VehiclePurchaseUpdate(BaseModel):
    applicant: Optional[str] = None; department: Optional[str] = None
    vehicle_brand: Optional[str] = None; vehicle_model: Optional[str] = None
    configuration: Optional[str] = None; estimated_price: Optional[float] = None
    supplier_name: Optional[str] = None; supplier_contact: Optional[str] = None
    reason: Optional[str] = None

class VehiclePurchaseResponse(BaseModel):
    id: int; company_id: int; applicant: str; department: str
    vehicle_brand: str; vehicle_model: str; configuration: Optional[str] = None
    estimated_price: float; supplier_name: Optional[str] = None
    supplier_contact: Optional[str] = None; reason: Optional[str] = None
    status: str; submit_date: Optional[str] = None
    created_at: Optional[datetime] = None; updated_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class VehicleCreate(BaseModel):
    company_id: int; license_plate: str; engine_number: Optional[str] = None
    vin: Optional[str] = None; brand: Optional[str] = None; model: Optional[str] = None
    insurance_provider: Optional[str] = None; insurance_policy_no: Optional[str] = None
    insurance_expiry: Optional[str] = None; insurance_doc_path: Optional[str] = None
    purchase_date: Optional[str] = None; purchase_price: float = 0
    status: str = "使用中"; department: Optional[str] = None; notes: Optional[str] = None

class VehicleUpdate(BaseModel):
    license_plate: Optional[str] = None; engine_number: Optional[str] = None
    vin: Optional[str] = None; brand: Optional[str] = None; model: Optional[str] = None
    insurance_provider: Optional[str] = None; insurance_policy_no: Optional[str] = None
    insurance_expiry: Optional[str] = None; insurance_doc_path: Optional[str] = None
    purchase_date: Optional[str] = None; purchase_price: Optional[float] = None
    status: Optional[str] = None; department: Optional[str] = None; notes: Optional[str] = None

class VehicleResponse(BaseModel):
    id: int; company_id: int; license_plate: str
    engine_number: Optional[str] = None; vin: Optional[str] = None
    brand: Optional[str] = None; model: Optional[str] = None
    insurance_provider: Optional[str] = None; insurance_policy_no: Optional[str] = None
    insurance_expiry: Optional[str] = None; insurance_doc_path: Optional[str] = None
    purchase_date: Optional[str] = None; purchase_price: float
    status: str; department: Optional[str] = None; notes: Optional[str] = None
    created_at: Optional[datetime] = None; updated_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class VehicleMaintenanceCreate(BaseModel):
    company_id: int; vehicle_id: int; maintenance_type: str
    vendor: str; estimated_cost: float = 0; actual_cost: Optional[float] = None
    description: Optional[str] = None

class VehicleMaintenanceUpdate(BaseModel):
    vehicle_id: Optional[int] = None; maintenance_type: Optional[str] = None
    vendor: Optional[str] = None; estimated_cost: Optional[float] = None
    actual_cost: Optional[float] = None; description: Optional[str] = None

class VehicleMaintenanceResponse(BaseModel):
    id: int; company_id: int; vehicle_id: int; maintenance_type: str
    vendor: str; estimated_cost: float; actual_cost: Optional[float] = None
    description: Optional[str] = None; status: str; submit_date: Optional[str] = None
    created_at: Optional[datetime] = None; updated_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class InsurancePolicyCreate(BaseModel):
    company_id: int; policy_type: str; insured_assets: str
    insurance_company: str; coverage_amount: float = 0; premium: float = 0
    start_date: str; end_date: str

class InsurancePolicyUpdate(BaseModel):
    policy_type: Optional[str] = None; insured_assets: Optional[str] = None
    insurance_company: Optional[str] = None; coverage_amount: Optional[float] = None
    premium: Optional[float] = None; start_date: Optional[str] = None
    end_date: Optional[str] = None

class InsurancePolicyResponse(BaseModel):
    id: int; company_id: int; policy_type: str; insured_assets: str
    insurance_company: str; coverage_amount: float; premium: float
    start_date: str; end_date: str; status: str; submit_date: Optional[str] = None
    created_at: Optional[datetime] = None; updated_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class StockCategoryCreate(BaseModel):
    company_id: int; name: str; code: str

class StockCategoryUpdate(BaseModel):
    name: Optional[str] = None; code: Optional[str] = None; is_active: Optional[bool] = None

class StockCategoryResponse(BaseModel):
    id: int; company_id: int; name: str; code: str; is_active: bool
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class StockAssetCreate(BaseModel):
    company_id: int; asset_code: str; name: str
    category_id: Optional[int] = None; brand: Optional[str] = None
    model: Optional[str] = None; department: Optional[str] = None
    custodian: Optional[str] = None; location: Optional[str] = None
    purchase_date: Optional[str] = None; purchase_price: float = 0
    status: str = "使用中"; quantity: int = 1; notes: Optional[str] = None

class StockAssetUpdate(BaseModel):
    asset_code: Optional[str] = None; name: Optional[str] = None
    category_id: Optional[int] = None; brand: Optional[str] = None
    model: Optional[str] = None; department: Optional[str] = None
    custodian: Optional[str] = None; location: Optional[str] = None
    purchase_date: Optional[str] = None; purchase_price: Optional[float] = None
    status: Optional[str] = None; quantity: Optional[int] = None; notes: Optional[str] = None

class StockAssetResponse(BaseModel):
    id: int; company_id: int; asset_code: str; name: str
    category_id: Optional[int] = None; brand: Optional[str] = None
    model: Optional[str] = None; department: Optional[str] = None
    custodian: Optional[str] = None; location: Optional[str] = None
    purchase_date: Optional[str] = None; purchase_price: float
    status: str; quantity: int; notes: Optional[str] = None
    created_at: Optional[datetime] = None; updated_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class StockPurchaseCreate(BaseModel):
    company_id: int; applicant: str; department: str
    asset_name: str; category: Optional[str] = None; quantity: int = 1
    estimated_price: float = 0; reason: Optional[str] = None

class StockPurchaseUpdate(BaseModel):
    applicant: Optional[str] = None; department: Optional[str] = None
    asset_name: Optional[str] = None; category: Optional[str] = None
    quantity: Optional[int] = None; estimated_price: Optional[float] = None
    reason: Optional[str] = None

class StockPurchaseResponse(BaseModel):
    id: int; company_id: int; applicant: str; department: str
    asset_name: str; category: Optional[str] = None; quantity: int
    estimated_price: float; reason: Optional[str] = None
    status: str; submit_date: Optional[str] = None
    created_at: Optional[datetime] = None; updated_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class StockRequisitionCreate(BaseModel):
    company_id: int; asset_id: Optional[int] = None
    applicant: str; department: str; quantity: int = 1; reason: Optional[str] = None

class StockRequisitionUpdate(BaseModel):
    asset_id: Optional[int] = None; applicant: Optional[str] = None
    department: Optional[str] = None; quantity: Optional[int] = None
    reason: Optional[str] = None

class StockRequisitionResponse(BaseModel):
    id: int; company_id: int; asset_id: Optional[int] = None
    applicant: str; department: str; quantity: int
    reason: Optional[str] = None; status: str; submit_date: Optional[str] = None
    created_at: Optional[datetime] = None; updated_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class StockInboundCreate(BaseModel):
    company_id: int; asset_id: Optional[int] = None
    inbound_type: str = "采购入库"; quantity: int = 1
    receiver: str; inbound_date: str; notes: Optional[str] = None

class StockInboundUpdate(BaseModel):
    asset_id: Optional[int] = None; inbound_type: Optional[str] = None
    quantity: Optional[int] = None; receiver: Optional[str] = None
    inbound_date: Optional[str] = None; notes: Optional[str] = None

class StockInboundResponse(BaseModel):
    id: int; company_id: int; asset_id: Optional[int] = None
    inbound_type: str; quantity: int; receiver: str; inbound_date: str
    status: str; notes: Optional[str] = None; submit_date: Optional[str] = None
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class StockOutboundCreate(BaseModel):
    company_id: int; asset_id: int; outbound_type: str = "领用"
    quantity: int = 1; recipient: str; outbound_date: str; notes: Optional[str] = None

class StockOutboundUpdate(BaseModel):
    asset_id: Optional[int] = None; outbound_type: Optional[str] = None
    quantity: Optional[int] = None; recipient: Optional[str] = None
    outbound_date: Optional[str] = None; notes: Optional[str] = None

class StockOutboundResponse(BaseModel):
    id: int; company_id: int; asset_id: int; outbound_type: str
    quantity: int; recipient: str; outbound_date: str
    status: str; notes: Optional[str] = None; submit_date: Optional[str] = None
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class StockCountCreate(BaseModel):
    company_id: int; count_date: str; asset_id: int
    book_quantity: int = 0; actual_quantity: int = 0
    discrepancy: int = 0; reason: Optional[str] = None; counter: Optional[str] = None

class StockCountUpdate(BaseModel):
    count_date: Optional[str] = None; asset_id: Optional[int] = None
    book_quantity: Optional[int] = None; actual_quantity: Optional[int] = None
    discrepancy: Optional[int] = None; reason: Optional[str] = None
    counter: Optional[str] = None

class StockCountResponse(BaseModel):
    id: int; company_id: int; count_date: str; asset_id: int
    book_quantity: int; actual_quantity: int; discrepancy: int
    reason: Optional[str] = None; counter: Optional[str] = None
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class GiftCategoryCreate(BaseModel):
    company_id: int; name: str

class GiftCategoryUpdate(BaseModel):
    name: Optional[str] = None; is_active: Optional[bool] = None

class GiftCategoryResponse(BaseModel):
    id: int; company_id: int; name: str; is_active: bool
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class StockGiftCreate(BaseModel):
    company_id: int; name: str; category_id: Optional[int] = None
    unit: str = "个"; current_stock: int = 0; unit_price: float = 0

class StockGiftUpdate(BaseModel):
    name: Optional[str] = None; category_id: Optional[int] = None
    unit: Optional[str] = None; current_stock: Optional[int] = None
    unit_price: Optional[float] = None

class StockGiftResponse(BaseModel):
    id: int; company_id: int; name: str; category_id: Optional[int] = None
    unit: str; current_stock: int; unit_price: float
    created_at: Optional[datetime] = None; updated_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class StockGiftPurchaseCreate(BaseModel):
    company_id: int; gift_id: Optional[int] = None
    applicant: str; department: str; gift_name: str
    quantity: int = 0; unit_price: float = 0; total_price: float = 0
    supplier: Optional[str] = None; reason: Optional[str] = None

class StockGiftPurchaseUpdate(BaseModel):
    gift_id: Optional[int] = None; applicant: Optional[str] = None
    department: Optional[str] = None; gift_name: Optional[str] = None
    quantity: Optional[int] = None; unit_price: Optional[float] = None
    total_price: Optional[float] = None; supplier: Optional[str] = None
    reason: Optional[str] = None

class StockGiftPurchaseResponse(BaseModel):
    id: int; company_id: int; gift_id: Optional[int] = None
    applicant: str; department: str; gift_name: str
    quantity: int; unit_price: float; total_price: float
    supplier: Optional[str] = None; reason: Optional[str] = None
    status: str; submit_date: Optional[str] = None
    created_at: Optional[datetime] = None; updated_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class StockGiftRequisitionCreate(BaseModel):
    company_id: int; gift_id: Optional[int] = None
    applicant: str; department: str; quantity: int = 0
    recipient: Optional[str] = None; recipient_organization: Optional[str] = None
    reason: Optional[str] = None

class StockGiftRequisitionUpdate(BaseModel):
    gift_id: Optional[int] = None; applicant: Optional[str] = None
    department: Optional[str] = None; quantity: Optional[int] = None
    recipient: Optional[str] = None; recipient_organization: Optional[str] = None
    reason: Optional[str] = None

class StockGiftRequisitionResponse(BaseModel):
    id: int; company_id: int; gift_id: Optional[int] = None
    applicant: str; department: str; quantity: int
    recipient: Optional[str] = None; recipient_organization: Optional[str] = None
    reason: Optional[str] = None; status: str; submit_date: Optional[str] = None
    created_at: Optional[datetime] = None; updated_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class StockGiftInboundCreate(BaseModel):
    company_id: int; gift_id: int; inbound_type: str = "采购"
    quantity: int = 0; unit_price: float = 0; supplier: Optional[str] = None
    inbound_date: str; receiver: str; notes: Optional[str] = None

class StockGiftInboundUpdate(BaseModel):
    gift_id: Optional[int] = None; inbound_type: Optional[str] = None
    quantity: Optional[int] = None; unit_price: Optional[float] = None
    supplier: Optional[str] = None; inbound_date: Optional[str] = None
    receiver: Optional[str] = None; notes: Optional[str] = None

class StockGiftInboundResponse(BaseModel):
    id: int; company_id: int; gift_id: int; inbound_type: str
    quantity: int; unit_price: float; supplier: Optional[str] = None
    inbound_date: str; receiver: str; status: str
    notes: Optional[str] = None; submit_date: Optional[str] = None
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class StockGiftOutboundCreate(BaseModel):
    company_id: int; gift_id: int; outbound_type: str = "赠送"
    quantity: int = 0; recipient: str; recipient_organization: Optional[str] = None
    outbound_date: str; notes: Optional[str] = None

class StockGiftOutboundUpdate(BaseModel):
    gift_id: Optional[int] = None; outbound_type: Optional[str] = None
    quantity: Optional[int] = None; recipient: Optional[str] = None
    recipient_organization: Optional[str] = None; outbound_date: Optional[str] = None
    notes: Optional[str] = None

class StockGiftOutboundResponse(BaseModel):
    id: int; company_id: int; gift_id: int; outbound_type: str
    quantity: int; recipient: str; recipient_organization: Optional[str] = None
    outbound_date: str; status: str; notes: Optional[str] = None
    submit_date: Optional[str] = None; created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════
# 服务器与服务管理 Schemas
# ═══════════════════════════════════════════

class ServerCreate(BaseModel):
    company_id: int
    name: str
    host: Optional[str] = None
    port: Optional[int] = None
    os: Optional[str] = None
    cpu_cores: Optional[int] = None
    memory_gb: Optional[float] = None
    disk_gb: Optional[float] = None
    location: Optional[str] = None
    description: Optional[str] = None

class ServerUpdate(BaseModel):
    name: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    os: Optional[str] = None
    cpu_cores: Optional[int] = None
    memory_gb: Optional[float] = None
    disk_gb: Optional[float] = None
    location: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None

class ServerResponse(BaseModel):
    id: int; company_id: int; name: str
    host: Optional[str] = None; port: Optional[int] = None
    os: Optional[str] = None; cpu_cores: Optional[int] = None
    memory_gb: Optional[float] = None; disk_gb: Optional[float] = None
    location: Optional[str] = None; status: str = "active"
    description: Optional[str] = None
    created_at: Optional[datetime] = None; updated_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


class ServerServiceCreate(BaseModel):
    server_id: int
    name: str
    description: Optional[str] = None
    service_type: str = "application"
    status: str = "stopped"
    port: Optional[int] = None
    health_check_url: Optional[str] = None
    process_name: Optional[str] = None
    auto_start: bool = False
    notes: Optional[str] = None

class ServerServiceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    service_type: Optional[str] = None
    port: Optional[int] = None
    health_check_url: Optional[str] = None
    process_name: Optional[str] = None
    auto_start: Optional[bool] = None
    notes: Optional[str] = None

class ServerServiceResponse(BaseModel):
    id: int; server_id: int; name: str
    description: Optional[str] = None; service_type: str = "application"
    status: str = "stopped"; port: Optional[int] = None
    health_check_url: Optional[str] = None; process_name: Optional[str] = None
    last_started_at: Optional[datetime] = None; uptime_hours: Optional[float] = None
    auto_start: bool = False; notes: Optional[str] = None
    created_at: Optional[datetime] = None; updated_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class ServerServiceStatusUpdate(BaseModel):
    action: str  # start / stop / restart


# ═══════════ 知识库分类与文章 Schemas ═══════════

class KbArticleCreate(BaseModel):
    company_id: int
    title: str
    content_md: Optional[str] = None
    category_id: int
    tags: list[str] = []
    status: str = "draft"

class KbArticleUpdate(BaseModel):
    title: Optional[str] = None
    content_md: Optional[str] = None
    category_id: Optional[int] = None
    tags: Optional[list[str]] = None
    status: Optional[str] = None

class KbArticleResponse(BaseModel):
    id: int; company_id: int; title: str
    content_md: Optional[str] = None
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    tags: Optional[str] = None; author: Optional[str] = None
    status: str = "draft"; version: int = 1
    created_at: Optional[datetime] = None; updated_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


# ═══════════ 知识库分类 Schemas ═══════════

class KbCategoryCreate(BaseModel):
    company_id: int
    name: str
    parent_id: Optional[int] = None

class KbCategoryUpdate(BaseModel):
    name: Optional[str] = None
    sort_order: Optional[int] = None

class KbCategoryResponse(BaseModel):
    id: int; company_id: int; name: str
    parent_id: Optional[int] = None; level: int = 1
    sort_order: int = 0; is_system: bool = False
    is_active: bool = True; created_by: Optional[int] = None
    created_at: Optional[datetime] = None; updated_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class KbCategoryTreeNode(BaseModel):
    id: int; name: str; level: int; is_system: bool = False
    sort_order: int = 0; article_count: int = 0
    children: list["KbCategoryTreeNode"] = []
    model_config = {"from_attributes": True}


# ═══════════ 预算管理 ═══════════

class BudgetItemCreate(BaseModel):
    account_code: str
    department_id: Optional[int] = None
    month: str  # yyyy-MM
    amount: Optional[float] = 0.0

class BudgetItemResponse(BaseModel):
    id: int
    budget_id: int
    account_code: str
    department_id: Optional[int] = None
    month: str
    amount: float = 0.0
    model_config = {"from_attributes": True}

class BudgetCreate(BaseModel):
    company_id: int
    name: str
    year: int
    items: Optional[list[BudgetItemCreate]] = []

class BudgetUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    items: Optional[list[BudgetItemCreate]] = None

class BudgetResponse(BaseModel):
    id: int
    company_id: int
    name: str
    year: int
    status: str = "draft"
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    items: list[BudgetItemResponse] = []
    model_config = {"from_attributes": True}


# ═══════════ 期末结转 ═══════════

class CarryForwardEntryCreate(BaseModel):
    company_id: int
    period: str
    entry_type: str  # revenue_to_profit / expense_to_profit / profit_to_retained
    debit_account_id: Optional[int] = None
    credit_account_id: Optional[int] = None
    amount: float = 0.0

class CarryForwardEntryResponse(BaseModel):
    id: int
    company_id: int
    period: str
    entry_type: str
    debit_account_id: Optional[int] = None
    credit_account_id: Optional[int] = None
    amount: float
    voucher_id: Optional[int] = None
    status: str
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


class CloseCheckResult(BaseModel):
    """关账检查结果"""
    period: str
    unposted_vouchers: int = 0
    unbalanced_vouchers: int = 0
    can_close: bool = False
    message: str = ""


class QuarterlyPeriodStatus(BaseModel):
    quarter: str  # Q1/Q2/Q3/Q4
    months: list[str]  # ['2026-01','2026-02','2026-03']
    closed_months: int = 0
    total_months: int = 3
    is_quarter_closed: bool = False


class YearlyPeriodStatus(BaseModel):
    year: int
    months: list[dict]  # [{"period":"2026-01","is_closed":true},...]
    closed_months: int = 0
    total_months: int = 12
    is_year_closed: bool = False


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
    template_type: str = "fixed"
    frequency: str = "manual"
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
    query_type: str
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
    range: str
    amount: float


class AgingRow(BaseModel):
    """账龄分析行"""
    counterparty_id: int
    counterparty_name: str
    total_balance: float
    buckets: list[AgingBucket]


# ──────────────── 现金流量表项目 ────────────────

class CashFlowItemCreate(BaseModel):
    company_id: int
    code: str
    name: str
    category_code: Optional[str] = None
    direction: str  # inflow / outflow
    debit_accounts: Optional[str] = None
    credit_accounts: Optional[str] = None
    is_active: bool = True


class CashFlowItemUpdate(BaseModel):
    name: Optional[str] = None
    category_code: Optional[str] = None
    direction: Optional[str] = None
    debit_accounts: Optional[str] = None
    credit_accounts: Optional[str] = None
    is_active: Optional[bool] = None


class CashFlowItemResponse(BaseModel):
    id: int
    company_id: int
    code: str
    name: str
    category_code: Optional[str] = None
    direction: Optional[str] = None
    debit_accounts: Optional[str] = None
    credit_accounts: Optional[str] = None
    is_active: bool

    model_config = {"from_attributes": True}
