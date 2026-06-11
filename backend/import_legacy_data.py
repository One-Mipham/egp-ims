"""Past System 数据导入脚本 — 从 basic_master_data/ 导入基础档案、科目、期初余额、1-4月汇总凭证。"""
import sys, os
from pathlib import Path
import pandas as pd
from datetime import date

sys.path.insert(0, str(Path(__file__).parent))

from app.database import SessionLocal
from app.models import (
    Account, Company, Department, Counterparty, Person,
    Voucher, VoucherEntry, AuditLog,
    VoucherTemplate,
    Region, Warehouse, UnitOfMeasure, SettlementMethod, BankAccount,
    InventoryCategory, Inventory, ExpenseItem, RevenueItem,
    CashFlowCategory, CashFlowItem,
)

DATA = Path(__file__).parent.parent / "basic_master_data"

CATEGORY_MAP = {
    "资产": "asset", "负债": "liability", "权益": "equity",
    "成本": "cost", "损益": "profit_loss",
}
DIR_MAP = {"借方": "debit", "贷方": "credit"}

def read_sheet(filename, sheet_name=None, header_row=1):
    fp = DATA / filename
    if not fp.exists():
        print(f"  SKIP: {filename} not found")
        return None
    kwargs = {"header": header_row} if header_row is not None else {}
    if sheet_name:
        return pd.read_excel(fp, sheet_name=sheet_name, **kwargs)
    return pd.read_excel(fp, **kwargs)


def import_accounts(db, company_id):
    """从原系统科目表创建子科目（level 2/3/4）并更新辅助核算配置。"""
    df = read_sheet("科目.xlsx", "科目", header_row=0)
    if df is None:
        return
    df = df.iloc[1:]  # skip instruction row
    df.columns = [
        "settle_flag", "forex_adjust", "code", "name", "mnemonic",
        "type_code", "type_name", "stopped", "page_format", "balance_dir",
        "is_cash", "is_bank", "cash_equiv", "summary_print", "summary_code",
        "summary_name", "qty_acct", "unit", "forex_acct", "default_ccy_code",
        "default_ccy", "controlled", "biz_sys", "ctrl_manual",
        "aux_dept", "aux_person", "aux_counterparty", "aux_inventory", "aux_project",
    ]
    created = 0
    updated = 0
    for _, row in df.iterrows():
        code = str(row["code"]).strip()
        if not code or code == "nan":
            continue
        existing = db.query(Account).filter(
            Account.company_id == company_id, Account.code == code
        ).first()
        if existing:
            existing.aux_dept = int(row["aux_dept"] or 0)
            existing.aux_person = int(row["aux_person"] or 0)
            existing.aux_counterparty = int(row["aux_counterparty"] or 0)
            existing.aux_project = int(row["aux_project"] or 0)
            updated += 1
        else:
            level = 1 if len(code) <= 4 else (2 if len(code) == 6 else (3 if len(code) == 8 else 4))
            parent = None
            if level > 1:
                parent_code_len = 4 + (level - 2) * 2
                parent = code[:parent_code_len] if len(code) > parent_code_len else None
            cat = CATEGORY_MAP.get(row["type_name"], "asset")
            bal_dir = DIR_MAP.get(row["balance_dir"], "debit")
            db.add(Account(
                company_id=company_id, code=code, name=str(row["name"]).strip(),
                level=level, parent_code=parent or None,
                category=cat, balance_direction=bal_dir,
                initial_balance=0.0, is_system=False,
                aux_dept=int(row["aux_dept"] or 0),
                aux_person=int(row["aux_person"] or 0),
                aux_counterparty=int(row["aux_counterparty"] or 0),
                aux_project=int(row["aux_project"] or 0),
            ))
            created += 1
    db.commit()
    print(f"  科目: 新建 {created}, 更新辅助核算 {updated}")


