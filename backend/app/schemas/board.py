"""董事办 — Pydantic schemas."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# ── BoardFiling ──

class BoardFilingCreate(BaseModel):
    company_id: int
    doc_type: str  # filing/approval/meeting/archive
    doc_subtype: Optional[str] = None
    title: str
    target_org: Optional[str] = None
    deadline: Optional[str] = None
    submit_date: Optional[str] = None
    status: Optional[str] = "待提交"
    approver: Optional[str] = None
    contact_person: Optional[str] = None
    contact_method: Optional[str] = None
    party_name: Optional[str] = None
    summary: Optional[str] = None
    content: Optional[str] = None
    file_path: Optional[str] = None
    extra_data: Optional[dict] = None


class BoardFilingUpdate(BaseModel):
    doc_type: Optional[str] = None
    doc_subtype: Optional[str] = None
    title: Optional[str] = None
    target_org: Optional[str] = None
    deadline: Optional[str] = None
    submit_date: Optional[str] = None
    status: Optional[str] = None
    approver: Optional[str] = None
    contact_person: Optional[str] = None
    contact_method: Optional[str] = None
    party_name: Optional[str] = None
    summary: Optional[str] = None
    content: Optional[str] = None
    file_path: Optional[str] = None
    extra_data: Optional[dict] = None


class BoardFilingResponse(BaseModel):
    id: int
    company_id: int
    doc_type: str
    doc_subtype: Optional[str]
    title: str
    target_org: Optional[str]
    deadline: Optional[str]
    submit_date: Optional[str]
    status: str
    approver: Optional[str]
    contact_person: Optional[str]
    contact_method: Optional[str]
    party_name: Optional[str]
    summary: Optional[str]
    content: Optional[str]
    file_path: Optional[str]
    extra_data: Optional[dict]
    created_by: Optional[int]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


# ── BoardShareholder ──

class BoardShareholderCreate(BaseModel):
    company_id: int
    name: str
    share_type: Optional[str] = "普通股"
    share_count: Optional[float] = 0
    share_ratio: Optional[float] = 0
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    entry_date: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = "active"


class BoardShareholderUpdate(BaseModel):
    name: Optional[str] = None
    share_type: Optional[str] = None
    share_count: Optional[float] = None
    share_ratio: Optional[float] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    entry_date: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None


class BoardShareholderResponse(BaseModel):
    id: int
    company_id: int
    name: str
    share_type: str
    share_count: float
    share_ratio: float
    contact_person: Optional[str]
    contact_phone: Optional[str]
    contact_email: Optional[str]
    entry_date: Optional[str]
    notes: Optional[str]
    status: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


# ── Cockpit lights ──

class CockpitLight(BaseModel):
    label: str
    status: str  # green/yellow/red


class BoardCockpitResponse(BaseModel):
    lights: list[CockpitLight]
