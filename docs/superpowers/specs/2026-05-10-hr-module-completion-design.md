# HR 模块补全 — 设计文档

> 日期：2026-05-10 | 状态：待审核 | 项目：omc-project1

## 1. 概述

在现有 HR 模块（制度/职级/入职/培训/考核/奖惩/离职/预算）基础上，补充以下功能：

- 假期申请与审批
- 月度工资表（编制→审核→审批→提交财务→发放）
- 薪酬调整、部门调动、岗位调整（统一审批流）
- 员工档案管理、HR 专属公司文件管理
- 部门设置入口

### 设计原则

- 统一审批任务表 — 所有 HR 变动共用一张 `approval_tasks` 表
- 月度工资表升级为独立的明细表 + 批次表，原 `hr_salaries` 废弃
- 审批通过后自动更新 HrEmployee 对应字段
- 薪酬预算（财管模块）列数精简为汇总大类

---

## 2. 数据模型

### 2.1 HrEmployee 升级（加 2 列）

```
hr_employees
  + base_salary               Float   基本工资
  + social_insurance_base     Float   社保缴费基数（默认=base_salary）
```

### 2.2 社保比例配置 `hr_si_rates`（新增）

| 列 | 类型 | 默认值 | 说明 |
|----|------|--------|------|
| id | Integer PK | | |
| company_id | FK companies | | |
| pension_personal | Float | 0.08 | 养老个人 |
| pension_company | Float | 0.16 | 养老公司 |
| medical_personal | Float | 0.02 | 医疗个人 |
| medical_company | Float | 0.08 | 医疗公司 |
| unemployment_personal | Float | 0.005 | 失业个人 |
| unemployment_company | Float | 0.005 | 失业公司 |
| injury_company | Float | 0.005 | 工伤（仅公司） |
| maternity_company | Float | 0.008 | 生育（仅公司） |
| housing_fund_personal | Float | 0.07 | 公积金个人（5-12%） |
| housing_fund_company | Float | 0.07 | 公积金公司（5-12%） |
| tax_threshold | Float | 5000 | 个税起征点 |
| si_base_lower | Float | NULL | 社保基数下限 |
| si_base_upper | Float | NULL | 社保基数上限 |
| created_at, updated_at | DateTime | | |

每家公司一条记录，提供默认值和手动覆盖。

### 2.3 月度工资批次 `hr_payroll_batches`（新增）

| 列 | 类型 | 说明 |
|----|------|------|
| id | Integer PK | |
| company_id | FK companies | |
| year_month | String(7) | "2026-05" |
| status | String(20) | draft→reviewed→approved→submitted→disbursed |
| total_amount | Float | 应发合计 |
| total_net | Float | 实发合计 |
| created_by | Integer FK users | |
| created_at, updated_at | DateTime | |

状态流转：`draft → reviewed → approved → submitted → disbursed`

### 2.4 月度工资明细 `hr_salary_details`（新增，替代原 hr_salaries）

#### 基本信息

| 列 | 类型 | 说明 |
|----|------|------|
| id | Integer PK | |
| batch_id | FK payroll_batches | |
| employee_id | FK hr_employees | |
| department_id | Integer | 冗余，用于部门分组 |
| row_order | Integer | 排序 |

#### 薪酬项

| 列 | 类型 | 说明 |
|----|------|------|
| base_salary | Float | 基本工资（从 HrEmployee 带入） |
| mobile_allowance | Float | 手机补贴 |
| meal_allowance | Float | 餐费补贴 |
| transport_allowance | Float | 交通补贴 |
| other_allowance | Float | 其他补贴（手动） |
| allowance_subtotal | Float | 补贴小计（自动） |

#### 五险一金 — 个人部分（4 列有值 + 合计）

| 列 | 类型 | 计算 |
|----|------|------|
| si_pension_personal | Float | base×0.08 |
| si_medical_personal | Float | base×0.02 |
| si_unemployment_personal | Float | base×0.005 |
| si_housing_fund_personal | Float | base×比例 |
| si_personal_total | Float | 以上四项之和 |

#### 五险一金 — 公司部分（6 列有值 + 合计）

| 列 | 类型 | 计算 |
|----|------|------|
| si_pension_company | Float | base×0.16 |
| si_medical_company | Float | base×0.08 |
| si_unemployment_company | Float | base×0.005 |
| si_injury_company | Float | base×0.005 |
| si_maternity_company | Float | base×0.008 |
| si_housing_fund_company | Float | base×比例 |
| si_company_total | Float | 以上六项之和 |

