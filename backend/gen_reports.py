"""Generate May 2026 reports and compare with Excel."""
import sys, os
os.chdir("/opt/egp-ims/intranet/backend")
sys.path.insert(0, ".")

from app.database import SessionLocal
from app.models import Voucher, VoucherEntry, Account
from collections import defaultdict

db = SessionLocal()
cid = 1

# Post all vouchers
vouchers = db.query(Voucher).filter(Voucher.company_id == cid).all()
for v in vouchers:
    v.status = "posted"
db.commit()

accounts = db.query(Account).filter(Account.company_id == cid, Account.is_active == True).order_by(Account.code).all()

# Build activity
may_act = defaultdict(lambda: {"d": 0.0, "c": 0.0})
ytd_act = defaultdict(lambda: {"d": 0.0, "c": 0.0})
for v in vouchers:
    is_may = v.date.startswith("2026-05")
    for e in db.query(VoucherEntry).filter(VoucherEntry.voucher_id == v.id).all():
        ytd_act[e.account_code]["d"] += e.debit
        ytd_act[e.account_code]["c"] += e.credit
        if is_may:
            may_act[e.account_code]["d"] += e.debit
            may_act[e.account_code]["c"] += e.credit

def children(code):
    return [code] + [a.code for a in accounts if a.code != code and a.code.startswith(code)]

# ============================
# Trial Balance (Level 1)
# ============================
print("=" * 90)
print("  TRIAL BALANCE - May 2026 (Level 1)")
print("=" * 90)
hdr = f"{'Code':10s} {'Name':24s} {'InitBal':>14s} {'MayDr':>14s} {'MayCr':>14s} {'EndBal':>14s}"
print(hdr)
print("-" * 90)

dr_init = cr_init = may_d = may_c = edr = ecr = 0.0
for a in accounts:
    if a.level != 1:
        continue
    ch = children(a.code)
    init = a.initial_balance
    md = sum(may_act[c]["d"] for c in ch)
    mc = sum(may_act[c]["c"] for c in ch)

    if a.balance_direction == "debit":
        end = init + md - mc
    else:
        end = init + mc - md

    if a.balance_direction == "debit":
        if init > 0: dr_init += init
        else: cr_init += abs(init)
    else:
        if init > 0: cr_init += init
        else: dr_init += abs(init)

    if end > 0:
        if a.balance_direction == "debit": edr += end
        else: ecr += end
    else:
        if a.balance_direction == "debit": ecr += abs(end)
        else: edr += abs(end)

    may_d += md; may_c += mc

    if init != 0 or md != 0 or mc != 0:
        print(f"{a.code:10s} {a.name:24s} {init:>14,.2f} {md:>14,.2f} {mc:>14,.2f} {end:>14,.2f}")

print("-" * 90)
print(f"{'TOTAL':34s} {'':>14s} {may_d:>14,.2f} {may_c:>14,.2f} {'':>14s}")
print(f"  Init: Dr={dr_init:,.2f} Cr={cr_init:,.2f} Diff={abs(dr_init-cr_init):,.2f} {'OK' if abs(dr_init-cr_init)<0.01 else 'IMBAL'}")
print(f"  End:  Dr={edr:,.2f} Cr={ecr:,.2f} Diff={abs(edr-ecr):,.2f} {'OK' if abs(edr-ecr)<0.01 else 'IMBAL'}")

# ============================
# Income Statement (May)
# ============================
print("\n" + "=" * 90)
print("  INCOME STATEMENT - May 2026")
print("=" * 90)

rev = exp = cost = 0.0
for a in accounts:
    if a.level != 1:
        continue
    ch = children(a.code)
    md = sum(may_act[c]["d"] for c in ch)
    mc = sum(may_act[c]["c"] for c in ch)
    if md == 0 and mc == 0:
        continue

    if a.code.startswith("6") and a.category in ("profit_loss",):
        net = mc - md
        rev += net
        print(f"  [Revenue]  {a.code} {a.name:30s} Dr={md:>12,.2f} Cr={mc:>12,.2f} Net={net:>12,.2f}")
    elif a.code.startswith("5"):
        net = md - mc
        cost += net
        print(f"  [Cost]     {a.code} {a.name:30s} Dr={md:>12,.2f} Cr={mc:>12,.2f} Net={net:>12,.2f}")
    elif a.code.startswith("6"):
        net = md - mc
        exp += net
        print(f"  [Expense]  {a.code} {a.name:30s} Dr={md:>12,.2f} Cr={mc:>12,.2f} Net={net:>12,.2f}")

print(f"\n  Revenue:  {rev:>14,.2f}")
print(f"  Cost:     {cost:>14,.2f}")
print(f"  Expense:  {exp:>14,.2f}")
print(f"  Net Profit: {rev - cost - exp:>14,.2f}")

# ============================
# Summary per month
# ============================
print("\n" + "=" * 90)
print("  MONTHLY SUMMARY")
print("=" * 90)
for m in range(1, 6):
    month = f"2026-{m:02d}"
    mvs = [v for v in vouchers if v.date.startswith(month)]
    md = mc = 0.0
    entries = 0
    for v in mvs:
        for e in db.query(VoucherEntry).filter(VoucherEntry.voucher_id == v.id).all():
            md += e.debit
            mc += e.credit
            entries += 1
    print(f"  {month}: {len(mvs):3d} vouchers, {entries:4d} entries, Dr={md:>14,.2f}, Cr={mc:>14,.2f}, {'OK' if abs(md-mc)<0.01 else 'IMBAL'}")

db.close()
