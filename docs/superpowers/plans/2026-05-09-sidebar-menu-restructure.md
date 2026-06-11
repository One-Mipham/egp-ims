# Sidebar Menu Restructure — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure sidebar into 5-module system (HR, Admin, Accounting, Finance, Board), extract SidebarMenu component, split cockpit pages, simplify Dashboard.

**Architecture:** Extract menu data to `menuConfig.ts`, sidebar rendering to `SidebarMenu.vue`, cockpit sections from Dashboard into independent pages with role-based access. Existing routes/views preserved.

**Tech Stack:** Vue 3 Composition API, PrimeVue, Vue Router, TypeScript

---

### Task 1: Create menuConfig.ts — 5-module menu data

**Files:**
- Create: `frontend/src/config/menuConfig.ts`

- [ ] **Step 1: Write the menu config file**

```typescript
// frontend/src/config/menuConfig.ts

export interface MenuChild {
  label: string
  to: string
}

export interface MenuItem {
  label: string
  icon?: string
  to?: string
  children?: MenuChild[]
  /** If set, item is locked (gray + lock icon) for roles NOT in this list */
  roles?: string[]
  /** Message shown when locked item is clicked */
  lockedMessage?: string
}

export interface MenuSection {
  icon: string
  title: string
  items: MenuItem[]
}

export const menuSections: MenuSection[] = [
  // ═══════════ 一、人力资源管理系统 ═══════════
  {
    icon: 'pi pi-users',
    title: '一、人力资源管理系统',
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

  // ═══════════ 二、行政综合管理系统 ═══════════
  {
    icon: 'pi pi-building',
    title: '二、行政综合管理系统',
    items: [
      { label: '2.1 文件管理', to: '/finance/admin/documents', icon: 'pi pi-file' },
      { label: '2.2 车辆管理', to: '/finance/admin/vehicles', icon: 'pi pi-car' },
      { label: '2.3 财产保险', to: '/finance/admin/insurance', icon: 'pi pi-shield' },
      { label: '2.4 门禁管理', to: '/finance/admin/access', icon: 'pi pi-lock' },
      { label: '2.5 资产与仓库管理', to: '/finance/inventory', icon: 'pi pi-box' },
    ],
  },

  // ═══════════ 三、会计管理系统 ═══════════
  {
    icon: 'pi pi-book',
    title: '三、会计管理系统',
    items: [
      {
        label: '3.0 会计管理驾驶舱',
        to: '/finance/cockpit/accounting',
        icon: 'pi pi-desktop',
        roles: ['accountant', 'finance_manager', 'finance_director', 'super_admin'],
        lockedMessage: '您无权访问会计管理驾驶舱。需要：会计、财务经理、财务总监或系统管理员权限。',
      },
      {
        label: '3.1 基础设置',
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
        label: '3.2 总账',
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
      { label: '3.3 进销存管理', to: '/finance/inventory-trade', icon: 'pi pi-shopping-cart' },
      { label: '3.4 应收账款', to: '/finance/receivables', icon: 'pi pi-arrow-right' },
      { label: '3.5 应付账款', to: '/finance/payables', icon: 'pi pi-arrow-left' },
      { label: '3.6 固定资产管理', to: '/finance/fixed-assets', icon: 'pi pi-wrench' },
      {
        label: '3.7 税务管理',
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
        label: '3.8 投资管理',
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
      {
        label: '3.9 报表中心',
        icon: 'pi pi-chart-bar',
        children: [
          { label: '财务报表', to: '/finance/reports' },
          { label: '月度报表', to: '/finance/reports/monthly' },
          { label: '季度报表', to: '/finance/reports/quarterly' },
          { label: '年度报表', to: '/finance/reports/yearly' },
          { label: '审计日志', to: '/finance/audit' },
        ],
      },
      { label: '3.10 协同办公', to: '/finance/todo', icon: 'pi pi-inbox' },
      {
        label: '3.11 系统设置',
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

  // ═══════════ 四、财务管理系统 ═══════════
  {
    icon: 'pi pi-chart-line',
    title: '四、财务管理系统',
    items: [
      {
        label: '4.0 财务管理驾驶舱',
        to: '/finance/cockpit/finance',
        icon: 'pi pi-desktop',
        roles: ['finance_manager', 'finance_director', 'super_admin'],
        lockedMessage: '您无权访问财务管理驾驶舱。需要：财务经理、财务总监或系统管理员权限。',
      },
      { label: '4.1 预算管理与绩效评价', to: '/finance/cockpit/budget', icon: 'pi pi-chart-line' },
      { label: '4.2 现金流计划与融资计划', to: '/finance/cockpit/cashflow', icon: 'pi pi-money-bill' },
      { label: '4.3 经营分析指标', to: '/finance/cockpit/indicators', icon: 'pi pi-chart-bar' },
    ],
  },

  // ═══════════ 五、董事办工作 ═══════════
  {
    icon: 'pi pi-briefcase',
    title: '五、董事办工作',
    items: [
      { label: '5.1 董事会工作条例', to: '/finance/board/bylaws', icon: 'pi pi-file' },
      {
        label: '5.2 董事会专业委员会',
        icon: 'pi pi-sitemap',
        children: [
          { label: '提名委员会', to: '/finance/board/committees/nomination' },
          { label: '薪酬与绩效考核委员会', to: '/finance/board/committees/compensation' },
          { label: '战略发展委员会', to: '/finance/board/committees/strategy' },
          { label: '审计与稽核委员会', to: '/finance/board/committees/audit' },
        ],
      },
      { label: '5.3 董秘工作职责', to: '/finance/board/secretary', icon: 'pi pi-user' },
      { label: '5.4 交易所工作对接', to: '/finance/board/exchange', icon: 'pi pi-globe' },
      { label: '5.5 证监会、局工作对接', to: '/finance/board/csrc', icon: 'pi pi-shield' },
      { label: '5.6 财务报告', to: '/finance/board/financial-reports', icon: 'pi pi-chart-bar' },
      { label: '5.7 股东管理', to: '/finance/board/shareholders', icon: 'pi pi-users' },
      { label: '5.8 投资者关系管理', to: '/finance/board/investors', icon: 'pi pi-comments' },
      { label: '5.9 政府关系管理', to: '/finance/board/government', icon: 'pi pi-building' },
      { label: '5.10 媒体关系管理', to: '/finance/board/media', icon: 'pi pi-video' },
    ],
  },
]

/** Flatten all menu items for breadcrumb title matching */
export function flattenItems(sections: MenuSection[]) {
  const result: Array<{ label: string; to?: string }> = []
  for (const s of sections) {
    for (const item of s.items) {
      if (item.to && !item.children) result.push({ label: item.label, to: item.to })
      if (item.children) result.push(...item.children.map(c => ({ label: c.label, to: c.to })))
    }
  }
  return result
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/config/menuConfig.ts
git commit -m "feat: add 5-module menu configuration with permission support"
```

