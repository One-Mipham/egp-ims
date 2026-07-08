"""JWT 认证与密码加密."""
import os
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User

_SECRET = os.environ.get("SECRET_KEY", "")
if _SECRET:
    SECRET_KEY = _SECRET
elif os.environ.get("ENV", "dev") == "production":
    raise RuntimeError("SECRET_KEY must be set in production environment")
else:
    SECRET_KEY = secrets.token_urlsafe(48)
    import logging
    logging.getLogger("uvicorn").warning(
        "SECRET_KEY not set — using random key for dev (tokens invalid after restart)"
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    to_encode["sub"] = str(to_encode["sub"])  # jose requires string sub
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的认证凭证")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = int(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exception
    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        raise credentials_exception
    return user


def require_role(*roles: str):
    """依赖注入：检查当前用户是否具有指定角色之一。"""
    def _check(user: User = Depends(get_current_user)):
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="权限不足")
        return user
    return _check


def get_jwt_payload(token: str = Depends(oauth2_scheme)) -> dict:
    """从 JWT 中提取完整 payload（含 company_id）。"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的认证凭证")


def get_current_company_id(payload: dict = Depends(get_jwt_payload)) -> int:
    """从 JWT 中提取 company_id，确保用户只能操作其登录时选择的公司。"""
    cid = payload.get("company_id")
    if cid is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token中未包含公司信息")
    return int(cid)


def require_company_scope(requested_cid: int, jwt_cid: int = Depends(get_current_company_id)) -> None:
    """验证请求中的 company_id 与 JWT 中的一致，防止跨公司数据访问。"""
    if requested_cid != jwt_cid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问其他公司的数据"
        )


def verify_company_isolation(token_str: str, requested_company_id: int) -> None:
    """验证请求的 company_id 与 JWT 中的一致。"""
    try:
        payload = jwt.decode(token_str, SECRET_KEY, algorithms=[ALGORITHM])
        jwt_cid = payload.get("company_id")
        if jwt_cid is not None and int(jwt_cid) != requested_company_id:
            raise HTTPException(status_code=403, detail="无权访问其他公司的数据")
    except JWTError:
        pass  # token 无效，交给 get_current_user 处理
