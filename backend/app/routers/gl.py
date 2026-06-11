"""总账模块路由：自动转账、科目账、辅助账、自定义账、自定义明细表、往来管理。"""
from datetime import datetime, timezone, date
from io import StringIO
import csv

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    User, Company, Account, Voucher, VoucherEntry,
    AccountingPeriod, Counterparty, Department, Person, Project,
    AutoTransferTemplate, CustomQuery,
)
from app.schemas import (
    AutoTransferTemplateCreate, AutoTransferTemplateUpdate,
    AutoTransferTemplateResponse,
    SubjectLedgerResponse, SubjectLedgerEntry,
    AuxLedgerResponse, AuxLedgerEntry,
    CustomQueryCreate, CustomQueryUpdate, CustomQueryResponse,
    CustomDetailColumn, CustomDetailQueryRequest,
    TransactionBalanceRow, TransactionDetailResponse,
    TransactionDetailEntry, AgingRow, AgingBucket,
)
from app.auth import get_current_user

router = APIRouter()


def _get_company(db: Session, company_id: int) -> Company:
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="公司不存在")
    return company


# ── 自动转账模板 ──

@router.get("/auto-transfer-templates", response_model=list[AutoTransferTemplateResponse])
def list_auto_transfer_templates(
    company_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return (
        db.query(AutoTransferTemplate)
        .filter(AutoTransferTemplate.company_id == company_id)
        .order_by(AutoTransferTemplate.created_at.desc())
        .all()
    )


@router.post("/auto-transfer-templates", response_model=AutoTransferTemplateResponse)
def create_auto_transfer_template(
    data: AutoTransferTemplateCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    obj = AutoTransferTemplate(
        company_id=data.company_id,
        name=data.name,
        description=data.description,
        template_type=data.template_type,
        frequency=data.frequency,
        is_active=data.is_active,
        entries=[e.model_dump() for e in data.entries],
        created_by=user.id,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.put("/auto-transfer-templates/{template_id}", response_model=AutoTransferTemplateResponse)
def update_auto_transfer_template(
    template_id: int,
    data: AutoTransferTemplateUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    obj = db.query(AutoTransferTemplate).filter(AutoTransferTemplate.id == template_id).first()
    if not obj:
        raise HTTPException(404, "模板不存在")
    if data.name is not None:
        obj.name = data.name
    if data.description is not None:
        obj.description = data.description
    if data.template_type is not None:
        obj.template_type = data.template_type
    if data.frequency is not None:
        obj.frequency = data.frequency
    if data.is_active is not None:
        obj.is_active = data.is_active
    if data.entries is not None:
        obj.entries = [e.model_dump() for e in data.entries]
    obj.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/auto-transfer-templates/{template_id}")
def delete_auto_transfer_template(
    template_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    obj = db.query(AutoTransferTemplate).filter(AutoTransferTemplate.id == template_id).first()
    if not obj:
        raise HTTPException(404, "模板不存在")
    db.delete(obj)
    db.commit()
    return {"detail": "已删除"}


@router.post("/auto-transfer-templates/{template_id}/execute")
def execute_auto_transfer(
    template_id: int,
    company_id: int,
    period: str = Query(..., description="执行期间 yyyy-MM"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """执行自动转账，生成凭证。"""
    template = db.query(AutoTransferTemplate).filter(
        AutoTransferTemplate.id == template_id,
        AutoTransferTemplate.company_id == company_id,
    ).first()
    if not template:
        raise HTTPException(404, "模板不存在")
    if not template.is_active:
        raise HTTPException(400, "模板已停用")
    if not template.entries:
        raise HTTPException(400, "模板没有分录定义")

    account_codes_needed = [e["account_code"] for e in template.entries]
    accounts_map = {
        a.code: a
        for a in db.query(Account).filter(
            Account.company_id == company_id,
            Account.code.in_(account_codes_needed),
        ).all()
    }

    voucher_entries = []
    for entry_def in template.entries:
        code = entry_def["account_code"]
        direction = entry_def["direction"]
        formula = entry_def["formula"]
        summary = entry_def.get("summary", "")

        if template.template_type == "fixed":
            amount = float(formula)
        elif template.template_type == "ratio":
            account = accounts_map.get(code)
            if not account:
                raise HTTPException(400, f"科目 {code} 不存在")
            balance = _get_account_balance(db, company_id, code, period)
            pct = float(formula.rstrip("%")) / 100.0
            amount = round(balance * pct, 2)
        elif template.template_type == "balance":
            account = accounts_map.get(code)
            if not account:
                raise HTTPException(400, f"科目 {code} 不存在")
            amount = _get_account_balance(db, company_id, code, period)
        else:
            raise HTTPException(400, f"不支持的模板类型: {template.template_type}")

        if amount == 0:
            continue

        if direction == "debit":
            voucher_entries.append({"account_code": code, "debit": amount, "credit": 0, "description": summary})
        else:
            voucher_entries.append({"account_code": code, "debit": 0, "credit": amount, "description": summary})

    if not voucher_entries:
        raise HTTPException(400, "所有分录金额为零，无法生成凭证")

    voucher_no = f"转-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    voucher = Voucher(
        company_id=company_id,
        date=f"{period}-01",
        voucher_no=voucher_no,
        voucher_type="transfer",
        summary=template.name,
        creator_id=user.id,
        status="draft",
    )
    db.add(voucher)
    db.flush()

    total_debit = sum(e["debit"] for e in voucher_entries)
    total_credit = sum(e["credit"] for e in voucher_entries)
    if total_debit != total_credit:
        diff = round(total_debit - total_credit, 2)
        if voucher_entries[-1]["debit"] > 0:
            voucher_entries[-1]["debit"] = round(voucher_entries[-1]["debit"] - diff, 2)
        else:
            voucher_entries[-1]["credit"] = round(voucher_entries[-1]["credit"] + diff, 2)

    for entry_data in voucher_entries:
        db.add(VoucherEntry(
            voucher_id=voucher.id,
            account_code=entry_data["account_code"],
            debit=entry_data["debit"],
            credit=entry_data["credit"],
            description=entry_data.get("description", ""),
        ))

    db.commit()
    db.refresh(voucher)
    return {"ok": True, "voucher_id": voucher.id, "voucher_no": voucher_no}


def _get_account_balance(db: Session, company_id: int, account_code: str, period: str) -> float:
    """Get current balance for an account up to given period."""
    entries = (
        db.query(VoucherEntry)
        .join(Voucher, VoucherEntry.voucher_id == Voucher.id)
        .filter(
            Voucher.company_id == company_id,
            VoucherEntry.account_code == account_code,
            Voucher.date <= f"{period}-31",
            Voucher.status.in_(["posted", "closed"]),
        )
        .all()
    )
    total_debit = sum(e.debit for e in entries)
    total_credit = sum(e.credit for e in entries)
    account = db.query(Account).filter(
        Account.company_id == company_id, Account.code == account_code
    ).first()
    if account and account.balance_direction == "debit":
        return account.initial_balance + total_debit - total_credit
    return total_debit - total_credit


# ── 科目账 ──

@router.get("/subject-ledger", response_model=list[SubjectLedgerResponse])
def get_subject_ledger(
    company_id: int,
    start_period: str = Query(..., description="起始期间 yyyy-MM"),
    end_period: str = Query(..., description="截止期间 yyyy-MM"),
    account_code: str = Query(None, description="科目代码，支持模糊"),
    level: int = Query(None, description="科目级别过滤"),
    include_zero: bool = Query(False, description="包含无发生额科目"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(Account).filter(Account.company_id == company_id, Account.is_active == True)
    if account_code:
        query = query.filter(Account.code.like(f"{account_code}%"))
    if level:
        query = query.filter(Account.level == level)

    accounts = query.order_by(Account.code).all()
    result = []
    for account in accounts:
        ledger = _build_ledger_for_account(db, company_id, account, start_period, end_period)
        if not include_zero and ledger.total_debit == 0 and ledger.total_credit == 0:
            continue
        result.append(ledger)
    return result


@router.get("/subject-ledger/{code}", response_model=SubjectLedgerResponse)
def get_single_subject_ledger(
    code: str,
    company_id: int,
    start_period: str = Query(...),
    end_period: str = Query(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    account = db.query(Account).filter(
        Account.company_id == company_id, Account.code == code
    ).first()
    if not account:
        raise HTTPException(404, "科目不存在")
    return _build_ledger_for_account(db, company_id, account, start_period, end_period)


def _build_ledger_for_account(
    db: Session, company_id: int, account: Account,
    start_period: str, end_period: str,
) -> SubjectLedgerResponse:
    beg_entries = (
        db.query(VoucherEntry)
        .join(Voucher, VoucherEntry.voucher_id == Voucher.id)
        .filter(
            Voucher.company_id == company_id,
            VoucherEntry.account_code == account.code,
            Voucher.date < f"{start_period}-01",
            Voucher.status.in_(["posted", "closed"]),
        )
        .all()
    )
    beg_debit = sum(e.debit for e in beg_entries)
    beg_credit = sum(e.credit for e in beg_entries)
    if account.balance_direction == "debit":
        beginning_balance = account.initial_balance + beg_debit - beg_credit
    else:
        beginning_balance = account.initial_balance + beg_credit - beg_debit

    period_entries = (
        db.query(VoucherEntry)
        .join(Voucher, VoucherEntry.voucher_id == Voucher.id)
        .filter(
            Voucher.company_id == company_id,
            VoucherEntry.account_code == account.code,
            Voucher.date >= f"{start_period}-01",
            Voucher.date <= f"{end_period}-31",
            Voucher.status.in_(["posted", "closed"]),
        )
        .order_by(Voucher.date, Voucher.voucher_no)
        .all()
    )

    running_balance = beginning_balance
    entries = []
    for e in period_entries:
        if account.balance_direction == "debit":
            running_balance = running_balance + e.debit - e.credit
        else:
            running_balance = running_balance + e.credit - e.debit
        entries.append(SubjectLedgerEntry(
            date=e.voucher.date,
            voucher_no=e.voucher.voucher_no,
            summary=e.voucher.summary,
            debit=e.debit,
            credit=e.credit,
            balance=round(running_balance, 2),
        ))

    total_debit = sum(e.debit for e in period_entries)
    total_credit = sum(e.credit for e in period_entries)
    if account.balance_direction == "debit":
        ending_balance = beginning_balance + total_debit - total_credit
    else:
        ending_balance = beginning_balance + total_credit - total_debit

    return SubjectLedgerResponse(
        account_code=account.code,
        account_name=account.name,
        beginning_balance=round(beginning_balance, 2),
        direction=account.balance_direction,
        entries=entries,
        total_debit=round(total_debit, 2),
        total_credit=round(total_credit, 2),
        ending_balance=round(ending_balance, 2),
    )


# ── 辅助账 ──

@router.get("/aux-ledger", response_model=AuxLedgerResponse)
def get_aux_ledger(
    company_id: int,
    aux_type: str = Query(..., description="department/person/counterparty/project"),
    aux_id: int = Query(...),
    start_period: str = Query(...),
    end_period: str = Query(...),
    account_code: str = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if aux_type not in ("department", "person", "counterparty", "project"):
        raise HTTPException(400, "aux_type 必须是 department/person/counterparty/project")

    aux_name = ""
    if aux_type == "department":
        obj = db.query(Department).filter(Department.id == aux_id).first()
    elif aux_type == "person":
        obj = db.query(Person).filter(Person.id == aux_id).first()
    elif aux_type == "counterparty":
        obj = db.query(Counterparty).filter(Counterparty.id == aux_id).first()
    elif aux_type == "project":
        obj = db.query(Project).filter(Project.id == aux_id).first()
    aux_name = obj.name if obj else "未知"

    filter_col = {
        "department": VoucherEntry.department_id,
        "person": VoucherEntry.person_id,
        "counterparty": VoucherEntry.counterparty_id,
        "project": VoucherEntry.project_id,
    }[aux_type]

    beg_query = (
        db.query(VoucherEntry)
        .join(Voucher, VoucherEntry.voucher_id == Voucher.id)
        .filter(
            Voucher.company_id == company_id,
            filter_col == aux_id,
            Voucher.date < f"{start_period}-01",
            Voucher.status.in_(["posted", "closed"]),
        )
    )
    if account_code:
        beg_query = beg_query.filter(VoucherEntry.account_code.like(f"{account_code}%"))
    beg_entries = beg_query.all()
    beg_debit = sum(e.debit for e in beg_entries)
    beg_credit = sum(e.credit for e in beg_entries)
    beginning_balance = beg_debit - beg_credit

    cur_query = (
        db.query(VoucherEntry)
        .join(Voucher, VoucherEntry.voucher_id == Voucher.id)
        .filter(
            Voucher.company_id == company_id,
            filter_col == aux_id,
            Voucher.date >= f"{start_period}-01",
            Voucher.date <= f"{end_period}-31",
            Voucher.status.in_(["posted", "closed"]),
        )
    )
    if account_code:
        cur_query = cur_query.filter(VoucherEntry.account_code.like(f"{account_code}%"))
    cur_entries = cur_query.order_by(Voucher.date, Voucher.voucher_no).all()

    account_codes = list(set(e.account_code for e in cur_entries))
    account_map = {
        a.code: a.name
        for a in db.query(Account).filter(
            Account.company_id == company_id, Account.code.in_(account_codes),
        ).all()
    }

    running_balance = beginning_balance
    entries = []
    for e in cur_entries:
        running_balance = running_balance + e.debit - e.credit
        entries.append(AuxLedgerEntry(
            date=e.voucher.date,
            voucher_no=e.voucher.voucher_no,
            account_code=e.account_code,
            account_name=account_map.get(e.account_code, ""),
            summary=e.voucher.summary,
            aux_name=aux_name,
            debit=e.debit,
            credit=e.credit,
            balance=round(running_balance, 2),
        ))

    total_debit = sum(e.debit for e in cur_entries)
    total_credit = sum(e.credit for e in cur_entries)
    ending_balance = beginning_balance + total_debit - total_credit

    return AuxLedgerResponse(
        aux_type=aux_type, aux_id=aux_id, aux_name=aux_name,
        beginning_balance=round(beginning_balance, 2), direction="debit",
        entries=entries, total_debit=round(total_debit, 2),
        total_credit=round(total_credit, 2), ending_balance=round(ending_balance, 2),
    )


# ── 自定义查询 ──

@router.get("/custom-queries", response_model=list[CustomQueryResponse])
def list_custom_queries(
    company_id: int,
    query_type: str = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(CustomQuery).filter(CustomQuery.company_id == company_id)
    if query_type:
        q = q.filter(CustomQuery.query_type == query_type)
    return q.order_by(CustomQuery.updated_at.desc()).all()


@router.post("/custom-queries", response_model=CustomQueryResponse)
def create_custom_query(
    data: CustomQueryCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    obj = CustomQuery(
        company_id=data.company_id, name=data.name,
        query_type=data.query_type, filters=data.filters, created_by=user.id,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.put("/custom-queries/{query_id}", response_model=CustomQueryResponse)
def update_custom_query(
    query_id: int, data: CustomQueryUpdate,
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    obj = db.query(CustomQuery).filter(CustomQuery.id == query_id).first()
    if not obj:
        raise HTTPException(404, "查询不存在")
    if data.name is not None:
        obj.name = data.name
    if data.filters is not None:
        obj.filters = data.filters
    obj.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/custom-queries/{query_id}")
def delete_custom_query(
    query_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    obj = db.query(CustomQuery).filter(CustomQuery.id == query_id).first()
    if not obj:
        raise HTTPException(404, "查询不存在")
    db.delete(obj)
    db.commit()
    return {"detail": "已删除"}


@router.get("/custom-queries/{query_id}/execute")
def execute_custom_query(
    query_id: int, company_id: int,
    start_period: str = Query(...), end_period: str = Query(...),
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    obj = db.query(CustomQuery).filter(CustomQuery.id == query_id).first()
    if not obj:
        raise HTTPException(404, "查询不存在")
    filters = obj.filters
    filters.setdefault("start_period", start_period)
    filters.setdefault("end_period", end_period)
    if obj.query_type == "subject":
        return _execute_saved_subject(db, company_id, filters)
    elif obj.query_type == "aux":
        return _execute_saved_aux(db, company_id, filters)
    elif obj.query_type == "detail":
        return _execute_custom_detail(db, company_id, filters)
    else:
        raise HTTPException(400, f"不支持的查询类型: {obj.query_type}")


def _execute_saved_subject(db, company_id, filters):
    account_code = filters.get("account_code")
    level = filters.get("level")
    start_period = filters.get("start_period", "2024-01")
    end_period = filters.get("end_period", "2026-12")
    include_zero = filters.get("include_zero", False)
    query = db.query(Account).filter(Account.company_id == company_id, Account.is_active == True)
    if account_code:
        query = query.filter(Account.code.like(f"{account_code}%"))
    if level:
        query = query.filter(Account.level == level)
    accounts = query.order_by(Account.code).all()
    result = []
    for account in accounts:
        ledger = _build_ledger_for_account(db, company_id, account, start_period, end_period)
        if not include_zero and ledger.total_debit == 0 and ledger.total_credit == 0:
            continue
        result.append(ledger.model_dump())
    return result


def _execute_saved_aux(db, company_id, filters):
    aux_type = filters["aux_type"]
    aux_id = filters["aux_id"]
    start_period = filters.get("start_period", "2024-01")
    end_period = filters.get("end_period", "2026-12")
    account_code = filters.get("account_code")
    filter_col = {
        "department": VoucherEntry.department_id,
        "person": VoucherEntry.person_id,
        "counterparty": VoucherEntry.counterparty_id,
        "project": VoucherEntry.project_id,
    }[aux_type]
    cur_query = (
        db.query(VoucherEntry)
        .join(Voucher, VoucherEntry.voucher_id == Voucher.id)
        .filter(
            Voucher.company_id == company_id, filter_col == aux_id,
            Voucher.date >= f"{start_period}-01", Voucher.date <= f"{end_period}-31",
            Voucher.status.in_(["posted", "closed"]),
        )
    )
    if account_code:
        cur_query = cur_query.filter(VoucherEntry.account_code.like(f"{account_code}%"))
    entries = cur_query.order_by(Voucher.date, Voucher.voucher_no).all()
    return [{"date": e.voucher.date, "voucher_no": e.voucher.voucher_no,
             "account_code": e.account_code, "debit": e.debit, "credit": e.credit,
             "summary": e.voucher.summary} for e in entries]


# ── 自定义明细表 ──

@router.get("/custom-detail/columns", response_model=list[CustomDetailColumn])
def get_custom_detail_columns(user: User = Depends(get_current_user)):
    return [
        CustomDetailColumn(field="date", header="日期"),
        CustomDetailColumn(field="voucher_no", header="凭证号"),
        CustomDetailColumn(field="voucher_type", header="凭证类型"),
        CustomDetailColumn(field="account_code", header="科目代码"),
        CustomDetailColumn(field="account_name", header="科目名称"),
        CustomDetailColumn(field="summary", header="摘要"),
        CustomDetailColumn(field="debit", header="借方金额"),
        CustomDetailColumn(field="credit", header="贷方金额"),
        CustomDetailColumn(field="department_name", header="部门"),
        CustomDetailColumn(field="person_name", header="个人"),
        CustomDetailColumn(field="counterparty_name", header="往来单位"),
        CustomDetailColumn(field="project_name", header="项目"),
    ]


@router.post("/custom-detail/query")
def query_custom_detail(
    company_id: int, data: CustomDetailQueryRequest,
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    return _execute_custom_detail(db, company_id, data.filters)


def _execute_custom_detail(db, company_id, filters):
    start_date = filters.get("start_date", "2024-01-01")
    end_date = filters.get("end_date", "2026-12-31")
    account_code = filters.get("account_code")

    entries = (
        db.query(VoucherEntry, Voucher, Account, Department, Person, Counterparty, Project)
        .join(Voucher, VoucherEntry.voucher_id == Voucher.id)
        .outerjoin(Account, (VoucherEntry.account_code == Account.code) & (Account.company_id == company_id))
        .outerjoin(Department, VoucherEntry.department_id == Department.id)
        .outerjoin(Person, VoucherEntry.person_id == Person.id)
        .outerjoin(Counterparty, VoucherEntry.counterparty_id == Counterparty.id)
        .outerjoin(Project, VoucherEntry.project_id == Project.id)
        .filter(
            Voucher.company_id == company_id,
            Voucher.date >= start_date, Voucher.date <= end_date,
            Voucher.status.in_(["posted", "closed"]),
        )
    )
    if account_code:
        entries = entries.filter(VoucherEntry.account_code.like(f"{account_code}%"))
    entries = entries.order_by(Voucher.date, Voucher.voucher_no).all()

    return [
        {
            "date": e[1].date,
            "voucher_no": e[1].voucher_no,
            "voucher_type": e[1].voucher_type,
            "account_code": e[0].account_code,
            "account_name": e[2].name if e[2] else "",
            "summary": e[1].summary,
            "debit": e[0].debit,
            "credit": e[0].credit,
            "department_name": e[3].name if e[3] else "",
            "person_name": e[4].name if e[4] else "",
            "counterparty_name": e[5].name if e[5] else "",
            "project_name": e[6].name if e[6] else "",
        }
        for e in entries
    ]


@router.get("/custom-detail/export")
def export_custom_detail(
    company_id: int,
    start_date: str = Query(default="2024-01-01"),
    end_date: str = Query(default="2026-12-31"),
    account_code: str = Query(None),
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    filters = {"start_date": start_date, "end_date": end_date, "account_code": account_code}
    rows = _execute_custom_detail(db, company_id, filters)
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["日期", "凭证号", "凭证类型", "科目代码", "科目名称", "摘要", "借方金额", "贷方金额", "部门", "个人", "往来单位", "项目"])
    for r in rows:
        writer.writerow([r["date"], r["voucher_no"], r.get("voucher_type", ""),
                         r["account_code"], r.get("account_name", ""), r["summary"],
                         r["debit"], r["credit"], r.get("department_name", ""),
                         r.get("person_name", ""), r.get("counterparty_name", ""),
                         r.get("project_name", "")])
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=custom_detail.csv"})


# ── 往来管理 ──

@router.get("/transactions/balance", response_model=list[TransactionBalanceRow])
def get_transaction_balances(
    company_id: int, start_period: str = Query(...), end_period: str = Query(...),
    account_code: str = Query(None), db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    cp_ids = [
        r[0] for r in
        db.query(VoucherEntry.counterparty_id)
        .join(Voucher, VoucherEntry.voucher_id == Voucher.id)
        .filter(Voucher.company_id == company_id, VoucherEntry.counterparty_id.isnot(None),
                Voucher.status.in_(["posted", "closed"]))
        .distinct().all()
    ]
    if not cp_ids:
        return []

    counterparties = {cp.id: cp for cp in db.query(Counterparty).filter(Counterparty.id.in_(cp_ids)).all()}
    result = []
    for cp_id in cp_ids:
        cp = counterparties.get(cp_id)
        cp_name = cp.name if cp else "未知"
        beg = (
            db.query(VoucherEntry).join(Voucher, VoucherEntry.voucher_id == Voucher.id)
            .filter(Voucher.company_id == company_id, VoucherEntry.counterparty_id == cp_id,
                    Voucher.date < f"{start_period}-01", Voucher.status.in_(["posted", "closed"]))
        )
        if account_code:
            beg = beg.filter(VoucherEntry.account_code.like(f"{account_code}%"))
        beg_entries = beg.all()
        beginning_balance = sum(e.debit for e in beg_entries) - sum(e.credit for e in beg_entries)
        cur = (
            db.query(VoucherEntry).join(Voucher, VoucherEntry.voucher_id == Voucher.id)
            .filter(Voucher.company_id == company_id, VoucherEntry.counterparty_id == cp_id,
                    Voucher.date >= f"{start_period}-01", Voucher.date <= f"{end_period}-31",
                    Voucher.status.in_(["posted", "closed"]))
        )
        if account_code:
            cur = cur.filter(VoucherEntry.account_code.like(f"{account_code}%"))
        cur_entries = cur.all()
        cur_debit = sum(e.debit for e in cur_entries)
        cur_credit = sum(e.credit for e in cur_entries)
        ending_balance = beginning_balance + cur_debit - cur_credit
        direction = "debit" if ending_balance >= 0 else "credit"
        result.append(TransactionBalanceRow(
            counterparty_id=cp_id, counterparty_name=cp_name,
            beginning_balance=round(beginning_balance, 2), direction=direction,
            current_debit=round(cur_debit, 2), current_credit=round(cur_credit, 2),
            ending_balance=round(abs(ending_balance), 2),
        ))
    return sorted(result, key=lambda r: abs(r.ending_balance), reverse=True)


@router.get("/transactions/{counterparty_id}", response_model=TransactionDetailResponse)
def get_transaction_detail(
    counterparty_id: int, company_id: int, start_period: str = Query(...),
    end_period: str = Query(...), account_code: str = Query(None),
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    cp = db.query(Counterparty).filter(Counterparty.id == counterparty_id).first()
    cp_name = cp.name if cp else "未知"
    beg = (
        db.query(VoucherEntry).join(Voucher, VoucherEntry.voucher_id == Voucher.id)
        .filter(Voucher.company_id == company_id, VoucherEntry.counterparty_id == counterparty_id,
                Voucher.date < f"{start_period}-01", Voucher.status.in_(["posted", "closed"]))
    )
    if account_code:
        beg = beg.filter(VoucherEntry.account_code.like(f"{account_code}%"))
    beg_entries = beg.all()
    beginning_balance = sum(e.debit for e in beg_entries) - sum(e.credit for e in beg_entries)
    cur = (
        db.query(VoucherEntry).join(Voucher, VoucherEntry.voucher_id == Voucher.id)
        .filter(Voucher.company_id == company_id, VoucherEntry.counterparty_id == counterparty_id,
                Voucher.date >= f"{start_period}-01", Voucher.date <= f"{end_period}-31",
                Voucher.status.in_(["posted", "closed"]))
    )
    if account_code:
        cur = cur.filter(VoucherEntry.account_code.like(f"{account_code}%"))
    cur_entries = cur.order_by(Voucher.date, Voucher.voucher_no).all()
    acct_codes = list(set(e.account_code for e in cur_entries))
    acct_map = {a.code: a.name for a in db.query(Account).filter(
        Account.company_id == company_id, Account.code.in_(acct_codes)).all()}
    running = beginning_balance
    entries = []
    for e in cur_entries:
        running = running + e.debit - e.credit
        entries.append(TransactionDetailEntry(
            date=e.voucher.date, voucher_no=e.voucher.voucher_no,
            account_code=e.account_code, account_name=acct_map.get(e.account_code, ""),
            summary=e.voucher.summary, debit=e.debit, credit=e.credit,
            balance=round(running, 2),
        ))
    total_debit = sum(e.debit for e in cur_entries)
    total_credit = sum(e.credit for e in cur_entries)
    ending = beginning_balance + total_debit - total_credit
    direction = "debit" if ending >= 0 else "credit"
    return TransactionDetailResponse(
        counterparty_id=counterparty_id, counterparty_name=cp_name,
        beginning_balance=round(beginning_balance, 2), direction=direction,
        entries=entries, total_debit=round(total_debit, 2),
        total_credit=round(total_credit, 2), ending_balance=round(abs(ending_balance), 2),
    )


@router.get("/transactions/aging", response_model=list[AgingRow])
def get_transaction_aging(
    company_id: int, end_period: str = Query(...), account_code: str = Query(None),
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    cp_ids = [
        r[0] for r in
        db.query(VoucherEntry.counterparty_id)
        .join(Voucher, VoucherEntry.voucher_id == Voucher.id)
        .filter(Voucher.company_id == company_id, VoucherEntry.counterparty_id.isnot(None),
                Voucher.status.in_(["posted", "closed"]))
        .distinct().all()
    ]
    if not cp_ids:
        return []
    counterparties = {cp.id: cp for cp in db.query(Counterparty).filter(Counterparty.id.in_(cp_ids)).all()}
    ref_date_str = f"{end_period}-31"
    ref_date = date.fromisoformat(ref_date_str)
    buckets_def = [
        ("0-30天", 0, 30), ("31-90天", 31, 90), ("91-180天", 91, 180),
        ("181-365天", 181, 365), ("365天+", 366, 99999),
    ]
    result = []
    for cp_id in cp_ids:
        cp = counterparties.get(cp_id)
        cp_name = cp.name if cp else "未知"
        entries_query = (
            db.query(VoucherEntry).join(Voucher, VoucherEntry.voucher_id == Voucher.id)
            .filter(Voucher.company_id == company_id, VoucherEntry.counterparty_id == cp_id,
                    Voucher.date <= ref_date_str, Voucher.status.in_(["posted", "closed"]))
        )
        if account_code:
            entries_query = entries_query.filter(VoucherEntry.account_code.like(f"{account_code}%"))
        entries = entries_query.all()
        buckets = []
        total_balance = 0
        for label, min_days, max_days in buckets_def:
            amount = 0.0
            for e in entries:
                e_date = date.fromisoformat(e.voucher.date)
                days = (ref_date - e_date).days
                if min_days <= days <= max_days:
                    amount += e.debit - e.credit
            buckets.append(AgingBucket(range=label, amount=round(amount, 2)))
            total_balance += amount
        result.append(AgingRow(counterparty_id=cp_id, counterparty_name=cp_name,
                               total_balance=round(total_balance, 2), buckets=buckets))
    return sorted(result, key=lambda r: abs(r.total_balance), reverse=True)
