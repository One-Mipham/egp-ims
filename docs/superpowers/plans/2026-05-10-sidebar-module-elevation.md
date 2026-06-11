# Sidebar Module Elevation & New Module Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure sidebar from 6→13 top-level modules by elevating 6 modules from Accounting, add 2 placeholder modules (Knowledge Base, Expense Reimbursement), and implement full-stack CRUD for Fixed Assets → AR → AP → Admin → Inventory in priority order.

**Architecture:** Sidebar is driven by `menuConfig.ts` (data) + `SidebarMenu.vue` (rendering). Each new business module follows HR pattern: backend model → schema → router → frontend API → Vue views. Routes are flat under `/finance/*`.

**Tech Stack:** Python 3.12+ / FastAPI / SQLAlchemy / SQLite (backend) · Vue 3 / PrimeVue / Tailwind CSS (frontend)

**Spec:** [2026-05-10-sidebar-module-elevation-design.md](../specs/2026-05-10-sidebar-module-elevation-design.md)

---

## File Structure Map

| File | Responsibility |
|------|---------------|
| `frontend/src/config/menuConfig.ts` | 13-section menu data definition |
| `frontend/src/router/index.ts` | Flat route entries under `/finance/*` |
| `frontend/src/views/PlaceholderPage.vue` | "Under construction" page (already exists) |
| `backend/app/models.py` | SQLAlchemy models (all in one file) |
| `backend/app/schemas.py` | Pydantic request/response schemas |
| `backend/app/routers/fixed_assets.py` | Fixed Assets CRUD endpoints |
| `backend/app/routers/receivables.py` | AR CRUD endpoints |
| `backend/app/routers/payables.py` | AP CRUD endpoints |
| `backend/app/routers/inventory_trade.py` | Inventory CRUD endpoints |
| `backend/app/main.py` | Router registration |
| `frontend/src/api/index.ts` | All API functions (single file) |
| `frontend/src/views/fixed_assets/` | Fixed Asset Vue pages |
| `frontend/src/views/receivables/` | AR Vue pages |
| `frontend/src/views/payables/` | AP Vue pages |
| `frontend/src/views/admin/` | Admin module pages |
| `frontend/src/views/inventory_trade/` | Inventory Vue pages |

---

## Phase 1: Menu Config & Router Foundation

### Task 1.1: Restructure menuConfig.ts

**Files:**
- Modify: `frontend/src/config/menuConfig.ts`

- [ ] **Step 1: Rewrite menuSections array**

