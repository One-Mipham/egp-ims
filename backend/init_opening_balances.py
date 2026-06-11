"""
直接以2026年4月30日期末余额作为系统初始化数据（5月1日切换上线）。
无需补录历史凭证，所有科目期初余额 = 4月30日确认报表的期末数。
"""
from app.database import SessionLocal
from app.models import Voucher, VoucherEntry, Account, Company

db = SessionLocal()
company = db.query(Company).first()

# ── Step 1: 删除所有凭证 ──
print("清空所有凭证...")
db.query(VoucherEntry).delete()
db.query(Voucher).delete()
db.commit()

# ── Step 2: 重置所有科目初始余额为0 ──
for a in db.query(Account).filter(Account.company_id == company.id).all():
    a.initial_balance = 0.0
db.commit()

# ── Step 3: 按4月30日确认报表设置期末余额 ──
# 确认报表 — 2026年4月30日资产负债表 (单位：元)
# ================================================================
# 资产 (Assets)
#   货币资金: 1,079,530.99    应收账款: 145,714.00
#   预付款项: 1,008,000.00    其他应收款: 663,979.10
#   存货: 500,000.00         可供出售金融资产: 30,000,000.00
#   长期股权投资: 16,900,000.00
# ================================================================
# 负债 (Liabilities)
#   应付职工薪酬: 807,440.00   应交税费: -237.63
#   其他应付款: 369,427.96    短期借款: 0
# ================================================================
# 所有者权益 (Equity)
#   实收资本: 49,975,000.00   未分配利润: -854,406.24
# ================================================================

# 科目余额分配 (子科目按年初比例分摊)
BALANCES = {
    # ── 资产类 ──
    # 货币资金 = 1,079,530.99
    # 年初: 100201=1,024,654.70, 100210=45,564.68 → ratio 95.74% / 4.26%
    "100201": 1079530.99 * (1024654.70 / 1070219.38),  # 招商银行
    "100210": 1079530.99 * (45564.68 / 1070219.38),      # 微众银行
    # 应收账款 = 145,714.00 (全部在 112201)
    "112201": 145714.00,
    # 预付款项 = 1,008,000.00
    "1123": 1008000.00,
    # 其他应收款 = 663,979.10
    # 年初分布: 122101=609,156.74, 122102=10,592.64, 122103=38,533.22 → total=658,282.60
    # 4月期末差额: 663,979.10 - 658,282.60 = +5,696.50 (按比例分摊)
    "122101": 663979.10 * (609156.74 / 658282.60),
    "122102": 663979.10 * (10592.64 / 658282.60),
    "122103": 663979.10 * (38533.22 / 658282.60),
    # 存货 = 500,000.00
    "1405": 500000.00,
    # 可供出售金融资产 = 30,000,000.00
    "1503": 30000000.00,
    # 长期股权投资 = 16,900,000.00
    "1511": 16900000.00,

    # ── 负债类 ──
    # 应付职工薪酬 = 807,440.00
    # 年初: 221101=791,540.00, 221102=10,900.00
    # 变化: +5,000 → 按比例分摊
    "221101": 807440.00 * (791540.00 / 802440.00),
    "221102": 807440.00 * (10900.00 / 802440.00),
    # 应交税费 = -237.63
    # 只保留 222115 (城建税), 无增值税余额
    "222115": -237.63,
    # 其他应付款 = 369,427.96
    # 年初: 224101=44,490.03, 224102=2,200.00, 224104=20,000.00,
    #       224105=153,347.99, 224106=128,139.94 → total=348,177.96
    # 变化: +21,250.00 → 按比例分摊
    "224101": 369427.96 * (44490.03 / 348177.96),
    "224102": 369427.96 * (2200.00 / 348177.96),
    "224104": 369427.96 * (20000.00 / 348177.96),
    "224105": 369427.96 * (153347.99 / 348177.96),
    "224106": 369427.96 * (128139.94 / 348177.96),

    # ── 权益类 ──
    "4001": 49975000.00,     # 实收资本
    "4104": -854406.24,      # 利润分配-未分配利润
}