---

### Task 2: Create SidebarMenu.vue — extracted sidebar menu component

**Files:**
- Create: `frontend/src/components/SidebarMenu.vue`

- [ ] **Step 1: Write the SidebarMenu component**

```vue
<!-- frontend/src/components/SidebarMenu.vue -->
<script setup lang="ts">
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import type { MenuSection } from '@/config/menuConfig'

defineProps<{
  sections: MenuSection[]
  userRole: string
}>()

const emit = defineEmits<{
  locked: [message: string]
}>()

const route = useRoute()
const expandedSections = ref<Set<string>>(new Set())
const expandedSubmenus = ref<Set<string>>(new Set())

function toggleSection(key: string) {
  const set = expandedSections.value
  if (set.has(key)) set.delete(key)
  else set.add(key)
  expandedSections.value = new Set(set)
}

function toggleSubmenu(key: string) {
  const set = expandedSubmenus.value
  if (set.has(key)) set.delete(key)
  else set.add(key)
  expandedSubmenus.value = new Set(set)
}

function isLocked(item: { roles?: string[] }, userRole: string): boolean {
  if (!item.roles || item.roles.length === 0) return false
  return !item.roles.includes(userRole)
}

function handleLockedClick(item: { lockedMessage?: string }) {
  emit('locked', item.lockedMessage || '您无权访问此功能')
}
</script>

<template>
  <nav class="flex-1 overflow-y-auto py-1">
    <template v-for="section in sections" :key="section.title">
      <!-- Section header with expand/collapse -->
      <button
        @click="toggleSection(section.title)"
        class="w-full flex items-center gap-2 px-3 py-2 text-xs sidebar-item transition-colors tracking-wide"
      >
        <i :class="[section.icon, 'text-xs w-4 text-center']" />
        <span class="flex-1 text-left">{{ section.title }}</span>
        <i
          :class="[
            'pi text-[10px] sidebar-item-sub transition-transform',
            expandedSections.has(section.title) ? 'pi-angle-up' : 'pi-angle-down'
          ]"
        />
      </button>

      <!-- Section items -->
      <div v-show="expandedSections.has(section.title)">
        <template v-for="item in section.items" :key="item.label">
          <!-- Item with children (3rd level submenu) -->
          <div v-if="item.children && item.children.length">
            <button
              @click="toggleSubmenu(item.label)"
              class="w-full flex items-center gap-2 pl-7 pr-3 py-1.5 text-xs sidebar-item-sub transition-colors tracking-wide"
            >
              <i :class="['pi', item.icon, 'text-[10px] w-4 text-center']" />
              <span class="flex-1 text-left">{{ item.label }}</span>
              <i
                :class="[
                  'pi text-[10px] sidebar-item-sub transition-transform',
                  expandedSubmenus.has(item.label) ? 'pi-angle-up' : 'pi-angle-down'
                ]"
              />
            </button>
            <div v-show="expandedSubmenus.has(item.label)" class="sidebar-submenu-bg">
              <router-link
                v-for="child in item.children"
                :key="child.to"
                :to="child.to"
                class="flex items-center gap-2 pl-12 pr-3 py-1 text-xs sidebar-item-sub transition-colors"
                :class="{ 'sidebar-item-active': route.path === child.to }"
              >
                {{ child.label }}
              </router-link>
            </div>
          </div>

          <!-- Direct link item -->
          <router-link
            v-else-if="item.to && !isLocked(item, userRole)"
            :to="item.to"
            class="flex items-center gap-2 pl-7 pr-3 py-1.5 text-xs sidebar-item-sub transition-colors"
            :class="{ 'sidebar-item-active': route.path === item.to }"
          >
            <i :class="['pi', item.icon, 'text-[10px] w-4 text-center']" />
            <span>{{ item.label }}</span>
          </router-link>

          <!-- Locked item (visible but grayed out) -->
          <button
            v-else-if="item.to && isLocked(item, userRole)"
            @click="handleLockedClick(item)"
            class="w-full flex items-center gap-2 pl-7 pr-3 py-1.5 text-xs sidebar-item-sub transition-colors tracking-wide opacity-50 cursor-not-allowed"
          >
            <i :class="['pi', item.icon, 'text-[10px] w-4 text-center']" />
            <span class="flex-1 text-left">{{ item.label }}</span>
            <i class="pi pi-lock text-[10px]" />
          </button>
        </template>
      </div>
    </template>
  </nav>
</template>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/SidebarMenu.vue
git commit -m "feat: extract SidebarMenu component with permission-locked items"
```

