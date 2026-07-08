"""认证路由：注册、登录。"""
import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Company
from app.schemas import UserResponse, LoginRequest
from app.auth import hash_password, verify_password, create_access_token, get_current_user
from app.seed import seed_level1_accounts, seed_level2_accounts, seed_tax_accounts, seed_cashflow_items

router = APIRouter()

PASSWORD_PATTERN = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$")
PHONE_PATTERN = re.compile(r"^1[3-9]\d{9}$")


class RegisterRequest(BaseModel):
    phone: str
    company_name: str
    password: str

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        if not PHONE_PATTERN.match(v):
            raise ValueError("手机号码格式不正确")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if not PASSWORD_PATTERN.match(v):
            raise ValueError("密码必须8位以上，包含大写字母、小写字母和数字")
        return v


class RegisterResponse(BaseModel):
    company_id: int
    company_name: str
    phone: str
    password: str  # 仅注册成功时返回一次
    message: str


@router.post("/register", response_model=RegisterResponse)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    # 1. 手机号唯一性
    if db.query(User).filter(User.username == data.phone).first():
        raise HTTPException(status_code=400, detail="该手机号已注册")

    # 2. 公司名唯一性
    if db.query(Company).filter(Company.name == data.company_name).first():
        raise HTTPException(status_code=400, detail="该公司名称已存在")

    # 3. 创建公司（SaaS 环境公司编号从 1004 起）
    from sqlalchemy import func
    max_id = db.query(func.max(Company.id)).scalar() or 0
    company = Company(
        name=data.company_name,
        short_name=data.company_name,
        internal_control_mode="standard",
    )
    if max_id < 1004:
        company.id = max(1004, max_id + 1)
    db.add(company)
    db.flush()

    # 4. 创建管理员用户（super_admin），绑定公司
    user = User(
        username=data.phone,
        email=f"{data.phone}@user.mipham.ai",
        password_hash=hash_password(data.password),
        role="super_admin",
        is_admin=True,
        company_id=company.id,
    )
    db.add(user)
    db.flush()

    # 5. 自动初始化国标科目及现金流量项目
    seed_level1_accounts(db, company.id)
    seed_level2_accounts(db, company.id)
    seed_tax_accounts(db, company.id)
    seed_cashflow_items(db, company.id)

    db.commit()

    return RegisterResponse(
        company_id=company.id,
        company_name=company.name,
        phone=data.phone,
        password="********",  # 不在响应中返回明文密码
        message="注册成功！请妥善保管您的公司序号和密码，登录后请立即修改密码。",
    )


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    username: str
    role: str
    is_admin: bool
    company_id: int
    company_name: str
    company_short_name: str = ""
    period: str


class IdentifyRequest(BaseModel):
    username: str
    password: str


class IdentifyResponse(BaseModel):
    user_id: int
    username: str
    company_id: int
    company_name: str
    company_short_name: str


@router.post("/identify", response_model=IdentifyResponse)
def identify_user(data: IdentifyRequest, db: Session = Depends(get_db)):
    """验证用户名密码并返回关联公司信息（不登录，仅识别）。"""
    user = db.query(User).filter(User.username == data.username).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已被禁用")

    # 优先使用 user.company_id，否则回退到 company-lookup
    cid = user.company_id
    if cid:
        company = db.query(Company).filter(Company.id == cid).first()
    else:
        company = None

    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="该用户未关联公司，请联系管理员")

    return IdentifyResponse(
        user_id=user.id,
        username=user.username,
        company_id=company.id,
        company_name=company.name,
        company_short_name=company.short_name or company.name,
    )


@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已被禁用")

    # company_id 可选：如未提供则使用用户绑定的公司
    cid = data.company_id if data.company_id else user.company_id
    # period 可选：默认当前月份
    period = data.period if data.period else datetime.now(timezone.utc).strftime("%Y-%m")
    if not cid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请提供公司编号")

    company = db.query(Company).filter(Company.id == cid).first()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="公司不存在")

    user.last_login = datetime.now(timezone.utc)
    db.commit()

    token = create_access_token(data={
        "sub": user.id,
        "role": user.role,
        "is_admin": user.is_admin,
        "company_id": cid,
    })

    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        username=user.username,
        role=user.role,
        is_admin=user.is_admin,
        company_id=cid,
        company_name=company.name,
        company_short_name=company.short_name or company.name,
        period=period,
    )


@router.get("/me", response_model=UserResponse)
def get_me(user: User = Depends(get_current_user)):
    return user


@router.get("/company-lookup/{company_id}")
def company_lookup(company_id: int, db: Session = Depends(get_db)):
    """公开接口：根据公司编号查询公司名称（无需认证）。"""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="公司不存在")
    return {"id": company.id, "name": company.name, "short_name": company.short_name}


class ChangePasswordBody(BaseModel):
    current_password: str
    new_password: str


@router.post("/change-password")
def change_password(body: ChangePasswordBody, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """用户修改自身密码（密码通过 JSON body 传递，不经过 URL）。"""
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="当前密码错误")
    user.password_hash = hash_password(body.new_password)
    db.commit()
    return {"ok": True}
