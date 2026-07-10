"""招投标管理路由."""

from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.auth import get_current_user
from app.models import TenderProject, BidSubmission, BidExceptionEvent, User, AuditLog
from app.schemas import BypassAction
from app.permissions import check_approval_bypass
from app.schemas.bids import (
    TENDER_TYPES,
    PROCUREMENT_CATEGORIES,
    EVALUATION_METHODS,
    TENDER_STATUSES,
    BID_TYPES,
    BOND_STATUSES,
    BID_STATUSES,
    TENDER_EXCEPTION_TYPES,
    BID_EXCEPTION_TYPES,
    EXCEPTION_STATUSES,
    TARGET_TYPES,
    TenderProjectCreate,
    TenderProjectUpdate,
    TenderProjectResponse,
    BidSubmissionCreate,
    BidSubmissionUpdate,
    BidSubmissionResponse,
    BidExceptionCreate,
    BidExceptionUpdate,
    BidExceptionResponse,
    BidStatsResponse,
)

router = APIRouter()

PERMITTED_ROLES = {"finance_manager", "finance_director", "super_admin"}


def _can_view_all(user: User) -> bool:
    return user.role in PERMITTED_ROLES


# ── 编号生成 ──


def _generate_tender_no(company_id: int, db: Session) -> str:
    today = date.today().strftime("%Y%m%d")
    count = (
        db.query(TenderProject)
        .filter(
            TenderProject.company_id == company_id,
            TenderProject.project_no.like(f"ZB-{today}-%"),
        )
        .count()
    )
    return f"ZB-{today}-{count + 1:03d}"


def _generate_bid_no(company_id: int, db: Session) -> str:
    today = date.today().strftime("%Y%m%d")
    count = (
        db.query(BidSubmission)
        .filter(
            BidSubmission.company_id == company_id,
            BidSubmission.bid_no.like(f"TB-{today}-%"),
        )
        .count()
    )
    return f"TB-{today}-{count + 1:03d}"


# ═══════════════════════════════════════════
# 招标项目 — 选项（必须在 /{id} 之前注册）
# ═══════════════════════════════════════════


@router.get("/tender-projects/options")
def get_tender_options(user=Depends(get_current_user)):
    return {
        "tender_types": TENDER_TYPES,
        "procurement_categories": PROCUREMENT_CATEGORIES,
        "evaluation_methods": EVALUATION_METHODS,
        "statuses": TENDER_STATUSES,
    }


# ═══════════════════════════════════════════
# 招标项目 — CRUD
# ═══════════════════════════════════════════


