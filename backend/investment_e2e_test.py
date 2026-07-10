"""投资模块端到端集成测试"""

import requests, json

BASE = "http://localhost:8000/api"
TOKEN = None
CID = 1  # 利美融信资本 (已有数据)
PASS = 0
FAIL = 0


def step(n, label):
    print(f"\n{'=' * 50}")
    print(f"  Step {n}: {label}")
    print(f"{'=' * 50}")


def ok(resp, label=""):
    global PASS
    try:
        d = resp.json() if resp.text else {}
    except:
        d = resp.text[:100]
    if resp.status_code < 400:
        PASS += 1
        print(f"  ✅ {label} → {resp.status_code}")
        return d
    else:
        global FAIL
        FAIL += 1
        print(f"  ❌ {label} → {resp.status_code}: {json.dumps(d, ensure_ascii=False)[:200]}")
        return None


def api(method, path, data=None, params=None):
    headers = {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}
    url = f"{BASE}{path}"
    if method == "GET":
        return requests.get(url, headers=headers, params=params)
    elif method == "POST":
        return requests.post(url, headers=headers, json=data, params=params)
    elif method == "PUT":
        return requests.put(url, headers=headers, json=data, params=params)
    elif method == "DELETE":
        return requests.delete(url, headers=headers, params=params)


# Login
step(1, "登录 (利美融信资本)")
resp = api(
    "POST",
    "/auth/login",
    data={"username": "18612538539", "password": "Zhanghanyu400101", "company_id": CID, "period": "2026-05"},
)
d = ok(resp, "Login")
if d:
    TOKEN = d.get("access_token")
    print(f"  👤 {d.get('company_name')}")

# Create portfolio
step(2, "创建投资组合")
pf = None
resp = api(
    "POST",
    "/investments/portfolios",
    data={
        "name": "测试组合-港股科技",
        "investment_type": "secondary_market",
        "currency": "HKD",
        "description": "E2E测试用",
    },
    params={"company_id": CID},
)
pf = ok(resp, "Create portfolio (secondary_market)")
if pf:
    print(f"  📁 {pf.get('name')} ID={pf.get('id')}")

# List portfolios
resp = api("GET", "/investments/portfolios", params={"company_id": CID})
ok(resp, "List portfolios")

# Create position
step(3, "创建持仓")
pos = None
if pf:
    resp = api(
        "POST",
        "/investments/positions",
        data={
            "portfolio_id": pf["id"],
            "account_code": "1101",
            "security_name": "腾讯控股",
            "security_code": "00700.HK",
            "quantity": 1000,
            "unit_cost": 320,
            "cost_amount": 320000,
            "fair_value": 350000,
            "fair_value_date": "2026-05-15",
            "valuation_method": "market_price",
        },
        params={"company_id": CID},
    )
    pos = ok(resp, "Create position 腾讯控股")
    if pos:
        print(f"  📊 {pos.get('security_name')} ID={pos.get('id')}")

# List positions
resp = api("GET", "/investments/positions", params={"company_id": CID})
ok(resp, "List positions")

# Create transaction
step(4, "创建投资交易（买入）")
txn = None
if pos:
    resp = api(
        "POST",
        "/investments/transactions",
        data={
            "position_id": pos["id"],
            "transaction_type": "buy",
            "transaction_date": "2026-05-15",
            "quantity": 1000,
            "price": 320,
            "amount": 320000,
            "fee": 500,
            "notes": "通过港股通买入腾讯",
        },
        params={"company_id": CID},
    )
    txn = ok(resp, "Create buy transaction → auto-voucher")
    if txn:
        print(f"  💰 金额: ¥{txn.get('amount'):,} 凭证ID: {txn.get('voucher_id')}")

# Edit transaction
step(5, "编辑交易")
if txn:
    resp = api(
        "PUT",
        f"/investments/transactions/{txn['id']}",
        data={"amount": 321000, "fee": 1000, "notes": "港股通买入腾讯（更新：含印花税）"},
    )
    updated_txn = ok(resp, "Update transaction amount+notes")
    if updated_txn:
        print(f"  ✏️ Updated amount: ¥{updated_txn.get('amount'):,}")

