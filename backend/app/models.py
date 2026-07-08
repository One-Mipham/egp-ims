"""SQLAlchemy 数据模型."""
from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(30), nullable=False, default="accountant")  # cashier/accountant/finance_manager/finance_director/super_admin
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)  # 系统管理员标识
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    company = relationship("Company", foreign_keys=[company_id])


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    short_name = Column(String(50))
    industry = Column(String(30), default="consulting")  # investment/consulting/tech_dev/ai
    internal_control_mode = Column(String(20), default="standard")  # simplified/standard/strict
    currency = Column(String(3), default="CNY")
    fiscal_year_start = Column(String(5), default="01-01")
    tax_number = Column(String(50), nullable=True)
    english_name = Column(String(200), nullable=True)
    english_short_name = Column(String(100), nullable=True)
    tax_region = Column(String(50), nullable=True)
    website = Column(String(200), nullable=True)
    email = Column(String(100), nullable=True)
    address = Column(String(200), nullable=True)
    phone = Column(String(20), nullable=True)
    contact_person = Column(String(50), nullable=True)
    module_set = Column(String(20), default="trial")  # trial/basic/advanced/pro/custom
    enabled_modules = Column(JSON, default=list)       # ["accounting","receivables",...]
    subscription_status = Column(String(20), default="trialing")  # trialing/active/past_due/cancelled/expired
    trial_ends_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    departments = relationship("Department", back_populates="company")
    projects = relationship("Project", back_populates="company")
    counterparties = relationship("Counterparty", back_populates="company")
    persons = relationship("Person", back_populates="company")
    accounts = relationship("Account", back_populates="company")
    vouchers = relationship("Voucher", back_populates="company")
    periods = relationship("AccountingPeriod", back_populates="company")
    templates = relationship("VoucherTemplate", back_populates="company")
    reports = relationship("ReportSnapshot", back_populates="company")
    budgets = relationship("Budget", back_populates="company")


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    name = Column(String(100), nullable=False)
    code = Column(String(10), nullable=False)
    is_active = Column(Boolean, default=True)
    manager = Column(String(100), nullable=True)
    parent_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)

    company = relationship("Company", back_populates="departments")
    parent = relationship("Department", remote_side="Department.id", backref="children")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    code = Column(String(20), nullable=False)
    name = Column(String(200), nullable=False)
    project_type = Column(String(20), default="product")  # product/platform/research/temp
    status = Column(String(16), default="active")  # active/paused/completed/capitalized
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    manager = Column(String(100), nullable=True)
    start_date = Column(String(10), nullable=True)
    end_date = Column(String(10), nullable=True)
    budget = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="projects")


class Counterparty(Base):
    __tablename__ = "counterparties"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    code = Column(String(20), nullable=False)
    name = Column(String(200), nullable=False)
    short_name = Column(String(100), nullable=True)
    category = Column(String(20), nullable=True)
    category_code = Column(String(20), nullable=True)
    tax_number = Column(String(50), nullable=True)
    bank_account = Column(String(50), nullable=True)
    bank_name = Column(String(100), nullable=True)
    address = Column(String(200), nullable=True)
    phone = Column(String(20), nullable=True)
    contact_person = Column(String(50), nullable=True)
    website = Column(String(200), nullable=True)
    email = Column(String(100), nullable=True)
    zip_code = Column(String(10), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="counterparties")


class Person(Base):
    __tablename__ = "persons"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    code = Column(String(20), nullable=False)
    name = Column(String(100), nullable=False)
    department_code = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="persons")


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    code = Column(String(10), nullable=False)  # 存储连续字符串如 10020101
    name = Column(String(100), nullable=False)
    level = Column(Integer, nullable=False)  # 1/2/3/4
    parent_code = Column(String(10), nullable=True)
    category = Column(String(10), nullable=False)  # asset/liability/equity/cost/profit_loss
    balance_direction = Column(String(4), nullable=False)  # debit/credit
    initial_balance = Column(Float, default=0.0)
    is_system = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    aux_dept = Column(Integer, default=0)
    aux_person = Column(Integer, default=0)
    aux_counterparty = Column(Integer, default=0)
    aux_project = Column(Integer, default=0)

    company = relationship("Company", back_populates="accounts")


class Voucher(Base):
    __tablename__ = "vouchers"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    date = Column(String(10), nullable=False)
    voucher_no = Column(String(20), nullable=False)
    voucher_type = Column(String(10), nullable=False)  # receipt/payment/transfer
    summary = Column(String(500), nullable=False)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(12), default="draft")  # draft/approved/posted/reversed
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    posted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    posted_at = Column(DateTime, nullable=True)
    reversed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reversed_at = Column(DateTime, nullable=True)
    reverse_reason = Column(String(500), nullable=True)

    company = relationship("Company", back_populates="vouchers")
    entries = relationship("VoucherEntry", back_populates="voucher", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("company_id", "voucher_no", name="uq_voucher_no"),
    )


class VoucherSequence(Base):
    """凭证序号计数器 — 按公司+类型+月份独立递增，只增不减，删除不递补。"""
    __tablename__ = "voucher_sequences"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    voucher_type = Column(String(10), nullable=False)
    period = Column(String(7), nullable=False)  # yyyy-MM
    last_seq = Column(Integer, nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint("company_id", "voucher_type", "period", name="uq_voucher_seq"),
    )


class VoucherEntry(Base):
    __tablename__ = "voucher_entries"

    id = Column(Integer, primary_key=True, index=True)
    voucher_id = Column(Integer, ForeignKey("vouchers.id"), nullable=False)
    account_code = Column(String(10), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    counterparty_id = Column(Integer, ForeignKey("counterparties.id"), nullable=True)
    person_id = Column(Integer, ForeignKey("persons.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    debit = Column(Float, default=0.0)
    credit = Column(Float, default=0.0)
    description = Column(String(500), nullable=True)

    voucher = relationship("Voucher", back_populates="entries")
    settlements = relationship("BankSettlement", back_populates="entry", cascade="all, delete-orphan")


class BankSettlement(Base):
    """银行结算明细 — 仅当分录科目为银行存款(1002)时启用。"""
    __tablename__ = "bank_settlements"

    id = Column(Integer, primary_key=True, index=True)
    voucher_entry_id = Column(Integer, ForeignKey("voucher_entries.id"), nullable=False)
    seq = Column(Integer, nullable=False)
    settlement_method = Column(String(20), nullable=False)
    account_name = Column(String(100), nullable=True)
    instrument_no = Column(String(50), nullable=True)
    instrument_date = Column(String(10), nullable=True)
    direction = Column(String(6), nullable=False, default="debit")  # debit / credit
    amount = Column(Float, default=0.0)

    entry = relationship("VoucherEntry", back_populates="settlements")


class AccountingPeriod(Base):
    __tablename__ = "accounting_periods"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    period = Column(String(7), nullable=False)  # yyyy-MM
    is_closed = Column(Boolean, default=False)
    closed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    closed_at = Column(DateTime, nullable=True)
    closed_status = Column(String(10), default="open")  # open/closing/closed

    company = relationship("Company", back_populates="periods")


class VoucherTemplate(Base):
    __tablename__ = "voucher_templates"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)  # NULL = built-in
    name = Column(String(100), nullable=False)
    type = Column(String(20), default="user_defined")  # built_in/user_defined
    entries = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    company = relationship("Company", back_populates="templates")


class ReportSnapshot(Base):
    __tablename__ = "report_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    period = Column(String(10), nullable=False)
    period_type = Column(String(16), default="monthly")  # monthly/quarterly/semiannual/annual
    type = Column(String(16), nullable=False)  # balance/income/cashflow
    data = Column(JSON, nullable=False)
    generated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    generated_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="reports")


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    name = Column(String(100), nullable=False)  # 如"2026年度预算"
    year = Column(Integer, nullable=False)
    status = Column(String(10), default="draft")  # draft/approved
    revenue_growth_rate = Column(Float, nullable=True)  # 收入增长率 %
    manual_adjustment = Column(Float, nullable=True)  # 手动调整额
    cost_rate = Column(Float, nullable=True)  # 成本占收入比 %
    operating_exp_rate = Column(Float, nullable=True)  # 经营费用占收入比 %
    admin_exp_rate = Column(Float, nullable=True)  # 管理费用占收入比 %
    finance_exp_rate = Column(Float, nullable=True)  # 财务费用占收入比 %
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="budgets")
    items = relationship("BudgetItem", back_populates="budget", cascade="all, delete-orphan")