---

### Task 3: Modify App.vue — use SidebarMenu, remove inline menu

**Files:**
- Modify: `frontend/src/App.vue`

- [ ] **Step 1: Remove the old `menuSections` array, `expandedSections`, `expandedSubmenus`, toggle functions, and `flattenItems` from `<script setup>`**

Delete lines 9-26 (expanded refs + toggle functions) and lines 29-194 (menuSections + flattenItems + menuItems).

- [ ] **Step 2: Add imports for menu config and SidebarMenu component**

Add at the top of `<script setup>` (after existing imports):

```typescript
import SidebarMenu from '@/components/SidebarMenu.vue'
import { menuSections, flattenItems } from '@/config/menuConfig'
```

- [ ] **Step 3: Add toast notification state and handler, recompute menuItems**

Add after theme state (around line 203):

```typescript
const notificationMessage = ref<string | null>(null)
let notificationTimer: ReturnType<typeof setTimeout> | null = null

function showNotification(msg: string) {
  notificationMessage.value = msg
  if (notificationTimer) clearTimeout(notificationTimer)
  notificationTimer = setTimeout(() => {
    notificationMessage.value = null
  }, 3000)
}

const menuItems = flattenItems(menuSections)
```

- [ ] **Step 4: Replace sidebar nav template (lines 282-338) with SidebarMenu component**

Replace the entire `<nav class="flex-1 overflow-y-auto py-1">` block with:

```html
<SidebarMenu
  :sections="menuSections"
  :user-role="currentUser?.role || ''"
  @locked="showNotification"
/>
```

- [ ] **Step 5: Add toast notification UI in the template**

Add after the top-bar `</header>` tag and before `<main>` (around line 406):

```html
<!-- Toast notification -->
<div
  v-if="notificationMessage"
  class="fixed top-4 right-4 z-50 bg-red-700 text-white text-xs px-4 py-2.5 rounded-sm shadow-lg transition-all max-w-xs"
>
  <div class="flex items-center gap-2">
    <i class="pi pi-lock text-xs" />
    <span>{{ notificationMessage }}</span>
  </div>
</div>
```

- [ ] **Step 6: Verify no broken references**

