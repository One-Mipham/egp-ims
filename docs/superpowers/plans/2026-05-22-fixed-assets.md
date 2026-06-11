# 固定资产模块完善 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 完善固定资产模块的全部 16 项缺口：后端 5 个新端点 + 校验 + 分页筛选 + Schema 修复，前端去硬编码 company_id + 批量计提 + 折旧编辑删除 + 处置改造 + 导出

**Architecture:** 后端在现有 `fixed_assets.py` 路由器上追加端点，模型增加处置字段和 updated_at，Schema 新增 Update/Dispose/BatchRequest。前端所有视图去硬编码，折旧计算权威源移至后端，处置使用专用端点。

**Tech Stack:** Python 3.12 / FastAPI / SQLAlchemy / SQLite, Vue 3 / TypeScript / PrimeVue

---

## 文件变更清单

| 操作 | 文件 |
|------|------|
| 修改 | `backend/app/models.py` (FixedAsset +4字段, FixedAssetDepreciation +1字段) |
| 修改 | `backend/app/database.py` (ALTER TABLE migrations) |
| 修改 | `backend/app/schemas/__init__.py` (新增 FixedAssetUpdate, FixedAssetDispose, BatchDepreciationRequest, 更新两个 Response) |
| 修改 | `backend/app/routers/fixed_assets.py` (5新端点 + 校验增强 + 分页筛选) |
| 修改 | `frontend/src/api/index.ts` (新增5个API函数 + 更新2个) |
| 修改 | `frontend/src/views/fixed_assets/FixedAssetRegister.vue` (去硬编码 + 搜索筛选 + 分页 + 移除前端折旧计算 + 导出CSV) |
| 修改 | `frontend/src/views/fixed_assets/FixedAssetDepreciation.vue` (去硬编码 + 批量计提 + 编辑删除 + 后端计算折旧金额) |
| 修改 | `frontend/src/views/fixed_assets/FixedAssetDisposal.vue` (去硬编码 + 专用 dispose API + 处置日期/收入字段) |
| 修改 | `frontend/src/views/fixed_assets/FixedAssetCheck.vue` (去硬编码) |
| 修改 | `frontend/src/views/fixed_assets/FixedAssetReports.vue` (去硬编码 + 导出CSV) |

---

### Task 1: 数据模型变更 + 数据库迁移

**Files:**
- Modify: `backend/app/models.py`
- Modify: `backend/app/database.py`

- [ ] **Step 1: 更新 `FixedAsset` 模型加处置字段**

在 `backend/app/models.py` 的 `FixedAsset` 类中（约 line 728），在 `notes` 字段之后、`created_at` 之前添加四个处置字段：

```python
    disposal_date = Column(String(10), nullable=True, comment="处置日期")
    disposal_proceeds = Column(Float, nullable=False, default=0, comment="处置收入")
    disposal_gain_loss = Column(Float, nullable=False, default=0, comment="处置损益")
    disposal_reason = Column(Text, nullable=True, comment="处置原因")
```

- [ ] **Step 2: 更新 `FixedAssetDepreciation` 模型加 `updated_at`**

在 `backend/app/models.py` 的 `FixedAssetDepreciation` 类中（约 line 753），在 `created_at` 字段之后添加：

```python
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

- [ ] **Step 3: 在 `run_migrations()` 中添加新列**

在 `backend/app/database.py` 的 `migrations` 列表中（约 line 33），追加以下 SQL：

```python
        "ALTER TABLE fixed_assets ADD COLUMN disposal_date VARCHAR(10)",
        "ALTER TABLE fixed_assets ADD COLUMN disposal_proceeds FLOAT DEFAULT 0",
        "ALTER TABLE fixed_assets ADD COLUMN disposal_gain_loss FLOAT DEFAULT 0",
        "ALTER TABLE fixed_assets ADD COLUMN disposal_reason TEXT",
        "ALTER TABLE fixed_asset_depreciations ADD COLUMN updated_at TIMESTAMP",
```

- [ ] **Step 4: 验证迁移**

```bash
cd backend && uv run python -c "from app.database import init_db, run_migrations; init_db(); run_migrations(); print('OK')"
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/models.py backend/app/database.py
git commit -m "feat(fixed-assets): add disposal tracking fields + depreciation updated_at"
```

---

### Task 2: Schema 变更

**Files:**
- Modify: `backend/app/schemas/__init__.py`

- [ ] **Step 1: 更新 `FixedAssetResponse` 加入处置字段**

找到 `FixedAssetResponse`（约 line 602），在 `notes` 和 `created_at` 之间加入新字段：

```python
class FixedAssetResponse(BaseModel):
    id: int; company_id: int; asset_code: str; name: str; category: str
    acquisition_date: Optional[str] = None
    original_value: float; residual_value: float; useful_life: int
    depreciation_method: str; monthly_depreciation: float
    accumulated_depreciation: float; net_value: float; status: str
    location: Optional[str] = None; department_id: Optional[int] = None
    disposal_date: Optional[str] = None
    disposal_proceeds: Optional[float] = None
    disposal_gain_loss: Optional[float] = None
    disposal_reason: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None; updated_at: Optional[datetime] = None
    model_config = {"from_attributes": True}