class BudgetItem(Base):
    __tablename__ = "budget_items"

    id = Column(Integer, primary_key=True, index=True)
    budget_id = Column(Integer, ForeignKey("budgets.id"), nullable=False)
    account_code = Column(String(10), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    month = Column(String(7), nullable=False)  # yyyy-MM
    amount = Column(Float, default=0.0)

    budget = relationship("Budget", back_populates="items")


class CashflowPlan(Base):
    __tablename__ = "cashflow_plans"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    name = Column(String(100), nullable=False)
    year = Column(Integer, nullable=False)
    status = Column(String(10), default="draft")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company")
    items = relationship("CashflowPlanItem", back_populates="plan", cascade="all, delete-orphan")


class CashflowPlanItem(Base):
    __tablename__ = "cashflow_plan_items"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("cashflow_plans.id"), nullable=False)
    account_code = Column(String(10), nullable=False)
    month = Column(String(7), nullable=False)  # yyyy-MM
    amount = Column(Float, default=0.0)

    plan = relationship("CashflowPlan", back_populates="items")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(30), nullable=False)
    target_type = Column(String(20), nullable=False)
    target_id = Column(Integer, nullable=True)
    reason = Column(String(500), nullable=True)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class UserPermission(Base):
    __tablename__ = "user_permissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    # 凭证类
    voucher_create = Column(Boolean, default=True)
    voucher_edit = Column(Boolean, default=True)
    voucher_delete = Column(Boolean, default=False)
    voucher_post = Column(Boolean, default=True)
    voucher_reverse = Column(Boolean, default=False)
    # 期间类
    period_close = Column(Boolean, default=False)
    period_unclose = Column(Boolean, default=False)
    # 查询类
    view_detail_ledger = Column(Boolean, default=True)
    view_general_ledger = Column(Boolean, default=True)
    view_reports = Column(Boolean, default=True)


class InvestmentPortfolio(Base):
    __tablename__ = "investment_portfolios"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    name = Column(String(200), nullable=False)
    investment_type = Column(String(20), nullable=False, default="general_equity")  # vc/pe/angel/general_equity/secondary_market/fixed_income/mutual_fund/private_fund/etf/alternative/real_estate/infrastructure/private_credit/commodity/digital_asset/trust/derivatives
    currency = Column(String(3), default="CNY")
    status = Column(String(16), default="active")  # active/closed/liquidated
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    positions = relationship("InvestmentPosition", back_populates="portfolio", cascade="all, delete-orphan")


class InvestmentPosition(Base):
    __tablename__ = "investment_positions"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("investment_portfolios.id"), nullable=False)
    account_code = Column(String(10), nullable=False)
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
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
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


class SecurityMaster(Base):
    """证券主数据"""
    __tablename__ = "securities_master"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    security_code = Column(String(50), nullable=False, comment="证券代码")
    security_name = Column(String(200), nullable=False, comment="证券名称")
    security_type = Column(String(30), default="equity", comment="equity/bond/fund/etf/derivative/commodity/forex")
    exchange = Column(String(20), nullable=True, comment="SSE/SZSE/SEHK/NYSE/NASDAQ")
    currency = Column(String(3), default="CNY")
    isin_code = Column(String(20), nullable=True)
    status = Column(String(16), default="active", comment="active/inactive/delisted")
    created_at = Column(DateTime, default=datetime.utcnow)


class InvestmentFund(Base):
    """基金管理"""
    __tablename__ = "investment_funds"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    fund_name = Column(String(200), nullable=False)
    fund_type = Column(String(20), default="private_fund", comment="private_fund/hedge_fund/fof/trust_plan")
    management_company = Column(String(200), nullable=True)
    inception_date = Column(String(10), nullable=True)
    currency = Column(String(3), default="CNY")
    total_commitment = Column(Float, default=0.0, comment="总规模/承诺出资")
    portfolio_id = Column(Integer, ForeignKey("investment_portfolios.id"), nullable=True)
    status = Column(String(16), default="active", comment="raising/active/liquidating/liquidated")
    created_at = Column(DateTime, default=datetime.utcnow)

    capital_accounts = relationship("CapitalAccount", back_populates="fund", cascade="all, delete-orphan")
    capital_calls = relationship("CapitalCall", back_populates="fund", cascade="all, delete-orphan")
    distributions = relationship("FundDistribution", back_populates="fund", cascade="all, delete-orphan")


class CapitalAccount(Base):
    """LP资本账户"""
    __tablename__ = "capital_accounts"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    fund_id = Column(Integer, ForeignKey("investment_funds.id"), nullable=False)
    investor_id = Column(Integer, ForeignKey("counterparties.id"), nullable=False)
    committed_capital = Column(Float, default=0.0)
    called_capital = Column(Float, default=0.0)
    ownership_pct = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    fund = relationship("InvestmentFund", back_populates="capital_accounts")


