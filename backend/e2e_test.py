"""端到端全链路集成测试 — 从注册到报表"""
import requests, json, sys

BASE = "http://localhost:8000/api"
TOKEN = None
CID = None
UID = None
PASS = 0
FAIL = 0

def step(n, label):
    print(f"\n{'='*50}")
    print(f"  Step {n}: {label}")
    print(f"{'='*50}")

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

def api(method, path, data=None, params=None, auth=True):
    headers = {}
    if auth and TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    url = f"{BASE}{path}"
    if method == "GET":
        return requests.get(url, headers=headers, params=params)
    elif method == "POST":
        return requests.post(url, headers=headers, json=data, params=params)
    elif method == "PUT":
        return requests.put(url, headers=headers, json=data, params=params)
    elif method == "DELETE":
        return requests.delete(url, headers=headers, params=params)

def login(uname, pwd, cid):
    global TOKEN, CID, UID
    CID = cid
    resp = api("POST", "/auth/login", data={"username": uname, "password": pwd, "company_id": cid, "period": "2026-05"}, auth=False)
    d = ok(resp, f"Login as {uname}")
    if d:
        TOKEN = d.get("access_token")
        UID = d.get("user_id")

# ═══════════════════════════════════════
# Step 1: Register new company #3
step(1, "注册新公司")
resp = api("POST", "/auth/register",
    data={"phone": "13900000003", "company_name": "端到端测试公司", "password": "E2eTest2026"},
    auth=False)
d = ok(resp, "Register")
if d:
    CID = d.get("company_id")
    print(f"  📋 Company ID: {CID}, Phone: {d.get('phone')}")

# Step 2: Activate trial
step(2, "激活7天试用")
login("13900000003", "E2eTest2026", CID)
resp = api("POST", "/subscriptions/activate-trial", params={"company_id": CID})
ok(resp, "Activate trial")

# Step 3: Seed accounts (L1 for new company)
step(3, "初始化国标科目")
from app.database import SessionLocal
from app.seed import seed_level1_accounts, seed_level2_accounts
db = SessionLocal()
seed_level1_accounts(db, CID)
seed_level2_accounts(db, CID)
db.close()
resp = api("GET", "/accounts/", params={"company_id": CID})
accts = ok(resp, "List accounts")
if accts:
    print(f"  📋 {len(accts)} accounts seeded")

# Step 4: Add employee
step(4, "新增员工")
resp = api("POST", "/hr/employees", data={
    "company_id": CID, "employee_code": "EMP001", "name": "张三",
    "gender": "男", "department_id": None,
    "position": "会计主管", "hire_date": "2026-01-01",
    "status": "在职", "phone": "13900000001",
})
emp = ok(resp, "Add employee 张三")
if emp: print(f"  👤 {emp.get('name')} ID={emp.get('id')}")

# Step 5: Add counterparties (customer + supplier)
step(5, "新增往来单位")
resp = api("POST", "/counterparties/", data={
    "company_id": CID, "code": "CUST01", "name": "北京明远科技有限公司",
    "category": "客户", "short_name": "明远科技",
})
cust = ok(resp, "Add customer")
resp = api("POST", "/counterparties/", data={
    "company_id": CID, "code": "SUPP01", "name": "北京华创软件有限公司",
    "category": "供应商", "short_name": "华创软件",
})
supp = ok(resp, "Add supplier")

# Step 6: Create voucher (手动记账)
step(6, "手工录入凭证")
resp = api("POST", "/vouchers/", data={
    "company_id": CID, "date": "2026-05-15", "voucher_type": "payment",
    "summary": "支付办公室租金 5月",
    "entries": [
        {"account_code": "660208", "debit": 15000, "credit": 0, "description": "管理费用-租赁费"},
        {"account_code": "100201", "debit": 0, "credit": 15000, "description": "银行存款-招行"},
    ]
})
vch = ok(resp, "Create voucher")
if vch: print(f"  📝 {vch.get('voucher_no')} ID={vch.get('id')} status={vch.get('status')}")

# Step 7: Approve + Post voucher
step(7, "审核并记账")
vid = vch.get("id") if vch else None
if vid:
    resp = api("POST", f"/vouchers/{vid}/approve")
    ok(resp, "Approve")
    resp = api("POST", f"/vouchers/{vid}/post")
    ok(resp, "Post (记账)")

# Step 8: Expense reimbursement
step(8, "费用报销（申请→审批→付款）")
# Create expense item
resp = api("POST", "/expenses/items", data={"company_id": CID, "code": "TRAVEL", "name": "差旅费"})
ok(resp, "Create expense item")
# Create expense report
resp = api("POST", "/expenses/reports", data={
    "company_id": CID, "expense_date": "2026-05-20",
    "notes": "出差北京拜访客户",
    "items": [{"row_seq": 1, "date": "2026-05-20", "amount": 2500, "description": "高铁往返+住宿", "receipt_count": 2}]
})
er = ok(resp, "Create expense report")
if er:
    er_id = er.get("id")
    resp = api("POST", f"/expenses/reports/{er_id}/submit")
    ok(resp, "Submit for approval")
    resp = api("POST", f"/expenses/reports/{er_id}/approve")
    ok(resp, "Approve expense")
    resp = api("POST", f"/expenses/reports/{er_id}/pay")
    ok(resp, "Pay expense")
    print(f"  💰 Expense report ID={er_id} approved+paid")

