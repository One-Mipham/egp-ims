# General Ledger (总账) Module Design Spec

> **版本**: 0.1.0
> **日期**: 2026-05-21
> **项目**: omc-project1 — 企业智能管理系统

## 1. 概述

总账模块是企业智能管理系统的核心财务模块。本设计将 11 条路由精简为 8 个菜单项：

- 3 条与已有功能重叠的路由（记账、反记账、凭证审核）通过导航整合重定向到 `/finance/vouchers`
- 2 条已有报表/打印的（现金流量、账簿打印）重定向到对应模块
- 6 个全新功能从零开发：自动转账、科目账、辅助账、自定义账、自定义明细表、往来管理

## 2. 菜单结构（精简后）

```
11.2 总账
├── 凭证          → /finance/vouchers (已有)
├── 自动转账      → /finance/gl/auto-transfer (新)
├── 科目账        → /finance/gl/subject-ledger (新)
├── 辅助账        → /finance/gl/aux-ledger (新)
├── 自定义账      → /finance/gl/custom-ledger (新)
├── 自定义明细表  → /finance/gl/custom-detail (新)
├── 往来管理      → /finance/gl/transactions (新)
├── 现金流量      → /finance/reports?tab=cashflow (重定向)
├── 账簿打印      → /finance/print (重定向)
└── 初始化导航    → /finance/init (已有)
```

## 3. 新增数据模型

### 3.1 AutoTransferTemplate — 自动转账模板

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | PK |
| company_id | int | FK -> companies，公司隔离 |
| name | str(100) | 模板名称 |
| description | str(500) | 说明 |
| template_type | str(20) | `fixed` / `ratio` / `balance` |
| frequency | str(20) | `manual` / `monthly` / `quarterly` / `yearly` |
| is_active | bool | 启用/停用 |
| entries | JSON | 分录定义列表 |
| created_by | int | FK -> users |
| created_at | datetime | |
| updated_at | datetime | |

**entries JSON 结构：**
```json
[
  {
    "account_code": "6001",
    "direction": "credit",
    "formula": "100%",
    "summary": "结转主营业务收入"
  }
]
```

### 3.2 CustomQuery — 保存的自定义查询

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | PK |
| company_id | int | FK -> companies |
| name | str(100) | 查询名称 |
| query_type | str(20) | `subject` / `aux` / `detail` |
| filters | JSON | 保存的筛选条件 |
| created_by | int | FK -> users |
| created_at | datetime | |
| updated_at | datetime | |

服务对象：自定义账 + 自定义明细表，共用此模型。

## 4. API 端点（全部在 `/api/gl` 前缀下）

### 4.1 自动转账

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/gl/auto-transfer-templates` | 模板列表 |
| POST | `/api/gl/auto-transfer-templates` | 创建模板 |
| PUT | `/api/gl/auto-transfer-templates/{id}` | 更新模板 |
| DELETE | `/api/gl/auto-transfer-templates/{id}` | 删除模板 |
| POST | `/api/gl/auto-transfer-templates/{id}/execute` | 执行转账，生成凭证 |

**execute 逻辑**：读取模板 entries → 按 formula 计算金额（fixed 取固定值，ratio 查科目余额×百分比，balance 取科目余额）→ 创建 Voucher + VoucherEntry 行 → 返回凭证 ID。

### 4.2 科目账

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/gl/subject-ledger` | 多科目汇总查询 |
| GET | `/api/gl/subject-ledger/{account_code}` | 单科目明细查询 |

查询参数：account_code, start_period, end_period, level, include_zero

### 4.3 辅助账

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/gl/aux-ledger` | 辅助维度明细查询 |

查询参数：aux_type (department/person/counterparty/project), aux_id, account_code(可选), start_period, end_period

### 4.4 自定义账

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/gl/custom-queries` | 已保存查询列表 |
| POST | `/api/gl/custom-queries` | 保存查询 |
| PUT | `/api/gl/custom-queries/{id}` | 更新查询 |
| DELETE | `/api/gl/custom-queries/{id}` | 删除查询 |
| GET | `/api/gl/custom-queries/{id}/execute` | 执行查询，返回结果 |

execute 根据 query_type 调用对应查询逻辑（subject→科目账 / aux→辅助账 / detail→自定义明细）。

### 4.5 自定义明细表

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/gl/custom-detail/columns` | 获取可用列定义 |
| POST | `/api/gl/custom-detail/query` | 执行自定义查询 |
| GET | `/api/gl/custom-detail/export` | 导出 CSV |

### 4.6 往来管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/gl/transactions/balance` | 往来单位余额汇总 |
| GET | `/api/gl/transactions/{counterparty_id}` | 单个往来单位明细 |
| GET | `/api/gl/transactions/aging` | 账龄分析（0-30/31-90/91-180/181-365/365+天） |

## 5. 前端组件

| 组件 | 路由 | 复杂度 |
|------|------|--------|
| AutoTransfer.vue | `/finance/gl/auto-transfer` | 中：模板卡片列表 + 创建/编辑弹窗 + 执行按钮 |
| SubjectLedger.vue | `/finance/gl/subject-ledger` | 中：科目选择 + 期间筛选 + 账页表格 |
| AuxLedger.vue | `/finance/gl/aux-ledger` | 中：维度切换 + 对象选择 + 账页表格 |
| CustomLedger.vue | `/finance/gl/custom-ledger` | 低：保存查询 + 加载执行 + 复用科目/辅助账结果展示 |
| CustomDetail.vue | `/finance/gl/custom-detail` | 高：列选择器 + 条件构建 + 数据表格 + 导出 |
| Transactions.vue | `/finance/gl/transactions` | 中：余额汇总表 + 点击穿透明细 + 账龄选项卡 |

## 6. 后端实施架构

新增文件：
- `backend/app/routers/gl.py` — 路由处理器，注册到 main.py 为 `/api/gl`
- `backend/app/models.py` — 追加 `AutoTransferTemplate`、`CustomQuery` 两个模型
- `backend/app/schemas/__init__.py` — 追加对应 Pydantic schemas
- 前端 `frontend/src/api/index.ts` — 追加 GL API 函数

不新增文件，纯查询的：科目账、辅助账、往来管理 — 完全在 gl.py router 中实现。

## 7. 依赖关系

- 所有端点依赖 `get_current_user` → 验证登录状态
- 所有端点依赖 `get_current_company` → 数据隔离
- 自动转账 execute 依赖已有 Voucher 模型创建凭证
- 科目账/辅助账/往来管理 纯查询已有 VoucherEntry
- 自定义查询 依赖 CustomQuery 模型

## 8. 测试策略

- 后端单元测试覆盖每个端点（HTTP 200 + 正确响应结构）
- 自动转账 execute 测试：验证生成的 Voucher 和 VoucherEntry 正确性
- 科目账/辅助账 测试：验证期初/本期/期末金额计算正确
- 往来账龄测试：验证各账龄段金额分区正确
