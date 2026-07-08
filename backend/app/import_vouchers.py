"""根据 2026.01-2026.04 科目发生额及余额表，重建凭证并过账。

基于官方试算表反推月度分解，确保三张财务报表与原始数据一致。
"""
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.database import SessionLocal, init_db
from app.models import Account, Company, Department, Voucher, VoucherEntry, AccountingPeriod

CREATOR_ID = 1

# ═══════════════════════════════════════════════════════════
# 月度费用分解（基于试算表反推）
#
# 管理费月度总额（来自官方利润表）:
#   1月 17,920 | 2月 25,244.10 | 3月 22,420 | 4月 18,920 | 合计 84,504.10
#
# 试算表固定项:
#   技术服务费 6,824.1 → 全部4月
#   物业费 5,000 → 4月均分 = 1,250/月
#   房租 15,000 → 4月均分 = 3,750/月
#   工资 52,680 + 福利 5,000 = 57,680 → 按月度剩余比例分配
#
# 财务费用（来自官方利润表）:
#   1月 25.00 | 2月 34.67 | 3月 32.52 | 4月 31.00 | 合计 123.19
# ═══════════════════════════════════════════════════════════

VOUCHERS = [
    # ═══════════════════════════════════════════════════════
    # 1 月：管理费 17,920 | 财务费用 25 | 收入 0
    # 工资 11,800.03 + 福利 1,119.97 + 物业 1,250 + 房租 3,750 = 17,920
    # 银行手续费 25.13 - 利息收入 0.13 = 25.00
    # ═══════════════════════════════════════════════════════

    ("2026-01-15", "记-001", "accrual", "计提1月人员费用", [
        ("66020101", 11800.03, 0.0, "005"),   # 管理费用-人员费用-工资
        ("66020109", 1119.97, 0.0, "004"),    # 管理费用-人员费用-福利费
        ("221101", 0.0, 11800.03, None),      # 应付职工薪资-工资
        ("221102", 0.0, 1119.97, None),       # 应付职工薪资-职工福利费
    ]),

    ("2026-01-20", "记-002", "accrual", "计提1月物业费和房租", [
        ("66020901", 1250.0, 0.0, "004"),     # 管理费用-物业费
        ("66020904", 3750.0, 0.0, "004"),     # 管理费用-物业费-房租
        ("224104", 0.0, 5000.0, None),        # 其他应付款-房租
    ]),

    ("2026-01-25", "记-003", "payment", "1月银行手续费", [
        ("660301", 25.0, 0.0, None),          # 财务费用-手续费
        ("100210", 0.0, 25.0, None),          # 微众银行
    ]),

    ("2026-01-31", "记-004", "transfer", "结转1月损益", [
        ("66020101", 0.0, 11800.03, None),
        ("66020109", 0.0, 1119.97, None),
        ("66020901", 0.0, 1250.0, None),
        ("66020904", 0.0, 3750.0, None),
        ("660301", 0.0, 25.0, None),
        ("4103", 17945.0, 0.0, None),
    ]),

    # ═══════════════════════════════════════════════════════
    # 2 月：管理费 25,244.10 | 财务费用 34.67 | 收入 52,000
    # 工资 18,489.24 + 福利 1,754.86 + 物业 1,250 + 房租 3,750 = 25,244.10
    # 银行手续费 35.41 - 利息收入 0.74 = 34.67
    # ═══════════════════════════════════════════════════════

    ("2026-02-10", "记-005", "receipt", "确认2月咨询业务收入", [
        ("112201", 53560.0, 0.0, None),       # 应收账款-咨询
        ("60010304", 0.0, 22000.0, "013"),    # 主营业务收入-财务咨询
        ("60010307", 0.0, 30000.0, "013"),    # 主营业务收入-技术咨询
        ("22210106", 0.0, 1560.0, None),      # 销项税额
    ]),

    ("2026-02-15", "记-006", "accrual", "计提2月人员费用", [
        ("66020101", 18489.24, 0.0, "005"),   # 管理费用-人员费用-工资
        ("66020109", 1754.86, 0.0, "004"),    # 管理费用-人员费用-福利费
        ("221101", 0.0, 18489.24, None),      # 应付职工薪资-工资
        ("221102", 0.0, 1754.86, None),       # 应付职工薪资-职工福利费
    ]),

    ("2026-02-20", "记-007", "accrual", "计提2月物业费和房租", [
        ("66020901", 1250.0, 0.0, "004"),
        ("66020904", 3750.0, 0.0, "004"),
        ("224104", 0.0, 5000.0, None),
    ]),

    ("2026-02-25", "记-008", "payment", "2月银行手续费", [
        ("660301", 34.67, 0.0, None),
        ("100210", 0.0, 34.67, None),
    ]),

    ("2026-02-28", "记-009", "transfer", "结转2月损益", [
        ("60010304", 22000.0, 0.0, None),
        ("60010307", 30000.0, 0.0, None),
        ("66020101", 0.0, 18489.24, None),
        ("66020109", 0.0, 1754.86, None),
        ("66020901", 0.0, 1250.0, None),
        ("66020904", 0.0, 3750.0, None),
        ("660301", 0.0, 34.67, None),
        ("4103", 0.0, 26721.23, None),
    ]),

    # ═══════════════════════════════════════════════════════
    # 3 月：管理费 22,420 | 财务费用 32.52 | 收入 0
    # 工资 15,909.94 + 福利 1,510.06 + 物业 1,250 + 房租 3,750 = 22,420
    # 银行手续费 31.44 - 利息收入(-1.08) = 32.52
    # ═══════════════════════════════════════════════════════

    ("2026-03-15", "记-010", "accrual", "计提3月人员费用", [
        ("66020101", 15909.94, 0.0, "005"),
        ("66020109", 1510.06, 0.0, "004"),
        ("221101", 0.0, 15909.94, None),
        ("221102", 0.0, 1510.06, None),
    ]),

    ("2026-03-20", "记-011", "accrual", "计提3月物业费和房租", [
        ("66020901", 1250.0, 0.0, "004"),
        ("66020904", 3750.0, 0.0, "004"),
        ("224104", 0.0, 5000.0, None),
    ]),

    ("2026-03-25", "记-012", "payment", "3月银行手续费", [
        ("660301", 32.52, 0.0, None),
        ("100210", 0.0, 32.52, None),
    ]),

    ("2026-03-31", "记-013", "transfer", "结转3月损益", [
        ("66020101", 0.0, 15909.94, None),
        ("66020109", 0.0, 1510.06, None),
        ("66020901", 0.0, 1250.0, None),
        ("66020904", 0.0, 3750.0, None),
        ("660301", 0.0, 32.52, None),
        ("4103", 22452.52, 0.0, None),
    ]),

    # ═══════════════════════════════════════════════════════
    # 4 月：管理费 18,920 | 财务费用 31 | 收入 0
    # 工资 6,480.79 + 福利 615.11 + 物业 1,250 + 房租 3,750 + 技术服务 6,824.10 = 18,920
    # 银行手续费 31.0（4月无利息收入）
    # ═══════════════════════════════════════════════════════

    ("2026-04-10", "记-014", "accrual", "计提4月人员费用", [
        ("66020101", 6480.79, 0.0, "005"),
        ("66020109", 615.11, 0.0, "004"),
        ("221101", 0.0, 6480.79, None),
        ("221102", 0.0, 615.11, None),
    ]),

    ("2026-04-15", "记-015", "accrual", "计提4月物业费和房租", [
        ("66020901", 1250.0, 0.0, "004"),
        ("66020904", 3750.0, 0.0, "004"),
        ("224104", 0.0, 5000.0, None),
    ]),

    ("2026-04-18", "记-016", "payment", "支付技术服务费", [
        ("660210", 6824.1, 0.0, "004"),        # 管理费用-技术服务费
        ("100210", 0.0, 6824.1, None),         # 微众银行
    ]),

    ("2026-04-25", "记-017", "payment", "4月银行手续费", [
        ("660301", 31.0, 0.0, None),
        ("100210", 0.0, 31.0, None),
    ]),

    ("2026-04-30", "记-018", "transfer", "结转4月损益", [
        ("66020101", 0.0, 6480.79, None),
        ("66020109", 0.0, 615.11, None),
        ("66020901", 0.0, 1250.0, None),
        ("66020904", 0.0, 3750.0, None),
        ("660210", 0.0, 6824.1, None),
        ("660301", 0.0, 31.0, None),
        ("4103", 18951.0, 0.0, None),         # 本年利润（净亏损）
    ]),

    # 增值税结转（进项税额 → 销项税额，两者相等，应交增值税为0）
    ("2026-04-30", "记-019-vat", "transfer", "结转增值税", [
        ("22210106", 1560.0, 0.0, None),      # 销项税额（借方冲减）
        ("22210101", 0.0, 1560.0, None),      # 进项税额（贷方冲减）
    ]),

    # 本年利润结转至未分配利润
    # 1月: -17,945 | 2月: +26,721.23 | 3月: -22,452.52 | 4月: -18,951
    # 累计: -32,627.29 → 4103 借方余额 32,627.29
    ("2026-04-30", "记-020-retained", "transfer", "结转本年利润至未分配利润", [
        ("4104", 32627.29, 0.0, None),        # 利润分配-未分配利润（借方=亏损）
        ("4103", 0.0, 32627.29, None),        # 本年利润（贷方清零）
    ]),

    # ═══════════════════════════════════════════════════════
    # 投资与资本类凭证
    # ═══════════════════════════════════════════════════════

    ("2026-02-15", "记-021", "receipt", "股东投入资本金", [
        ("100210", 46975000.0, 0.0, None),     # 微众银行
        ("4001", 0.0, 46975000.0, None),       # 实收资本
    ]),

    ("2026-03-20", "记-022", "payment", "购入可供出售金融资产", [
        ("1503", 30000000.0, 0.0, None),       # 可供出售金融资产
        ("100210", 0.0, 30000000.0, None),     # 微众银行
    ]),

    ("2026-03-25", "记-023", "payment", "长期股权投资", [
        ("1511", 16900000.0, 0.0, None),       # 长期股权投资
        ("100210", 0.0, 16900000.0, None),     # 微众银行
    ]),

    # ═══════════════════════════════════════════════════════
    # 往来调整
    # ═══════════════════════════════════════════════════════

    ("2026-04-15", "记-024", "transfer", "往来调整—个人往来", [
        ("100210", 12200.0, 0.0, None),        # 微众银行
        ("224101", 0.0, 10000.0, None),        # 其他应付款-张国华
        ("224102", 0.0, 2200.0, None),         # 其他应付款-李素敏
    ]),

    ("2026-04-20", "记-025", "payment", "支付房租押金", [
        ("224104", 5000.0, 0.0, None),         # 其他应付款-房租
        ("100210", 0.0, 5000.0, None),         # 微众银行
    ]),

    ("2026-04-22", "记-026", "payment", "确认进项税额", [
        ("22210101", 1560.0, 0.0, None),       # 进项税额
        ("100210", 0.0, 1560.0, None),         # 微众银行
    ]),

    # 应付工资实际支付（4月支付）
    ("2026-04-28", "记-027", "payment", "支付应付工资", [
        ("221101", 47680.0, 0.0, None),        # 应付职工薪资-工资
        ("100210", 0.0, 47680.0, None),        # 微众银行
    ]),
]