```

- [ ] **Step 2: 新增 `FixedAssetUpdate` schema**

在 `FixedAssetResponse` 之后添加：

```python
class FixedAssetUpdate(BaseModel):
    asset_code: Optional[str] = None
    name: Optional[str] = None
    category: Optional[str] = None
    acquisition_date: Optional[str] = None
    original_value: Optional[float] = None
    residual_value: Optional[float] = None
    useful_life: Optional[int] = None
    depreciation_method: Optional[str] = None
    monthly_depreciation: Optional[float] = None
    status: Optional[str] = None
    location: Optional[str] = None
    department_id: Optional[int] = None
    notes: Optional[str] = None
```

- [ ] **Step 3: 新增 `FixedAssetDispose` schema**

```python
class FixedAssetDispose(BaseModel):
    disposal_date: str
    disposal_proceeds: float = 0
    disposal_reason: Optional[str] = None
    status: str  # "已处置" or "报废"
```

- [ ] **Step 4: 新增 `BatchDepreciationRequest` schema**

```python
class BatchDepreciationRequest(BaseModel):
    company_id: int
    period: str
    asset_ids: Optional[list[int]] = None
```

- [ ] **Step 5: 更新 `FixedAssetDepreciationResponse` 加 `updated_at`**

```python
class FixedAssetDepreciationResponse(BaseModel):
    id: int; company_id: int; fixed_asset_id: int; period: str
    depreciation_amount: float; accumulated_before: float; accumulated_after: float
    created_at: Optional[datetime] = None; updated_at: Optional[datetime] = None
    model_config = {"from_attributes": True}
```

- [ ] **Step 6: 验证导入**

```bash
cd backend && uv run python -c "from app.schemas import FixedAssetUpdate, FixedAssetDispose, BatchDepreciationRequest; print('OK')"
```

- [ ] **Step 7: Commit**

```bash
git add backend/app/schemas/__init__.py
git commit -m "feat(fixed-assets): add Update, Dispose, BatchDepreciation schemas"
```

---

### Task 3: 后端 — GET 单条资产 + 列表分页筛选

**Files:**
- Modify: `backend/app/routers/fixed_assets.py`

- [ ] **Step 1: 更新 import，引入新 schemas 和 Union**

在 `fixed_assets.py` 顶部更新 imports：

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user
from app.models import FixedAsset, FixedAssetDepreciation, User
from app.schemas import (
    FixedAssetCreate, FixedAssetUpdate, FixedAssetResponse,
    FixedAssetDepreciationCreate, FixedAssetDepreciationResponse,
    FixedAssetDispose, BatchDepreciationRequest,
)
```

- [ ] **Step 2: 替换 `list_assets`，增加分页和筛选**

```python
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
```

- [ ] **Step 3: 新增 `GET /assets/{asset_id}` 端点**

```python
@router.get("/assets/{asset_id}", response_model=FixedAssetResponse)
def get_asset(asset_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(FixedAsset).filter(FixedAsset.id == asset_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="资产不存在")
    return item
```

- [ ] **Step 4: 更新 `update_asset` 使用 `FixedAssetUpdate`**

```python
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
```

- [ ] **Step 5: 验证端点**

```bash
cd backend && uv run uvicorn app.main:app --port 8000 &
sleep 3
curl -s http://localhost:8000/api/fixed-assets/assets?company_id=1 | head -c 200
curl -s http://localhost:8000/api/fixed-assets/assets?company_id=1\&category=设备\&search=电脑 | head -c 200
```

- [ ] **Step 6: Commit**

```bash
git add backend/app/routers/fixed_assets.py
git commit -m "feat(fixed-assets): add GET single asset + pagination/filtering on list"
```

---

### Task 4: 后端 — 折旧修改与删除 + 列表分页

**Files:**
- Modify: `backend/app/routers/fixed_assets.py`

- [ ] **Step 1: 更新 `list_depreciations` 加分页**

```python
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
```

- [ ] **Step 2: 新增 `PUT /depreciations/{dep_id}`**

```python
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
    old_after = dep.accumulated_after
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
```

- [ ] **Step 3: 新增 `DELETE /depreciations/{dep_id}`**

```python
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
```

- [ ] **Step 4: 验证**

```bash
curl -s "http://localhost:8000/api/fixed-assets/depreciations?company_id=1&limit=5&offset=0" | python -m json.tool | head -20
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/routers/fixed_assets.py
git commit -m "feat(fixed-assets): add PUT/DELETE depreciation + pagination"
```

---

### Task 5: 后端 — 批量计提折旧

**Files:**
- Modify: `backend/app/routers/fixed_assets.py`

- [ ] **Step 1: 新增 `POST /depreciations/batch`**

在现有 `create_depreciation` 之后添加：

```python
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

    db.commit()
    return {"success": success, "failed": failed, "total": len(assets)}
```

- [ ] **Step 2: 验证批量计提**

```bash
curl -s -X POST http://localhost:8000/api/fixed-assets/depreciations/batch \
  -H 'Content-Type: application/json' \
  -d '{"company_id": 1, "period": "2026-05"}' | python -m json.tool
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/routers/fixed_assets.py
git commit -m "feat(fixed-assets): add batch depreciation endpoint"
```

