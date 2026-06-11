# 费用报销模块 — 完整设计方案

> **项目**: omc-project1 企业智能管理系统
> **版本**: 1.0.0
> **日期**: 2026-05-18
> **状态**: 已确认

---

## 一、模块定位

面向企业全员的费用报销管理模块，覆盖费用报销、借款预支、费用标准管理，独立运行不与会计凭证自动联动。

### 关键决策

| 维度 | 决策 |
|------|------|
| 用户范围 | 全员使用 |
| 审批链 | 部门负责人 → 财务经理 → 财务总监 → 单位负责人（可选），按金额自动分级 |
| 费用类型 | 六大类：差旅费、办公费、招待费、交通费、通讯费、其他 |
| 会计对接 | 独立运行，不自动生成凭证 |
| 借款预支 | 支持：借款 → 报销冲销 → 多退少补 |
| 标准控制 | 柔性预警，终审人最终决定 |
| 费用标准 | 公司自维护，按国别/地区/部门/岗位灵活配置 |

---

## 二、数据模型

### 现有表（保留不改）

**`ExpenseItem`** — 费用项目字典（已有）
```
code, name, parent_code, tax_rate, is_active
```

### 新增表

**1. `ExpenseReport` — 报销单主表**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | |
| company_id | FK(companies) | 多公司隔离 |
| report_no | String(20) | 报销单号，格式 ER-YYYYMMDD-001 |
| applicant_id | FK(users) | 申请人 |
| department_id | FK(departments) | 申请部门 |
| expense_date | String(10) | 费用发生日期 |
| total_amount | Float | 报销总额 |
| loan_offset_amount | Float | 冲销借款金额，默认 0 |
| net_payable | Float | 实付金额 = total_amount - loan_offset_amount |
| status | String(20) | draft / submitted / dept_approved / finance_approved / director_approved / unit_head_approved / paid / closed / rejected |
| current_approver_id | FK(users) | 当前审批人 |
| approval_chain | JSON | 审批链记录 [{step, role, user_id, status, comment, timestamp}] |
| policy_warnings | JSON | 超标预警汇总 |
| notes | Text | 备注 |
| created_at | DateTime | |
| updated_at | DateTime | |

**2. `ExpenseReportItem` — 报销单明细行**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | |
| report_id | FK(expense_reports) | |
| row_seq | Integer | 行序号 |
| expense_item_id | FK(expense_items) | 费用类型 |
| date | String(10) | 发生日期 |
| amount | Float | 金额 |
| description | String(300) | 费用说明 |
| receipt_count | Integer | 发票张数，默认 0 |
| policy_check | JSON | 该行的标准检查结果 |

**3. `ExpenseLoan` — 借款单**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | |
| company_id | FK(companies) | 多公司隔离 |
| loan_no | String(20) | 借款单号 |
| applicant_id | FK(users) | 借款人 |
| department_id | FK(departments) | 借款部门 |
| loan_date | String(10) | 借款日期 |
| amount | Float | 借款金额 |
| repaid_amount | Float | 已还金额，默认 0 |
| reason | Text | 借款事由 |
| status | String(20) | submitted / approved / partial_repaid / fully_repaid / closed |
| expected_repay_date | String(10) | 预计还款日期 |
| notes | Text | 备注 |
| created_at | DateTime | |
| updated_at | DateTime | |

**4. `ExpensePolicy` — 费用标准**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | |
| company_id | FK(companies) | 所属公司 |
| expense_item_id | FK(expense_items) | 费用类型 |
| country | String(10) | 国别（可选） |
| region | String(50) | 地区（可选） |
| department_id | FK(departments) | 适用部门（可选） |
| position_level | Integer | 适用岗位级别（可选） |
| policy_type | String(20) | daily / event / per_person |
| max_amount | Float | 上限金额 |
| currency | String(5) | 币种，默认 CNY |
| effective_from | String(10) | 生效日期 |
| effective_to | String(10) | 失效日期（可选） |
| notes | String(300) | 备注（政策依据等） |

> 所有费用标准由公司管理员人工填入修改，非系统强制。匹配时逐级找最具体的标准。超标仅做预警提示，不阻塞提交。

**5. `ExpenseAttachment` — 报销附件**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | |
| report_id | FK(expense_reports) | 关联报销单（可空） |
| loan_id | FK(expense_loans) | 关联借款单（可空） |
| file_name | String(200) | 强制规范命名 |
| category | String(20) | 发票/机票/车票/合同/签收单/其他 |
| doc_number | String(100) | 票据号码 |
| file_path | String(300) | 存储路径 |
| file_size | Integer | 文件大小（bytes） |
| uploaded_at | DateTime | |

