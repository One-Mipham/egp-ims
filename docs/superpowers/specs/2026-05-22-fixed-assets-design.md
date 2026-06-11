# 固定资产模块完善 — 设计文档

> 日期：2026-05-22
> 状态：approved
> 范围：omc-project1 固定资产模块全部 16 项缺口

---

## 一、数据模型变更

### 1.1 FixedAssetDepreciation 加 updated_at

```python
updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### 1.2 FixedAsset 加处置追踪字段

```python
disposal_date = Column(String(10), nullable=True, comment="处置日期")
disposal_proceeds = Column(Float, nullable=False, default=0, comment="处置收入")
disposal_gain_loss = Column(Float, nullable=False, default=0, comment="处置损益")
disposal_reason = Column(Text, nullable=True, comment="处置原因")
```

处置损益 = disposal_proceeds - net_value（处置时净值），写入时计算。

---

## 二、后端 API

### 2.1 新增端点

| 方法 | 路径 | 用途 |
|------|------|------|
| GET | `/assets/{asset_id}` | 单条资产查询 |
| PUT | `/depreciations/{dep_id}` | 修改折旧（重算累计+回写资产） |
| DELETE | `/depreciations/{dep_id}` | 删除折旧（扣减累计+恢复净值） |
| POST | `/depreciations/batch` | 批量计提全部/指定资产 |
| POST | `/assets/{asset_id}/dispose` | 专用处置（计算损益） |

### 2.2 批量计提逻辑 `POST /depreciations/batch`

```
请求: { company_id, period, asset_ids?: number[] }
逻辑:
  for each asset (status in ["使用中","闲置"], 未在该period已计提):
    按折旧方法计算月折旧额:
      直线法: (原值-残值) / (年限*12)
    校验: accumulated + amount <= 原值 - 残值
    创建折旧记录, 更新资产累计折旧和净值
返回: { success: [...], failed: [{asset_id, reason}] }
```

### 2.3 处置逻辑 `POST /assets/{asset_id}/dispose`

```
请求: { disposal_date, disposal_proceeds, disposal_reason, status }
  status 仅允许 "已处置" 或 "报废"
逻辑:
  gain_loss = disposal_proceeds - asset.net_value
  写入 asset 的四个处置字段 + status
  处置后该资产不可再计提折旧
```

### 2.4 校验规则（create_depreciation & batch）

- 同一 (fixed_asset_id, period) 唯一约束
- 计提后 accumulated <= original_value - residual_value
- 资产状态必须是 "使用中" 或 "闲置"
- 已处置/报废资产拒绝计提

### 2.5 列表端点增强

`GET /assets` 新增 query params:
- `limit`, `offset` — 分页
- `category`, `status`, `location` — 精确筛选
- `search` — 模糊匹配 name 和 asset_code

`GET /depreciations` 新增 `limit`, `offset`

### 2.6 Schema 变更

- 新增 `FixedAssetUpdate(BaseModel)` — 所有业务字段 Optional
- 新增 `FixedAssetDispose(BaseModel)` — disposal_date, disposal_proceeds, disposal_reason, status
- 新增 `BatchDepreciationRequest(BaseModel)` — company_id, period, asset_ids (Optional)
- `FixedAssetResponse` 加四个处置字段
- `FixedAssetDepreciationResponse` 加 updated_at

---

## 三、前端变更

### 3.1 去硬编码 company_id

所有固定资产生命周期视图从 `localStorage.getItem('companyId')` 读取公司 ID，与其他模块保持一致。

### 3.2 折旧计算移除前端逻辑

- FixedAssetRegister：删除 `calcDepreciation()`，`monthly_depreciation` 仍可为直线法手动设置
- FixedAssetDepreciation：计提对话框改为只选资产+期间，金额由后端计算后显示

### 3.3 折旧管理增强

- 折旧记录行增加"编辑"和"删除"按钮
- 编辑对话框可修改折旧金额
- 删除后自动重载列表

### 3.4 处置流程改造

- 从 `updateFixedAsset` 改为调用 `/assets/{asset_id}/dispose`
- 对话框增加"处置日期"、"处置收入"、"处置原因"字段
- 处置后列表自动刷新

### 3.5 资产台账增强

- 顶栏加搜索框（名称/编号模糊搜索）+ 类别/状态/地点下拉筛选
- 表格底部加分页控件

### 3.6 导出

- 资产台账和报表页面加"导出 CSV"按钮

### 3.7 API 函数新增

```ts
getFixedAsset(id)           // GET  /fixed-assets/assets/{id}
updateDepreciation(id, data) // PUT  /fixed-assets/depreciations/{id}
deleteDepreciation(id)       // DELETE /fixed-assets/depreciations/{id}
batchDepreciate(data)        // POST /fixed-assets/depreciations/batch
disposeAsset(id, data)       // POST /fixed-assets/assets/{id}/dispose
```

### 3.8 前端 API 函数签名更新

`listFixedAssets` 和 `listDepreciations` 增加 query params 支持（limit, offset, 筛选条件）。

---

## 四、测试验证

- 折旧重复期间校验 → 返回 400
- 已处置资产计提 → 返回 400
- 残值下限校验 → 返回 400
- 批量计提正确性 → 各资产金额正确，累计更新正确
- 删除折旧 → 资产净值正确恢复
- 处置损益计算 → 收入 - 净值 = 损益
- 前端 company_id → 多公司切换时不串数据
