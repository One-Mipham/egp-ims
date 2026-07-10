"""财务管理驾驶舱 — 公司预算、现金流计划、经营指标"""

import calendar
import os
from typing import Optional, List
from pydantic import BaseModel as PydanticBase
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user
from app.models import User, Voucher, VoucherEntry, Account, CashflowPlan, CashflowPlanItem
from app.routers.reports import _get_leaf_descendants

router = APIRouter()

DOWNLOADS = os.path.expanduser("~/Downloads")


# ═══════════════════════════════════════════
# 辅助函数 — 从报表模块提取，避免循环导入
# ═══════════════════════════════════════════


def _period_end_date(period: str) -> str:
    y, m = int(period[:4]), int(period[5:7])
    last_day = calendar.monthrange(y, m)[1]
    return f"{y}-{m:02d}-{last_day:02d}"


def _calc_account_ending(code: str, db: Session, company_id: int, end_date: str) -> float:
    """计算单个科目的期末余额。"""
    acct = db.query(Account).filter(Account.company_id == company_id, Account.code == code).first()
    if not acct:
        return 0.0
    q = (
        db.query(VoucherEntry)
        .join(Voucher)
        .filter(
            Voucher.company_id == company_id,
            VoucherEntry.account_code == acct.code,
            Voucher.status.in_(["posted", "closed"]),
            Voucher.date <= end_date,
        )
    )
    entries = q.all()
    debit = sum(e.debit for e in entries)
    credit = sum(e.credit for e in entries)
    if acct.balance_direction == "debit":
        return acct.initial_balance + debit - credit
    return acct.initial_balance + credit - debit


def _sum_by_prefix(prefix: str, db: Session, company_id: int, end_date: str) -> float:
    """汇总所有以 prefix 开头的科目余额，使用 recursive parent_code 层级遍历。"""
    accounts = (
        db.query(Account)
        .filter(
            Account.company_id == company_id,
            Account.code.like(f"{prefix}%"),
        )
        .all()
    )
    if not accounts:
        return 0.0
    accts_by_code = {a.code: a for a in accounts}

    # 找出该 prefix 下的顶级科目（parent_code 不在本次结果集中）
    codes_in_set = set(accts_by_code.keys())
    top_level = [a for a in accounts if a.parent_code not in codes_in_set]

    total = 0.0
    seen = set()
    for a in top_level:
        leaves = _get_leaf_descendants(a.code, accts_by_code)
        for leaf in leaves:
            if leaf.code not in seen:
                seen.add(leaf.code)
                total += _calc_account_ending(leaf.code, db, company_id, end_date)
    return round(total, 2)


def _sum_occurrence_by_prefix(prefix: str, db: Session, company_id: int, start: str, end: str) -> float:
    """汇总以 prefix 开头的科目在期间内的净发生额，使用 recursive parent_code 层级遍历。"""
    accounts = (
        db.query(Account)
        .filter(
            Account.company_id == company_id,
            Account.code.like(f"{prefix}%"),
        )
        .all()
    )
    if not accounts:
        return 0.0
    accts_by_code = {a.code: a for a in accounts}

    # 找出该 prefix 下的顶级科目
    codes_in_set = set(accts_by_code.keys())
    top_level = [a for a in accounts if a.parent_code not in codes_in_set]

    total = 0.0
    seen = set()
    for a in top_level:
        leaves = _get_leaf_descendants(a.code, accts_by_code)
        for leaf in leaves:
            if leaf.code in seen:
                continue
            seen.add(leaf.code)
            q = (
                db.query(VoucherEntry)
                .join(Voucher)
                .filter(
                    Voucher.company_id == company_id,
                    VoucherEntry.account_code == leaf.code,
                    Voucher.status.in_(["posted", "closed"]),
                    Voucher.date >= start,
                    Voucher.date <= end,
                )
            )
            entries = q.all()
            debit = sum(e.debit for e in entries)
            credit = sum(e.credit for e in entries)
            if leaf.balance_direction == "debit":
                total += debit - credit
            else:
                total += credit - debit
    return round(total, 2)


def _has_data(db: Session, company_id: int) -> bool:
    """检查公司是否有已记账凭证。"""
    return db.query(Voucher).filter(Voucher.company_id == company_id, Voucher.status.in_(["posted", "closed"])).count() > 0


# ═══════════════════════════════════════════
# 1. 公司预算与绩效评价
# ═══════════════════════════════════════════


