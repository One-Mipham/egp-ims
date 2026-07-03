"""报表中心路由：资产负债表、利润表、现金流量表。"""
import calendar
from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Voucher, VoucherEntry, Account, CashFlowItem
from app.auth import get_current_user

router = APIRouter()


# ──────────────── 日期辅助函数 ────────────────

def _period_end_date(period: str) -> str:
    y, m = int(period[:4]), int(period[5:7])
    last_day = calendar.monthrange(y, m)[1]
    return f"{y}-{m:02d}-{last_day:02d}"


def _year_start(period: str) -> str:
    return f"{period[:4]}-01-01"


def _prev_year_period(period: str) -> str:
    y, m = int(period[:4]), int(period[5:7])
    return f"{y - 1:04d}-{m:02d}"


def _prev_year_end(period: str) -> str:
    """Return Dec 31 of the year before the given period."""
    return f"{int(period[:4]) - 1}-12-31"


# ──────────────── 余额计算 ────────────────

def _calc_ending(acct: Account, db: Session, company_id: int, end_date: str | None = None) -> float:
    q = db.query(VoucherEntry).join(Voucher).filter(
        Voucher.company_id == company_id,
        VoucherEntry.account_code == acct.code,
        Voucher.status == "posted",
    )
    if end_date:
        q = q.filter(Voucher.date <= end_date)
    entries = q.all()
    debit = sum(e.debit for e in entries)
    credit = sum(e.credit for e in entries)
    if acct.balance_direction == "debit":
        return acct.initial_balance + debit - credit
    return acct.initial_balance + credit - debit


def _occurrence(acct: Account, db: Session, company_id: int, start: str, end: str, exclude_transfer: bool = False) -> tuple[float, float]:
    q = db.query(VoucherEntry).join(Voucher).filter(
        Voucher.company_id == company_id,
        VoucherEntry.account_code == acct.code,
        Voucher.status == "posted",
        Voucher.date >= start,
        Voucher.date <= end,
    )
    if exclude_transfer:
        q = q.filter(~Voucher.summary.contains("结转"))
    entries = q.all()
    return sum(e.debit for e in entries), sum(e.credit for e in entries)


def _sum_codes(codes: list[str], db: Session, company_id: int, end_date: str | None = None) -> float:
    total = 0.0
    for acct in db.query(Account).filter(Account.company_id == company_id, Account.code.in_(codes)).all():
        total += _calc_ending(acct, db, company_id, end_date)
    return total


def _sum_occurrence(codes: list[str], db: Session, company_id: int, start: str, end: str) -> tuple[float, float]:
    total_d, total_c = 0.0, 0.0
    for acct in db.query(Account).filter(Account.company_id == company_id, Account.code.in_(codes)).all():
        d, c = _occurrence(acct, db, company_id, start, end)
        total_d += d
        total_c += c
    return total_d, total_c


# ──────────────── 资产负债表 ────────────────

