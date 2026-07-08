"""行政综合管理系统 API Router"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models import (
    User, AuditLog,
    ApprovalRecord, AdminDocument,
    VehicleSupplier, VehiclePurchase, Vehicle, VehicleMaintenance,
    InsurancePolicy,
    StockCategory, StockAsset, StockPurchase, StockRequisition,
    StockInbound, StockOutbound, StockCount,
    GiftCategory, StockGift, StockGiftPurchase, StockGiftRequisition,
    StockGiftInbound, StockGiftOutbound,
)
from app.permissions import check_approval_bypass
from app.schemas import (
    ApprovalRecordResponse, SubmitApprovalRequest, ApprovalAction, BypassAction,
    AdminDocumentCreate, AdminDocumentUpdate, AdminDocumentResponse,
    VehicleSupplierCreate, VehicleSupplierUpdate, VehicleSupplierResponse,
    VehiclePurchaseCreate, VehiclePurchaseUpdate, VehiclePurchaseResponse,
    VehicleCreate, VehicleUpdate, VehicleResponse,
    VehicleMaintenanceCreate, VehicleMaintenanceUpdate, VehicleMaintenanceResponse,
    InsurancePolicyCreate, InsurancePolicyUpdate, InsurancePolicyResponse,
    StockCategoryCreate, StockCategoryUpdate, StockCategoryResponse,
    StockAssetCreate, StockAssetUpdate, StockAssetResponse,
    StockPurchaseCreate, StockPurchaseUpdate, StockPurchaseResponse,
    StockRequisitionCreate, StockRequisitionUpdate, StockRequisitionResponse,
    StockInboundCreate, StockInboundUpdate, StockInboundResponse,
    StockOutboundCreate, StockOutboundUpdate, StockOutboundResponse,
    StockCountCreate, StockCountUpdate, StockCountResponse,
    GiftCategoryCreate, GiftCategoryUpdate, GiftCategoryResponse,
    StockGiftCreate, StockGiftUpdate, StockGiftResponse,
    StockGiftPurchaseCreate, StockGiftPurchaseUpdate, StockGiftPurchaseResponse,
    StockGiftRequisitionCreate, StockGiftRequisitionUpdate, StockGiftRequisitionResponse,
    StockGiftInboundCreate, StockGiftInboundUpdate, StockGiftInboundResponse,
    StockGiftOutboundCreate, StockGiftOutboundUpdate, StockGiftOutboundResponse,
)

router = APIRouter()


# ── helpers ──

def _write_audit(db: Session, company_id: int, user: User, action: str, target_type: str, target_id: int | None = None, reason: str | None = None):
    db.add(AuditLog(
        company_id=company_id, user_id=user.id,
        action=action, target_type=target_type,
        target_id=target_id, reason=reason,
    ))
    db.commit()


def _process_approval(db: Session, target_type: str, target_id: int, user: User, action: str, comment: str | None):
    """Process approve/reject for any admin entity."""
    records = db.query(ApprovalRecord).filter(
        ApprovalRecord.target_type == target_type,
        ApprovalRecord.target_id == target_id,
    ).order_by(ApprovalRecord.step).all()

    if not records:
        return "审批记录不存在"

    current_step = None
    for r in records:
        if r.status == "pending":
            current_step = r
            break

    if current_step is None:
        return "该审批流程已结束"

    if current_step.approver_id != user.id:
        return "您不是当前步骤的审批人"

    if action == "approve":
        current_step.status = "approved"
        current_step.comment = comment
        # check if this is the last step
        remaining = any(r.status == "pending" for r in records if r.step > current_step.step)
        if not remaining:
            _update_entity_status(db, target_type, target_id, "approved")
        _write_audit(db, user.company_id if hasattr(user, 'company_id') else 0, user, "approve_step", target_type, target_id)
    elif action == "reject":
        current_step.status = "rejected"
        current_step.comment = comment
        for r in records:
            if r.status == "pending":
                r.status = "rejected"
        _update_entity_status(db, target_type, target_id, "rejected")
        _write_audit(db, user.company_id if hasattr(user, 'company_id') else 0, user, "reject_step", target_type, target_id)

    db.commit()
    return None


def _update_entity_status(db: Session, target_type: str, target_id: int, new_status: str):
    """Update the status field on the target entity."""
    model_map = {
        "admin_document": AdminDocument,
        "vehicle_purchase": VehiclePurchase,
        "vehicle_maintenance": VehicleMaintenance,
        "insurance_policy": InsurancePolicy,
        "stock_purchase": StockPurchase,
        "stock_requisition": StockRequisition,
        "stock_inbound": StockInbound,
        "stock_outbound": StockOutbound,
        "gift_purchase": StockGiftPurchase,
        "gift_requisition": StockGiftRequisition,
        "gift_inbound": StockGiftInbound,
        "gift_outbound": StockGiftOutbound,
    }
    model = model_map.get(target_type)
    if model is None:
        return
    entity = db.query(model).filter(model.id == target_id).first()
    if entity:
        entity.status = new_status
        db.commit()


def _submit_for_approval(db: Session, company_id: int, target_type: str, target_id: int, approver_ids: list[int], user: User):
    """Create approval records and update entity status."""
    # Delete any existing approval records for this target
    db.query(ApprovalRecord).filter(
        ApprovalRecord.target_type == target_type,
        ApprovalRecord.target_id == target_id,
    ).delete()

    for i, approver_id in enumerate(approver_ids, 1):
        approver = db.query(User).filter(User.id == approver_id).first()
        db.add(ApprovalRecord(
            company_id=company_id,
            target_type=target_type,
            target_id=target_id,
            step=i,
            approver_id=approver_id,
            approver_name=approver.username if approver else str(approver_id),
        ))

    _update_entity_status(db, target_type, target_id, "pending_approval")
    entity = None
    model_map = {
        "admin_document": AdminDocument,
        "vehicle_purchase": VehiclePurchase,
        "vehicle_maintenance": VehicleMaintenance,
        "insurance_policy": InsurancePolicy,
        "stock_purchase": StockPurchase,
        "stock_requisition": StockRequisition,
        "stock_inbound": StockInbound,
        "stock_outbound": StockOutbound,
        "gift_purchase": StockGiftPurchase,
        "gift_requisition": StockGiftRequisition,
        "gift_inbound": StockGiftInbound,
        "gift_outbound": StockGiftOutbound,
    }
    model = model_map.get(target_type)
    if model:
        entity = db.query(model).filter(model.id == target_id).first()
        if entity:
            entity.submit_date = date.today().isoformat()

    db.commit()
    _write_audit(db, company_id, user, "submit_approval", target_type, target_id)


def _get_company_id(user: User) -> int:
    """Extract company_id from user or its attributes."""
    # Try direct attribute first, then fall back to the auth login context
    if hasattr(user, 'company_id'):
        return user.company_id or 0
    return 0


# ── Approval Records ──

@router.get("/approvals/pending", response_model=list[ApprovalRecordResponse])
def list_pending_approvals(
    company_id: int = Query(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return db.query(ApprovalRecord).filter(
        ApprovalRecord.company_id == company_id,
        ApprovalRecord.approver_id == user.id,
        ApprovalRecord.status == "pending",
    ).order_by(ApprovalRecord.created_at.desc()).all()


@router.get("/approvals")
def list_approvals(
    company_id: int = Query(...),
    target_type: str = Query(...),
    target_id: int = Query(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return db.query(ApprovalRecord).filter(
        ApprovalRecord.company_id == company_id,
        ApprovalRecord.target_type == target_type,
        ApprovalRecord.target_id == target_id,
    ).order_by(ApprovalRecord.step).all()


@router.post("/approvals/{record_id}/approve")
def approve_step(
    record_id: int,
    body: ApprovalAction = ApprovalAction(),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    record = db.query(ApprovalRecord).filter(ApprovalRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    err = _process_approval(db, record.target_type, record.target_id, user, "approve", body.comment)
    if err:
        raise HTTPException(status_code=400, detail=err)
    return {"ok": True}


@router.post("/approvals/{record_id}/reject")
def reject_step(
    record_id: int,
    body: ApprovalAction = ApprovalAction(),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    record = db.query(ApprovalRecord).filter(ApprovalRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    err = _process_approval(db, record.target_type, record.target_id, user, "reject", body.comment)
    if err:
        raise HTTPException(status_code=400, detail=err)
    return {"ok": True}


@router.post("/{target_type}/{target_id}/bypass-step")
def bypass_admin_step(
    target_type: str,
    target_id: int,
    action: BypassAction,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """强制跳过行政审批当前步骤（仅管理员/财务总监）"""
    err = check_approval_bypass(user)
    if err:
        raise HTTPException(status_code=403, detail=err)

    records = db.query(ApprovalRecord).filter(
        ApprovalRecord.target_type == target_type,
        ApprovalRecord.target_id == target_id,
    ).order_by(ApprovalRecord.step).all()

    if not records:
        raise HTTPException(status_code=404, detail="审批记录不存在")

    current_step = None
    for r in records:
        if r.status == "pending":
            current_step = r
            break

    if current_step is None:
        raise HTTPException(status_code=400, detail="该审批流程已结束")

    current_step.status = "bypassed"
    current_step.comment = action.reason

    remaining = any(r.status == "pending" for r in records if r.step > current_step.step)
    if not remaining:
        _update_entity_status(db, target_type, target_id, "approved")

    _write_audit(db, 0, user, "bypass_step", target_type, target_id, action.reason)

    db.commit()
    return {"ok": True, "bypassed": True}


# ── Documents ──

@router.get("/documents", response_model=list[AdminDocumentResponse])
def list_documents(
    company_id: int = Query(...),
    status: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(AdminDocument).filter(AdminDocument.company_id == company_id)
    if status:
        q = q.filter(AdminDocument.status == status)
    return q.order_by(AdminDocument.created_at.desc()).all()


@router.post("/documents", response_model=AdminDocumentResponse)
def create_document(
    data: AdminDocumentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    doc = AdminDocument(**data.model_dump())
    db.add(doc)
    db.commit()
    db.refresh(doc)
    _write_audit(db, data.company_id, user, "create", "admin_document", doc.id)
    return doc


@router.put("/documents/{doc_id}", response_model=AdminDocumentResponse)
def update_document(
    doc_id: int,
    data: AdminDocumentUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    doc = db.query(AdminDocument).filter(AdminDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文件不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(doc, k, v)
    db.commit()
    db.refresh(doc)
    _write_audit(db, doc.company_id, user, "update", "admin_document", doc.id)
    return doc


@router.delete("/documents/{doc_id}")
def delete_document(
    doc_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    doc = db.query(AdminDocument).filter(AdminDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文件不存在")
    if doc.status != "draft":
        raise HTTPException(status_code=400, detail="只能删除草稿状态的文件")
    cid = doc.company_id
    db.delete(doc)
    db.commit()
    _write_audit(db, cid, user, "delete", "admin_document", doc_id)
    return {"ok": True}


@router.post("/documents/{doc_id}/submit")
def submit_document(
    doc_id: int,
    body: SubmitApprovalRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    doc = db.query(AdminDocument).filter(AdminDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文件不存在")
    if doc.status != "draft":
        raise HTTPException(status_code=400, detail="只能提交草稿状态的文件")
    if not body.approver_ids:
        raise HTTPException(status_code=400, detail="至少指定一位审批人")
    _submit_for_approval(db, doc.company_id, "admin_document", doc_id, body.approver_ids, user)
    return {"ok": True}


@router.post("/documents/{doc_id}/issue")
def issue_document(
    doc_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    doc = db.query(AdminDocument).filter(AdminDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文件不存在")
    if doc.status != "approved":
        raise HTTPException(status_code=400, detail="只有已审批的文件才能下发")
    doc.status = "issued"
    doc.issuance_date = date.today().isoformat()
    db.commit()
    _write_audit(db, doc.company_id, user, "issue", "admin_document", doc.id)
    return {"ok": True}


# ── Vehicle Suppliers ──

@router.get("/vehicles/suppliers", response_model=list[VehicleSupplierResponse])
def list_vehicle_suppliers(company_id: int = Query(...), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(VehicleSupplier).filter(VehicleSupplier.company_id == company_id).order_by(VehicleSupplier.name).all()

@router.post("/vehicles/suppliers", response_model=VehicleSupplierResponse)
def create_vehicle_supplier(data: VehicleSupplierCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    s = VehicleSupplier(**data.model_dump())
    db.add(s)
    db.commit()
    db.refresh(s)
    return s

@router.put("/vehicles/suppliers/{sid}", response_model=VehicleSupplierResponse)
def update_vehicle_supplier(sid: int, data: VehicleSupplierUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    s = db.query(VehicleSupplier).filter(VehicleSupplier.id == sid).first()
    if not s:
        raise HTTPException(status_code=404, detail="供应商不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(s, k, v)
    db.commit()
    db.refresh(s)
    return s

@router.delete("/vehicles/suppliers/{sid}")
def delete_vehicle_supplier(sid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    s = db.query(VehicleSupplier).filter(VehicleSupplier.id == sid).first()
    if not s:
        raise HTTPException(status_code=404, detail="供应商不存在")
    db.delete(s)
    db.commit()
    return {"ok": True}


# ── Vehicle Purchases ──

@router.get("/vehicles/purchases", response_model=list[VehiclePurchaseResponse])
def list_vehicle_purchases(company_id: int = Query(...), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(VehiclePurchase).filter(VehiclePurchase.company_id == company_id).order_by(VehiclePurchase.created_at.desc()).all()

@router.post("/vehicles/purchases", response_model=VehiclePurchaseResponse)
def create_vehicle_purchase(data: VehiclePurchaseCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    vp = VehiclePurchase(**data.model_dump())
    db.add(vp)
    db.commit()
    db.refresh(vp)
    _write_audit(db, data.company_id, user, "create", "vehicle_purchase", vp.id)
    return vp

@router.put("/vehicles/purchases/{pid}", response_model=VehiclePurchaseResponse)
def update_vehicle_purchase(pid: int, data: VehiclePurchaseUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    vp = db.query(VehiclePurchase).filter(VehiclePurchase.id == pid).first()
    if not vp:
        raise HTTPException(status_code=404, detail="采购申请不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(vp, k, v)
    db.commit()
    db.refresh(vp)
    return vp

@router.delete("/vehicles/purchases/{pid}")
def delete_vehicle_purchase(pid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    vp = db.query(VehiclePurchase).filter(VehiclePurchase.id == pid).first()
    if not vp:
        raise HTTPException(status_code=404, detail="采购申请不存在")
    if vp.status != "draft":
        raise HTTPException(status_code=400, detail="只能删除草稿状态")
    cid = vp.company_id
    db.delete(vp)
    db.commit()
    _write_audit(db, cid, user, "delete", "vehicle_purchase", pid)
    return {"ok": True}

@router.post("/vehicles/purchases/{pid}/submit")
def submit_vehicle_purchase(pid: int, body: SubmitApprovalRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    vp = db.query(VehiclePurchase).filter(VehiclePurchase.id == pid).first()
    if not vp:
        raise HTTPException(status_code=404, detail="采购申请不存在")
    if vp.status != "draft":
        raise HTTPException(status_code=400, detail="只能提交草稿状态")
    if not body.approver_ids:
        raise HTTPException(status_code=400, detail="至少指定一位审批人")
    _submit_for_approval(db, vp.company_id, "vehicle_purchase", pid, body.approver_ids, user)
    return {"ok": True}


# ── Vehicles ──

@router.get("/vehicles", response_model=list[VehicleResponse])
def list_vehicles(company_id: int = Query(...), status: str | None = Query(None), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q = db.query(Vehicle).filter(Vehicle.company_id == company_id)
    if status:
        q = q.filter(Vehicle.status == status)
    return q.order_by(Vehicle.license_plate).all()

@router.post("/vehicles", response_model=VehicleResponse)
def create_vehicle(data: VehicleCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    v = Vehicle(**data.model_dump())
    db.add(v)
    db.commit()
    db.refresh(v)
    _write_audit(db, data.company_id, user, "create", "vehicle", v.id)
    return v

@router.put("/vehicles/{vid}", response_model=VehicleResponse)
def update_vehicle(vid: int, data: VehicleUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    v = db.query(Vehicle).filter(Vehicle.id == vid).first()
    if not v:
        raise HTTPException(status_code=404, detail="车辆不存在")
    for k, val in data.model_dump(exclude_unset=True).items():
        setattr(v, k, val)
    db.commit()
    db.refresh(v)
    _write_audit(db, v.company_id, user, "update", "vehicle", v.id)
    return v

@router.delete("/vehicles/{vid}")
def delete_vehicle(vid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    v = db.query(Vehicle).filter(Vehicle.id == vid).first()
    if not v:
        raise HTTPException(status_code=404, detail="车辆不存在")
    cid = v.company_id
    db.delete(v)
    db.commit()
    _write_audit(db, cid, user, "delete", "vehicle", vid)
    return {"ok": True}


# ── Vehicle Maintenance ──

@router.get("/vehicles/maintenance", response_model=list[VehicleMaintenanceResponse])
def list_vehicle_maintenance(company_id: int = Query(...), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(VehicleMaintenance).filter(VehicleMaintenance.company_id == company_id).order_by(VehicleMaintenance.created_at.desc()).all()

@router.post("/vehicles/maintenance", response_model=VehicleMaintenanceResponse)
def create_vehicle_maintenance(data: VehicleMaintenanceCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    vm = VehicleMaintenance(**data.model_dump())
    db.add(vm)
    db.commit()
    db.refresh(vm)
    _write_audit(db, data.company_id, user, "create", "vehicle_maintenance", vm.id)
    return vm

@router.put("/vehicles/maintenance/{mid}", response_model=VehicleMaintenanceResponse)
def update_vehicle_maintenance(mid: int, data: VehicleMaintenanceUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    vm = db.query(VehicleMaintenance).filter(VehicleMaintenance.id == mid).first()
    if not vm:
        raise HTTPException(status_code=404, detail="维保申请不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(vm, k, v)
    db.commit()
    db.refresh(vm)
    return vm

@router.delete("/vehicles/maintenance/{mid}")
def delete_vehicle_maintenance(mid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    vm = db.query(VehicleMaintenance).filter(VehicleMaintenance.id == mid).first()
    if not vm:
        raise HTTPException(status_code=404, detail="维保申请不存在")
    if vm.status != "draft":
        raise HTTPException(status_code=400, detail="只能删除草稿状态")
    cid = vm.company_id
    db.delete(vm)
    db.commit()
    _write_audit(db, cid, user, "delete", "vehicle_maintenance", mid)
    return {"ok": True}

@router.post("/vehicles/maintenance/{mid}/submit")
def submit_vehicle_maintenance(mid: int, body: SubmitApprovalRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    vm = db.query(VehicleMaintenance).filter(VehicleMaintenance.id == mid).first()
    if not vm:
        raise HTTPException(status_code=404, detail="维保申请不存在")
    if vm.status != "draft":
        raise HTTPException(status_code=400, detail="只能提交草稿状态")
    if not body.approver_ids:
        raise HTTPException(status_code=400, detail="至少指定一位审批人")
    _submit_for_approval(db, vm.company_id, "vehicle_maintenance", mid, body.approver_ids, user)
    return {"ok": True}


# ── Insurance ──

@router.get("/insurance", response_model=list[InsurancePolicyResponse])
def list_insurance(company_id: int = Query(...), status: str | None = Query(None), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q = db.query(InsurancePolicy).filter(InsurancePolicy.company_id == company_id)
    if status:
        q = q.filter(InsurancePolicy.status == status)
    return q.order_by(InsurancePolicy.created_at.desc()).all()

@router.post("/insurance", response_model=InsurancePolicyResponse)
def create_insurance(data: InsurancePolicyCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ip = InsurancePolicy(**data.model_dump())
    db.add(ip)
    db.commit()
    db.refresh(ip)
    _write_audit(db, data.company_id, user, "create", "insurance_policy", ip.id)
    return ip

@router.put("/insurance/{iid}", response_model=InsurancePolicyResponse)
def update_insurance(iid: int, data: InsurancePolicyUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ip = db.query(InsurancePolicy).filter(InsurancePolicy.id == iid).first()
    if not ip:
        raise HTTPException(status_code=404, detail="保单不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(ip, k, v)
    db.commit()
    db.refresh(ip)
    return ip

@router.delete("/insurance/{iid}")
def delete_insurance(iid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ip = db.query(InsurancePolicy).filter(InsurancePolicy.id == iid).first()
    if not ip:
        raise HTTPException(status_code=404, detail="保单不存在")
    if ip.status != "draft":
        raise HTTPException(status_code=400, detail="只能删除草稿状态")
    cid = ip.company_id
    db.delete(ip)
    db.commit()
    _write_audit(db, cid, user, "delete", "insurance_policy", iid)
    return {"ok": True}

@router.post("/insurance/{iid}/submit")
def submit_insurance(iid: int, body: SubmitApprovalRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ip = db.query(InsurancePolicy).filter(InsurancePolicy.id == iid).first()
    if not ip:
        raise HTTPException(status_code=404, detail="保单不存在")
    if ip.status != "draft":
        raise HTTPException(status_code=400, detail="只能提交草稿状态")
    if not body.approver_ids:
        raise HTTPException(status_code=400, detail="至少指定一位审批人")
    _submit_for_approval(db, ip.company_id, "insurance_policy", iid, body.approver_ids, user)
    return {"ok": True}

@router.get("/insurance/expiring", response_model=list[InsurancePolicyResponse])
def list_expiring_insurance(company_id: int = Query(...), days: int = Query(30), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    date.today().isoformat()
    all_active = db.query(InsurancePolicy).filter(
        InsurancePolicy.company_id == company_id,
        InsurancePolicy.status == "active",
    ).all()
    from datetime import timedelta
    cutoff = (date.today() + timedelta(days=days)).isoformat()
    return [p for p in all_active if p.end_date <= cutoff]


# ── Stock Categories ──

@router.get("/stock/categories", response_model=list[StockCategoryResponse])
def list_stock_categories(company_id: int = Query(...), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(StockCategory).filter(StockCategory.company_id == company_id, StockCategory.is_active).order_by(StockCategory.code).all()

@router.post("/stock/categories", response_model=StockCategoryResponse)
def create_stock_category(data: StockCategoryCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    c = StockCategory(**data.model_dump())
    db.add(c)
    db.commit()
    db.refresh(c)
    return c

@router.put("/stock/categories/{cid}", response_model=StockCategoryResponse)
def update_stock_category(cid: int, data: StockCategoryUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    c = db.query(StockCategory).filter(StockCategory.id == cid).first()
    if not c:
        raise HTTPException(status_code=404, detail="类别不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(c, k, v)
    db.commit()
    db.refresh(c)
    return c

@router.delete("/stock/categories/{cid}")
def delete_stock_category(cid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    c = db.query(StockCategory).filter(StockCategory.id == cid).first()
    if not c:
        raise HTTPException(status_code=404, detail="类别不存在")
    c.is_active = False
    db.commit()
    return {"ok": True}


# ── Stock Assets ──

@router.get("/stock/assets", response_model=list[StockAssetResponse])
def list_stock_assets(company_id: int = Query(...), status: str | None = Query(None), category_id: int | None = Query(None), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q = db.query(StockAsset).filter(StockAsset.company_id == company_id)
    if status:
        q = q.filter(StockAsset.status == status)
    if category_id is not None:
        q = q.filter(StockAsset.category_id == category_id)
    return q.order_by(StockAsset.asset_code).all()

@router.post("/stock/assets", response_model=StockAssetResponse)
def create_stock_asset(data: StockAssetCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    a = StockAsset(**data.model_dump())
    db.add(a)
    db.commit()
    db.refresh(a)
    _write_audit(db, data.company_id, user, "create", "stock_asset", a.id)
    return a

@router.put("/stock/assets/{aid}", response_model=StockAssetResponse)
def update_stock_asset(aid: int, data: StockAssetUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    a = db.query(StockAsset).filter(StockAsset.id == aid).first()
    if not a:
        raise HTTPException(status_code=404, detail="资产不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(a, k, v)
    db.commit()
    db.refresh(a)
    return a

@router.delete("/stock/assets/{aid}")
def delete_stock_asset(aid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    a = db.query(StockAsset).filter(StockAsset.id == aid).first()
    if not a:
        raise HTTPException(status_code=404, detail="资产不存在")
    cid = a.company_id
    db.delete(a)
    db.commit()
    _write_audit(db, cid, user, "delete", "stock_asset", aid)
    return {"ok": True}


# ── Stock Purchases ──

@router.get("/stock/assets/purchases", response_model=list[StockPurchaseResponse])
def list_stock_purchases(company_id: int = Query(...), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(StockPurchase).filter(StockPurchase.company_id == company_id).order_by(StockPurchase.created_at.desc()).all()

@router.post("/stock/assets/purchases", response_model=StockPurchaseResponse)
def create_stock_purchase(data: StockPurchaseCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    sp = StockPurchase(**data.model_dump())
    db.add(sp)
    db.commit()
    db.refresh(sp)
    _write_audit(db, data.company_id, user, "create", "stock_purchase", sp.id)
    return sp

@router.put("/stock/assets/purchases/{pid}", response_model=StockPurchaseResponse)
def update_stock_purchase(pid: int, data: StockPurchaseUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    sp = db.query(StockPurchase).filter(StockPurchase.id == pid).first()
    if not sp:
        raise HTTPException(status_code=404, detail="采购申请不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(sp, k, v)
    db.commit()
    db.refresh(sp)
    return sp

@router.delete("/stock/assets/purchases/{pid}")
def delete_stock_purchase(pid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    sp = db.query(StockPurchase).filter(StockPurchase.id == pid).first()
    if not sp:
        raise HTTPException(status_code=404, detail="采购申请不存在")
    if sp.status != "draft":
        raise HTTPException(status_code=400, detail="只能删除草稿状态")
    cid = sp.company_id
    db.delete(sp)
    db.commit()
    _write_audit(db, cid, user, "delete", "stock_purchase", pid)
    return {"ok": True}

@router.post("/stock/assets/purchases/{pid}/submit")
def submit_stock_purchase(pid: int, body: SubmitApprovalRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    sp = db.query(StockPurchase).filter(StockPurchase.id == pid).first()
    if not sp:
        raise HTTPException(status_code=404, detail="采购申请不存在")
    if sp.status != "draft":
        raise HTTPException(status_code=400, detail="只能提交草稿状态")
    if not body.approver_ids:
        raise HTTPException(status_code=400, detail="至少指定一位审批人")
    _submit_for_approval(db, sp.company_id, "stock_purchase", pid, body.approver_ids, user)
    return {"ok": True}


# ── Stock Requisitions ──

@router.get("/stock/assets/requisitions", response_model=list[StockRequisitionResponse])
def list_stock_requisitions(company_id: int = Query(...), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(StockRequisition).filter(StockRequisition.company_id == company_id).order_by(StockRequisition.created_at.desc()).all()

@router.post("/stock/assets/requisitions", response_model=StockRequisitionResponse)
def create_stock_requisition(data: StockRequisitionCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    sr = StockRequisition(**data.model_dump())
    db.add(sr)
    db.commit()
    db.refresh(sr)
    _write_audit(db, data.company_id, user, "create", "stock_requisition", sr.id)
    return sr

@router.put("/stock/assets/requisitions/{rid}", response_model=StockRequisitionResponse)
def update_stock_requisition(rid: int, data: StockRequisitionUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    sr = db.query(StockRequisition).filter(StockRequisition.id == rid).first()
    if not sr:
        raise HTTPException(status_code=404, detail="领用申请不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(sr, k, v)
    db.commit()
    db.refresh(sr)
    return sr

@router.delete("/stock/assets/requisitions/{rid}")
def delete_stock_requisition(rid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    sr = db.query(StockRequisition).filter(StockRequisition.id == rid).first()
    if not sr:
        raise HTTPException(status_code=404, detail="领用申请不存在")
    if sr.status != "draft":
        raise HTTPException(status_code=400, detail="只能删除草稿状态")
    cid = sr.company_id
    db.delete(sr)
    db.commit()
    _write_audit(db, cid, user, "delete", "stock_requisition", rid)
    return {"ok": True}

@router.post("/stock/assets/requisitions/{rid}/submit")
def submit_stock_requisition(rid: int, body: SubmitApprovalRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    sr = db.query(StockRequisition).filter(StockRequisition.id == rid).first()
    if not sr:
        raise HTTPException(status_code=404, detail="领用申请不存在")
    if sr.status != "draft":
        raise HTTPException(status_code=400, detail="只能提交草稿状态")
    if not body.approver_ids:
        raise HTTPException(status_code=400, detail="至少指定一位审批人")
    _submit_for_approval(db, sr.company_id, "stock_requisition", rid, body.approver_ids, user)
    return {"ok": True}


# ── Stock Inbound ──

@router.get("/stock/assets/inbound", response_model=list[StockInboundResponse])
def list_stock_inbound(company_id: int = Query(...), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(StockInbound).filter(StockInbound.company_id == company_id).order_by(StockInbound.created_at.desc()).all()

@router.post("/stock/assets/inbound", response_model=StockInboundResponse)
def create_stock_inbound(data: StockInboundCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    si = StockInbound(**data.model_dump())
    db.add(si)
    db.commit()
    db.refresh(si)
    _write_audit(db, data.company_id, user, "create", "stock_inbound", si.id)
    return si

@router.put("/stock/assets/inbound/{iid}", response_model=StockInboundResponse)
def update_stock_inbound(iid: int, data: StockInboundUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    si = db.query(StockInbound).filter(StockInbound.id == iid).first()
    if not si:
        raise HTTPException(status_code=404, detail="入库记录不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(si, k, v)
    db.commit()
    db.refresh(si)
    return si

@router.delete("/stock/assets/inbound/{iid}")
def delete_stock_inbound(iid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    si = db.query(StockInbound).filter(StockInbound.id == iid).first()
    if not si:
        raise HTTPException(status_code=404, detail="入库记录不存在")
    if si.status != "draft":
        raise HTTPException(status_code=400, detail="只能删除草稿状态")
    cid = si.company_id
    db.delete(si)
    db.commit()
    _write_audit(db, cid, user, "delete", "stock_inbound", iid)
    return {"ok": True}

@router.post("/stock/assets/inbound/{iid}/submit")
def submit_stock_inbound(iid: int, body: SubmitApprovalRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    si = db.query(StockInbound).filter(StockInbound.id == iid).first()
    if not si:
        raise HTTPException(status_code=404, detail="入库记录不存在")
    if si.status != "draft":
        raise HTTPException(status_code=400, detail="只能提交草稿状态")
    if not body.approver_ids:
        raise HTTPException(status_code=400, detail="至少指定一位审批人")
    _submit_for_approval(db, si.company_id, "stock_inbound", iid, body.approver_ids, user)
    return {"ok": True}


# ── Stock Outbound ──

@router.get("/stock/assets/outbound", response_model=list[StockOutboundResponse])
def list_stock_outbound(company_id: int = Query(...), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(StockOutbound).filter(StockOutbound.company_id == company_id).order_by(StockOutbound.created_at.desc()).all()

@router.post("/stock/assets/outbound", response_model=StockOutboundResponse)
def create_stock_outbound(data: StockOutboundCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    so = StockOutbound(**data.model_dump())
    db.add(so)
    db.commit()
    db.refresh(so)
    _write_audit(db, data.company_id, user, "create", "stock_outbound", so.id)
    return so

@router.put("/stock/assets/outbound/{oid}", response_model=StockOutboundResponse)
def update_stock_outbound(oid: int, data: StockOutboundUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    so = db.query(StockOutbound).filter(StockOutbound.id == oid).first()
    if not so:
        raise HTTPException(status_code=404, detail="出库记录不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(so, k, v)
    db.commit()
    db.refresh(so)
    return so

@router.delete("/stock/assets/outbound/{oid}")
def delete_stock_outbound(oid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    so = db.query(StockOutbound).filter(StockOutbound.id == oid).first()
    if not so:
        raise HTTPException(status_code=404, detail="出库记录不存在")
    if so.status != "draft":
        raise HTTPException(status_code=400, detail="只能删除草稿状态")
    cid = so.company_id
    db.delete(so)
    db.commit()
    _write_audit(db, cid, user, "delete", "stock_outbound", oid)
    return {"ok": True}

@router.post("/stock/assets/outbound/{oid}/submit")
def submit_stock_outbound(oid: int, body: SubmitApprovalRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    so = db.query(StockOutbound).filter(StockOutbound.id == oid).first()
    if not so:
        raise HTTPException(status_code=404, detail="出库记录不存在")
    if so.status != "draft":
        raise HTTPException(status_code=400, detail="只能提交草稿状态")
    if not body.approver_ids:
        raise HTTPException(status_code=400, detail="至少指定一位审批人")
    _submit_for_approval(db, so.company_id, "stock_outbound", oid, body.approver_ids, user)
    return {"ok": True}


# ── Stock Counts ──

@router.get("/stock/assets/counts", response_model=list[StockCountResponse])
def list_stock_counts(company_id: int = Query(...), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(StockCount).filter(StockCount.company_id == company_id).order_by(StockCount.count_date.desc()).all()

@router.post("/stock/assets/counts", response_model=StockCountResponse)
def create_stock_count(data: StockCountCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    sc = StockCount(**data.model_dump())
    db.add(sc)
    db.commit()
    db.refresh(sc)
    _write_audit(db, data.company_id, user, "create", "stock_count", sc.id)
    return sc

@router.put("/stock/assets/counts/{cid}", response_model=StockCountResponse)
def update_stock_count(cid: int, data: StockCountUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    sc = db.query(StockCount).filter(StockCount.id == cid).first()
    if not sc:
        raise HTTPException(status_code=404, detail="盘库记录不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(sc, k, v)
    db.commit()
    db.refresh(sc)
    return sc

@router.delete("/stock/assets/counts/{cid}")
def delete_stock_count(cid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    sc = db.query(StockCount).filter(StockCount.id == cid).first()
    if not sc:
        raise HTTPException(status_code=404, detail="盘库记录不存在")
    cid_val = sc.company_id
    db.delete(sc)
    db.commit()
    _write_audit(db, cid_val, user, "delete", "stock_count", cid)
    return {"ok": True}


# ── Gift Categories ──

@router.get("/stock/gifts/categories", response_model=list[GiftCategoryResponse])
def list_gift_categories(company_id: int = Query(...), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(GiftCategory).filter(GiftCategory.company_id == company_id, GiftCategory.is_active).order_by(GiftCategory.name).all()

@router.post("/stock/gifts/categories", response_model=GiftCategoryResponse)
def create_gift_category(data: GiftCategoryCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    c = GiftCategory(**data.model_dump())
    db.add(c)
    db.commit()
    db.refresh(c)
    return c

@router.put("/stock/gifts/categories/{cid}", response_model=GiftCategoryResponse)
def update_gift_category(cid: int, data: GiftCategoryUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    c = db.query(GiftCategory).filter(GiftCategory.id == cid).first()
    if not c:
        raise HTTPException(status_code=404, detail="类别不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(c, k, v)
    db.commit()
    db.refresh(c)
    return c

@router.delete("/stock/gifts/categories/{cid}")
def delete_gift_category(cid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    c = db.query(GiftCategory).filter(GiftCategory.id == cid).first()
    if not c:
        raise HTTPException(status_code=404, detail="类别不存在")
    c.is_active = False
    db.commit()
    return {"ok": True}


# ── Stock Gifts ──

@router.get("/stock/gifts", response_model=list[StockGiftResponse])
def list_stock_gifts(company_id: int = Query(...), category_id: int | None = Query(None), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q = db.query(StockGift).filter(StockGift.company_id == company_id)
    if category_id is not None:
        q = q.filter(StockGift.category_id == category_id)
    return q.order_by(StockGift.name).all()

@router.post("/stock/gifts", response_model=StockGiftResponse)
def create_stock_gift(data: StockGiftCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    g = StockGift(**data.model_dump())
    db.add(g)
    db.commit()
    db.refresh(g)
    _write_audit(db, data.company_id, user, "create", "stock_gift", g.id)
    return g

@router.put("/stock/gifts/{gid}", response_model=StockGiftResponse)
def update_stock_gift(gid: int, data: StockGiftUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    g = db.query(StockGift).filter(StockGift.id == gid).first()
    if not g:
        raise HTTPException(status_code=404, detail="礼品不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(g, k, v)
    db.commit()
    db.refresh(g)
    return g

@router.delete("/stock/gifts/{gid}")
def delete_stock_gift(gid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    g = db.query(StockGift).filter(StockGift.id == gid).first()
    if not g:
        raise HTTPException(status_code=404, detail="礼品不存在")
    cid = g.company_id
    db.delete(g)
    db.commit()
    _write_audit(db, cid, user, "delete", "stock_gift", gid)
    return {"ok": True}


# ── Gift Purchases ──

@router.get("/stock/gifts/purchases", response_model=list[StockGiftPurchaseResponse])
def list_gift_purchases(company_id: int = Query(...), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(StockGiftPurchase).filter(StockGiftPurchase.company_id == company_id).order_by(StockGiftPurchase.created_at.desc()).all()

@router.post("/stock/gifts/purchases", response_model=StockGiftPurchaseResponse)
def create_gift_purchase(data: StockGiftPurchaseCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    gp = StockGiftPurchase(**data.model_dump())
    db.add(gp)
    db.commit()
    db.refresh(gp)
    _write_audit(db, data.company_id, user, "create", "gift_purchase", gp.id)
    return gp

@router.put("/stock/gifts/purchases/{pid}", response_model=StockGiftPurchaseResponse)
def update_gift_purchase(pid: int, data: StockGiftPurchaseUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    gp = db.query(StockGiftPurchase).filter(StockGiftPurchase.id == pid).first()
    if not gp:
        raise HTTPException(status_code=404, detail="采购申请不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(gp, k, v)
    db.commit()
    db.refresh(gp)
    return gp

@router.delete("/stock/gifts/purchases/{pid}")
def delete_gift_purchase(pid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    gp = db.query(StockGiftPurchase).filter(StockGiftPurchase.id == pid).first()
    if not gp:
        raise HTTPException(status_code=404, detail="采购申请不存在")
    if gp.status != "draft":
        raise HTTPException(status_code=400, detail="只能删除草稿状态")
    cid = gp.company_id
    db.delete(gp)
    db.commit()
    _write_audit(db, cid, user, "delete", "gift_purchase", pid)
    return {"ok": True}

@router.post("/stock/gifts/purchases/{pid}/submit")
def submit_gift_purchase(pid: int, body: SubmitApprovalRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    gp = db.query(StockGiftPurchase).filter(StockGiftPurchase.id == pid).first()
    if not gp:
        raise HTTPException(status_code=404, detail="采购申请不存在")
    if gp.status != "draft":
        raise HTTPException(status_code=400, detail="只能提交草稿状态")
    if not body.approver_ids:
        raise HTTPException(status_code=400, detail="至少指定一位审批人")
    _submit_for_approval(db, gp.company_id, "gift_purchase", pid, body.approver_ids, user)
    return {"ok": True}


# ── Gift Requisitions ──

@router.get("/stock/gifts/requisitions", response_model=list[StockGiftRequisitionResponse])
def list_gift_requisitions(company_id: int = Query(...), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(StockGiftRequisition).filter(StockGiftRequisition.company_id == company_id).order_by(StockGiftRequisition.created_at.desc()).all()

@router.post("/stock/gifts/requisitions", response_model=StockGiftRequisitionResponse)
def create_gift_requisition(data: StockGiftRequisitionCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    gr = StockGiftRequisition(**data.model_dump())
    db.add(gr)
    db.commit()
    db.refresh(gr)
    _write_audit(db, data.company_id, user, "create", "gift_requisition", gr.id)
    return gr

@router.put("/stock/gifts/requisitions/{rid}", response_model=StockGiftRequisitionResponse)
def update_gift_requisition(rid: int, data: StockGiftRequisitionUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    gr = db.query(StockGiftRequisition).filter(StockGiftRequisition.id == rid).first()
    if not gr:
        raise HTTPException(status_code=404, detail="领用申请不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(gr, k, v)
    db.commit()
    db.refresh(gr)
    return gr

@router.delete("/stock/gifts/requisitions/{rid}")
def delete_gift_requisition(rid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    gr = db.query(StockGiftRequisition).filter(StockGiftRequisition.id == rid).first()
    if not gr:
        raise HTTPException(status_code=404, detail="领用申请不存在")
    if gr.status != "draft":
        raise HTTPException(status_code=400, detail="只能删除草稿状态")
    cid = gr.company_id
    db.delete(gr)
    db.commit()
    _write_audit(db, cid, user, "delete", "gift_requisition", rid)
    return {"ok": True}

@router.post("/stock/gifts/requisitions/{rid}/submit")
def submit_gift_requisition(rid: int, body: SubmitApprovalRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    gr = db.query(StockGiftRequisition).filter(StockGiftRequisition.id == rid).first()
    if not gr:
        raise HTTPException(status_code=404, detail="领用申请不存在")
    if gr.status != "draft":
        raise HTTPException(status_code=400, detail="只能提交草稿状态")
    if not body.approver_ids:
        raise HTTPException(status_code=400, detail="至少指定一位审批人")
    _submit_for_approval(db, gr.company_id, "gift_requisition", rid, body.approver_ids, user)
    return {"ok": True}


# ── Gift Inbound ──

@router.get("/stock/gifts/inbound", response_model=list[StockGiftInboundResponse])
def list_gift_inbound(company_id: int = Query(...), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(StockGiftInbound).filter(StockGiftInbound.company_id == company_id).order_by(StockGiftInbound.created_at.desc()).all()

@router.post("/stock/gifts/inbound", response_model=StockGiftInboundResponse)
def create_gift_inbound(data: StockGiftInboundCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    gi = StockGiftInbound(**data.model_dump())
    db.add(gi)
    db.commit()
    db.refresh(gi)
    _write_audit(db, data.company_id, user, "create", "gift_inbound", gi.id)
    return gi

@router.put("/stock/gifts/inbound/{iid}", response_model=StockGiftInboundResponse)
def update_gift_inbound(iid: int, data: StockGiftInboundUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    gi = db.query(StockGiftInbound).filter(StockGiftInbound.id == iid).first()
    if not gi:
        raise HTTPException(status_code=404, detail="入库记录不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(gi, k, v)
    db.commit()
    db.refresh(gi)
    return gi

@router.delete("/stock/gifts/inbound/{iid}")
def delete_gift_inbound(iid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    gi = db.query(StockGiftInbound).filter(StockGiftInbound.id == iid).first()
    if not gi:
        raise HTTPException(status_code=404, detail="入库记录不存在")
    if gi.status != "draft":
        raise HTTPException(status_code=400, detail="只能删除草稿状态")
    cid = gi.company_id
    db.delete(gi)
    db.commit()
    _write_audit(db, cid, user, "delete", "gift_inbound", iid)
    return {"ok": True}

@router.post("/stock/gifts/inbound/{iid}/submit")
def submit_gift_inbound(iid: int, body: SubmitApprovalRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    gi = db.query(StockGiftInbound).filter(StockGiftInbound.id == iid).first()
    if not gi:
        raise HTTPException(status_code=404, detail="入库记录不存在")
    if gi.status != "draft":
        raise HTTPException(status_code=400, detail="只能提交草稿状态")
    if not body.approver_ids:
        raise HTTPException(status_code=400, detail="至少指定一位审批人")
    _submit_for_approval(db, gi.company_id, "gift_inbound", iid, body.approver_ids, user)
    return {"ok": True}


# ── Gift Outbound ──

@router.get("/stock/gifts/outbound", response_model=list[StockGiftOutboundResponse])
def list_gift_outbound(company_id: int = Query(...), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(StockGiftOutbound).filter(StockGiftOutbound.company_id == company_id).order_by(StockGiftOutbound.created_at.desc()).all()

@router.post("/stock/gifts/outbound", response_model=StockGiftOutboundResponse)
def create_gift_outbound(data: StockGiftOutboundCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    go = StockGiftOutbound(**data.model_dump())
    db.add(go)
    db.commit()
    db.refresh(go)
    _write_audit(db, data.company_id, user, "create", "gift_outbound", go.id)
    return go

@router.put("/stock/gifts/outbound/{oid}", response_model=StockGiftOutboundResponse)
def update_gift_outbound(oid: int, data: StockGiftOutboundUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    go = db.query(StockGiftOutbound).filter(StockGiftOutbound.id == oid).first()
    if not go:
        raise HTTPException(status_code=404, detail="出库记录不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(go, k, v)
    db.commit()
    db.refresh(go)
    return go

@router.delete("/stock/gifts/outbound/{oid}")
def delete_gift_outbound(oid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    go = db.query(StockGiftOutbound).filter(StockGiftOutbound.id == oid).first()
    if not go:
        raise HTTPException(status_code=404, detail="出库记录不存在")
    if go.status != "draft":
        raise HTTPException(status_code=400, detail="只能删除草稿状态")
    cid = go.company_id
    db.delete(go)
    db.commit()
    _write_audit(db, cid, user, "delete", "gift_outbound", oid)
    return {"ok": True}

@router.post("/stock/gifts/outbound/{oid}/submit")
def submit_gift_outbound(oid: int, body: SubmitApprovalRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    go = db.query(StockGiftOutbound).filter(StockGiftOutbound.id == oid).first()
    if not go:
        raise HTTPException(status_code=404, detail="出库记录不存在")
    if go.status != "draft":
        raise HTTPException(status_code=400, detail="只能提交草稿状态")
    if not body.approver_ids:
        raise HTTPException(status_code=400, detail="至少指定一位审批人")
    _submit_for_approval(db, go.company_id, "gift_outbound", oid, body.approver_ids, user)
    return {"ok": True}