@router.get("/budget")
def get_budget(user: User = Depends(get_current_user)):
    """读取公司预算与绩效评价表，返回行列数据供前端渲染"""
    return {
        "message": "预算数据端点就绪，使用Excel导入",
        "rows": [],
        "summary": {
            "total_revenue": 0,
            "total_cost": 0,
            "gross_profit": 0,
            "operating_expense": 0,
            "admin_expense": 0,
            "finance_expense": 0,
            "pretax_profit": 0,
            "income_tax": 0,
            "net_profit": 0,
            "revenue_completion": 0,
            "profit_completion": 0,
        },
    }


# ═══════════════════════════════════════════
# 2. 现金流计划与融资计划
# ═══════════════════════════════════════════


@router.get("/cashflow-plan")
def get_cashflow_plan_summary(user: User = Depends(get_current_user)):
    return {
        "message": "现金流计划数据端点就绪",
        "rows": [],
        "summary": {
            "beginning_balance": 0,
            "actual_inflow": 0,
            "actual_outflow": 0,
            "ending_balance": 0,
            "equity_financing": 0,
            "debt_financing": 0,
            "cash_safety_days": 0,
        },
    }


# ═══════════════════════════════════════════
# 3. 公司经营分析指标
# ═══════════════════════════════════════════

INDICATOR_DEFS = [
    # 偿债能力
    {
        "dimension": "偿债能力",
        "name": "流动比率",
        "key": "current_ratio",
        "unit": "%",
        "green_min": 150,
        "yellow_min": 100,
    },
    {
        "dimension": "偿债能力",
        "name": "速动比率",
        "key": "quick_ratio",
        "unit": "%",
        "green_min": 100,
        "yellow_min": 50,
    },
    {
        "dimension": "偿债能力",
        "name": "现金流动负债比",
        "key": "cash_current_liab_ratio",
        "unit": "%",
        "green_min": 50,
        "yellow_min": 20,
    },
    {
        "dimension": "偿债能力",
        "name": "资产负债率",
        "key": "debt_ratio",
        "unit": "%",
        "green_max": 50,
        "yellow_max": 70,
    },
    {
        "dimension": "偿债能力",
        "name": "利息保障倍数",
        "key": "interest_coverage",
        "unit": "倍",
        "green_min": 3,
        "yellow_min": 1,
    },
    # 营运能力
    {
        "dimension": "营运能力",
        "name": "应收帐款周转率",
        "key": "ar_turnover",
        "unit": "次",
        "green_min": 6,
        "yellow_min": 3,
    },
    {
        "dimension": "营运能力",
        "name": "存货周转率",
        "key": "inventory_turnover",
        "unit": "次",
        "green_min": 5,
        "yellow_min": 2,
    },
    {
        "dimension": "营运能力",
        "name": "流动资产周转率",
        "key": "current_asset_turnover",
        "unit": "次",
        "green_min": 2,
        "yellow_min": 1,
    },
    {
        "dimension": "营运能力",
        "name": "总资产周转率",
        "key": "total_asset_turnover",
        "unit": "次",
        "green_min": 0.8,
        "yellow_min": 0.4,
    },
    # 盈利能力
    {"dimension": "盈利能力", "name": "毛利率", "key": "gross_margin", "unit": "%", "green_min": 30, "yellow_min": 15},
    {
        "dimension": "盈利能力",
        "name": "营业利润率",
        "key": "operating_margin",
        "unit": "%",
        "green_min": 15,
        "yellow_min": 5,
    },
    {"dimension": "盈利能力", "name": "总资产回报率(ROA)", "key": "roa", "unit": "%", "green_min": 5, "yellow_min": 2},
    {"dimension": "盈利能力", "name": "净资产回报率(ROE)", "key": "roe", "unit": "%", "green_min": 10, "yellow_min": 5},
    {
        "dimension": "盈利能力",
        "name": "成本费用率",
        "key": "cost_expense_ratio",
        "unit": "%",
        "green_max": 80,
        "yellow_max": 95,
    },
    # 成长能力
    {
        "dimension": "成长能力",
        "name": "营业收入增长率",
        "key": "revenue_growth",
        "unit": "%",
        "green_min": 15,
        "yellow_min": 5,
    },
    {
        "dimension": "成长能力",
        "name": "净利润增长率",
        "key": "profit_growth",
        "unit": "%",
        "green_min": 10,
        "yellow_min": 0,
    },
    {
        "dimension": "成长能力",
        "name": "总资产增长率",
        "key": "asset_growth",
        "unit": "%",
        "green_min": 10,
        "yellow_min": 0,
    },
    {
        "dimension": "成长能力",
        "name": "资本积累率",
        "key": "capital_accum_rate",
        "unit": "%",
        "green_min": 8,
        "yellow_min": 0,
    },
    {
        "dimension": "成长能力",
        "name": "研发经费投入强度",
        "key": "rd_intensity",
        "unit": "%",
        "green_min": 5,
        "yellow_min": 2,
    },
]