Confirm the template still references `currentUser`, `menuItems`, `handleLogout`, `showThemePopup`, `THEMES`, `currentTheme`, `applyTheme`, `isLoginPage` — all still exist.

The breadcrumb in top-bar (line 395) uses `menuItems` which is now computed from the new config.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/App.vue
git commit -m "refactor: use SidebarMenu component, clean up App.vue"
```

---

### Task 4: Create AccountingCockpit.vue — accounting cockpit (6 boxes)

**Files:**
- Create: `frontend/src/views/AccountingCockpit.vue`

- [ ] **Step 1: Write AccountingCockpit.vue**

Extract the "会计管理驾驶舱" section from Dashboard.vue — 4 stat cards + 2 toggle cards.

```vue
<!-- frontend/src/views/AccountingCockpit.vue -->
<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { listVouchers, listPeriods, listAccounts, listDepartments } from '@/api'

const stats = ref([
  { label: '凭证总数', value: 0, icon: 'pi pi-file', color: 'bg-sky-700' },
  { label: '科目数量', value: 0, icon: 'pi pi-book', color: 'bg-indigo-600' },
  { label: '部门数量', value: 0, icon: 'pi pi-building', color: 'bg-emerald-600' },
  { label: '已结账期间', value: 0, icon: 'pi pi-check-circle', color: 'bg-violet-600' },
])

const taxFiledOnTime = ref<boolean | null>(null)
const bankReconciled = ref<boolean | null>(null)
const loading = ref(false)
const companyId = computed(() => parseInt(localStorage.getItem('companyId') || '1'))

onMounted(async () => {
  loading.value = true
  try {
    const [v, a, d, p] = await Promise.all([
      listVouchers(companyId.value),
      listAccounts(companyId.value),
      listDepartments(companyId.value),
      listPeriods(companyId.value),
    ])
    stats.value[0].value = v.data.length
    stats.value[1].value = a.data.length
    stats.value[2].value = d.data.length
    stats.value[3].value = p.data.filter((x: any) => x.is_closed).length
  } catch { /* use defaults */ }
  finally { loading.value = false }
})
</script>

<template>
  <div class="space-y-6">
    <div class="page-header">
      <h2>会计管理驾驶舱</h2>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div v-for="stat in stats" :key="stat.label" class="stat-card">
        <div :class="['stat-icon', stat.color]">
          <i :class="['pi', stat.icon]" />
        </div>
        <div>
          <div class="stat-value">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.label }}</div>
        </div>
      </div>

      <!-- 是否按时报税 -->
      <div
        class="stat-card cursor-pointer"
        @click="taxFiledOnTime = taxFiledOnTime === null ? true : taxFiledOnTime === true ? false : null"
      >
        <div
          :class="[
            'stat-icon',
            taxFiledOnTime === true ? 'bg-emerald-600' : taxFiledOnTime === false ? 'bg-red-600' : 'bg-zinc-400'
          ]"
        >
          <i :class="['pi', taxFiledOnTime === true ? 'pi-check' : taxFiledOnTime === false ? 'pi-times' : 'pi-calendar']" />
        </div>
        <div>
          <div class="stat-value text-sm">
            {{ taxFiledOnTime === true ? '已报税' : taxFiledOnTime === false ? '未报税' : '点击设置' }}
          </div>
          <div class="stat-label">是否按时报税</div>
        </div>
      </div>

      <!-- 是否按时完成银行对账 -->
      <div
        class="stat-card cursor-pointer"
        @click="bankReconciled = bankReconciled === null ? true : bankReconciled === true ? false : null"
      >
        <div
          :class="[
            'stat-icon',
            bankReconciled === true ? 'bg-emerald-600' : bankReconciled === false ? 'bg-red-600' : 'bg-zinc-400'
          ]"
        >
          <i :class="['pi', bankReconciled === true ? 'pi-check' : bankReconciled === false ? 'pi-times' : 'pi-building']" />
        </div>
        <div>
          <div class="stat-value text-sm">
            {{ bankReconciled === true ? '已对账' : bankReconciled === false ? '未对账' : '点击设置' }}
          </div>
          <div class="stat-label">是否按时完成银行对账</div>
        </div>
      </div>
    </div>

    <p v-if="loading" class="text-stone-400 text-xs tracking-wide">加载数据中...</p>
  </div>
</template>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/AccountingCockpit.vue
git commit -m "feat: add accounting cockpit page (6 boxes)"
```

---

### Task 5: Create FinanceCockpit.vue — finance cockpit (3 menu + 6 indicators)

**Files:**
- Create: `frontend/src/views/FinanceCockpit.vue`

- [ ] **Step 1: Write FinanceCockpit.vue**

Extract the "财务管理驾驶舱" section from Dashboard.vue — 3 menu items + 6 indicator lights.

```vue
<!-- frontend/src/views/FinanceCockpit.vue -->
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api'