#### 专项附加扣除（7 项 + 合计）

| 列 | 类型 | 说明 |
|----|------|------|
| ded_children_edu | Float | 子女教育 |
| ded_continuing_edu | Float | 继续教育 |
| ded_major_medical | Float | 大病医疗 |
| ded_housing_loan | Float | 住房贷款利息 |
| ded_housing_rent | Float | 住房租金 |
| ded_elderly_care | Float | 赡养老人 |
| ded_infant_care | Float | 婴幼儿照护 |
| ded_total | Float | 七项之和（自动） |

#### 个税计算

| 列 | 类型 | 计算 |
|----|------|------|
| taxable_income | Float | base_salary + allowance_subtotal − si_personal_total − ded_total − 5000 |
| tax_rate | Float | 查表（0.03/0.1/0.2/0.25/0.3/0.35/0.45） |
| quick_deduction | Float | 速算扣除数 |
| income_tax | Float | taxable × rate − quick_deduction |
| net_salary | Float | base + allowances − si_personal − income_tax |

#### 其他

| 列 | 类型 |
|----|------|
| notes | Text |
| is_manual_override | Bool（每列可手动覆盖自动计算结果） |

### 2.5 假期类型 `hr_leave_types`（新增）

| 列 | 类型 | 说明 |
|----|------|------|
| id | Integer PK | |
| company_id | FK companies | |
| name | String(50) | 年假/事假/病假/婚假/产假/陪产假/丧假/工伤假 |
| default_days_per_year | Float | 每年默认天数 |
| is_paid | Bool | 是否带薪 |

### 2.6 假期申请 `hr_leave_applications`（新增）

| 列 | 类型 | 说明 |
|----|------|------|
| id | Integer PK | |
| company_id | FK companies | |
| employee_id | FK hr_employees | |
| leave_type_id | FK hr_leave_types | |
| start_date | String(10) | |
| end_date | String(10) | |
| days | Float | 申请天数 |
| reason | Text | 事由 |
| remaining_days | Float | 当前剩余假期（审批时快照） |
| status | String(20) | draft→submitted→approved→rejected |
| created_at, updated_at | DateTime | |

### 2.7 薪酬调整 `hr_salary_adjustments`（新增）

| 列 | 类型 | 说明 |
|----|------|------|
| id | Integer PK | |
| company_id | FK companies | |
| employee_id | FK hr_employees | |
| old_base_salary | Float | |
| new_base_salary | Float | |
| adjust_type | String(20) | 普调/晋升/降薪/其他 |
| reason | Text | |
| status | String(20) | draft→submitted→approved→rejected→executed |
| effective_date | String(10) | 生效日期 |
| created_at | DateTime | |

审批通过（executed）→ 更新 `hr_employees.base_salary`

### 2.8 部门调动 `hr_department_transfers`（新增）

| 列 | 类型 | 说明 |
|----|------|------|
| id | Integer PK | |
| company_id | FK companies | |
| employee_id | FK hr_employees | |
| from_dept_id | FK departments | 必填 |
| to_dept_id | FK departments | 必填 |
| new_position_id | FK hr_positions | 可选（岗位跟随调整） |
| new_base_salary | Float | 可选（薪酬跟随调整） |
| reason | Text | |
| status | String(20) | draft→submitted→approved→rejected→executed |
| effective_date | String(10) | |
| created_at | DateTime | |

审批通过 → 更新 `hr_employees.department_id`，可选更新 position_id、base_salary

### 2.9 岗位调整 `hr_position_changes`（新增）

| 列 | 类型 | 说明 |
|----|------|------|
| id | Integer PK | |
| company_id | FK companies | |
| employee_id | FK hr_employees | |
| from_position_id | FK hr_positions | 必填 |
| to_position_id | FK hr_positions | 必填 |
| new_base_salary | Float | 可选（薪酬跟随调整） |
| reason | Text | |
| status | String(20) | draft→submitted→approved→rejected→executed |
| effective_date | String(10) | |
| created_at | DateTime | |

审批通过 → 更新 `hr_employees.position_id`，可选更新 base_salary

### 2.10 统一审批任务 `approval_tasks`（新增）