def set_opening_balances(db, company_id):
    """从发生额及余额表设置末级科目期初余额，再向上汇总父科目。"""
    fp = DATA / "2026.01.01-2026.4.30-科目发生额及余额表.xlsx"
    if not fp.exists():
        print("  SKIP: 发生额及余额表 not found")
        return
    df = pd.read_excel(fp, sheet_name="第一页", header=None)

    # Build list of accounts from balance sheet
    accounts_data = []
    for _, row in df.iterrows():
        cat = row.iloc[1]
        code = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else ""
        if not code or code == "nan":
            continue
        if cat not in ("资产", "负债", "权益", "成本", "损益"):
            continue
        opening_dr = float(row.iloc[5]) if pd.notna(row.iloc[5]) else 0.0
        opening_cr = float(row.iloc[6]) if pd.notna(row.iloc[6]) else 0.0
        accounts_data.append({
            "code": code, "cat": cat,
            "opening": opening_dr - opening_cr,
        })

    all_codes = {a["code"] for a in accounts_data}
    # Leaf = no other account has this code as prefix
    leaves = {a["code"]: a for a in accounts_data
              if not any(c.startswith(a["code"]) and c != a["code"] for c in all_codes)}

    all_accounts = db.query(Account).filter(Account.company_id == company_id).all()
    code_to_acct = {a.code: a for a in all_accounts}

    # Zero all first
    for a in all_accounts:
        a.initial_balance = 0.0
    db.flush()

    # Set leaf balances (store as positive, direction indicated by balance_direction)
    updated = 0
    for code, data in leaves.items():
        acct = code_to_acct.get(code)
        if acct:
            if acct.balance_direction == "credit":
                acct.initial_balance = -data["opening"]  # cr - dr = -(dr - cr)
            else:
                acct.initial_balance = data["opening"]
            updated += 1

    # Bottom-up recompute parents
    by_level = {}
    for a in all_accounts:
        by_level.setdefault(a.level, []).append(a)

    recomputed = 0
    for level in sorted(by_level.keys(), reverse=True):
        if level == 1:
            continue
        for child in by_level[level]:
            pc = child.parent_code or (child.code[:4] if len(child.code) > 4 else None)
            if pc and pc in code_to_acct:
                parent = code_to_acct[pc]
                parent.initial_balance = (parent.initial_balance or 0.0) + (child.initial_balance or 0.0)
                recomputed += 1

    db.commit()
    print(f"  期初余额: 末级 {updated} 个科目, 向上汇总 {recomputed} 次")


def import_counterparties(db, company_id):
    """导入往来单位。"""
    df = read_sheet("往来单位.xlsx", "往来单位", header_row=1)
    if df is None:
        return
    created = 0
    for _, row in df.iterrows():
        code = str(row.iloc[0]).strip()
        name = str(row.iloc[1]).strip()
        if not code or code == "nan" or not name or name == "nan":
            continue
        if db.query(Counterparty).filter(
            Counterparty.company_id == company_id, Counterparty.code == code
        ).first():
            continue
        cat_code = str(row.iloc[4]).strip() if pd.notna(row.iloc[4]) else "0000001"
        cat_name = str(row.iloc[5]).strip() if pd.notna(row.iloc[5]) else "咨询"
        db.add(Counterparty(
            company_id=company_id, code=code, name=name,
            category_code=cat_code, category=cat_name,
            contact_person=str(row.iloc[16] or "").strip() if pd.notna(row.iloc[16]) else "",
            phone=str(row.iloc[21] or "").strip() if pd.notna(row.iloc[21]) else "",
        ))
        created += 1
    db.commit()
    print(f"  往来单位: 导入 {created}")


def import_employees(db, company_id):
    """导入员工。"""
    df = read_sheet("员工.xlsx", "员工", header_row=1)
    if df is None:
        return
    created = 0
    for _, row in df.iterrows():
        name = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
        if not name or name == "nan":
            continue
        if db.query(Person).filter(
            Person.company_id == company_id, Person.name == name
        ).first():
            continue
        code = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else f"EMP{created+1:04d}"
        dept_code = str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else None
        db.add(Person(
            company_id=company_id, code=code, name=name,
            department_code=dept_code if dept_code and dept_code != "nan" else None,
        ))
        created += 1
    db.commit()
    print(f"  员工: 导入 {created}")


