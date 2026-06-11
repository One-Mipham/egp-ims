"""合同管理 Pydantic Schema."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# ── 预设常量 ──

CONTRACT_CATEGORIES = [
    "录用合同", "保密协议", "竞业限制协议",
    "咨询服务协议", "中介服务合同", "技术服务合同", "审计合同",
    "销售合同", "采购合同", "委托加工合同",
    "贷款合同", "融资租赁合同", "担保合同", "股权投资合同", "项目投资合同",
    "技术开发合同", "技术转让合同",
    "办公室租赁合同", "建设工程合同", "运输合同", "仓储合同",
    "财产保险合同", "保险合同",
    "战略合作协议",
    "其他",
]

LEGAL_BASIS_OPTIONS = [
    "合同法", "公司法", "经济法", "劳动法",
    "劳动合同法", "民法典", "招标投标法",
    "政府采购法", "担保法", "证券法",
    "商标法", "专利法", "著作权法",
    "反垄断法", "反不正当竞争法",
]


# ── 合同 CRUD ──

class ContractCreate(BaseModel):
    company_id: int
    contract_no: str
    contract_type: str  # supplier/customer/labor/lease
    contract_category: str = "其他"
    contract_name: Optional[str] = None
    subject: Optional[str] = None
    legal_basis: Optional[str] = None
    # 甲方
    party_a: Optional[str] = None
    party_a_address: Optional[str] = None
    party_a_phone: Optional[str] = None
    party_a_representative: Optional[str] = None
    party_a_signatory: Optional[str] = None
    # 乙方
    party_b: Optional[str] = None
    party_b_address: Optional[str] = None
    party_b_phone: Optional[str] = None
    party_b_representative: Optional[str] = None
    party_b_signatory: Optional[str] = None
    # 金额与日期
    amount: float = 0.0
    sign_date: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    # 条款
    payment_terms: Optional[str] = None
    force_majeure: Optional[str] = None
    arbitration_venue: Optional[str] = None
    # 管理
    status: str = "draft"
    department_id: Optional[int] = None
    owner_id: Optional[int] = None
    notes: Optional[str] = None
    # 执行进展与闭环
    execution_progress: Optional[str] = None
    supplement_notes: Optional[str] = None
    closure_confirmed: bool = False


class ContractUpdate(BaseModel):
    contract_no: Optional[str] = None
    contract_type: Optional[str] = None
    contract_category: Optional[str] = None
    contract_name: Optional[str] = None
    subject: Optional[str] = None
    legal_basis: Optional[str] = None
    # 甲方
    party_a: Optional[str] = None
    party_a_address: Optional[str] = None
    party_a_phone: Optional[str] = None
    party_a_representative: Optional[str] = None
    party_a_signatory: Optional[str] = None
    # 乙方
    party_b: Optional[str] = None
    party_b_address: Optional[str] = None
    party_b_phone: Optional[str] = None
    party_b_representative: Optional[str] = None
    party_b_signatory: Optional[str] = None
    # 金额与日期
    amount: Optional[float] = None
    sign_date: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    # 条款
    payment_terms: Optional[str] = None
    force_majeure: Optional[str] = None
    arbitration_venue: Optional[str] = None
    # 管理
    status: Optional[str] = None
    department_id: Optional[int] = None
    owner_id: Optional[int] = None
    notes: Optional[str] = None
    # 执行进展与闭环
    execution_progress: Optional[str] = None
    supplement_notes: Optional[str] = None
    closure_confirmed: Optional[bool] = None


class ContractResponse(BaseModel):
    id: int
    company_id: int
    contract_no: str
    contract_type: str
    contract_category: str
    contract_name: Optional[str] = None
    subject: Optional[str] = None
    legal_basis: Optional[str] = None
    # 甲方
    party_a: Optional[str] = None
    party_a_address: Optional[str] = None
    party_a_phone: Optional[str] = None
    party_a_representative: Optional[str] = None
    party_a_signatory: Optional[str] = None
    # 乙方
    party_b: Optional[str] = None
    party_b_address: Optional[str] = None
    party_b_phone: Optional[str] = None
    party_b_representative: Optional[str] = None
    party_b_signatory: Optional[str] = None
    # 金额与日期
    amount: float
    sign_date: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    # 条款
    payment_terms: Optional[str] = None
    force_majeure: Optional[str] = None
    arbitration_venue: Optional[str] = None
    # 管理
    status: str
    department_id: Optional[int] = None
    owner_id: Optional[int] = None
    notes: Optional[str] = None
    # 审批环节（非强制）
    reviewer_id: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    approver_id: Optional[int] = None
    approved_at: Optional[datetime] = None
    sealer_id: Optional[int] = None
    sealed_at: Optional[datetime] = None
    # 扫描与存档
    scan_file_path: Optional[str] = None
    archived_at: Optional[datetime] = None
    # 执行进展与闭环
    execution_progress: Optional[str] = None
    supplement_notes: Optional[str] = None
    closure_confirmed: bool = False
    closure_confirmed_at: Optional[datetime] = None
    closure_confirmed_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── 统计 ──

class ContractStatsResponse(BaseModel):
    total_count: int
    total_amount: float
    by_type: dict
    by_category: dict
    by_department: dict
    by_status: dict