| 列 | 类型 | 说明 |
|----|------|------|
| id | Integer PK | |
| company_id | FK companies | |
| source_type | String(30) | leave / salary_adjust / dept_transfer / position_change / payroll_batch |
| source_id | Integer | 关联业务记录 ID |
| step | String(30) | 审批步骤名称 |
| assignee_id | FK users（NULL=任意审批人） | |
| status | String(20) | pending / approved / rejected |
| comment | Text | 审批意见 |
| created_at | DateTime | |
| processed_at | DateTime | |
| processed_by | FK users | |

### 2.11 HR 公司文件 `hr_documents`（新增）

| 列 | 类型 | 说明 |
|----|------|------|
| id | Integer PK | |
| company_id | FK companies | |
| title | String(200) | 文件标题 |
| doc_type | String(20) | 人事任免 / 奖惩通知 / 其他 |
| content | Text | 文件正文（或附件路径） |
| issued_by | String(50) | 发文单位 |
| issued_at | String(10) | 发文日期 |
| created_at | DateTime | |

---

## 3. API 路由

后端新增路由文件 `backend/app/routers/hr_extended.py`（或在现有 `hr.py` 中添加端点）：

| 方法 | 路径 | 说明 |
|------|------|------|
| **社保配置** | | |
| GET | /api/hr/si-rates | 获取公司社保比例配置 |
| POST | /api/hr/si-rates | 创建或更新社保比例配置 |
| **月度工资表** | | |
| GET | /api/hr/payroll-batches | 批次列表（按年月筛选） |
| POST | /api/hr/payroll-batches | 创建工资批次（生成明细行） |
| GET | /api/hr/payroll-batches/:id/details | 获取批次所有明细行 |
| PUT | /api/hr/payroll-batches/:id/details/:did | 更新某行数据（仅 draft） |
| POST | /api/hr/payroll-batches/:id/submit | 提交审批 → 创建 approval_task |
| **假期管理** | | |
| GET | /api/hr/leave-types | 假期类型列表 |
| POST | /api/hr/leave-types | 新增假期类型 |
| GET | /api/hr/leave-applications | 假期申请列表 |
| POST | /api/hr/leave-applications | 提交假期申请 → 创建 approval_task |
| GET | /api/hr/leave-applications/:id | 申请详情 |
| **薪酬调整** | | |
| GET | /api/hr/salary-adjustments | 列表 |
| POST | /api/hr/salary-adjustments | 新增 → 创建 approval_task |
| **部门调动** | | |
| GET | /api/hr/department-transfers | 列表 |
| POST | /api/hr/department-transfers | 新增 → 创建 approval_task |
| **岗位调整** | | |
| GET | /api/hr/position-changes | 列表 |
| POST | /api/hr/position-changes | 新增 → 创建 approval_task |
| **审批任务** | | |
| GET | /api/hr/approval-tasks | 审批队列（按状态/类型筛选） |
| POST | /api/hr/approval-tasks/:id/approve | 审批通过 → 执行关联业务 |
| POST | /api/hr/approval-tasks/:id/reject | 审批驳回 |
| **HR 文件管理** | | |
| GET | /api/hr/documents | 文件列表 |
| POST | /api/hr/documents | 新增文件 |
| PUT | /api/hr/documents/:id | 编辑文件 |
| DELETE | /api/hr/documents/:id | 删除文件 |
| **员工档案** | | |
| GET | /api/hr/employees/:id/profile | 员工完整档案（含薪酬历史/调动记录） |

审批通过后的自动执行逻辑：
- payroll batch 审过 → 更新 batch status
- leave 审过 → 更新 leave status
- salary_adjust 审过 → 更新 HrEmployee.base_salary，status=executed
- dept_transfer 审过 → 更新 HrEmployee.department_id 等，status=executed
- position_change 审过 → 更新 HrEmployee.position_id 等，status=executed

---

## 4. 前端页面

### 4.1 导航结构（menuConfig.ts 中 HR section 更新）