Replace entire `menuSections` array with the new 13-section structure. Existing sections 1-3 (HR, Contracts, Admin) stay. Accounting section (was #4) gets stripped of elevated items and becomes #10. New sections 4-9 are the elevated modules. Sections 11-13 are Finance, Board, Knowledge Base.

```typescript
export const menuSections: MenuSection[] = [
  // ═══════════ 一、人力资源管理系统 ═══════════
  {
    icon: 'pi pi-users',
    title: '一、人力资源管理系统',
    shortTitle: '人力资源',
    items: [
      { label: '1.0 公司人力资源管理制度', to: '/finance/hr/policy', icon: 'pi pi-file' },
      { label: '1.1 员工入职', to: '/finance/hr/onboarding', icon: 'pi pi-user-plus' },
      { label: '1.2 员工培训', to: '/finance/hr/training', icon: 'pi pi-book' },
      { label: '1.3 员工考核', to: '/finance/hr/evaluation', icon: 'pi pi-star' },
      { label: '1.4 薪酬管理', to: '/finance/hr/compensation', icon: 'pi pi-dollar' },
      { label: '1.5 员工奖惩', to: '/finance/hr/rewards', icon: 'pi pi-thumbs-up' },
      { label: '1.6 员工离职', to: '/finance/hr/offboarding', icon: 'pi pi-sign-out' },
      { label: '1.7 人力资源预算管理', to: '/finance/hr/budget', icon: 'pi pi-chart-bar' },
    ],
  },

  // ═══════════ 二、合同管理系统 ═══════════
  {
    icon: 'pi pi-file',
    title: '二、合同管理系统',
    shortTitle: '合同管理',
    items: [
      { label: '2.1 供应商合同', to: '/finance/contracts/supplier', icon: 'pi pi-truck' },
      { label: '2.2 客户合同', to: '/finance/contracts/customer', icon: 'pi pi-users' },
      { label: '2.3 劳动合同', to: '/finance/contracts/labor', icon: 'pi pi-id-card' },
      { label: '2.4 租赁合同', to: '/finance/contracts/lease', icon: 'pi pi-home' },
      { label: '2.5 合同查询统计', to: '/finance/contracts/query', icon: 'pi pi-search' },
    ],
  },

  // ═══════════ 三、行政综合管理系统 ═══════════
  {
    icon: 'pi pi-building',
    title: '三、行政综合管理系统',
    shortTitle: '行政综合',
    items: [
      { label: '3.1 文件管理', to: '/finance/admin/documents', icon: 'pi pi-file' },
      { label: '3.2 车辆管理', to: '/finance/admin/vehicles', icon: 'pi pi-car' },
      { label: '3.3 财产保险', to: '/finance/admin/insurance', icon: 'pi pi-shield' },
      { label: '3.4 门禁管理', to: '/finance/admin/access', icon: 'pi pi-lock' },
      { label: '3.5 资产与仓库管理', to: '/finance/inventory', icon: 'pi pi-box' },
    ],
  },

  // ═══════════ 四、固定资产管理 ═══════════
  {
    icon: 'pi pi-box',
    title: '四、固定资产管理',
    shortTitle: '固定资产',
    items: [
      { label: '4.1 资产台账', to: '/finance/fixed-assets/register', icon: 'pi pi-list' },
      { label: '4.2 折旧管理', to: '/finance/fixed-assets/depreciation', icon: 'pi pi-sort-amount-down' },
      { label: '4.3 资产盘点', to: '/finance/fixed-assets/inventory-check', icon: 'pi pi-check-square' },
      { label: '4.4 资产处置', to: '/finance/fixed-assets/disposal', icon: 'pi pi-trash' },
      { label: '4.5 资产报表', to: '/finance/fixed-assets/reports', icon: 'pi pi-chart-bar' },
    ],
  },

  // ═══════════ 五、应收账款管理 ═══════════
  {
    icon: 'pi pi-money-bill',
    title: '五、应收账款管理',
    shortTitle: '应收账款',
    items: [
      { label: '5.1 客户信息', to: '/finance/receivables/customers', icon: 'pi pi-users' },
      { label: '5.2 应收发票', to: '/finance/receivables/invoices', icon: 'pi pi-file' },
      { label: '5.3 收款管理', to: '/finance/receivables/payments', icon: 'pi pi-credit-card' },
      { label: '5.4 账龄分析', to: '/finance/receivables/aging', icon: 'pi pi-clock' },
      { label: '5.5 坏账管理', to: '/finance/receivables/bad-debts', icon: 'pi pi-exclamation-triangle' },
    ],
  },

  // ═══════════ 六、应付账款管理 ═══════════
  {
    icon: 'pi pi-credit-card',
    title: '六、应付账款管理',
    shortTitle: '应付账款',
    items: [
      { label: '6.1 供应商信息', to: '/finance/payables/suppliers', icon: 'pi pi-truck' },
      { label: '6.2 应付发票', to: '/finance/payables/invoices', icon: 'pi pi-file' },
      { label: '6.3 付款管理', to: '/finance/payables/payments', icon: 'pi pi-wallet' },
      { label: '6.4 账龄分析', to: '/finance/payables/aging', icon: 'pi pi-clock' },
      { label: '6.5 付款计划', to: '/finance/payables/schedule', icon: 'pi pi-calendar' },
    ],
  },

  // ═══════════ 七、费用报销管理 ═══════════
  {
    icon: 'pi pi-receipt',
    title: '七、费用报销管理',
    shortTitle: '费用报销',
    items: [
      {
        label: '7.0 费用报销（开发中）',
        to: '/finance/expense-reimbursement',
        icon: 'pi pi-lock',
        roles: ['super_admin'],
        lockedMessage: '费用报销模块正在规划中，敬请期待。',
      },
    ],
  },

  // ═══════════ 八、进销存管理 ═══════════
  {
    icon: 'pi pi-shopping-cart',
    title: '八、进销存管理',
    shortTitle: '进销存',
    items: [
      { label: '8.1 采购管理', to: '/finance/inventory-trade/purchases', icon: 'pi pi-cart-plus' },
      { label: '8.2 销售管理', to: '/finance/inventory-trade/sales', icon: 'pi pi-cart-arrow-down' },
      { label: '8.3 库存管理', to: '/finance/inventory-trade/stock', icon: 'pi pi-box' },
      { label: '8.4 成本核算', to: '/finance/inventory-trade/costing', icon: 'pi pi-calculator' },
      { label: '8.5 库存报表', to: '/finance/inventory-trade/reports', icon: 'pi pi-chart-bar' },
    ],
  },

  // ═══════════ 九、投资管理系统 ═══════════
  {
    icon: 'pi pi-chart-bar',
    title: '九、投资管理系统',
    shortTitle: '投资管理',
    items: [
      {
        label: '9.1 投资组合总览',
        icon: 'pi pi-chart-line',
        children: [
          { label: '投资组合总览', to: '/finance/investments/portfolio' },
          { label: '投资持仓', to: '/finance/investments/positions' },
          { label: '投资交易', to: '/finance/investments/transactions' },
          { label: '投资收益', to: '/finance/investments/income' },
          { label: '投资报表', to: '/finance/investments/reports' },
          { label: '基金管理', to: '/finance/investments/funds' },
          { label: 'LP投资管理', to: '/finance/investments/investors' },
          { label: '绩效分析', to: '/finance/investments/performance' },
          { label: '分配瀑布', to: '/finance/investments/waterfall' },
        ],
      },
    ],
  },

  // ═══════════ 十、会计管理系统 ═══════════
  {
    icon: 'pi pi-book',
    title: '十、会计管理系统',
    shortTitle: '会计管理',
    items: [
      {
        label: '10.0 会计管理驾驶舱',
        to: '/finance/cockpit/accounting',
        icon: 'pi pi-desktop',
        roles: ['accountant', 'finance_manager', 'finance_director', 'super_admin'],
        lockedMessage: '您无权访问会计管理驾驶舱。需要：会计、财务经理、财务总监或系统管理员权限。',
      },
      {
        label: '10.1 基础设置',
        icon: 'pi pi-cog',
        children: [
          { label: '公司信息', to: '/finance/settings/basic' },
          { label: '科目', to: '/finance/accounts' },
          { label: '凭证类别', to: '/finance/settings/voucher-types' },
          { label: '常用凭证', to: '/finance/settings/common-vouchers' },
          { label: '常用摘要', to: '/finance/settings/common-summaries' },
          { label: '现金流量项目', to: '/finance/settings/cash-flow-items' },
          { label: '收付信息', to: '/finance/settings/payment' },
          { label: '部门管理', to: '/finance/departments' },
          { label: '选项设置', to: '/finance/settings/options' },
        ],
      },
      {
        label: '10.2 总账',
        icon: 'pi pi-file-edit',
        children: [
          { label: '凭证', to: '/finance/vouchers' },
          { label: '凭证审核', to: '/finance/gl/voucher-review' },
          { label: '记账', to: '/finance/gl/journal' },
          { label: '反记账', to: '/finance/gl/journal-reverse' },
          { label: '科目账', to: '/finance/gl/subject-ledger' },
          { label: '辅助账', to: '/finance/gl/aux-ledger' },
          { label: '自定义账', to: '/finance/gl/custom-ledger' },
          { label: '自定义明细表', to: '/finance/gl/custom-detail' },
          { label: '自动转账', to: '/finance/gl/auto-transfer' },
          { label: '往来管理', to: '/finance/gl/transactions' },
          { label: '现金流量', to: '/finance/gl/cashflow' },
          { label: '账簿打印', to: '/finance/gl/print-books' },
          { label: '初始化导航', to: '/finance/init' },
        ],
      },
      {
        label: '10.3 税务管理',
        icon: 'pi pi-calculator',
        children: [
          { label: '客户信息维护', to: '/finance/tax/customers' },
          { label: '销项发票', to: '/finance/tax/invoice/sales' },
          { label: '进项发票', to: '/finance/tax/invoice/purchase' },
          { label: '发票查询统计', to: '/finance/tax/invoice/query' },
          { label: '增值税管理', to: '/finance/tax/vat' },
          { label: '城市维护建设税', to: '/finance/tax/surcharge/urban' },
          { label: '教育费附加', to: '/finance/tax/surcharge/education' },
          { label: '地方教育附加', to: '/finance/tax/surcharge/local-edu' },
          { label: '企业所得税', to: '/finance/tax/corporate-income' },
          { label: '个人所得税代扣代缴', to: '/finance/tax/iit' },
          { label: '印花税', to: '/finance/tax/stamp-duty' },
          { label: '房产税', to: '/finance/tax/property-tax' },
          { label: '土地使用税', to: '/finance/tax/land-use-tax' },
          { label: '车船税', to: '/finance/tax/vehicle-tax' },
          { label: '土地增值税', to: '/finance/tax/land-vat' },
          { label: '罚款与滞纳金', to: '/finance/tax/penalty' },
          { label: '增值税申报表', to: '/finance/tax/reports/vat' },
          { label: '所得税申报表', to: '/finance/tax/reports/cit' },
          { label: '其他税种申报汇总', to: '/finance/tax/reports/other' },
        ],
      },
      {
        label: '10.4 报表中心',
        icon: 'pi pi-chart-bar',
        children: [
          { label: '财务报表', to: '/finance/reports' },
          { label: '月度报表', to: '/finance/reports/monthly' },
          { label: '季度报表', to: '/finance/reports/quarterly' },
          { label: '年度报表', to: '/finance/reports/yearly' },
          { label: '审计日志', to: '/finance/audit' },
        ],
      },
      { label: '10.5 协同办公', to: '/finance/todo', icon: 'pi pi-inbox' },
      {
        label: '10.6 系统设置',
        icon: 'pi pi-wrench',
        children: [
          { label: '用户管理', to: '/finance/users' },
          { label: '服务器', to: '/finance/servers' },
          { label: '系统设置', to: '/finance/settings' },
          { label: '数据导出', to: '/finance/system/data-export' },
          { label: '月度数据备份', to: '/finance/system/monthly-backup' },
          { label: '年度数据备份', to: '/finance/system/yearly-backup' },
          { label: '期末处理', to: '/finance/period/monthly-close' },
        ],
      },
    ],
  },

  // ═══════════ 十一、财务管理系统 ═══════════
  {
    icon: 'pi pi-chart-line',
    title: '十一、财务管理系统',
    shortTitle: '财务管理',
    items: [
      {
        label: '11.0 财务管理驾驶舱',
        to: '/finance/cockpit/finance',
        icon: 'pi pi-desktop',
        roles: ['finance_manager', 'finance_director', 'super_admin'],
        lockedMessage: '您无权访问财务管理驾驶舱。需要：财务经理、财务总监或系统管理员权限。',
      },
      { label: '11.1 预算管理与绩效评价', to: '/finance/cockpit/budget', icon: 'pi pi-chart-line' },
      { label: '11.2 现金流计划与融资计划', to: '/finance/cockpit/cashflow', icon: 'pi pi-money-bill' },
      { label: '11.3 经营分析指标', to: '/finance/cockpit/indicators', icon: 'pi pi-chart-bar' },
    ],
  },

  // ═══════════ 十二、董事办工作 ═══════════
  {
    icon: 'pi pi-briefcase',
    title: '十二、董事办工作',
    shortTitle: '董事办',
    items: [
      { label: '12.1 董事会工作条例', to: '/finance/board/bylaws', icon: 'pi pi-file' },
      {
        label: '12.2 董事会专业委员会',
        icon: 'pi pi-sitemap',
        children: [
          { label: '提名委员会', to: '/finance/board/committees/nomination' },
          { label: '薪酬与绩效考核委员会', to: '/finance/board/committees/compensation' },
          { label: '战略发展委员会', to: '/finance/board/committees/strategy' },
          { label: '审计与稽核委员会', to: '/finance/board/committees/audit' },
        ],
      },
      { label: '12.3 董秘工作职责', to: '/finance/board/secretary', icon: 'pi pi-user' },
      { label: '12.4 交易所工作对接', to: '/finance/board/exchange', icon: 'pi pi-globe' },
      { label: '12.5 证监会、局工作对接', to: '/finance/board/csrc', icon: 'pi pi-shield' },
      { label: '12.6 财务报告', to: '/finance/board/financial-reports', icon: 'pi pi-chart-bar' },
      { label: '12.7 股东管理', to: '/finance/board/shareholders', icon: 'pi pi-users' },
      { label: '12.8 投资者关系管理', to: '/finance/board/investors', icon: 'pi pi-comments' },
      { label: '12.9 政府关系管理', to: '/finance/board/government', icon: 'pi pi-building' },
      { label: '12.10 媒体关系管理', to: '/finance/board/media', icon: 'pi pi-video' },
    ],
  },

  // ═══════════ 十三、知识库 ═══════════
  {
    icon: 'pi pi-bookmark',
    title: '十三、知识库',
    shortTitle: '知识库',
    items: [
      {
        label: '13.0 知识库（规划中）',
        to: '/finance/knowledge-base',
        icon: 'pi pi-lock',
        roles: ['super_admin'],
        lockedMessage: '知识库模块正在规划中，敬请期待。',
      },
    ],
  },
]
```

- [ ] **Step 2: Verify TypeScript compiles**

Run: `cd frontend && npx vue-tsc --noEmit 2>&1 | head -20`
Expected: No new errors from menuConfig.ts

- [ ] **Step 3: Commit**

```bash
git add frontend/src/config/menuConfig.ts
git commit --no-gpg-sign -m "feat: restructure sidebar to 13 modules, elevate FA/AR/AP/Inv/Investment from Accounting

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 1.2: Add routes for new modules

**Files:**
- Modify: `frontend/src/router/index.ts`

- [ ] **Step 1: Add new route entries**

Remove the old placeholder routes for `/finance/inventory-trade`, `/finance/receivables`, `/finance/payables`, `/finance/fixed-assets` (lines 120-123).

Replace them with the new module routes. Insert after the last admin route (after `/finance/inventory` at line 118):

```typescript
  // ═══════════ 四、固定资产管理 ═══════════
  { path: '/finance/fixed-assets/register', component: () => import('../views/fixed_assets/FixedAssetRegister.vue'), meta: { requiresAuth: true } },
  { path: '/finance/fixed-assets/depreciation', component: () => import('../views/fixed_assets/FixedAssetDepreciation.vue'), meta: { requiresAuth: true } },
  { path: '/finance/fixed-assets/inventory-check', component: () => import('../views/fixed_assets/FixedAssetCheck.vue'), meta: { requiresAuth: true } },
  { path: '/finance/fixed-assets/disposal', component: () => import('../views/fixed_assets/FixedAssetDisposal.vue'), meta: { requiresAuth: true } },
  { path: '/finance/fixed-assets/reports', component: () => import('../views/fixed_assets/FixedAssetReports.vue'), meta: { requiresAuth: true } },
  // ═══════════ 五、应收账款管理 ═══════════
  { path: '/finance/receivables/customers', component: () => import('../views/receivables/ReceivableCustomers.vue'), meta: { requiresAuth: true } },
  { path: '/finance/receivables/invoices', component: () => import('../views/receivables/ReceivableInvoices.vue'), meta: { requiresAuth: true } },
  { path: '/finance/receivables/payments', component: () => import('../views/receivables/ReceivablePayments.vue'), meta: { requiresAuth: true } },
  { path: '/finance/receivables/aging', component: () => import('../views/receivables/ReceivableAging.vue'), meta: { requiresAuth: true } },
  { path: '/finance/receivables/bad-debts', component: () => import('../views/receivables/ReceivableBadDebts.vue'), meta: { requiresAuth: true } },
  // ═══════════ 六、应付账款管理 ═══════════
  { path: '/finance/payables/suppliers', component: () => import('../views/payables/PayableSuppliers.vue'), meta: { requiresAuth: true } },
  { path: '/finance/payables/invoices', component: () => import('../views/payables/PayableInvoices.vue'), meta: { requiresAuth: true } },
  { path: '/finance/payables/payments', component: () => import('../views/payables/PayablePayments.vue'), meta: { requiresAuth: true } },
  { path: '/finance/payables/aging', component: () => import('../views/payables/PayableAging.vue'), meta: { requiresAuth: true } },
  { path: '/finance/payables/schedule', component: () => import('../views/payables/PayableSchedule.vue'), meta: { requiresAuth: true } },
  // ═══════════ 七、费用报销管理（占位） ═══════════
  { path: '/finance/expense-reimbursement', component: () => import('../views/PlaceholderPage.vue'), meta: { requiresAuth: true, pageTitle: '费用报销管理', allowedRoles: ['super_admin'] } },
  // ═══════════ 八、进销存管理 ═══════════
  { path: '/finance/inventory-trade/purchases', component: () => import('../views/inventory_trade/InvPurchases.vue'), meta: { requiresAuth: true } },
  { path: '/finance/inventory-trade/sales', component: () => import('../views/inventory_trade/InvSales.vue'), meta: { requiresAuth: true } },
  { path: '/finance/inventory-trade/stock', component: () => import('../views/inventory_trade/InvStock.vue'), meta: { requiresAuth: true } },
  { path: '/finance/inventory-trade/costing', component: () => import('../views/inventory_trade/InvCosting.vue'), meta: { requiresAuth: true } },
  { path: '/finance/inventory-trade/reports', component: () => import('../views/inventory_trade/InvReports.vue'), meta: { requiresAuth: true } },
  // ═══════════ 十三、知识库（占位） ═══════════
  { path: '/finance/knowledge-base', component: () => import('../views/PlaceholderPage.vue'), meta: { requiresAuth: true, pageTitle: '知识库', allowedRoles: ['super_admin'] } },
```

- [ ] **Step 2: Verify router compiles**

Run: `cd frontend && npx vue-tsc --noEmit 2>&1 | head -20`
Expected: No new errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/router/index.ts
git commit --no-gpg-sign -m "feat: add routes for new modules (FA/AR/AP/Inv/Expense/KB)

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 1.3: Create placeholder Vue pages for pending modules

**Files:**
- Create: `frontend/src/views/fixed_assets/FixedAssetRegister.vue`
- Create: `frontend/src/views/fixed_assets/FixedAssetDepreciation.vue`
- Create: `frontend/src/views/fixed_assets/FixedAssetCheck.vue`
- Create: `frontend/src/views/fixed_assets/FixedAssetDisposal.vue`
- Create: `frontend/src/views/fixed_assets/FixedAssetReports.vue`
- Create: `frontend/src/views/receivables/ReceivableCustomers.vue`
- Create: `frontend/src/views/receivables/ReceivableInvoices.vue`
- Create: `frontend/src/views/receivables/ReceivablePayments.vue`
- Create: `frontend/src/views/receivables/ReceivableAging.vue`
- Create: `frontend/src/views/receivables/ReceivableBadDebts.vue`
- Create: `frontend/src/views/payables/PayableSuppliers.vue`
- Create: `frontend/src/views/payables/PayableInvoices.vue`
- Create: `frontend/src/views/payables/PayablePayments.vue`
- Create: `frontend/src/views/payables/PayableAging.vue`
- Create: `frontend/src/views/payables/PayableSchedule.vue`
- Create: `frontend/src/views/inventory_trade/InvPurchases.vue`
- Create: `frontend/src/views/inventory_trade/InvSales.vue`
- Create: `frontend/src/views/inventory_trade/InvStock.vue`
- Create: `frontend/src/views/inventory_trade/InvCosting.vue`
- Create: `frontend/src/views/inventory_trade/InvReports.vue`

- [ ] **Step 1: Create directories**

```bash
mkdir -p frontend/src/views/fixed_assets
mkdir -p frontend/src/views/receivables
mkdir -p frontend/src/views/payables
mkdir -p frontend/src/views/inventory_trade
```

- [ ] **Step 2: Generate placeholder pages with correct pageTitle**

For each file, create a minimal component that uses PlaceholderPage pattern. Each one takes ~3 seconds to write since they're identical templates with different pageTitles.

Fixed Assets pages:
```vue
<!-- frontend/src/views/fixed_assets/FixedAssetRegister.vue -->
<template>
  <div class="flex items-center justify-center h-full">
    <div class="text-center">
      <i class="pi pi-list text-4xl text-zinc-300 mb-4" />
      <h2 class="text-sm font-light text-zinc-500 mb-2">资产台账</h2>
      <p class="text-xs text-zinc-400">该模块正在开发中，敬请期待</p>
    </div>
  </div>
</template>
```

```vue
<!-- frontend/src/views/fixed_assets/FixedAssetDepreciation.vue -->
<template>
  <div class="flex items-center justify-center h-full">
    <div class="text-center">
      <i class="pi pi-sort-amount-down text-4xl text-zinc-300 mb-4" />
      <h2 class="text-sm font-light text-zinc-500 mb-2">折旧管理</h2>
      <p class="text-xs text-zinc-400">该模块正在开发中，敬请期待</p>
    </div>
  </div>
</template>
```

```vue
<!-- frontend/src/views/fixed_assets/FixedAssetCheck.vue -->
<template>
  <div class="flex items-center justify-center h-full">
    <div class="text-center">
      <i class="pi pi-check-square text-4xl text-zinc-300 mb-4" />
      <h2 class="text-sm font-light text-zinc-500 mb-2">资产盘点</h2>
      <p class="text-xs text-zinc-400">该模块正在开发中，敬请期待</p>
    </div>
  </div>
</template>
```

```vue
<!-- frontend/src/views/fixed_assets/FixedAssetDisposal.vue -->
<template>
  <div class="flex items-center justify-center h-full">
    <div class="text-center">
      <i class="pi pi-trash text-4xl text-zinc-300 mb-4" />
      <h2 class="text-sm font-light text-zinc-500 mb-2">资产处置</h2>
      <p class="text-xs text-zinc-400">该模块正在开发中，敬请期待</p>
    </div>
  </div>
</template>
```

```vue
<!-- frontend/src/views/fixed_assets/FixedAssetReports.vue -->
<template>
  <div class="flex items-center justify-center h-full">
    <div class="text-center">
      <i class="pi pi-chart-bar text-4xl text-zinc-300 mb-4" />
      <h2 class="text-sm font-light text-zinc-500 mb-2">资产报表</h2>
      <p class="text-xs text-zinc-400">该模块正在开发中，敬请期待</p>
    </div>
  </div>
</template>
```

Receivables pages:
```vue
<!-- frontend/src/views/receivables/ReceivableCustomers.vue -->
<template>
  <div class="flex items-center justify-center h-full">
    <div class="text-center">
      <i class="pi pi-users text-4xl text-zinc-300 mb-4" />
      <h2 class="text-sm font-light text-zinc-500 mb-2">客户信息</h2>
      <p class="text-xs text-zinc-400">该模块正在开发中，敬请期待</p>
    </div>
  </div>
</template>
```

```vue
<!-- frontend/src/views/receivables/ReceivableInvoices.vue -->
<template>
  <div class="flex items-center justify-center h-full">
    <div class="text-center">
      <i class="pi pi-file text-4xl text-zinc-300 mb-4" />
      <h2 class="text-sm font-light text-zinc-500 mb-2">应收发票</h2>
      <p class="text-xs text-zinc-400">该模块正在开发中，敬请期待</p>
    </div>
  </div>
</template>
```

```vue
<!-- frontend/src/views/receivables/ReceivablePayments.vue -->
<template>
  <div class="flex items-center justify-center h-full">
    <div class="text-center">
      <i class="pi pi-credit-card text-4xl text-zinc-300 mb-4" />
      <h2 class="text-sm font-light text-zinc-500 mb-2">收款管理</h2>
      <p class="text-xs text-zinc-400">该模块正在开发中，敬请期待</p>
    </div>
  </div>
</template>
```

```vue
<!-- frontend/src/views/receivables/ReceivableAging.vue -->
<template>
  <div class="flex items-center justify-center h-full">
    <div class="text-center">
      <i class="pi pi-clock text-4xl text-zinc-300 mb-4" />
      <h2 class="text-sm font-light text-zinc-500 mb-2">账龄分析</h2>
      <p class="text-xs text-zinc-400">该模块正在开发中，敬请期待</p>
    </div>
  </div>
</template>
```

```vue
<!-- frontend/src/views/receivables/ReceivableBadDebts.vue -->
<template>
  <div class="flex items-center justify-center h-full">
    <div class="text-center">
      <i class="pi pi-exclamation-triangle text-4xl text-zinc-300 mb-4" />
      <h2 class="text-sm font-light text-zinc-500 mb-2">坏账管理</h2>
      <p class="text-xs text-zinc-400">该模块正在开发中，敬请期待</p>
    </div>
  </div>
</template>
```

Payables pages:
```vue
<!-- frontend/src/views/payables/PayableSuppliers.vue -->
<template>
  <div class="flex items-center justify-center h-full">
    <div class="text-center">
      <i class="pi pi-truck text-4xl text-zinc-300 mb-4" />
      <h2 class="text-sm font-light text-zinc-500 mb-2">供应商信息</h2>
      <p class="text-xs text-zinc-400">该模块正在开发中，敬请期待</p>
    </div>
  </div>
</template>
```

```vue
<!-- frontend/src/views/payables/PayableInvoices.vue -->
<template>
  <div class="flex items-center justify-center h-full">
    <div class="text-center">
      <i class="pi pi-file text-4xl text-zinc-300 mb-4" />
      <h2 class="text-sm font-light text-zinc-500 mb-2">应付发票</h2>
      <p class="text-xs text-zinc-400">该模块正在开发中，敬请期待</p>
    </div>
  </div>
</template>
```

```vue
<!-- frontend/src/views/payables/PayablePayments.vue -->
<template>
  <div class="flex items-center justify-center h-full">
    <div class="text-center">
      <i class="pi pi-wallet text-4xl text-zinc-300 mb-4" />
      <h2 class="text-sm font-light text-zinc-500 mb-2">付款管理</h2>
      <p class="text-xs text-zinc-400">该模块正在开发中，敬请期待</p>
    </div>
  </div>
</template>
```

```vue
<!-- frontend/src/views/payables/PayableAging.vue -->
<template>
  <div class="flex items-center justify-center h-full">
    <div class="text-center">
      <i class="pi pi-clock text-4xl text-zinc-300 mb-4" />
      <h2 class="text-sm font-light text-zinc-500 mb-2">账龄分析</h2>
      <p class="text-xs text-zinc-400">该模块正在开发中，敬请期待</p>
    </div>
  </div>
</template>
```

```vue
<!-- frontend/src/views/payables/PayableSchedule.vue -->
<template>
  <div class="flex items-center justify-center h-full">
    <div class="text-center">
      <i class="pi pi-calendar text-4xl text-zinc-300 mb-4" />
      <h2 class="text-sm font-light text-zinc-500 mb-2">付款计划</h2>
      <p class="text-xs text-zinc-400">该模块正在开发中，敬请期待</p>
    </div>
  </div>
</template>
```

Inventory pages:
```vue
<!-- frontend/src/views/inventory_trade/InvPurchases.vue -->
<template>
  <div class="flex items-center justify-center h-full">
    <div class="text-center">
      <i class="pi pi-cart-plus text-4xl text-zinc-300 mb-4" />
      <h2 class="text-sm font-light text-zinc-500 mb-2">采购管理</h2>
      <p class="text-xs text-zinc-400">该模块正在开发中，敬请期待</p>
    </div>
  </div>
</template>
```

```vue
<!-- frontend/src/views/inventory_trade/InvSales.vue -->
<template>
  <div class="flex items-center justify-center h-full">
    <div class="text-center">
      <i class="pi pi-cart-arrow-down text-4xl text-zinc-300 mb-4" />
      <h2 class="text-sm font-light text-zinc-500 mb-2">销售管理</h2>
      <p class="text-xs text-zinc-400">该模块正在开发中，敬请期待</p>
    </div>
  </div>
</template>
```

```vue
<!-- frontend/src/views/inventory_trade/InvStock.vue -->
<template>
  <div class="flex items-center justify-center h-full">
    <div class="text-center">
      <i class="pi pi-box text-4xl text-zinc-300 mb-4" />
      <h2 class="text-sm font-light text-zinc-500 mb-2">库存管理</h2>
      <p class="text-xs text-zinc-400">该模块正在开发中，敬请期待</p>
    </div>
  </div>
</template>
```

```vue
<!-- frontend/src/views/inventory_trade/InvCosting.vue -->
<template>
  <div class="flex items-center justify-center h-full">
    <div class="text-center">
      <i class="pi pi-calculator text-4xl text-zinc-300 mb-4" />
      <h2 class="text-sm font-light text-zinc-500 mb-2">成本核算</h2>
      <p class="text-xs text-zinc-400">该模块正在开发中，敬请期待</p>
    </div>
  </div>
</template>
```

```vue
<!-- frontend/src/views/inventory_trade/InvReports.vue -->
<template>
  <div class="flex items-center justify-center h-full">
    <div class="text-center">
      <i class="pi pi-chart-bar text-4xl text-zinc-300 mb-4" />
      <h2 class="text-sm font-light text-zinc-500 mb-2">库存报表</h2>
      <p class="text-xs text-zinc-400">该模块正在开发中，敬请期待</p>
    </div>
  </div>
</template>
```

- [ ] **Step 3: Quick build check**

Run: `cd frontend && npx vite build 2>&1 | tail -5`
Expected: Build succeeds.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/views/fixed_assets/ frontend/src/views/receivables/ frontend/src/views/payables/ frontend/src/views/inventory_trade/
git commit --no-gpg-sign -m "feat: add placeholder pages for FA/AR/AP/Inventory modules (20 pages)

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Phase 2: Fixed Assets Management — Full Stack

### Task 2.1: Backend models for Fixed Assets

**Files:**
- Modify: `backend/app/models.py`

- [ ] **Step 1: Add FixedAsset and FixedAssetDepreciation models**

Insert before the last model in models.py:

```python
# ═══════════ 固定资产管理 ═══════════

class FixedAsset(Base):
    __tablename__ = "fixed_assets"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    asset_code = Column(String(50), nullable=False, comment="资产编号")
    name = Column(String(200), nullable=False, comment="资产名称")
    category = Column(String(50), nullable=False, default="设备", comment="资产类别")
    acquisition_date = Column(String(10), nullable=True, comment="购置日期")
    original_value = Column(Float, nullable=False, default=0, comment="原值")
    residual_value = Column(Float, nullable=False, default=0, comment="残值")
    useful_life = Column(Integer, nullable=False, default=5, comment="使用年限(年)")
    depreciation_method = Column(String(20), nullable=False, default="直线法", comment="折旧方法")
    monthly_depreciation = Column(Float, nullable=False, default=0, comment="月折旧额")
    accumulated_depreciation = Column(Float, nullable=False, default=0, comment="累计折旧")
    net_value = Column(Float, nullable=False, default=0, comment="净值")
    status = Column(String(20), nullable=False, default="使用中", comment="使用中/已处置/报废")
    location = Column(String(200), nullable=True, comment="存放地点")
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    department = relationship("Department")


class FixedAssetDepreciation(Base):
    __tablename__ = "fixed_asset_depreciations"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    fixed_asset_id = Column(Integer, ForeignKey("fixed_assets.id"), nullable=False)
    period = Column(String(7), nullable=False, comment="折旧期间 YYYY-MM")
    depreciation_amount = Column(Float, nullable=False, default=0, comment="本期折旧额")
    accumulated_before = Column(Float, nullable=False, default=0, comment="计提前累计")
    accumulated_after = Column(Float, nullable=False, default=0, comment="计提后累计")
    created_at = Column(DateTime, default=datetime.utcnow)

    fixed_asset = relationship("FixedAsset")
```

- [ ] **Step 2: Verify backend starts**

Run: `cd backend && uv run python -c "from app.models import FixedAsset, FixedAssetDepreciation; print('OK')"`
Expected: "OK" with no import errors.

- [ ] **Step 3: Commit**

```bash
git add backend/app/models.py
git commit --no-gpg-sign -m "feat: add FixedAsset and FixedAssetDepreciation models

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 2.2: Backend schemas for Fixed Assets

**Files:**
- Modify: `backend/app/schemas.py`

- [ ] **Step 1: Add Pydantic schemas**

Insert before the last class in schemas.py:

```python
# ═══════════ 固定资产管理 ═══════════

class FixedAssetCreate(BaseModel):
    company_id: int
    asset_code: str
    name: str
    category: str = "设备"
    acquisition_date: Optional[str] = None
    original_value: float = 0
    residual_value: float = 0
    useful_life: int = 5
    depreciation_method: str = "直线法"
    monthly_depreciation: float = 0
    status: str = "使用中"
    location: Optional[str] = None
    department_id: Optional[int] = None
    notes: Optional[str] = None

class FixedAssetResponse(BaseModel):
    id: int
    company_id: int
    asset_code: str
    name: str
    category: str
    acquisition_date: Optional[str] = None
    original_value: float
    residual_value: float
    useful_life: int
    depreciation_method: str
    monthly_depreciation: float
    accumulated_depreciation: float
    net_value: float
    status: str
    location: Optional[str] = None
    department_id: Optional[int] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class FixedAssetDepreciationCreate(BaseModel):
    company_id: int
    fixed_asset_id: int
    period: str
    depreciation_amount: float = 0

class FixedAssetDepreciationResponse(BaseModel):
    id: int
    company_id: int
    fixed_asset_id: int
    period: str
    depreciation_amount: float
    accumulated_before: float
    accumulated_after: float
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}
```

- [ ] **Step 2: Verify backend imports**

Run: `cd backend && uv run python -c "from app.schemas import FixedAssetCreate, FixedAssetResponse; print('OK')"`
Expected: "OK"

- [ ] **Step 3: Commit**

```bash
git add backend/app/schemas.py
git commit --no-gpg-sign -m "feat: add FixedAsset Pydantic schemas

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 2.3: Backend router for Fixed Assets

**Files:**
- Create: `backend/app/routers/fixed_assets.py`

- [ ] **Step 1: Create router with full CRUD**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user
from app.models import FixedAsset, FixedAssetDepreciation, User
from app.schemas import (
    FixedAssetCreate, FixedAssetResponse,
    FixedAssetDepreciationCreate, FixedAssetDepreciationResponse,
)

router = APIRouter()


# ─── Fixed Assets ────────────────────────────────

@router.get("/assets", response_model=list[FixedAssetResponse])
def list_assets(company_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(FixedAsset).filter(
        FixedAsset.company_id == company_id
    ).order_by(FixedAsset.id.desc()).all()


@router.post("/assets", response_model=FixedAssetResponse)
def create_asset(data: FixedAssetCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = FixedAsset(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/assets/{asset_id}", response_model=FixedAssetResponse)
def update_asset(asset_id: int, data: FixedAssetCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
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


# ─── Depreciation ────────────────────────────────

@router.get("/depreciations", response_model=list[FixedAssetDepreciationResponse])
def list_depreciations(company_id: int, fixed_asset_id: int | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q = db.query(FixedAssetDepreciation).filter(FixedAssetDepreciation.company_id == company_id)
    if fixed_asset_id:
        q = q.filter(FixedAssetDepreciation.fixed_asset_id == fixed_asset_id)
    return q.order_by(FixedAssetDepreciation.period.desc()).all()


@router.post("/depreciations", response_model=FixedAssetDepreciationResponse)
def create_depreciation(data: FixedAssetDepreciationCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # Compute accumulated
    asset = db.query(FixedAsset).filter(FixedAsset.id == data.fixed_asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="资产不存在")
    before = asset.accumulated_depreciation
    after = before + data.depreciation_amount
    item = FixedAssetDepreciation(
        **data.model_dump(),
        accumulated_before=before,
        accumulated_after=after,
    )
    db.add(item)
    # Update asset accumulated
    asset.accumulated_depreciation = after
    asset.net_value = asset.original_value - after
    db.commit()
    db.refresh(item)
    return item
```

- [ ] **Step 2: Register router in main.py**

Add import at top of `backend/app/main.py`:
```python
from app.routers import fixed_assets
```

Add route registration after other routers:
```python
app.include_router(fixed_assets.router, prefix="/api/fixed-assets", tags=["固定资产管理"])
```

- [ ] **Step 3: Verify backend starts**

Run: `cd backend && timeout 5 uv run uvicorn app.main:app 2>&1 || true`
Expected: No import errors.

- [ ] **Step 4: Commit**

```bash
git add backend/app/routers/fixed_assets.py backend/app/main.py
git commit --no-gpg-sign -m "feat: add Fixed Assets router with full CRUD + depreciation

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 2.4: Frontend API functions for Fixed Assets

**Files:**
- Modify: `frontend/src/api/index.ts`

- [ ] **Step 1: Add API functions**

Insert after existing HR API functions:

```typescript
// ═══════════ 固定资产管理 ═══════════
export const listFixedAssets = (companyId: number) =>
    api.get('/fixed-assets/assets', { params: { company_id: companyId } })
export const createFixedAsset = (data: any) =>
    api.post('/fixed-assets/assets', data)
export const updateFixedAsset = (id: number, data: any) =>
    api.put(`/fixed-assets/assets/${id}`, data)
export const deleteFixedAsset = (id: number) =>
    api.delete(`/fixed-assets/assets/${id}`)

export const listDepreciations = (companyId: number, fixedAssetId?: number) =>
    api.get('/fixed-assets/depreciations', { params: { company_id: companyId, fixed_asset_id: fixedAssetId } })
export const createDepreciation = (data: any) =>
    api.post('/fixed-assets/depreciations', data)
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/api/index.ts
git commit --no-gpg-sign -m "feat: add Fixed Assets API functions to frontend

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 2.5: Fixed Asset Register view (PrimeVue DataTable)

**Files:**
- Overwrite: `frontend/src/views/fixed_assets/FixedAssetRegister.vue`

This is the main working page. Follow the HR view pattern with PrimeVue DataTable + Dialog.

- [ ] **Step 1: Build full CRUD page**

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useToast } from 'primevue/usetoast'
import { listFixedAssets, createFixedAsset, updateFixedAsset, deleteFixedAsset } from '../../api'