def import_departments(db, company_id):
    """从原系统科目表的辅助核算配置推断并创建部门。"""
    existing = {d.name for d in db.query(Department).filter(
        Department.company_id == company_id
    ).all()}
    # 利美融信的部门来自原系统往来单位中的分管部门
    df = read_sheet("往来单位.xlsx", "往来单位", header_row=1)
    if df is None:
        return
    created = 0
    seen = set()
    for _, row in df.iterrows():
        dept_code = str(row.iloc[10]).strip() if pd.notna(row.iloc[10]) else ""
        dept_name = str(row.iloc[11]).strip() if pd.notna(row.iloc[11]) else ""
        if not dept_name or dept_name == "nan" or dept_name in seen:
            continue
        seen.add(dept_name)
        if dept_name in existing:
            continue
        db.add(Department(
            company_id=company_id, code=dept_code if dept_code and dept_code != "nan" else f"D{created+1:03d}",
            name=dept_name,
        ))
        created += 1
    db.commit()
    print(f"  部门: 导入 {created}")


def create_period_vouchers(db, company_id):
    """从发生额及余额表反推 1-4 月汇总凭证（仅末级科目）并记账。"""
    fp = DATA / "2026.01.01-2026.4.30-科目发生额及余额表.xlsx"
    if not fp.exists():
        print("  SKIP: 发生额及余额表 not found")
        return

    # Delete old imported vouchers (must delete entries first for cascade to work)
    old_vouchers = db.query(Voucher).filter(
        Voucher.company_id == company_id,
        Voucher.summary.contains("科目发生额汇总导入"),
    ).all()
    deleted = len(old_vouchers)
    for v in old_vouchers:
        db.query(VoucherEntry).filter(VoucherEntry.voucher_id == v.id).delete()
        db.delete(v)
    if deleted:
        db.commit()
        print(f"  删除旧凭证: {deleted} 条")

    df = pd.read_excel(fp, sheet_name="第一页", header=None)
    all_rows = []
    for _, row in df.iterrows():
        cat = row.iloc[1]
        code = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else ""
        if not code or code == "nan" or cat not in ("资产", "负债", "权益", "成本", "损益"):
            continue
        name = str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else ""
        period_dr = float(row.iloc[7]) if pd.notna(row.iloc[7]) else 0.0
        period_cr = float(row.iloc[8]) if pd.notna(row.iloc[8]) else 0.0
        all_rows.append({"code": code, "name": name, "period_dr": period_dr, "period_cr": period_cr})

    all_codes = {r["code"] for r in all_rows}
    # Use only leaf accounts
    accounts_data = [
        r for r in all_rows
        if not any(c.startswith(r["code"]) and c != r["code"] for c in all_codes)
        and abs(r["period_dr"] - r["period_cr"]) > 0.005
    ]

    if not accounts_data:
        print("  无发生额数据")
        return

    admin_id = 1
    months = [
        (date(2026, 1, 31), "2026-01"),
        (date(2026, 2, 28), "2026-02"),
        (date(2026, 3, 31), "2026-03"),
        (date(2026, 4, 30), "2026-04"),
    ]

    total_created = 0
    for voucher_date, month_label in months:
        entries = []
        for item in accounts_data:
            monthly_dr = round(item["period_dr"] / 4, 2)
            monthly_cr = round(item["period_cr"] / 4, 2)
            if monthly_dr > 0 or monthly_cr > 0:
                entries.append({
                    "account_code": item["code"],
                    "debit": monthly_dr,
                    "credit": monthly_cr,
                    "description": f"{month_label} 发生额汇总",
                })

        if not entries:
            continue

        # Balance the voucher: add rounding difference to 银行存款
        total_dr = sum(e["debit"] for e in entries)
        total_cr = sum(e["credit"] for e in entries)
        diff = round(total_dr - total_cr, 2)
        if abs(diff) > 0.01:
            entries.append({
                "account_code": "1002",
                "debit": max(0, -diff),
                "credit": max(0, diff),
                "description": f"{month_label} 汇总差额调整",
            })

        # Recalculate totals
        total_dr = round(sum(e["debit"] for e in entries), 2)
        total_cr = round(sum(e["credit"] for e in entries), 2)

        # Validate balance
        if abs(total_dr - total_cr) > 0.02 or total_dr < 0.01:
            print(f"  WARNING: {month_label} unbalanced dr={total_dr} cr={total_cr}")
            continue

        # Check for existing
        existing = db.query(Voucher).filter(
            Voucher.company_id == company_id,
            Voucher.date == str(voucher_date),
            Voucher.summary == f"{month_label} 科目发生额汇总导入",
        ).first()
        if existing:
            print(f"  SKIP: {month_label} voucher already exists")
            continue

        voucher = Voucher(
            company_id=company_id,
            date=str(voucher_date),
            voucher_no=f"记字{month_label.replace('-','')}-0001",
            voucher_type="transfer",
            summary=f"{month_label} 科目发生额汇总导入",
            creator_id=admin_id,
            status="draft",
        )
        db.add(voucher)
        db.flush()

        for e in entries:
            db.add(VoucherEntry(
                voucher_id=voucher.id,
                account_code=e["account_code"],
                debit=e["debit"],
                credit=e["credit"],
                description=e["description"],
            ))

        # Auto-approve and post
        voucher.status = "posted"
        voucher.posted_by = admin_id
        voucher.posted_at = voucher_date

        db.add(AuditLog(
            user_id=admin_id, company_id=company_id,
            action="import_period_voucher",
            target_type="voucher",
            target_id=voucher.id,
            reason=f"原系统导入 {month_label} 发生额汇总凭证",
        ))
        db.commit()
        total_created += 1
        print(f"  ✓ {month_label}: voucher_no={voucher.voucher_no}, entries={len(entries)}, dr={total_dr}, cr={total_cr}")

    print(f"  期间凭证: 创建 {total_created}/4 个月")


