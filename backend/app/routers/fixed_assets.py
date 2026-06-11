"""固定资产管理 — CRUD + 折旧 + 处置."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user
from app.models import FixedAsset, FixedAssetDepreciation, User, Voucher, VoucherEntry
from app.schemas import (
    FixedAssetCreate, FixedAssetUpdate, FixedAssetResponse,
    FixedAssetDepreciationCreate, FixedAssetDepreciationResponse,
    FixedAssetDispose, BatchDepreciationRequest,
)

router = APIRouter()


def _generate_voucher(db: Session, company_id: int, user_id: int, vtype: str, summary: str, entries: list[dict]):
    """生成会计凭证。entries: [{account_code, debit, credit, description}]"""
    voucher_no = f"{vtype}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    voucher = Voucher(
        company_id=company_id,
        creator_id=user_id,
        date=datetime.utcnow().strftime('%Y-%m-%d'),
        voucher_no=voucher_no,
        voucher_type=vtype,
        summary=summary,
        status="posted",
    )
    db.add(voucher)
    db.flush()
    for e in entries:
        db.add(VoucherEntry(
            voucher_id=voucher.id,
            account_code=e["account_code"],
            debit=e.get("debit", 0),
            credit=e.get("credit", 0),
            description=e.get("description", ""),
        ))
    return voucher


# ═══════════ 资产 CRUD ═══════════

@router.get("/assets", response_model=list[FixedAssetResponse])
def list_assets(
    company_id: int,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    category: str | None = None,
    status: str | None = None,
    location: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(FixedAsset).filter(FixedAsset.company_id == company_id)
    if category:
        q = q.filter(FixedAsset.category == category)
    if status:
        q = q.filter(FixedAsset.status == status)
    if location:
        q = q.filter(FixedAsset.location == location)
    if search:
        pattern = f"%{search}%"
        q = q.filter(
            (FixedAsset.name.ilike(pattern)) | (FixedAsset.asset_code.ilike(pattern))
        )
    return q.order_by(FixedAsset.id.desc()).offset(offset).limit(limit).all()


@router.get("/assets/{asset_id}", response_model=FixedAssetResponse)
def get_asset(asset_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(FixedAsset).filter(FixedAsset.id == asset_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="资产不存在")
    return item


@router.post("/assets", response_model=FixedAssetResponse)
def create_asset(data: FixedAssetCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = FixedAsset(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/assets/{asset_id}", response_model=FixedAssetResponse)
def update_asset(asset_id: int, data: FixedAssetUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(FixedAsset).filter(FixedAsset.id == asset_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="资产不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(item, k, v)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/assets/{asset_id}")
def delete_asset(asset_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(FixedAsset).filter(FixedAsset.id == asset_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="资产不存在")
    db.delete(item)
    db.commit()
    return {"ok": True}


# ═══════════ 处置 ═══════════

@router.post("/assets/{asset_id}/dispose", response_model=FixedAssetResponse)
def dispose_asset(
    asset_id: int,
    data: FixedAssetDispose,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if data.status not in ("已处置", "报废"):
        raise HTTPException(status_code=400, detail="处置状态必须为'已处置'或'报废'")

    asset = db.query(FixedAsset).filter(FixedAsset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="资产不存在")
    if asset.status in ("已处置", "报废"):
        raise HTTPException(status_code=400, detail="资产已处置或报废")

    gain_loss = round(data.disposal_proceeds - asset.net_value, 2)
    asset.status = data.status
    asset.disposal_date = data.disposal_date
    asset.disposal_proceeds = data.disposal_proceeds
    asset.disposal_gain_loss = gain_loss
    asset.disposal_reason = data.disposal_reason

    # 自动生成处置凭证：借累计折旧 + 借银行存款(收入) + 借营业外支出(损失) / 贷固定资产原值 + 贷营业外收入(利得)
    entries: list[dict] = []
    entries.append({"account_code": "1602", "debit": asset.accumulated_depreciation, "credit": 0, "description": f"转销累计折旧 {asset.name}"})
    entries.append({"account_code": "1601", "debit": 0, "credit": asset.original_value, "description": f"转销固定资产原值 {asset.name}"})
    if data.disposal_proceeds > 0:
        entries.append({"account_code": "1002", "debit": data.disposal_proceeds, "credit": 0, "description": f"处置收入 {asset.name}"})
    if gain_loss > 0:
        entries.append({"account_code": "6301", "debit": 0, "credit": gain_loss, "description": f"处置利得 {asset.name}"})
    elif gain_loss < 0:
        entries.append({"account_code": "6711", "debit": abs(gain_loss), "credit": 0, "description": f"处置损失 {asset.name}"})

    _generate_voucher(db, asset.company_id, user.id, "transfer", f"固定资产处置 {asset.name} ({asset.asset_code})", entries)

    db.commit()
    db.refresh(asset)
    return asset


# ═══════════ 折旧 CRUD ═══════════

@router.get("/depreciations", response_model=list[FixedAssetDepreciationResponse])
def list_depreciations(
    company_id: int,
    fixed_asset_id: int | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(FixedAssetDepreciation).filter(FixedAssetDepreciation.company_id == company_id)
    if fixed_asset_id:
        q = q.filter(FixedAssetDepreciation.fixed_asset_id == fixed_asset_id)
    return q.order_by(FixedAssetDepreciation.period.desc()).offset(offset).limit(limit).all()


@router.post("/depreciations", response_model=FixedAssetDepreciationResponse)
def create_depreciation(
    data: FixedAssetDepreciationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    asset = db.query(FixedAsset).filter(FixedAsset.id == data.fixed_asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="资产不存在")
    if asset.status not in ("使用中", "闲置"):
        raise HTTPException(status_code=400, detail=f"资产状态为'{asset.status}'，不可计提折旧")

    existing = db.query(FixedAssetDepreciation).filter(
        FixedAssetDepreciation.fixed_asset_id == data.fixed_asset_id,
        FixedAssetDepreciation.period == data.period,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"资产在期间{data.period}已计提折旧")

    before = asset.accumulated_depreciation
    after = before + data.depreciation_amount
    max_depreciable = asset.original_value - asset.residual_value
    if after > max_depreciable:
        raise HTTPException(status_code=400, detail=f"累计折旧{after}超过可折旧上限{max_depreciable}")

    item = FixedAssetDepreciation(
        **data.model_dump(),
        accumulated_before=before,
        accumulated_after=after,
    )
    db.add(item)
    asset.accumulated_depreciation = after
    asset.net_value = asset.original_value - after

    # 自动生成折旧凭证：借管理费用/贷累计折旧
    _generate_voucher(db, data.company_id, user.id, "transfer", f"计提折旧 {asset.name} ({data.period})", [
        {"account_code": "6602", "debit": data.depreciation_amount, "credit": 0, "description": f"折旧费 {asset.name}"},
        {"account_code": "1602", "debit": 0, "credit": data.depreciation_amount, "description": f"累计折旧 {asset.name}"},
    ])

    db.commit()
    db.refresh(item)
    return item


@router.put("/depreciations/{dep_id}", response_model=FixedAssetDepreciationResponse)
def update_depreciation(
    dep_id: int,
    data: FixedAssetDepreciationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    dep = db.query(FixedAssetDepreciation).filter(FixedAssetDepreciation.id == dep_id).first()
    if not dep:
        raise HTTPException(status_code=404, detail="折旧记录不存在")
    asset = db.query(FixedAsset).filter(FixedAsset.id == dep.fixed_asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="资产不存在")

    old_amount = dep.depreciation_amount
    new_amount = data.depreciation_amount
    after = dep.accumulated_before + new_amount

    if after > asset.original_value - asset.residual_value:
        raise HTTPException(status_code=400, detail=f"折旧后累计{after}将超过可折旧上限{asset.original_value - asset.residual_value}")

    dep.depreciation_amount = new_amount
    dep.accumulated_after = after

    asset.accumulated_depreciation = asset.accumulated_depreciation - old_amount + new_amount
    asset.net_value = asset.original_value - asset.accumulated_depreciation

    db.commit()
    db.refresh(dep)
    return dep


@router.delete("/depreciations/{dep_id}")
def delete_depreciation(
    dep_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    dep = db.query(FixedAssetDepreciation).filter(FixedAssetDepreciation.id == dep_id).first()
    if not dep:
        raise HTTPException(status_code=404, detail="折旧记录不存在")
    asset = db.query(FixedAsset).filter(FixedAsset.id == dep.fixed_asset_id).first()
    if asset:
        asset.accumulated_depreciation -= dep.depreciation_amount
        asset.net_value = asset.original_value - asset.accumulated_depreciation
    db.delete(dep)
    db.commit()
    return {"ok": True}


# ═══════════ 批量计提 ═══════════

@router.post("/depreciations/batch")
def batch_depreciate(
    data: BatchDepreciationRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(FixedAsset).filter(
        FixedAsset.company_id == data.company_id,
        FixedAsset.status.in_(["使用中", "闲置"]),
    )
    if data.asset_ids:
        q = q.filter(FixedAsset.id.in_(data.asset_ids))

    assets = q.all()
    success = []
    failed = []

    for asset in assets:
        existing = db.query(FixedAssetDepreciation).filter(
            FixedAssetDepreciation.fixed_asset_id == asset.id,
            FixedAssetDepreciation.period == data.period,
        ).first()
        if existing:
            failed.append({"asset_id": asset.id, "asset_name": asset.name, "reason": f"期间{data.period}已计提"})
            continue

        if asset.depreciation_method == "直线法":
            amount = round((asset.original_value - asset.residual_value) / (asset.useful_life * 12), 2)
        else:
            amount = asset.monthly_depreciation

        if amount <= 0:
            failed.append({"asset_id": asset.id, "asset_name": asset.name, "reason": "月折旧额为0"})
            continue

        after = asset.accumulated_depreciation + amount
        if after > asset.original_value - asset.residual_value:
            amount = round(asset.original_value - asset.residual_value - asset.accumulated_depreciation, 2)
            after = asset.original_value - asset.residual_value

        if amount <= 0:
            failed.append({"asset_id": asset.id, "asset_name": asset.name, "reason": "已提足折旧"})
            continue

        dep = FixedAssetDepreciation(
            company_id=data.company_id,
            fixed_asset_id=asset.id,
            period=data.period,
            depreciation_amount=amount,
            accumulated_before=asset.accumulated_depreciation,
            accumulated_after=after,
        )
        db.add(dep)
        asset.accumulated_depreciation = after
        asset.net_value = asset.original_value - after
        success.append({"asset_id": asset.id, "asset_name": asset.name, "amount": amount})

    # 批量折旧汇总生成一张凭证
    total_amount = round(sum(s["amount"] for s in success), 2)
    if total_amount > 0:
        _generate_voucher(db, data.company_id, user.id, "transfer", f"批量计提折旧 {data.period} ({len(success)}项)", [
            {"account_code": "6602", "debit": total_amount, "credit": 0, "description": f"折旧费 {data.period}"},
            {"account_code": "1602", "debit": 0, "credit": total_amount, "description": f"累计折旧 {data.period}"},
        ])

    db.commit()
    return {"success": success, "failed": failed, "total": len(assets)}
