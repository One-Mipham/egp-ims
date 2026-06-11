"""Setup cash flow mappings and generate cash flow statement for Company 1."""
import sys, os
os.chdir("/opt/egp-ims/intranet/backend")
sys.path.insert(0, ".")

from app.database import SessionLocal
from app.models import Voucher, VoucherEntry, Account, CashFlowItem
from collections import defaultdict

db = SessionLocal()
cid = 1

# 1. Clear old cash flow items and set up proper mappings
db.query(CashFlowItem).filter(CashFlowItem.company_id == cid).delete()
db.commit()

# Cash flow items with account code mappings
# Format: (code, name, direction, debit_accounts, credit_accounts)
items = [
    # === Operating Activities - Inflows ===
    ("CF01", "销售商品、提供劳务收到的现金", "inflow",
     "1001,1002",  # cash debited...
     "1122,6001"),  # when receivables credited or revenue credited

    # === Operating Activities - Outflows ===
    ("CF02", "支付给职工以及为职工支付的现金", "outflow",
     "2211",   # 应付职工薪酬 debited
     "1001,1002"),  # cash credited

    ("CF03", "支付的各项税费", "outflow",
     "2221",   # 应交税费 debited
     "1001,1002"),

    ("CF04", "支付其它与经营活动有关的现金", "outflow",
     "6602,6603,2241,1221",  # expenses & other payables debited
     "1001,1002"),  # cash credited

    # === Investing Activities ===
    ("CF05", "购建固定资产、无形资产和其他长期资产所支付的现金", "outflow",
     "1601,1604,1701",  # fixed assets, construction, intangibles
     "1001,1002"),

    ("CF06", "投资支付的现金", "outflow",
     "1503,1511",  # financial assets, long-term investments
     "1001,1002"),

    # === Financing Activities ===
    ("CF07", "取得借款收到的现金", "inflow",
     "1001,1002",  # cash debited
     "2241,2001,2501"),  # borrowings credited

    ("CF08", "吸收投资收到的现金", "inflow",
     "1001,1002",  # cash debited
     "4001"),  # paid-in capital credited
]

for code, name, direction, dr_accts, cr_accts in items:
    db.add(CashFlowItem(
        company_id=cid,
        code=code,
        name=name,
        direction=direction,
        debit_accounts=dr_accts,
        credit_accounts=cr_accts,
        is_active=True,
    ))
db.commit()
print("Cash flow items seeded")

# 2. Generate cash flow statement
vouchers = db.query(Voucher).filter(Voucher.company_id == cid).all()
cf_items = db.query(CashFlowItem).filter(
    CashFlowItem.company_id == cid, CashFlowItem.is_active == True
).all()

# Parse account code lists
def parse_codes(s):
    if not s:
        return set()
    return {c.strip() for c in s.split(",") if c.strip()}

# Classify each voucher entry pair
# Approach: for each voucher, find cash account entries and match with counterpart entries
cf_data = defaultdict(lambda: {"may": 0.0, "ytd": 0.0})

for v in vouchers:
    is_may = v.date.startswith("2026-05")
    entries = db.query(VoucherEntry).filter(VoucherEntry.voucher_id == v.id).all()

    # Find cash entries (1001, 1002)
    cash_entries = []
    other_entries = []
    for e in entries:
        if e.account_code.startswith("1001") or e.account_code.startswith("1002"):
            cash_entries.append(e)
        else:
            other_entries.append(e)

    if not cash_entries:
        continue

    # Classify each cash entry based on counterpart
    for ce in cash_entries:
        if ce.debit > 0:
            # Cash received - look for credited counterpart
            counterparts = [e for e in other_entries if e.credit > 0]
        else:
            # Cash paid - look for debited counterpart
            counterparts = [e for e in other_entries if e.debit > 0]

        if not counterparts:
            continue

        amount = ce.debit if ce.debit > 0 else ce.credit

        # Find matching CF item
        matched = False
        for cfi in cf_items:
            dr_set = parse_codes(cfi.debit_accounts)
            cr_set = parse_codes(cfi.credit_accounts)

            if cfi.direction == "inflow":
                # Cash is debited (received), counterpart credited
                for cp in counterparts:
                    cp_prefix = cp.account_code[:4]
                    cp_full = cp.account_code
                    if cp_full in cr_set or cp_prefix in cr_set or any(cp_full.startswith(c) for c in cr_set):
                        cf_data[cfi.code]["ytd"] += cp.credit
                        if is_may:
                            cf_data[cfi.code]["may"] += cp.credit
                        matched = True
                        break
            else:  # outflow
                # Cash is credited (paid), counterpart debited
                for cp in counterparts:
                    cp_prefix = cp.account_code[:4]
                    cp_full = cp.account_code
                    if cp_full in dr_set or cp_prefix in dr_set or any(cp_full.startswith(c) for c in dr_set):
                        cf_data[cfi.code]["ytd"] += cp.debit
                        if is_may:
                            cf_data[cfi.code]["may"] += cp.debit
                        matched = True
                        break

        # If no specific match, classify as "其他经营活动"
        if not matched and amount > 0:
            # Check if it looks like financing (other payables, borrowings)
            has_financing = any(e.account_code.startswith("2241") for e in other_entries if e.credit > 0 and ce.debit > 0)
            if has_financing and ce.debit > 0:
                cf_data["CF07"]["ytd"] += amount
                if is_may:
                    cf_data["CF07"]["may"] += amount
            else:
                cf_data["CF04"]["ytd"] += amount
                if is_may:
                    cf_data["CF04"]["may"] += amount

