# 投资管理模块 — 设计规格

> **版本**: 0.1.0 | **日期**: 2026-05-08 | **维护人**: 技术委员会
> **状态**: 已确认 — 待实施

## 1. 范围与定位

**当前阶段：B 方案 — 投资会计记录系统**

以会计视角记录投资活动——投资成本、公允价值变动、投资收益/亏损、减值准备等与总账科目对接。侧重财务核算准确性和合规报告。

**后续演进**：预留 A/C 方案路由，未来可扩展为全功能投资管理（基金结构、LP/GP、Waterfall、IRR 等）。

## 2. 菜单结构

在现有 `投资管理` 菜单下，采用 **统一台账 + 按类型筛选** 模式：

```
📊 投资管理
├─ 📋 投资组合总览（按类型筛选：VC/PE/股权/二级/另类）
├─ 💼 投资持仓（持仓明细 + 公允价值）
├─ 🔄 投资交易（买入/卖出/赎回/资本召唤/分配）
├─ 💰 投资收益（分红/利息/已实现/未实现损益）
└─ 📈 投资报表（持仓报告/损益报告/公允价值变动表）
```

投资类型通过 `investment_type` 字段区分：`vc` / `pe` / `general_equity` / `secondary_market` / `alternative`。

## 3. 集成深度

**B 方案：自动凭证生成**

- 投资交易录入后，系统自动生成对应的会计凭证（Voucher + VoucherEntry）
- 凭证可预览/编辑后再过账
- 通过 `AccountMapping` 表定义交易类型 → 会计科目的映射规则

## 4. 数据模型

### 新表 6 张

#### 4.1 InvestmentPortfolio — 投资组合

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | |
| company_id | FK → companies | 多公司隔离 |
| name | VARCHAR(200) | 组合名称 |
| investment_type | VARCHAR(20) | vc / pe / general_equity / secondary_market / alternative |
| currency | CHAR(3) | CNY/USD/HKD |
| status | VARCHAR(16) | active / closed / liquidated |
| description | TEXT | 备注 |

#### 4.2 InvestmentPosition — 投资持仓

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | |
| portfolio_id | FK → investment_portfolios | |
| account_code | VARCHAR(10) | 对应会计科目（1101/1501/1503/1511） |
| security_name | VARCHAR(200) | 标的名称 |
| security_code | VARCHAR(50) | 股票代码/基金代码 |
| quantity | DECIMAL(18,6) | 持仓数量 |
| unit_cost | DECIMAL(18,6) | 单位成本 |
| cost_amount | DECIMAL(18,2) | 成本总额 |
| fair_value | DECIMAL(18,2) | 当前公允价值 |
| fair_value_date | DATE | 估值日期 |
| valuation_method | VARCHAR(30) | market_price / cost / dcf / comparables |
| counterparty_id | FK → counterparties (nullable) | 被投资方 |
| status | VARCHAR(16) | active / exited / impaired |

#### 4.3 InvestmentTransaction — 投资交易

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | |
| position_id | FK → investment_positions | |
| transaction_type | VARCHAR(20) | buy / sell / capital_call / distribution / dividend / interest |
| transaction_date | DATE | |
| quantity | DECIMAL(18,6) | |
| price | DECIMAL(18,6) | |
| amount | DECIMAL(18,2) | 交易金额 |
| fee | DECIMAL(18,2) | 手续费 |
| voucher_id | FK → vouchers (nullable) | 自动生成的凭证 |
| counterparty_id | FK → counterparties (nullable) | |
| notes | TEXT | |

#### 4.4 FairValueAdjustment — 公允价值调整

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | |
| position_id | FK → investment_positions | |
| adjustment_date | DATE | |
| previous_value | DECIMAL(18,2) | |
| adjusted_value | DECIMAL(18,2) | |
| change_amount | DECIMAL(18,2) | 调整差额 |
| reason | VARCHAR(200) | 调整原因 |
| voucher_id | FK → vouchers (nullable) | 自动生成的凭证 |

