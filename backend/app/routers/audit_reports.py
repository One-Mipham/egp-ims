"""年度审计报告路由。"""
import os
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models import User, AuditReport

router = APIRouter()

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "audit_reports")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("/")
def get_audit_report(
    company_id: int = Query(...),
    year: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取某公司某年度的审计报告信息。"""
    report = db.query(AuditReport).filter(
        AuditReport.company_id == company_id,
        AuditReport.year == year,
    ).first()
    if not report:
        return {"found": False, "data": None}
    return {
        "found": True,
        "data": {
            "id": report.id,
            "company_id": report.company_id,
            "year": report.year,
            "firm_name": report.firm_name,
            "contact_person": report.contact_person,
            "contact_email": report.contact_email,
            "contact_phone": report.contact_phone,
            "report_file": report.report_file,
            "report_file_name": report.report_file_name,
            "balance_sheet_ok": report.balance_sheet_ok,
            "income_statement_ok": report.income_statement_ok,
            "cashflow_statement_ok": report.cashflow_statement_ok,
            "notes": report.notes,
            "created_at": report.created_at.isoformat() if report.created_at else None,
            "updated_at": report.updated_at.isoformat() if report.updated_at else None,
        },
    }


@router.put("/")
def save_audit_report(
    company_id: int = Query(...),
    year: int = Query(...),
    firm_name: str = Form(None),
    contact_person: str = Form(None),
    contact_email: str = Form(None),
    contact_phone: str = Form(None),
    balance_sheet_ok: bool = Form(False),
    income_statement_ok: bool = Form(False),
    cashflow_statement_ok: bool = Form(False),
    notes: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建或更新审计报告信息。"""
    report = db.query(AuditReport).filter(
        AuditReport.company_id == company_id,
        AuditReport.year == year,
    ).first()

    if not report:
        report = AuditReport(company_id=company_id, year=year)
        db.add(report)

    report.firm_name = firm_name
    report.contact_person = contact_person
    report.contact_email = contact_email
    report.contact_phone = contact_phone
    report.balance_sheet_ok = balance_sheet_ok
    report.income_statement_ok = income_statement_ok
    report.cashflow_statement_ok = cashflow_statement_ok
    report.notes = notes
    report.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(report)
    return {"ok": True, "id": report.id}


@router.post("/upload")
def upload_audit_file(
    company_id: int = Query(...),
    year: int = Query(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """上传审计报告文件（PDF等）。"""
    # 限制文件大小 20MB
    contents = file.file.read()
    if len(contents) > 20 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="文件大小不能超过 20MB")

    # 保存到 data/audit_reports/{company_id}/{year}/
    target_dir = os.path.join(UPLOAD_DIR, str(company_id), str(year))
    os.makedirs(target_dir, exist_ok=True)

    ext = os.path.splitext(file.filename or "report.pdf")[1] or ".pdf"
    safe_name = f"audit_report{ext}"
    file_path = os.path.join(target_dir, safe_name)

    with open(file_path, "wb") as f:
        f.write(contents)

    # 更新数据库记录
    report = db.query(AuditReport).filter(
        AuditReport.company_id == company_id,
        AuditReport.year == year,
    ).first()
    if not report:
        report = AuditReport(company_id=company_id, year=year)
        db.add(report)

    report.report_file = file_path
    report.report_file_name = file.filename
    report.updated_at = datetime.utcnow()
    db.commit()

    return {"ok": True, "file_name": file.filename}


@router.get("/download")
def download_audit_file(
    company_id: int = Query(...),
    year: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """下载审计报告文件。"""
    report = db.query(AuditReport).filter(
        AuditReport.company_id == company_id,
        AuditReport.year == year,
    ).first()
    if not report or not report.report_file:
        raise HTTPException(status_code=404, detail="未找到审计报告文件")

    if not os.path.isfile(report.report_file):
        raise HTTPException(status_code=404, detail="文件已被删除")

    return FileResponse(
        report.report_file,
        filename=report.report_file_name or "audit_report.pdf",
        media_type="application/octet-stream",
    )