BS_ROWS = [
    # 资产（左侧）
    ("货币资金",         "left",  "1001,1002,1012"),
    ("交易性金融资产",     "left",  "1101"),
    ("应收票据",           "left",  "1121"),
    ("应收账款",           "left",  "1122"),
    ("预付款项",           "left",  "1123"),
    ("应收利息",           "left",  "1132"),
    ("应收股利",           "left",  "1131"),
    ("其他应收款",         "left",  "1221"),
    ("存货",              "left",  "1405,1406"),
    ("一年内到期的非流动资产","left",  "1501"),  # 需按科目明细拆分：长期债权/长期应收等一年内到期部分
    ("其他流动资产",        "left",  "1901"),  # 待处理财产损溢等
    ("流动资产合计",        "left",  "CURRENT_TOTAL"),
    ("可供出售金融资产",     "left",  "1503"),
    ("持有至到期投资",       "left",  "1502"),  # 与1501区分：1502=持有至到期投资，1501=一年内到期
    ("长期应收款",          "left",  "1531"),
    ("长期股权投资",        "left",  "1511"),
    ("投资性房地产",        "left",  "1521"),
    ("固定资产",            "left",  "1601"),
    ("在建工程",            "left",  "1604"),
    ("工程物资",            "left",  "1605"),
    ("固定资产清理",        "left",  "1606"),
    ("生产性生物资产",       "left",  "1621"),
    ("油气资产",            "left",  "1631"),
    ("无形资产",            "left",  "1701"),
    ("开发支出",            "left",  "1702"),
    ("商誉",               "left",  "1711"),
    ("长期待摊费用",        "left",  "1801"),
    ("递延所得税资产",       "left",  "1811"),
    ("其他非流动资产",       "left",  "1902"),  # 长期待摊/递延之外的其他非流动资产
    ("非流动资产合计",       "left",  "NCURRENT_TOTAL"),
    ("资产总计",            "left",  "ASSET_TOTAL"),
    # 负债（右侧上半）
    ("短期借款",            "right", "2001"),
    ("交易性金融负债",       "right", "2101"),
    ("应付票据",            "right", "2201"),
    ("应付账款",            "right", "2202"),
    ("预收款项",            "right", "2203"),
    ("应付职工薪酬",         "right", "2211"),
    ("应交税费",            "right", "2221"),
    ("应付利息",            "right", "2231"),
    ("应付股利",            "right", "2232"),
    ("其他应付款",           "right", "2241"),
    ("一年内到期的非流动负债","right", "2501"),  # 长期借款等一年内到期部分，需按明细分析
    ("其他流动负债",         "right", "2251"),  # 其他流动负债
    ("流动负债合计",         "right", "CURRENT_TOTAL"),
    ("非流动负债",           "right", ""),  # 节标题，非数据行
    ("长期借款",            "right", "2501"),
    ("应付债券",            "right", "2502"),
    ("长期应付款",           "right", "2701"),
    ("专项应付款",           "right", "2711"),
    ("预计负债",            "right", "2801"),
    ("递延所得税负债",        "right", "2901"),
    ("其他非流动负债",        "right", "2902"),  # 其他非流动负债
    ("非流动负债合计",        "right", "NCURRENT_TOTAL"),
    ("负债合计",            "right", "LIABILITY_TOTAL"),
    ("",                   "right", ""),  # 对齐占位行
    # 所有者权益（右侧下半）
    ("实收资本（或股本）",    "right", "4001"),
    ("资本公积",            "right", "4002"),
    ("减：库存股",           "right", "4003"),  # 库存股（备抵项）
    ("盈余公积",            "right", "4101"),
    ("未分配利润",           "right", "4104,4103"),  # 4104利润分配 + 4103本年利润
    ("所有者权益合计",        "right", "EQUITY_TOTAL"),
    ("负债和所有者权益总计",   "right", "TOTAL"),
]


