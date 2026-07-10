"""权限管理路由：获取/设置用户细粒度权限。"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, UserPermission, Company
from app.schemas import UserPermissionSchema
from app.auth import get_current_user

router = APIRouter()


@router.get("/")
def list_all_permissions(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """列出公司所有用户及权限。"""
    users = db.query(User).all()
    result = []
    for u in users:
        perm = db.query(UserPermission).filter_by(user_id=u.id, company_id=company_id).first()
        perm_data = (
            UserPermissionSchema.model_validate(perm)
            if perm
            else UserPermissionSchema(user_id=u.id, company_id=company_id)
        )
        result.append(
            {
                "user_id": u.id,
                "username": u.username,
                "role": u.role,
                "is_admin": u.is_admin,
                "permissions": {
                    k: getattr(perm_data, k)
                    for k in UserPermissionSchema.model_fields
                    if k not in ("user_id", "company_id")
                },
            }
        )
    return result


def _get_user_or_404(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


def _get_company_or_404(db: Session, company_id: int) -> Company:
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="公司不存在")
    return company


@router.get("/{user_id}")
def get_user_permissions(
    user_id: int,
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取指定用户在指定公司的权限。"""
    _get_user_or_404(db, user_id)
    _get_company_or_404(db, company_id)

    perm = db.query(UserPermission).filter_by(user_id=user_id, company_id=company_id).first()
    if perm:
        return UserPermissionSchema.model_validate(perm)

    # Return defaults if no record exists
    return UserPermissionSchema(user_id=user_id, company_id=company_id)


@router.put("/{user_id}")
def set_user_permissions(
    user_id: int,
    data: UserPermissionSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """设置指定用户在指定公司的权限（仅管理员可操作）。"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="仅管理员可设置权限")

    _get_user_or_404(db, user_id)
    _get_company_or_404(db, data.company_id)

    perm = db.query(UserPermission).filter_by(user_id=user_id, company_id=data.company_id).first()
    if perm:
        for field in UserPermissionSchema.model_fields:
            if field not in ("user_id", "company_id"):
                setattr(perm, field, getattr(data, field))
    else:
        perm = UserPermission(**data.model_dump())
        db.add(perm)

    db.commit()
    db.refresh(perm)
    return UserPermissionSchema.model_validate(perm)