#### 4.5 InvestmentIncome — 投资收益

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | |
| position_id | FK → investment_positions (nullable) | 可为空（portfolio 级别收入） |
| income_type | VARCHAR(20) | dividend / interest / realized_gain / unrealized_gain / other |
| income_date | DATE | |
| amount | DECIMAL(18,2) | |
| voucher_id | FK → vouchers (nullable) | 自动生成的凭证 |
| notes | TEXT | |

#### 4.6 AccountMapping — 科目映射

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | |
| transaction_type | VARCHAR(30) | e.g., buy / sell / dividend / fair_value_up / fair_value_down |
| investment_type | VARCHAR(20) | 可为空，按投资类型可覆盖 |
| debit_account_code | VARCHAR(10) | |
| credit_account_code | VARCHAR(10) | |
| description_template | VARCHAR(200) | 凭证摘要模板 |

### 预置科目映射

| transaction_type | debit | credit | 说明 |
|---|---|---|---|
| buy | 1101/1503/1511 | 1002 | 按持仓科目 |
| sell | 1002 | 1101/1503/1511 | |
| dividend | 1002 | 6111 | 分红收入 |
| interest | 1002 | 6111 | 利息收入 |
| fair_value_up | 1101/1503 | 6101 | 公允价值上涨 |
| fair_value_down | 6101 | 1101/1503 | 公允价值下跌 |
| capital_call | 1511 | 1002 | PE 资本召唤 |
| distribution | 1002 | 1511 | PE 分配返还 |

## 5. 前/后端实现清单

### 5.1 后端（FastAPI）

**新文件**：
- `backend/app/models.py` — 新增 6 个 SQLAlchemy 模型
- `backend/app/schemas.py` — 新增 Pydantic schema
- `backend/app/routers/investments.py` — CRUD + 自动凭证生成
- `backend/app/seed.py` — 预置 AccountMapping 数据

**API 路由** (前缀 `/api/investments`)：
- `GET/POST /portfolios` — 投资组合 CRUD
- `GET/POST /positions` — 持仓 CRUD
- `GET/POST /transactions` — 交易 CRUD（保存时自动生成凭证）
- `GET/POST /adjustments` — 公允价值调整
- `GET /income` — 收益列表
- `GET /reports/positions` — 持仓报告
- `GET /reports/income` — 收益报告
- `GET /reports/fair-value` — 公允价值变动报告

### 5.2 前端（Vue 3 + PrimeVue）

**新建页面**（替换现有占位路由）：
- `frontend/src/views/InvestmentPortfolio.vue` — 投资组合总览
- `frontend/src/views/InvestmentPositions.vue` — 持仓管理
- `frontend/src/views/InvestmentTransactions.vue` — 交易管理 + 凭证预览
- `frontend/src/views/InvestmentIncome.vue` — 收益记录
- `frontend/src/views/InvestmentReports.vue` — 投资报表

**修改文件**：
- `frontend/src/router/index.ts` — 更新路由指向新组件
- `frontend/src/App.vue` — 更新菜单结构
- `frontend/src/api/index.ts` — 新增 API 函数

### 5.3 数据库迁移

- 新建 6 张表
- 执行 `python backend/seed.py` 预置科目映射数据

## 6. 预留扩展路由（A/C 方案）

以下路由保留为占位，指向 PlaceholderPage，供未来升级全功能系统时使用：

- `/finance/investments/funds` — 基金管理
- `/finance/investments/investors` — LP 投资管理
- `/finance/investments/performance` — 绩效分析 (IRR/MOIC/TVPI)
- `/finance/investments/waterfall` — 分配瀑布
- `/finance/investments/securities` — 证券主数据（二级市场）
- `/finance/investments/real-estate` — 房地产资产
- `/finance/investments/infrastructure` — 基础设施资产
- `/finance/investments/private-credit` — 私募信贷资产

## 7. 行业参考

本设计参考了以下行业标准和系统：
- ILPA 2.0 报告模板（PE/VC 报告标准）
- 黑石、红杉、软银、凯雷等机构的投资管理实践
- eFront / Investran / Allvue 等商业系统的数据模型设计原则

完整研究报告见 `docs/superpowers/specs/2026-05-08-investment-industry-research.md`。

---

*本规格由 omc-project1 技术团队维护，每季度复审一次。*