class CapitalCall(Base):
    """资本召唤/出资通知"""
    __tablename__ = "capital_calls"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    fund_id = Column(Integer, ForeignKey("investment_funds.id"), nullable=False)
    call_date = Column(String(10), nullable=False)
    call_amount = Column(Float, default=0.0)
    due_date = Column(String(10), nullable=True)
    status = Column(String(16), default="pending", comment="pending/paid/overdue")
    notes = Column(Text, nullable=True)
    voucher_id = Column(Integer, ForeignKey("vouchers.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    fund = relationship("InvestmentFund", back_populates="capital_calls")


class FundDistribution(Base):
    """基金分配"""
    __tablename__ = "fund_distributions"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    fund_id = Column(Integer, ForeignKey("investment_funds.id"), nullable=False)
    distribution_date = Column(String(10), nullable=False)
    amount = Column(Float, default=0.0)
    distribution_type = Column(String(20), default="income", comment="return_of_capital/income/carry")
    notes = Column(Text, nullable=True)
    voucher_id = Column(Integer, ForeignKey("vouchers.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    fund = relationship("InvestmentFund", back_populates="distributions")


class WaterfallConfig(Base):
    """分配瀑布配置"""
    __tablename__ = "waterfall_configs"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    name = Column(String(200), nullable=False)
    portfolio_id = Column(Integer, ForeignKey("investment_portfolios.id"), nullable=True)
    tiers = Column(JSON, default=list, comment="[{order, name, type, threshold_pct, gp_share_pct, lp_share_pct}]")
    created_at = Column(DateTime, default=datetime.utcnow)


class RealEstateAsset(Base):
    """房地产资产"""
    __tablename__ = "real_estate_assets"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    property_name = Column(String(200), nullable=False)
    property_type = Column(String(20), default="commercial", comment="commercial/residential/industrial/land/mixed")
    location = Column(String(200), nullable=True)
    acquisition_date = Column(String(10), nullable=True)
    acquisition_cost = Column(Float, default=0.0)
    current_value = Column(Float, default=0.0)
    valuation_date = Column(String(10), nullable=True)
    area_sqm = Column(Float, default=0.0, comment="建筑面积(m²)")
    occupancy_pct = Column(Float, default=0.0, comment="出租率%")
    annual_rental_income = Column(Float, default=0.0)
    portfolio_id = Column(Integer, ForeignKey("investment_portfolios.id"), nullable=True)
    status = Column(String(16), default="active", comment="active/sold/under_renovation")
    created_at = Column(DateTime, default=datetime.utcnow)

    valuations = relationship("RealEstateValuation", back_populates="asset", cascade="all, delete-orphan")


class RealEstateValuation(Base):
    """房地产估值记录"""
    __tablename__ = "real_estate_valuations"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    asset_id = Column(Integer, ForeignKey("real_estate_assets.id"), nullable=False)
    valuation_date = Column(String(10), nullable=False)
    value = Column(Float, default=0.0)
    valuation_method = Column(String(30), default="comparable", comment="comparable/cost/income/dcf")
    appraiser = Column(String(100), nullable=True, comment="评估机构")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    asset = relationship("RealEstateAsset", back_populates="valuations")


class InfraAsset(Base):
    """基础设施资产"""
    __tablename__ = "infra_assets"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    project_name = Column(String(200), nullable=False)
    asset_type = Column(String(20), default="energy", comment="energy/transport/utilities/telecom/social/ppp")
    location = Column(String(200), nullable=True)
    investment_date = Column(String(10), nullable=True)
    investment_amount = Column(Float, default=0.0)
    current_value = Column(Float, default=0.0)
    valuation_date = Column(String(10), nullable=True)
    annual_revenue = Column(Float, default=0.0)
    concession_expiry = Column(String(10), nullable=True, comment="特许经营到期日")
    portfolio_id = Column(Integer, ForeignKey("investment_portfolios.id"), nullable=True)
    status = Column(String(16), default="operational", comment="development/operational/harvesting/sold")
    created_at = Column(DateTime, default=datetime.utcnow)


class PrivateCredit(Base):
    """私募信贷资产"""
    __tablename__ = "private_credits"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    borrower_name = Column(String(200), nullable=False)
    instrument_type = Column(String(20), default="senior_secured", comment="senior_secured/mezzanine/unitranche/subordinated/bridge")
    principal_amount = Column(Float, default=0.0)
    interest_rate = Column(Float, default=0.0, comment="年利率%")
    origination_date = Column(String(10), nullable=True)
    maturity_date = Column(String(10), nullable=True)
    outstanding_principal = Column(Float, default=0.0)
    accrued_interest = Column(Float, default=0.0)
    credit_rating = Column(String(10), nullable=True, comment="AAA/AA/A/BBB/BB/B/CCC/D")
    collateral = Column(String(200), nullable=True)
    counterparty_id = Column(Integer, ForeignKey("counterparties.id"), nullable=True)
    status = Column(String(16), default="performing", comment="performing/watchlist/non_performing/restructured/repaid")
    created_at = Column(DateTime, default=datetime.utcnow)

    payments = relationship("CreditPayment", back_populates="credit", cascade="all, delete-orphan")


class CreditPayment(Base):
    """信贷还款记录"""
    __tablename__ = "credit_payments"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    credit_id = Column(Integer, ForeignKey("private_credits.id"), nullable=False)
    payment_date = Column(String(10), nullable=False)
    payment_type = Column(String(20), default="interest", comment="interest/principal/fee")
    amount = Column(Float, default=0.0)
    voucher_id = Column(Integer, ForeignKey("vouchers.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    credit = relationship("PrivateCredit", back_populates="payments")


class InitContract(Base):
    __tablename__ = "init_contracts"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    contract_no = Column(String(50), nullable=False)
    counterparty_id = Column(Integer, ForeignKey("counterparties.id"), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    subject = Column(String(300), nullable=True)
    amount = Column(Float, default=0.0)
    sign_date = Column(String(10), nullable=True)
    status = Column(String(16), default="active")  # active/completed/terminated
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class InitInvoice(Base):
    __tablename__ = "init_invoices"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    invoice_no = Column(String(50), nullable=False)
    invoice_type = Column(String(20), default="vat_special")  # vat_special/vat_normal/electronic
    counterparty_id = Column(Integer, ForeignKey("counterparties.id"), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    amount = Column(Float, default=0.0)
    invoice_date = Column(String(10), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ═══════════════════════════════════════════
# 基础档案 (Basic Master Data) — 从原系统导入
# ═══════════════════════════════════════════

class Region(Base):
    """地区"""
    __tablename__ = "regions"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    code = Column(String(20), nullable=False)
    name = Column(String(100), nullable=False)
    parent_code = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True)


class Warehouse(Base):
    """仓库"""
    __tablename__ = "warehouses"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    code = Column(String(20), nullable=False)
    name = Column(String(100), nullable=False)
    manager_code = Column(String(20), nullable=True)
    manager_name = Column(String(50), nullable=True)
    address = Column(String(200), nullable=True)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)


class UnitOfMeasure(Base):
    """计量单位"""
    __tablename__ = "units_of_measure"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    group_name = Column(String(50), nullable=False)
    unit_name = Column(String(50), nullable=False)
    is_primary = Column(Boolean, default=False)
    conversion_type = Column(String(10), nullable=True)  # fixed/float
    conversion_rate = Column(Float, nullable=True)
    notes = Column(String(200), nullable=True)


class SettlementMethod(Base):
    """结算方式"""
    __tablename__ = "settlement_methods"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    code = Column(String(20), nullable=False)
    name = Column(String(50), nullable=False)
    default_account = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)


class BankAccount(Base):
    """银行账号"""
    __tablename__ = "bank_accounts"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    code = Column(String(20), nullable=False)
    name = Column(String(100), nullable=False)
    account_type = Column(String(10), default="bank")  # bank/cash/other
    bank_name = Column(String(100), nullable=True)
    account_number = Column(String(50), nullable=True)
    currency = Column(String(5), default="CNY")
    is_active = Column(Boolean, default=True)


class InventoryCategory(Base):
    """存货分类"""
    __tablename__ = "inventory_categories"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    code = Column(String(20), nullable=False)
    name = Column(String(100), nullable=False)
    parent_code = Column(String(20), nullable=True)
    auto_create_project = Column(Boolean, default=False)


class Inventory(Base):
    """存货"""
    __tablename__ = "inventory"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    code = Column(String(20), nullable=False)
    name = Column(String(200), nullable=False)
    category_code = Column(String(20), nullable=True)
    specs = Column(String(200), nullable=True)
    unit = Column(String(20), nullable=True)
    unit_group = Column(String(50), nullable=True)
    tax_rate = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)


class ExpenseItem(Base):
    """费用项目"""
    __tablename__ = "expense_items"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    code = Column(String(20), nullable=False)
    name = Column(String(100), nullable=False)
    parent_code = Column(String(20), nullable=True)
    tax_rate = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True)


class RevenueItem(Base):
    """收入项目"""
    __tablename__ = "revenue_items"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    code = Column(String(20), nullable=False)
    name = Column(String(100), nullable=False)
    parent_code = Column(String(20), nullable=True)
    tax_rate = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True)


class CashFlowCategory(Base):
    """现金流量项目分类"""
    __tablename__ = "cashflow_categories"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    code = Column(String(20), nullable=False)
    name = Column(String(100), nullable=False)
    parent_code = Column(String(20), nullable=True)


class CashFlowItem(Base):
    """现金流量项目"""
    __tablename__ = "cashflow_items"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    code = Column(String(20), nullable=False)
    name = Column(String(100), nullable=False)
    category_code = Column(String(20), nullable=True)
    direction = Column(String(10), nullable=True)  # inflow/outflow
    debit_accounts = Column(String(500), nullable=True)  # comma-separated codes
    credit_accounts = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)


# ═══════════════════════════════════════════
# 人力资源管理模块
# ═══════════════════════════════════════════

class HrPolicy(Base):
    """公司人力资源管理制度文档"""
    __tablename__ = "hr_policies"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class HrPosition(Base):
    """职级数据库"""
    __tablename__ = "hr_positions"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    name = Column(String(50), nullable=False)
    level = Column(Integer, nullable=False)  # 1董事会 2监事会 3管理层 4部门正职 5部门副职 6中层 7基层
    sort_order = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)


class HrEmployee(Base):
    """员工信息表"""
    __tablename__ = "hr_employees"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    employee_code = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    gender = Column(String(4), nullable=True)
    birth_date = Column(String(10), nullable=True)
    id_card = Column(String(18), nullable=True)
    passport = Column(String(50), nullable=True)
    native_place = Column(String(100), nullable=True)
    graduate_school = Column(String(100), nullable=True)
    graduate_date = Column(String(10), nullable=True)
    major = Column(String(100), nullable=True)
    career_history = Column(Text, nullable=True)
    expertise = Column(String(200), nullable=True)
    mobile = Column(String(20), nullable=True)
    personal_email = Column(String(100), nullable=True)
    company_email = Column(String(100), nullable=True)
    emergency_contact = Column(String(100), nullable=True)
    home_address = Column(String(200), nullable=True)
    nationality = Column(String(50), nullable=True)
    political_party = Column(String(50), nullable=True)
    religion = Column(String(50), nullable=True)
    professional_associations = Column(String(200), nullable=True)
    certifications = Column(Text, nullable=True)
    position_id = Column(Integer, ForeignKey("hr_positions.id"), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    status = Column(String(10), nullable=False, default="在职")  # 在职/试用/离职
    hire_date = Column(String(10), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    position = relationship("HrPosition")
    department = relationship("Department")


class HrTraining(Base):
    """员工培训"""
    __tablename__ = "hr_trainings"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("hr_employees.id"), nullable=False)
    training_name = Column(String(200), nullable=False)
    training_date = Column(String(10), nullable=True)
    provider = Column(String(100), nullable=True)
    cost = Column(Float, nullable=True)
    status = Column(String(10), nullable=False, default="计划中")
    notes = Column(Text, nullable=True)

    employee = relationship("HrEmployee")


class HrEvaluation(Base):
    """员工考核"""
    __tablename__ = "hr_evaluations"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("hr_employees.id"), nullable=False)
    period = Column(String(10), nullable=True)
    score = Column(Float, nullable=True)
    grade = Column(String(10), nullable=True)
    evaluator = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    employee = relationship("HrEmployee")


class HrSalary(Base):
    """薪酬管理"""
    __tablename__ = "hr_salaries"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("hr_employees.id"), nullable=False)
    year_month = Column(String(7), nullable=False)
    base_salary = Column(Float, default=0)
    bonus = Column(Float, default=0)
    allowance = Column(Float, default=0)
    deduction = Column(Float, default=0)
    net_salary = Column(Float, default=0)
    notes = Column(Text, nullable=True)

    employee = relationship("HrEmployee")