---

### Task 6: 后端 — 专用处置端点

**Files:**
- Modify: `backend/app/routers/fixed_assets.py`

- [ ] **Step 1: 新增 `POST /assets/{asset_id}/dispose`**

```python
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
    db.commit()
    db.refresh(asset)
    return asset
```

- [ ] **Step 2: 验证处置**

```bash
curl -s -X POST http://localhost:8000/api/fixed-assets/assets/1/dispose \
  -H 'Content-Type: application/json' \
  -d '{"disposal_date":"2026-05-22","disposal_proceeds":5000,"disposal_reason":"正常出售","status":"已处置"}' | python -m json.tool
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/routers/fixed_assets.py
git commit -m "feat(fixed-assets): add dedicated dispose endpoint with gain/loss tracking"
```

---

### Task 7: 后端 — 校验增强（create_depreciation）

**Files:**
- Modify: `backend/app/routers/fixed_assets.py`

- [ ] **Step 1: 重写 `create_depreciation` 加入校验**

将现有 `create_depreciation` 端点（约 line 61-78）替换为：

```python
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
    db.commit()
    db.refresh(item)
    return item
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/routers/fixed_assets.py
git commit -m "fix(fixed-assets): add duplicate-period, status, and residual-value validations"
```

---

### Task 8: 前端 API 函数

**Files:**
- Modify: `frontend/src/api/index.ts`

- [ ] **Step 1: 更新 `listFixedAssets` 和 `listDepreciations` 签名，新增 5 个 API 函数**

找到 `frontend/src/api/index.ts` 中固定资产生命周期 API 区域（约 line 223-236），替换为：

```ts
// ═══════════ 固定资产管理 ═══════════
export const listFixedAssets = (companyId: number, params?: Record<string, any>) =>
    api.get('/fixed-assets/assets', { params: { company_id: companyId, ...params } })
export const getFixedAsset = (id: number) =>
    api.get(`/fixed-assets/assets/${id}`)
export const createFixedAsset = (data: any) =>
    api.post('/fixed-assets/assets', data)
export const updateFixedAsset = (id: number, data: any) =>
    api.put(`/fixed-assets/assets/${id}`, data)
export const deleteFixedAsset = (id: number) =>
    api.delete(`/fixed-assets/assets/${id}`)
export const disposeFixedAsset = (id: number, data: any) =>
    api.post(`/fixed-assets/assets/${id}/dispose`, data)

export const listDepreciations = (companyId: number, params?: Record<string, any>) =>
    api.get('/fixed-assets/depreciations', { params: { company_id: companyId, ...params } })
export const createDepreciation = (data: any) =>
    api.post('/fixed-assets/depreciations', data)
export const updateDepreciation = (id: number, data: any) =>
    api.put(`/fixed-assets/depreciations/${id}`, data)
export const deleteDepreciation = (id: number) =>
    api.delete(`/fixed-assets/depreciations/${id}`)
export const batchDepreciate = (data: any) =>
    api.post('/fixed-assets/depreciations/batch', data)
```

- [ ] **Step 2: 验证编译**

```bash
cd frontend && npx tsc --noEmit --skipLibCheck 2>&1 | head -10
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/api/index.ts
git commit -m "feat(fixed-assets): add frontend API functions for new endpoints"
```

---

### Task 9: 前端 — FixedAssetRegister 完整改造

**Files:**
- Modify: `frontend/src/views/fixed_assets/FixedAssetRegister.vue`

- [ ] **Step 1: 完全替换 FixedAssetRegister.vue**

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useToast } from 'primevue/usetoast'
import { listFixedAssets, createFixedAsset, updateFixedAsset, deleteFixedAsset } from '../../api'