const router = useRouter()

const indicators = ref([
  { label: '预算完成表现', status: 'green' as 'green' | 'yellow' | 'red' },
  { label: '现金流安全',   status: 'green' as 'green' | 'yellow' | 'red' },
  { label: '偿债能力',     status: 'green' as 'green' | 'yellow' | 'red' },
  { label: '营运能力',     status: 'green' as 'green' | 'yellow' | 'red' },
  { label: '盈利能力',     status: 'green' as 'green' | 'yellow' | 'red' },
  { label: '成长能力',     status: 'green' as 'green' | 'yellow' | 'red' },
])

const cockpitPaths: Record<string, string> = {
  '预算完成表现': '/finance/cockpit/budget',
  '现金流安全':   '/finance/cockpit/cashflow',
  '偿债能力':     '/finance/cockpit/indicators',
  '营运能力':     '/finance/cockpit/indicators',
  '盈利能力':     '/finance/cockpit/indicators',
  '成长能力':     '/finance/cockpit/indicators',
}

function goCockpit(label: string) {
  const path = cockpitPaths[label]
  if (path) router.push(path)
}

const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    const res = await api.get('/cockpit/cockpit-lights')
    if (res.data) {
      for (const ind of indicators.value) {
        if (res.data[ind.label]) ind.status = res.data[ind.label]
      }
    }
  } catch { /* use defaults */ }
  finally { loading.value = false }
})

const STATUS_MAP: Record<string, { bg: string; dot: string; text: string; label: string }> = {
  green:  { bg: 'bg-emerald-50 border-emerald-300', dot: 'bg-emerald-500', text: 'text-emerald-700', label: '绿灯' },
  yellow: { bg: 'bg-amber-50 border-amber-300',     dot: 'bg-amber-500',   text: 'text-amber-700',   label: '黄灯' },
  red:    { bg: 'bg-red-50 border-red-300',         dot: 'bg-red-500',     text: 'text-red-700',     label: '红灯' },
}

const financeMenu = [
  { label: '公司预算与分析评价', path: '/finance/cockpit/budget', icon: 'pi-chart-line' },
  { label: '现金流计划与融资计划', path: '/finance/cockpit/cashflow', icon: 'pi-money-bill' },
  { label: '公司经营分析指标', path: '/finance/cockpit/indicators', icon: 'pi-chart-bar' },
]
</script>