# 3. Print cash flow statement
print("\n" + "=" * 80)
print("  CASH FLOW STATEMENT - May 2026")
print("=" * 80)
print(f'  {"Item":45s} {"May":>14s} {"YTD":>14s}')
print("-" * 80)

cf_order = ["CF01", "CF02", "CF03", "CF04", "CF05", "CF06", "CF07", "CF08"]
cf_names = {i.code: i.name for i in cf_items}
cf_dir = {i.code: i.direction for i in cf_items}

# Operating
print("  [Operating Activities]")
op_in = op_out = op_in_ytd = op_out_ytd = 0.0
for code in ["CF01"]:
    name = cf_names.get(code, code)
    may = cf_data[code]["may"]
    ytd = cf_data[code]["ytd"]
    if may or ytd:
        print(f"  {name:45s} {may:>14,.2f} {ytd:>14,.2f}")
    op_in += may; op_in_ytd += ytd
print(f'  {"  Operating Inflow Subtotal":45s} {op_in:>14,.2f} {op_in_ytd:>14,.2f}')

for code in ["CF02", "CF03", "CF04"]:
    name = cf_names.get(code, code)
    may = cf_data[code]["may"]
    ytd = cf_data[code]["ytd"]
    if may or ytd:
        print(f"  {name:45s} {may:>14,.2f} {ytd:>14,.2f}")
    op_out += may; op_out_ytd += ytd
print(f'  {"  Operating Outflow Subtotal":45s} {op_out:>14,.2f} {op_out_ytd:>14,.2f}')
print(f'  {"  Net Operating Cash Flow":45s} {op_in - op_out:>14,.2f} {op_in_ytd - op_out_ytd:>14,.2f}')

# Investing
print("\n  [Investing Activities]")
inv_in = inv_out = inv_in_ytd = inv_out_ytd = 0.0
for code in ["CF05", "CF06"]:
    name = cf_names.get(code, code)
    may = cf_data[code]["may"]
    ytd = cf_data[code]["ytd"]
    if may or ytd:
        print(f"  {name:45s} {may:>14,.2f} {ytd:>14,.2f}")
    inv_out += may; inv_out_ytd += ytd
print(f'  {"  Net Investing Cash Flow":45s} {-inv_out:>14,.2f} {-inv_out_ytd:>14,.2f}')

# Financing
print("\n  [Financing Activities]")
fin_in = fin_out = fin_in_ytd = fin_out_ytd = 0.0
for code in ["CF07", "CF08"]:
    name = cf_names.get(code, code)
    may = cf_data[code]["may"]
    ytd = cf_data[code]["ytd"]
    if may or ytd:
        print(f"  {name:45s} {may:>14,.2f} {ytd:>14,.2f}")
    fin_in += may; fin_in_ytd += ytd
print(f'  {"  Net Financing Cash Flow":45s} {fin_in:>14,.2f} {fin_in_ytd:>14,.2f}')

# Totals
net_may = op_in - op_out - inv_out + fin_in
net_ytd = op_in_ytd - op_out_ytd - inv_out_ytd + fin_in_ytd

# Get cash balances from actual data
accounts = db.query(Account).filter(Account.company_id == cid).all()
cash_init = sum(a.initial_balance for a in accounts if a.code in ('1001', '1002') and a.level == 1)

def get_ending(code):
    a = next((x for x in accounts if x.code == code and x.level == 1), None)
    if not a:
        return 0
    children = [code] + [x.code for x in accounts if x.code != code and x.code.startswith(code)]
    d = c = 0.0
    for v in vouchers:
        for e in db.query(VoucherEntry).filter(VoucherEntry.voucher_id == v.id, VoucherEntry.account_code.in_(children)).all():
            d += e.debit; c += e.credit
    if a.balance_direction == "debit":
        return a.initial_balance + d - c
    return a.initial_balance + c - d

cash_end = sum(get_ending(c) for c in ('1001', '1002'))

print(f"\n  Opening Cash:     {cash_init:>14,.2f}")
print(f"  Net Change:       {net_ytd:>14,.2f}")
print(f"  Ending Cash:      {cash_end:>14,.2f}")
print(f"  Reconcile Diff:   {cash_end - cash_init - net_ytd:>14,.2f}")

# Show Excel comparison
print("\n" + "=" * 80)
print("  COMPARISON WITH EXCEL REPORT")
print("=" * 80)
excel_data = {
    "CF01_may": 20230.00, "CF01_ytd": 20230.00,
    "CF02_may": 10973.80, "CF02_ytd": 58653.80,
    "CF04_may": 8149.08, "CF04_ytd": 31641.70,
    "CF07_may": 70800.82, "CF07_ytd": 151285.05,
}

for code in cf_order:
    name = cf_names.get(code, code)
    may_sys = cf_data[code]["may"]
    ytd_sys = cf_data[code]["ytd"]
    may_xl = excel_data.get(f"{code}_may", 0)
    ytd_xl = excel_data.get(f"{code}_ytd", 0)

    if may_sys or may_xl or ytd_sys or ytd_xl:
        d_may = may_sys - may_xl
        d_ytd = ytd_sys - ytd_xl
        print(f"  {name:40s} May: sys={may_sys:>12,.2f} xl={may_xl:>12,.2f} diff={d_may:>10,.2f}  |  YTD: sys={ytd_sys:>12,.2f} xl={ytd_xl:>12,.2f} diff={d_ytd:>10,.2f}")

db.close()