**附件命名规范**：`{序号}-{类别}-{号码}-{备注}.{ext}`
- 序号：每单从 01 开始
- 类别：发票、机票、车票、合同、签收单、其他
- 号码：票据号，无则填 `-`
- 备注：简短说明，无则填 `-`

示例：`01-发票-01123456-北京出差住宿.pdf`

---

## 三、审批流程

### 状态流转

```
draft
  ↓ submit
submitted
  ↓ approve (部门负责人)
dept_approved
  ↓ approve (财务经理)
finance_approved
  ↓ approve (财务总监)        ← 金额 > 中额度时需此节点
director_approved
  ↓ approve (单位负责人)       ← 可选，按配置决定
unit_head_approved
  ↓ pay
paid
  ↓ close
closed
```

任意审批节点可 → `rejected`（退回申请人，修改后重新提交）
申请人在 `submitted` / `dept_approved` 状态可撤回 → `draft`

### 金额分级

| 条件 | 审批链 |
|------|--------|
| 总额 ≤ 小额度 | 部门负责人 → paid |
| 总额 ≤ 中额度 | 部门负责人 → 财务经理 → paid |
| 总额 > 中额度 | 部门负责人 → 财务经理 → 财务总监 → (可选：单位负责人) → paid |

阈值由费用标准中配置，默认：小额度 2000，中额度 10000。

### 审批人匹配

| 审批角色 | 匹配规则 |
|----------|---------|
| 部门负责人 | 申请人所在 Department.manager |
| 财务经理 | 同公司 role = finance_manager 的用户 |
| 财务总监 | 同公司 role = finance_director 的用户 |
| 单位负责人 | 同公司 role = super_admin 的用户（可选加签） |

### 借款冲销

- 报销单创建时检测申请人是否有未还清的借款
- 申请人可选择用报销款全额或部分冲销借款
- 冲销后：
  - 借款 repaid_amount 增加
  - 净支付 = total_amount - loan_offset_amount
  - 如净支付为负（报销不足冲销），申请人需补还差额

---

## 四、后端 API

### 路由: `/api/expenses`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/reports` | 报销单列表（分页、筛选） | 认证用户 |
| POST | `/reports` | 新建报销单 | 认证用户 |
| GET | `/reports/{id}` | 报销单详情 | 认证用户 |
| PUT | `/reports/{id}` | 更新草稿报销单 | 创建人 |
| POST | `/reports/{id}/submit` | 提交审批 | 创建人 |
| POST | `/reports/{id}/approve` | 审批通过 | 当前审批人 |
| POST | `/reports/{id}/reject` | 审批驳回 | 当前审批人 |
| POST | `/reports/{id}/pay` | 确认付款 | 财务经理/总监 |
| POST | `/reports/{id}/cancel` | 撤回 | 创建人 |
| GET | `/items` | 费用项目列表 | 认证用户 |
| POST | `/items` | 新增费用项目 | 财务经理+ |
| PUT | `/items/{id}` | 编辑费用项目 | 财务经理+ |
| GET | `/loans` | 借款单列表 | 认证用户 |
| POST | `/loans` | 新建借款申请 | 认证用户 |
| POST | `/loans/{id}/approve` | 借款审批 | 财务经理+ |
| POST | `/loans/{id}/repay` | 借款还款 | 财务经理+ |
| GET | `/policies` | 费用标准列表 | 认证用户 |
| POST | `/policies` | 新增费用标准 | 财务经理+ |
| PUT | `/policies/{id}` | 编辑费用标准 | 财务经理+ |
| DELETE | `/policies/{id}` | 删除费用标准 | 财务经理+ |
| POST | `/attachments` | 上传附件 | 认证用户 |
| DELETE | `/attachments/{id}` | 删除附件 | 创建人 |
| GET | `/reports/{id}/attachments` | 报销单附件列表 | 认证用户 |
| GET | `/stats` | 报销汇总统计 | 财务经理+ |

### 关键业务逻辑

**提交审批时：**
1. 校验必填字段和明细行
2. 遍历明细行，匹配费用标准，超标项记录到 `policy_warnings`
3. 按总额确定审批链
4. 生成审批链 JSON，设置 `current_approver_id`
5. 状态从 draft → submitted