<template>
  <div class="space-y-6">
    <div class="page-header">
      <h2>财务管理驾驶舱</h2>
    </div>

    <div class="flex flex-col lg:flex-row gap-6">
      <!-- 左侧菜单 — 三个可点击项目 -->
      <div class="lg:w-64 shrink-0">
        <div class="bg-white border border-stone-200 rounded-sm shadow-sm overflow-hidden">
          <div
            v-for="(item, idx) in financeMenu"
            :key="item.label"
            @click="router.push(item.path)"
            class="px-4 py-2.5 text-sm text-stone-700 hover:bg-stone-50 cursor-pointer transition-colors flex items-center gap-2"
            :class="{ 'border-b border-stone-100': idx < financeMenu.length - 1 }"
          >
            <i :class="['pi', item.icon, 'text-xs']" />
            {{ item.label }}
          </div>
        </div>
      </div>

      <!-- 右侧六项指标灯 -->
      <div class="flex-1 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        <div
          v-for="ind in indicators"
          :key="ind.label"
          @click="goCockpit(ind.label)"
          class="border rounded-sm px-4 py-3 cursor-pointer transition-all hover:shadow-sm select-none"
          :class="STATUS_MAP[ind.status].bg"
        >
          <div class="flex items-center justify-between">
            <span class="text-sm font-medium text-stone-700">{{ ind.label }}</span>
            <span
              class="inline-flex items-center gap-1.5 text-xs font-medium px-2 py-0.5 rounded-full"
              :class="ind.status === 'green' ? 'bg-emerald-100 text-emerald-700' : ind.status === 'yellow' ? 'bg-amber-100 text-amber-700' : 'bg-red-100 text-red-700'"
            >
              <span class="w-2 h-2 rounded-full" :class="STATUS_MAP[ind.status].dot"></span>
              {{ STATUS_MAP[ind.status].label }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <p class="text-xs text-stone-400 mt-3">点击指示灯可查看详细指标分析</p>
    <p v-if="loading" class="text-stone-400 text-xs tracking-wide">加载数据中...</p>
  </div>
</template>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/FinanceCockpit.vue
git commit -m "feat: add finance cockpit page (3 menu + 6 indicators)"
```

---

### Task 6: Modify Dashboard.vue — simplify to summary home page

**Files:**
- Modify: `frontend/src/views/Dashboard.vue`

- [ ] **Step 1: Replace entire Dashboard.vue content**

Keep only cockpit entry cards as a summary overview.

```vue
<!-- frontend/src/views/Dashboard.vue -->
<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { getMe } from '@/api'

const router = useRouter()
const userRole = ref<string>('')

const canViewAccountingCockpit = computed(() =>
  ['accountant', 'finance_manager', 'finance_director', 'super_admin'].includes(userRole.value)
)
const canViewFinanceCockpit = computed(() =>
  ['finance_manager', 'finance_director', 'super_admin'].includes(userRole.value)
)

onMounted(async () => {
  try {
    const me = await getMe()
    userRole.value = me.data.role
  } catch { /* hidden if no role */ }
})
</script>

<template>
  <div class="space-y-8">
    <!-- Welcome -->
    <div class="page-header">
      <h2>管理驾驶舱</h2>
    </div>
    <p class="text-sm text-stone-500 -mt-4">选择以下驾驶舱进入对应管理视图</p>

    <!-- Cockpit entry cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-3xl">
      <!-- 会计管理驾驶舱入口 -->
      <div
        @click="canViewAccountingCockpit && router.push('/finance/cockpit/accounting')"
        class="border rounded-sm p-6 transition-all shadow-sm hover:shadow-md select-none"
        :class="canViewAccountingCockpit
          ? 'bg-white border-stone-200 cursor-pointer hover:border-emerald-300'
          : 'bg-stone-100 border-stone-200 opacity-60 cursor-not-allowed'"
      >
        <div class="flex items-center gap-3 mb-3">
          <div class="w-10 h-10 rounded-full bg-sky-100 flex items-center justify-center">
            <i class="pi pi-book text-sky-700" />
          </div>
          <div>
            <h3 class="text-base font-semibold text-stone-800">会计管理驾驶舱</h3>
            <p class="text-xs text-stone-500">凭证 · 科目 · 报税 · 对账</p>
          </div>
        </div>
        <div class="grid grid-cols-2 gap-2 text-xs text-stone-500">
          <span class="flex items-center gap-1"><i class="pi pi-check text-emerald-500 text-[10px]" /> 凭证统计</span>
          <span class="flex items-center gap-1"><i class="pi pi-check text-emerald-500 text-[10px]" /> 科目概览</span>
          <span class="flex items-center gap-1"><i class="pi pi-check text-emerald-500 text-[10px]" /> 报税状态</span>
          <span class="flex items-center gap-1"><i class="pi pi-check text-emerald-500 text-[10px]" /> 对账状态</span>
        </div>
        <div v-if="!canViewAccountingCockpit" class="mt-3 flex items-center gap-1 text-xs text-stone-400">
          <i class="pi pi-lock text-[10px]" /> 需要会计及以上权限
        </div>
      </div>

      <!-- 财务管理驾驶舱入口 -->
      <div
        @click="canViewFinanceCockpit && router.push('/finance/cockpit/finance')"
        class="border rounded-sm p-6 transition-all shadow-sm hover:shadow-md select-none"
        :class="canViewFinanceCockpit
          ? 'bg-white border-stone-200 cursor-pointer hover:border-amber-300'
          : 'bg-stone-100 border-stone-200 opacity-60 cursor-not-allowed'"
      >
        <div class="flex items-center gap-3 mb-3">
          <div class="w-10 h-10 rounded-full bg-amber-100 flex items-center justify-center">
            <i class="pi pi-chart-line text-amber-700" />
          </div>
          <div>
            <h3 class="text-base font-semibold text-stone-800">财务管理驾驶舱</h3>
            <p class="text-xs text-stone-500">预算 · 现金流 · 经营指标</p>
          </div>
        </div>
        <div class="grid grid-cols-2 gap-2 text-xs text-stone-500">
          <span class="flex items-center gap-1"><i class="pi pi-check text-emerald-500 text-[10px]" /> 预算表现</span>
          <span class="flex items-center gap-1"><i class="pi pi-check text-emerald-500 text-[10px]" /> 现金流安全</span>
          <span class="flex items-center gap-1"><i class="pi pi-check text-emerald-500 text-[10px]" /> 偿债/营运/盈利</span>
          <span class="flex items-center gap-1"><i class="pi pi-check text-emerald-500 text-[10px]" /> 成长能力</span>
        </div>
        <div v-if="!canViewFinanceCockpit" class="mt-3 flex items-center gap-1 text-xs text-stone-400">
          <i class="pi pi-lock text-[10px]" /> 需要财务经理及以上权限
        </div>
      </div>
    </div>
  </div>
</template>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/Dashboard.vue
git commit -m "refactor: simplify Dashboard to cockpit entry summary page"
```

---

### Task 7: Modify router/index.ts — add new routes with role guards

**Files:**
- Modify: `frontend/src/router/index.ts`

- [ ] **Step 1: Add cockpit routes with role metadata**

Add after the existing cockpit routes (line 99):

```typescript
// Cockpit — standalone pages with role permissions
{ path: '/finance/cockpit/accounting', component: () => import('../views/AccountingCockpit.vue'), meta: { requiresAuth: true, allowedRoles: ['accountant', 'finance_manager', 'finance_director', 'super_admin'] } },
{ path: '/finance/cockpit/finance', component: () => import('../views/FinanceCockpit.vue'), meta: { requiresAuth: true, allowedRoles: ['finance_manager', 'finance_director', 'super_admin'] } },
```

- [ ] **Step 2: Add placeholder routes for new modules (HR, Admin, Board)**

Add after existing routes:

```typescript
// HR module (placeholder)
{ path: '/finance/hr/policy', component: () => import('../views/PlaceholderPage.vue'), meta: { requiresAuth: true, pageTitle: '公司人力资源管理制度' } },
{ path: '/finance/hr/onboarding', component: () => import('../views/PlaceholderPage.vue'), meta: { requiresAuth: true, pageTitle: '员工入职' } },
{ path: '/finance/hr/training', component: () => import('../views/PlaceholderPage.vue'), meta: { requiresAuth: true, pageTitle: '员工培训' } },
{ path: '/finance/hr/evaluation', component: () => import('../views/PlaceholderPage.vue'), meta: { requiresAuth: true, pageTitle: '员工考核' } },
{ path: '/finance/hr/compensation', component: () => import('../views/PlaceholderPage.vue'), meta: { requiresAuth: true, pageTitle: '薪酬管理' } },
{ path: '/finance/hr/rewards', component: () => import('../views/PlaceholderPage.vue'), meta: { requiresAuth: true, pageTitle: '员工奖惩' } },
{ path: '/finance/hr/offboarding', component: () => import('../views/PlaceholderPage.vue'), meta: { requiresAuth: true, pageTitle: '员工离职' } },
{ path: '/finance/hr/budget', component: () => import('../views/PlaceholderPage.vue'), meta: { requiresAuth: true, pageTitle: '人力资源预算管理' } },
// Admin module (placeholder)
{ path: '/finance/admin/documents', component: () => import('../views/PlaceholderPage.vue'), meta: { requiresAuth: true, pageTitle: '文件管理' } },
{ path: '/finance/admin/vehicles', component: () => import('../views/PlaceholderPage.vue'), meta: { requiresAuth: true, pageTitle: '车辆管理' } },
{ path: '/finance/admin/insurance', component: () => import('../views/PlaceholderPage.vue'), meta: { requiresAuth: true, pageTitle: '财产保险' } },
{ path: '/finance/admin/access', component: () => import('../views/PlaceholderPage.vue'), meta: { requiresAuth: true, pageTitle: '门禁管理' } },
// Inventory (migrated from 移动仓管)
{ path: '/finance/inventory', component: () => import('../views/PlaceholderPage.vue'), meta: { requiresAuth: true, pageTitle: '资产与仓库管理' } },
// Accounting — placeholder submodules
{ path: '/finance/inventory-trade', component: () => import('../views/PlaceholderPage.vue'), meta: { requiresAuth: true, pageTitle: '进销存管理' } },
{ path: '/finance/receivables', component: () => import('../views/PlaceholderPage.vue'), meta: { requiresAuth: true, pageTitle: '应收账款' } },
{ path: '/finance/payables', component: () => import('../views/PlaceholderPage.vue'), meta: { requiresAuth: true, pageTitle: '应付账款' } },
{ path: '/finance/fixed-assets', component: () => import('../views/PlaceholderPage.vue'), meta: { requiresAuth: true, pageTitle: '固定资产管理' } },
// Board module (placeholder)
{ path: '/finance/board/bylaws', component: () => import('../views/PlaceholderPage.vue'), meta: { requiresAuth: true, pageTitle: '董事会工作条例' } },
{ path: '/finance/board/committees/nomination', component: () => import('../views/PlaceholderPage.vue'), meta: { requiresAuth: true, pageTitle: '提名委员会' } },
{ path: '/finance/board/committees/compensation', component: () => import('../views/PlaceholderPage.vue'), meta: { requiresAuth: true, pageTitle: '薪酬与绩效考核委员会' } },
{ path: '/finance/board/committees/strategy', component: () => import('../views/PlaceholderPage.vue'), meta: { requiresAuth: true, pageTitle: '战略发展委员会' } },
{ path: '/finance/board/committees/audit', component: () => import('../views/PlaceholderPage.vue'), meta: { requiresAuth: true, pageTitle: '审计与稽核委员会' } },
{ path: '/finance/board/secretary', component: () => import('../views/PlaceholderPage.vue'), meta: { requiresAuth: true, pageTitle: '董秘工作职责' } },
{ path: '/finance/board/exchange', component: () => import('../views/PlaceholderPage.vue'), meta: { requiresAuth: true, pageTitle: '交易所工作对接' } },
{ path: '/finance/board/csrc', component: () => import('../views/PlaceholderPage.vue'), meta: { requiresAuth: true, pageTitle: '证监会、局工作对接' } },
{ path: '/finance/board/financial-reports', component: () => import('../views/PlaceholderPage.vue'), meta: { requiresAuth: true, pageTitle: '财务报告' } },
{ path: '/finance/board/shareholders', component: () => import('../views/PlaceholderPage.vue'), meta: { requiresAuth: true, pageTitle: '股东管理' } },
{ path: '/finance/board/investors', component: () => import('../views/PlaceholderPage.vue'), meta: { requiresAuth: true, pageTitle: '投资者关系管理' } },
{ path: '/finance/board/government', component: () => import('../views/PlaceholderPage.vue'), meta: { requiresAuth: true, pageTitle: '政府关系管理' } },
{ path: '/finance/board/media', component: () => import('../views/PlaceholderPage.vue'), meta: { requiresAuth: true, pageTitle: '媒体关系管理' } },
```

- [ ] **Step 3: Update the beforeEach guard to check role permissions**

Replace the existing `router.beforeEach` (lines 117-126) with:

```typescript
router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth && !token) {
    next('/finance/login')
  } else if (to.path === '/finance/login' && token) {
    next('/finance')
  } else if (to.meta.allowedRoles) {
    const role = localStorage.getItem('role') || ''
    const roles = to.meta.allowedRoles as string[]
    if (!roles.includes(role)) {
      // Redirect to home for unauthorized cockpit access
      next('/finance')
    } else {
      next()
    }
  } else {
    next()
  }
})
```

- [ ] **Step 4: Remove old mobile-stock route (optional — replaced by /finance/inventory)**

The old route `{ path: '/finance/mobile-stock', ... }` (line 94) can stay for backward compatibility but is no longer in the menu.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/router/index.ts
git commit -m "feat: add cockpit routes with role guards, HR/admin/board placeholder routes"
```