const toast = useToast()
const companyId = Number(localStorage.getItem('companyId') || '1')
const items = ref<any[]>([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref<number | null>(null)

const searchText = ref('')
const filterCategory = ref('')
const filterStatus = ref('')
const filterLocation = ref('')
const page = ref(1)
const pageSize = 20

const emptyForm = () => ({
  company_id: companyId, asset_code: '', name: '', category: '设备',
  acquisition_date: '', original_value: 0, residual_value: 0, useful_life: 5,
  depreciation_method: '直线法', monthly_depreciation: 0,
  status: '使用中', location: '', department_id: null, notes: '',
})

const form = ref(emptyForm())
const categoryOptions = ['设备', '车辆', '房产', '家具', '电子设备', '软件', '其他']
const statusOptions = ['使用中', '已处置', '报废', '闲置']

async function load() {
  const params: Record<string, any> = { limit: pageSize, offset: (page.value - 1) * pageSize }
  if (searchText.value) params.search = searchText.value
  if (filterCategory.value) params.category = filterCategory.value
  if (filterStatus.value) params.status = filterStatus.value
  if (filterLocation.value) params.location = filterLocation.value
  const { data } = await listFixedAssets(companyId, params)
  items.value = data
}

function openCreate() {
  form.value = emptyForm()
  isEdit.value = false; editId.value = null
  dialogVisible.value = true
}

function openEdit(row: any) {
  form.value = { ...row }
  isEdit.value = true; editId.value = row.id
  dialogVisible.value = true
}

async function save() {
  if (isEdit.value && editId.value) {
    const payload: Record<string, any> = {}
    for (const [k, v] of Object.entries(form.value)) {
      if (v !== undefined && k !== 'company_id' && k !== 'id' && k !== 'created_at' && k !== 'updated_at'
        && k !== 'accumulated_depreciation' && k !== 'net_value'
        && k !== 'disposal_date' && k !== 'disposal_proceeds' && k !== 'disposal_gain_loss' && k !== 'disposal_reason') {
        payload[k] = v
      }
    }
    await updateFixedAsset(editId.value, payload)
    toast.add({ severity: 'success', summary: '已更新', life: 2000 })
  } else {
    await createFixedAsset(form.value)
    toast.add({ severity: 'success', summary: '已创建', life: 2000 })
  }
  dialogVisible.value = false
  await load()
}

async function remove(id: number) {
  if (confirm('确定删除该资产？')) {
    await deleteFixedAsset(id)
    toast.add({ severity: 'success', summary: '已删除', life: 2000 })
    await load()
  }
}

function exportCSV() {
  const header = ['资产编号','名称','类别','原值','累计折旧','净值','状态','存放地点']
  const rows = items.value.map((i: any) => [i.asset_code, i.name, i.category, i.original_value, i.accumulated_depreciation, i.net_value, i.status, i.location])
  const csv = [header.join(','), ...rows.map((r: any[]) => r.map((c: any) => `"${String(c ?? '').replace(/"/g, '""')}"`).join(','))].join('\n')
  const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = '固定资产台账.csv'; a.click()
  URL.revokeObjectURL(url)
}

onMounted(load)
</script>

<template>
  <div class="p-4">
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-lg font-bold">资产台账</h1>
      <div class="flex gap-2">
        <button @click="exportCSV" class="px-3 py-2 border rounded text-sm hover:bg-zinc-100">导出CSV</button>
        <button @click="openCreate" class="px-4 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700">+ 新增资产</button>
      </div>
    </div>

    <div class="flex gap-2 mb-3">
      <input v-model="searchText" @input="page=1; load()" placeholder="搜索名称/编号..." class="border rounded px-2 py-1 text-sm w-48" />
      <select v-model="filterCategory" @change="page=1; load()" class="border rounded px-2 py-1 text-sm">
        <option value="">全部类别</option>
        <option v-for="c in categoryOptions" :key="c" :value="c">{{ c }}</option>
      </select>
      <select v-model="filterStatus" @change="page=1; load()" class="border rounded px-2 py-1 text-sm">
        <option value="">全部状态</option>
        <option v-for="s in statusOptions" :key="s" :value="s">{{ s }}</option>
      </select>
    </div>

    <table class="w-full text-sm border-collapse">
      <thead>
        <tr class="bg-zinc-100 text-left">
          <th class="p-2 border">资产编号</th><th class="p-2 border">名称</th><th class="p-2 border">类别</th>
          <th class="p-2 border text-right">原值</th><th class="p-2 border text-right">累计折旧</th><th class="p-2 border text-right">净值</th>
          <th class="p-2 border">状态</th><th class="p-2 border">操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in items" :key="item.id" class="hover:bg-zinc-50">
          <td class="p-2 border font-mono text-xs">{{ item.asset_code }}</td>
          <td class="p-2 border">{{ item.name }}</td>
          <td class="p-2 border text-xs">{{ item.category }}</td>
          <td class="p-2 border text-right">{{ (item.original_value || 0).toLocaleString() }}</td>
          <td class="p-2 border text-right">{{ (item.accumulated_depreciation || 0).toLocaleString() }}</td>
          <td class="p-2 border text-right">{{ (item.net_value || 0).toLocaleString() }}</td>
          <td class="p-2 border"><span :class="item.status === '使用中' ? 'text-green-600' : 'text-red-500'">{{ item.status }}</span></td>
          <td class="p-2 border">
            <button @click="openEdit(item)" class="text-blue-600 mr-2 text-xs">编辑</button>
            <button @click="remove(item.id)" class="text-red-500 text-xs">删除</button>
          </td>
        </tr>
      </tbody>
    </table>

    <div class="flex items-center justify-between mt-3">
      <span class="text-xs text-zinc-400">第 {{ page }} 页</span>
      <div class="flex gap-1">
        <button @click="page = Math.max(1, page - 1); load()" :disabled="page <= 1" class="px-3 py-1 border rounded text-sm disabled:opacity-30">上一页</button>
        <button @click="page = page + 1; load()" class="px-3 py-1 border rounded text-sm">下一页</button>
      </div>
    </div>

    <div v-if="dialogVisible" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg w-[600px] max-h-[80vh] overflow-auto p-6">
        <h2 class="text-lg font-bold mb-4">{{ isEdit ? '编辑资产' : '新增资产' }}</h2>
        <div class="grid grid-cols-2 gap-3">
          <div><label class="text-xs text-zinc-500">资产编号</label><input v-model="form.asset_code" class="w-full border rounded px-2 py-1 text-sm" /></div>
          <div><label class="text-xs text-zinc-500">名称</label><input v-model="form.name" class="w-full border rounded px-2 py-1 text-sm" /></div>
          <div>
            <label class="text-xs text-zinc-500">类别</label>
            <select v-model="form.category" class="w-full border rounded px-2 py-1 text-sm">
              <option v-for="c in categoryOptions" :key="c" :value="c">{{ c }}</option>
            </select>
          </div>
          <div>
            <label class="text-xs text-zinc-500">状态</label>
            <select v-model="form.status" class="w-full border rounded px-2 py-1 text-sm">
              <option v-for="s in statusOptions" :key="s" :value="s">{{ s }}</option>
            </select>
          </div>
          <div><label class="text-xs text-zinc-500">购置日期</label><input type="date" v-model="form.acquisition_date" class="w-full border rounded px-2 py-1 text-sm" /></div>
          <div><label class="text-xs text-zinc-500">存放地点</label><input v-model="form.location" class="w-full border rounded px-2 py-1 text-sm" /></div>
          <div><label class="text-xs text-zinc-500">原值</label><input type="number" v-model.number="form.original_value" class="w-full border rounded px-2 py-1 text-sm" /></div>
          <div><label class="text-xs text-zinc-500">残值</label><input type="number" v-model.number="form.residual_value" class="w-full border rounded px-2 py-1 text-sm" /></div>
          <div><label class="text-xs text-zinc-500">使用年限(年)</label><input type="number" v-model.number="form.useful_life" class="w-full border rounded px-2 py-1 text-sm" /></div>
          <div>
            <label class="text-xs text-zinc-500">折旧方法</label>
            <select v-model="form.depreciation_method" class="w-full border rounded px-2 py-1 text-sm">
              <option value="直线法">直线法</option><option value="双倍余额递减法">双倍余额递减法</option><option value="年数总和法">年数总和法</option>
            </select>
          </div>
          <div><label class="text-xs text-zinc-500">月折旧额（参考值）</label><input type="number" v-model.number="form.monthly_depreciation" class="w-full border rounded px-2 py-1 text-sm" /></div>
        </div>
        <div class="mt-3"><label class="text-xs text-zinc-500">备注</label><textarea v-model="form.notes" class="w-full border rounded px-2 py-1 text-sm" rows="2"></textarea></div>
        <div class="flex justify-end gap-2 mt-4">
          <button @click="dialogVisible = false" class="px-4 py-1.5 border rounded text-sm">取消</button>
          <button @click="save" class="px-4 py-1.5 bg-blue-600 text-white rounded text-sm">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>
```

- [ ] **Step 2: 验证前端编译**

```bash
cd frontend && npx vue-tsc --noEmit --skipLibCheck 2>&1 | grep -i "fixed_asset\|FixedAsset" | head -10
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/fixed_assets/FixedAssetRegister.vue
git commit -m "feat(fixed-assets): add search/filter/pagination/export + de-hardcode companyId in Register"
```

---

### Task 10: 前端 — FixedAssetDepreciation 完整改造

**Files:**
- Modify: `frontend/src/views/fixed_assets/FixedAssetDepreciation.vue`

- [ ] **Step 1: 完全替换 FixedAssetDepreciation.vue**

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useToast } from 'primevue/usetoast'
import { listDepreciations, createDepreciation, updateDepreciation, deleteDepreciation, batchDepreciate, listFixedAssets } from '../../api'

const toast = useToast()
const companyId = Number(localStorage.getItem('companyId') || '1')
const items = ref<any[]>([])
const assets = ref<any[]>([])
const dialogVisible = ref(false)
const batchDialogVisible = ref(false)
const editDialogVisible = ref(false)
const editId = ref<number | null>(null)
const editAmount = ref(0)

const emptyForm = () => ({
  company_id: companyId, fixed_asset_id: null as number | null, period: '',
  depreciation_amount: 0,
})

const form = ref(emptyForm())
const batchPeriod = ref('')
const selectedAsset = ref<any>(null)
const page = ref(1)
const pageSize = 20

function assetName(id: number) {
  const a = assets.value.find((x: any) => x.id === id)
  return a ? `${a.asset_code} ${a.name}` : `#${id}`
}

async function load() {
  const [r1, r2] = await Promise.all([
    listDepreciations(companyId, { limit: pageSize, offset: (page.value - 1) * pageSize }),
    listFixedAssets(companyId)
  ])
  items.value = r1.data
  assets.value = r2.data
}

function openCreate() {
  form.value = emptyForm()
  selectedAsset.value = null
  dialogVisible.value = true
}

function onAssetChange() {
  const a = assets.value.find((x: any) => x.id === form.value.fixed_asset_id)
  selectedAsset.value = a || null
  form.value.depreciation_amount = 0
}

async function save() {
  await createDepreciation(form.value)
  toast.add({ severity: 'success', summary: '折旧已计提', life: 2000 })
  dialogVisible.value = false
  await load()
}

function openEdit(row: any) {
  editId.value = row.id
  editAmount.value = row.depreciation_amount
  editDialogVisible.value = true
}

async function saveEdit() {
  const row = items.value.find((i: any) => i.id === editId.value)
  if (!row) return
  await updateDepreciation(editId.value!, {
    company_id: row.company_id,
    fixed_asset_id: row.fixed_asset_id,
    period: row.period,
    depreciation_amount: editAmount.value,
  })
  toast.add({ severity: 'success', summary: '已更新', life: 2000 })
  editDialogVisible.value = false
  await load()
}

async function remove(id: number) {
  if (confirm('确定删除该折旧记录？将恢复资产净值。')) {
    await deleteDepreciation(id)
    toast.add({ severity: 'success', summary: '已删除并恢复净值', life: 2000 })
    await load()
  }
}

async function runBatch() {
  if (!batchPeriod.value) return
  const res = await batchDepreciate({ company_id: companyId, period: batchPeriod.value })
  const { success, failed } = res.data
  toast.add({ severity: 'success', summary: `批量计提完成：成功${success.length}条，跳过${failed.length}条`, life: 4000 })
  batchDialogVisible.value = false
  await load()
}

onMounted(load)
</script>

<template>
  <div class="p-4">
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-lg font-bold">折旧管理</h1>
      <div class="flex gap-2">
        <button @click="batchDialogVisible = true" class="px-3 py-2 border rounded text-sm hover:bg-zinc-100">批量计提</button>
        <button @click="openCreate" class="px-4 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700">+ 计提折旧</button>
      </div>
    </div>

    <table class="w-full text-sm border-collapse">
      <thead>
        <tr class="bg-zinc-100 text-left">
          <th class="p-2 border">资产</th><th class="p-2 border">期间</th>
          <th class="p-2 border text-right">本期折旧</th><th class="p-2 border text-right">计提前累计</th><th class="p-2 border text-right">计提后累计</th>
          <th class="p-2 border text-xs text-zinc-400">计提时间</th><th class="p-2 border">操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in items" :key="item.id" class="hover:bg-zinc-50">
          <td class="p-2 border">{{ assetName(item.fixed_asset_id) }}</td>
          <td class="p-2 border font-mono text-xs">{{ item.period }}</td>
          <td class="p-2 border text-right">{{ (item.depreciation_amount || 0).toLocaleString() }}</td>
          <td class="p-2 border text-right">{{ (item.accumulated_before || 0).toLocaleString() }}</td>
          <td class="p-2 border text-right">{{ (item.accumulated_after || 0).toLocaleString() }}</td>
          <td class="p-2 border text-xs text-zinc-400">{{ item.created_at?.slice(0, 10) }}</td>
          <td class="p-2 border">
            <button @click="openEdit(item)" class="text-blue-600 mr-2 text-xs">编辑</button>
            <button @click="remove(item.id)" class="text-red-500 text-xs">删除</button>
          </td>
        </tr>
        <tr v-if="items.length === 0">
          <td colspan="7" class="p-6 text-center text-zinc-400 text-sm">暂无折旧记录</td>
        </tr>
      </tbody>
    </table>

    <div class="flex items-center justify-between mt-3">
      <span class="text-xs text-zinc-400">第 {{ page }} 页</span>
      <div class="flex gap-1">
        <button @click="page = Math.max(1, page - 1); load()" :disabled="page <= 1" class="px-3 py-1 border rounded text-sm disabled:opacity-30">上一页</button>
        <button @click="page = page + 1; load()" class="px-3 py-1 border rounded text-sm">下一页</button>
      </div>
    </div>

    <!-- 单项计提 -->
    <div v-if="dialogVisible" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg w-[480px] p-6">
        <h2 class="text-lg font-bold mb-4">计提折旧</h2>
        <div class="space-y-3">
          <div>
            <label class="text-xs text-zinc-500">选择资产</label>
            <select v-model.number="form.fixed_asset_id" @change="onAssetChange" class="w-full border rounded px-2 py-1.5 text-sm">
              <option :value="null" disabled>-- 请选择 --</option>
              <option v-for="a in assets.filter((x: any) => x.status === '使用中' || x.status === '闲置')" :key="a.id" :value="a.id">{{ a.asset_code }} {{ a.name }} (净值 {{ (a.net_value || 0).toLocaleString() }})</option>
            </select>
          </div>
          <div v-if="selectedAsset" class="bg-zinc-50 rounded p-3 text-xs space-y-1">
            <div class="flex justify-between"><span class="text-zinc-500">原值</span><span>{{ (selectedAsset.original_value || 0).toLocaleString() }}</span></div>
            <div class="flex justify-between"><span class="text-zinc-500">累计折旧</span><span>{{ (selectedAsset.accumulated_depreciation || 0).toLocaleString() }}</span></div>
            <div class="flex justify-between"><span class="text-zinc-500">残值</span><span>{{ (selectedAsset.residual_value || 0).toLocaleString() }}</span></div>
          </div>
          <div><label class="text-xs text-zinc-500">折旧期间</label><input v-model="form.period" placeholder="YYYY-MM" class="w-full border rounded px-2 py-1.5 text-sm" /></div>
          <div><label class="text-xs text-zinc-500">折旧金额</label><input type="number" v-model.number="form.depreciation_amount" class="w-full border rounded px-2 py-1.5 text-sm" /></div>
        </div>
        <div class="flex justify-end gap-2 mt-4">
          <button @click="dialogVisible = false" class="px-4 py-1.5 border rounded text-sm">取消</button>
          <button @click="save" class="px-4 py-1.5 bg-blue-600 text-white rounded text-sm">确认计提</button>
        </div>
      </div>
    </div>

    <!-- 批量计提 -->
    <div v-if="batchDialogVisible" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg w-[400px] p-6">
        <h2 class="text-lg font-bold mb-4">批量计提折旧</h2>
        <p class="text-xs text-zinc-500 mb-3">将为所有"使用中"和"闲置"状态的资产计提折旧。已在该期间计提过的资产将自动跳过。</p>
        <div class="space-y-3">
          <div><label class="text-xs text-zinc-500">折旧期间</label><input v-model="batchPeriod" placeholder="YYYY-MM" class="w-full border rounded px-2 py-1.5 text-sm" /></div>
        </div>
        <div class="flex justify-end gap-2 mt-4">
          <button @click="batchDialogVisible = false" class="px-4 py-1.5 border rounded text-sm">取消</button>
          <button @click="runBatch" class="px-4 py-1.5 bg-blue-600 text-white rounded text-sm">执行批量计提</button>
        </div>
      </div>
    </div>

    <!-- 编辑折旧 -->
    <div v-if="editDialogVisible" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg w-[400px] p-6">
        <h2 class="text-lg font-bold mb-4">修改折旧金额</h2>
        <div><label class="text-xs text-zinc-500">折旧金额</label><input type="number" v-model.number="editAmount" class="w-full border rounded px-2 py-1.5 text-sm" /></div>
        <div class="flex justify-end gap-2 mt-4">
          <button @click="editDialogVisible = false" class="px-4 py-1.5 border rounded text-sm">取消</button>
          <button @click="saveEdit" class="px-4 py-1.5 bg-blue-600 text-white rounded text-sm">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/fixed_assets/FixedAssetDepreciation.vue
git commit -m "feat(fixed-assets): add batch depreciate, edit/delete depreciation, de-hardcode companyId"
```

---

### Task 11: 前端 — FixedAssetDisposal 改造

**Files:**
- Modify: `frontend/src/views/fixed_assets/FixedAssetDisposal.vue`

- [ ] **Step 1: 替换 FixedAssetDisposal.vue 的 script 部分**

将 `<script setup>` 标签内容（约 line 1-42）替换为：

```vue
<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useToast } from 'primevue/usetoast'
import { listFixedAssets, disposeFixedAsset } from '../../api'