# Step 9: Fixed Asset + depreciation
step(9, "固定资产（新增→折旧）")
resp = api("POST", "/fixed-assets/assets", data={
    "company_id": CID, "asset_code": "FA001", "name": "办公室电脑设备",
    "category": "设备", "acquisition_date": "2026-03-01",
    "original_value": 48000, "residual_value": 2400, "useful_life": 5,
    "depreciation_method": "直线法", "monthly_depreciation": 760,
    "status": "使用中", "location": "北京办公室",
})
fa = ok(resp, "Create fixed asset")
if fa:
    resp = api("POST", "/fixed-assets/depreciations", data={
        "company_id": CID, "fixed_asset_id": fa.get("id"),
        "period": "2026-05", "depreciation_amount": 760,
    })
    dep = ok(resp, "Create depreciation")
    if dep:
        print(f"  🖥️  Asset: {fa.get('name')}, monthly depn: ¥{fa.get('monthly_depreciation'):,}")
        # Check auto voucher
        resp = api("GET", "/vouchers/", params={"company_id": CID})
        vouchers = ok(resp)
        if vouchers:
            for v in vouchers:
                if "折旧" in (v.get("summary") or ""):
                    print(f"  📝 Auto-voucher: {v.get('voucher_no')} {v.get('summary')}")

# Step 10: Accounts Receivable
step(10, "应收账款（开票→收款）")
resp = api("POST", "/receivables/invoices", data={
    "company_id": CID, "customer_name": "北京明远科技有限公司",
    "invoice_no": "INV-2026-001", "invoice_date": "2026-05-10",
    "amount": 80000, "due_date": "2026-06-10",
})
inv = ok(resp, "Create AR invoice")
if inv:
    resp = api("POST", "/receivables/payments", data={
        "company_id": CID, "receivable_id": inv.get("id"),
        "payment_date": "2026-05-22", "amount": 50000, "payment_method": "银行转账",
    })
    pymt = ok(resp, "Record AR payment")
    if pymt:
        print(f"  💵 AR: ¥{inv.get('amount'):,} invoice, ¥{pymt.get('amount'):,} received")
        resp = api("GET", "/receivables/summary", params={"company_id": CID})
        sm = ok(resp, "AR summary")
        if sm: print(f"  📊 AR total: ¥{sm.get('total_receivable', 0):,}")

# Step 11: Accounts Payable
step(11, "应付账款（发票→付款）")
resp = api("POST", "/payables/invoices", data={
    "company_id": CID, "supplier_name": "北京华创软件有限公司",
    "invoice_no": "PO-2026-001", "invoice_date": "2026-05-05",
    "amount": 35000, "due_date": "2026-06-05",
})
pinv = ok(resp, "Create AP invoice")
if pinv:
    resp = api("POST", "/payables/payments", data={
        "company_id": CID, "payable_id": pinv.get("id"),
        "payment_date": "2026-05-23", "amount": 35000, "payment_method": "银行转账",
    })
    ppymt = ok(resp, "Record AP payment")
    if ppymt:
        print(f"  💳 AP: ¥{pinv.get('amount'):,} invoice, ¥{ppymt.get('amount'):,} paid")
        resp = api("GET", "/payables/summary", params={"company_id": CID})
        sm2 = ok(resp, "AP summary")
        if sm2: print(f"  📊 AP total: ¥{sm2.get('total_payable', 0):,}")

# Step 12: Batch depreciation
step(12, "批量计提折旧")
resp = api("POST", "/fixed-assets/depreciations/batch", data={
    "company_id": CID, "period": "2026-05",
})
bd = ok(resp, "Batch depreciate")
if bd: print(f"  📊 Success: {len(bd.get('success',[]))}, Failed: {len(bd.get('failed',[]))}")

# Step 13: Close period
step(13, "会计期间结账")
resp = api("GET", "/periods/close-checks", params={"company_id": CID, "period": "2026-05"})
chk = ok(resp, "Close checks")
if chk:
    print(f"  🔍 {chk.get('unposted_count', 0)} unposted vouchers, balanced={chk.get('trial_balance_ok', False)}")
# Post all remaining vouchers first
resp = api("GET", "/vouchers/", params={"company_id": CID, "status": "draft"})
drafts = ok(resp, "Find drafts")
if drafts:
    for v in drafts:
        api("POST", f"/vouchers/{v['id']}/post")
    print(f"  📝 Posted {len(drafts)} draft vouchers")
# Now close
resp = api("POST", "/periods/close", data={"company_id": CID, "period": "2026-05"})
cl = ok(resp, "Close period 2026-05")

# Step 14: Reports
step(14, "生成报表")
resp = api("GET", "/reports/balance", params={"company_id": CID, "period": "2026-05"})
bs = ok(resp, "Balance sheet")
if bs:
    assets = bs.get("assets_total", 0)
    liabilities = bs.get("liabilities_total", 0)
    equity = bs.get("equity_total", 0)
    print(f"  📊 Assets: ¥{assets:,.2f}  Liabilities: ¥{liabilities:,.2f}  Equity: ¥{equity:,.2f}")
    print(f"  ⚖️  Balanced: {'YES ✅' if abs(assets - (liabilities + equity)) < 1 else '❌'}")

resp = api("GET", "/reports/income", params={"company_id": CID, "period_start": "2026-05", "period_end": "2026-05"})
inc = ok(resp, "Income statement")
if inc:
    rev = inc.get("revenue_total", 0)
    exp = inc.get("expense_total", 0)
    ni = inc.get("net_income", 0) if inc.get("net_income") else rev - exp
    print(f"  📊 Revenue: ¥{rev:,.2f}  Expenses: ¥{exp:,.2f}  Net: ¥{ni:,.2f}")

# ═══════════════════════════════════════
print(f"\n{'='*50}")
print(f"  🏁 E2E TEST COMPLETE")
print(f"  ✅ Passed: {PASS}")
print(f"  ❌ Failed: {FAIL}")
print(f"{'='*50}")