@router.get("/tender-projects", response_model=list[TenderProjectResponse])
def list_tender_projects(
    company_id: int = Query(...),
    tender_type: str | None = Query(None),
    procurement_category: str | None = Query(None),
    department_id: int | None = Query(None),
    status: str | None = Query(None),
    search: str | None = Query(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    q = db.query(TenderProject).filter(TenderProject.company_id == company_id)
    if not _can_view_all(user):
        q = q.filter(TenderProject.owner_id == user.id)
    if tender_type:
        types = [t.strip() for t in tender_type.split(",")]
        q = q.filter(TenderProject.tender_type.in_(types))
    if procurement_category:
        cats = [c.strip() for c in procurement_category.split(",")]
        q = q.filter(TenderProject.procurement_category.in_(cats))
    if department_id:
        q = q.filter(TenderProject.department_id == department_id)
    if status:
        q = q.filter(TenderProject.status == status)
    if search:
        like = f"%{search}%"
        q = q.filter(TenderProject.project_no.like(like) | TenderProject.project_name.like(like))
    return q.order_by(TenderProject.id.desc()).all()


@router.get("/tender-projects/{project_id}", response_model=TenderProjectResponse)
def get_tender_project(
    project_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    p = db.query(TenderProject).filter(TenderProject.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="招标项目不存在")
    return p


@router.post("/tender-projects", response_model=TenderProjectResponse)
def create_tender_project(
    data: TenderProjectCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    p = TenderProject(**data.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.put("/tender-projects/{project_id}", response_model=TenderProjectResponse)
def update_tender_project(
    project_id: int,
    data: TenderProjectUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    p = db.query(TenderProject).filter(TenderProject.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="招标项目不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(p, k, v)
    db.commit()
    db.refresh(p)
    return p


@router.delete("/tender-projects/{project_id}")
def delete_tender_project(
    project_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    p = db.query(TenderProject).filter(TenderProject.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="招标项目不存在")
    db.delete(p)
    db.commit()
    return {"ok": True}


# ── 审批流程 ──


@router.post("/tender-projects/{project_id}/review")
def review_tender_project(
    project_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    p = db.query(TenderProject).filter(TenderProject.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="招标项目不存在")
    p.reviewer_id = user.id
    p.reviewed_at = datetime.utcnow()
    db.commit()
    return {"ok": True, "reviewed": True}


@router.post("/tender-projects/{project_id}/approve")
def approve_tender_project(
    project_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    p = db.query(TenderProject).filter(TenderProject.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="招标项目不存在")
    p.approver_id = user.id
    p.approved_at = datetime.utcnow()
    if p.status == "draft":
        p.status = "announced"
    db.commit()
    return {"ok": True, "approved": True}


@router.post("/tender-projects/{project_id}/bypass")
def bypass_tender_project(
    project_id: int,
    action: BypassAction,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """强制跳过招标项目审批（仅管理员/财务总监）"""
    err = check_approval_bypass(user)
    if err:
        raise HTTPException(status_code=403, detail=err)

    p = db.query(TenderProject).filter(TenderProject.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="招标项目不存在")

    p.approver_id = user.id
    p.approved_at = datetime.utcnow()
    if p.status == "draft":
        p.status = "approved"

    db.add(
        AuditLog(
            company_id=getattr(p, "company_id", 0),
            user_id=user.id,
            action="bypass_approval",
            target_type="tender_project",
            target_id=p.id,
            reason=action.reason,
        )
    )
    db.commit()
    return {"ok": True, "bypassed": True}


# ═══════════════════════════════════════════
# 投标登记 — 选项（必须在 /{id} 之前注册）
# ═══════════════════════════════════════════


@router.get("/submissions/options")
def get_bid_options(user=Depends(get_current_user)):
    return {
        "bid_types": BID_TYPES,
        "bond_statuses": BOND_STATUSES,
        "statuses": BID_STATUSES,
    }


# ═══════════════════════════════════════════
# 投标登记 — CRUD
# ═══════════════════════════════════════════


@router.get("/submissions", response_model=list[BidSubmissionResponse])
def list_bid_submissions(
    company_id: int = Query(...),
    bid_type: str | None = Query(None),
    bond_status: str | None = Query(None),
    department_id: int | None = Query(None),
    status: str | None = Query(None),
    search: str | None = Query(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    q = db.query(BidSubmission).filter(BidSubmission.company_id == company_id)
    if not _can_view_all(user):
        q = q.filter(BidSubmission.owner_id == user.id)
    if bid_type:
        types = [t.strip() for t in bid_type.split(",")]
        q = q.filter(BidSubmission.bid_type.in_(types))
    if bond_status:
        statuses_list = [s.strip() for s in bond_status.split(",")]
        q = q.filter(BidSubmission.bond_status.in_(statuses_list))
    if department_id:
        q = q.filter(BidSubmission.department_id == department_id)
    if status:
        q = q.filter(BidSubmission.status == status)
    if search:
        like = f"%{search}%"
        q = q.filter(
            BidSubmission.bid_no.like(like)
            | BidSubmission.project_name.like(like)
            | BidSubmission.tendering_party.like(like)
        )
    return q.order_by(BidSubmission.id.desc()).all()


@router.get("/submissions/{submission_id}", response_model=BidSubmissionResponse)
def get_bid_submission(
    submission_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    s = db.query(BidSubmission).filter(BidSubmission.id == submission_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="投标项目不存在")
    return s


@router.post("/submissions", response_model=BidSubmissionResponse)
def create_bid_submission(
    data: BidSubmissionCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    s = BidSubmission(**data.model_dump())
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


@router.put("/submissions/{submission_id}", response_model=BidSubmissionResponse)
def update_bid_submission(
    submission_id: int,
    data: BidSubmissionUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    s = db.query(BidSubmission).filter(BidSubmission.id == submission_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="投标项目不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(s, k, v)
    db.commit()
    db.refresh(s)
    return s


@router.delete("/submissions/{submission_id}")
def delete_bid_submission(
    submission_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    s = db.query(BidSubmission).filter(BidSubmission.id == submission_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="投标项目不存在")
    db.delete(s)
    db.commit()
    return {"ok": True}


# ═══════════════════════════════════════════
# 统计
# ═══════════════════════════════════════════


@router.get("/stats", response_model=BidStatsResponse)
def get_stats(
    company_id: int = Query(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    # 招标统计
    tq = db.query(TenderProject).filter(TenderProject.company_id == company_id)
    tender_count = tq.count()
    tender_amount = tq.with_entities(func.coalesce(func.sum(TenderProject.estimated_amount), 0)).scalar()
    tender_status = {
        r[0]: r[1] for r in tq.with_entities(TenderProject.status, func.count()).group_by(TenderProject.status).all()
    }

    # 投标统计
    bq = db.query(BidSubmission).filter(BidSubmission.company_id == company_id)
    bid_count = bq.count()
    bid_amount = bq.with_entities(func.coalesce(func.sum(BidSubmission.bid_amount), 0)).scalar()
    bid_status = {
        r[0]: r[1] for r in bq.with_entities(BidSubmission.status, func.count()).group_by(BidSubmission.status).all()
    }
    won = bq.filter(BidSubmission.status == "won").count()

    return BidStatsResponse(
        tender={
            "total_count": tender_count,
            "total_amount": round(tender_amount, 2),
            "by_status": tender_status,
        },
        bid={
            "total_count": bid_count,
            "total_amount": round(bid_amount, 2),
            "won_count": won,
            "by_status": bid_status,
        },
    )


# ═══════════════════════════════════════════
# 例外事项 — 选项（必须在 /{id} 之前注册）
# ═══════════════════════════════════════════


@router.get("/exceptions/options")
def get_exception_options(
    target_type: str | None = Query(None),
    user=Depends(get_current_user),
):
    return {
        "exception_types": TENDER_EXCEPTION_TYPES + BID_EXCEPTION_TYPES,
        "tender_exception_types": TENDER_EXCEPTION_TYPES,
        "bid_exception_types": BID_EXCEPTION_TYPES,
        "statuses": EXCEPTION_STATUSES,
        "target_types": TARGET_TYPES,
    }


# ═══════════════════════════════════════════
# 例外事项 — CRUD
# ═══════════════════════════════════════════


@router.get("/exceptions", response_model=list[BidExceptionResponse])
def list_exception_events(
    company_id: int = Query(...),
    target_type: str | None = Query(None),
    exception_type: str | None = Query(None),
    target_id: int | None = Query(None),
    status: str | None = Query(None),
    search: str | None = Query(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    q = db.query(BidExceptionEvent).filter(BidExceptionEvent.company_id == company_id)
    if not _can_view_all(user):
        q = q.filter(BidExceptionEvent.owner_id == user.id)
    if target_type:
        q = q.filter(BidExceptionEvent.target_type == target_type)
    if exception_type:
        q = q.filter(BidExceptionEvent.exception_type == exception_type)
    if target_id:
        q = q.filter(BidExceptionEvent.target_id == target_id)
    if status:
        q = q.filter(BidExceptionEvent.status == status)
    if search:
        like = f"%{search}%"
        q = q.filter(BidExceptionEvent.title.like(like) | BidExceptionEvent.reason.like(like))
    return q.order_by(BidExceptionEvent.id.desc()).all()


@router.get("/exceptions/{event_id}", response_model=BidExceptionResponse)
def get_exception_event(
    event_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    e = db.query(BidExceptionEvent).filter(BidExceptionEvent.id == event_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="例外事项不存在")
    return e


@router.post("/exceptions", response_model=BidExceptionResponse)
def create_exception_event(
    data: BidExceptionCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    e = BidExceptionEvent(**data.model_dump())
    db.add(e)
    db.commit()
    db.refresh(e)
    return e


@router.put("/exceptions/{event_id}", response_model=BidExceptionResponse)
def update_exception_event(
    event_id: int,
    data: BidExceptionUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    e = db.query(BidExceptionEvent).filter(BidExceptionEvent.id == event_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="例外事项不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(e, k, v)
    db.commit()
    db.refresh(e)
    return e


@router.delete("/exceptions/{event_id}")
def delete_exception_event(
    event_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    e = db.query(BidExceptionEvent).filter(BidExceptionEvent.id == event_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="例外事项不存在")
    db.delete(e)
    db.commit()
    return {"ok": True}


# ── 例外事项审批 ──


@router.post("/exceptions/{event_id}/review")
def review_exception_event(
    event_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    e = db.query(BidExceptionEvent).filter(BidExceptionEvent.id == event_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="例外事项不存在")
    e.reviewer_id = user.id
    e.reviewed_at = datetime.utcnow()
    e.status = "reviewed"
    db.commit()
    return {"ok": True, "reviewed": True}


@router.post("/exceptions/{event_id}/approve")
def approve_exception_event(
    event_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """批准例外事项，并联动更新关联的招标/投标项目状态以形成闭环"""
    e = db.query(BidExceptionEvent).filter(BidExceptionEvent.id == event_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="例外事项不存在")
    e.approver_id = user.id
    e.approved_at = datetime.utcnow()
    e.status = "approved"

    # ── 闭环联动：根据例外类型自动更新关联项目的状态 ──
    if e.target_type == "tender_project":
        target = db.query(TenderProject).filter(TenderProject.id == e.target_id).first()
        if target:
            closure_map = {
                "流标": "cancelled",
                "废标": "cancelled",
                "终止招标": "closed",
            }
            new_status = closure_map.get(e.exception_type)
            if new_status:
                target.status = new_status
    elif e.target_type == "bid_submission":
        target = db.query(BidSubmission).filter(BidSubmission.id == e.target_id).first()
        if target:
            closure_map = {
                "弃标": "lost",
                "被废标": "lost",
            }
            new_status = closure_map.get(e.exception_type)
            if new_status:
                target.status = new_status
            # 保证金争议：如已解决，更新 bond_status
            if e.exception_type == "保证金争议" and "退还" in (e.resolution or ""):
                target.bond_status = "已退"
            elif e.exception_type == "保证金争议" and "没收" in (e.resolution or ""):
                target.bond_status = "被没收"

    db.commit()
    return {"ok": True, "approved": True, "closure_applied": True}


@router.post("/exceptions/{event_id}/bypass")
def bypass_exception_event(
    event_id: int,
    action: BypassAction,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """强制跳过例外事项审批（仅管理员/财务总监）"""
    err = check_approval_bypass(user)
    if err:
        raise HTTPException(status_code=403, detail=err)

    e = db.query(BidExceptionEvent).filter(BidExceptionEvent.id == event_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="例外事项不存在")

    e.approver_id = user.id
    e.approved_at = datetime.utcnow()
    e.status = "approved"

    db.add(
        AuditLog(
            company_id=getattr(e, "company_id", 0),
            user_id=user.id,
            action="bypass_approval",
            target_type="exception_event",
            target_id=e.id,
            reason=action.reason,
        )
    )
    db.commit()
    return {"ok": True, "bypassed": True}


@router.post("/exceptions/{event_id}/reject")
def reject_exception_event(
    event_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    e = db.query(BidExceptionEvent).filter(BidExceptionEvent.id == event_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="例外事项不存在")
    e.status = "rejected"
    db.commit()
    return {"ok": True, "rejected": True}