def get_department_by_code(db: Session, company_id: int, code: str) -> int | None:
    dept = db.query(Department).filter(
        Department.company_id == company_id, Department.code == code
    ).first()
    return dept.id if dept else None


def get_account_by_code(db: Session, company_id: int, code: str) -> Account | None:
    return db.query(Account).filter(
        Account.company_id == company_id, Account.code == code
    ).first()


def ensure_periods(db: Session, company_id: int):
    for month in ["2026-01", "2026-02", "2026-03", "2026-04"]:
        period = db.query(AccountingPeriod).filter(
            AccountingPeriod.company_id == company_id,
            AccountingPeriod.period == month,
        ).first()
        if not period:
            db.add(AccountingPeriod(
                company_id=company_id, period=month, is_closed=False
            ))
    db.commit()


def create_vouchers(db: Session, company_id: int) -> int:
    """创建全部凭证并过账。"""
    from app.models import VoucherEntry as VE
    existing_vouchers = db.query(Voucher).filter(Voucher.company_id == company_id).all()
    for v in existing_vouchers:
        db.query(VE).filter(VE.voucher_id == v.id).delete()
    db.query(Voucher).filter(Voucher.company_id == company_id).delete()
    db.commit()

    created = 0
    for date_str, voucher_no, vtype, summary, entries_data in VOUCHERS:
        voucher = Voucher(
            company_id=company_id,
            date=date_str,
            voucher_no=voucher_no,
            voucher_type=vtype,
            summary=summary,
            creator_id=CREATOR_ID,
            status="posted",
            approved_by=CREATOR_ID,
            approved_at=datetime.now(timezone.utc),
            posted_by=CREATOR_ID,
            posted_at=datetime.now(timezone.utc),
        )
        db.add(voucher)
        db.flush()

        for acct_code, debit, credit, dept_code in entries_data:
            acct = get_account_by_code(db, company_id, acct_code)
            if not acct:
                print(f"    警告：科目 {acct_code} 不存在，跳过")
                continue
            dept_id = None
            if dept_code:
                dept_id = get_department_by_code(db, company_id, dept_code)
            db.add(VoucherEntry(
                voucher_id=voucher.id,
                account_code=acct_code,
                department_id=dept_id,
                debit=debit,
                credit=credit,
            ))
        created += 1

    db.commit()
    return created