const toast = useToast()
const items = ref<any[]>([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref<number | null>(null)

const emptyForm = () => ({
  company_id: 1,
  asset_code: '',
  name: '',
  category: '设备',
  acquisition_date: '',
  original_value: 0,
  residual_value: 0,
  useful_life: 5,
  depreciation_method: '直线法',
  monthly_depreciation: 0,
  status: '使用中',
  location: '',
  department_id: null,
  notes: '',
})

const form = ref(emptyForm())

const categoryOptions = ['设备', '车辆', '房产', '家具', '电子设备', '软件', '其他']
const statusOptions = ['使用中', '已处置', '报废', '闲置']

async function load() {
  const { data } = await listFixedAssets(1)
  items.value = data
}

function openCreate() {
  form.value = emptyForm()
  isEdit.value = false
  editId.value = null
  dialogVisible.value = true
}

function openEdit(row: any) {
  form.value = { ...row }
  isEdit.value = true
  editId.value = row.id
  dialogVisible.value = true
}

async function save() {
  if (isEdit.value && editId.value) {
    await updateFixedAsset(editId.value, form.value)
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

function calcDepreciation() {
  const f = form.value
  if (f.original_value > 0 && f.useful_life > 0) {
    if (f.depreciation_method === '直线法') {
      f.monthly_depreciation = parseFloat(((f.original_value - f.residual_value) / (f.useful_life * 12)).toFixed(2))
    }
  }
}

onMounted(load)
</script>

<template>
  <div class="p-4">
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-lg font-bold">资产台账</h1>
      <button @click="openCreate" class="px-4 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700">
        + 新增资产
      </button>
    </div>

    <table class="w-full text-sm border-collapse">
      <thead>
        <tr class="bg-zinc-100 text-left">
          <th class="p-2 border">资产编号</th>
          <th class="p-2 border">名称</th>
          <th class="p-2 border">类别</th>
          <th class="p-2 border">原值</th>
          <th class="p-2 border">累计折旧</th>
          <th class="p-2 border">净值</th>
          <th class="p-2 border">状态</th>
          <th class="p-2 border">操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in items" :key="item.id" class="hover:bg-zinc-50">
          <td class="p-2 border font-mono">{{ item.asset_code }}</td>
          <td class="p-2 border">{{ item.name }}</td>
          <td class="p-2 border">{{ item.category }}</td>
          <td class="p-2 border text-right">{{ item.original_value.toLocaleString() }}</td>
          <td class="p-2 border text-right">{{ item.accumulated_depreciation.toLocaleString() }}</td>
          <td class="p-2 border text-right">{{ item.net_value.toLocaleString() }}</td>
          <td class="p-2 border">
            <span :class="item.status === '使用中' ? 'text-green-600' : 'text-red-500'">{{ item.status }}</span>
          </td>
          <td class="p-2 border">
            <button @click="openEdit(item)" class="text-blue-600 mr-2 text-xs">编辑</button>
            <button @click="remove(item.id)" class="text-red-500 text-xs">删除</button>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Dialog -->
    <div v-if="dialogVisible" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg w-[600px] max-h-[80vh] overflow-auto p-6">
        <h2 class="text-lg font-bold mb-4">{{ isEdit ? '编辑资产' : '新增资产' }}</h2>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-xs text-zinc-500">资产编号</label>
            <input v-model="form.asset_code" class="w-full border rounded px-2 py-1 text-sm" />
          </div>
          <div>
            <label class="text-xs text-zinc-500">名称</label>
            <input v-model="form.name" class="w-full border rounded px-2 py-1 text-sm" />
          </div>
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
          <div>
            <label class="text-xs text-zinc-500">购置日期</label>
            <input type="date" v-model="form.acquisition_date" class="w-full border rounded px-2 py-1 text-sm" />
          </div>
          <div>
            <label class="text-xs text-zinc-500">存放地点</label>
            <input v-model="form.location" class="w-full border rounded px-2 py-1 text-sm" />
          </div>
          <div>
            <label class="text-xs text-zinc-500">原值</label>
            <input type="number" v-model.number="form.original_value" @change="calcDepreciation" class="w-full border rounded px-2 py-1 text-sm" />
          </div>
          <div>
            <label class="text-xs text-zinc-500">残值</label>
            <input type="number" v-model.number="form.residual_value" @change="calcDepreciation" class="w-full border rounded px-2 py-1 text-sm" />
          </div>
          <div>
            <label class="text-xs text-zinc-500">使用年限(年)</label>
            <input type="number" v-model.number="form.useful_life" @change="calcDepreciation" class="w-full border rounded px-2 py-1 text-sm" />
          </div>
          <div>
            <label class="text-xs text-zinc-500">折旧方法</label>
            <select v-model="form.depreciation_method" @change="calcDepreciation" class="w-full border rounded px-2 py-1 text-sm">
              <option value="直线法">直线法</option>
              <option value="双倍余额递减法">双倍余额递减法</option>
              <option value="年数总和法">年数总和法</option>
            </select>
          </div>
          <div>
            <label class="text-xs text-zinc-500">月折旧额（自动计算）</label>
            <input type="number" v-model.number="form.monthly_depreciation" disabled class="w-full border rounded px-2 py-1 text-sm bg-zinc-50" />
          </div>
        </div>
        <div class="mt-3">
          <label class="text-xs text-zinc-500">备注</label>
          <textarea v-model="form.notes" class="w-full border rounded px-2 py-1 text-sm" rows="2"></textarea>
        </div>
        <div class="flex justify-end gap-2 mt-4">
          <button @click="dialogVisible = false" class="px-4 py-1.5 border rounded text-sm">取消</button>
          <button @click="save" class="px-4 py-1.5 bg-blue-600 text-white rounded text-sm">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>
```

- [ ] **Step 2: Verify frontend compiles**

Run: `cd frontend && npx vue-tsc --noEmit 2>&1 | head -20`
Expected: No new errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/fixed_assets/FixedAssetRegister.vue
git commit --no-gpg-sign -m "feat: implement Fixed Asset Register with full CRUD and auto-depreciation calc

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 2.6: Create database tables

- [ ] **Step 1: Create tables via backend startup**

Run: `cd backend && uv run python -c "
from app.database import engine
from app.models import Base, FixedAsset, FixedAssetDepreciation
Base.metadata.create_all(bind=engine)
print('Tables created')
"`
Expected: "Tables created"

- [ ] **Step 2: Commit**

```bash
git add -A
git commit --no-gpg-sign -m "chore: create fixed_assets and fixed_asset_depreciations tables

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Phase 3: Accounts Receivable — Full Stack

### Task 3.1: Backend models for AR

**Files:**
- Modify: `backend/app/models.py`

- [ ] **Step 1: Add Receivable and ReceivablePayment models**

```python
# ═══════════ 应收账款管理 ═══════════

class Receivable(Base):
    __tablename__ = "receivables"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    customer_name = Column(String(200), nullable=False, comment="客户名称")
    invoice_no = Column(String(100), nullable=False, comment="发票号")
    invoice_date = Column(String(10), nullable=True, comment="发票日期")
    amount = Column(Float, nullable=False, default=0, comment="应收金额")
    received_amount = Column(Float, nullable=False, default=0, comment="已收金额")
    balance = Column(Float, nullable=False, default=0, comment="余额")
    due_date = Column(String(10), nullable=True, comment="到期日")
    aging_days = Column(Integer, nullable=False, default=0, comment="账龄(天)")
    status = Column(String(20), nullable=False, default="未收款", comment="未收款/部分收款/已收款/坏账")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ReceivablePayment(Base):
    __tablename__ = "receivable_payments"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    receivable_id = Column(Integer, ForeignKey("receivables.id"), nullable=False)
    payment_date = Column(String(10), nullable=False)
    amount = Column(Float, nullable=False, default=0)
    payment_method = Column(String(50), nullable=True, comment="银行转账/现金/承兑汇票")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    receivable = relationship("Receivable")
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/models.py
git commit --no-gpg-sign -m "feat: add Receivable and ReceivablePayment models

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 3.2: Backend schemas for AR

**Files:**
- Modify: `backend/app/schemas.py`

- [ ] **Step 1: Add AR schemas**

```python
# ═══════════ 应收账款管理 ═══════════

class ReceivableCreate(BaseModel):
    company_id: int
    customer_name: str
    invoice_no: str
    invoice_date: Optional[str] = None
    amount: float = 0
    due_date: Optional[str] = None
    notes: Optional[str] = None

class ReceivableResponse(BaseModel):
    id: int
    company_id: int
    customer_name: str
    invoice_no: str
    invoice_date: Optional[str] = None
    amount: float
    received_amount: float
    balance: float
    due_date: Optional[str] = None
    aging_days: int
    status: str
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class ReceivablePaymentCreate(BaseModel):
    company_id: int
    receivable_id: int
    payment_date: str
    amount: float = 0
    payment_method: Optional[str] = None
    notes: Optional[str] = None

class ReceivablePaymentResponse(BaseModel):
    id: int
    company_id: int
    receivable_id: int
    payment_date: str
    amount: float
    payment_method: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/schemas.py
git commit --no-gpg-sign -m "feat: add AR Pydantic schemas

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 3.3: Backend router for AR

**Files:**
- Create: `backend/app/routers/receivables.py`

- [ ] **Step 1: Create AR router with balance tracking**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user
from app.models import Receivable, ReceivablePayment, User
from app.schemas import (
    ReceivableCreate, ReceivableResponse,
    ReceivablePaymentCreate, ReceivablePaymentResponse,
)
from datetime import date

router = APIRouter()


@router.get("/invoices", response_model=list[ReceivableResponse])
def list_receivables(company_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Receivable).filter(
        Receivable.company_id == company_id
    ).order_by(Receivable.id.desc()).all()


@router.post("/invoices", response_model=ReceivableResponse)
def create_receivable(data: ReceivableCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # Calculate aging days
    aging = 0
    if data.due_date:
        try:
            due = date.fromisoformat(data.due_date)
            aging = max(0, (date.today() - due).days)
        except ValueError:
            pass
    item = Receivable(
        **data.model_dump(),
        balance=data.amount,
        aging_days=aging,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/invoices/{inv_id}", response_model=ReceivableResponse)
def update_receivable(inv_id: int, data: ReceivableCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(Receivable).filter(Receivable.id == inv_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="应收记录不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(item, k, v)
    item.balance = item.amount - item.received_amount
    db.commit()
    db.refresh(item)
    return item


@router.delete("/invoices/{inv_id}")
def delete_receivable(inv_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(Receivable).filter(Receivable.id == inv_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="应收记录不存在")
    db.delete(item)
    db.commit()
    return {"ok": True}


# ─── Payments ────────────────────────────────

@router.get("/payments", response_model=list[ReceivablePaymentResponse])
def list_payments(company_id: int, receivable_id: int | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q = db.query(ReceivablePayment).filter(ReceivablePayment.company_id == company_id)
    if receivable_id:
        q = q.filter(ReceivablePayment.receivable_id == receivable_id)
    return q.order_by(ReceivablePayment.payment_date.desc()).all()


@router.post("/payments", response_model=ReceivablePaymentResponse)
def create_payment(data: ReceivablePaymentCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    inv = db.query(Receivable).filter(Receivable.id == data.receivable_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="应收记录不存在")
    item = ReceivablePayment(**data.model_dump())
    db.add(item)
    inv.received_amount += data.amount
    inv.balance = inv.amount - inv.received_amount
    inv.status = "已收款" if inv.balance <= 0 else ("部分收款" if inv.received_amount > 0 else "未收款")
    db.commit()
    db.refresh(item)
    return item
```

- [ ] **Step 2: Register in main.py**

```python
from app.routers import receivables
# ...
app.include_router(receivables.router, prefix="/api/receivables", tags=["应收账款管理"])
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/routers/receivables.py backend/app/main.py
git commit --no-gpg-sign -m "feat: add AR router with invoice CRUD + payment tracking

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 3.4: Frontend API + ReceivableCustomers view

**Files:**
- Modify: `frontend/src/api/index.ts`
- Overwrite: `frontend/src/views/receivables/ReceivableCustomers.vue`

- [ ] **Step 1: Add AR API functions**

```typescript
// ═══════════ 应收账款管理 ═══════════
export const listReceivables = (companyId: number) =>
    api.get('/receivables/invoices', { params: { company_id: companyId } })
export const createReceivable = (data: any) =>
    api.post('/receivables/invoices', data)
export const updateReceivable = (id: number, data: any) =>
    api.put(`/receivables/invoices/${id}`, data)
export const deleteReceivable = (id: number) =>
    api.delete(`/receivables/invoices/${id}`)

export const listReceivablePayments = (companyId: number, receivableId?: number) =>
    api.get('/receivables/payments', { params: { company_id: companyId, receivable_id: receivableId } })
export const createReceivablePayment = (data: any) =>
    api.post('/receivables/payments', data)
```

- [ ] **Step 2: Create ReceivableCustomers.vue (AR invoice list + payment modal)**

This view shows the AR invoice list with customer info, amounts, aging, and a payment button.

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useToast } from 'primevue/usetoast'
import { listReceivables, createReceivable, updateReceivable, deleteReceivable, createReceivablePayment } from '../../api'

const toast = useToast()
const items = ref<any[]>([])
const dialogVisible = ref(false)
const paymentDialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref<number | null>(null)
const selectedItem = ref<any>(null)
const paymentAmount = ref(0)

const emptyForm = () => ({
  company_id: 1,
  customer_name: '',
  invoice_no: '',
  invoice_date: '',
  amount: 0,
  due_date: '',
  notes: '',
})

const form = ref(emptyForm())
const statusOptions = ['未收款', '部分收款', '已收款', '坏账']

async function load() {
  const { data } = await listReceivables(1)
  items.value = data
}

function openCreate() {
  form.value = emptyForm()
  isEdit.value = false
  dialogVisible.value = true
}

function openEdit(row: any) {
  form.value = { ...row }
  isEdit.value = true
  editId.value = row.id
  dialogVisible.value = true
}

async function save() {
  if (isEdit.value && editId.value) {
    await updateReceivable(editId.value, form.value)
    toast.add({ severity: 'success', summary: '已更新', life: 2000 })
  } else {
    await createReceivable(form.value)
    toast.add({ severity: 'success', summary: '已创建', life: 2000 })
  }
  dialogVisible.value = false
  await load()
}

async function remove(id: number) {
  if (confirm('确定删除？')) {
    await deleteReceivable(id)
    toast.add({ severity: 'success', summary: '已删除', life: 2000 })
    await load()
  }
}

function openPayment(row: any) {
  selectedItem.value = row
  paymentAmount.value = row.balance
  paymentDialogVisible.value = true
}

async function submitPayment() {
  await createReceivablePayment({
    company_id: 1,
    receivable_id: selectedItem.value.id,
    payment_date: new Date().toISOString().slice(0, 10),
    amount: paymentAmount.value,
    payment_method: '银行转账',
  })
  toast.add({ severity: 'success', summary: '收款已登记', life: 2000 })
  paymentDialogVisible.value = false
  await load()
}

onMounted(load)
</script>

<template>
  <div class="p-4">
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-lg font-bold">客户应收管理</h1>
      <button @click="openCreate" class="px-4 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700">+ 新增应收</button>
    </div>

    <table class="w-full text-sm border-collapse">
      <thead>
        <tr class="bg-zinc-100 text-left">
          <th class="p-2 border">客户</th>
          <th class="p-2 border">发票号</th>
          <th class="p-2 border">发票日期</th>
          <th class="p-2 border text-right">金额</th>
          <th class="p-2 border text-right">已收</th>
          <th class="p-2 border text-right">余额</th>
          <th class="p-2 border text-right">账龄(天)</th>
          <th class="p-2 border">状态</th>
          <th class="p-2 border">操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in items" :key="item.id" class="hover:bg-zinc-50">
          <td class="p-2 border">{{ item.customer_name }}</td>
          <td class="p-2 border font-mono text-xs">{{ item.invoice_no }}</td>
          <td class="p-2 border text-xs">{{ item.invoice_date }}</td>
          <td class="p-2 border text-right">{{ item.amount.toLocaleString() }}</td>
          <td class="p-2 border text-right">{{ item.received_amount.toLocaleString() }}</td>
          <td class="p-2 border text-right font-bold" :class="item.balance > 0 ? 'text-red-600' : 'text-green-600'">{{ item.balance.toLocaleString() }}</td>
          <td class="p-2 border text-right" :class="item.aging_days > 90 ? 'text-red-600' : ''">{{ item.aging_days }}</td>
          <td class="p-2 border">{{ item.status }}</td>
          <td class="p-2 border">
            <button @click="openEdit(item)" class="text-blue-600 mr-1 text-xs">编辑</button>
            <button @click="openPayment(item)" v-if="item.balance > 0" class="text-green-600 mr-1 text-xs">收款</button>
            <button @click="remove(item.id)" class="text-red-500 text-xs">删除</button>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Invoice Dialog -->
    <div v-if="dialogVisible" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg w-[500px] p-6">
        <h2 class="text-lg font-bold mb-4">{{ isEdit ? '编辑应收' : '新增应收' }}</h2>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-xs text-zinc-500">客户名称</label>
            <input v-model="form.customer_name" class="w-full border rounded px-2 py-1 text-sm" />
          </div>
          <div>
            <label class="text-xs text-zinc-500">发票号</label>
            <input v-model="form.invoice_no" class="w-full border rounded px-2 py-1 text-sm" />
          </div>
          <div>
            <label class="text-xs text-zinc-500">发票日期</label>
            <input type="date" v-model="form.invoice_date" class="w-full border rounded px-2 py-1 text-sm" />
          </div>
          <div>
            <label class="text-xs text-zinc-500">到期日</label>
            <input type="date" v-model="form.due_date" class="w-full border rounded px-2 py-1 text-sm" />
          </div>
          <div>
            <label class="text-xs text-zinc-500">金额</label>
            <input type="number" v-model.number="form.amount" class="w-full border rounded px-2 py-1 text-sm" />
          </div>
        </div>
        <div class="flex justify-end gap-2 mt-4">
          <button @click="dialogVisible = false" class="px-4 py-1.5 border rounded text-sm">取消</button>
          <button @click="save" class="px-4 py-1.5 bg-blue-600 text-white rounded text-sm">保存</button>
        </div>
      </div>
    </div>

    <!-- Payment Dialog -->
    <div v-if="paymentDialogVisible" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg w-[400px] p-6">
        <h2 class="text-lg font-bold mb-4">登记收款 - {{ selectedItem?.customer_name }}</h2>
        <p class="text-sm text-zinc-500 mb-3">发票号：{{ selectedItem?.invoice_no }} | 余额：{{ selectedItem?.balance.toLocaleString() }}</p>
        <div>
          <label class="text-xs text-zinc-500">收款金额</label>
          <input type="number" v-model.number="paymentAmount" class="w-full border rounded px-2 py-1 text-sm" />
        </div>
        <div class="flex justify-end gap-2 mt-4">
          <button @click="paymentDialogVisible = false" class="px-4 py-1.5 border rounded text-sm">取消</button>
          <button @click="submitPayment" class="px-4 py-1.5 bg-green-600 text-white rounded text-sm">确认收款</button>
        </div>
      </div>
    </div>
  </div>
</template>
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/api/index.ts frontend/src/views/receivables/ReceivableCustomers.vue
git commit --no-gpg-sign -m "feat: add AR frontend — invoice CRUD + payment modal

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Phase 4: Accounts Payable — Full Stack

### Task 4.1: Backend models for AP

**Files:**
- Modify: `backend/app/models.py`

- [ ] **Step 1: Add Payable and PayablePayment models**

```python
# ═══════════ 应付账款管理 ═══════════

class Payable(Base):
    __tablename__ = "payables"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    supplier_name = Column(String(200), nullable=False, comment="供应商名称")
    invoice_no = Column(String(100), nullable=False, comment="发票号")
    invoice_date = Column(String(10), nullable=True, comment="发票日期")
    amount = Column(Float, nullable=False, default=0, comment="应付金额")
    paid_amount = Column(Float, nullable=False, default=0, comment="已付金额")
    balance = Column(Float, nullable=False, default=0, comment="余额")
    due_date = Column(String(10), nullable=True, comment="到期日")
    aging_days = Column(Integer, nullable=False, default=0, comment="账龄(天)")
    status = Column(String(20), nullable=False, default="未付款", comment="未付款/部分付款/已付款")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PayablePayment(Base):
    __tablename__ = "payable_payments"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    payable_id = Column(Integer, ForeignKey("payables.id"), nullable=False)
    payment_date = Column(String(10), nullable=False)
    amount = Column(Float, nullable=False, default=0)
    payment_method = Column(String(50), nullable=True, comment="银行转账/现金/承兑汇票")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    payable = relationship("Payable")
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/models.py
git commit --no-gpg-sign -m "feat: add Payable and PayablePayment models

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 4.2: Backend schemas + router for AP

**Files:**
- Modify: `backend/app/schemas.py`
- Create: `backend/app/routers/payables.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Add AP schemas**

```python
# ═══════════ 应付账款管理 ═══════════

class PayableCreate(BaseModel):
    company_id: int
    supplier_name: str
    invoice_no: str
    invoice_date: Optional[str] = None
    amount: float = 0
    due_date: Optional[str] = None
    notes: Optional[str] = None

class PayableResponse(BaseModel):
    id: int
    company_id: int
    supplier_name: str
    invoice_no: str
    invoice_date: Optional[str] = None
    amount: float
    paid_amount: float
    balance: float
    due_date: Optional[str] = None
    aging_days: int
    status: str
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class PayablePaymentCreate(BaseModel):
    company_id: int
    payable_id: int
    payment_date: str
    amount: float = 0
    payment_method: Optional[str] = None
    notes: Optional[str] = None

class PayablePaymentResponse(BaseModel):
    id: int
    company_id: int
    payable_id: int
    payment_date: str
    amount: float
    payment_method: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}
```

- [ ] **Step 2: Create AP router**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user
from app.models import Payable, PayablePayment, User
from app.schemas import PayableCreate, PayableResponse, PayablePaymentCreate, PayablePaymentResponse
from datetime import date

router = APIRouter()


@router.get("/invoices", response_model=list[PayableResponse])
def list_payables(company_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Payable).filter(Payable.company_id == company_id).order_by(Payable.id.desc()).all()


@router.post("/invoices", response_model=PayableResponse)
def create_payable(data: PayableCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    aging = 0
    if data.due_date:
        try:
            aging = max(0, (date.today() - date.fromisoformat(data.due_date)).days)
        except ValueError:
            pass
    item = Payable(**data.model_dump(), balance=data.amount, aging_days=aging)
    db.add(item); db.commit(); db.refresh(item)
    return item


@router.put("/invoices/{inv_id}", response_model=PayableResponse)
def update_payable(inv_id: int, data: PayableCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(Payable).filter(Payable.id == inv_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="应付记录不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(item, k, v)
    item.balance = item.amount - item.paid_amount
    db.commit(); db.refresh(item)
    return item


@router.delete("/invoices/{inv_id}")
def delete_payable(inv_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(Payable).filter(Payable.id == inv_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="应付记录不存在")
    db.delete(item); db.commit()
    return {"ok": True}


@router.get("/payments", response_model=list[PayablePaymentResponse])
def list_payments(company_id: int, payable_id: int | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q = db.query(PayablePayment).filter(PayablePayment.company_id == company_id)
    if payable_id: q = q.filter(PayablePayment.payable_id == payable_id)
    return q.order_by(PayablePayment.payment_date.desc()).all()


@router.post("/payments", response_model=PayablePaymentResponse)
def create_payment(data: PayablePaymentCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    inv = db.query(Payable).filter(Payable.id == data.payable_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="应付记录不存在")
    item = PayablePayment(**data.model_dump())
    db.add(item)
    inv.paid_amount += data.amount
    inv.balance = inv.amount - inv.paid_amount
    inv.status = "已付款" if inv.balance <= 0 else ("部分付款" if inv.paid_amount > 0 else "未付款")
    db.commit(); db.refresh(item)
    return item
```

- [ ] **Step 3: Register in main.py**

```python
from app.routers import payables
# ...
app.include_router(payables.router, prefix="/api/payables", tags=["应付账款管理"])
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/schemas.py backend/app/routers/payables.py backend/app/main.py
git commit --no-gpg-sign -m "feat: add AP backend — schemas, router, registered in main

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 4.3: Frontend API + PayableSuppliers view

**Files:**
- Modify: `frontend/src/api/index.ts`
- Overwrite: `frontend/src/views/payables/PayableSuppliers.vue`

- [ ] **Step 1: Add AP API functions**

```typescript
// ═══════════ 应付账款管理 ═══════════
export const listPayables = (companyId: number) =>
    api.get('/payables/invoices', { params: { company_id: companyId } })
export const createPayable = (data: any) =>
    api.post('/payables/invoices', data)
export const updatePayable = (id: number, data: any) =>
    api.put(`/payables/invoices/${id}`, data)
export const deletePayable = (id: number) =>
    api.delete(`/payables/invoices/${id}`)

export const listPayablePayments = (companyId: number, payableId?: number) =>
    api.get('/payables/payments', { params: { company_id: companyId, payable_id: payableId } })
export const createPayablePayment = (data: any) =>
    api.post('/payables/payments', data)
```

- [ ] **Step 2: Create PayableSuppliers.vue**

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useToast } from 'primevue/usetoast'
import { listPayables, createPayable, updatePayable, deletePayable, createPayablePayment } from '../../api'

const toast = useToast()
const items = ref<any[]>([])
const dialogVisible = ref(false)
const paymentDialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref<number | null>(null)
const selectedItem = ref<any>(null)
const paymentAmount = ref(0)

const emptyForm = () => ({
  company_id: 1, supplier_name: '', invoice_no: '', invoice_date: '',
  amount: 0, due_date: '', notes: '',
})

const form = ref(emptyForm())

async function load() {
  const { data } = await listPayables(1)
  items.value = data
}

function openCreate() {
  form.value = emptyForm()
  isEdit.value = false
  dialogVisible.value = true
}

function openEdit(row: any) {
  form.value = { ...row }
  isEdit.value = true
  editId.value = row.id
  dialogVisible.value = true
}

async function save() {
  if (isEdit.value && editId.value) {
    await updatePayable(editId.value, form.value)
    toast.add({ severity: 'success', summary: '已更新', life: 2000 })
  } else {
    await createPayable(form.value)
    toast.add({ severity: 'success', summary: '已创建', life: 2000 })
  }
  dialogVisible.value = false
  await load()
}

async function remove(id: number) {
  if (confirm('确定删除？')) {
    await deletePayable(id)
    toast.add({ severity: 'success', summary: '已删除', life: 2000 })
    await load()
  }
}

function openPayment(row: any) {
  selectedItem.value = row
  paymentAmount.value = row.balance
  paymentDialogVisible.value = true
}

async function submitPayment() {
  await createPayablePayment({
    company_id: 1, payable_id: selectedItem.value.id,
    payment_date: new Date().toISOString().slice(0, 10),
    amount: paymentAmount.value, payment_method: '银行转账',
  })
  toast.add({ severity: 'success', summary: '付款已登记', life: 2000 })
  paymentDialogVisible.value = false
  await load()
}

onMounted(load)
</script>

<template>
  <div class="p-4">
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-lg font-bold">供应商应付管理</h1>
      <button @click="openCreate" class="px-4 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700">+ 新增应付</button>
    </div>
    <table class="w-full text-sm border-collapse">
      <thead>
        <tr class="bg-zinc-100 text-left">
          <th class="p-2 border">供应商</th>
          <th class="p-2 border">发票号</th>
          <th class="p-2 border">发票日期</th>
          <th class="p-2 border text-right">金额</th>
          <th class="p-2 border text-right">已付</th>
          <th class="p-2 border text-right">余额</th>
          <th class="p-2 border text-right">账龄(天)</th>
          <th class="p-2 border">状态</th>
          <th class="p-2 border">操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in items" :key="item.id" class="hover:bg-zinc-50">
          <td class="p-2 border">{{ item.supplier_name }}</td>
          <td class="p-2 border font-mono text-xs">{{ item.invoice_no }}</td>
          <td class="p-2 border text-xs">{{ item.invoice_date }}</td>
          <td class="p-2 border text-right">{{ item.amount.toLocaleString() }}</td>
          <td class="p-2 border text-right">{{ item.paid_amount.toLocaleString() }}</td>
          <td class="p-2 border text-right font-bold" :class="item.balance > 0 ? 'text-red-600' : 'text-green-600'">{{ item.balance.toLocaleString() }}</td>
          <td class="p-2 border text-right">{{ item.aging_days }}</td>
          <td class="p-2 border">{{ item.status }}</td>
          <td class="p-2 border">
            <button @click="openEdit(item)" class="text-blue-600 mr-1 text-xs">编辑</button>
            <button @click="openPayment(item)" v-if="item.balance > 0" class="text-orange-600 mr-1 text-xs">付款</button>
            <button @click="remove(item.id)" class="text-red-500 text-xs">删除</button>
          </td>
        </tr>
      </tbody>
    </table>
    <!-- Invoice Dialog -->
    <div v-if="dialogVisible" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg w-[500px] p-6">
        <h2 class="text-lg font-bold mb-4">{{ isEdit ? '编辑应付' : '新增应付' }}</h2>
        <div class="grid grid-cols-2 gap-3">
          <div><label class="text-xs text-zinc-500">供应商名称</label><input v-model="form.supplier_name" class="w-full border rounded px-2 py-1 text-sm" /></div>
          <div><label class="text-xs text-zinc-500">发票号</label><input v-model="form.invoice_no" class="w-full border rounded px-2 py-1 text-sm" /></div>
          <div><label class="text-xs text-zinc-500">发票日期</label><input type="date" v-model="form.invoice_date" class="w-full border rounded px-2 py-1 text-sm" /></div>
          <div><label class="text-xs text-zinc-500">到期日</label><input type="date" v-model="form.due_date" class="w-full border rounded px-2 py-1 text-sm" /></div>
          <div><label class="text-xs text-zinc-500">金额</label><input type="number" v-model.number="form.amount" class="w-full border rounded px-2 py-1 text-sm" /></div>
        </div>
        <div class="flex justify-end gap-2 mt-4">
          <button @click="dialogVisible = false" class="px-4 py-1.5 border rounded text-sm">取消</button>
          <button @click="save" class="px-4 py-1.5 bg-blue-600 text-white rounded text-sm">保存</button>
        </div>
      </div>
    </div>
    <!-- Payment Dialog -->
    <div v-if="paymentDialogVisible" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg w-[400px] p-6">
        <h2 class="text-lg font-bold mb-4">登记付款 - {{ selectedItem?.supplier_name }}</h2>
        <p class="text-sm text-zinc-500 mb-3">发票号：{{ selectedItem?.invoice_no }} | 余额：{{ selectedItem?.balance.toLocaleString() }}</p>
        <div><label class="text-xs text-zinc-500">付款金额</label><input type="number" v-model.number="paymentAmount" class="w-full border rounded px-2 py-1 text-sm" /></div>
        <div class="flex justify-end gap-2 mt-4">
          <button @click="paymentDialogVisible = false" class="px-4 py-1.5 border rounded text-sm">取消</button>
          <button @click="submitPayment" class="px-4 py-1.5 bg-orange-600 text-white rounded text-sm">确认付款</button>
        </div>
      </div>
    </div>
  </div>
</template>
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/api/index.ts frontend/src/views/payables/PayableSuppliers.vue
git commit --no-gpg-sign -m "feat: add AP frontend — invoice CRUD + payment modal

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Phase 5: Admin Module Enhancement

### Task 5.1: Improve existing admin placeholder pages

**Files:**
- Overwrite: `frontend/src/views/admin/` files (only if they are still PlaceholderPage)

- [ ] **Step 1: Check current state of admin views**

Existing routes point to `PlaceholderPage.vue` for all admin sub-modules (`/finance/admin/documents`, `/finance/admin/vehicles`, `/finance/admin/insurance`, `/finance/admin/access`). These remain placeholders for now — the admin module was listed as priority ❹. The current placeholder pages are functional.

For today's scope, mark the admin section as having placeholders ready. The real implementation of individual admin sub-pages (文件管理, 车辆管理, etc.) will be done later.

- [ ] **Step 2: Commit (if changes made)**

If no changes needed, skip commit. The admin module already has correct menu entries, routes, and placeholder pages.

---

## Phase 6: Inventory Management (进销存) — Full Stack

### Task 6.1: Backend models for Inventory

**Files:**
- Modify: `backend/app/models.py`

- [ ] **Step 1: Add Inventory models**

```python
# ═══════════ 进销存管理 ═══════════

class InvPurchase(Base):
    __tablename__ = "inv_purchases"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    order_no = Column(String(100), nullable=False, comment="采购单号")
    supplier_name = Column(String(200), nullable=False)
    order_date = Column(String(10), nullable=True)
    product_name = Column(String(200), nullable=False)
    quantity = Column(Float, nullable=False, default=0)
    unit = Column(String(20), nullable=False, default="个")
    unit_price = Column(Float, nullable=False, default=0)
    total_amount = Column(Float, nullable=False, default=0)
    status = Column(String(20), nullable=False, default="待入库")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class InvSale(Base):
    __tablename__ = "inv_sales"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    order_no = Column(String(100), nullable=False, comment="销售单号")
    customer_name = Column(String(200), nullable=False)
    order_date = Column(String(10), nullable=True)
    product_name = Column(String(200), nullable=False)
    quantity = Column(Float, nullable=False, default=0)
    unit = Column(String(20), nullable=False, default="个")
    unit_price = Column(Float, nullable=False, default=0)
    total_amount = Column(Float, nullable=False, default=0)
    cost_amount = Column(Float, nullable=False, default=0, comment="成本金额")
    profit = Column(Float, nullable=False, default=0, comment="毛利")
    status = Column(String(20), nullable=False, default="待出库")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class InvStock(Base):
    __tablename__ = "inv_stocks"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    product_code = Column(String(100), nullable=False)
    product_name = Column(String(200), nullable=False)
    category = Column(String(50), nullable=True)
    quantity = Column(Float, nullable=False, default=0)
    unit = Column(String(20), nullable=False, default="个")
    unit_cost = Column(Float, nullable=False, default=0)
    total_cost = Column(Float, nullable=False, default=0)
    warehouse = Column(String(100), nullable=True)
    min_stock = Column(Float, nullable=False, default=0, comment="最低库存")
    max_stock = Column(Float, nullable=False, default=0, comment="最高库存")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/models.py
git commit --no-gpg-sign -m "feat: add Inventory models — Purchase/Sale/Stock

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 6.2: Backend schemas for Inventory

**Files:**
- Modify: `backend/app/schemas.py`

- [ ] **Step 1: Add Inventory schemas**

```python
# ═══════════ 进销存管理 ═══════════

class InvPurchaseCreate(BaseModel):
    company_id: int
    order_no: str
    supplier_name: str
    order_date: Optional[str] = None
    product_name: str
    quantity: float = 0
    unit: str = "个"
    unit_price: float = 0
    total_amount: float = 0
    status: str = "待入库"
    notes: Optional[str] = None

class InvPurchaseResponse(BaseModel):
    id: int; company_id: int; order_no: str; supplier_name: str
    order_date: Optional[str] = None; product_name: str
    quantity: float; unit: str; unit_price: float; total_amount: float
    status: str; notes: Optional[str] = None
    created_at: Optional[datetime] = None; updated_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class InvSaleCreate(BaseModel):
    company_id: int
    order_no: str
    customer_name: str
    order_date: Optional[str] = None
    product_name: str
    quantity: float = 0
    unit: str = "个"
    unit_price: float = 0
    total_amount: float = 0
    cost_amount: float = 0
    status: str = "待出库"
    notes: Optional[str] = None

class InvSaleResponse(BaseModel):
    id: int; company_id: int; order_no: str; customer_name: str
    order_date: Optional[str] = None; product_name: str
    quantity: float; unit: str; unit_price: float; total_amount: float
    cost_amount: float; profit: float; status: str
    notes: Optional[str] = None
    created_at: Optional[datetime] = None; updated_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class InvStockCreate(BaseModel):
    company_id: int
    product_code: str
    product_name: str
    category: Optional[str] = None
    quantity: float = 0
    unit: str = "个"
    unit_cost: float = 0
    total_cost: float = 0
    warehouse: Optional[str] = None
    min_stock: float = 0
    max_stock: float = 0
    notes: Optional[str] = None

class InvStockResponse(BaseModel):
    id: int; company_id: int; product_code: str; product_name: str
    category: Optional[str] = None; quantity: float; unit: str
    unit_cost: float; total_cost: float; warehouse: Optional[str] = None
    min_stock: float; max_stock: float; notes: Optional[str] = None
    created_at: Optional[datetime] = None; updated_at: Optional[datetime] = None
    model_config = {"from_attributes": True}
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/schemas.py
git commit --no-gpg-sign -m "feat: add Inventory Pydantic schemas — Purchase/Sale/Stock

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 6.3: Backend router for Inventory

**Files:**
- Create: `backend/app/routers/inventory_trade.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Create Inventory router with 3 resource groups**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user
from app.models import InvPurchase, InvSale, InvStock, User
from app.schemas import (
    InvPurchaseCreate, InvPurchaseResponse,
    InvSaleCreate, InvSaleResponse,
    InvStockCreate, InvStockResponse,
)

router = APIRouter()

# ─── Purchases ────────────────────────────────
@router.get("/purchases", response_model=list[InvPurchaseResponse])
def list_purchases(company_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(InvPurchase).filter(InvPurchase.company_id == company_id).order_by(InvPurchase.id.desc()).all()

@router.post("/purchases", response_model=InvPurchaseResponse)
def create_purchase(data: InvPurchaseCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = InvPurchase(**data.model_dump())
    db.add(item); db.commit(); db.refresh(item)
    return item

@router.put("/purchases/{id}", response_model=InvPurchaseResponse)
def update_purchase(id: int, data: InvPurchaseCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(InvPurchase).filter(InvPurchase.id == id).first()
    if not item: raise HTTPException(status_code=404, detail="采购单不存在")
    for k, v in data.model_dump(exclude_unset=True).items(): setattr(item, k, v)
    db.commit(); db.refresh(item)
    return item

@router.delete("/purchases/{id}")
def delete_purchase(id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(InvPurchase).filter(InvPurchase.id == id).first()
    if not item: raise HTTPException(status_code=404, detail="采购单不存在")
    db.delete(item); db.commit()
    return {"ok": True}

# ─── Sales ────────────────────────────────
@router.get("/sales", response_model=list[InvSaleResponse])
def list_sales(company_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(InvSale).filter(InvSale.company_id == company_id).order_by(InvSale.id.desc()).all()

@router.post("/sales", response_model=InvSaleResponse)
def create_sale(data: InvSaleCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    data.total_amount = data.quantity * data.unit_price
    data.profit = data.total_amount - data.cost_amount
    item = InvSale(**data.model_dump())
    db.add(item); db.commit(); db.refresh(item)
    return item

@router.put("/sales/{id}", response_model=InvSaleResponse)
def update_sale(id: int, data: InvSaleCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(InvSale).filter(InvSale.id == id).first()
    if not item: raise HTTPException(status_code=404, detail="销售单不存在")
    for k, v in data.model_dump(exclude_unset=True).items(): setattr(item, k, v)
    db.commit(); db.refresh(item)
    return item

@router.delete("/sales/{id}")
def delete_sale(id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(InvSale).filter(InvSale.id == id).first()
    if not item: raise HTTPException(status_code=404, detail="销售单不存在")
    db.delete(item); db.commit()
    return {"ok": True}

# ─── Stock ────────────────────────────────
@router.get("/stock", response_model=list[InvStockResponse])
def list_stock(company_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(InvStock).filter(InvStock.company_id == company_id).order_by(InvStock.id.desc()).all()

@router.post("/stock", response_model=InvStockResponse)
def create_stock(data: InvStockCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    data.total_cost = data.quantity * data.unit_cost
    item = InvStock(**data.model_dump())
    db.add(item); db.commit(); db.refresh(item)
    return item

@router.put("/stock/{id}", response_model=InvStockResponse)
def update_stock(id: int, data: InvStockCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(InvStock).filter(InvStock.id == id).first()
    if not item: raise HTTPException(status_code=404, detail="库存记录不存在")
    for k, v in data.model_dump(exclude_unset=True).items(): setattr(item, k, v)
    item.total_cost = item.quantity * item.unit_cost
    db.commit(); db.refresh(item)
    return item

@router.delete("/stock/{id}")
def delete_stock(id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(InvStock).filter(InvStock.id == id).first()
    if not item: raise HTTPException(status_code=404, detail="库存记录不存在")
    db.delete(item); db.commit()
    return {"ok": True}
```

- [ ] **Step 2: Register in main.py**

```python
from app.routers import inventory_trade
# ...
app.include_router(inventory_trade.router, prefix="/api/inventory-trade", tags=["进销存管理"])
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/routers/inventory_trade.py backend/app/main.py
git commit --no-gpg-sign -m "feat: add Inventory router — Purchase/Sale/Stock full CRUD

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 6.4: Frontend API + Views for Inventory

**Files:**
- Modify: `frontend/src/api/index.ts`
- Overwrite: `frontend/src/views/inventory_trade/InvPurchases.vue`
- Overwrite: `frontend/src/views/inventory_trade/InvStock.vue`

- [ ] **Step 1: Add Inventory API functions**

```typescript
// ═══════════ 进销存管理 ═══════════
export const listPurchases = (companyId: number) =>
    api.get('/inventory-trade/purchases', { params: { company_id: companyId } })
export const createPurchase = (data: any) =>
    api.post('/inventory-trade/purchases', data)
export const updatePurchase = (id: number, data: any) =>
    api.put(`/inventory-trade/purchases/${id}`, data)
export const deletePurchase = (id: number) =>
    api.delete(`/inventory-trade/purchases/${id}`)

export const listInvSales = (companyId: number) =>
    api.get('/inventory-trade/sales', { params: { company_id: companyId } })
export const createInvSale = (data: any) =>
    api.post('/inventory-trade/sales', data)
export const updateInvSale = (id: number, data: any) =>
    api.put(`/inventory-trade/sales/${id}`, data)
export const deleteInvSale = (id: number) =>
    api.delete(`/inventory-trade/sales/${id}`)

export const listInvStock = (companyId: number) =>
    api.get('/inventory-trade/stock', { params: { company_id: companyId } })
export const createInvStock = (data: any) =>
    api.post('/inventory-trade/stock', data)
export const updateInvStock = (id: number, data: any) =>
    api.put(`/inventory-trade/stock/${id}`, data)
export const deleteInvStock = (id: number) =>
    api.delete(`/inventory-trade/stock/${id}`)
```

- [ ] **Step 2: Create InvPurchases.vue and InvStock.vue**

**InvPurchases.vue** — Purchase order CRUD:

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useToast } from 'primevue/usetoast'
import { listPurchases, createPurchase, updatePurchase, deletePurchase } from '../../api'

const toast = useToast()
const items = ref<any[]>([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref<number | null>(null)

const emptyForm = () => ({
  company_id: 1, order_no: '', supplier_name: '', order_date: '',
  product_name: '', quantity: 0, unit: '个', unit_price: 0, total_amount: 0, status: '待入库', notes: '',
})

const form = ref(emptyForm())

async function load() {
  const { data } = await listPurchases(1)
  items.value = data
}

function openCreate() { form.value = emptyForm(); isEdit.value = false; dialogVisible.value = true }
function openEdit(row: any) { form.value = { ...row }; isEdit.value = true; editId.value = row.id; dialogVisible.value = true }

async function save() {
  form.value.total_amount = form.value.quantity * form.value.unit_price
  if (isEdit.value && editId.value) {
    await updatePurchase(editId.value, form.value)
    toast.add({ severity: 'success', summary: '已更新', life: 2000 })
  } else {
    await createPurchase(form.value)
    toast.add({ severity: 'success', summary: '已创建', life: 2000 })
  }
  dialogVisible.value = false
  await load()
}

async function remove(id: number) {
  if (confirm('确定删除？')) { await deletePurchase(id); toast.add({ severity: 'success', summary: '已删除', life: 2000 }); await load() }
}

onMounted(load)
</script>

<template>
  <div class="p-4">
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-lg font-bold">采购管理</h1>
      <button @click="openCreate" class="px-4 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700">+ 新增采购单</button>
    </div>
    <table class="w-full text-sm border-collapse">
      <thead>
        <tr class="bg-zinc-100 text-left">
          <th class="p-2 border">采购单号</th><th class="p-2 border">供应商</th><th class="p-2 border">产品</th>
          <th class="p-2 border text-right">数量</th><th class="p-2 border text-right">单价</th><th class="p-2 border text-right">总金额</th>
          <th class="p-2 border">状态</th><th class="p-2 border">操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in items" :key="item.id" class="hover:bg-zinc-50">
          <td class="p-2 border font-mono text-xs">{{ item.order_no }}</td>
          <td class="p-2 border">{{ item.supplier_name }}</td>
          <td class="p-2 border">{{ item.product_name }}</td>
          <td class="p-2 border text-right">{{ item.quantity }} {{ item.unit }}</td>
          <td class="p-2 border text-right">{{ item.unit_price.toLocaleString() }}</td>
          <td class="p-2 border text-right">{{ item.total_amount.toLocaleString() }}</td>
          <td class="p-2 border">{{ item.status }}</td>
          <td class="p-2 border">
            <button @click="openEdit(item)" class="text-blue-600 mr-1 text-xs">编辑</button>
            <button @click="remove(item.id)" class="text-red-500 text-xs">删除</button>
          </td>
        </tr>
      </tbody>
    </table>
    <div v-if="dialogVisible" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg w-[550px] p-6">
        <h2 class="text-lg font-bold mb-4">{{ isEdit ? '编辑采购单' : '新增采购单' }}</h2>
        <div class="grid grid-cols-2 gap-3">
          <div><label class="text-xs text-zinc-500">采购单号</label><input v-model="form.order_no" class="w-full border rounded px-2 py-1 text-sm" /></div>
          <div><label class="text-xs text-zinc-500">供应商</label><input v-model="form.supplier_name" class="w-full border rounded px-2 py-1 text-sm" /></div>
          <div><label class="text-xs text-zinc-500">采购日期</label><input type="date" v-model="form.order_date" class="w-full border rounded px-2 py-1 text-sm" /></div>
          <div><label class="text-xs text-zinc-500">状态</label><select v-model="form.status" class="w-full border rounded px-2 py-1 text-sm"><option>待入库</option><option>已入库</option><option>已取消</option></select></div>
          <div><label class="text-xs text-zinc-500">产品名称</label><input v-model="form.product_name" class="w-full border rounded px-2 py-1 text-sm" /></div>
          <div><label class="text-xs text-zinc-500">单位</label><input v-model="form.unit" class="w-full border rounded px-2 py-1 text-sm" /></div>
          <div><label class="text-xs text-zinc-500">数量</label><input type="number" v-model.number="form.quantity" class="w-full border rounded px-2 py-1 text-sm" /></div>
          <div><label class="text-xs text-zinc-500">单价</label><input type="number" v-model.number="form.unit_price" class="w-full border rounded px-2 py-1 text-sm" /></div>
        </div>
        <div class="flex justify-end gap-2 mt-4">
          <button @click="dialogVisible = false" class="px-4 py-1.5 border rounded text-sm">取消</button>
          <button @click="save" class="px-4 py-1.5 bg-blue-600 text-white rounded text-sm">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>
```

**InvStock.vue** — Stock inventory list with low-stock alert coloring:

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useToast } from 'primevue/usetoast'
import { listInvStock, createInvStock, updateInvStock, deleteInvStock } from '../../api'

const toast = useToast()
const items = ref<any[]>([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref<number | null>(null)

const emptyForm = () => ({
  company_id: 1, product_code: '', product_name: '', category: '',
  quantity: 0, unit: '个', unit_cost: 0, total_cost: 0,
  warehouse: '', min_stock: 0, max_stock: 0, notes: '',
})

const form = ref(emptyForm())

async function load() {
  const { data } = await listInvStock(1)
  items.value = data
}

function openCreate() { form.value = emptyForm(); isEdit.value = false; dialogVisible.value = true }
function openEdit(row: any) { form.value = { ...row }; isEdit.value = true; editId.value = row.id; dialogVisible.value = true }

async function save() {
  form.value.total_cost = form.value.quantity * form.value.unit_cost
  if (isEdit.value && editId.value) {
    await updateInvStock(editId.value, form.value)
    toast.add({ severity: 'success', summary: '已更新', life: 2000 })
  } else {
    await createInvStock(form.value)
    toast.add({ severity: 'success', summary: '已创建', life: 2000 })
  }
  dialogVisible.value = false
  await load()
}

async function remove(id: number) {
  if (confirm('确定删除？')) { await deleteInvStock(id); toast.add({ severity: 'success', summary: '已删除', life: 2000 }); await load() }
}

onMounted(load)
</script>

<template>
  <div class="p-4">
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-lg font-bold">库存管理</h1>
      <button @click="openCreate" class="px-4 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700">+ 新增库存</button>
    </div>
    <table class="w-full text-sm border-collapse">
      <thead>
        <tr class="bg-zinc-100 text-left">
          <th class="p-2 border">产品编码</th><th class="p-2 border">产品名称</th><th class="p-2 border">类别</th>
          <th class="p-2 border text-right">数量</th><th class="p-2 border text-right">单位成本</th><th class="p-2 border text-right">总成本</th>
          <th class="p-2 border">仓库</th><th class="p-2 border">操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in items" :key="item.id" class="hover:bg-zinc-50" :class="item.quantity <= item.min_stock ? 'bg-red-50' : ''">
          <td class="p-2 border font-mono text-xs">{{ item.product_code }}</td>
          <td class="p-2 border">{{ item.product_name }}</td>
          <td class="p-2 border">{{ item.category }}</td>
          <td class="p-2 border text-right" :class="item.quantity <= item.min_stock ? 'text-red-600 font-bold' : ''">
            {{ item.quantity }} {{ item.unit }}
            <span v-if="item.quantity <= item.min_stock" class="text-xs text-red-500 ml-1">⚠低于最低库存</span>
          </td>
          <td class="p-2 border text-right">{{ item.unit_cost.toLocaleString() }}</td>
          <td class="p-2 border text-right">{{ item.total_cost.toLocaleString() }}</td>
          <td class="p-2 border">{{ item.warehouse }}</td>
          <td class="p-2 border">
            <button @click="openEdit(item)" class="text-blue-600 mr-1 text-xs">编辑</button>
            <button @click="remove(item.id)" class="text-red-500 text-xs">删除</button>
          </td>
        </tr>
      </tbody>
    </table>
    <div v-if="dialogVisible" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg w-[550px] p-6">
        <h2 class="text-lg font-bold mb-4">{{ isEdit ? '编辑库存' : '新增库存' }}</h2>
        <div class="grid grid-cols-2 gap-3">
          <div><label class="text-xs text-zinc-500">产品编码</label><input v-model="form.product_code" class="w-full border rounded px-2 py-1 text-sm" /></div>
          <div><label class="text-xs text-zinc-500">产品名称</label><input v-model="form.product_name" class="w-full border rounded px-2 py-1 text-sm" /></div>
          <div><label class="text-xs text-zinc-500">类别</label><input v-model="form.category" class="w-full border rounded px-2 py-1 text-sm" /></div>
          <div><label class="text-xs text-zinc-500">单位</label><input v-model="form.unit" class="w-full border rounded px-2 py-1 text-sm" /></div>
          <div><label class="text-xs text-zinc-500">数量</label><input type="number" v-model.number="form.quantity" class="w-full border rounded px-2 py-1 text-sm" /></div>
          <div><label class="text-xs text-zinc-500">单位成本</label><input type="number" v-model.number="form.unit_cost" class="w-full border rounded px-2 py-1 text-sm" /></div>
          <div><label class="text-xs text-zinc-500">仓库</label><input v-model="form.warehouse" class="w-full border rounded px-2 py-1 text-sm" /></div>
          <div><label class="text-xs text-zinc-500">最低库存</label><input type="number" v-model.number="form.min_stock" class="w-full border rounded px-2 py-1 text-sm" /></div>
        </div>
        <div class="flex justify-end gap-2 mt-4">
          <button @click="dialogVisible = false" class="px-4 py-1.5 border rounded text-sm">取消</button>
          <button @click="save" class="px-4 py-1.5 bg-blue-600 text-white rounded text-sm">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/api/index.ts frontend/src/views/inventory_trade/InvPurchases.vue frontend/src/views/inventory_trade/InvStock.vue
git commit --no-gpg-sign -m "feat: add Inventory frontend — Purchase/Stock CRUD pages + API

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Phase 7: Final Integration & Database Tables

### Task 7.1: Create all new database tables

- [ ] **Step 1: Create tables**

```bash
cd backend && uv run python -c "
from app.database import engine
from app.models import Base
# Import all new models to register them with Base
from app.models import FixedAsset, FixedAssetDepreciation
from app.models import Receivable, ReceivablePayment
from app.models import Payable, PayablePayment
from app.models import InvPurchase, InvSale, InvStock
Base.metadata.create_all(bind=engine)
print('All new tables created')
"
```

Expected: "All new tables created"

- [ ] **Step 2: Verify backend starts cleanly**

```bash
cd backend && timeout 5 uv run uvicorn app.main:app 2>&1 || true
```

Expected: No import errors, server starts.

- [ ] **Step 3: Verify frontend builds**

```bash
cd frontend && npx vite build 2>&1 | tail -10
```

Expected: Build succeeds.

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit --no-gpg-sign -m "feat: add database tables for FA/AR/AP/Inventory modules

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Summary: Task Execution Order

| # | Task | Est. Time | Phase |
|---|------|-----------|-------|
| 1.1 | Restructure menuConfig.ts | 10 min | Foundation |
| 1.2 | Add routes for new modules | 5 min | Foundation |
| 1.3 | Create 20 placeholder Vue pages | 10 min | Foundation |
| 2.1 | FixedAsset models | 5 min | FA Backend |
| 2.2 | FixedAsset schemas | 5 min | FA Backend |
| 2.3 | FixedAsset router + main.py | 10 min | FA Backend |
| 2.4 | FixedAsset API functions | 5 min | FA Frontend |
| 2.5 | FixedAssetRegister.vue (CRUD page) | 15 min | FA Frontend |
| 2.6 | Create FA tables | 2 min | FA |
| 3.1 | AR models | 5 min | AR Backend |
| 3.2 | AR schemas | 3 min | AR Backend |
| 3.3 | AR router + main.py | 10 min | AR Backend |
| 3.4 | AR API + ReceivableCustomers.vue | 15 min | AR Frontend |
| 4.1 | AP models | 5 min | AP Backend |
| 4.2 | AP schemas + router + main.py | 10 min | AP Backend |
| 4.3 | AP API + PayableSuppliers.vue | 10 min | AP Frontend |
| 5.1 | Admin module (verify/improve existing) | 5 min | Admin |
| 6.1 | Inventory models | 5 min | Inv Backend |
| 6.2 | Inventory schemas | 5 min | Inv Backend |
| 6.3 | Inventory router + main.py | 10 min | Inv Backend |
| 6.4 | Inventory API + 2 views | 10 min | Inv Frontend |
| 7.1 | Create DB tables + final verification | 5 min | Integration |

**Total estimated: ~3 hours**