def import_common_summaries(db, company_id):
    """导入常用摘要。"""
    df = read_sheet("常用摘要.xlsx", "常用摘要", header_row=1)
    if df is None:
        return
    created = 0
    for _, row in df.iterrows():
        code = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
        summary = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
        if not summary or summary == "nan":
            continue
        existing = db.query(VoucherTemplate).filter(
            VoucherTemplate.company_id == company_id,
            VoucherTemplate.name == summary,
        ).first()
        if existing:
            continue
        db.add(VoucherTemplate(
            company_id=company_id, name=summary,
            type="user_defined", entries=[],
        ))
        created += 1
    db.commit()
    print(f"  常用摘要: 导入 {created}")


def _import_simple(db, company_id, model, filename, sheet, code_cols, name_col, extra_fields=None, header_row=1):
    """通用导入：简单 code+name 型档案。返回导入条数。"""
    fp = DATA / filename
    if not fp.exists():
        return 0
    try:
        df = pd.read_excel(fp, sheet_name=sheet, header=header_row)
    except Exception:
        # Try header=0 if header=1 fails (empty files)
        try:
            df = pd.read_excel(fp, sheet_name=sheet, header=0)
        except Exception:
            return 0
    if df is None or len(df) == 0:
        return 0
    created = 0
    for _, row in df.iterrows():
        code = str(row.iloc[code_cols[0]]).strip() if pd.notna(row.iloc[code_cols[0]]) else ""
        name = str(row.iloc[name_col]).strip() if pd.notna(row.iloc[name_col]) else ""
        if (not code or code == "nan") and (not name or name == "nan"):
            continue
        if not code or code == "nan":
            code = name
        if db.query(model).filter(model.company_id == company_id, model.code == code).first():
            continue
        kwargs = {"company_id": company_id, "code": code, "name": name}
        if extra_fields:
            for col_idx, attr in extra_fields:
                val = row.iloc[col_idx] if pd.notna(row.iloc[col_idx]) else None
                if val is not None and str(val) != "nan":
                    kwargs[attr] = str(val).strip() if isinstance(val, str) else float(val)
        db.add(model(**kwargs))
        created += 1
    db.commit()
    return created


