"""系统管理路由：数据导出、数据库备份。"""
import io
import os
import csv
import shutil
import glob
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user, require_role
from app.models import User, Account, Voucher, VoucherEntry, Department, AccountingPeriod

router = APIRouter()

BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "backups")
os.makedirs(BACKUP_DIR, exist_ok=True)

DB_PATH = os.environ.get("DATABASE_URL", "").replace("sqlite:///", "")
if not DB_PATH:
    DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "finance.db")


def _get_db_path() -> str:
    """Get the actual SQLite database file path."""
    if DB_PATH and os.path.isfile(DB_PATH):
        return DB_PATH
    # Fallback: look in the data directory
    fallback = os.path.join(os.path.dirname(BACKUP_DIR), "finance.db")
    if os.path.isfile(fallback):
        return fallback
    raise HTTPException(status_code=500, detail="找不到数据库文件")


def _backup_path(label: str) -> str:
    """Return backup dir for a given label (monthly/yearly)."""
    d = os.path.join(BACKUP_DIR, label)
    os.makedirs(d, exist_ok=True)
    return d


# ──────────────── 数据库备份 ────────────────

@router.get("/backups")
def list_backups(
    type: str = Query("monthly", pattern="^(monthly|yearly)$"),
    user: User = Depends(get_current_user),
):
    """列出已有备份。"""
    d = _backup_path(type)
    files = sorted(glob.glob(os.path.join(d, "*.db")), reverse=True)
    result = []
    for f in files:
        name = os.path.basename(f)
        stat = os.stat(f)
        size_kb = round(stat.st_size / 1024, 1)
        result.append({
            "filename": name,
            "size_kb": size_kb,
            "created_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S"),
        })
    return result


@router.post("/backup")
def create_backup(
    type: str = Query("monthly", pattern="^(monthly|yearly)$"),
    label: str = Query(""),
    user: User = Depends(get_current_user),
):
    """创建新备份（复制 finance.db）。label 为可选标记，如 '2026-05'。"""
    require_role(user, ["super_admin", "finance_manager", "finance_director"])
    db_path = _get_db_path()
    ts = datetime.now(timezone(timedelta(hours=8))).strftime("%Y%m%d_%H%M%S")
    prefix = f"backup_{label}_" if label else "backup_"
    filename = f"{prefix}{ts}.db"
    dest = os.path.join(_backup_path(type), filename)
    shutil.copy2(db_path, dest)
    size_kb = round(os.path.getsize(dest) / 1024, 1)
    return {"filename": filename, "size_kb": size_kb, "message": "备份创建成功"}


@router.get("/backups/{filename}")
def download_backup(
    filename: str,
    type: str = Query("monthly", pattern="^(monthly|yearly)$"),
    user: User = Depends(get_current_user),
):
    """下载备份文件。"""
    path = os.path.join(_backup_path(type), filename)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="备份文件不存在")
    return FileResponse(path, media_type="application/octet-stream", filename=filename)


@router.delete("/backups/{filename}")
def delete_backup(
    filename: str,
    type: str = Query("monthly", pattern="^(monthly|yearly)$"),
    user: User = Depends(get_current_user),
):
    """删除备份文件。"""
    require_role(user, ["super_admin", "finance_manager", "finance_director"])
    path = os.path.join(_backup_path(type), filename)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="备份文件不存在")
    os.remove(path)
    return {"message": "备份已删除"}


# ──────────────── 数据导出 ────────────────

EXPORT_TABLES = {
    "accounts": ("科目表", Account, ["code", "name", "level", "parent_code", "category", "balance_direction", "initial_balance", "is_active"]),
    "vouchers": ("凭证", Voucher, ["id", "date", "voucher_no", "voucher_type", "summary", "status", "creator_id"]),
    "voucher_entries": ("凭证分录", VoucherEntry, ["id", "voucher_id", "account_code", "debit", "credit", "description"]),
    "departments": ("部门", Department, ["id", "code", "name", "parent_id", "is_active"]),
    "periods": ("会计期间", AccountingPeriod, ["id", "company_id", "period", "is_closed", "closed_at"]),
}


@router.get("/export")
def export_data(
    company_id: int,
    tables: str = Query("accounts,vouchers,departments", description="逗号分隔的表名"),
    format: str = Query("csv", pattern="^(csv|json)$"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """导出指定表的数据为 CSV 或 JSON。"""
    selected = [t.strip() for t in tables.split(",") if t.strip() in EXPORT_TABLES]
    if not selected:
        raise HTTPException(status_code=400, detail="未选择有效的导出表")

    if format == "json":
        import json as _json
        result = {}
        for key in selected:
            label, model, cols = EXPORT_TABLES[key]
            q = db.query(model).filter(_filter_company(model, company_id)).all()
            result[key] = [{c: _serialize(getattr(r, c)) for c in cols} for r in q]
        return result

    # CSV: 每个表一个 section，用空行分隔
    output = io.StringIO()
    writer = csv.writer(output)
    for key in selected:
        label, model, cols = EXPORT_TABLES[key]
        q = db.query(model).filter(_filter_company(model, company_id)).all()
        writer.writerow([f"# {label}"])
        writer.writerow(cols)
        for row in q:
            writer.writerow([_serialize(getattr(row, c)) for c in cols])
        writer.writerow([])

    output.seek(0)
    ts = datetime.now(timezone(timedelta(hours=8))).strftime("%Y%m%d_%H%M%S")
    return StreamingResponse(
        output,
        media_type="text/csv; charset=utf-8-sig",
        headers={"Content-Disposition": f"attachment; filename=egp_export_{ts}.csv"},
    )


@router.get("/export/full")
def export_full_db(user: User = Depends(get_current_user)):
    """下载完整数据库文件。"""
    require_role(user, ["super_admin", "finance_manager", "finance_director"])
    db_path = _get_db_path()
    ts = datetime.now(timezone(timedelta(hours=8))).strftime("%Y%m%d_%H%M%S")
    return FileResponse(db_path, media_type="application/octet-stream", filename=f"egp_ims_full_{ts}.db")


def _filter_company(model, company_id: int):
    """Return SQLAlchemy filter for company_id if the model has that column."""
    if hasattr(model, "company_id"):
        return model.company_id == company_id
    return True  # noqa


def _serialize(val) -> str:
    if val is None:
        return ""
    if isinstance(val, datetime):
        return val.strftime("%Y-%m-%d %H:%M:%S")
    return str(val)