class HrRewardPunishment(Base):
    """员工奖惩"""
    __tablename__ = "hr_rewards_punishments"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("hr_employees.id"), nullable=False)
    type = Column(String(4), nullable=False)  # 奖励/惩罚
    date = Column(String(10), nullable=True)
    description = Column(Text, nullable=True)
    amount = Column(Float, nullable=True)
    approved_by = Column(String(50), nullable=True)

    employee = relationship("HrEmployee")


class HrOffboarding(Base):
    """员工离职"""
    __tablename__ = "hr_offboarding"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("hr_employees.id"), nullable=False)
    apply_date = Column(String(10), nullable=True)
    last_day = Column(String(10), nullable=True)
    reason = Column(Text, nullable=True)
    handover_to = Column(String(100), nullable=True)
    status = Column(String(10), nullable=False, default="申请")  # 申请/审批中/已批准/已离职
    notes = Column(Text, nullable=True)

    employee = relationship("HrEmployee")


class HrBudget(Base):
    """人力资源预算"""
    __tablename__ = "hr_budgets"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    year = Column(Integer, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    headcount_planned = Column(Integer, default=0)
    headcount_actual = Column(Integer, default=0)
    salary_budget = Column(Float, default=0)
    training_budget = Column(Float, default=0)
    recruitment_budget = Column(Float, default=0)
    total_budget = Column(Float, default=0)
    notes = Column(Text, nullable=True)


# ═══════════ 固定资产管理 ═══════════

class FixedAsset(Base):
    __tablename__ = "fixed_assets"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    asset_code = Column(String(50), nullable=False, comment="资产编号")
    name = Column(String(200), nullable=False, comment="资产名称")
    category = Column(String(50), nullable=False, default="设备", comment="资产类别")
    acquisition_date = Column(String(10), nullable=True, comment="购置日期")
    original_value = Column(Float, nullable=False, default=0, comment="原值")
    residual_value = Column(Float, nullable=False, default=0, comment="残值")
    useful_life = Column(Integer, nullable=False, default=5, comment="使用年限(年)")
    depreciation_method = Column(String(20), nullable=False, default="直线法", comment="折旧方法")
    monthly_depreciation = Column(Float, nullable=False, default=0, comment="月折旧额")
    accumulated_depreciation = Column(Float, nullable=False, default=0, comment="累计折旧")
    net_value = Column(Float, nullable=False, default=0, comment="净值")
    status = Column(String(20), nullable=False, default="使用中", comment="使用中/已处置/报废")
    location = Column(String(200), nullable=True, comment="存放地点")
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    disposal_date = Column(String(10), nullable=True, comment="处置日期")
    disposal_proceeds = Column(Float, nullable=False, default=0, comment="处置收入")
    disposal_gain_loss = Column(Float, nullable=False, default=0, comment="处置损益")
    disposal_reason = Column(Text, nullable=True, comment="处置原因")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    department = relationship("Department")


class FixedAssetDepreciation(Base):
    __tablename__ = "fixed_asset_depreciations"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    fixed_asset_id = Column(Integer, ForeignKey("fixed_assets.id"), nullable=False)
    period = Column(String(7), nullable=False, comment="折旧期间 YYYY-MM")
    depreciation_amount = Column(Float, nullable=False, default=0, comment="本期折旧额")
    accumulated_before = Column(Float, nullable=False, default=0, comment="计提前累计")
    accumulated_after = Column(Float, nullable=False, default=0, comment="计提后累计")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    fixed_asset = relationship("FixedAsset")


# ═══════════ 应收账款管理 ═══════════

class Receivable(Base):
    __tablename__ = "receivables"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    customer_name = Column(String(200), nullable=False, comment="客户名称")
    invoice_no = Column(String(100), nullable=False, comment="发票号")
    invoice_date = Column(String(10), nullable=True, comment="发票日期")
    amount = Column(Float, nullable=False, default=0, comment="应收金额")
    received_amount = Column(Float, nullable=False, default=0, comment="已收金额")
    balance = Column(Float, nullable=False, default=0, comment="余额")
    due_date = Column(String(10), nullable=True, comment="到期日")
    aging_days = Column(Integer, nullable=False, default=0, comment="账龄(天)")
    status = Column(String(20), nullable=False, default="未收款", comment="未收款/部分收款/已收款/坏账")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ReceivablePayment(Base):
    __tablename__ = "receivable_payments"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    receivable_id = Column(Integer, ForeignKey("receivables.id"), nullable=False)
    payment_date = Column(String(10), nullable=False)
    amount = Column(Float, nullable=False, default=0)
    payment_method = Column(String(50), nullable=True, comment="银行转账/现金/承兑汇票")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    receivable = relationship("Receivable")


# ═══════════ 应付账款管理 ═══════════

class Payable(Base):
    __tablename__ = "payables"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    supplier_name = Column(String(200), nullable=False, comment="供应商名称")
    invoice_no = Column(String(100), nullable=False, comment="发票号")
    invoice_date = Column(String(10), nullable=True, comment="发票日期")
    amount = Column(Float, nullable=False, default=0, comment="应付金额")
    paid_amount = Column(Float, nullable=False, default=0, comment="已付金额")
    balance = Column(Float, nullable=False, default=0, comment="余额")
    due_date = Column(String(10), nullable=True, comment="到期日")
    aging_days = Column(Integer, nullable=False, default=0, comment="账龄(天)")
    status = Column(String(20), nullable=False, default="未付款", comment="未付款/部分付款/已付款")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PayablePayment(Base):
    __tablename__ = "payable_payments"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    payable_id = Column(Integer, ForeignKey("payables.id"), nullable=False)
    payment_date = Column(String(10), nullable=False)
    amount = Column(Float, nullable=False, default=0)
    payment_method = Column(String(50), nullable=True, comment="银行转账/现金/承兑汇票")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    payable = relationship("Payable")


# ═══════════ 进销存管理 ═══════════

class InvPurchase(Base):
    __tablename__ = "inv_purchases"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    order_no = Column(String(100), nullable=False, comment="采购单号")
    supplier_name = Column(String(200), nullable=False)
    order_date = Column(String(10), nullable=True)
    product_name = Column(String(200), nullable=False)
    quantity = Column(Float, nullable=False, default=0)
    unit = Column(String(20), nullable=False, default="个")
    unit_price = Column(Float, nullable=False, default=0)
    total_amount = Column(Float, nullable=False, default=0)
    status = Column(String(20), nullable=False, default="待入库")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class InvSale(Base):
    __tablename__ = "inv_sales"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    order_no = Column(String(100), nullable=False, comment="销售单号")
    customer_name = Column(String(200), nullable=False)
    order_date = Column(String(10), nullable=True)
    product_name = Column(String(200), nullable=False)
    quantity = Column(Float, nullable=False, default=0)
    unit = Column(String(20), nullable=False, default="个")
    unit_price = Column(Float, nullable=False, default=0)
    total_amount = Column(Float, nullable=False, default=0)
    cost_amount = Column(Float, nullable=False, default=0, comment="成本金额")
    profit = Column(Float, nullable=False, default=0, comment="毛利")
    status = Column(String(20), nullable=False, default="待出库")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class InvStock(Base):
    __tablename__ = "inv_stocks"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    product_code = Column(String(100), nullable=False)
    product_name = Column(String(200), nullable=False)
    category = Column(String(50), nullable=True)
    quantity = Column(Float, nullable=False, default=0)
    unit = Column(String(20), nullable=False, default="个")
    unit_cost = Column(Float, nullable=False, default=0)
    total_cost = Column(Float, nullable=False, default=0)
    warehouse = Column(String(100), nullable=True)
    min_stock = Column(Float, nullable=False, default=0, comment="最低库存")
    max_stock = Column(Float, nullable=False, default=0, comment="最高库存")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ── 行政综合管理系统 (Admin Management System) ──

class ApprovalRecord(Base):
    __tablename__ = "approval_records"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    target_type = Column(String(30), nullable=False)
    target_id = Column(Integer, nullable=False)
    step = Column(Integer, nullable=False)
    approver_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approver_name = Column(String(100), nullable=True)
    status = Column(String(20), default="pending")
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AdminDocument(Base):
    __tablename__ = "admin_documents"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    title = Column(String(200), nullable=False)
    document_number = Column(String(50), nullable=False)
    issuing_department = Column(String(100), nullable=False)
    recipient_departments = Column(String(500), nullable=True)
    priority = Column(String(10), default="普通")
    content = Column(Text, nullable=True)
    attachment_path = Column(String(300), nullable=True)
    issuance_date = Column(String(10), nullable=True)
    applicant_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    applicant_name = Column(String(100), nullable=False)
    status = Column(String(20), default="draft")
    submit_date = Column(String(10), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class VehicleSupplier(Base):
    __tablename__ = "vehicle_suppliers"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    name = Column(String(100), nullable=False)
    contact_person = Column(String(50), nullable=True)
    contact_phone = Column(String(30), nullable=True)
    brands_carried = Column(String(300), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class VehiclePurchase(Base):
    __tablename__ = "vehicle_purchases"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    applicant = Column(String(100), nullable=False)
    department = Column(String(100), nullable=False)
    vehicle_brand = Column(String(100), nullable=False)
    vehicle_model = Column(String(100), nullable=False)
    configuration = Column(Text, nullable=True)
    estimated_price = Column(Float, nullable=False, default=0)
    supplier_name = Column(String(100), nullable=True)
    supplier_contact = Column(String(200), nullable=True)
    reason = Column(Text, nullable=True)
    status = Column(String(20), default="draft")
    submit_date = Column(String(10), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Vehicle(Base):
    __tablename__ = "vehicles"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    license_plate = Column(String(20), nullable=False)
    engine_number = Column(String(50), nullable=True)
    vin = Column(String(50), nullable=True)
    brand = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    insurance_provider = Column(String(100), nullable=True)
    insurance_policy_no = Column(String(50), nullable=True)
    insurance_expiry = Column(String(10), nullable=True)
    insurance_doc_path = Column(String(300), nullable=True)
    purchase_date = Column(String(10), nullable=True)
    purchase_price = Column(Float, default=0)
    status = Column(String(20), default="使用中")
    department = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class VehicleMaintenance(Base):
    __tablename__ = "vehicle_maintenances"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    maintenance_type = Column(String(20), nullable=False)
    vendor = Column(String(100), nullable=False)
    estimated_cost = Column(Float, nullable=False, default=0)
    actual_cost = Column(Float, nullable=True)
    description = Column(Text, nullable=True)
    status = Column(String(20), default="draft")
    submit_date = Column(String(10), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class InsurancePolicy(Base):
    __tablename__ = "insurance_policies"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    policy_type = Column(String(30), nullable=False)
    insured_assets = Column(Text, nullable=False)
    insurance_company = Column(String(100), nullable=False)
    coverage_amount = Column(Float, nullable=False, default=0)
    premium = Column(Float, nullable=False, default=0)
    start_date = Column(String(10), nullable=False)
    end_date = Column(String(10), nullable=False)
    status = Column(String(20), default="draft")
    submit_date = Column(String(10), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class StockCategory(Base):
    __tablename__ = "stock_categories"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    name = Column(String(50), nullable=False)
    code = Column(String(20), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class StockAsset(Base):
    __tablename__ = "stock_assets"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    asset_code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    category_id = Column(Integer, ForeignKey("stock_categories.id"), nullable=True)
    brand = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    department = Column(String(100), nullable=True)
    custodian = Column(String(50), nullable=True)
    location = Column(String(200), nullable=True)
    purchase_date = Column(String(10), nullable=True)
    purchase_price = Column(Float, default=0)
    status = Column(String(20), default="使用中")
    quantity = Column(Integer, default=1)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class StockPurchase(Base):
    __tablename__ = "stock_purchases"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    applicant = Column(String(100), nullable=False)
    department = Column(String(100), nullable=False)
    asset_name = Column(String(200), nullable=False)
    category = Column(String(50), nullable=True)
    quantity = Column(Integer, default=1)
    estimated_price = Column(Float, nullable=False, default=0)
    reason = Column(Text, nullable=True)
    status = Column(String(20), default="draft")
    submit_date = Column(String(10), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class StockRequisition(Base):
    __tablename__ = "stock_requisitions"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    asset_id = Column(Integer, ForeignKey("stock_assets.id"), nullable=True)
    applicant = Column(String(100), nullable=False)
    department = Column(String(100), nullable=False)
    quantity = Column(Integer, default=1)
    reason = Column(Text, nullable=True)
    status = Column(String(20), default="draft")
    submit_date = Column(String(10), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class StockInbound(Base):
    __tablename__ = "stock_inbound"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    asset_id = Column(Integer, ForeignKey("stock_assets.id"), nullable=True)
    inbound_type = Column(String(20), default="采购入库")
    quantity = Column(Integer, default=1)
    receiver = Column(String(50), nullable=False)
    inbound_date = Column(String(10), nullable=False)
    status = Column(String(20), default="draft")
    notes = Column(Text, nullable=True)
    submit_date = Column(String(10), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class StockOutbound(Base):
    __tablename__ = "stock_outbound"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    asset_id = Column(Integer, ForeignKey("stock_assets.id"), nullable=False)
    outbound_type = Column(String(20), default="领用")
    quantity = Column(Integer, default=1)
    recipient = Column(String(50), nullable=False)
    outbound_date = Column(String(10), nullable=False)
    status = Column(String(20), default="draft")
    notes = Column(Text, nullable=True)
    submit_date = Column(String(10), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class StockCount(Base):
    __tablename__ = "stock_counts"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    count_date = Column(String(10), nullable=False)
    asset_id = Column(Integer, ForeignKey("stock_assets.id"), nullable=False)
    book_quantity = Column(Integer, default=0)
    actual_quantity = Column(Integer, default=0)
    discrepancy = Column(Integer, default=0)
    reason = Column(Text, nullable=True)
    counter = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class GiftCategory(Base):
    __tablename__ = "gift_categories"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    name = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class StockGift(Base):
    __tablename__ = "stock_gifts"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    name = Column(String(200), nullable=False)
    category_id = Column(Integer, ForeignKey("gift_categories.id"), nullable=True)
    unit = Column(String(20), default="个")
    current_stock = Column(Integer, default=0)
    unit_price = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class StockGiftPurchase(Base):
    __tablename__ = "stock_gift_purchases"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    gift_id = Column(Integer, ForeignKey("stock_gifts.id"), nullable=True)
    applicant = Column(String(100), nullable=False)
    department = Column(String(100), nullable=False)
    gift_name = Column(String(200), nullable=False)
    quantity = Column(Integer, default=0)
    unit_price = Column(Float, default=0)
    total_price = Column(Float, default=0)
    supplier = Column(String(100), nullable=True)
    reason = Column(Text, nullable=True)
    status = Column(String(20), default="draft")
    submit_date = Column(String(10), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class StockGiftRequisition(Base):
    __tablename__ = "stock_gift_requisitions"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    gift_id = Column(Integer, ForeignKey("stock_gifts.id"), nullable=True)
    applicant = Column(String(100), nullable=False)
    department = Column(String(100), nullable=False)
    quantity = Column(Integer, default=0)
    recipient = Column(String(100), nullable=True)
    recipient_organization = Column(String(200), nullable=True)
    reason = Column(Text, nullable=True)
    status = Column(String(20), default="draft")
    submit_date = Column(String(10), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class StockGiftInbound(Base):
    __tablename__ = "stock_gift_inbound"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    gift_id = Column(Integer, ForeignKey("stock_gifts.id"), nullable=False)
    inbound_type = Column(String(20), default="采购")
    quantity = Column(Integer, default=0)
    unit_price = Column(Float, default=0)
    supplier = Column(String(100), nullable=True)
    inbound_date = Column(String(10), nullable=False)
    receiver = Column(String(50), nullable=False)
    status = Column(String(20), default="draft")
    notes = Column(Text, nullable=True)
    submit_date = Column(String(10), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class StockGiftOutbound(Base):
    __tablename__ = "stock_gift_outbound"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    gift_id = Column(Integer, ForeignKey("stock_gifts.id"), nullable=False)
    outbound_type = Column(String(20), default="赠送")
    quantity = Column(Integer, default=0)
    recipient = Column(String(100), nullable=False)
    recipient_organization = Column(String(200), nullable=True)
    outbound_date = Column(String(10), nullable=False)
    status = Column(String(20), default="draft")
    notes = Column(Text, nullable=True)
    submit_date = Column(String(10), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ═══════════════════════════════════════════
# 服务器与服务管理
# ═══════════════════════════════════════════

class Server(Base):
    """物理/虚拟服务器"""
    __tablename__ = "servers"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    name = Column(String(100), nullable=False, comment="服务器名称")
    host = Column(String(200), nullable=True, comment="IP/域名")
    port = Column(Integer, nullable=True, comment="管理端口")
    os = Column(String(100), nullable=True, comment="操作系统")
    cpu_cores = Column(Integer, nullable=True, comment="CPU核心数")
    memory_gb = Column(Float, nullable=True, comment="内存(GB)")
    disk_gb = Column(Float, nullable=True, comment="磁盘(GB)")
    location = Column(String(100), nullable=True, comment="物理位置/云区域")
    status = Column(String(20), default="active", comment="active/inactive/maintenance")
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    services = relationship("ServerService", back_populates="server", cascade="all, delete-orphan")


class ServerService(Base):
    """服务器上运行的服务"""
    __tablename__ = "server_services"

    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, ForeignKey("servers.id"), nullable=False)
    name = Column(String(100), nullable=False, comment="服务名称")
    description = Column(String(300), nullable=True, comment="服务描述")
    service_type = Column(String(30), nullable=False, default="application",
                          comment="服务类型: its/application/task/update/database/gateway/monitoring/other")
    status = Column(String(20), default="stopped",
                    comment="运行状态: running/stopped/error/starting/stopping")
    port = Column(Integer, nullable=True, comment="服务端口")
    health_check_url = Column(String(300), nullable=True, comment="健康检查地址")
    process_name = Column(String(100), nullable=True, comment="进程名/docker容器名")
    last_started_at = Column(DateTime, nullable=True, comment="最近启动时间")
    uptime_hours = Column(Float, nullable=True, comment="运行时长(小时)")
    auto_start = Column(Boolean, default=False, comment="是否开机自启")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    server = relationship("Server", back_populates="services")


# ═══════════ 知识库管理 ═══════════

class KbArticle(Base):
    __tablename__ = "kb_articles"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    title = Column(String(300), nullable=False, comment="文章标题")
    content_md = Column(Text, nullable=True, comment="Markdown 正文")
    category = Column(String(30), default="inbox", nullable=True, comment="[已废弃] 改用 category_id")
    category_id = Column(Integer, ForeignKey("kb_categories.id"), nullable=True, comment="分类ID（新树形结构）")
    tags = Column(String(500), nullable=True, comment="标签，逗号分隔")
    author = Column(String(100), nullable=True, comment="作者")
    status = Column(String(20), nullable=False, default="draft", comment="draft/published/archived")
    version = Column(Integer, nullable=False, default=1, comment="版本号")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class KbCategory(Base):
    __tablename__ = "kb_categories"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    name = Column(String(100), nullable=False, comment="分类名称")
    parent_id = Column(Integer, ForeignKey("kb_categories.id"), nullable=True)
    level = Column(Integer, nullable=False, default=1, comment="层级深度 1/2/3...")
    sort_order = Column(Integer, nullable=False, default=0)
    is_system = Column(Boolean, nullable=False, default=False, comment="系统预置不可删")
    is_active = Column(Boolean, nullable=False, default=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ═══════════ 费用报销管理 ═══════════

class ExpenseReport(Base):
    """报销单主表"""
    __tablename__ = "expense_reports"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    report_no = Column(String(20), nullable=False, comment="报销单号")
    applicant_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="申请人")
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True, comment="申请部门")
    expense_date = Column(String(10), nullable=False, comment="费用发生日期")
    total_amount = Column(Float, nullable=False, default=0, comment="报销总额")
    loan_offset_amount = Column(Float, nullable=False, default=0, comment="冲销借款金额")
    net_payable = Column(Float, nullable=False, default=0, comment="实付金额")
    status = Column(String(20), nullable=False, default="draft",
                    comment="draft/submitted/dept_approved/finance_approved/director_approved/unit_head_approved/paid/closed/rejected")
    current_approver_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="当前审批人")
    approval_chain = Column(JSON, nullable=True, comment="审批链记录")
    policy_warnings = Column(JSON, nullable=True, comment="超标预警汇总")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("Company")
    applicant = relationship("User", foreign_keys=[applicant_id])
    items = relationship("ExpenseReportItem", back_populates="report", cascade="all, delete-orphan")
    attachments = relationship("ExpenseAttachment", back_populates="report", cascade="all, delete-orphan")


class ExpenseReportItem(Base):
    """报销单明细行"""
    __tablename__ = "expense_report_items"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("expense_reports.id"), nullable=False)
    row_seq = Column(Integer, nullable=False, default=1, comment="行序号")
    expense_item_id = Column(Integer, ForeignKey("expense_items.id"), nullable=True, comment="费用类型")
    date = Column(String(10), nullable=False, comment="发生日期")
    amount = Column(Float, nullable=False, default=0, comment="金额")
    description = Column(String(300), nullable=True, comment="费用说明")
    receipt_count = Column(Integer, nullable=False, default=0, comment="发票张数")
    policy_check = Column(JSON, nullable=True, comment="费用标准检查结果")

    report = relationship("ExpenseReport", back_populates="items")


class ExpenseLoan(Base):
    """借款单"""
    __tablename__ = "expense_loans"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    loan_no = Column(String(20), nullable=False, comment="借款单号")
    applicant_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="借款人")
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True, comment="借款部门")
    loan_date = Column(String(10), nullable=False, comment="借款日期")
    amount = Column(Float, nullable=False, default=0, comment="借款金额")
    repaid_amount = Column(Float, nullable=False, default=0, comment="已还金额")
    reason = Column(Text, nullable=True, comment="借款事由")
    status = Column(String(20), nullable=False, default="submitted",
                    comment="submitted/approved/partial_repaid/fully_repaid/closed")
    expected_repay_date = Column(String(10), nullable=True, comment="预计还款日期")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("Company")
    applicant = relationship("User", foreign_keys=[applicant_id])
    attachments = relationship("ExpenseAttachment", back_populates="loan", cascade="all, delete-orphan")


class ExpensePolicy(Base):
    """费用标准配置"""
    __tablename__ = "expense_policies"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    expense_item_id = Column(Integer, ForeignKey("expense_items.id"), nullable=True, comment="费用类型")
    country = Column(String(10), nullable=True, comment="国别")
    region = Column(String(50), nullable=True, comment="地区")
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True, comment="适用部门")
    position_level = Column(Integer, nullable=True, comment="适用岗位级别")
    policy_type = Column(String(20), nullable=False, default="event",
                         comment="daily/event/per_person")
    max_amount = Column(Float, nullable=False, default=0, comment="上限金额")
    currency = Column(String(5), nullable=False, default="CNY", comment="币种")
    effective_from = Column(String(10), nullable=False, comment="生效日期")
    effective_to = Column(String(10), nullable=True, comment="失效日期")
    notes = Column(String(300), nullable=True, comment="备注")

    company = relationship("Company")


class ExpenseAttachment(Base):
    """报销附件"""
    __tablename__ = "expense_attachments"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("expense_reports.id"), nullable=True, comment="关联报销单")
    loan_id = Column(Integer, ForeignKey("expense_loans.id"), nullable=True, comment="关联借款单")
    file_name = Column(String(200), nullable=False, comment="规范命名文件名")
    category = Column(String(20), nullable=False, default="其他",
                      comment="发票/机票/车票/合同/签收单/其他")
    doc_number = Column(String(100), nullable=True, comment="票据号码")
    file_path = Column(String(300), nullable=False, comment="存储路径")
    file_size = Column(Integer, nullable=False, default=0, comment="文件大小(bytes)")
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    report = relationship("ExpenseReport", back_populates="attachments")
    loan = relationship("ExpenseLoan", back_populates="attachments")


# ═══════════════════════════════════════════
# 合同管理模块
# ═══════════════════════════════════════════

class Contract(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)

    # 合同基本信息
    contract_name = Column(String(300), nullable=True, comment="合同名称")
    contract_no = Column(String(50), nullable=False, comment="合同号码")
    contract_type = Column(String(20), nullable=False, index=True,
                           comment="supplier/customer/labor/lease")
    contract_category = Column(String(50), nullable=False, default="其他",
                               comment="录用合同/咨询服务协议/销售合同/采购合同/贷款合同...")
    subject = Column(String(300), nullable=True, comment="合同事由/标的")

    # 法律依据（多选，逗号分隔: 合同法,公司法,经济法,劳动法...）
    legal_basis = Column(String(200), nullable=True, comment="法律依据")

    # 甲方信息（我方）
    party_a = Column(String(200), nullable=True, comment="甲方")
    party_a_address = Column(String(300), nullable=True, comment="甲方地址")
    party_a_phone = Column(String(50), nullable=True, comment="甲方电话")
    party_a_representative = Column(String(100), nullable=True, comment="甲方法定代表人")
    party_a_signatory = Column(String(100), nullable=True, comment="甲方授权签字人")

    # 乙方信息（对方）
    party_b = Column(String(200), nullable=True, comment="乙方")
    party_b_address = Column(String(300), nullable=True, comment="乙方地址")
    party_b_phone = Column(String(50), nullable=True, comment="乙方电话")
    party_b_representative = Column(String(100), nullable=True, comment="乙方法定代表人")
    party_b_signatory = Column(String(100), nullable=True, comment="乙方授权签字人")

    # 金额与日期
    amount = Column(Float, default=0.0, comment="合同金额")
    sign_date = Column(String(10), nullable=True, comment="签署日期")
    start_date = Column(String(10), nullable=True, comment="生效日期")
    end_date = Column(String(10), nullable=True, comment="到期日期")

    # 条款
    payment_terms = Column(Text, nullable=True, comment="财务支付条款")
    force_majeure = Column(Text, nullable=True, comment="不可抗力条款")
    arbitration_venue = Column(String(200), nullable=True, comment="仲裁/诉讼地")

    # 状态与管理
    status = Column(String(16), default="draft",
                    comment="draft/active/completed/terminated")
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True, comment="发起部门")
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="经办人")
    notes = Column(Text, nullable=True, comment="备注")

    # 审批环节（非强制）
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="审核人")
    reviewed_at = Column(DateTime, nullable=True, comment="审核时间")
    approver_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="批准人")
    approved_at = Column(DateTime, nullable=True, comment="批准时间")
    sealer_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="盖章人")
    sealed_at = Column(DateTime, nullable=True, comment="盖章时间")

    # 扫描与存档
    scan_file_path = Column(String(500), nullable=True, comment="盖章扫描件路径")
    archived_at = Column(DateTime, nullable=True, comment="归档时间")

    # 执行进展与闭环
    execution_progress = Column(Text, nullable=True, comment="合同执行进展记录")
    supplement_notes = Column(Text, nullable=True, comment="补录说明")
    closure_confirmed = Column(Boolean, default=False, comment="闭环确认")
    closure_confirmed_at = Column(DateTime, nullable=True, comment="闭环确认时间")
    closure_confirmed_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="闭环确认人")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("Company")
    department = relationship("Department")
    owner = relationship("User", foreign_keys=[owner_id])


# ═══════════════════════════════════════════
# 招投标管理模块
# ═══════════════════════════════════════════

class TenderProject(Base):
    """招标项目 — 我方作为招标人"""
    __tablename__ = "tender_projects"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    project_no = Column(String(50), nullable=False, comment="招标编号")
    project_name = Column(String(300), nullable=False, comment="招标项目名称")
    tender_type = Column(String(30), nullable=False, default="公开招标",
                         comment="公开招标/邀请招标/竞争性谈判/询价/单一来源")
    procurement_category = Column(String(20), nullable=False, default="服务",
                                  comment="货物/工程/服务")
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="经办人")
    estimated_amount = Column(Float, default=0.0, comment="预算金额")
    currency = Column(String(5), default="CNY")

    announcement_date = Column(String(10), nullable=True, comment="公告日期")
    bid_deadline = Column(String(10), nullable=True, comment="投标截止日期")
    opening_date = Column(String(10), nullable=True, comment="开标日期")
    opening_location = Column(String(200), nullable=True, comment="开标地点")

    evaluation_method = Column(String(30), nullable=True, default="综合评分法",
                               comment="综合评分法/最低价法/性价比法")
    evaluation_summary = Column(Text, nullable=True, comment="评标总结")

    status = Column(String(20), default="draft",
                    comment="draft/announced/opening/evaluating/awarded/closed/cancelled")

    winner_name = Column(String(200), nullable=True, comment="中标单位")
    winner_amount = Column(Float, nullable=True, comment="中标金额")
    award_date = Column(String(10), nullable=True, comment="定标日期")
    result_summary = Column(Text, nullable=True, comment="定标结果摘要")

    tender_doc_path = Column(String(500), nullable=True, comment="招标文件路径")
    bid_opening_record = Column(Text, nullable=True, comment="开标记录")

    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="审核人")
    reviewed_at = Column(DateTime, nullable=True, comment="审核时间")
    approver_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="批准人")
    approved_at = Column(DateTime, nullable=True, comment="批准时间")

    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("Company")
    department = relationship("Department")
    owner = relationship("User", foreign_keys=[owner_id])