def import_all_master_data(db, company_id):
    """导入所有基础档案。"""
    results = {}

    # 1. Regions
    results['地区'] = _import_simple(db, company_id, Region, "地区.xlsx", "地区", [0], 1,
                                      [(2, 'parent_code')])

    # 2. Warehouses
    results['仓库'] = _import_simple(db, company_id, Warehouse, "仓库.xlsx", "仓库", [0], 1,
                                      [(3, 'manager_code'), (4, 'manager_name'), (5, 'address')])

    # 3. Units of Measure
    df = read_sheet("计量单位.xlsx", "计量单位组", header_row=0)
    unit_count = 0
    if df is not None:
        df = df.iloc[1:]
        for _, row in df.iterrows():
            group = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
            if not group or group == "nan":
                continue
            df2 = read_sheet("计量单位.xlsx", "计量单位列表", header_row=0)
            if df2 is not None:
                df2 = df2.iloc[1:]
                for _, r2 in df2.iterrows():
                    g = str(r2.iloc[0]).strip() if pd.notna(r2.iloc[0]) else ""
                    if g != group:
                        continue
                    uname = str(r2.iloc[1]).strip() if pd.notna(r2.iloc[1]) else ""
                    if not uname or uname == "nan":
                        continue
                    is_pri = str(r2.iloc[2]).strip() if pd.notna(r2.iloc[2]) else ""
                    ct = str(r2.iloc[3]).strip() if pd.notna(r2.iloc[3]) else None
                    cr = float(r2.iloc[4]) if pd.notna(r2.iloc[4]) else None
                    existing = db.query(UnitOfMeasure).filter(
                        UnitOfMeasure.company_id == company_id,
                        UnitOfMeasure.group_name == group,
                        UnitOfMeasure.unit_name == uname,
                    ).first()
                    if not existing:
                        db.add(UnitOfMeasure(company_id=company_id, group_name=group,
                                             unit_name=uname, is_primary=(is_pri == "TRUE"),
                                             conversion_type=ct, conversion_rate=cr))
                        unit_count += 1
        db.commit()
    results['计量单位'] = unit_count

    # 4. Settlement Methods
    results['结算方式'] = _import_simple(db, company_id, SettlementMethod, "结算方式.xlsx", "结算方式", [0], 1,
                                          [(2, 'default_account')])

    # 5. Bank Accounts
    df = read_sheet("账号.xlsx", "账号", header_row=0)
    bank_count = 0
    if df is not None:
        df = df.iloc[1:]
        for _, row in df.iterrows():
            code = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
            name = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
            if (not code or code == "nan") and (not name or name == "nan"):
                continue
            if not code or code == "nan":
                code = name
            if db.query(BankAccount).filter(BankAccount.company_id == company_id, BankAccount.code == code).first():
                continue
            acct_type = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else "bank"
            db.add(BankAccount(company_id=company_id, code=code, name=name, account_type=acct_type,
                               bank_name=str(row.iloc[3] or "").strip() if pd.notna(row.iloc[3]) else None,
                               account_number=str(row.iloc[4] or "").strip() if pd.notna(row.iloc[4]) else None))
            bank_count += 1
        db.commit()
    results['账号'] = bank_count

    # 6. Inventory Categories
    results['存货分类'] = _import_simple(db, company_id, InventoryCategory, "存货分类.xlsx", "存货分类", [0], 1,
                                          [(2, 'parent_code')])

    # 7. Inventory
    df = read_sheet("存货.xlsx", "存货", header_row=0)
    inv_count = 0
    if df is not None:
        df = df.iloc[1:]
        for _, row in df.iterrows():
            code = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
            name = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
            if (not code or code == "nan") and (not name or name == "nan"):
                continue
            if not code or code == "nan":
                code = name
            if db.query(Inventory).filter(Inventory.company_id == company_id, Inventory.code == code).first():
                continue
            db.add(Inventory(company_id=company_id, code=code, name=name,
                             category_code=str(row.iloc[2] or "").strip() if pd.notna(row.iloc[2]) else None,
                             specs=str(row.iloc[3] or "").strip() if pd.notna(row.iloc[3]) else None,
                             unit=str(row.iloc[4] or "").strip() if pd.notna(row.iloc[4]) else None))
            inv_count += 1
        db.commit()
    results['存货'] = inv_count

    # 8. Expense Items
    results['费用'] = _import_simple(db, company_id, ExpenseItem, "费用.xlsx", "费用", [0], 1,
                                      [(2, 'parent_code'), (4, 'tax_rate')])

    # 9. Revenue Items
    results['收入'] = _import_simple(db, company_id, RevenueItem, "收入.xlsx", "收入", [0], 1,
                                      [(2, 'parent_code'), (4, 'tax_rate')])

    # 10. Cash Flow Categories
    results['现金流量分类'] = _import_simple(db, company_id, CashFlowCategory, "现金流量项目分类.xlsx", "现金流量项目分类", [0], 1,
                                               [(2, 'parent_code')])

    # 11. Cash Flow Items
    df = read_sheet("现金流量项目.xlsx", "现金流量项目", header_row=1)
    cf_count = 0
    if df is not None:
        for _, row in df.iterrows():
            code = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
            name = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
            if not name or name == "nan":
                continue
            if not code or code == "nan":
                code = name
            if db.query(CashFlowItem).filter(CashFlowItem.company_id == company_id, CashFlowItem.code == code).first():
                continue
            db.add(CashFlowItem(company_id=company_id, code=code, name=name,
                                category_code=str(row.iloc[2] or "").strip() if pd.notna(row.iloc[2]) else None,
                                direction=str(row.iloc[4] or "").strip() if pd.notna(row.iloc[4]) else None,
                                debit_accounts=str(row.iloc[5] or "").strip() if pd.notna(row.iloc[5]) else None,
                                credit_accounts=str(row.iloc[6] or "").strip() if pd.notna(row.iloc[6]) else None))
            cf_count += 1
        db.commit()
    results['现金流量项目'] = cf_count

    # Print summary
    for k, v in results.items():
        print(f"  {k}: 导入 {v}")


def main():
    db = SessionLocal()
    company = db.query(Company).filter(Company.id == 1).first()
    if not company:
        print("错误: 公司 ID=1 不存在，请先创建公司")
        db.close()
        return

    cid = company.id
    print(f"开始原系统数据导入 → {company.name} (ID={cid})")
    print()

    import_accounts(db, cid)
    set_opening_balances(db, cid)
    import_all_master_data(db, cid)
    import_departments(db, cid)
    import_employees(db, cid)
    import_counterparties(db, cid)
    import_common_summaries(db, cid)
    create_period_vouchers(db, cid)

    print()
    print("导入完成 ✅")

    # Summary stats
    acct_count = db.query(Account).filter(Account.company_id == cid).count()
    dept_count = db.query(Department).filter(Department.company_id == cid).count()
    cp_count = db.query(Counterparty).filter(Counterparty.company_id == cid).count()
    person_count = db.query(Person).filter(Person.company_id == cid).count()
    voucher_count = db.query(Voucher).filter(Voucher.company_id == cid).count()
    print(f"  科目: {acct_count} | 部门: {dept_count} | 往来单位: {cp_count} | 员工: {person_count} | 凭证: {voucher_count}")

    db.close()


if __name__ == "__main__":
    main()