def verify_balances(db: Session, company_id: int):
    """验证借贷平衡。"""
    from sqlalchemy import func as sa_func
    from app.models import VoucherEntry as VE

    voucher_count = db.query(Voucher).filter(
        Voucher.company_id == company_id
    ).count()
    entry_count = db.query(VE).join(Voucher).filter(
        Voucher.company_id == company_id
    ).count()

    total_dr = db.query(sa_func.sum(VE.debit)).join(Voucher).filter(
        Voucher.company_id == company_id
    ).scalar() or 0
    total_cr = db.query(sa_func.sum(VE.credit)).join(Voucher).filter(
        Voucher.company_id == company_id
    ).scalar() or 0

    print(f"  凭证数: {voucher_count}")
    print(f"  分录数: {entry_count}")
    print(f"  借方合计: {total_dr:,.2f}")
    print(f"  贷方合计: {total_cr:,.2f}")
    diff = abs(total_dr - total_cr)
    if diff < 0.01:
        print(f"  借贷平衡: 差异 {diff:.2f} OK")
    else:
        print(f"  WARNING: 借贷不平衡! 差异 {diff:,.2f}")

    # 按科目汇总发生额
    print()
    print("  科目发生额汇总:")
    rows = db.query(
        VE.account_code,
        sa_func.sum(VE.debit),
        sa_func.sum(VE.credit)
    ).join(Voucher).filter(
        Voucher.company_id == company_id
    ).group_by(VE.account_code).order_by(
        sa_func.sum(VE.debit) + sa_func.sum(VE.credit)
    ).all()

    for code, dr, cr in rows:
        if dr > 0 or cr > 0:
            acct = db.query(Account).filter(
                Account.company_id == company_id, Account.code == code
            ).first()
            name = acct.name if acct else "?"
            print(f"    {code} {name}: DR={dr:>14,.2f}  CR={cr:>14,.2f}")

    # 按月汇总
    print()
    print("  按月汇总（收入/管理费/财务费）:")
    for month in ["2026-01", "2026-02", "2026-03", "2026-04"]:
        month_prefix = month[:7]
        revenue = db.query(sa_func.sum(VE.credit)).join(Voucher).join(
            Account, VE.account_code == Account.code
        ).filter(
            Voucher.company_id == company_id,
            Account.category == "profit_loss",
            Account.code.like("60%"),
            Voucher.date.startswith(month_prefix),
        ).scalar() or 0

        mgmt_exp = db.query(sa_func.sum(VE.debit)).join(Voucher).join(
            Account, VE.account_code == Account.code
        ).filter(
            Voucher.company_id == company_id,
            Account.code.like("6602%"),
            Voucher.date.startswith(month_prefix),
        ).scalar() or 0

        fin_exp = db.query(sa_func.sum(VE.debit) - sa_func.sum(VE.credit)).join(Voucher).join(
            Account, VE.account_code == Account.code
        ).filter(
            Voucher.company_id == company_id,
            Account.code.like("6603%"),
            Voucher.date.startswith(month_prefix),
        ).scalar() or 0

        profit = revenue - mgmt_exp - fin_exp
        print(f"    {month}: 收入={revenue:>12,.2f}  管理费={mgmt_exp:>12,.2f}  财务费={fin_exp:>10,.2f}  利润={profit:>12,.2f}")


def main():
    print("=" * 50)
    print("2026年凭证导入（基于试算表重建）")
    print("=" * 50)
    init_db()
    db = SessionLocal()
    try:
        company = db.query(Company).filter(
            Company.name == "青岛利美融信投资控股有限责任公司"
        ).first()
        if not company:
            print("错误：公司不存在，请先运行 import_data.py")
            return

        company_id = company.id
        print(f"  公司: {company.name} (id={company_id})")

        ensure_periods(db, company_id)
        print("  期间: 2026-01 至 2026-04 OK")

        print()
        print("创建凭证...")
        created = create_vouchers(db, company_id)
        print(f"  创建凭证: {created} 张")

        print()
        print("验证...")
        verify_balances(db, company_id)

        print()
        print("=" * 50)
        print("凭证导入完成！")
        print("请在浏览器中查看三张财务报表验证数据。")
        print("=" * 50)
    finally:
        db.close()


if __name__ == "__main__":
    main()
