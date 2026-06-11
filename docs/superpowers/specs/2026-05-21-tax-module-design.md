# 税务管理模块设计

> **日期**: 2026-05-21
> **状态**: 设计中 → 待实现
> **模式**: 记录追踪型（手动录入，不自动计算）

## 一、范围

覆盖菜单 11.3 税务管理下全部 18 个占位页面 + 1 个已实现页面（`TaxCustomers.vue` 不动）：

| 类别 | 页面数 | 菜单项 |
|------|--------|--------|
| 发票管理 | 3 | 销项发票、进项发票、发票查询统计 |
| 税种管理 | 11 | 增值税、城建税、教育费附加、地方教育附加、企业所得税、个税代扣代缴、印花税、房产税、土地使用税、车船税、土地增值税 |
| 罚款滞纳金 | 1 | 罚款与滞纳金 |
| 申报表 | 3 | 增值税申报表、所得税申报表、其他税种申报汇总 |

## 二、数据模型

### TaxDeclaration（统一税种申报）

覆盖 11 税种 + 罚款滞纳金，通过 `tax_type` 区分。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | Integer PK | - | 主键 |
| company_id | FK → companies.id | Y | 公司账套隔离 |
| tax_type | String(30) | Y | vat / urban / education / local_edu / corporate_income / iit / stamp_duty / property_tax / land_use_tax / vehicle_tax / land_vat / penalty |
| period_start | Date | Y | 计税期间起始 |
| period_end | Date | Y | 计税期间截止 |
| tax_base | Float | N | 税基（计税依据） |
| tax_rate | Float | N | 税率（%），展示用 |
| tax_amount | Float | Y | 税额 |
| paid_amount | Float | N | 已缴金额，默认 0 |
| status | String(20) | Y | pending → filed → paid，默认 pending |
| declaration_date | Date | N | 申报日期 |
| payment_deadline | Date | N | 缴纳截止日 |
| payment_date | Date | N | 实际缴纳日 |
| created_by | Integer | N | 创建人 user_id |
| notes | Text | N | 备注 |

### TaxInvoice（发票管理）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | Integer PK | - | 主键 |
| company_id | FK → companies.id | Y | 公司账套隔离 |
| invoice_type | String(10) | Y | sales / purchase |
| invoice_number | String(50) | Y | 发票号码 |
| invoice_date | Date | Y | 开票日期 |
| counterparty_id | FK → counterparties.id | N | 对方单位 |
| amount | Float | Y | 不含税金额 |
| tax_rate | Float | Y | 税率（%） |
| tax_amount | Float | Y | 税额 |
| total_amount | Float | Y | 价税合计 |
| category | String(30) | N | 商品/服务类别 |
| status | String(20) | Y | draft → issued → verified，默认 draft |
| notes | Text | N | 备注 |

## 三、后端

### Router: `routers/taxes.py`
### Schemas: `schemas/taxes.py`
### 注册: `/api/taxes`

**TaxDeclaration 端点（6 个）**：
- `GET /api/taxes/declarations` — 列表，支持 `?tax_type=&status=&company_id=&period_start=&period_end=`
- `GET /api/taxes/declarations/{id}` — 详情
- `POST /api/taxes/declarations` — 新增
- `PUT /api/taxes/declarations/{id}` — 更新
- `DELETE /api/taxes/declarations/{id}` — 删除
- `GET /api/taxes/declarations/summary` — 按 tax_type 分组汇总（应缴/已缴/未缴），用于申报表

**TaxInvoice 端点（6 个）**：
- `GET /api/taxes/invoices` — 列表，支持 `?invoice_type=&status=&company_id=&counterparty_id=&date_from=&date_to=`
- `GET /api/taxes/invoices/{id}` — 详情
- `POST /api/taxes/invoices` — 新增
- `PUT /api/taxes/invoices/{id}` — 更新
- `DELETE /api/taxes/invoices/{id}` — 删除
- `GET /api/taxes/invoices/summary` — 按类型/月份汇总统计

## 四、前端

### API 文件: `api/taxes.ts`
### 组件（3 个覆盖 18 页）：

| 组件 | 路由 | 覆盖菜单 |
|------|------|---------|
| `TaxInvoiceList.vue` | `/finance/tax/invoice/:mode` (sales / purchase / query) | 销项发票、进项发票、发票查询统计 |
| `TaxDeclarationList.vue` | `/finance/tax/declaration/:taxType` | 11 税种 + 罚款滞纳金 |
| `TaxReport.vue` | `/finance/tax/reports/:reportType` (vat / cit / other) | 3 个申报表 |

### 组件行为：

**TaxInvoiceList.vue**：
- 按 `mode` 参数预筛选发票类型
- `sales` / `purchase`：标准 CRUD 表格 + 对话框
- `query`：跨类型查询，额外支持日期范围、对方单位、类别的组合筛选
- 表格列：发票号、日期、对方单位名称、金额、税率、税额、价税合计、状态
- 状态流转：draft → issued → verified

**TaxDeclarationList.vue**：
- 按 `taxType` 参数筛选税种
- 页头动态显示当前税种名称
- CRUD 表格 + 对话框
- 表格列：计税期间、税基、税率、税额、已缴金额、未缴金额、状态、申报日期、缴纳日期
- 状态流转：pending → filed → paid
- 罚款类型（penalty）：隐藏税基/税率列，显示处罚原因/处罚机关

**TaxReport.vue**：
- 调用 `/declarations/summary` 接口获取汇总数据
- `vat`：仅增值税汇总卡片
- `cit`：企业所得税汇总卡片
- `other`：其余所有税种汇总列表
- 每个卡片：本期应缴、已缴、未缴，带期间筛选器

### 路由变更：
- 18 条占位路由 → 3 条参数化路由
- 菜单保持不变（19 项，不同 to 指向同一组件带不同参数）

## 五、权限

沿用现有四级内控模式（simplified / standard / strict），所有税务端点要求认证，写操作检查角色权限（admin / manager 可写，clerk 只读）。

## 六、测试

- 后端：pytest 覆盖 CRUD + 筛选 + 汇总端点
- 前端：手动验证 3 个组件在各参数模式下的表现
- 测试账号：Company 1 (admin/admin123)