const toast = useToast()
const companyId = Number(localStorage.getItem('companyId') || '1')
const items = ref<any[]>([])
const statusFilter = ref('')
const dialogVisible = ref(false)
const selectedItem = ref<any>(null)
const disposalDate = ref('')
const disposalProceeds = ref(0)
const disposalReason = ref('')
const disposalType = ref('已处置')

const filteredItems = computed(() => {
  if (!statusFilter.value) return items.value
  return items.value.filter((i: any) => i.status === statusFilter.value)
})

async function load() {
  const { data } = await listFixedAssets(companyId)
  items.value = data
}

function openDisposal(row: any) {
  selectedItem.value = row
  disposalDate.value = new Date().toISOString().slice(0, 10)
  disposalProceeds.value = 0
  disposalReason.value = ''
  disposalType.value = '已处置'
  dialogVisible.value = true
}

async function confirmDisposal() {
  await disposeFixedAsset(selectedItem.value.id, {
    disposal_date: disposalDate.value,
    disposal_proceeds: disposalProceeds.value,
    disposal_reason: disposalReason.value,
    status: disposalType.value,
  })
  toast.add({ severity: 'success', summary: '处置完成', life: 2000 })
  dialogVisible.value = false
  await load()
}

onMounted(load)
</script>
```

- [ ] **Step 2: 更新处置对话框模板**

将对话框（约 line 83-104）替换为：

```vue
    <div v-if="dialogVisible" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg w-[440px] p-6">
        <h2 class="text-lg font-bold mb-4">资产处置 - {{ selectedItem?.name }}</h2>
        <div class="bg-zinc-50 rounded p-3 mb-3 text-sm">
          <div class="flex justify-between"><span>原值</span><span>{{ (selectedItem?.original_value || 0).toLocaleString() }}</span></div>
          <div class="flex justify-between"><span>累计折旧</span><span>{{ (selectedItem?.accumulated_depreciation || 0).toLocaleString() }}</span></div>
          <div class="flex justify-between"><span>净值</span><span class="font-bold">{{ (selectedItem?.net_value || 0).toLocaleString() }}</span></div>
          <div v-if="disposalProceeds > 0" class="flex justify-between mt-1 pt-1 border-t"><span>预计处置损益</span><span :class="(disposalProceeds - (selectedItem?.net_value || 0)) >= 0 ? 'text-green-600' : 'text-red-500'">{{ (disposalProceeds - (selectedItem?.net_value || 0)).toLocaleString() }}</span></div>
        </div>
        <div class="space-y-3">
          <div>
            <label class="text-xs text-zinc-500">处置类型</label>
            <select v-model="disposalType" class="w-full border rounded px-2 py-1.5 text-sm">
              <option value="已处置">已处置</option><option value="报废">报废</option>
            </select>
          </div>
          <div><label class="text-xs text-zinc-500">处置日期</label><input type="date" v-model="disposalDate" class="w-full border rounded px-2 py-1.5 text-sm" /></div>
          <div><label class="text-xs text-zinc-500">处置收入</label><input type="number" v-model.number="disposalProceeds" class="w-full border rounded px-2 py-1.5 text-sm" /></div>
          <div><label class="text-xs text-zinc-500">处置原因</label><textarea v-model="disposalReason" rows="2" class="w-full border rounded px-2 py-1.5 text-sm"></textarea></div>
        </div>
        <div class="flex justify-end gap-2 mt-4">
          <button @click="dialogVisible = false" class="px-4 py-1.5 border rounded text-sm">取消</button>
          <button @click="confirmDisposal" class="px-4 py-1.5 bg-orange-600 text-white rounded text-sm">确认处置</button>
        </div>
      </div>
    </div>
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/fixed_assets/FixedAssetDisposal.vue
git commit -m "feat(fixed-assets): switch to dedicated dispose API + disposal date/proceeds/reason + de-hardcode companyId"
```

---

### Task 12: 前端 — FixedAssetCheck 去硬编码

**Files:**
- Modify: `frontend/src/views/fixed_assets/FixedAssetCheck.vue`

- [ ] **Step 1: 修改 script 部分去硬编码**

将 `listFixedAssets(1)` 调用（line 35）和 `updateFixedAsset` 调用改为使用 localStorage 读取 companyId。在 script 部分添加：

```ts
const companyId = Number(localStorage.getItem('companyId') || '1')
```

然后将 `listFixedAssets(1)` 改为 `listFixedAssets(companyId)`。

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/fixed_assets/FixedAssetCheck.vue
git commit -m "fix(fixed-assets): de-hardcode companyId in AssetCheck"
```

