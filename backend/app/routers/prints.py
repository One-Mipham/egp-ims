"""打印模块路由：公司信息、部门、科目表、科目余额表、总账、凭证、月/季/年报。"""
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Company, Department, Account, Voucher, VoucherEntry, AccountingPeriod, Counterparty, Person, Project
from app.auth import get_current_user
from app.routers.reports import (
    _period_end_date, _year_start, _prev_year_period,
    _calc_ending, _occurrence,
    BS_ROWS, IS_ROWS,
    _compute_cash_flows, _is_cash_account,
    CASH_CODES,
)

router = APIRouter()


def _get_company(db: Session, company_id: int) -> Company:
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="公司不存在")
    return company


# ──────────────── 公司信息 ────────────────

@router.get("/company")
def print_company(company_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    company = _get_company(db, company_id)
    return {
        "name": company.name,
        "short_name": company.short_name,
        "industry": company.industry,
        "currency": company.currency,
        "fiscal_year_start": company.fiscal_year_start,
        "internal_control_mode": company.internal_control_mode,
    }


# ──────────────── 部门信息 ────────────────

@router.get("/departments")
def print_departments(company_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _get_company(db, company_id)
    depts = db.query(Department).filter(
        Department.company_id == company_id,
    ).order_by(Department.code).all()
    return [
        {"code": d.code, "name": d.name, "manager": d.manager, "is_active": d.is_active}
        for d in depts
    ]


# ──────────────── 科目表 ────────────────

@router.get("/subjects")
def print_subjects(
    company_id: int,
    level: Optional[int] = Query(None, ge=1, le=4),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _get_company(db, company_id)
    q = db.query(Account).filter(Account.company_id == company_id, Account.is_active == True)
    if level is not None:
        q = q.filter(Account.level == level)
    accts = q.order_by(Account.code).all()
    LEVEL_LABELS = {1: "一级科目", 2: "二级科目", 3: "三级科目", 4: "四级科目"}
    return [
        {
            "code": a.code,
            "name": a.name,
            "level": LEVEL_LABELS.get(a.level, str(a.level)),
            "category": a.category,
            "balance_direction": a.balance_direction,
            "parent_code": a.parent_code,
        }
        for a in accts
    ]


# ──────────────── 科目余额表 ────────────────

@router.get("/subject-balance")
def print_subject_balance(
    company_id: int,
    period: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _get_company(db, company_id)
    end_date = _period_end_date(period)
    prev_period_end = _period_end_date(f"{int(period[:4])}-{int(period[5:7]) - 1:02d}" if int(period[5:7]) > 1 else f"{int(period[:4]) - 1}-12")

    accts = db.query(Account).filter(
        Account.company_id == company_id,
        Account.is_active == True,
    ).order_by(Account.code).all()

    rows = []
    for a in accts:
        beginning = _calc_ending(a, db, company_id, period[:4] + "-01-01")
        # 本期发生
        d, c = _occurrence(a, db, company_id, period + "-01", end_date)
        ending = _calc_ending(a, db, company_id, end_date)
        rows.append({
            "code": a.code,
            "name": a.name,
            "beginning": round(beginning, 2),
            "debit": round(d, 2),
            "credit": round(c, 2),
            "ending": round(ending, 2),
        })

    return {"period": period, "rows": rows}


# ──────────────── 总账余额表 ────────────────

@router.get("/general-ledger")
def print_general_ledger(
    company_id: int,
    period: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _get_company(db, company_id)
    end_date = _period_end_date(period)
    # 只取一级科目
    accts = db.query(Account).filter(
        Account.company_id == company_id,
        Account.level == 1,
        Account.is_active == True,
    ).order_by(Account.code).all()

    rows = []
    for a in accts:
        beginning = _calc_ending(a, db, company_id, period[:4] + "-01-01")
        d, c = _occurrence(a, db, company_id, period + "-01", end_date)
        ending = _calc_ending(a, db, company_id, end_date)
        rows.append({
            "code": a.code,
            "name": a.name,
            "beginning": round(beginning, 2),
            "debit": round(d, 2),
            "credit": round(c, 2),
            "ending": round(ending, 2),
        })

    return {"period": period, "rows": rows}


# ──────────────── 凭证打印 ────────────────

@router.get("/vouchers")
def print_vouchers(
    company_id: int,
    range: str = Query("month", pattern="^(today|week|month)$"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _get_company(db, company_id)
    now = datetime.now(timezone(timedelta(hours=8)))
    today = now.strftime("%Y-%m-%d")
    if range == "today":
        start, end = today, today
    elif range == "week":
        monday = now - timedelta(days=now.weekday())
        start = monday.strftime("%Y-%m-%d")
        end = today
    else:
        start = now.strftime("%Y-%m") + "-01"
        end = today

    vouchers = db.query(Voucher).filter(
        Voucher.company_id == company_id,
        Voucher.date >= start,
        Voucher.date <= end,
    ).order_by(Voucher.date).all()

    result = []
    for v in vouchers:
        entries = db.query(VoucherEntry).filter(VoucherEntry.voucher_id == v.id).all()
        entry_data = []
        for e in entries:
            dept_name = db.query(Department).filter(Department.id == e.department_id).first() if e.department_id else None
            cp_name = db.query(Counterparty).filter(Counterparty.id == e.counterparty_id).first() if e.counterparty_id else None
            p_name = db.query(Person).filter(Person.id == e.person_id).first() if e.person_id else None
            pr_name = db.query(Project).filter(Project.id == e.project_id).first() if e.project_id else None
            entry_data.append({
                "account_code": e.account_code,
                "debit": e.debit,
                "credit": e.credit,
                "description": e.description,
                "department_name": dept_name.name if dept_name else None,
                "counterparty_name": cp_name.name if cp_name else None,
                "person_name": p_name.name if p_name else None,
                "project_name": pr_name.name if pr_name else None,
            })
        result.append({
            "id": v.id,
            "date": v.date,
            "voucher_no": v.voucher_no,
            "voucher_type": v.voucher_type,
            "summary": v.summary,
            "status": v.status,
            "entries": entry_data,
        })
    return {"range": range, "start": start, "end": end, "vouchers": result}


# ──────────────── 月报/季报/年报 ────────────────

def _get_report_data(db: Session, company_id: int, period: str, report: str):
    end_date = _period_end_date(period)
    ys = _year_start(period)
    py_end = _period_end_date(_prev_year_period(period))
    py_ys = _year_start(_prev_year_period(period))

    accts = {a.code: a for a in db.query(Account).filter(Account.company_id == company_id).all()}
    parent_codes = set()
    for a in accts.values():
        if a.parent_code:
            parent_codes.add(a.parent_code)

    if report == "balance":
        def _calc(code_str):
            if not code_str or code_str in ("CURRENT_TOTAL", "NCURRENT_TOTAL", "ASSET_TOTAL", "LIABILITY_TOTAL", "EQUITY_TOTAL", "TOTAL"):
                return 0.0
            codes = [c.strip() for c in code_str.split(",") if c.strip()]
            total = 0.0
            for code in codes:
                children = [a for a in accts.values() if a.code.startswith(code) and a.code not in parent_codes]
                if not children and code in accts and code not in parent_codes:
                    children = [accts[code]]
                for a in children:
                    total += _calc_ending(a, db, company_id, end_date)
            return round(total, 2)

        left_items, right_items = [], []
        for name, side, codes in BS_ROWS:
            val = _calc(codes)
            item = {"name": name, "ending": val, "beginning": 0.0}
            if side == "left":
                left_items.append(item)
            else:
                right_items.append(item)

        for item in left_items:
            if item["name"] == "流动资产合计":
                item["ending"] = round(sum(i["ending"] for i in left_items[:10]), 2)
            elif item["name"] == "非流动资产合计":
                item["ending"] = round(sum(i["ending"] for i in left_items[11:29]), 2)
            elif item["name"] == "资产总计":
                item["ending"] = round(left_items[10]["ending"] + left_items[29]["ending"], 2)

        for item in right_items:
            if item["name"] == "流动负债合计":
                item["ending"] = round(sum(i["ending"] for i in right_items[:12]), 2)
            elif item["name"] == "非流动负债合计":
                item["ending"] = round(sum(i["ending"] for i in right_items[13:21]), 2)
            elif item["name"] == "负债合计":
                item["ending"] = round(right_items[12]["ending"] + right_items[21]["ending"], 2)
            elif item["name"] == "所有者权益合计":
                item["ending"] = round(sum(i["ending"] for i in right_items[23:28]), 2)
            elif item["name"] == "负债和所有者权益总计":
                item["ending"] = round(right_items[22]["ending"] + right_items[28]["ending"], 2)

        y, m = int(period[:4]), int(period[5:7])
        last_day = 31 if m in (1, 3, 5, 7, 8, 10, 12) else (30 if m in (4, 6, 9, 11) else 28)
        return {"type": "balance", "date_display": f"{y} 年 {m:02d} 月 {last_day} 日", "left_items": left_items, "right_items": right_items}

    elif report == "income":
        def _calc(code_str, start, end):
            if not code_str:
                return 0.0
            codes = [c.strip() for c in code_str.split(",") if c.strip()]
            total = 0.0
            for code in codes:
                children = [a for a in accts.values() if a.code.startswith(code) and a.code not in parent_codes]
                if not children and code in accts and code not in parent_codes:
                    children = [accts[code]]
                for a in children:
                    exclude_xfer = (a.category == "profit_loss")
                    d, c = _occurrence(a, db, company_id, start, end, exclude_transfer=exclude_xfer)
                    if a.category == "profit_loss":
                        if a.code.startswith(("64", "66", "67", "68")):
                            total += d
                        else:
                            total += c
            return round(total, 2)

        month_start = period + "-01"
        items = []
        for name, codes in IS_ROWS:
            if codes in ("OP_PROFIT", "TOTAL_PROFIT", "NET_PROFIT"):
                items.append({"name": name, "curr": 0, "ytd": 0, "prev": 0, "formula": codes})
            else:
                items.append({
                    "name": name,
                    "curr": round(_calc(codes, month_start, end_date), 2),
                    "ytd": round(_calc(codes, ys, end_date), 2),
                    "prev": round(_calc(codes, py_ys, py_end), 2),
                    "formula": "",
                })

        for item in items:
            f = item.get("formula", "")
            if f == "OP_PROFIT":
                op = items[0]["curr"] - items[1]["curr"] - items[2]["curr"] - items[3]["curr"] - items[4]["curr"] - items[5]["curr"] - items[6]["curr"]
                item["curr"] = round(op, 2)
            elif f == "TOTAL_PROFIT":
                op = next(i["curr"] for i in items if i.get("formula") == "OP_PROFIT")
                nonop = items[10]["curr"] - items[11]["curr"]
                item["curr"] = round(op + nonop, 2)
            elif f == "NET_PROFIT":
                tp = next(i["curr"] for i in items if i.get("formula") == "TOTAL_PROFIT")
                item["curr"] = round(tp - items[13]["curr"], 2)

        for col in ("ytd", "prev"):
            s = ys if col == "ytd" else py_ys
            e = end_date if col == "ytd" else py_end
            def _calc_col(code_str):
                if not code_str:
                    return 0.0
                return _calc(code_str, s, e)
            vals = {}
            for item in items:
                if item.get("formula", "") in ("OP_PROFIT", "TOTAL_PROFIT", "NET_PROFIT"):
                    continue
                vals[item["name"]] = round(_calc_col(next((codes for n, codes in IS_ROWS if n == item["name"]), "")), 2)
            for item in items:
                f = item.get("formula", "")
                if f == "OP_PROFIT":
                    item[col] = round(vals["一、营业收入"] - vals["    减：营业成本"] - vals["        税金及附加"] - vals["        销售费用"] - vals["        管理费用"] - vals["        财务费用"] - vals["        资产减值损失"], 2)
                elif f == "TOTAL_PROFIT":
                    op = next(i[col] for i in items if i.get("formula") == "OP_PROFIT")
                    item[col] = round(op + vals["    加：营业外收入"] - vals["    减：营业外支出"], 2)
                elif f == "NET_PROFIT":
                    tp = next(i[col] for i in items if i.get("formula") == "TOTAL_PROFIT")
                    item[col] = round(tp - vals["    减：所得税费用"], 2)

        y, m = int(period[:4]), int(period[5:7])
        return {"type": "income", "period_display": f"{y} 年 {m:02d} 月", "items": items}

    elif report == "cashflow":
        from app.models import CashFlowItem

        cf_items = {cfi.code: cfi for cfi in db.query(CashFlowItem).filter(
            CashFlowItem.company_id == company_id, CashFlowItem.is_active == True
        ).all()}

        curr_items = _compute_cash_flows(db, company_id, ys, end_date)

        # Compute 6-category totals from per-item data
        op_in = sum(v for k, v in curr_items.items() if cf_items.get(k) and cf_items[k].category_code and cf_items[k].category_code.startswith("op_") and cf_items[k].direction == "inflow")
        op_out = sum(v for k, v in curr_items.items() if cf_items.get(k) and cf_items[k].category_code and cf_items[k].category_code.startswith("op_") and cf_items[k].direction == "outflow")
        inv_in = sum(v for k, v in curr_items.items() if cf_items.get(k) and cf_items[k].category_code and cf_items[k].category_code.startswith("inv_") and cf_items[k].direction == "inflow")
        inv_out = sum(v for k, v in curr_items.items() if cf_items.get(k) and cf_items[k].category_code and cf_items[k].category_code.startswith("inv_") and cf_items[k].direction == "outflow")
        fin_in = sum(v for k, v in curr_items.items() if cf_items.get(k) and cf_items[k].category_code and cf_items[k].category_code.startswith("fin_") and cf_items[k].direction == "inflow")
        fin_out = sum(v for k, v in curr_items.items() if cf_items.get(k) and cf_items[k].category_code and cf_items[k].category_code.startswith("fin_") and cf_items[k].direction == "outflow")

        all_accts = db.query(Account).filter(Account.company_id == company_id).all()
        accts_cf = {a.code: a for a in all_accts if _is_cash_account(a.code, CASH_CODES)}
        beginning_balance = sum(_calc_ending(a, db, company_id, ys) for a in accts_cf.values())

        op_in = round(op_in, 2); op_out = round(op_out, 2)
        inv_in = round(inv_in, 2); inv_out = round(inv_out, 2)
        fin_in = round(fin_in, 2); fin_out = round(fin_out, 2)

        net_operating = round(op_in - op_out, 2)
        net_investing = round(inv_in - inv_out, 2)
        net_financing = round(fin_in - fin_out, 2)
        net_change = round(net_operating + net_investing + net_financing, 2)
        ending_balance = round(beginning_balance + net_change, 2)

        y, m = int(period[:4]), int(period[5:7])
        last_day = 31 if m in (1, 3, 5, 7, 8, 10, 12) else (30 if m in (4, 6, 9, 11) else 28)
        rows = [
            ("一、经营活动产生的现金流量：", "", "", ""),
            ("     销售商品、提供劳务收到的现金", op_in, op_in, 0.0),
            ("     经营活动现金流入小计", op_in, op_in, 0.0),
            ("     支付其它与经营活动有关的现金", op_out, op_out, 0.0),
            ("     经营活动现金流出小计", op_out, op_out, 0.0),
            ("     经营活动产生的现金流量净额", net_operating, net_operating, 0.0),
            ("二、投资活动产生的现金流量：", "", "", ""),
            ("     收回投资收到的现金", inv_in, inv_in, 0.0),
            ("     投资活动现金流入小计", inv_in, inv_in, 0.0),
            ("     投资支付的现金", inv_out, inv_out, 0.0),
            ("     投资活动现金流出小计", inv_out, inv_out, 0.0),
            ("     投资活动产生的现金流量净额", net_investing, net_investing, 0.0),
            ("三、筹资活动产生的现金流量：", "", "", ""),
            ("     吸收投资收到的现金", fin_in, fin_in, 0.0),
            ("     筹资活动现金流入小计", fin_in, fin_in, 0.0),
            ("     支付其他与筹资活动有关的现金", fin_out, fin_out, 0.0),
            ("     筹资活动现金流出小计", fin_out, fin_out, 0.0),
            ("     筹资活动产生的现金流量净额", net_financing, net_financing, 0.0),
            ("五、现金及现金等价物净增加额", net_change, net_change, 0.0),
            ("        加：期初现金及现金等价物余额", round(beginning_balance, 2), round(beginning_balance, 2), 0.0),
            ("六、期末现金及现金等价物余额", ending_balance, ending_balance, 0.0),
        ]
        return {"type": "cashflow", "date_display": f"{y} 年 {m:02d} 月 {last_day} 日", "rows": rows}

    raise HTTPException(status_code=400, detail="报表类型不支持")


@router.get("/periodic")
def print_periodic(
    company_id: int,
    period: str,
    report: str = Query("balance", pattern="^(balance|income|cashflow)$"),
    type: str = Query("monthly", pattern="^(monthly|quarterly|yearly)$"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _get_company(db, company_id)
    return _get_report_data(db, company_id, period, report)
