"""费用报销管理 — 报销单 + 借款 + 费用标准."""
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user
from app.models import (
    User, ExpenseItem, ExpenseReport, ExpenseReportItem,
    ExpenseLoan, ExpensePolicy, ExpenseAttachment, AuditLog,
)
from app.schemas.expenses import (
    ExpenseItemCreate, ExpenseItemResponse,
    ExpensePolicyCreate, ExpensePolicyResponse,
    ExpenseReportCreate, ExpenseReportUpdate, ExpenseReportResponse,
    ExpenseReportItemResponse,
    ExpenseLoanCreate, ExpenseLoanResponse,
    ExpenseAttachmentResponse,
    ApprovalAction, RepayAction,
)
from app.schemas import BypassAction
from app.permissions import check_approval_bypass
import os
import json

router = APIRouter()


# ── 辅助函数 ──

def _generate_report_no(company_id: int, db: Session) -> str:
    today = date.today().strftime("%Y%m%d")
    count = db.query(ExpenseReport).filter(
        ExpenseReport.company_id == company_id,
        ExpenseReport.report_no.like(f"ER-{today}-%"),
    ).count()
    return f"ER-{today}-{count + 1:03d}"


def _generate_loan_no(company_id: int, db: Session) -> str:
    today = date.today().strftime("%Y%m%d")
    count = db.query(ExpenseLoan).filter(
        ExpenseLoan.company_id == company_id,
        ExpenseLoan.loan_no.like(f"LN-{today}-%"),
    ).count()
    return f"LN-{today}-{count + 1:03d}"


def _check_policy(company_id: int, expense_item_id: int, amount: float, db: Session) -> dict:
    """匹配费用标准，返回检查结果。"""
    result = {"exceeded": False, "limit": None, "message": None}
    today_iso = date.today().isoformat()
    policies = db.query(ExpensePolicy).filter(
        ExpensePolicy.company_id == company_id,
        ExpensePolicy.expense_item_id == expense_item_id,
        ExpensePolicy.effective_from <= today_iso,
    ).all()
    for p in policies:
        if p.effective_to and p.effective_to < today_iso:
            continue
        if p.max_amount > 0 and amount > p.max_amount:
            result["exceeded"] = True
            result["limit"] = p.max_amount
            result["message"] = f"超过标准 ¥{p.max_amount:.2f}（{p.policy_type}）"
            break
    return result


def _build_approval_chain(total_amount: float, user: User, db: Session) -> list[dict]:
    """按金额构建审批链。"""
    chain = []

    # Step 1: 部门负责人
    chain.append({
        "step": 1, "role": "department_head", "title": "部门负责人",
        "user_id": None, "status": "pending", "comment": None, "timestamp": None,
    })

    if total_amount > 2000:
        fm_users = db.query(User).filter(User.role == "finance_manager", User.is_active).all()
        chain.append({
            "step": 2, "role": "finance_manager", "title": "财务经理",
            "user_id": fm_users[0].id if fm_users else None,
            "status": "pending", "comment": None, "timestamp": None,
        })

    if total_amount > 10000:
        fd_users = db.query(User).filter(User.role == "finance_director", User.is_active).all()
        chain.append({
            "step": len(chain) + 1, "role": "finance_director", "title": "财务总监",
            "user_id": fd_users[0].id if fd_users else None,
            "status": "pending", "comment": None, "timestamp": None,
        })

    return chain


# ═══════════ 费用项目 CRUD ═══════════