class BidSubmission(Base):
    """投标登记 — 我方作为投标人"""
    __tablename__ = "bid_submissions"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    bid_no = Column(String(50), nullable=False, comment="投标编号")
    project_name = Column(String(300), nullable=False, comment="投标项目名称")
    tendering_party = Column(String(200), nullable=True, comment="招标方")
    tendering_agency = Column(String(200), nullable=True, comment="招标代理机构")
    bid_type = Column(String(30), nullable=False, default="公开投标",
                      comment="公开投标/邀请投标")

    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="经办人")

    bid_amount = Column(Float, default=0.0, comment="投标报价")
    currency = Column(String(5), default="CNY")

    bond_amount = Column(Float, default=0.0, comment="保证金金额")
    bond_paid_date = Column(String(10), nullable=True, comment="保证金缴纳日期")
    bond_returned_date = Column(String(10), nullable=True, comment="保证金退还日期")
    bond_status = Column(String(20), default="未缴", comment="未缴/已缴/已退/被没收")

    bid_doc_submitted_date = Column(String(10), nullable=True, comment="投标文件递交日期")
    bid_deadline = Column(String(10), nullable=True, comment="投标截止日期")
    opening_date = Column(String(10), nullable=True, comment="开标日期")

    technical_score = Column(Float, nullable=True, comment="技术得分")
    price_score = Column(Float, nullable=True, comment="价格得分")
    total_score = Column(Float, nullable=True, comment="总得分")
    rank = Column(Integer, nullable=True, comment="排名")

    status = Column(String(20), default="draft",
                    comment="draft/submitted/opened/evaluated/won/lost/cancelled")
    result_notes = Column(Text, nullable=True, comment="投标结果备注")

    bid_doc_path = Column(String(500), nullable=True, comment="投标文件路径")

    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("Company")
    department = relationship("Department")
    owner = relationship("User", foreign_keys=[owner_id])