# Create fair value adjustment
step(6, "公允价值调整")
adj = None
if pos:
    resp = api(
        "POST",
        "/investments/adjustments",
        data={
            "position_id": pos["id"],
            "adjustment_date": "2026-05-23",
            "previous_value": 350000,
            "adjusted_value": 380000,
            "change_amount": 30000,
            "reason": "港股腾讯股价上涨至HK$380",
        },
        params={"company_id": CID},
    )
    adj = ok(resp, "Create fair value up adjustment → auto-voucher")
    if adj:
        print(f"  📈 Change: +¥{adj.get('change_amount'):,} 凭证ID: {adj.get('voucher_id')}")

# Edit adjustment
step(7, "编辑调整")
if adj:
    resp = api(
        "PUT",
        f"/investments/adjustments/{adj['id']}",
        data={"adjusted_value": 385000, "change_amount": 35000, "reason": "更正：腾讯涨至HK$385"},
    )
    updated_adj = ok(resp, "Update fair value adjustment")
    if updated_adj:
        print(f"  ✏️ Adjusted: ¥{updated_adj.get('adjusted_value'):,}")

# Create income
step(8, "投资收益记录")
inc = None
resp = api(
    "POST",
    "/investments/income",
    data={
        "position_id": pos["id"] if pos else None,
        "income_type": "dividend",
        "income_date": "2026-05-20",
        "amount": 5000,
        "notes": "腾讯2025年度末期股息",
    },
    params={"company_id": CID},
)
inc = ok(resp, "Create dividend income → auto-voucher")
if inc:
    print(f"  💵 金额: ¥{inc.get('amount'):,} 凭证ID: {inc.get('voucher_id')}")

# Edit income
step(9, "编辑收益")
if inc:
    resp = api("PUT", f"/investments/income/{inc['id']}", data={"amount": 5200, "notes": "腾讯末期股息（含税）"})
    updated_inc = ok(resp, "Update income amount+notes")
    if updated_inc:
        print(f"  ✏️ Updated: ¥{updated_inc.get('amount'):,}")

# Reports
step(10, "投资报表")
resp = api("GET", "/investments/reports/positions", params={"company_id": CID})
report = ok(resp, "Positions report")
if report:
    print(f"  📊 {len(report)} positions")
    for r in report:
        print(f"    {r['security_name']}: cost={r['cost_amount']:,} fv={r['fair_value']:,} ugl={r['unrealized_gl']:,}")

resp = api("GET", "/investments/reports/income", params={"company_id": CID})
inc_report = ok(resp, "Income report")
if inc_report:
    print(f"  💰 Total income: ¥{inc_report.get('total'):,}")

resp = api("GET", "/investments/reports/fair-value", params={"company_id": CID})
fv_report = ok(resp, "Fair value report")
if fv_report:
    print(f"  📈 Total change: ¥{fv_report.get('total_change'):,}")

# List adjustments standalone
step(11, "公允价值调整列表")
resp = api("GET", "/investments/adjustments", params={"company_id": CID})
adj_list = ok(resp, "List adjustments")
if adj_list:
    print(f"  📋 {len(adj_list)} adjustment records")

# Delete in reverse order (cleanup)
step(12, "清理测试数据（删除收益→调整→交易→持仓→组合）")
if inc:
    resp = api("DELETE", f"/investments/income/{inc['id']}")
    ok(resp, "Delete income (cascade voucher)")

if adj:
    resp = api("DELETE", f"/investments/adjustments/{adj['id']}")
    ok(resp, "Delete adjustment (cascade voucher)")

if txn:
    resp = api("DELETE", f"/investments/transactions/{txn['id']}")
    ok(resp, "Delete transaction (cascade voucher)")

if pos:
    resp = api("DELETE", f"/investments/positions/{pos['id']}")
    ok(resp, "Delete position")

if pf:
    resp = api("DELETE", f"/investments/portfolios/{pf['id']}")
    ok(resp, "Delete portfolio")

# ═══════════════════════════════════════
print(f"\n{'=' * 50}")
print(f"  🏁 INVESTMENT E2E COMPLETE")
print(f"  ✅ Passed: {PASS}")
print(f"  ❌ Failed: {FAIL}")
print(f"{'=' * 50}")
