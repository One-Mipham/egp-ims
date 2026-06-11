"""公司/账套管理路由。"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Company
from app.schemas import CompanyCreate, CompanyResponse, CompanyUpdate
from app.seed import seed_level1_accounts, seed_level2_accounts, seed_hr_positions
from app.auth import get_current_user, User
from app.permissions import check_company_create

router = APIRouter()




@router.get("/", response_model=list[CompanyResponse])
def list_companies(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """列出所有公司（仅 super_admin）。"""
    if user.role != "super_admin":
        raise HTTPException(status_code=403, detail="仅系统管理员可查看公司列表")
    return db.query(Company).all()


@router.get("/{company_id}", response_model=CompanyResponse)
def get_company(company_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """查看公司信息（仅 super_admin）。"""
    if user.role != "super_admin":
        raise HTTPException(status_code=403, detail="仅系统管理员可查看公司详情")
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="公司不存在")
    return company


@router.post("/", response_model=CompanyResponse)
def create_company(data: CompanyCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    err = check_company_create(user)
    if err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=err)
    company = Company(name=data.name, short_name=data.short_name, industry=data.industry, internal_control_mode=data.internal_control_mode, currency=data.currency)
    db.add(company)
    db.commit()
    db.refresh(company)
    seed_level1_accounts(db, company.id)
    seed_level2_accounts(db, company.id)
    seed_hr_positions(db, company.id)
    return company


@router.put("/{company_id}", response_model=CompanyResponse)
def update_company(company_id: int, data: CompanyUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="仅管理员可编辑公司信息")
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="公司不存在")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(company, field, value)
    db.commit()
    db.refresh(company)
    return company
