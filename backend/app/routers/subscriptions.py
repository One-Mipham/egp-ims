"""订阅管理路由 — 套餐列表 + 订阅 + 试用激活."""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.auth import get_current_user
from app.models import Company, SubscriptionPlan, CompanySubscription, PaymentTransaction, User

router = APIRouter()


class SubscribeRequest(BaseModel):
    company_id: int
    plan_slug: str
    billing_cycle: str = "monthly"


class SubscriptionStatusResponse(BaseModel):
    company_id: int
    module_set: str
    enabled_modules: list[str]
    subscription_status: str
    trial_ends_at: str | None = None
    current_period_end: str | None = None
    plans: list[dict] | None = None
    model_config = {"from_attributes": True}


@router.get("/plans")
def list_plans(db: Session = Depends(get_db)):
    """列出所有可用套餐。"""
    plans = db.query(SubscriptionPlan).filter(SubscriptionPlan.is_active).order_by(SubscriptionPlan.sort_order).all()
    return [
        {
            "id": p.id, "name": p.name, "slug": p.slug,
            "description": p.description, "billing_cycle": p.billing_cycle,
            "price_cny": p.price_cny, "price_usd": p.price_usd,
            "modules": p.modules,
        }
        for p in plans
    ]


@router.get("/current")
def current_subscription(company_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """获取公司当前的订阅状态。"""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="公司不存在")
    sub = db.query(CompanySubscription).filter(
        CompanySubscription.company_id == company_id,
        CompanySubscription.status.in_(["trialing", "active"]),
    ).order_by(CompanySubscription.id.desc()).first()
    return {
        "company_id": company.id,
        "module_set": company.module_set,
        "enabled_modules": company.enabled_modules or [],
        "subscription_status": company.subscription_status,
        "trial_ends_at": company.trial_ends_at.isoformat() if company.trial_ends_at else None,
        "current_period_end": sub.current_period_end.isoformat() if sub and sub.current_period_end else None,
    }


@router.post("/activate-trial")
def activate_trial(company_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """激活 30 天全模块试用。仅允许认证用户为自己所属公司激活。"""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="公司不存在")
    # 仅允许激活自己所属公司（超级管理员可激活任意公司）
    if user.role != "super_admin" and user.company_id != company_id:
        raise HTTPException(status_code=403, detail="仅可为自己的公司激活试用")
    if company.subscription_status == "active":
        raise HTTPException(status_code=400, detail="公司已有有效订阅")

    all_modules = ["accounting", "reports", "receivables", "payables", "expenses",
                    "finance", "assets", "inventory", "contracts",
                    "investments", "hr", "board", "admin", "bids", "knowledge"]

    company.module_set = "trial"
    company.enabled_modules = all_modules
    company.subscription_status = "trialing"
    company.trial_ends_at = datetime.utcnow() + timedelta(days=30)

    # 创建试用订阅记录
    sub = CompanySubscription(
        company_id=company_id,
        status="trialing",
        trial_ends_at=company.trial_ends_at,
        billing_cycle="monthly",
    )
    db.add(sub)
    db.commit()
    return {
        "ok": True,
        "enabled_modules": all_modules,
        "trial_ends_at": company.trial_ends_at.isoformat(),
    }


@router.post("/subscribe")
def subscribe(data: SubscribeRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """选择套餐并创建订阅。"""
    company = db.query(Company).filter(Company.id == data.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="公司不存在")

    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.slug == data.plan_slug).first()
    if not plan:
        raise HTTPException(status_code=404, detail="套餐不存在")

    if plan.billing_cycle == "lifetime":
        company.module_set = "custom"
        company.enabled_modules = plan.modules
        company.subscription_status = "active"
        company.trial_ends_at = None
        sub = CompanySubscription(
            company_id=data.company_id,
            plan_id=plan.id,
            billing_cycle="lifetime",
            status="active",
        )
    else:
        company.module_set = plan.slug.split("-")[0]
        company.enabled_modules = plan.modules
        company.subscription_status = "active"
        company.trial_ends_at = None
        now = datetime.utcnow()
        if data.billing_cycle == "annual":
            period_end = now + timedelta(days=365)
        elif data.billing_cycle == "semi_annual":
            period_end = now + timedelta(days=180)
        else:
            period_end = now + timedelta(days=30)
        sub = CompanySubscription(
            company_id=data.company_id,
            plan_id=plan.id,
            billing_cycle=data.billing_cycle,
            status="active",
            current_period_start=now,
            current_period_end=period_end,
        )

    db.add(sub)
    db.commit()
    return {
        "ok": True,
        "enabled_modules": plan.modules,
        "subscription_status": "active",
    }