# Apply balances
for code, val in BALANCES.items():
    acct = db.query(Account).filter(
        Account.code == code,
        Account.company_id == company.id
    ).first()
    if acct:
        acct.initial_balance = round(val, 2)
        print(f"  {code} {acct.name}: {acct.initial_balance:,.2f}")
    else:
        print(f"  WARNING: {code} not found")

db.commit()

# ── Step 4: 验证 ──
print("\n=== 验证：资产 = 负债 + 所有者权益 ===\n")

all_accts = db.query(Account).filter(Account.company_id == company.id).all()
parent_codes = set()
for a in all_accts:
    if a.parent_code:
        parent_codes.add(a.code)

assets = sum(a.initial_balance for a in all_accts
             if a.category == "asset" and a.code not in parent_codes)
liabilities = sum(a.initial_balance for a in all_accts
                  if a.category == "liability" and a.code not in parent_codes)
equity = sum(a.initial_balance for a in all_accts
             if a.category == "equity" and a.code not in parent_codes)

print(f"  资产总计: {assets:,.2f}")
print(f"  负债总计: {liabilities:,.2f}")
print(f"  所有者权益总计: {equity:,.2f}")
print(f"  负债+权益: {liabilities + equity:,.2f}")
print(f"  差异: {assets - (liabilities + equity):,.2f}")

# Verify against confirmed totals
print("\n=== 与确认报表4月30日数据对照 ===\n")
checks = {
    "货币资金 (1001+1002)": (1079530.99, sum(a.initial_balance for a in all_accts if a.code.startswith("100") and a.code not in parent_codes)),
    "应收账款 (1122)": (145714.00, sum(a.initial_balance for a in all_accts if a.code.startswith("1122") and a.code not in parent_codes)),
    "预付账款 (1123)": (1008000.00, sum(a.initial_balance for a in all_accts if a.code.startswith("1123") and a.code not in parent_codes)),
    "其他应收款 (1221)": (663979.10, sum(a.initial_balance for a in all_accts if a.code.startswith("1221") and a.code not in parent_codes)),
    "存货 (1405)": (500000.00, sum(a.initial_balance for a in all_accts if a.code.startswith("1405") and a.code not in parent_codes)),
    "可供出售 (1503)": (30000000.00, sum(a.initial_balance for a in all_accts if a.code.startswith("1503") and a.code not in parent_codes)),
    "长期股权投资 (1511)": (16900000.00, sum(a.initial_balance for a in all_accts if a.code.startswith("1511") and a.code not in parent_codes)),
    "应付职工薪酬 (2211)": (807440.00, sum(a.initial_balance for a in all_accts if a.code.startswith("2211") and a.code not in parent_codes)),
    "应交税费 (2221)": (-237.63, sum(a.initial_balance for a in all_accts if a.code.startswith("2221") and a.code not in parent_codes)),
    "其他应付款 (2241)": (369427.96, sum(a.initial_balance for a in all_accts if a.code.startswith("2241") and a.code not in parent_codes)),
    "实收资本 (4001)": (49975000.00, sum(a.initial_balance for a in all_accts if a.code.startswith("4001") and a.code not in parent_codes)),
    "未分配利润 (4104)": (-854406.24, sum(a.initial_balance for a in all_accts if a.code.startswith("4104") and a.code not in parent_codes)),
}

all_ok = True
for name, (expected, actual) in checks.items():
    actual = round(actual, 2)
    diff = round(actual - expected, 2)
    status = "✓" if abs(diff) < 0.10 else "✗ MISMATCH"
    if abs(diff) >= 0.10:
        all_ok = False
    print(f"  {status} {name}: {actual:,.2f} (expected {expected:,.2f}) diff={diff:,.2f}")

if all_ok:
    print("\n✓✓✓ 所有科目余额与确认报表一致！系统已准备好5月1日上线。")
else:
    print("\n⚠️  存在差异需要修复")

print(f"\n凭证数量: {db.query(Voucher).count()} (应为0)")
db.close()
