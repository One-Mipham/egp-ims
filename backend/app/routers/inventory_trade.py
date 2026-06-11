"""进销存管理 — 采购/销售/库存 CRUD + 主数据 + 联动 + 审计 + 凭证."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user
from app.models import (
    InvPurchase, InvSale, InvStock,
    Warehouse, Inventory, InventoryCategory, UnitOfMeasure,
    Voucher, VoucherEntry, AuditLog,
    User,
)
from app.schemas import (
    InvPurchaseCreate, InvPurchaseResponse,
    InvSaleCreate, InvSaleResponse,
    InvStockCreate, InvStockResponse,
    WarehouseCreate, WarehouseResponse,
    InventoryCreate, InventoryResponse,
    InventoryCategoryCreate, InventoryCategoryResponse,
    UnitOfMeasureCreate, UnitOfMeasureResponse,
)

router = APIRouter()


# ═══════════ 审计辅助 ═══════════

def _audit(db: Session, user: User, action: str, target_type: str, target_id: int | None = None, details: dict | None = None):
    db.add(AuditLog(
        company_id=user.company_id if hasattr(user, 'company_id') else 1,
        user_id=user.id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
        created_at=datetime.utcnow(),
    ))


# ═══════════ 凭证生成 ═══════════

def _generate_voucher(db: Session, company_id: int, user_id: int, vtype: str, summary: str, entries: list[dict]):
    """生成会计凭证。entries: [{account_code, debit, credit, description}]"""
    date = datetime.utcnow().strftime("%Y-%m-%d")
    voucher_no = f"{vtype}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    voucher = Voucher(
        company_id=company_id,
        date=date,
        voucher_no=voucher_no,
        voucher_type=vtype,
        summary=summary,
        creator_id=user_id,
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


# ═══════════ Purchases ═══════════════════════

@router.get("/purchases", response_model=list[InvPurchaseResponse])
def list_purchases(
    company_id: int,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    status: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(InvPurchase).filter(InvPurchase.company_id == company_id)
    if status:
        q = q.filter(InvPurchase.status == status)
    if start_date:
        q = q.filter(InvPurchase.order_date >= start_date)
    if end_date:
        q = q.filter(InvPurchase.order_date <= end_date)
    if search:
        pattern = f"%{search}%"
        q = q.filter(
            (InvPurchase.order_no.ilike(pattern)) |
            (InvPurchase.supplier_name.ilike(pattern)) |
            (InvPurchase.product_name.ilike(pattern))
        )
    return q.order_by(InvPurchase.id.desc()).offset(offset).limit(limit).all()


@router.post("/purchases", response_model=InvPurchaseResponse)
def create_purchase(data: InvPurchaseCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if data.quantity <= 0:
        raise HTTPException(status_code=400, detail="数量必须大于0")
    if data.unit_price < 0:
        raise HTTPException(status_code=400, detail="单价不能为负数")
    item = InvPurchase(**data.model_dump())
    db.add(item); db.commit(); db.refresh(item)
    _audit(db, user, "create", "purchase", item.id, {"order_no": item.order_no, "amount": item.total_amount})
    db.commit()
    return item


@router.put("/purchases/{id}", response_model=InvPurchaseResponse)
def update_purchase(id: int, data: InvPurchaseCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(InvPurchase).filter(InvPurchase.id == id).first()
    if not item: raise HTTPException(status_code=404, detail="采购单不存在")
    old_status = item.status
    for k, v in data.model_dump(exclude_unset=True).items(): setattr(item, k, v)
    # 入库联动 + 生成凭证
    if old_status != "已入库" and item.status == "已入库":
        _purchase_to_stock(item, db)
        _generate_voucher(db, item.company_id, user.id, "transfer", f"采购入库 {item.order_no} {item.product_name}", [
            {"account_code": "1405", "debit": item.total_amount, "credit": 0, "description": f"库存商品 {item.product_name}"},
            {"account_code": "2202", "debit": 0, "credit": item.total_amount, "description": f"应付账款 {item.supplier_name}"},
        ])
        _audit(db, user, "post", "purchase_inbound", item.id, {"order_no": item.order_no, "amount": item.total_amount, "product": item.product_name})
    _audit(db, user, "update", "purchase", item.id, {"order_no": item.order_no})
    db.commit(); db.refresh(item)
    return item


@router.delete("/purchases/{id}")
def delete_purchase(id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(InvPurchase).filter(InvPurchase.id == id).first()
    if not item: raise HTTPException(status_code=404, detail="采购单不存在")
    _audit(db, user, "delete", "purchase", item.id, {"order_no": item.order_no})
    db.delete(item); db.commit()
    return {"ok": True}


# ═══════════ Sales ═══════════════════════════

@router.get("/sales", response_model=list[InvSaleResponse])
def list_sales(
    company_id: int,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    status: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(InvSale).filter(InvSale.company_id == company_id)
    if status:
        q = q.filter(InvSale.status == status)
    if start_date:
        q = q.filter(InvSale.order_date >= start_date)
    if end_date:
        q = q.filter(InvSale.order_date <= end_date)
    if search:
        pattern = f"%{search}%"
        q = q.filter(
            (InvSale.order_no.ilike(pattern)) |
            (InvSale.customer_name.ilike(pattern)) |
            (InvSale.product_name.ilike(pattern))
        )
    return q.order_by(InvSale.id.desc()).offset(offset).limit(limit).all()


@router.post("/sales", response_model=InvSaleResponse)
def create_sale(data: InvSaleCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if data.quantity <= 0:
        raise HTTPException(status_code=400, detail="数量必须大于0")
    if data.unit_price < 0:
        raise HTTPException(status_code=400, detail="单价不能为负数")
    profit = data.total_amount - data.cost_amount
    item = InvSale(**data.model_dump(), profit=profit)
    db.add(item); db.commit(); db.refresh(item)
    _audit(db, user, "create", "sale", item.id, {"order_no": item.order_no, "amount": item.total_amount, "profit": item.profit})
    db.commit()
    return item


@router.put("/sales/{id}", response_model=InvSaleResponse)
def update_sale(id: int, data: InvSaleCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(InvSale).filter(InvSale.id == id).first()
    if not item: raise HTTPException(status_code=404, detail="销售单不存在")
    old_status = item.status
    for k, v in data.model_dump(exclude_unset=True).items(): setattr(item, k, v)
    item.profit = item.total_amount - item.cost_amount
    # 出库联动 + 生成凭证
    if old_status != "已出库" and item.status == "已出库":
        _sale_to_stock(item, db)
        _generate_voucher(db, item.company_id, user.id, "transfer", f"销售出库 {item.order_no} {item.product_name}", [
            {"account_code": "1122", "debit": item.total_amount, "credit": 0, "description": f"应收账款 {item.customer_name}"},
            {"account_code": "6001", "debit": 0, "credit": item.total_amount, "description": f"主营业务收入 {item.product_name}"},
        ])
        if item.cost_amount > 0:
            _generate_voucher(db, item.company_id, user.id, "transfer", f"结转成本 {item.order_no} {item.product_name}", [
                {"account_code": "6401", "debit": item.cost_amount, "credit": 0, "description": f"主营业务成本 {item.product_name}"},
                {"account_code": "1405", "debit": 0, "credit": item.cost_amount, "description": f"库存商品 {item.product_name}"},
            ])
        _audit(db, user, "post", "sale_outbound", item.id, {"order_no": item.order_no, "amount": item.total_amount, "profit": item.profit})
    _audit(db, user, "update", "sale", item.id, {"order_no": item.order_no})
    db.commit(); db.refresh(item)
    return item


@router.delete("/sales/{id}")
def delete_sale(id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(InvSale).filter(InvSale.id == id).first()
    if not item: raise HTTPException(status_code=404, detail="销售单不存在")
    _audit(db, user, "delete", "sale", item.id, {"order_no": item.order_no})
    db.delete(item); db.commit()
    return {"ok": True}


# ═══════════ Stock ═══════════════════════════

@router.get("/stock/low-stock-alerts", response_model=list[InvStockResponse])
def list_low_stock_alerts(company_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(InvStock).filter(
        InvStock.company_id == company_id,
        InvStock.quantity <= InvStock.min_stock,
        InvStock.min_stock > 0,
    ).order_by(InvStock.quantity - InvStock.min_stock).all()


@router.get("/stock", response_model=list[InvStockResponse])
def list_stock(
    company_id: int,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    category: str | None = None,
    warehouse: str | None = None,
    low_stock: bool | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(InvStock).filter(InvStock.company_id == company_id)
    if category:
        q = q.filter(InvStock.category == category)
    if warehouse:
        q = q.filter(InvStock.warehouse == warehouse)
    if low_stock:
        q = q.filter(InvStock.quantity <= InvStock.min_stock)
    if search:
        pattern = f"%{search}%"
        q = q.filter(
            (InvStock.product_code.ilike(pattern)) |
            (InvStock.product_name.ilike(pattern)) |
            (InvStock.category.ilike(pattern))
        )
    return q.order_by(InvStock.id.desc()).offset(offset).limit(limit).all()


@router.post("/stock", response_model=InvStockResponse)
def create_stock_item(data: InvStockCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if data.quantity < 0:
        raise HTTPException(status_code=400, detail="数量不能为负数")
    if data.unit_cost < 0:
        raise HTTPException(status_code=400, detail="单位成本不能为负数")
    total_cost = data.quantity * data.unit_cost
    item = InvStock(**data.model_dump(), total_cost=total_cost)
    db.add(item); db.commit(); db.refresh(item)
    _audit(db, user, "create", "stock", item.id, {"product_name": item.product_name, "quantity": item.quantity})
    db.commit()
    return item


@router.put("/stock/{id}", response_model=InvStockResponse)
def update_stock_item(id: int, data: InvStockCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(InvStock).filter(InvStock.id == id).first()
    if not item: raise HTTPException(status_code=404, detail="库存记录不存在")
    for k, v in data.model_dump(exclude_unset=True).items(): setattr(item, k, v)
    item.total_cost = item.quantity * item.unit_cost
    _audit(db, user, "update", "stock", item.id, {"product_name": item.product_name, "quantity": item.quantity})
    db.commit(); db.refresh(item)
    return item


@router.delete("/stock/{id}")
def delete_stock_item(id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(InvStock).filter(InvStock.id == id).first()
    if not item: raise HTTPException(status_code=404, detail="库存记录不存在")
    _audit(db, user, "delete", "stock", item.id, {"product_name": item.product_name})
    db.delete(item); db.commit()
    return {"ok": True}


# ═══════════ 联动辅助函数 ═══════════════════

def _purchase_to_stock(purchase: InvPurchase, db: Session):
    """采购入库 → 增加或创建库存记录。按产品名称+仓库匹配。"""
    stock = db.query(InvStock).filter(
        InvStock.company_id == purchase.company_id,
        InvStock.product_name == purchase.product_name,
        InvStock.warehouse == (purchase.notes or ""),
    ).first()
    if stock:
        total_qty = stock.quantity + purchase.quantity
        stock.unit_cost = round(
            (stock.total_cost + purchase.total_amount) / total_qty, 2
        ) if total_qty > 0 else stock.unit_cost
        stock.quantity = total_qty
        stock.total_cost = round(stock.quantity * stock.unit_cost, 2)
    else:
        unit_cost = purchase.unit_price if purchase.unit_price > 0 else round(purchase.total_amount / purchase.quantity, 2) if purchase.quantity > 0 else 0
        db.add(InvStock(
            company_id=purchase.company_id,
            product_code=purchase.order_no,
            product_name=purchase.product_name,
            category="",
            quantity=purchase.quantity,
            unit=purchase.unit,
            unit_cost=unit_cost,
            total_cost=purchase.total_amount,
            warehouse=purchase.notes or "",
        ))


def _sale_to_stock(sale: InvSale, db: Session):
    """销售出库 → 减少库存。按产品名称匹配，优先扣减有库存的仓库。"""
    stocks = db.query(InvStock).filter(
        InvStock.company_id == sale.company_id,
        InvStock.product_name == sale.product_name,
    ).order_by(InvStock.quantity.desc()).all()
    remaining = sale.quantity
    for stock in stocks:
        if remaining <= 0:
            break
        deduct = min(stock.quantity, remaining)
        stock.quantity -= deduct
        stock.total_cost = round(stock.quantity * stock.unit_cost, 2)
        remaining -= deduct


# ═══════════ 批量操作 ═══════════════════════

class BatchDeleteRequest(BaseModel):
    ids: list[int]

@router.post("/purchases/batch-delete")
def batch_delete_purchases(data: BatchDeleteRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    count = db.query(InvPurchase).filter(InvPurchase.id.in_(data.ids)).delete(synchronize_session=False)
    db.commit()
    return {"deleted": count}

@router.post("/sales/batch-delete")
def batch_delete_sales(data: BatchDeleteRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    count = db.query(InvSale).filter(InvSale.id.in_(data.ids)).delete(synchronize_session=False)
    db.commit()
    return {"deleted": count}

@router.post("/stock/batch-delete")
def batch_delete_stock(data: BatchDeleteRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    count = db.query(InvStock).filter(InvStock.id.in_(data.ids)).delete(synchronize_session=False)
    db.commit()
    return {"deleted": count}


# ═══════════ 主数据: 仓库 ═══════════════════

@router.get("/warehouses", response_model=list[WarehouseResponse])
def list_warehouses(company_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Warehouse).filter(Warehouse.company_id == company_id, Warehouse.is_active == True).order_by(Warehouse.code).all()

@router.post("/warehouses", response_model=WarehouseResponse)
def create_warehouse(data: WarehouseCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = Warehouse(**data.model_dump())
    db.add(item); db.commit(); db.refresh(item)
    _audit(db, user, "create", "warehouse", item.id, {"name": item.name})
    db.commit()
    return item

@router.put("/warehouses/{id}", response_model=WarehouseResponse)
def update_warehouse(id: int, data: WarehouseCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(Warehouse).filter(Warehouse.id == id).first()
    if not item: raise HTTPException(status_code=404, detail="仓库不存在")
    for k, v in data.model_dump(exclude_unset=True).items(): setattr(item, k, v)
    db.commit(); db.refresh(item)
    return item


# ═══════════ 主数据: 存货分类 ═══════════════

@router.get("/categories", response_model=list[InventoryCategoryResponse])
def list_inventory_categories(company_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(InventoryCategory).filter(InventoryCategory.company_id == company_id).order_by(InventoryCategory.code).all()

@router.post("/categories", response_model=InventoryCategoryResponse)
def create_inventory_category(data: InventoryCategoryCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = InventoryCategory(**data.model_dump())
    db.add(item); db.commit(); db.refresh(item)
    return item

@router.put("/categories/{id}", response_model=InventoryCategoryResponse)
def update_inventory_category(id: int, data: InventoryCategoryCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(InventoryCategory).filter(InventoryCategory.id == id).first()
    if not item: raise HTTPException(status_code=404, detail="分类不存在")
    for k, v in data.model_dump(exclude_unset=True).items(): setattr(item, k, v)
    db.commit(); db.refresh(item)
    return item


# ═══════════ 主数据: 存货 ═══════════

@router.get("/inventory", response_model=list[InventoryResponse])
def list_inventory(company_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Inventory).filter(Inventory.company_id == company_id, Inventory.is_active == True).order_by(Inventory.code).all()

@router.post("/inventory", response_model=InventoryResponse)
def create_inventory(data: InventoryCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = Inventory(**data.model_dump())
    db.add(item); db.commit(); db.refresh(item)
    return item

@router.put("/inventory/{id}", response_model=InventoryResponse)
def update_inventory(id: int, data: InventoryCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(Inventory).filter(Inventory.id == id).first()
    if not item: raise HTTPException(status_code=404, detail="存货不存在")
    for k, v in data.model_dump(exclude_unset=True).items(): setattr(item, k, v)
    db.commit(); db.refresh(item)
    return item


# ═══════════ 主数据: 计量单位 ═══════════

@router.get("/units", response_model=list[UnitOfMeasureResponse])
def list_units_of_measure(company_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(UnitOfMeasure).filter(UnitOfMeasure.company_id == company_id).order_by(UnitOfMeasure.group_name, UnitOfMeasure.unit_name).all()

@router.post("/units", response_model=UnitOfMeasureResponse)
def create_unit_of_measure(data: UnitOfMeasureCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = UnitOfMeasure(**data.model_dump())
    db.add(item); db.commit(); db.refresh(item)
    return item

@router.put("/units/{id}", response_model=UnitOfMeasureResponse)
def update_unit_of_measure(id: int, data: UnitOfMeasureCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(UnitOfMeasure).filter(UnitOfMeasure.id == id).first()
    if not item: raise HTTPException(status_code=404, detail="计量单位不存在")
    for k, v in data.model_dump(exclude_unset=True).items(): setattr(item, k, v)
    db.commit(); db.refresh(item)
    return item