```
一、人力资源管理系统
├── 基础管理
│   ├── 1.0 公司制度          /finance/hr/policy
│   ├── 1.1 级别与岗位管理    /finance/hr/positions
│   ├── 1.2 部门设置          /finance/departments
│   ├── 1.3 员工档案管理      /finance/hr/employee-profiles    ← 新增
│   └── 1.4 公司文件（人事）   /finance/hr/documents            ← 新增
├── 员工管理
│   ├── 1.5 入职管理          /finance/hr/onboarding
│   ├── 1.6 薪酬调整          /finance/hr/salary-adjustments   ← 新增
│   ├── 1.7 部门调动          /finance/hr/dept-transfers       ← 新增
│   ├── 1.8 岗位调整          /finance/hr/position-changes     ← 新增
│   └── 1.9 审批任务          /finance/hr/approval-tasks       ← 新增
├── 薪酬与考勤
│   ├── 1.10 月度工资表       /finance/hr/payroll              ← 新增
│   ├── 1.11 假期管理         /finance/hr/leave                ← 新增
│   └── 1.12 社保比例配置     /finance/hr/si-rates             ← 新增
├── 培训与发展
│   ├── 1.13 员工培训         /finance/hr/training
│   ├── 1.14 员工考核         /finance/hr/evaluation
│   ├── 1.15 员工奖惩         /finance/hr/rewards
│   └── 1.16 员工离职         /finance/hr/offboarding
└── 预算与报表
    └── 1.17 人力资源预算      /finance/hr/budget
```

### 4.2 核心页面说明

**月度工资表** (`HrPayroll.vue`)：
- 选择月份 → 点击「生成工资表」→ 自动为所有在职员工创建明细行（带入基本工资、社保基数）
- 表格：完整列（≈30 列），横向可滚动，前 5 列（序号/部门/姓名/基本工资/补贴小计）固定
- 自动计算列用灰色底色（不可编辑），手动列用白色（draft 状态可编辑）
- 部门小计行（蓝色底色）+ 全公司合计行（深色底色）
- 操作按钮随状态变化：编制中→提交审核→审核通过→审批通过→提交财务→确认发放
- 审批通过的可手动覆盖列显示覆盖标记

**审批任务** (`HrApprovalTasks.vue`)：
- 筛选栏：按类型（假期/薪酬/调动/岗位/工资表）+ 状态（待审/已批/已驳）
- 列表：类型图标、申请人、内容摘要、提交时间、状态
- 点击进入详情 → 审批操作（通过/驳回 + 意见）

**假期管理** (`HrLeave.vue`)：
- 标签切换：假期申请 / 假期余额总览 / 假期类型设置（管理员）
- 申请表单：选择员工、假期类型、起止日期、天数自动计算
- 员工端仅显示自己的申请和历史

**薪酬调整 / 部门调动 / 岗位调整** — 结构统一：
- 表格列表 + 新增按钮
- 弹窗填写 → 提交 → 创建审批任务

**员工档案** (`HrEmployeeProfile.vue`)：
- 左侧员工列表（可搜索），右侧档案详情
- 档案包含：基本信息、薪酬历史、调动记录、奖惩记录、考核记录

---

## 5. 审批工作流

```
业务提交 → approval_tasks (status=pending)
              │
              ├─ approve → 执行业务动作 → approval_tasks (status=approved)
              │            ├─ salary_adjust → HrEmployee.base_salary = new
              │            ├─ dept_transfer → HrEmployee.department_id = to_dept
              │            ├─ position_change → HrEmployee.position_id = to_position
              │            ├─ leave → hr_leave_applications.status = approved
              │            └─ payroll_batch → batch.status = approved → 下一审批步骤
              │
              └─ reject → approval_tasks (status=rejected)
                          业务记录 status = rejected（可重新提交）
```

月度工资表多步审批：

```
draft → submit(review) → create task(step=review)
      → approve → reviewed → create task(step=approve)
      → approve → approved → create task(step=submit)
      → approve → submitted(财务) → create task(step=disburse)
      → approve → disbursed
```

---

## 6. 与财务管理模块的关系

- 财管「薪酬预算」：列精简为「基本薪酬、补贴与福利、社保与保险、招聘与培训、预算合计」汇总大类
- 月度工资表提交财务后（status=submitted），财务部在应付账款或费用模块中看到待发放的工资批量数据
- 个税代扣代缴：月度工资表生成后，可在税务管理模块「个人所得税代扣代缴」中引用

---

## 7. 迁移计划

- `hr_salaries` 表保留不动（已有 4 个月数据），新功能使用 `hr_salary_details`
- 原 `HrCompensation.vue` 页面替换为 `HrPayroll.vue`
- 原 `HrSalary` 模型保留不删除（避免迁移风险）