# ═══════════════════════════════════════════
# 招投标 — 例外事项（非标/异常流程闭环）
# ═══════════════════════════════════════════

# ═══════════════════════════════════════════
# 董事办工作模块 (Board of Directors Office)
# ═══════════════════════════════════════════

class BoardFiling(Base):
    """董事办综合文档 — 覆盖合规报送、内部报批、三会决议、档案管理"""
    __tablename__ = "board_filings"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    doc_type = Column(String(20), nullable=False, index=True,
                     comment="filing/approval/meeting/archive")
    doc_subtype = Column(String(50), nullable=True,
                         comment="filing:csrc|exchange|shareholder|finance; "
                                 "approval:resolution|disclosure|legal|dividend|charter_amendment|other; "
                                 "meeting:shareholder|board|supervisory; "
                                 "archive:charter|agreement|investment|dividend|legal|financial_report|other")
    title = Column(String(300), nullable=False, comment="标题")
    target_org = Column(String(200), nullable=True, comment="目标机构（证监会/上交所/深交所/股东大会/财务部）")
    deadline = Column(String(10), nullable=True, comment="截止日期")
    submit_date = Column(String(10), nullable=True, comment="实际提交/完成日期")
    status = Column(String(20), nullable=False, default="待提交",
                    comment="待提交/已提交/已反馈/已逾期/已完成 —— filing/archive用; "
                            "草稿/部门审核/董秘审核/董事长审批/已完成 —— approval用")
    approver = Column(String(100), nullable=True, comment="审批人")
    contact_person = Column(String(100), nullable=True, comment="联系人（对接日志用）")
    contact_method = Column(String(100), nullable=True, comment="联系方式（对接日志用）")
    party_name = Column(String(200), nullable=True, comment="对方单位（对接日志用）")
    summary = Column(Text, nullable=True, comment="摘要")
    content = Column(Text, nullable=True, comment="正文（Markdown）")
    file_path = Column(String(500), nullable=True, comment="附件路径")
    extra_data = Column(JSON, nullable=True, comment="JSON灵活扩展")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("Company")
    creator = relationship("User", foreign_keys=[created_by])


