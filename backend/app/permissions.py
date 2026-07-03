"""集中式权限检查 — 根据公司内控模式动态判断。

三种模式：
- simplified: 一人通吃，所有操作均允许
- standard:   基础分离，不能审核自己创建的凭证
- strict:     全岗位分离，出纳不可审核/记账等

所有检查函数返回 None 表示允许，返回字符串表示拒绝原因。
"""


def check_voucher_create(user, company) -> str | None:
    """是否允许创建凭证。"""
    if company.internal_control_mode == "simplified":
        return None
    if company.internal_control_mode == "standard":
        # 会计及以上角色可创建
        if user.role in ("accountant", "finance_manager", "finance_director", "super_admin"):
            return None
        return "出纳不可创建凭证"
    # strict: 会计/经理/总监可创建
    if user.role in ("accountant", "finance_manager", "finance_director", "super_admin"):
        return None
    return "出纳不可创建凭证"


def check_voucher_update(user, company, creator_id) -> str | None:
    """是否允许修改凭证。"""
    if company.internal_control_mode == "simplified":
        return None
    if company.internal_control_mode == "standard":
        # 创建人或经理/总监可修改
        if creator_id == user.id or user.role in ("finance_manager", "finance_director", "super_admin"):
            return None
        return "无权修改此凭证"
    # strict: 仅创建人（草稿状态），其他角色不可修改
    if creator_id == user.id:
        return None
    return "无权修改此凭证"


def check_voucher_approve(user, company, creator_id) -> str | None:
    """是否允许审核凭证。"""
    if company.internal_control_mode == "simplified":
        return None
    if creator_id == user.id and user.role != "super_admin":
        return "不能审核自己创建的凭证"
    if company.internal_control_mode == "standard":
        # 非本人即可（会计/经理/总监）
        if user.role in ("finance_manager", "finance_director", "super_admin"):
            return None
        if user.role == "cashier":
            return "出纳不能审核凭证"
        return None  # accountant can approve if not creator
    # strict: 出纳不可审核，会计不可审核
    if user.role in ("cashier", "accountant"):
        return "出纳和会计不能审核凭证"
    if user.role in ("finance_manager", "finance_director", "super_admin"):
        return None
    return "权限不足"


def check_voucher_post(user, company) -> str | None:
    """是否允许记账。"""
    if company.internal_control_mode == "simplified":
        return None
    if company.internal_control_mode == "standard":
        # 任何非出纳可记账
        if user.role != "cashier":
            return None
        return "出纳不能记账"
    # strict: 出纳不可记账
    if user.role == "cashier":
        return "出纳不能记账"
    return None


def check_voucher_reverse(user, company) -> str | None:
    """是否允许反记账。"""
    if company.internal_control_mode == "simplified":
        return None
    if company.internal_control_mode == "standard":
        if user.role in ("finance_manager", "finance_director", "super_admin"):
            return None
        return "权限不足"
    # strict: 仅总监可反记账
    if user.role in ("finance_director", "super_admin"):
        return None
    return "仅财务总监可反记账"


def check_period_close(user, company) -> str | None:
    """是否允许结账。"""
    if company.internal_control_mode == "simplified":
        return None
    if company.internal_control_mode == "standard":
        if user.role in ("finance_manager", "finance_director", "super_admin"):
            return None
        return "仅财务经理或总监可结账"
    # strict: 仅总监可结账
    if user.role in ("finance_director", "super_admin"):
        return None
    return "仅财务总监可结账"


def check_period_unclose(user, company) -> str | None:
    """是否允许反结账。"""
    if company.internal_control_mode == "simplified":
        return None
    if company.internal_control_mode == "standard":
        if user.role in ("finance_manager", "finance_director", "super_admin"):
            return None
        return "仅财务经理或总监可反结账"
    # strict: 仅总监可反结账
    if user.role in ("finance_director", "super_admin"):
        return None
    return "仅财务总监可反结账"


def check_account_manage(user, company) -> str | None:
    """是否允许管理科目（新增/修改/设置期初余额）。"""
    if company.internal_control_mode == "simplified":
        return None
    # standard/strict: 会计及以上角色
    if user.role in ("accountant", "finance_manager", "finance_director", "super_admin"):
        return None
    return "出纳不可管理科目"


def check_department_manage(user, company) -> str | None:
    """是否允许管理部门。"""
    if company.internal_control_mode == "simplified":
        return None
    if user.role in ("accountant", "finance_manager", "finance_director", "super_admin"):
        return None
    return "出纳不可管理部门"


