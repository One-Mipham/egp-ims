"""预算管理路由."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.auth import get_current_user
from app.models import Budget, BudgetItem, User
from app.schemas import (
    BudgetCreate, BudgetUpdate, BudgetResponse,
)

router = APIRouter()


# ── 预算 CRUD ──

@router.get("/budgets", response_model=List[BudgetResponse])
def list_budgets(
    company_id: int = Query(...),
    year: int = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(Budget).filter(Budget.company_id == company_id)
    if year:
        q = q.filter(Budget.year == year)
    return q.order_by(Budget.year.desc()).all()


@router.post("/budgets", response_model=BudgetResponse)
def create_budget(
    data: BudgetCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    budget = Budget(
        company_id=data.company_id,
        name=data.name,
        year=data.year,
        status="draft",
        created_by=user.id,
    )
    db.add(budget)
    db.flush()

    for item_data in (data.items or []):
        item = BudgetItem(
            budget_id=budget.id,
            account_code=item_data.account_code,
            department_id=item_data.department_id,
            month=item_data.month,
            amount=item_data.amount or 0.0,
        )
        db.add(item)

    db.commit()
    db.refresh(budget)
    return budget


@router.get("/budgets/{budget_id}", response_model=BudgetResponse)
def get_budget(
    budget_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    budget = db.query(Budget).filter(Budget.id == budget_id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="预算不存在")
    return budget


@router.put("/budgets/{budget_id}", response_model=BudgetResponse)
def update_budget(
    budget_id: int,
    data: BudgetUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    budget = db.query(Budget).filter(Budget.id == budget_id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="预算不存在")

    if data.name is not None:
        budget.name = data.name
    if data.status is not None:
        budget.status = data.status

    if data.items is not None:
        # Replace all items
        db.query(BudgetItem).filter(BudgetItem.budget_id == budget.id).delete()
        for item_data in data.items:
            item = BudgetItem(
                budget_id=budget.id,
                account_code=item_data.account_code,
                department_id=item_data.department_id,
                month=item_data.month,
                amount=item_data.amount or 0.0,
            )
            db.add(item)

    db.commit()
    db.refresh(budget)
    return budget


@router.delete("/budgets/{budget_id}")
def delete_budget(
    budget_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    budget = db.query(Budget).filter(Budget.id == budget_id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="预算不存在")
    db.delete(budget)
    db.commit()
    return {"ok": True}