class BoardShareholder(Base):
    """股东名册"""
    __tablename__ = "board_shareholders"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    name = Column(String(200), nullable=False, comment="股东名称")
    share_type = Column(String(20), nullable=False, default="普通股",
                        comment="普通股/优先股")
    share_count = Column(Float, nullable=False, default=0, comment="持股数量")
    share_ratio = Column(Float, nullable=False, default=0, comment="持股比例(%)")
    contact_person = Column(String(100), nullable=True, comment="联系人")
    contact_phone = Column(String(20), nullable=True)
    contact_email = Column(String(100), nullable=True)
    entry_date = Column(String(10), nullable=True, comment="入股日期")
    notes = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="active",
                    comment="active/inactive")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class BidExceptionEvent(Base):
    """招投标例外事项 — 统一承载流标/废标/终止/弃标/异议/争议/变更/豁免"""
    __tablename__ = "bid_exception_events"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    target_type = Column(String(20), nullable=False, index=True,
                         comment="tender_project / bid_submission")
    target_id = Column(Integer, nullable=False, comment="关联招标/投标项目ID")
    exception_type = Column(String(30), nullable=False,
                            comment="流标/废标/终止招标/变更采购方式/紧急采购/弃标/被废标/异议申诉/保证金争议/中标后变更/其他")
    title = Column(String(300), nullable=False, comment="例外事项标题")
    reason = Column(Text, nullable=True, comment="事由说明")
    resolution = Column(Text, nullable=True, comment="处理结果")
    status = Column(String(20), default="draft",
                    comment="draft/reviewed/approved/rejected/closed")

    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    approver_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)

    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="经办人")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("Company")
    department = relationship("Department")
    owner = relationship("User", foreign_keys=[owner_id])