**审批通过时：**
1. 验证当前用户为 `current_approver_id`
2. 推进审批链到下一节点
3. 如为最后一级，状态变为 `paid` 或 `unit_head_approved` → `paid`

**借款冲销：**
1. 付款时如 `loan_offset_amount > 0`，增加对应借款的 `repaid_amount`
2. 借款全额还清 → `fully_repaid`

---

## 五、前端页面

### 目录结构

```
frontend/src/
├── views/expenses/
│   ├── ExpenseReportForm.vue      # 7.1 报销申请
│   ├── ExpenseReportList.vue      # 7.2 报销列表
│   ├── ExpenseLoanList.vue        # 7.3 借款管理
│   ├── ExpenseItems.vue           # 7.4 费用项目
│   ├── ExpensePolicies.vue        # 7.5 费用标准
│   └── ExpenseReports.vue         # 7.6 报销查询统计
├── api/
│   └── expenses.ts                # 费用报销 API 函数
```

### 菜单更新（`menuConfig.ts` — 第七组）

```
7.1 报销申请    → /finance/expenses/report-form
7.2 报销列表    → /finance/expenses/report-list
7.3 借款管理    → /finance/expenses/loans
7.4 费用项目    → /finance/expenses/items
7.5 费用标准    → /finance/expenses/policies
7.6 查询统计    → /finance/expenses/reports
```

### 页面要点

**7.1 报销申请** (`ExpenseReportForm.vue`)
- 自动填入报销人、部门、日期
- 明细行：费用类型下拉 + 金额 + 日期 + 描述 + 发票张数
- 超标行内黄色预警（⚠ 超过标准 ¥XX）
- 附件上传区域，强制规范命名，预览和删除
- 如有未还借款，显示"可冲销借款"提示区
- 保存草稿 / 提交审批

**7.2 报销列表** (`ExpenseReportList.vue`)
- Tab: 我的报销 | 待我审批 | 全部报销
- 状态标签颜色：draft灰 / submitted蓝 / approved绿 / paid深绿 / rejected红
- 列表列：单号、申请人、部门、金额、状态、日期、操作
- 审批操作弹窗：通过/驳回 + 意见

**7.3 借款管理** (`ExpenseLoanList.vue`)
- 借款申请表单（金额、事由、预计还款日期）
- 借款列表（状态：待审批/已批准/部分已还/已还清）
- 还款操作

**7.4 费用项目** (`ExpenseItems.vue`)
- 树形表格展示六大类及子项
- CRUD 操作

**7.5 费用标准** (`ExpensePolicies.vue`)
- 筛选：国别/地区/费用类型
- 列表：费用类型、国别、地区、部门、岗位、上限、币种、有效期
- 新增/编辑/删除

**7.6 查询统计** (`ExpenseReports.vue`)
- 按时间/部门/费用类型/状态筛选
- 汇总统计（总额/分类汇总/部门汇总）
- 导出（预留）

---

## 六、角色权限

| 操作 | cashier | accountant | finance_manager | finance_director | super_admin |
|------|---------|------------|-----------------|------------------|-------------|
| 提交报销单 | ✓ | ✓ | ✓ | ✓ | ✓ |
| 查看本人报销 | ✓ | ✓ | ✓ | ✓ | ✓ |
| 部门审批 | (部门负责人) | (部门负责人) | (部门负责人) | (部门负责人) | ✓ |
| 财务经理审批 | | | ✓ | ✓ | ✓ |
| 财务总监审批 | | | | ✓ | ✓ |
| 单位负责人审批 | | | | | ✓ |
| 确认付款 | | | ✓ | ✓ | ✓ |
| 维护费用项目 | | | ✓ | ✓ | ✓ |
| 维护费用标准 | | | ✓ | ✓ | ✓ |
| 查看全公司报销 | | ✓ | ✓ | ✓ | ✓ |
| 报销统计 | | | ✓ | ✓ | ✓ |

---

## 七、实现范围

### 本次开发（第一批）

- 全部 5 张数据表 + 数据库迁移
- 全部后端 API（`/api/expenses` 路由）
- 全部 6 个前端页面
- 侧边栏菜单解锁
- 审批流程 + 金额分级
- 费用标准匹配与预警
- 借款与冲销闭环
- 附件上传与规范命名
- 多公司隔离
- 审计日志记录

### 后续迭代（不在本次范围）

- 自动生成会计凭证
- 与预算模块联动
- 导出功能

---

## 修订历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0.0 | 2026-05-18 | 初版，全员报销+借款+审批+费用标准 |
