"""用户管理路由：super_admin 专用。"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserResponse
from app.auth import hash_password, get_current_user

router = APIRouter()


@router.get("/", response_model=list[UserResponse])
def list_users(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """列出所有用户。"""
    return db.query(User).all()


@router.post("/", response_model=UserResponse)
def create_user(user_data: UserCreate, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """创建新用户（需 super_admin）。"""
    if current.role != "super_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅系统管理员可创建用户")
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在")
    user = User(username=user_data.username, email=user_data.email, password_hash=hash_password(user_data.password), role=user_data.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, role: str = None, is_active: bool = None, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """更新用户角色/状态（需 super_admin）。"""
    if current.role != "super_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅系统管理员可修改用户")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    if role:
        user.role = role
    if is_active is not None:
        user.is_active = is_active
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}")
def delete_user(user_id: int, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """删除/停用用户（需 super_admin，不能删除自己）。"""
    if current.role != "super_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅系统管理员可删除用户")
    if user_id == current.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能删除自己")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    user.is_active = False
    db.commit()
    return {"ok": True}


@router.post("/{user_id}/reset-password")
def reset_password(user_id: int, new_password: str, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """管理员重置用户密码。"""
    if current.role != "super_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅系统管理员可重置密码")
    if user_id == current.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请使用修改自身密码功能")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    user.password_hash = hash_password(new_password)
    db.commit()
    return {"ok": True}