def check_company_create(user) -> str | None:
    """是否允许创建公司账套。"""
    if user.role in ("super_admin", "finance_director"):
        return None
    return "权限不足"


def check_account_level(user, company, level: int) -> str | None:
    """检查科目级别权限：普通用户不能修改二级科目，管理员无限制。"""
    if getattr(user, 'is_admin', False) or user.role == "super_admin":
        return None
    if level <= 2:
        return "普通用户不能管理二级科目"
    return check_account_manage(user, company)


def check_permission(user, company, permission_name: str, db=None) -> str | None:
    """细粒度权限检查。管理员拥有所有权限，非管理员查 UserPermission 表。"""
    if getattr(user, 'is_admin', False) or user.role == "super_admin":
        return None
    if db is None:
        return "权限表需要数据库连接"
    from app.models import UserPermission
    perm = db.query(UserPermission).filter_by(user_id=user.id, company_id=company.id).first()
    if perm is None:
        return "未配置权限"
    if not getattr(perm, permission_name, False):
        return f"无权限：{permission_name}"
    return None


def check_approval_bypass(user) -> str | None:
    """仅超级管理员和财务总监可强制跳过审批节点"""
    if user.role in ("super_admin", "finance_director"):
        return None
    return "仅管理员和财务总监可强制跳过审批"


MODULE_ROLES: dict[str, list[str]] = {
    "accounting": ["accountant", "finance_manager", "finance_director", "super_admin"],
    "finance": ["finance_manager", "finance_director", "super_admin"],
    "hr": ["hr_manager", "super_admin"],
    "admin": ["admin_staff", "hr_manager", "super_admin"],
    "reports": ["accountant", "finance_manager", "finance_director", "super_admin"],
    "bids": ["admin_staff", "super_admin"],
    "contracts": ["admin_staff", "accountant", "super_admin"],
    "investments": ["finance_manager", "finance_director", "super_admin"],
    "board": ["finance_director", "super_admin"],
    "knowledge": ["*"],  # 所有角色可访问
    "expenses": ["cashier", "accountant", "finance_manager", "finance_director", "super_admin", "department_head"],
    "assets": ["accountant", "finance_manager", "super_admin"],
    "receivables": ["accountant", "finance_manager", "finance_director", "super_admin"],
    "payables": ["accountant", "finance_manager", "finance_director", "super_admin"],
    "inventory": ["accountant", "admin_staff", "super_admin"],
}


def check_module_access(user, module: str) -> str | None:
    """验证用户是否有权访问指定模块。返回 None 表示允许，字符串表示拒绝原因。"""
    allowed = MODULE_ROLES.get(module)
    if not allowed:
        return f"未知模块: {module}"
    if "*" in allowed:
        return None
    if user.role in allowed:
        return None
    return f"您的角色 ({user.role}) 无权访问此模块"


from fastapi import Depends, HTTPException, Request
from app.auth import get_current_user
from app.database import get_db
from sqlalchemy.orm import Session


def check_module_enabled(company, module: str) -> str | None:
    """验证公司是否购买了指定模块。试用期(trialing)全模块可用。返回 None 表示允许。"""
    if company.subscription_status == "trialing":
        return None
    if module == "knowledge":
        return None
    enabled = company.enabled_modules or []
    if not enabled:
        return f"公司尚未购买任何模块"
    if module in enabled:
        return None
    return f"模块 {module} 未在您的套餐中，请升级订阅"


def require_module(module: str):
    """FastAPI 依赖工厂：限制路由仅允许有模块权限且公司已购买的用户访问。"""
    async def _check(user=Depends(get_current_user), db: Session = Depends(get_db), request: Request = None):
        err = check_module_access(user, module)
        if err:
            raise HTTPException(status_code=403, detail=err)

        # 检查公司是否购买了此模块
        company_id_param = None
        if request:
            company_id_param = request.query_params.get("company_id")
            # 从 POST/PUT/PATCH body 中读取 company_id
            if not company_id_param and request.method in ("POST", "PUT", "PATCH"):
                import json as _json
                body = await request.body()
                if body:
                    try:
                        data = _json.loads(body)
                        cid = data.get("company_id")
                        if cid is not None:
                            company_id_param = str(cid)
                    except (_json.JSONDecodeError, ValueError):
                        pass
        if not company_id_param and module == "knowledge":
            return user
        if not company_id_param:
            return user

        from app.models import Company
        company = db.query(Company).filter(Company.id == int(company_id_param)).first()
        if company and company.subscription_status != "trialing":
            module_err = check_module_enabled(company, module)
            if module_err:
                raise HTTPException(status_code=402, detail=module_err)
        return user
    return _check