---

### Task 13: 前端 — FixedAssetReports 去硬编码 + 导出

**Files:**
- Modify: `frontend/src/views/fixed_assets/FixedAssetReports.vue`

- [ ] **Step 1: 去硬编码 + 加导出按钮**

在 script 部分加 `const companyId = Number(localStorage.getItem('companyId') || '1')`，将 `listFixedAssets(1)` 改为 `listFixedAssets(companyId)`。

在 template 顶部分加导出按钮：

```html
<button @click="exportCSV" class="px-3 py-2 border rounded text-sm hover:bg-zinc-100">导出CSV</button>
```

在 script 中加 `exportCSV` 函数：

```ts
function exportCSV() {
  const header = ['资产编号','名称','类别','原值','累计折旧','净值','状态']
  const rows = items.value.map((i: any) => [i.asset_code, i.name, i.category, i.original_value, i.accumulated_depreciation, i.net_value, i.status])
  const csv = [header.join(','), ...rows.map((r: any[]) => r.map((c: any) => `"${String(c ?? '').replace(/"/g, '""')}"`).join(','))].join('\n')
  const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = '固定资产报表.csv'; a.click()
  URL.revokeObjectURL(url)
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/fixed_assets/FixedAssetReports.vue
git commit -m "fix(fixed-assets): de-hardcode companyId + add CSV export in Reports"
```

---

### Task 14: 端到端验证

- [ ] **Step 1: 启动后端**

```bash
cd backend && uv run uvicorn app.main:app --reload --port 8000 &
sleep 3
```

- [ ] **Step 2: 测试资产 CRUD + 筛选分页**

```bash
curl -s "http://localhost:8000/api/fixed-assets/assets?company_id=1&limit=3&offset=0" | python -m json.tool | head -10
```

- [ ] **Step 3: 测试批量计提**

```bash
curl -s -X POST http://localhost:8000/api/fixed-assets/depreciations/batch \
  -H 'Content-Type: application/json' \
  -d '{"company_id": 1, "period": "2026-05"}' | python -m json.tool