@router.get("/items", response_model=list[ExpenseItemResponse])
def list_expense_items(company_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(ExpenseItem).filter(
        ExpenseItem.company_id == company_id, ExpenseItem.is_active
    ).order_by(ExpenseItem.code).all()


@router.post("/items", response_model=ExpenseItemResponse)
def create_expense_item(data: ExpenseItemCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = ExpenseItem(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/items/{item_id}", response_model=ExpenseItemResponse)
def update_expense_item(item_id: int, data: ExpenseItemCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(ExpenseItem).filter(ExpenseItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="费用项目不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(item, k, v)
    db.commit()
    db.refresh(item)
    return item


# ═══════════ 费用标准 CRUD ═══════════

@router.get("/policies", response_model=list[ExpensePolicyResponse])
def list_policies(company_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(ExpensePolicy).filter(
        ExpensePolicy.company_id == company_id
    ).order_by(ExpensePolicy.effective_from.desc()).all()


@router.post("/policies", response_model=ExpensePolicyResponse)
def create_policy(data: ExpensePolicyCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = ExpensePolicy(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/policies/{policy_id}", response_model=ExpensePolicyResponse)
def update_policy(policy_id: int, data: ExpensePolicyCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(ExpensePolicy).filter(ExpensePolicy.id == policy_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="费用标准不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(item, k, v)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/policies/{policy_id}")
def delete_policy(policy_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(ExpensePolicy).filter(ExpensePolicy.id == policy_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="费用标准不存在")
    db.delete(item)
    db.commit()
    return {"ok": True}


# ═══════════ 报销单 CRUD ═══════════

@router.get("/reports", response_model=list[ExpenseReportResponse])
def list_reports(
    company_id: int,
    status: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(ExpenseReport).filter(ExpenseReport.company_id == company_id)
    if status:
        q = q.filter(ExpenseReport.status == status)
    return q.order_by(ExpenseReport.id.desc()).all()


@router.post("/reports", response_model=ExpenseReportResponse)
def create_report(data: ExpenseReportCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    total = sum(item.amount for item in data.items)
    report = ExpenseReport(
        company_id=data.company_id,
        report_no=_generate_report_no(data.company_id, db),
        applicant_id=user.id,
        department_id=data.department_id,
        expense_date=data.expense_date,
        total_amount=total,
        net_payable=total,
        notes=data.notes,
    )
    db.add(report)
    db.flush()

    for it in data.items:
        detail = ExpenseReportItem(
            report_id=report.id,
            row_seq=it.row_seq,
            expense_item_id=it.expense_item_id,
            date=it.date,
            amount=it.amount,
            description=it.description,
            receipt_count=it.receipt_count,
        )
        db.add(detail)

    db.commit()
    db.refresh(report)
    return report


@router.get("/reports/{report_id}", response_model=ExpenseReportResponse)
def get_report(report_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    report = db.query(ExpenseReport).filter(ExpenseReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报销单不存在")
    return report


@router.put("/reports/{report_id}", response_model=ExpenseReportResponse)
def update_report(report_id: int, data: ExpenseReportUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    report = db.query(ExpenseReport).filter(ExpenseReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报销单不存在")
    if report.status != "draft":
        raise HTTPException(status_code=400, detail="仅草稿状态可编辑")

    if data.expense_date is not None:
        report.expense_date = data.expense_date
    if data.department_id is not None:
        report.department_id = data.department_id
    if data.notes is not None:
        report.notes = data.notes

    if data.items is not None:
        db.query(ExpenseReportItem).filter(ExpenseReportItem.report_id == report.id).delete()
        total = 0
        for it in data.items:
            detail = ExpenseReportItem(
                report_id=report.id,
                row_seq=it.row_seq,
                expense_item_id=it.expense_item_id,
                date=it.date,
                amount=it.amount,
                description=it.description,
                receipt_count=it.receipt_count,
            )
            db.add(detail)
            total += it.amount
        report.total_amount = total
        report.net_payable = total - report.loan_offset_amount

    db.commit()
    db.refresh(report)
    return report


@router.get("/reports/{report_id}/items", response_model=list[ExpenseReportItemResponse])
def get_report_items(report_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(ExpenseReportItem).filter(
        ExpenseReportItem.report_id == report_id
    ).order_by(ExpenseReportItem.row_seq).all()


# ═══════════ 审批操作 ═══════════

@router.post("/reports/{report_id}/submit", response_model=ExpenseReportResponse)
def submit_report(report_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    report = db.query(ExpenseReport).filter(ExpenseReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报销单不存在")
    if report.status != "draft":
        raise HTTPException(status_code=400, detail="仅草稿状态可提交")
    if report.applicant_id != user.id:
        raise HTTPException(status_code=403, detail="只能提交自己的报销单")

    # 费用标准检查
    warnings = []
    items = db.query(ExpenseReportItem).filter(ExpenseReportItem.report_id == report.id).all()
    for item in items:
        if item.expense_item_id:
            check = _check_policy(report.company_id, item.expense_item_id, item.amount, db)
            item.policy_check = check
            if check["exceeded"]:
                warnings.append({
                    "row_seq": item.row_seq,
                    "description": item.description,
                    "amount": item.amount,
                    "limit": check["limit"],
                    "message": check["message"],
                })

    # 构建审批链
    chain = _build_approval_chain(report.total_amount, user, db)
    if not chain:
        raise HTTPException(status_code=500, detail="无法构建审批链，请检查部门设置和人员配置")

    report.approval_chain = chain
    report.policy_warnings = warnings if warnings else None
    report.status = "submitted"
    report.current_approver_id = chain[0].get("user_id")

    db.commit()
    db.refresh(report)
    return report


@router.post("/reports/{report_id}/approve", response_model=ExpenseReportResponse)
def approve_report(report_id: int, action: ApprovalAction, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    report = db.query(ExpenseReport).filter(ExpenseReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报销单不存在")
    if report.current_approver_id != user.id:
        raise HTTPException(status_code=403, detail="您不是当前审批人")

    chain = report.approval_chain or []
    now_iso = datetime.utcnow().isoformat()
    status_map = {
        "department_head": "dept_approved",
        "finance_manager": "finance_approved",
        "finance_director": "director_approved",
        "unit_head": "unit_head_approved",
    }

    # 标记当前节点完成
    for node in chain:
        if node["status"] == "pending":
            node["status"] = "approved"
            node["user_id"] = user.id
            node["comment"] = action.comment
            node["timestamp"] = now_iso
            report.status = status_map.get(node["role"], "approved")
            break

    # 找到下一个待审批节点
    next_node = None
    for node in chain:
        if node["status"] == "pending":
            next_node = node
            break

    if next_node:
        report.current_approver_id = next_node.get("user_id")
    else:
        report.current_approver_id = None

    report.approval_chain = chain
    db.commit()
    db.refresh(report)
    return report


@router.post("/reports/{report_id}/reject", response_model=ExpenseReportResponse)
def reject_report(report_id: int, action: ApprovalAction, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    report = db.query(ExpenseReport).filter(ExpenseReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报销单不存在")
    if report.current_approver_id != user.id:
        raise HTTPException(status_code=403, detail="您不是当前审批人")

    chain = report.approval_chain or []
    now_iso = datetime.utcnow().isoformat()
    for node in chain:
        if node["status"] == "pending":
            node["status"] = "rejected"
            node["user_id"] = user.id
            node["comment"] = action.comment
            node["timestamp"] = now_iso
            break

    report.status = "rejected"
    report.current_approver_id = None
    report.approval_chain = chain
    db.commit()
    db.refresh(report)
    return report


@router.post("/reports/{report_id}/pay", response_model=ExpenseReportResponse)
def pay_report(report_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    report = db.query(ExpenseReport).filter(ExpenseReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报销单不存在")
    if report.status not in ("dept_approved", "finance_approved", "director_approved", "unit_head_approved"):
        raise HTTPException(status_code=400, detail="当前状态不可付款")

    # 处理借款冲销
    if report.loan_offset_amount > 0:
        loans = db.query(ExpenseLoan).filter(
            ExpenseLoan.applicant_id == report.applicant_id,
            ExpenseLoan.status.in_(["approved", "partial_repaid"]),
        ).all()
        remaining = report.loan_offset_amount
        for loan in loans:
            if remaining <= 0:
                break
            due = loan.amount - loan.repaid_amount
            deduct = min(remaining, due)
            loan.repaid_amount += deduct
            loan.status = "fully_repaid" if loan.repaid_amount >= loan.amount else "partial_repaid"
            remaining -= deduct

    report.status = "paid"
    db.commit()
    db.refresh(report)
    return report


@router.post("/reports/{report_id}/cancel", response_model=ExpenseReportResponse)
def cancel_report(report_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    report = db.query(ExpenseReport).filter(ExpenseReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报销单不存在")
    if report.applicant_id != user.id:
        raise HTTPException(status_code=403, detail="只能撤回自己的报销单")
    if report.status not in ("submitted", "dept_approved"):
        raise HTTPException(status_code=400, detail="当前状态不可撤回")

    report.status = "draft"
    report.current_approver_id = None
    report.approval_chain = None
    report.policy_warnings = None
    db.commit()
    db.refresh(report)
    return report


@router.post("/reports/{report_id}/bypass", response_model=ExpenseReportResponse)
def bypass_report_approval(report_id: int, action: BypassAction, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """强制跳过当前审批节点（仅管理员/财务总监）"""
    report = db.query(ExpenseReport).filter(ExpenseReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报销单不存在")

    err = check_approval_bypass(user)
    if err:
        raise HTTPException(status_code=403, detail=err)

    chain = report.approval_chain or []
    now_iso = datetime.utcnow().isoformat()
    bypassed_node = None

    for node in chain:
        if node["status"] == "pending":
            bypassed_node = {"role": node.get("role"), "user_id": node.get("user_id")}
            node["status"] = "bypassed"
            node["user_id"] = user.id
            node["comment"] = action.reason
            node["timestamp"] = now_iso
            break

    next_node = None
    for node in chain:
        if node["status"] == "pending":
            next_node = node
            break

    if next_node:
        report.current_approver_id = next_node.get("user_id")
    else:
        report.current_approver_id = None

    report.approval_chain = chain

    db.add(AuditLog(
        company_id=report.company_id, user_id=user.id,
        action="bypass_approval", target_type="expense_report",
        target_id=report.id, reason=action.reason,
        details=json.dumps({"bypassed_node": bypassed_node}),
    ))

    db.commit()
    db.refresh(report)
    return report


# ═══════════ 借款管理 ═══════════

@router.get("/loans", response_model=list[ExpenseLoanResponse])
def list_loans(company_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(ExpenseLoan).filter(
        ExpenseLoan.company_id == company_id
    ).order_by(ExpenseLoan.id.desc()).all()


@router.post("/loans", response_model=ExpenseLoanResponse)
def create_loan(data: ExpenseLoanCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    loan = ExpenseLoan(
        company_id=data.company_id,
        loan_no=_generate_loan_no(data.company_id, db),
        applicant_id=user.id,
        department_id=data.department_id,
        loan_date=data.loan_date,
        amount=data.amount,
        reason=data.reason,
        expected_repay_date=data.expected_repay_date,
        notes=data.notes,
    )
    db.add(loan)
    db.commit()
    db.refresh(loan)
    return loan


@router.post("/loans/{loan_id}/approve", response_model=ExpenseLoanResponse)
def approve_loan(loan_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    loan = db.query(ExpenseLoan).filter(ExpenseLoan.id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="借款单不存在")
    if loan.status != "submitted":
        raise HTTPException(status_code=400, detail="当前状态不可审批")
    loan.status = "approved"
    db.commit()
    db.refresh(loan)
    return loan


@router.post("/loans/{loan_id}/bypass", response_model=ExpenseLoanResponse)
def bypass_loan_approval(loan_id: int, action: BypassAction, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """强制跳过借款审批（仅管理员/财务总监）"""
    loan = db.query(ExpenseLoan).filter(ExpenseLoan.id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="借款单不存在")

    err = check_approval_bypass(user)
    if err:
        raise HTTPException(status_code=403, detail=err)

    if loan.status not in ("submitted", "draft"):
        raise HTTPException(status_code=400, detail="当前状态不可跳过审批")

    loan.status = "approved"

    db.add(AuditLog(
        company_id=loan.company_id, user_id=user.id,
        action="bypass_approval", target_type="expense_loan",
        target_id=loan.id, reason=action.reason,
    ))

    db.commit()
    db.refresh(loan)
    return loan


@router.post("/loans/{loan_id}/repay", response_model=ExpenseLoanResponse)
def repay_loan(loan_id: int, data: RepayAction, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    loan = db.query(ExpenseLoan).filter(ExpenseLoan.id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="借款单不存在")
    if loan.status not in ("approved", "partial_repaid"):
        raise HTTPException(status_code=400, detail="当前状态不可还款")
    loan.repaid_amount += data.amount
    loan.status = "fully_repaid" if loan.repaid_amount >= loan.amount else "partial_repaid"
    db.commit()
    db.refresh(loan)
    return loan


# ═══════════ 附件管理 ═══════════

UPLOAD_DIR = "uploads/expenses"


@router.get("/reports/{report_id}/attachments", response_model=list[ExpenseAttachmentResponse])
def list_attachments(report_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(ExpenseAttachment).filter(
        ExpenseAttachment.report_id == report_id
    ).order_by(ExpenseAttachment.file_name).all()


@router.post("/attachments", response_model=ExpenseAttachmentResponse)
def upload_attachment(
    report_id: int = Form(...),
    category: str = Form("其他"),
    doc_number: str = Form("-"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    report = db.query(ExpenseReport).filter(ExpenseReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报销单不存在")

    count = db.query(ExpenseAttachment).filter(
        ExpenseAttachment.report_id == report_id
    ).count()
    seq = f"{count + 1:02d}"

    name_without_ext = file.filename.rsplit('.', 1)[0] if '.' in file.filename else file.filename
    safe_name = f"{seq}-{category}-{doc_number}-{name_without_ext}.{file.filename.rsplit('.', 1)[-1] if '.' in file.filename else 'bin'}"

    dir_path = os.path.join(UPLOAD_DIR, str(report.company_id), str(report_id))
    os.makedirs(dir_path, exist_ok=True)
    file_path = os.path.join(dir_path, safe_name)

    content = file.file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    attachment = ExpenseAttachment(
        report_id=report_id,
        file_name=safe_name,
        category=category,
        doc_number=doc_number,
        file_path=file_path,
        file_size=len(content),
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return attachment


@router.delete("/attachments/{attachment_id}")
def delete_attachment(attachment_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    att = db.query(ExpenseAttachment).filter(ExpenseAttachment.id == attachment_id).first()
    if not att:
        raise HTTPException(status_code=404, detail="附件不存在")
    if os.path.exists(att.file_path):
        os.remove(att.file_path)
    db.delete(att)
    db.commit()
    return {"ok": True}


# ═══════════ 查询统计 ═══════════

@router.get("/stats")
def expense_stats(
    company_id: int,
    start_date: str | None = None,
    end_date: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(ExpenseReport).filter(ExpenseReport.company_id == company_id)
    if start_date:
        q = q.filter(ExpenseReport.expense_date >= start_date)
    if end_date:
        q = q.filter(ExpenseReport.expense_date <= end_date)

    reports = q.all()
    total_amount = sum(r.total_amount for r in reports)
    total_count = len(reports)

    by_status: dict[str, float] = {}
    for r in reports:
        by_status[r.status] = by_status.get(r.status, 0) + r.total_amount

    return {
        "total_count": total_count,
        "total_amount": total_amount,
        "by_status": [{"status": k, "amount": v} for k, v in by_status.items()],
    }