def _traffic_light(
    value: float | None,
    green_min: float | None = None,
    yellow_min: float | None = None,
    green_max: float | None = None,
    yellow_max: float | None = None,
) -> str:
    """根据阈值返回 red / yellow / green / gray。
    gray = 无数据（公司尚无财务数据）。
    """
    if value is None:
        return "gray"
    if green_min is not None and yellow_min is not None:
        if value >= green_min:
            return "green"
        elif value >= yellow_min:
            return "yellow"
        else:
            return "red"
    if green_max is not None and yellow_max is not None:
        if value <= green_max:
            return "green"
        elif value <= yellow_max:
            return "yellow"
        else:
            return "red"
    return "gray"


def _compute_indicators(db: Session, company_id: int, period: str) -> dict[str, float | None]:
    """从实际财务数据计算经营指标。"""
    end_date = _period_end_date(period)
    result: dict[str, float | None] = {}

    # ── 从资产负债表提取关键数据 ──
    # 流动资产科目：以 1 开头的科目（1001 库存现金 ~ 19xx）
    current_assets = _sum_by_prefix("1", db, company_id, end_date)
    # 排除非流动资产：以 15/16/17/18 开头的通常是非流动的
    noncurrent_in_current = (
        _sum_by_prefix("15", db, company_id, end_date)
        + _sum_by_prefix("16", db, company_id, end_date)
        + _sum_by_prefix("18", db, company_id, end_date)
    )
    current_assets = current_assets - noncurrent_in_current

    # 总资产 = 所有资产科目
    total_assets = 0.0
    asset_categories = ["1"]  # 资产类
    for cat in asset_categories:
        total_assets += _sum_by_prefix(cat, db, company_id, end_date)

    # 流动负债：2001, 22xx, 2231, 2232, 2241
    current_liabilities = (
        _sum_by_prefix("2001", db, company_id, end_date)
        + _sum_by_prefix("22", db, company_id, end_date)
        + _sum_by_prefix("2231", db, company_id, end_date)
        + _sum_by_prefix("2232", db, company_id, end_date)
        + _sum_by_prefix("2241", db, company_id, end_date)
    )

    # 总负债 = 2 开头的科目
    total_liabilities = _sum_by_prefix("2", db, company_id, end_date)

    # 所有者权益 = 3/4 开头
    total_equity = _sum_by_prefix("3", db, company_id, end_date) + _sum_by_prefix("4", db, company_id, end_date)

    # 存货 = 1405 + 1406 等
    inventory = (
        _sum_by_prefix("1405", db, company_id, end_date)
        + _sum_by_prefix("1406", db, company_id, end_date)
        + _sum_by_prefix("1407", db, company_id, end_date)
        + _sum_by_prefix("1408", db, company_id, end_date)
    )

    # ── 从利润表提取数据 ──
    year_start = f"{period[:4]}-01-01"
    # 营业收入 = 60xx 科目
    revenue = _sum_occurrence_by_prefix("60", db, company_id, year_start, end_date)
    # 营业成本 = 64xx 科目
    cost = _sum_occurrence_by_prefix("64", db, company_id, year_start, end_date)
    # 净利润 ≈ 收入 - 成本 - 费用（简化）
    # 销售/管理/财务费用
    selling_exp = _sum_occurrence_by_prefix("6601", db, company_id, year_start, end_date)
    admin_exp = _sum_occurrence_by_prefix("6602", db, company_id, year_start, end_date)
    finance_exp = _sum_occurrence_by_prefix("6603", db, company_id, year_start, end_date)

    net_income = revenue - cost - selling_exp - admin_exp - finance_exp

    # ── 计算指标 ──
    # 偿债能力
    if current_liabilities != 0:
        result["current_ratio"] = round(current_assets / abs(current_liabilities) * 100, 1)
        quick_assets = current_assets - inventory
        result["quick_ratio"] = round(quick_assets / abs(current_liabilities) * 100, 1)
    else:
        result["current_ratio"] = None
        result["quick_ratio"] = None

    # 现金流动负债比 — 需要经营现金流，暂无简单计算
    result["cash_current_liab_ratio"] = None

    if total_assets != 0:
        result["debt_ratio"] = round(abs(total_liabilities) / total_assets * 100, 1)
    else:
        result["debt_ratio"] = None

    # 利息保障倍数 — 需要利息费用数据
    result["interest_coverage"] = None

    # 营运能力 — 需要期初期末平均值
    result["ar_turnover"] = None
    result["inventory_turnover"] = None

    if total_assets != 0 and revenue != 0:
        result["current_asset_turnover"] = round(abs(revenue) / current_assets, 1) if current_assets != 0 else None
        result["total_asset_turnover"] = round(abs(revenue) / total_assets, 1)
    else:
        result["current_asset_turnover"] = None
        result["total_asset_turnover"] = None

    # 盈利能力
    if revenue != 0:
        result["gross_margin"] = round((revenue - cost) / abs(revenue) * 100, 1) if revenue - cost != 0 else None
        result["operating_margin"] = round(net_income / abs(revenue) * 100, 1) if net_income != 0 else None
    else:
        result["gross_margin"] = None
        result["operating_margin"] = None

    if total_assets != 0:
        result["roa"] = round(net_income / total_assets * 100, 1) if net_income != 0 else None
    else:
        result["roa"] = None

    if total_equity != 0:
        result["roe"] = round(net_income / abs(total_equity) * 100, 1) if net_income != 0 else None
    else:
        result["roe"] = None

    if revenue != 0:
        result["cost_expense_ratio"] = round((cost + selling_exp + admin_exp + finance_exp) / abs(revenue) * 100, 1)
    else:
        result["cost_expense_ratio"] = None

    # 成长能力 — 需要去年同期数据进行比较，暂不计算
    result["revenue_growth"] = None
    result["profit_growth"] = None
    result["asset_growth"] = None
    result["capital_accum_rate"] = None
    result["rd_intensity"] = None

    return result