```

- [ ] **Step 4: 测试重复计提校验**

```bash
curl -s -X POST http://localhost:8000/api/fixed-assets/depreciations \
  -H 'Content-Type: application/json' \
  -d '{"company_id": 1, "fixed_asset_id": 1, "period": "2026-05", "depreciation_amount": 100}' | python -m json.tool
# 第二次应该返回 400 error
```

- [ ] **Step 5: 测试折旧修改和删除**

```bash
# 假设折旧记录 id=1 存在
curl -s -X PUT http://localhost:8000/api/fixed-assets/depreciations/1 \
  -H 'Content-Type: application/json' \
  -d '{"company_id": 1, "fixed_asset_id": 1, "period": "2026-05", "depreciation_amount": 200}' | python -m json.tool
```

- [ ] **Step 6: 测试处置**

```bash
curl -s -X POST http://localhost:8000/api/fixed-assets/assets/1/dispose \
  -H 'Content-Type: application/json' \
  -d '{"disposal_date":"2026-05-22","disposal_proceeds":5000,"disposal_reason":"test","status":"已处置"}' | python -m json.tool
```

- [ ] **Step 7: 验证前端无 TS 错误**

```bash
cd frontend && npx vue-tsc --noEmit --skipLibCheck 2>&1 | head -20
```

- [ ] **Step 8: Commit**

```bash
git add -A
git commit -m "chore: end-to-end validation of fixed-assets module"
```
