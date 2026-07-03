"""会计期间管理路由：结账/反结账。"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, AccountingPeriod, AuditLog, Company, Voucher, VoucherEntry, Account, CarryForwardEntry
from app.schemas import ClosePeriodRequest, PeriodResponse, CarryForwardEntryCreate, CarryForwardEntryResponse, CloseCheckResult, QuarterlyPeriodStatus, YearlyPeriodStatus
from app.auth import get_current_user
from app.permissions import check_period_close, check_period_unclose

router = APIRouter()


def _get_company(db: Session, company_id: int) -> Company:
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="公司不存在")
    return company


@router.get("/", response_model=list[PeriodResponse])
def list_periods(company_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(AccountingPeriod).filter(AccountingPeriod.company_id == company_id).order_by(AccountingPeriod.period).all()


def _prev_period(period: str) -> str:
    """返回上一会计期间，如 2026-03 → 2026-02，2026-01 → 2025-12。"""
    y, m = int(period[:4]), int(period[5:7])
    if m == 1:
        return f"{y - 1}-12"
    return f"{y}-{m - 1:02d}"


def _period_month_range(period: str) -> tuple[str, str]:
    """返回期间的起止日期，如 2026-03 → ('2026-03-01', '2026-03-31')。"""
    import calendar
    y, m = int(period[:4]), int(period[5:7])
    last_day = calendar.monthrange(y, m)[1]
    return f"{period}-01", f"{period}-{last_day:02d}"


def _auto_carry_forward(db: Session, company_id: int, period: str, user_id: int) -> dict:
    """自动执行损益结转：收入/费用科目余额 → 本年利润(4103)。
    返回 {'voucher_id': ..., 'entries': N, 'income_total': ..., 'expense_total': ...}。"""
    profit_account = db.query(Account).filter(
        Account.company_id == company_id,
        Account.code == "4103",
    ).first()
    if not profit_account:
        return {"skipped": True, "reason": "未找到本年利润科目（4103）"}

    pl_accounts = db.query(Account).filter(
        Account.company_id == company_id,
        Account.is_active == True,
        Account.category.in_(["profit_loss", "cost"]),
        Account.code != "4103",
    ).all()

    if not pl_accounts:
        return {"skipped": True, "reason": "无损益类科目"}

    start_date, end_date = _period_month_range(period)

    income_entries = []
    expense_entries = []

    for account in pl_accounts:
        agg = db.query(
            func.coalesce(func.sum(VoucherEntry.debit), 0),
            func.coalesce(func.sum(VoucherEntry.credit), 0),
        ).join(Voucher, VoucherEntry.voucher_id == Voucher.id).filter(
            VoucherEntry.account_code == account.code,
            Voucher.company_id == company_id,
            Voucher.date >= start_date,
            Voucher.date <= end_date,
            Voucher.status == "posted",
        ).first()

        total_debit = float(agg[0])
        total_credit = float(agg[1])
        # 损益结转仅计算本期发生额净值（initial_balance 已体现在
        # 科目累计余额中，不应每月重复加入）
        net = total_debit - total_credit
        if abs(net) < 0.01:
            continue

        if account.balance_direction == "credit":
            # 收入类：贷方余额 → 借方结转
            income_entries.append({"code": account.code, "name": account.name, "amount": abs(net)})
        else:
            # 费用/成本类：借方余额 → 贷方结转
            expense_entries.append({"code": account.code, "name": account.name, "amount": abs(net)})

    if not income_entries and not expense_entries:
        return {"skipped": True, "reason": "本月损益类科目无发生额，无需结转"}

    income_total = sum(e["amount"] for e in income_entries)
    expense_total = sum(e["amount"] for e in expense_entries)

    now = datetime.now(timezone.utc)
    month_str = period.replace("-", "")
    count = db.query(Voucher).filter(
        Voucher.company_id == company_id,
        Voucher.date >= start_date,
        Voucher.date <= end_date,
    ).count()

    voucher = Voucher(
        company_id=company_id,
        date=end_date,
        voucher_no=f"转字{month_str}-{count + 1:04d}",
        voucher_type="transfer",
        summary=f"{period} 月末损益结转（系统自动生成）",
        creator_id=user_id,
        status="posted",
        approved_by=user_id,
        approved_at=now,
    )
    db.add(voucher)
    db.flush()

    # 结转收入：借 收入科目，贷 本年利润
    for e in income_entries:
        db.add(VoucherEntry(
            voucher_id=voucher.id,
            account_code=e["code"],
            debit=e["amount"],
            credit=0,
            description=f"结转{e['name']}至本年利润",
        ))

    # 结转费用：借 本年利润，贷 费用科目
    for e in expense_entries:
        db.add(VoucherEntry(
            voucher_id=voucher.id,
            account_code=e["code"],
            debit=0,
            credit=e["amount"],
            description=f"结转{e['name']}至本年利润",
        ))

    # 本年利润汇总分录
    net_profit = income_total - expense_total
    if net_profit >= 0:
        # 净利润：贷方增加
        db.add(VoucherEntry(
            voucher_id=voucher.id,
            account_code="4103",
            debit=0,
            credit=abs(net_profit),
            description="本月净利润转入",
        ))
    else:
        # 净亏损：借方增加
        db.add(VoucherEntry(
            voucher_id=voucher.id,
            account_code="4103",
            debit=abs(net_profit),
            credit=0,
            description="本月净亏损转入",
        ))

    db.flush()
    return {
        "voucher_id": voucher.id,
        "voucher_no": voucher.voucher_no,
        "income_entries": len(income_entries),
        "expense_entries": len(expense_entries),
        "income_total": income_total,
        "expense_total": expense_total,
        "net_profit": net_profit,
    }


@router.post("/close")
def close_period(req: ClosePeriodRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """结账：顺序检查 → 试算验证 → 损益结转 → 锁定期间。"""
    company = _get_company(db, req.company_id)
    err = check_period_close(user, company)
    if err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=err)

    # ── 1. 顺序检查：前一月必须已关帐（1月除外）──
    if not req.period.endswith("-01"):
        prev = _prev_period(req.period)
        prev_closed = db.query(AccountingPeriod).filter(
            AccountingPeriod.company_id == req.company_id,
            AccountingPeriod.period == prev,
            AccountingPeriod.is_closed == True,
        ).first()
        if not prev_closed:
            raise HTTPException(
                status_code=400,
                detail=f"请先关闭上一会计期间（{prev}），再关闭当前期间。",
            )

    # ── 2. 结账前检查 ──
    start_date, end_date = _period_month_range(req.period)
    unposted = db.query(Voucher).filter(
        Voucher.company_id == req.company_id,
        Voucher.date >= start_date,
        Voucher.date <= end_date,
        Voucher.status == "draft",
    ).count()

    unbalanced = 0
    drafts = db.query(Voucher).filter(
        Voucher.company_id == req.company_id,
        Voucher.date >= start_date,
        Voucher.date <= end_date,
        Voucher.status == "draft",
    ).all()
    for v in drafts:
        total_debit = sum(e.debit for e in v.entries)
        total_credit = sum(e.credit for e in v.entries)
        if abs(total_debit - total_credit) > 0.01:
            unbalanced += 1

    if unposted > 0 or unbalanced > 0:
        raise HTTPException(
            status_code=400,
            detail=f"未过账凭证 {unposted} 张，试算不平衡 {unbalanced} 张。请处理后再关帐。",
        )

    # ── 3. 自动损益结转 ──
    carry_result = _auto_carry_forward(db, req.company_id, req.period, user.id)
    carry_detail = {}
    if carry_result.get("skipped"):
        carry_detail = {"carry_forward": "skipped", "reason": carry_result.get("reason")}
    else:
        carry_detail = {
            "carry_forward": "executed",
            "voucher_no": carry_result["voucher_no"],
            "income_entries": carry_result["income_entries"],
            "expense_entries": carry_result["expense_entries"],
            "net_profit": round(carry_result["net_profit"], 2),
        }

    # ── 4. 锁定期间 ──
    period = db.query(AccountingPeriod).filter(
        AccountingPeriod.company_id == req.company_id,
        AccountingPeriod.period == req.period,
    ).first()
    if not period:
        period = AccountingPeriod(company_id=req.company_id, period=req.period)
        db.add(period)
        db.flush()

    if period.is_closed:
        raise HTTPException(status_code=400, detail=f"期间 {req.period} 已关帐")

    period.is_closed = True
    period.closed_by = user.id
    period.closed_at = datetime.now(timezone.utc)
    period.closed_status = "closed"

    db.add(AuditLog(
        company_id=req.company_id, user_id=user.id,
        action="close_period", target_type="period",
        details={"period": req.period, **carry_detail},
    ))
    db.commit()
    return {"ok": True, "period": req.period, **carry_detail}


@router.post("/un-close")
def unclose_period(company_id: int, period: str, reason: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """反结账：逆序检查（必须先反结账最近月份）+ 权限验证。"""
    company = _get_company(db, company_id)
    err = check_period_unclose(user, company)
    if err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=err)

    p = db.query(AccountingPeriod).filter(
        AccountingPeriod.company_id == company_id, AccountingPeriod.period == period,
    ).first()
    if not p or not p.is_closed:
        raise HTTPException(status_code=400, detail="该期间未结账")

    # 逆序检查：不能反结账旧月份，如果后面月份已关帐
    later_periods = db.query(AccountingPeriod).filter(
        AccountingPeriod.company_id == company_id,
        AccountingPeriod.period > period,
        AccountingPeriod.is_closed == True,
    ).all()
    if later_periods:
        later_list = ", ".join(p.period for p in later_periods)
        raise HTTPException(
            status_code=400,
            detail=f"请先反结账后续期间（{later_list}），再反结账当前期间。",
        )

    p.is_closed = False
    p.closed_by = None
    p.closed_at = None
    p.closed_status = "open"

    # 删除关帐时自动生成的损益结转凭证（摘要含"损益结转（系统自动生成）"）
    start_date, end_date = _period_month_range(period)
    carry_vouchers = db.query(Voucher).filter(
        Voucher.company_id == company_id,
        Voucher.date >= start_date,
        Voucher.date <= end_date,
        Voucher.summary.contains("损益结转（系统自动生成）"),
    ).all()
    carry_detail = []
    for v in carry_vouchers:
        carry_detail.append(v.voucher_no)
        db.query(VoucherEntry).filter(VoucherEntry.voucher_id == v.id).delete()
        db.delete(v)

    db.add(AuditLog(
        company_id=company_id, user_id=user.id,
        action="reverse_close", target_type="period", reason=reason,
        details={"period": period, "reversed_carry_vouchers": carry_detail},
    ))
    db.commit()
    return {"ok": True, "reversed_carry_vouchers": carry_detail}


@router.get("/close-checks", response_model=CloseCheckResult)
def get_close_checks(
    company_id: int,
    period: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """结账前检查：未过账凭证、试算平衡。"""
    unposted = db.query(Voucher).filter(
        Voucher.company_id == company_id,
        Voucher.date.like(f"{period}%"),
        Voucher.status == "draft",
    ).count()

    # Check unbalanced vouchers for the period
    unbalanced = 0
    drafts = db.query(Voucher).filter(
        Voucher.company_id == company_id,
        Voucher.date.like(f"{period}%"),
        Voucher.status == "draft",
    ).all()
    for v in drafts:
        total_debit = sum(e.debit for e in v.entries)
        total_credit = sum(e.credit for e in v.entries)
        if abs(total_debit - total_credit) > 0.01:
            unbalanced += 1

    can_close = unposted == 0 and unbalanced == 0
    message = "可以关账" if can_close else f"未过账凭证 {unposted} 张，试算不平衡 {unbalanced} 张"

    return CloseCheckResult(
        period=period,
        unposted_vouchers=unposted,
        unbalanced_vouchers=unbalanced,
        can_close=can_close,
        message=message,
    )


@router.get("/quarterly-summary", response_model=list[QuarterlyPeriodStatus])
def get_quarterly_summary(
    company_id: int,
    year: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """季度关账汇总。"""
    quarters = [
        ("Q1", [f"{year}-01", f"{year}-02", f"{year}-03"]),
        ("Q2", [f"{year}-04", f"{year}-05", f"{year}-06"]),
        ("Q3", [f"{year}-07", f"{year}-08", f"{year}-09"]),
        ("Q4", [f"{year}-10", f"{year}-11", f"{year}-12"]),
    ]

    closed_periods = {
        p.period
        for p in db.query(AccountingPeriod).filter(
            AccountingPeriod.company_id == company_id,
            AccountingPeriod.period.like(f"{year}-%"),
            AccountingPeriod.is_closed == True,
        ).all()
    }

    result = []
    for q_name, months in quarters:
        closed = sum(1 for m in months if m in closed_periods)
        result.append(QuarterlyPeriodStatus(
            quarter=q_name,
            months=months,
            closed_months=closed,
            total_months=3,
            is_quarter_closed=closed == 3,
        ))
    return result


@router.get("/yearly-summary", response_model=YearlyPeriodStatus)
def get_yearly_summary(
    company_id: int,
    year: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """年度关账汇总。"""
    closed_periods = {
        p.period: p.is_closed
        for p in db.query(AccountingPeriod).filter(
            AccountingPeriod.company_id == company_id,
            AccountingPeriod.period.like(f"{year}-%"),
        ).all()
    }

    months = []
    for m in range(1, 13):
        period_key = f"{year}-{m:02d}"
        months.append({
            "period": period_key,
            "is_closed": closed_periods.get(period_key, False),
        })

    closed_count = sum(1 for m in months if m["is_closed"])

    return YearlyPeriodStatus(
        year=year,
        months=months,
        closed_months=closed_count,
        total_months=12,
        is_year_closed=closed_count == 12,
    )


# ── Carry-Forward CRUD ──

@router.get("/carry-forwards", response_model=list[CarryForwardEntryResponse])
def list_carry_forwards(
    company_id: int,
    period: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(CarryForwardEntry).filter(CarryForwardEntry.company_id == company_id)
    if period:
        q = q.filter(CarryForwardEntry.period == period)
    return q.order_by(CarryForwardEntry.period.desc(), CarryForwardEntry.entry_type).all()


@router.post("/carry-forward", response_model=CarryForwardEntryResponse)
def create_carry_forward(
    data: CarryForwardEntryCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    obj = CarryForwardEntry(
        company_id=data.company_id,
        period=data.period,
        entry_type=data.entry_type,
        debit_account_id=data.debit_account_id,
        credit_account_id=data.credit_account_id,
        amount=data.amount,
        status="draft",
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.post("/carry-forward/{entry_id}/execute", response_model=CarryForwardEntryResponse)
def execute_carry_forward(
    entry_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    obj = db.query(CarryForwardEntry).filter(CarryForwardEntry.id == entry_id).first()
    if not obj:
        raise HTTPException(404, "结转记录未找到")
    if obj.status == "executed":
        raise HTTPException(400, "该结转已执行")

    company_id = obj.company_id
    period = obj.period  # yyyy-MM

    # 1. 找到本年利润科目 (4103)
    profit_account = db.query(Account).filter(
        Account.company_id == company_id,
        Account.code == "4103",
    ).first()
    if not profit_account:
        raise HTTPException(400, "未找到本年利润科目（4103），请先创建")

    # 2. 查询所有损益类和成本类科目（排除本年利润本身）
    pl_accounts = db.query(Account).filter(
        Account.company_id == company_id,
        Account.is_active == True,
        Account.category.in_(["profit_loss", "cost"]),
        Account.code != "4103",
    ).all()

    if not pl_accounts:
        raise HTTPException(400, "未找到损益类科目")

    # 3. 计算每个科目的当前余额
    # 需要排除已结转凭证的影响 — 使用 VoucherEntry 聚合
    income_entries = []   # 收入类: 贷方余额 → 借方结转
    expense_entries = []  # 费用/成本类: 借方余额 → 贷方结转

    for account in pl_accounts:
        # 聚合该科目在本期间内的发生额
        agg = db.query(
            func.coalesce(func.sum(VoucherEntry.debit), 0),
            func.coalesce(func.sum(VoucherEntry.credit), 0),
        ).join(Voucher, VoucherEntry.voucher_id == Voucher.id).filter(
            VoucherEntry.account_code == account.code,
            Voucher.company_id == company_id,
            Voucher.date >= f"{period}-01",
            Voucher.date <= f"{period}-{_last_day_of_month(period)}",
            Voucher.status.in_(["posted"]),  # 仅已记账凭证
        ).first()

        total_debit = float(agg[0]) + (account.initial_balance if account.balance_direction == "debit" else 0)
        total_credit = float(agg[1]) + (account.initial_balance if account.balance_direction == "credit" else 0)

        net_balance = total_debit - total_credit

        if abs(net_balance) < 0.01:
            continue

        if account.balance_direction == "credit":
            # 收入类科目：贷方余额 → 借方结转 (借：收入，贷：本年利润)
            income_entries.append({
                "account_code": account.code,
                "account_name": account.name,
                "debit": abs(net_balance),
                "credit": 0,
            })
        else:
            # 成本费用类：借方余额 → 贷方结转 (借：本年利润，贷：费用)
            expense_entries.append({
                "account_code": account.code,
                "account_name": account.name,
                "debit": 0,
                "credit": abs(net_balance),
            })

    if not income_entries and not expense_entries:
        raise HTTPException(400, "该期间无损益类发生额需要结转")

    # 4. 生成结转凭证
    income_total = sum(e["debit"] for e in income_entries)
    expense_total = sum(e["credit"] for e in expense_entries)

    now = datetime.now(timezone.utc)
    voucher_no = f"转字{period.replace('-', '')}-{db.query(Voucher).filter(Voucher.company_id == company_id, Voucher.date.startswith(period)).count() + 1:04d}"

    voucher = Voucher(
        company_id=company_id,
        date=f"{period}-{_last_day_of_month(period)}",
        voucher_no=voucher_no,
        voucher_type="transfer",
        summary=f"{period} 月末损益结转",
        creator_id=user.id,
        status="approved",
        approved_by=user.id,
        approved_at=now,
    )
    db.add(voucher)
    db.flush()

    # 结转收入：借 收入科目，贷 本年利润
    for e in income_entries:
        db.add(VoucherEntry(
            voucher_id=voucher.id,
            account_code=e["account_code"],
            debit=e["debit"],
            credit=0,
            description=f"结转{e['account_name']}至本年利润",
        ))

    if income_total > 0:
        db.add(VoucherEntry(
            voucher_id=voucher.id,
            account_code="4103",
            debit=0,
            credit=income_total,
            description="收入结转",
        ))

    # 结转费用：借 本年利润，贷 费用科目
    if expense_total > 0:
        db.add(VoucherEntry(
            voucher_id=voucher.id,
            account_code="4103",
            debit=expense_total,
            credit=0,
            description="费用结转",
        ))

    for e in expense_entries:
        db.add(VoucherEntry(
            voucher_id=voucher.id,
            account_code=e["account_code"],
            debit=0,
            credit=e["credit"],
            description=f"结转{e['account_name']}至本年利润",
        ))

    # 5. 更新结转记录
    obj.status = "executed"
    obj.executed_at = now
    obj.voucher_id = voucher.id

    # 审计日志
    db.add(AuditLog(
        company_id=company_id,
        user_id=user.id,
        action="execute_carry_forward",
        target_type="carry_forward_entry",
        target_id=obj.id,
        reason=f"生成结转凭证 {voucher_no}",
    ))

    db.commit()
    db.refresh(obj)
    return obj


def _last_day_of_month(period: str) -> str:
    """返回 yyyy-MM-dd 格式的月末日期"""
    import calendar
    y, m = period.split("-")
    return f"{y}-{m}-{calendar.monthrange(int(y), int(m))[1]:02d}"


@router.delete("/carry-forwards/{entry_id}")
def delete_carry_forward(
    entry_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    obj = db.query(CarryForwardEntry).filter(CarryForwardEntry.id == entry_id).first()
    if not obj:
        raise HTTPException(404, "结转记录未找到")
    if obj.status == "executed":
        raise HTTPException(400, "已执行的结转不可删除")
    db.delete(obj)
    db.commit()
    return {"detail": "已删除"}
