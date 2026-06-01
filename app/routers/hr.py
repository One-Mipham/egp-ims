"""人力资源管理路由。"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    HrPolicy, HrPosition, HrEmployee, HrTraining,
    HrEvaluation, HrSalary, HrRewardPunishment,
    HrOffboarding, HrBudget,
)
from app.schemas import (
    HrPolicyCreate, HrPolicyResponse,
    HrPositionCreate, HrPositionResponse,
    HrEmployeeCreate, HrEmployeeResponse,
    HrTrainingCreate, HrTrainingResponse,
    HrEvaluationCreate, HrEvaluationResponse,
    HrSalaryCreate, HrSalaryResponse,
    HrRewardPunishmentCreate, HrRewardPunishmentResponse,
    HrOffboardingCreate, HrOffboardingResponse,
    HrBudgetCreate, HrBudgetResponse,
)
from app.auth import get_current_user

router = APIRouter()

# ═══════════ 公司人力资源管理制度 ═══════════

@router.get("/policies", response_model=list[HrPolicyResponse])
def list_policies(company_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(HrPolicy).filter(HrPolicy.company_id == company_id).all()

@router.post("/policies", response_model=HrPolicyResponse)
def upsert_policy(data: HrPolicyCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    existing = db.query(HrPolicy).filter(
        HrPolicy.company_id == data.company_id
    ).first()
    if existing:
        existing.title = data.title
        existing.content = data.content
    else:
        existing = HrPolicy(**data.model_dump())
        db.add(existing)
    db.commit()
    db.refresh(existing)
    return existing


# ═══════════ 职级管理 ═══════════

@router.get("/positions", response_model=list[HrPositionResponse])
def list_positions(company_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(HrPosition).filter(
        HrPosition.company_id == company_id
    ).order_by(HrPosition.sort_order).all()

@router.post("/positions", response_model=HrPositionResponse)
def create_position(data: HrPositionCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if data.sort_order is None:
        max_order = db.query(HrPosition.sort_order).filter(
            HrPosition.company_id == data.company_id
        ).order_by(HrPosition.sort_order.desc()).first()
        data.sort_order = (max_order[0] + 1) if max_order and max_order[0] else 0
    pos = HrPosition(**data.model_dump())
    db.add(pos)
    db.commit()
    db.refresh(pos)
    return pos

@router.put("/positions/{pos_id}", response_model=HrPositionResponse)
def update_position(pos_id: int, data: HrPositionCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    pos = db.query(HrPosition).filter(HrPosition.id == pos_id).first()
    if not pos:
        raise HTTPException(status_code=404, detail="职级不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(pos, k, v)
    db.commit()
    db.refresh(pos)
    return pos

@router.delete("/positions/{pos_id}")
def delete_position(pos_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    pos = db.query(HrPosition).filter(HrPosition.id == pos_id).first()
    if not pos:
        raise HTTPException(status_code=404, detail="职级不存在")
    pos.is_active = False
    db.commit()
    return {"ok": True}


# ═══════════ 员工管理 ═══════════

@router.get("/employees", response_model=list[HrEmployeeResponse])
def list_employees(
    company_id: int,
    status: str = Query(None),
    department_id: int = Query(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    q = db.query(HrEmployee).filter(HrEmployee.company_id == company_id)
    if status:
        q = q.filter(HrEmployee.status == status)
    if department_id:
        q = q.filter(HrEmployee.department_id == department_id)
    return q.order_by(HrEmployee.employee_code).all()

@router.post("/employees", response_model=HrEmployeeResponse)
def create_employee(data: HrEmployeeCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    emp = HrEmployee(**data.model_dump())
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return emp

@router.put("/employees/{emp_id}", response_model=HrEmployeeResponse)
def update_employee(emp_id: int, data: HrEmployeeCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    emp = db.query(HrEmployee).filter(HrEmployee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="员工不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(emp, k, v)
    db.commit()
    db.refresh(emp)
    return emp

@router.delete("/employees/{emp_id}")
def delete_employee(emp_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    emp = db.query(HrEmployee).filter(HrEmployee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="员工不存在")
    emp.status = "离职"
    db.commit()
    return {"ok": True}


# ═══════════ 员工培训 ═══════════

@router.get("/trainings", response_model=list[HrTrainingResponse])
def list_trainings(company_id: int, employee_id: int = Query(None), db: Session = Depends(get_db), user=Depends(get_current_user)):
    q = db.query(HrTraining).filter(HrTraining.company_id == company_id)
    if employee_id:
        q = q.filter(HrTraining.employee_id == employee_id)
    return q.order_by(HrTraining.training_date.desc()).all()

@router.post("/trainings", response_model=HrTrainingResponse)
def create_training(data: HrTrainingCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    t = HrTraining(**data.model_dump())
    db.add(t)
    db.commit()
    db.refresh(t)
    return t

@router.put("/trainings/{t_id}", response_model=HrTrainingResponse)
def update_training(t_id: int, data: HrTrainingCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    t = db.query(HrTraining).filter(HrTraining.id == t_id).first()
    if not t: raise HTTPException(status_code=404, detail="培训记录不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(t, k, v)
    db.commit(); db.refresh(t); return t

@router.delete("/trainings/{t_id}")
def delete_training(t_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    t = db.query(HrTraining).filter(HrTraining.id == t_id).first()
    if not t: raise HTTPException(status_code=404, detail="培训记录不存在")
    db.delete(t); db.commit()
    return {"ok": True}


# ═══════════ 员工考核 ═══════════

@router.get("/evaluations", response_model=list[HrEvaluationResponse])
def list_evaluations(company_id: int, employee_id: int = Query(None), db: Session = Depends(get_db), user=Depends(get_current_user)):
    q = db.query(HrEvaluation).filter(HrEvaluation.company_id == company_id)
    if employee_id: q = q.filter(HrEvaluation.employee_id == employee_id)
    return q.order_by(HrEvaluation.period.desc()).all()

@router.post("/evaluations", response_model=HrEvaluationResponse)
def create_evaluation(data: HrEvaluationCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    e = HrEvaluation(**data.model_dump()); db.add(e); db.commit(); db.refresh(e); return e

@router.put("/evaluations/{e_id}", response_model=HrEvaluationResponse)
def update_evaluation(e_id: int, data: HrEvaluationCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    e = db.query(HrEvaluation).filter(HrEvaluation.id == e_id).first()
    if not e: raise HTTPException(status_code=404, detail="考核记录不存在")
    for k, v in data.model_dump(exclude_unset=True).items(): setattr(e, k, v)
    db.commit(); db.refresh(e); return e

@router.delete("/evaluations/{e_id}")
def delete_evaluation(e_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    e = db.query(HrEvaluation).filter(HrEvaluation.id == e_id).first()
    if not e: raise HTTPException(status_code=404, detail="考核记录不存在")
    db.delete(e); db.commit(); return {"ok": True}


# ═══════════ 薪酬管理 ═══════════

@router.get("/salaries", response_model=list[HrSalaryResponse])
def list_salaries(company_id: int, employee_id: int = Query(None), year_month: str = Query(None), db: Session = Depends(get_db), user=Depends(get_current_user)):
    q = db.query(HrSalary).filter(HrSalary.company_id == company_id)
    if employee_id: q = q.filter(HrSalary.employee_id == employee_id)
    if year_month: q = q.filter(HrSalary.year_month == year_month)
    return q.order_by(HrSalary.year_month.desc()).all()

@router.post("/salaries", response_model=HrSalaryResponse)
def create_salary(data: HrSalaryCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    s = HrSalary(**data.model_dump()); db.add(s); db.commit(); db.refresh(s); return s

@router.put("/salaries/{s_id}", response_model=HrSalaryResponse)
def update_salary(s_id: int, data: HrSalaryCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    s = db.query(HrSalary).filter(HrSalary.id == s_id).first()
    if not s: raise HTTPException(status_code=404, detail="薪酬记录不存在")
    for k, v in data.model_dump(exclude_unset=True).items(): setattr(s, k, v)
    db.commit(); db.refresh(s); return s

@router.delete("/salaries/{s_id}")
def delete_salary(s_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    s = db.query(HrSalary).filter(HrSalary.id == s_id).first()
    if not s: raise HTTPException(status_code=404, detail="薪酬记录不存在")
    db.delete(s); db.commit(); return {"ok": True}


# ═══════════ 员工奖惩 ═══════════

@router.get("/rewards", response_model=list[HrRewardPunishmentResponse])
def list_rewards(company_id: int, employee_id: int = Query(None), db: Session = Depends(get_db), user=Depends(get_current_user)):
    q = db.query(HrRewardPunishment).filter(HrRewardPunishment.company_id == company_id)
    if employee_id: q = q.filter(HrRewardPunishment.employee_id == employee_id)
    return q.order_by(HrRewardPunishment.date.desc()).all()

@router.post("/rewards", response_model=HrRewardPunishmentResponse)
def create_reward(data: HrRewardPunishmentCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    r = HrRewardPunishment(**data.model_dump()); db.add(r); db.commit(); db.refresh(r); return r

@router.put("/rewards/{r_id}", response_model=HrRewardPunishmentResponse)
def update_reward(r_id: int, data: HrRewardPunishmentCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    r = db.query(HrRewardPunishment).filter(HrRewardPunishment.id == r_id).first()
    if not r: raise HTTPException(status_code=404, detail="记录不存在")
    for k, v in data.model_dump(exclude_unset=True).items(): setattr(r, k, v)
    db.commit(); db.refresh(r); return r

@router.delete("/rewards/{r_id}")
def delete_reward(r_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    r = db.query(HrRewardPunishment).filter(HrRewardPunishment.id == r_id).first()
    if not r: raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(r); db.commit(); return {"ok": True}


# ═══════════ 员工离职 ═══════════

@router.get("/offboarding", response_model=list[HrOffboardingResponse])
def list_offboarding(company_id: int, employee_id: int = Query(None), db: Session = Depends(get_db), user=Depends(get_current_user)):
    q = db.query(HrOffboarding).filter(HrOffboarding.company_id == company_id)
    if employee_id: q = q.filter(HrOffboarding.employee_id == employee_id)
    return q.order_by(HrOffboarding.apply_date.desc()).all()

@router.post("/offboarding", response_model=HrOffboardingResponse)
def create_offboarding(data: HrOffboardingCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    o = HrOffboarding(**data.model_dump()); db.add(o); db.commit(); db.refresh(o); return o

@router.put("/offboarding/{o_id}", response_model=HrOffboardingResponse)
def update_offboarding(o_id: int, data: HrOffboardingCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    o = db.query(HrOffboarding).filter(HrOffboarding.id == o_id).first()
    if not o: raise HTTPException(status_code=404, detail="记录不存在")
    for k, v in data.model_dump(exclude_unset=True).items(): setattr(o, k, v)
    if o.status == "已离职":
        emp = db.query(HrEmployee).filter(HrEmployee.id == o.employee_id).first()
        if emp: emp.status = "离职"
    db.commit(); db.refresh(o); return o

@router.delete("/offboarding/{o_id}")
def delete_offboarding(o_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    o = db.query(HrOffboarding).filter(HrOffboarding.id == o_id).first()
    if not o: raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(o); db.commit(); return {"ok": True}


# ═══════════ 人力资源预算 ═══════════

@router.get("/budgets", response_model=list[HrBudgetResponse])
def list_budgets(company_id: int, year: int = Query(None), db: Session = Depends(get_db), user=Depends(get_current_user)):
    q = db.query(HrBudget).filter(HrBudget.company_id == company_id)
    if year: q = q.filter(HrBudget.year == year)
    return q.order_by(HrBudget.year.desc(), HrBudget.department_id).all()

@router.post("/budgets", response_model=HrBudgetResponse)
def upsert_budget(data: HrBudgetCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    existing = db.query(HrBudget).filter(
        HrBudget.company_id == data.company_id,
        HrBudget.year == data.year,
        HrBudget.department_id == data.department_id,
    ).first()
    if existing:
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(existing, k, v)
    else:
        existing = HrBudget(**data.model_dump())
        db.add(existing)
    db.commit(); db.refresh(existing); return existing

@router.delete("/budgets/{b_id}")
def delete_budget(b_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    b = db.query(HrBudget).filter(HrBudget.id == b_id).first()
    if not b: raise HTTPException(status_code=404, detail="预算记录不存在")
    db.delete(b); db.commit(); return {"ok": True}