@router.post("/renew")
def renew_subscription(company_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """续费：将当前订阅延长一个周期。"""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="公司不存在")

    sub = db.query(CompanySubscription).filter(
        CompanySubscription.company_id == company_id,
        CompanySubscription.status.in_(["active", "past_due"]),
    ).order_by(CompanySubscription.id.desc()).first()

    if not sub:
        raise HTTPException(status_code=404, detail="无有效订阅")

    now = datetime.utcnow()
    if sub.billing_cycle == "annual":
        extend = timedelta(days=365)
    elif sub.billing_cycle == "semi_annual":
        extend = timedelta(days=180)
    else:
        extend = timedelta(days=30)

    base = max((sub.current_period_end or now), now)
    sub.current_period_start = base
    sub.current_period_end = base + extend
    sub.status = "active"

    company.subscription_status = "active"

    db.commit()
    return {
        "ok": True,
        "subscription_status": "active",
        "current_period_end": (base + extend).isoformat(),
    }


@router.post("/cancel")
def cancel_subscription(company_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """取消订阅。"""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="公司不存在")
    sub = db.query(CompanySubscription).filter(
        CompanySubscription.company_id == company_id,
        CompanySubscription.status.in_(["trialing", "active", "past_due"]),
    ).order_by(CompanySubscription.id.desc()).first()
    if sub:
        sub.status = "cancelled"
    company.subscription_status = "cancelled"
    company.enabled_modules = ["knowledge"]
    db.commit()
    return {"ok": True, "subscription_status": "cancelled"}


@router.get("/history")
def subscription_history(company_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """获取公司的订阅和支付历史。"""
    subs = db.query(CompanySubscription).filter(
        CompanySubscription.company_id == company_id,
    ).order_by(CompanySubscription.id.desc()).all()

    payments = db.query(PaymentTransaction).filter(
        PaymentTransaction.company_id == company_id,
    ).order_by(PaymentTransaction.id.desc()).all()

    return {
        "subscriptions": [
            {
                "id": s.id, "plan_name": s.plan.name if s.plan else "-",
                "billing_cycle": s.billing_cycle, "status": s.status,
                "period_start": s.current_period_start.isoformat() if s.current_period_start else None,
                "period_end": s.current_period_end.isoformat() if s.current_period_end else None,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in subs
        ],
        "payments": [
            {
                "id": p.id, "amount": p.amount, "currency": p.currency,
                "payment_method": p.payment_method, "status": p.status,
                "paid_at": p.paid_at.isoformat() if p.paid_at else None,
            }
            for p in payments
        ],
    }


@router.post("/check-expiry")
def check_expiry(db: Session = Depends(get_db)):
    """定时任务：检查所有订阅是否过期，自动切换状态。"""
    now = datetime.utcnow()
    companies = db.query(Company).filter(
        Company.subscription_status.in_(["trialing", "active"]),
    ).all()

    expired = 0
    for c in companies:
        if c.subscription_status == "trialing" and c.trial_ends_at and c.trial_ends_at < now:
            c.subscription_status = "expired"
            c.enabled_modules = ["knowledge"]
            expired += 1
        elif c.subscription_status == "active":
            sub = db.query(CompanySubscription).filter(
                CompanySubscription.company_id == c.id,
                CompanySubscription.status == "active",
            ).order_by(CompanySubscription.id.desc()).first()
            if sub and sub.current_period_end and sub.current_period_end < now:
                sub.status = "past_due"
                c.subscription_status = "past_due"
                expired += 1

    db.commit()
    return {"ok": True, "expired_updated": expired}