---

### Task 8: Verify — build and test

- [ ] **Step 1: Run TypeScript type check**

```bash
cd frontend && npx vue-tsc --noEmit
```
Expected: No type errors.

- [ ] **Step 2: Run Vite build**

```bash
cd frontend && npm run build
```
Expected: Successful build with no errors.

- [ ] **Step 3: Start dev server and manually verify**

```bash
cd frontend && npm run dev
```

Manual checks:
1. Login as `super_admin` — verify all 5 modules visible, both cockpits accessible
2. Click each first-level module — verify expand/collapse works
3. Click "3.0 会计管理驾驶舱" — verify 6 boxes render correctly
4. Click "4.0 财务管理驾驶舱" — verify 3 menu + 6 indicators render
5. Login as `accountant` — verify 会计驾驶舱 accessible, 财务驾驶舱 shows lock
6. Login as `cashier` — verify both cockpits show lock icon, click shows toast
7. Click any placeholder menu item — verify "模块开发中" page with correct title
8. Verify breadcrumb title in top bar updates on navigation
9. Verify dashboard home page shows entry cards with correct state per role

- [ ] **Step 4: Commit any final fixes**

```bash
git add -A
git commit -m "chore: final verification fixes for sidebar restructure"
```

---

## Self-Review Checklist

- [x] Spec coverage: 5 modules defined, cockpit pages separated, Dashboard simplified, permissions wired, placeholder routes added
- [x] No placeholders: All code is complete, no TBD/TODO
- [x] Type consistency: `MenuSection`, `MenuItem`, `MenuChild` types consistent across config and component
- [x] Route consistency: All menu `to` paths have corresponding router entries
