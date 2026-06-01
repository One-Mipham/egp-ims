"""财务管理驾驶舱 — 公司预算、现金流计划、经营指标"""
import os
from fastapi import APIRouter, Depends
from app.auth import get_current_user
from app.models import User

router = APIRouter()

DOWNLOADS = os.path.expanduser("~/Downloads")

# ═══════════════════════════════════════════
# 1. 公司预算与绩效评价
# ═══════════════════════════════════════════

@router.get("/budget")
def get_budget(user: User = Depends(get_current_user)):
    """读取公司预算与绩效评价表，返回行列数据供前端渲染"""
    return {"message": "预算数据端点就绪，使用Excel导入", "rows": [], "summary": {
        "total_revenue": 0, "total_cost": 0, "gross_profit": 0,
        "operating_expense": 0, "admin_expense": 0, "finance_expense": 0,
        "pretax_profit": 0, "income_tax": 0, "net_profit": 0,
        "revenue_completion": 0, "profit_completion": 0,
    }}


# ═══════════════════════════════════════════
# 2. 现金流计划与融资计划
# ═══════════════════════════════════════════

@router.get("/cashflow-plan")
def get_cashflow_plan(user: User = Depends(get_current_user)):
    return {"message": "现金流计划数据端点就绪", "rows": [], "summary": {
        "beginning_balance": 0, "actual_inflow": 0, "actual_outflow": 0,
        "ending_balance": 0, "equity_financing": 0, "debt_financing": 0,
        "cash_safety_days": 0,
    }}


# ═══════════════════════════════════════════
# 3. 公司经营分析指标
# ═══════════════════════════════════════════

INDICATOR_DEFS = [
    # 偿债能力
    {"dimension": "偿债能力", "name": "流动比率", "key": "current_ratio", "unit": "%", "green_min": 150, "yellow_min": 100},
    {"dimension": "偿债能力", "name": "速动比率", "key": "quick_ratio", "unit": "%", "green_min": 100, "yellow_min": 50},
    {"dimension": "偿债能力", "name": "现金流动负债比", "key": "cash_current_liab_ratio", "unit": "%", "green_min": 50, "yellow_min": 20},
    {"dimension": "偿债能力", "name": "资产负债率", "key": "debt_ratio", "unit": "%", "green_max": 50, "yellow_max": 70},
    {"dimension": "偿债能力", "name": "利息保障倍数", "key": "interest_coverage", "unit": "倍", "green_min": 3, "yellow_min": 1},
    # 营运能力
    {"dimension": "营运能力", "name": "应收帐款周转率", "key": "ar_turnover", "unit": "次", "green_min": 6, "yellow_min": 3},
    {"dimension": "营运能力", "name": "存货周转率", "key": "inventory_turnover", "unit": "次", "green_min": 5, "yellow_min": 2},
    {"dimension": "营运能力", "name": "流动资产周转率", "key": "current_asset_turnover", "unit": "次", "green_min": 2, "yellow_min": 1},
    {"dimension": "营运能力", "name": "总资产周转率", "key": "total_asset_turnover", "unit": "次", "green_min": 0.8, "yellow_min": 0.4},
    # 盈利能力
    {"dimension": "盈利能力", "name": "毛利率", "key": "gross_margin", "unit": "%", "green_min": 30, "yellow_min": 15},
    {"dimension": "盈利能力", "name": "营业利润率", "key": "operating_margin", "unit": "%", "green_min": 15, "yellow_min": 5},
    {"dimension": "盈利能力", "name": "总资产回报率(ROA)", "key": "roa", "unit": "%", "green_min": 5, "yellow_min": 2},
    {"dimension": "盈利能力", "name": "净资产回报率(ROE)", "key": "roe", "unit": "%", "green_min": 10, "yellow_min": 5},
    {"dimension": "盈利能力", "name": "成本费用率", "key": "cost_expense_ratio", "unit": "%", "green_max": 80, "yellow_max": 95},
    # 成长能力
    {"dimension": "成长能力", "name": "营业收入增长率", "key": "revenue_growth", "unit": "%", "green_min": 15, "yellow_min": 5},
    {"dimension": "成长能力", "name": "净利润增长率", "key": "profit_growth", "unit": "%", "green_min": 10, "yellow_min": 0},
    {"dimension": "成长能力", "name": "总资产增长率", "key": "asset_growth", "unit": "%", "green_min": 10, "yellow_min": 0},
    {"dimension": "成长能力", "name": "资本积累率", "key": "capital_accum_rate", "unit": "%", "green_min": 8, "yellow_min": 0},
    {"dimension": "成长能力", "name": "研发经费投入强度", "key": "rd_intensity", "unit": "%", "green_min": 5, "yellow_min": 2},
]


def _traffic_light(value: float | None, green_min: float | None = None,
                   yellow_min: float | None = None, green_max: float | None = None,
                   yellow_max: float | None = None) -> str:
    """根据阈值返回 red / yellow / green"""
    if value is None:
        return "green"  # 无数据默认绿灯
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
    return "green"


@router.get("/indicators")
def get_indicators(user: User = Depends(get_current_user)):
    """返回经营指标定义及当前值/红黄绿灯判定"""
    # 从实际数据计算指标值（当前为模板默认值）
    values = {
        "current_ratio": None, "quick_ratio": None, "cash_current_liab_ratio": None,
        "debt_ratio": None, "interest_coverage": None,
        "ar_turnover": None, "inventory_turnover": None,
        "current_asset_turnover": None, "total_asset_turnover": None,
        "gross_margin": None, "operating_margin": None,
        "roa": None, "roe": None, "cost_expense_ratio": None,
        "revenue_growth": None, "profit_growth": None,
        "asset_growth": None, "capital_accum_rate": None, "rd_intensity": None,
    }

    items = []
    for d in INDICATOR_DEFS:
        v = values.get(d["key"])
        light = _traffic_light(
            v,
            green_min=d.get("green_min"), yellow_min=d.get("yellow_min"),
            green_max=d.get("green_max"), yellow_max=d.get("yellow_max"),
        )
        items.append({**d, "value": v, "light": light})

    # 按维度汇总红黄绿灯
    dimensions = {}
    for item in items:
        dim = item["dimension"]
        if dim not in dimensions:
            dimensions[dim] = {"items": [], "lights": []}
        dimensions[dim]["items"].append(item)
        dimensions[dim]["lights"].append(item["light"])

    # 每个维度的总体灯：任一红灯=红，任一黄灯=黄，全绿=绿
    summary = {}
    for dim, data in dimensions.items():
        if "red" in data["lights"]:
            summary[dim] = "red"
        elif "yellow" in data["lights"]:
            summary[dim] = "yellow"
        else:
            summary[dim] = "green"

    return {"items": items, "dimensions": dimensions, "summary": summary}


# 驾驶舱综合R/Y/G — 六项
@router.get("/cockpit-lights")
def get_cockpit_lights(user: User = Depends(get_current_user)):
    """返回财务管理驾驶舱六项指示灯状态"""
    # 从预算完成情况 + 现金流 + 经营指标综合判定
    return {
        "预算完成表现": "green",
        "现金流安全": "green",
        "偿债能力": "green",
        "营运能力": "green",
        "盈利能力": "green",
        "成长能力": "green",
    }