# ═══════════════════════════════════════════
# 税务管理模块
# ═══════════════════════════════════════════

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
    creator = relationship("User", foreign_keys=[created_by])


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


class CarryForwardEntry(Base):
    """期末结转分录"""
    __tablename__ = "carry_forward_entries"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    period = Column(String(7), nullable=False, comment="期间 yyyy-MM")
    entry_type = Column(String(30), nullable=False,
                       comment="revenue_to_profit/expense_to_profit/profit_to_retained")
    debit_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    credit_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    amount = Column(Float, nullable=False, default=0.0)
    voucher_id = Column(Integer, ForeignKey("vouchers.id"), nullable=True, comment="生成的结转凭证ID")
    status = Column(String(20), nullable=False, default="draft", comment="draft/executed")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    executed_at = Column(DateTime, nullable=True)

    company = relationship("Company")


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


# ═══════════ 订阅与支付 ═══════════

class SubscriptionPlan(Base):
    """套餐定义"""
    __tablename__ = "subscription_plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    billing_cycle = Column(String(20), nullable=False, default="monthly")
    price_cny = Column(Float, nullable=False, default=0)
    price_usd = Column(Float, nullable=False, default=0)
    modules = Column(JSON, nullable=False)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class CompanySubscription(Base):
    """公司订阅记录"""
    __tablename__ = "company_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    plan_id = Column(Integer, ForeignKey("subscription_plans.id"), nullable=True)
    billing_cycle = Column(String(20), nullable=False, default="monthly")
    status = Column(String(20), nullable=False, default="trialing")
    trial_ends_at = Column(DateTime, nullable=True)
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    payment_method = Column(String(30), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("Company")
    plan = relationship("SubscriptionPlan")


class PaymentTransaction(Base):
    """支付记录"""
    __tablename__ = "payment_transactions"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    subscription_id = Column(Integer, ForeignKey("company_subscriptions.id"), nullable=True)
    amount = Column(Float, nullable=False, default=0)
    currency = Column(String(3), nullable=False, default="CNY")
    payment_method = Column(String(30), nullable=False)
    gateway_transaction_id = Column(String(200), nullable=True)
    status = Column(String(20), nullable=False, default="pending")
    paid_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company")
    subscription = relationship("CompanySubscription")


class AuditReport(Base):
    """年度审计报告"""
    __tablename__ = "audit_reports"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    year = Column(Integer, nullable=False)
    firm_name = Column(String(200), nullable=True)
    contact_person = Column(String(100), nullable=True)
    contact_email = Column(String(200), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    report_file = Column(String(500), nullable=True)
    report_file_name = Column(String(200), nullable=True)
    balance_sheet_ok = Column(Boolean, default=False)
    income_statement_ok = Column(Boolean, default=False)
    cashflow_statement_ok = Column(Boolean, default=False)
    notes = Column(String(1000), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TodoTask(Base):
    """协同办公 — 内部待办任务"""
    __tablename__ = "todo_tasks"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(String(1000), nullable=True)
    status = Column(String(20), default="pending")
    priority = Column(String(10), default="medium")
    due_date = Column(String(10), nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AccessRecord(Base):
    """门禁管理 — 人员出入记录"""
    __tablename__ = "access_records"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    person_name = Column(String(100), nullable=False)
    department = Column(String(100), nullable=True)
    phone = Column(String(50), nullable=True)
    direction = Column(String(10), nullable=False, default="entry")
    access_point = Column(String(100), nullable=True)
    reason = Column(String(500), nullable=True)
    record_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    notes = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