@router.get("/indicators")
def get_indicators(
    company_id: int = Query(...),
    period: str = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """返回经营指标定义及当前值/红黄绿灯判定。基于实际财务数据计算。"""
    if not period:
        from datetime import date

        today = date.today()
        period = f"{today.year}-{today.month:02d}"

    values = _compute_indicators(db, company_id, period)

    items = []
    for d in INDICATOR_DEFS:
        v = values.get(d["key"])
        light = _traffic_light(
            v,
            green_min=d.get("green_min"),
            yellow_min=d.get("yellow_min"),
            green_max=d.get("green_max"),
            yellow_max=d.get("yellow_max"),
        )
        items.append({**d, "value": v, "light": light})

    # 按维度汇总红黄绿灯
    dimensions: dict[str, dict] = {}
    for item in items:
        dim = item["dimension"]
        if dim not in dimensions:
            dimensions[dim] = {"items": [], "lights": []}
        dimensions[dim]["items"].append(item)
        dimensions[dim]["lights"].append(item["light"])

    # 每个维度的总体灯：灰>0=灰，红>0=红，黄>0=黄，全绿=绿
    summary: dict[str, str] = {}
    for dim, data in dimensions.items():
        if "red" in data["lights"]:
            summary[dim] = "red"
        elif "yellow" in data["lights"]:
            summary[dim] = "yellow"
        elif "gray" in data["lights"]:
            summary[dim] = "gray"
        else:
            summary[dim] = "green"

    return {"items": items, "dimensions": dimensions, "summary": summary}


# 驾驶舱综合R/Y/G — 六项
@router.get("/cockpit-lights")
def get_cockpit_lights(
    company_id: int = Query(...),
    period: str = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """返回财务管理驾驶舱六项指示灯状态。基于实际数据判定。"""
    if not period:
        from datetime import date

        today = date.today()
        period = f"{today.year}-{today.month:02d}"

    if not _has_data(db, company_id):
        # 无数据 → 全部灰色
        return {
            "预算完成表现": "gray",
            "现金流安全": "gray",
            "偿债能力": "gray",
            "营运能力": "gray",
            "盈利能力": "gray",
            "成长能力": "gray",
        }

    # 从 indicators 获取各维度汇总状态
    indicators_result = get_indicators(company_id=company_id, period=period, db=db, user=user)
    dim_summary = indicators_result["summary"]

    return {
        "预算完成表现": _get_budget_light(db, company_id, period),
        "现金流安全": _get_cashflow_light(db, company_id, period),
        "偿债能力": dim_summary.get("偿债能力", "gray"),
        "营运能力": dim_summary.get("营运能力", "gray"),
        "盈利能力": dim_summary.get("盈利能力", "gray"),
        "成长能力": dim_summary.get("成长能力", "gray"),
    }


def _get_budget_light(db: Session, company_id: int, period: str) -> str:
    """预算完成表现：检查是否有预算数据。"""
    from app.models import Budget

    year = int(period[:4])
    budgets = db.query(Budget).filter(Budget.company_id == company_id, Budget.year == year).count()
    if budgets == 0:
        return "gray"
    # 有预算数据 → 简单判定（后续可增强为实际vs预算比较）
    return "green"


def _get_cashflow_light(db: Session, company_id: int, period: str) -> str:
    """现金流安全：检查期末现金余额是否为正。"""
    end_date = _period_end_date(period)
    # 货币资金 = 1001(库存现金) + 1002(银行存款) + 1003(其他货币资金)
    cash = (
        _sum_by_prefix("1001", db, company_id, end_date)
        + _sum_by_prefix("1002", db, company_id, end_date)
        + _sum_by_prefix("1003", db, company_id, end_date)
    )
    if cash <= 0:
        return "red"
    if cash < 100000:  # 现金低于10万 → 黄灯
        return "yellow"
    return "green"


# ═══════════════════════════════════════════
# 4. 现金流计划 CRUD
# ═══════════════════════════════════════════


class CFPlanItemCreate(PydanticBase):
    account_code: str
    month: str
    amount: float = 0.0


class CFPlanCreate(PydanticBase):
    company_id: int
    name: str
    year: int
    items: List[CFPlanItemCreate] = []


class CFPlanUpdate(PydanticBase):
    name: Optional[str] = None
    items: Optional[List[CFPlanItemCreate]] = None


@router.get("/cashflow-plan/list")
def list_cashflow_plans(
    company_id: int = Query(...),
    year: int = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(CashflowPlan).filter(CashflowPlan.company_id == company_id)
    if year:
        q = q.filter(CashflowPlan.year == year)
    plans = q.order_by(CashflowPlan.year.desc()).all()
    return [
        {
            "id": p.id,
            "company_id": p.company_id,
            "name": p.name,
            "year": p.year,
            "status": p.status,
            "items": [
                {"id": i.id, "account_code": i.account_code, "month": i.month, "amount": i.amount} for i in p.items
            ],
        }
        for p in plans
    ]


@router.get("/cashflow-plan/{plan_id}")
def get_cashflow_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    p = db.query(CashflowPlan).filter(CashflowPlan.id == plan_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="现金流计划不存在")
    return {
        "id": p.id,
        "company_id": p.company_id,
        "name": p.name,
        "year": p.year,
        "status": p.status,
        "items": [{"id": i.id, "account_code": i.account_code, "month": i.month, "amount": i.amount} for i in p.items],
    }


@router.post("/cashflow-plan")
def create_cashflow_plan(
    data: CFPlanCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    plan = CashflowPlan(company_id=data.company_id, name=data.name, year=data.year, created_by=user.id)
    db.add(plan)
    db.flush()
    for item_data in data.items:
        db.add(
            CashflowPlanItem(
                plan_id=plan.id, account_code=item_data.account_code, month=item_data.month, amount=item_data.amount
            )
        )
    db.commit()
    db.refresh(plan)
    return {"id": plan.id, "name": plan.name, "year": plan.year, "status": plan.status}


@router.put("/cashflow-plan/{plan_id}")
def update_cashflow_plan(
    plan_id: int,
    data: CFPlanUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    plan = db.query(CashflowPlan).filter(CashflowPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="现金流计划不存在")
    if data.name is not None:
        plan.name = data.name
    if data.items is not None:
        db.query(CashflowPlanItem).filter(CashflowPlanItem.plan_id == plan.id).delete()
        for item_data in data.items:
            db.add(
                CashflowPlanItem(
                    plan_id=plan.id, account_code=item_data.account_code, month=item_data.month, amount=item_data.amount
                )
            )
    db.commit()
    return {"ok": True}


@router.delete("/cashflow-plan/{plan_id}")
def delete_cashflow_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    plan = db.query(CashflowPlan).filter(CashflowPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="现金流计划不存在")
    db.delete(plan)
    db.commit()
    return {"ok": True}
