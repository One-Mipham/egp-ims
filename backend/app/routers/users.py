"""用户管理路由：super_admin 专用，按公司隔离。"""
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserResponse
from app.auth import hash_password, get_current_user


class ResetPasswordBody(BaseModel):
    new_password: str

router = APIRouter()


def _get_company_scope(current: User):
    """返回当前用户可管理的 company_id。
    若当前用户无 company_id（全局 super_admin），返回 None 表示可看全部。
    """
    return current.company_id


def _require_same_company(current: User, target: User):
    """校验目标用户与当前用户同属一个公司。"""
    scope = _get_company_scope(current)
    if scope is not None and target.company_id != scope:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作其他公司的用户"
        )


@router.get("/", response_model=list[UserResponse])
def list_users(current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """列出用户。按公司隔离：仅显示当前用户同公司的用户。"""
    if current.role != "super_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅系统管理员可查看用户列表")
    scope = _get_company_scope(current)
    if scope is not None:
        return db.query(User).filter(User.company_id == scope).all()
    # 全局 super_admin（无公司归属）可查看全部
    return db.query(User).all()


@router.post("/", response_model=UserResponse)
def create_user(user_data: UserCreate, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """创建新用户（需 super_admin）。新用户自动归属于当前管理员的公司。"""
    if current.role != "super_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅系统管理员可创建用户")
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在")
    company_id = current.company_id
    if company_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="当前用户未关联公司，无法创建子用户")
    user = User(
        username=user_data.username, email=user_data.email,
        password_hash=hash_password(user_data.password), role=user_data.role,
        company_id=company_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, role: str = None, is_active: bool = None,
                current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """更新用户角色/状态（需 super_admin，仅限同公司用户）。"""
    if current.role != "super_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅系统管理员可修改用户")
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    _require_same_company(current, target)
    if role:
        target.role = role
    if is_active is not None:
        target.is_active = is_active
    db.commit()
    db.refresh(target)
    return target


@router.delete("/{user_id}")
def delete_user(user_id: int, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """删除/停用用户（需 super_admin，不能删除自己，仅限同公司用户）。"""
    if current.role != "super_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅系统管理员可删除用户")
    if user_id == current.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能删除自己")
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    _require_same_company(current, target)
    target.is_active = False
    db.commit()
    return {"ok": True}


@router.post("/{user_id}/reset-password")
def reset_password(user_id: int, body: ResetPasswordBody,
                   current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """管理员重置用户密码（仅限同公司用户）。"""
    if current.role != "super_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅系统管理员可重置密码")
    if user_id == current.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请使用修改自身密码功能")
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    _require_same_company(current, target)
    target.password_hash = hash_password(body.new_password)
    db.commit()
    return {"ok": True}