@router.get("/balance")
def balance_sheet(company_id: int, period: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    end_date = _period_end_date(period)

    # build account lookup
    accts = {a.code: a for a in db.query(Account).filter(Account.company_id == company_id).all()}

    # Find leaf accounts (those without children) to avoid double-counting
    parent_codes = set()
    for a in accts.values():
        if a.parent_code:
            parent_codes.add(a.parent_code)

    def _calc(code_str: str, ref_date: str | None = None):
        if not code_str or code_str in ("CURRENT_TOTAL", "NCURRENT_TOTAL", "ASSET_TOTAL", "LIABILITY_TOTAL", "EQUITY_TOTAL", "TOTAL", "TOTAL_CHECK"):
            return 0.0
        codes = [c.strip() for c in code_str.split(",") if c.strip()]
        total = 0.0
        target_date = ref_date or end_date
        for code in codes:
            # Balance sheet: use only leaf accounts (initial_balance already aggregated to parents)
            children = [a for a in accts.values() if a.code.startswith(code) and a.code not in parent_codes]
            if not children and code in accts:
                children = [accts[code]]
            for a in children:
                total += _calc_ending(a, db, company_id, target_date)
        return round(total, 2)

    pye = _prev_year_end(period)

    left_items = []
    right_items = []
    for name, side, codes in BS_ROWS:
        item = {"name": name, "ending": _calc(codes), "beginning": _calc(codes, pye)}
        if side == "left":
            left_items.append(item)
        else:
            right_items.append(item)

    # compute subtotals (both ending and beginning)
    for item in left_items:
        if item["name"] == "流动资产合计":
            item["ending"] = round(sum(i["ending"] for i in left_items[:10]), 2)
            item["beginning"] = round(sum(i["beginning"] for i in left_items[:10]), 2)
        elif item["name"] == "非流动资产合计":
            item["ending"] = round(sum(i["ending"] for i in left_items[11:29]), 2)
            item["beginning"] = round(sum(i["beginning"] for i in left_items[11:29]), 2)
        elif item["name"] == "资产总计":
            item["ending"] = round(left_items[10]["ending"] + left_items[29]["ending"], 2)
            item["beginning"] = round(left_items[10]["beginning"] + left_items[29]["beginning"], 2)

    for item in right_items:
        if item["name"] == "流动负债合计":
            item["ending"] = round(sum(i["ending"] for i in right_items[:12]), 2)
            item["beginning"] = round(sum(i["beginning"] for i in right_items[:12]), 2)
        elif item["name"] == "非流动负债合计":
            item["ending"] = round(sum(i["ending"] for i in right_items[13:21]), 2)
            item["beginning"] = round(sum(i["beginning"] for i in right_items[13:21]), 2)
        elif item["name"] == "负债合计":
            item["ending"] = round(right_items[12]["ending"] + right_items[21]["ending"], 2)
            item["beginning"] = round(right_items[12]["beginning"] + right_items[21]["beginning"], 2)
        elif item["name"] == "所有者权益合计":
            item["ending"] = round(sum(i["ending"] for i in right_items[24:29]), 2)
            item["beginning"] = round(sum(i["beginning"] for i in right_items[24:29]), 2)
        elif item["name"] == "负债和所有者权益总计":
            item["ending"] = round(right_items[22]["ending"] + right_items[29]["ending"], 2)
            item["beginning"] = round(right_items[22]["beginning"] + right_items[29]["beginning"], 2)

    y, m = int(period[:4]), int(period[5:7])
    if m == 12:
        last_day = 31
    elif m in (1, 3, 5, 7, 8, 10):
        last_day = 31
    elif m in (4, 6, 9, 11):
        last_day = 30
    else:
        last_day = calendar.monthrange(y, m)[1]
    date_display = f"{y} 年 {m:02d} 月 {last_day} 日"

    balanced = abs(left_items[30]["ending"] - right_items[30]["ending"]) < 1.0

    return {
        "period_display": f"{y} 年 {m:02d} 月",
        "date_display": date_display,
        "left_items": left_items,
        "right_items": right_items,
        "balanced": balanced,
    }


# ──────────────── 利润表 ────────────────

IS_ROWS = [
    ("一、营业收入",                   "6001"),
    ("    减：营业成本",               "6401"),
    ("        税金及附加",             "6403"),
    ("        销售费用",               "6601"),
    ("        管理费用",               "6602"),
    ("        财务费用",               "6603"),
    ("        资产减值损失",           "6701"),
    ("    加：公允价值变动收益",        "6101"),
    ("        投资收益",              "6111"),
    ("二、营业利润",                   "OP_PROFIT"),
    ("    加：营业外收入",             "6301"),
    ("    减：营业外支出",             "6711"),
    ("三、利润总额",                   "TOTAL_PROFIT"),
    ("    减：所得税费用",             "6801"),
    ("四、净利润",                     "NET_PROFIT"),
]


def _sum_occ(codes: list[str], db: Session, company_id: int, start: str, end: str) -> float:
    total_d, total_c = 0.0, 0.0
    for acct in db.query(Account).filter(Account.company_id == company_id, Account.code.in_(codes)).all():
        d, c = _occurrence(acct, db, company_id, start, end)
        total_d += d
        total_c += c
    # 损益类：收入看贷方，费用看借方
    return total_c - total_d


@router.get("/income")
def income_statement(company_id: int, period: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    end_date = _period_end_date(period)
    ys = _year_start(period)
    py_end = _period_end_date(_prev_year_period(period))
    py_ys = _year_start(_prev_year_period(period))

    accts = {a.code: a for a in db.query(Account).filter(Account.company_id == company_id).all()}

    # Find leaf accounts to avoid double-counting
    _parent_codes = set()
    for a in accts.values():
        if a.parent_code:
            _parent_codes.add(a.parent_code)

    def _calc(code_str: str, start: str, end: str) -> float:
        if not code_str:
            return 0.0
        codes = [c.strip() for c in code_str.split(",") if c.strip()]
        total = 0.0
        for code in codes:
            # Get leaf accounts; also always include the exact code as fallback
            matching = [a for a in accts.values() if a.code.startswith(code)]
            leaf_children = [a for a in matching if a.code not in _parent_codes]
            if not leaf_children and code in accts:
                leaf_children = [accts[code]]
            if code in accts and accts[code] not in leaf_children:
                leaf_children.append(accts[code])
            for a in leaf_children:
                # For P&L accounts, exclude closing entries to get actual occurrence
                exclude_xfer = (a.category == "profit_loss")
                d, c = _occurrence(a, db, company_id, start, end, exclude_transfer=exclude_xfer)
                if a.category == "profit_loss":
                    # 6xxx 费用类（64xx, 66xx, 67xx, 68xx）只看借方（发生额）
                    if a.code.startswith(("64", "66", "67", "68")):
                        total += d
                    # 60xx 收入类、63xx 营业外收入 只看贷方（发生额）
                    else:
                        total += c
        return round(total, 2)

    def _build_items(start: str, end: str):
        items = []
        for name, codes in IS_ROWS:
            if codes in ("OP_PROFIT", "TOTAL_PROFIT", "NET_PROFIT"):
                items.append({"name": name, "curr": 0, "ytd": 0, "prev": 0, "formula": codes})
            else:
                items.append({
                    "name": name,
                    "curr": round(_calc(codes, start, end), 2),
                    "ytd": round(_calc(codes, ys, end), 2),
                    "prev": round(_calc(codes, py_ys, py_end), 2),
                    "formula": "",
                })
        # 计算营业利润
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
        # 同时算ytd和prev
        for col in ("ytd", "prev"):
            s = ys if col == "ytd" else py_ys
            e = end_date if col == "ytd" else py_end

            def _calc_col(code_str: str):
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
        return items

    # Current month start: YYYY-MM-01
    month_start = period + "-01"
    items = _build_items(month_start, end_date)

    y, m = int(period[:4]), int(period[5:7])
    period_display = f"{y} 年 {m:02d} 月"

    return {
        "period_display": period_display,
        "date_display": period_display,
        "items": items,
    }


# ──────────────── 现金流量表 ────────────────

# 现金等价物科目：库存现金、银行存款、其他货币资金
CASH_CODES = {"1001", "1002", "1012"}


def _parse_code_set(codes_str: str | None) -> set:
    """Parse comma-separated account codes into a set."""
    if not codes_str:
        return set()
    return {c.strip() for c in codes_str.split(",") if c.strip()}


def _code_matches(code: str, code_set: set) -> bool:
    """Check if an account code matches a set of code patterns.
    Supports exact match, prefix match (parent codes match children), and child match."""
    if not code_set:
        return False
    if code in code_set:
        return True
    for c in code_set:
        if code.startswith(c) or c.startswith(code):
            return True
    return False


def _is_cash_account(code: str, cash_codes: set) -> bool:
    """判断科目是否为现金类（精确匹配或前缀匹配）。"""
    if code in cash_codes:
        return True
    for cc in cash_codes:
        if code.startswith(cc) and len(code) > len(cc):
            return True
    return False


def _compute_cash_flows(db: Session, company_id: int, start: str, end: str) -> dict[str, float]:
    """使用 CashFlowItem 映射表计算各现金流量项目的期间金额。

    对每张已过账凭证：
    1. 找到现金类分录（1001/1002/1012 及子科目）
    2. 现金借方 → 流入 → 用对方贷方科目匹配 CashFlowItem.credit_accounts
    3. 现金贷方 → 流出 → 用对方借方科目匹配 CashFlowItem.debit_accounts

    Returns: dict keyed by CashFlowItem.code, values = rounded amounts
    """
    cf_items = db.query(CashFlowItem).filter(
        CashFlowItem.company_id == company_id,
        CashFlowItem.is_active == True,
    ).all()

    if not cf_items:
        # Fallback: return empty dict, endpoint will show zeros
        return {}

    # Pre-parse all CF item configs
    cf_configs = [(cfi.code, cfi.direction, _parse_code_set(cfi.debit_accounts), _parse_code_set(cfi.credit_accounts)) for cfi in cf_items]
    result = {cfi.code: 0.0 for cfi in cf_items}

    vouchers = db.query(Voucher).filter(
        Voucher.company_id == company_id,
        Voucher.status == "posted",
        Voucher.date >= start,
        Voucher.date < end,
    ).all()

    for v in vouchers:
        entries = v.entries
        cash_entries = [e for e in entries if _is_cash_account(e.account_code, CASH_CODES)]
        non_cash = [e for e in entries if not _is_cash_account(e.account_code, CASH_CODES)]

        if not cash_entries or not non_cash:
            continue

        for ce in cash_entries:
            if ce.debit > 0:
                # Cash received (inflow) → match counterpart credits
                counterparts = [e for e in non_cash if e.credit > 0]
                for cfi_code, direction, _dr, cr_set in cf_configs:
                    if direction != "inflow":
                        continue
                    for cp in counterparts:
                        if _code_matches(cp.account_code, cr_set):
                            result[cfi_code] += cp.credit
            if ce.credit > 0:
                # Cash paid (outflow) → match counterpart debits
                counterparts = [e for e in non_cash if e.debit > 0]
                for cfi_code, direction, dr_set, _cr in cf_configs:
                    if direction != "outflow":
                        continue
                    for cp in counterparts:
                        if _code_matches(cp.account_code, dr_set):
                            result[cfi_code] += cp.debit

    return {k: round(v, 2) for k, v in result.items()}


def _get_cf_row_key(item: CashFlowItem) -> str:
    """Return the 会企03表 row key for a CashFlowItem, or its code as fallback."""
    if item.category_code:
        return item.category_code
    return item.code


@router.get("/cashflow")
def cash_flow(company_id: int, period: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """现金流量表（会企03表），基于 CashFlowItem 映射自动分类。"""
    end_date = _period_end_date(period)
    ys = _year_start(period)
    py_end = _period_end_date(_prev_year_period(period))
    py_ys = _year_start(_prev_year_period(period))

    y, m = int(period[:4]), int(period[5:7])
    period_display = f"{y} 年 {m:02d} 月"
    if m == 12:
        last_day = 31
    elif m in (1, 3, 5, 7, 8, 10):
        last_day = 31
    elif m in (4, 6, 9, 11):
        last_day = 30
    else:
        last_day = calendar.monthrange(y, m)[1]
    date_display = f"{y} 年 {m:02d} 月 {last_day} 日"

    # Compute granular per-item cash flows
    period_start = f"{period}-01"
    curr_items = _compute_cash_flows(db, company_id, period_start, end_date)  # 本月
    ytd_items = _compute_cash_flows(db, company_id, ys, end_date)  # 本年累计
    prev_items = _compute_cash_flows(db, company_id, py_ys, py_end)

    # Build lookup: row_key → (curr_amount, ytd_amount, prev_amount)
    cf_items = {cfi.code: cfi for cfi in db.query(CashFlowItem).filter(
        CashFlowItem.company_id == company_id, CashFlowItem.is_active == True
    ).all()}

    def _cf_val(row_key: str, period_data: dict) -> float:
        """Sum amounts from all CashFlowItems that map to this row key."""
        total = 0.0
        for code, cfi in cf_items.items():
            rk = cfi.category_code or code
            if rk == row_key:
                total += period_data.get(code, 0.0)
        return round(total, 2)

    def _cf_all(row_key: str):
        """Return (curr, ytd, prev) for a row key."""
        return (_cf_val(row_key, curr_items), _cf_val(row_key, ytd_items), _cf_val(row_key, prev_items))

    # 现金期初余额
    all_accts = db.query(Account).filter(Account.company_id == company_id).all()
    accts = {a.code: a for a in all_accts if _is_cash_account(a.code, CASH_CODES)}
    beginning_balance = sum(_calc_ending(a, db, company_id, ys) for a in accts.values())

    # --- Build 会企03表 rows ---
    def R(key, label, flow_type=None):
        """Build a row tuple. flow_type: 'inflow', 'outflow', 'subtotal', 'net', None(header/fixed)."""
        if flow_type == "inflow":
            c, y, p = _cf_all(key)
        elif flow_type == "outflow":
            c, y, p = _cf_all(key)
        elif flow_type in ("subtotal",):
            # Computed below after we have subtotals
            return (label, 0.0, 0.0, 0.0, key, flow_type)
        elif flow_type == "net":
            return (label, 0.0, 0.0, 0.0, key, flow_type)
        else:
            # Header or fixed value row
            return (label, "", "", "", key, flow_type)
        return (label, c, y, p, key, flow_type)

    rows_raw = [
        R("header_op", "一、经营活动产生的现金流量："),
        R("op_sales", "     销售商品、提供劳务收到的现金", "inflow"),
        R("op_refund", "     收到的税费返还", "inflow"),
        R("op_other_in", "     收到其他与经营活动有关的现金", "inflow"),
        R("op_in_sub", "             经营活动现金流入小计", "subtotal"),
        R("op_goods", "     购买商品、接受劳务支付的现金", "outflow"),
        R("op_staff", "     支付给职工以及为职工支付的现金", "outflow"),
        R("op_tax", "     支付的各项税费", "outflow"),
        R("op_other_out", "     支付其它与经营活动有关的现金", "outflow"),
        R("op_out_sub", "             经营活动现金流出小计", "subtotal"),
        R("op_net", "        经营活动产生的现金流量净额", "net"),
        R("header_inv", "二、投资活动产生的现金流量："),
        R("inv_recover", "     收回投资收到的现金", "inflow"),
        R("inv_income", "     取得投资收益收到的现金", "inflow"),
        R("inv_assets", "     处置固定资产、无形资产和其他长期资产收回的现金净额", "inflow"),
        R("inv_subsidiary", "     处置子公司及其他营业单位收到的现金净额", "inflow"),
        R("inv_other_in", "     收到其他与投资活动有关的现金", "inflow"),
        R("inv_in_sub", "             投资活动现金流入小计", "subtotal"),
        R("inv_build", "     购建固定资产、无形资产和其他长期资产所支付的现金", "outflow"),
        R("inv_pay", "     投资支付的现金", "outflow"),
        R("inv_subsidiary_out", "     取得子公司及其他营业单位支付的现金净额", "outflow"),
        R("inv_other_out", "     支付的其他与投资活动有关的现金", "outflow"),
        R("inv_out_sub", "            投资活动现金流出小计", "subtotal"),
        R("inv_net", "         投资活动产生的现金流量净额", "net"),
        R("header_fin", "三、筹资活动产生的现金流量： "),
        R("fin_invest", "     吸收投资收到的现金", "inflow"),
        R("fin_borrow", "     取得借款收到的现金", "inflow"),
        R("fin_other_in", "     收到其他与筹资活动有关的现金", "inflow"),
        R("fin_in_sub", "             筹资活动现金流入小计", "subtotal"),
        R("fin_repay", "     偿还债务支付的现金", "outflow"),
        R("fin_dividend", "     分配股利、利润或偿付利息支付的现金", "outflow"),
        R("fin_other_out", "     支付其他与筹资活动有关的现金", "outflow"),
        R("fin_out_sub", "            筹资活动现金流出小计", "subtotal"),
        R("fin_net", "         筹资活动产生的现金流量净额", "net"),
    ]

    # Compute subtotals and net values from the raw row data
    # First pass: collect inflow/outflow amounts per section
    def _compute_rows(rows_raw_local, curr_items_local, ytd_items_local, prev_items_local):
        # Pre-compute all data rows
        computed = []
        for raw in rows_raw_local:
            label, c, y, p, key, flow_type = raw
            if flow_type in ("inflow", "outflow"):
                cv, yv, pv = _cf_all(key)
                computed.append((label, cv, yv, pv, key, flow_type))
            else:
                computed.append((label, c, y, p, key, flow_type))
        return computed

    rows_computed = _compute_rows(rows_raw, curr_items, ytd_items, prev_items)

    # Second pass: compute subtotals and nets
    def _finalize_rows(computed_rows):
        result = []
        # Track running totals for current section
        sec_in_c = sec_in_y = sec_in_p = 0.0
        sec_out_c = sec_out_y = sec_out_p = 0.0
        overall_in_c = overall_in_y = overall_in_p = 0.0
        overall_out_c = overall_out_y = overall_out_p = 0.0

        for label, c, y, p, key, flow_type in computed_rows:
            if flow_type == "inflow":
                cv, yv, pv = c, y, p
                sec_in_c += cv; sec_in_y += yv; sec_in_p += pv
                overall_in_c += cv; overall_in_y += yv; overall_in_p += pv
                result.append((label, round(cv, 2), round(yv, 2), round(pv, 2)))
            elif flow_type == "outflow":
                cv, yv, pv = c, y, p
                sec_out_c += cv; sec_out_y += yv; sec_out_p += pv
                overall_out_c += cv; overall_out_y += yv; overall_out_p += pv
                result.append((label, round(cv, 2), round(yv, 2), round(pv, 2)))
            elif flow_type == "subtotal":
                is_inflow_sub = "_in_sub" in key
                result.append((label, round(sec_in_c, 2) if is_inflow_sub else round(sec_out_c, 2),
                               round(sec_in_y, 2) if is_inflow_sub else round(sec_out_y, 2),
                               round(sec_in_p, 2) if is_inflow_sub else round(sec_out_p, 2)))
            elif flow_type == "net":
                net_c = round(sec_in_c - sec_out_c, 2)
                net_y = round(sec_in_y - sec_out_y, 2)
                net_p = round(sec_in_p - sec_out_p, 2)
                result.append((label, net_c, net_y, net_p))
                # Reset section trackers for next section
                sec_in_c = sec_in_y = sec_in_p = 0.0
                sec_out_c = sec_out_y = sec_out_p = 0.0
            else:
                # Header
                result.append((label, c, y, p))

        return result, overall_in_c, overall_in_y, overall_in_p, overall_out_c, overall_out_y, overall_out_p

    rows_final, total_in_c, total_in_y, total_in_p, total_out_c, total_out_y, total_out_p = _finalize_rows(rows_computed)

    # Compute final summary values
    net_change_c = round(total_in_c - total_out_c, 2)
    net_change_y = round(total_in_y - total_out_y, 2)
    net_change_p = round(total_in_p - total_out_p, 2)
    ending_c = round(beginning_balance + net_change_c, 2)
    ending_y = round(beginning_balance + net_change_y, 2)
    ending_p = round(beginning_balance + net_change_p, 2)

    # Append final rows (四~六)
    rows_final.append(("四、汇率变动对现金及现金等价物的影响", 0.0, 0.0, 0.0))
    rows_final.append(("五、现金及现金等价物净增加额", net_change_c, net_change_y, net_change_p))
    rows_final.append(("        加：期初现金及现金等价物余额", round(beginning_balance, 2), round(beginning_balance, 2), round(beginning_balance, 2)))
    rows_final.append(("六、期末现金及现金等价物余额", ending_c, ending_y, ending_p))

    return {
        "period_display": period_display,
        "date_display": date_display,
        "rows": rows_final,
    }
