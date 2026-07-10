"""招投标管理 Pydantic Schema."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# ── 预设常量 ──

TENDER_TYPES = ["公开招标", "邀请招标", "竞争性谈判", "询价", "单一来源"]
PROCUREMENT_CATEGORIES = ["货物", "工程", "服务"]
EVALUATION_METHODS = ["综合评分法", "最低价法", "性价比法"]
TENDER_STATUSES = ["draft", "announced", "opening", "evaluating", "awarded", "closed", "cancelled"]

BID_TYPES = ["公开投标", "邀请投标"]
BOND_STATUSES = ["未缴", "已缴", "已退", "被没收"]
BID_STATUSES = ["draft", "submitted", "opened", "evaluated", "won", "lost", "cancelled"]


# ── 招标项目 CRUD ──


class TenderProjectCreate(BaseModel):
    company_id: int
    project_no: str
    project_name: str
    tender_type: str = "公开招标"
    procurement_category: str = "服务"
    department_id: Optional[int] = None
    owner_id: Optional[int] = None
    estimated_amount: float = 0.0
    currency: str = "CNY"
    announcement_date: Optional[str] = None
    bid_deadline: Optional[str] = None
    opening_date: Optional[str] = None
    opening_location: Optional[str] = None
    evaluation_method: str = "综合评分法"
    evaluation_summary: Optional[str] = None
    status: str = "draft"
    winner_name: Optional[str] = None
    winner_amount: Optional[float] = None
    award_date: Optional[str] = None
    result_summary: Optional[str] = None
    tender_doc_path: Optional[str] = None
    bid_opening_record: Optional[str] = None
    notes: Optional[str] = None


class TenderProjectUpdate(BaseModel):
    project_no: Optional[str] = None
    project_name: Optional[str] = None
    tender_type: Optional[str] = None
    procurement_category: Optional[str] = None
    department_id: Optional[int] = None
    owner_id: Optional[int] = None
    estimated_amount: Optional[float] = None
    currency: Optional[str] = None
    announcement_date: Optional[str] = None
    bid_deadline: Optional[str] = None
    opening_date: Optional[str] = None
    opening_location: Optional[str] = None
    evaluation_method: Optional[str] = None
    evaluation_summary: Optional[str] = None
    status: Optional[str] = None
    winner_name: Optional[str] = None
    winner_amount: Optional[float] = None
    award_date: Optional[str] = None
    result_summary: Optional[str] = None
    tender_doc_path: Optional[str] = None
    bid_opening_record: Optional[str] = None
    notes: Optional[str] = None


class TenderProjectResponse(BaseModel):
    id: int
    company_id: int
    project_no: str
    project_name: str
    tender_type: str
    procurement_category: str
    department_id: Optional[int] = None
    owner_id: Optional[int] = None
    estimated_amount: float
    currency: str
    announcement_date: Optional[str] = None
    bid_deadline: Optional[str] = None
    opening_date: Optional[str] = None
    opening_location: Optional[str] = None
    evaluation_method: Optional[str] = None
    evaluation_summary: Optional[str] = None
    status: str
    winner_name: Optional[str] = None
    winner_amount: Optional[float] = None
    award_date: Optional[str] = None
    result_summary: Optional[str] = None
    tender_doc_path: Optional[str] = None
    bid_opening_record: Optional[str] = None
    reviewer_id: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    approver_id: Optional[int] = None
    approved_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── 投标登记 CRUD ──


class BidSubmissionCreate(BaseModel):
    company_id: int
    bid_no: str
    project_name: str
    tendering_party: Optional[str] = None
    tendering_agency: Optional[str] = None
    bid_type: str = "公开投标"
    department_id: Optional[int] = None
    owner_id: Optional[int] = None
    bid_amount: float = 0.0
    currency: str = "CNY"
    bond_amount: float = 0.0
    bond_paid_date: Optional[str] = None
    bond_returned_date: Optional[str] = None
    bond_status: str = "未缴"
    bid_doc_submitted_date: Optional[str] = None
    bid_deadline: Optional[str] = None
    opening_date: Optional[str] = None
    technical_score: Optional[float] = None
    price_score: Optional[float] = None
    total_score: Optional[float] = None
    rank: Optional[int] = None
    status: str = "draft"
    result_notes: Optional[str] = None
    bid_doc_path: Optional[str] = None
    notes: Optional[str] = None


class BidSubmissionUpdate(BaseModel):
    project_name: Optional[str] = None
    tendering_party: Optional[str] = None
    tendering_agency: Optional[str] = None
    bid_type: Optional[str] = None
    department_id: Optional[int] = None
    owner_id: Optional[int] = None
    bid_amount: Optional[float] = None
    currency: Optional[str] = None
    bond_amount: Optional[float] = None
    bond_paid_date: Optional[str] = None
    bond_returned_date: Optional[str] = None
    bond_status: Optional[str] = None
    bid_doc_submitted_date: Optional[str] = None
    bid_deadline: Optional[str] = None
    opening_date: Optional[str] = None
    technical_score: Optional[float] = None
    price_score: Optional[float] = None
    total_score: Optional[float] = None
    rank: Optional[int] = None
    status: Optional[str] = None
    result_notes: Optional[str] = None
    bid_doc_path: Optional[str] = None
    notes: Optional[str] = None


class BidSubmissionResponse(BaseModel):
    id: int
    company_id: int
    bid_no: str
    project_name: str
    tendering_party: Optional[str] = None
    tendering_agency: Optional[str] = None
    bid_type: str
    department_id: Optional[int] = None
    owner_id: Optional[int] = None
    bid_amount: float
    currency: str
    bond_amount: float
    bond_paid_date: Optional[str] = None
    bond_returned_date: Optional[str] = None
    bond_status: str
    bid_doc_submitted_date: Optional[str] = None
    bid_deadline: Optional[str] = None
    opening_date: Optional[str] = None
    technical_score: Optional[float] = None
    price_score: Optional[float] = None
    total_score: Optional[float] = None
    rank: Optional[int] = None
    status: str
    result_notes: Optional[str] = None
    bid_doc_path: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── 例外事项 — 预设常量 ──

TENDER_EXCEPTION_TYPES = ["流标", "废标", "终止招标", "变更采购方式", "紧急采购", "其他"]
BID_EXCEPTION_TYPES = ["弃标", "被废标", "异议申诉", "保证金争议", "中标后变更", "其他"]
EXCEPTION_TYPES = TENDER_EXCEPTION_TYPES + BID_EXCEPTION_TYPES
EXCEPTION_STATUSES = ["draft", "reviewed", "approved", "rejected", "closed"]
TARGET_TYPES = ["tender_project", "bid_submission"]

EXCEPTION_STATUS_LABELS = {
    "draft": "草稿",
    "reviewed": "已审核",
    "approved": "已批准",
    "rejected": "已驳回",
    "closed": "已关闭",
}


# ── 例外事项 CRUD ──


class BidExceptionCreate(BaseModel):
    company_id: int
    target_type: str  # tender_project / bid_submission
    target_id: int
    exception_type: str
    title: str
    reason: Optional[str] = None
    resolution: Optional[str] = None
    status: str = "draft"
    department_id: Optional[int] = None
    owner_id: Optional[int] = None
    notes: Optional[str] = None


class BidExceptionUpdate(BaseModel):
    target_type: Optional[str] = None
    target_id: Optional[int] = None
    exception_type: Optional[str] = None
    title: Optional[str] = None
    reason: Optional[str] = None
    resolution: Optional[str] = None
    status: Optional[str] = None
    department_id: Optional[int] = None
    owner_id: Optional[int] = None
    notes: Optional[str] = None


class BidExceptionResponse(BaseModel):
    id: int
    company_id: int
    target_type: str
    target_id: int
    exception_type: str
    title: str
    reason: Optional[str] = None
    resolution: Optional[str] = None
    status: str
    reviewer_id: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    approver_id: Optional[int] = None
    approved_at: Optional[datetime] = None
    department_id: Optional[int] = None
    owner_id: Optional[int] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── 统计 ──


class BidStatsResponse(BaseModel):
    tender: dict
    bid: dict
