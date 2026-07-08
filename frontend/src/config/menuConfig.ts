export interface MenuChild {
  label: string
  to: string
  icon?: string
  i18nKey?: string
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
  i18nKey?: string
}

export interface MenuSection {
  icon: string
  title: string
  shortTitle: string
  roles?: string[] // 哪些角色可见此模块
  module?: string // 关联的模块标识（用于订阅检查）
  items: MenuItem[]
  i18nKey?: string
  i18nShortKey?: string
}

export const menuSections: MenuSection[] = [
  // ═══════════ 一、人力资源管理系统 ═══════════
  {
    icon: 'pi pi-users',
    title: 'menu.section1_title',
    shortTitle: 'menu.section1_short',
    roles: ['hr_manager', 'super_admin'],
    module: 'hr',
    items: [
      { label: 'menu.item1_0', to: '/hr/policy', icon: 'pi pi-file' },
      { label: 'menu.item1_1', to: '/hr/onboarding', icon: 'pi pi-user-plus' },
      { label: 'menu.item1_2', to: '/hr/training', icon: 'pi pi-book' },
      { label: 'menu.item1_3', to: '/hr/evaluation', icon: 'pi pi-star' },
      { label: 'menu.item1_4', to: '/hr/compensation', icon: 'pi pi-dollar' },
      { label: 'menu.item1_5', to: '/hr/rewards', icon: 'pi pi-thumbs-up' },
      { label: 'menu.item1_6', to: '/hr/offboarding', icon: 'pi pi-sign-out' },
      { label: 'menu.item1_7', to: '/hr/budget', icon: 'pi pi-chart-bar' },
    ],
  },

  // ═══════════ 二、行政综合管理系统 ═══════════
  {
    icon: 'pi pi-building',
    title: 'menu.section2_title',
    shortTitle: 'menu.section2_short',
    roles: ['admin_staff', 'hr_manager', 'super_admin'],
    module: 'admin',
    items: [
      { label: 'menu.item2_1', to: '/admin/documents', icon: 'pi pi-file' },
      {
        label: 'menu.item2_2',
        icon: 'pi pi-car',
        children: [
          { label: 'menu.item2_2_1', to: '/admin/vehicles/purchases' },
          { label: 'menu.item2_2_2', to: '/admin/vehicles/registry' },
          { label: 'menu.item2_2_3', to: '/admin/vehicles/maintenance' },
          { label: 'menu.item2_2_4', to: '/admin/vehicles/suppliers' },
        ],
      },
      { label: 'menu.item2_3', to: '/admin/insurance', icon: 'pi pi-shield' },
      { label: 'menu.item2_4', to: '/admin/access', icon: 'pi pi-lock' },
      {
        label: 'menu.item2_5',
        icon: 'pi pi-box',
        children: [
          { label: 'menu.item2_5_1', to: '/admin/stock/assets' },
          { label: 'menu.item2_5_2', to: '/admin/stock/assets/purchases' },
          { label: 'menu.item2_5_3', to: '/admin/stock/assets/requisitions' },
          { label: 'menu.item2_5_4', to: '/admin/stock/assets/inbound' },
          { label: 'menu.item2_5_5', to: '/admin/stock/assets/outbound' },
          { label: 'menu.item2_5_6', to: '/admin/stock/assets/counts' },
          { label: 'menu.item2_5_7', to: '/admin/stock/gifts' },
          { label: 'menu.item2_5_8', to: '/admin/stock/gifts/purchases' },
          { label: 'menu.item2_5_9', to: '/admin/stock/gifts/requisitions' },
          { label: 'menu.item2_5_10', to: '/admin/stock/gifts/inbound' },
          { label: 'menu.item2_5_11', to: '/admin/stock/gifts/outbound' },
        ],
      },
    ],
  },

  // ═══════════ 三、招投标管理 ═══════════
  {
    icon: 'pi pi-gavel',
    title: 'menu.section3_title',
    shortTitle: 'menu.section3_short',
    roles: ['admin_staff', 'super_admin'],
    module: 'bids',
    items: [
      {
        label: 'menu.item3_1',
        icon: 'pi pi-file-edit',
        children: [
          { label: 'menu.item3_1_1', to: '/bids/tendering/projects' },
          { label: 'menu.item3_1_2', to: '/bids/tendering/documents' },
          { label: 'menu.item3_1_3', to: '/bids/tendering/openings' },
          { label: 'menu.item3_1_4', to: '/bids/tendering/evaluations' },
          { label: 'menu.item3_1_5', to: '/bids/tendering/awards' },
          { label: 'menu.item3_1_6', to: '/bids/tendering/exceptions' },
        ],
      },
      {
        label: 'menu.item3_2',
        icon: 'pi pi-briefcase',
        children: [
          { label: 'menu.item3_2_1', to: '/bids/bidding/registrations' },
          { label: 'menu.item3_2_2', to: '/bids/bidding/documents' },
          { label: 'menu.item3_2_3', to: '/bids/bidding/pricing' },
          { label: 'menu.item3_2_4', to: '/bids/bidding/bonds' },
          { label: 'menu.item3_2_5', to: '/bids/bidding/exceptions' },
        ],
      },
    ],
  },

  // ═══════════ 四、投资管理系统 ═══════════
  {
    icon: 'pi pi-chart-bar',
    title: 'menu.section4_title',
    shortTitle: 'menu.section4_short',
    roles: ['finance_manager', 'finance_director', 'super_admin'],
    module: 'investments',
    items: [
      {
        label: 'menu.item4_0',
        icon: 'pi pi-chart-line',
        to: '/investments/dashboard',
      },
      {
        label: 'menu.item4_1',
        icon: 'pi pi-folder',
        children: [
          { label: 'menu.item4_1_1', to: '/investments/portfolio' },
          { label: 'menu.item4_1_2', to: '/investments/positions' },
          { label: 'menu.item4_1_3', to: '/investments/transactions' },
          { label: 'menu.item4_1_4', to: '/investments/income' },
          { label: 'menu.item4_1_5', to: '/investments/adjustments' },
          { label: 'menu.item4_1_6', to: '/investments/reports' },
          { label: 'menu.item4_1_7', to: '/investments/funds' },
          { label: 'menu.item4_1_8', to: '/investments/securities' },
          { label: 'menu.item4_1_9', to: '/investments/performance' },
          { label: 'menu.item4_1_10', to: '/investments/waterfall' },
          { label: 'menu.item4_1_11', to: '/investments/investors' },
          { label: 'menu.item4_1_12', to: '/investments/real-estate' },
          { label: 'menu.item4_1_13', to: '/investments/infrastructure' },
          { label: 'menu.item4_1_14', to: '/investments/private-credit' },
        ],
      },
    ],
  },

  // ═══════════ 五、合同管理系统 ═══════════
  {
    icon: 'pi pi-file',
    title: 'menu.section5_title',
    shortTitle: 'menu.section5_short',
    roles: ['admin_staff', 'accountant', 'super_admin'],
    module: 'contracts',
    items: [
      { label: 'menu.item5_1', to: '/contracts/supplier', icon: 'pi pi-truck' },
      { label: 'menu.item5_2', to: '/contracts/customer', icon: 'pi pi-users' },
      { label: 'menu.item5_3', to: '/contracts/labor', icon: 'pi pi-id-card' },
      { label: 'menu.item5_4', to: '/contracts/lease', icon: 'pi pi-home' },
      { label: 'menu.item5_5', to: '/contracts/query', icon: 'pi pi-search' },
    ],
  },

  // ═══════════ 六、固定资产管理 ═══════════
  {
    icon: 'pi pi-box',
    title: 'menu.section6_title',
    shortTitle: 'menu.section6_short',
    roles: ['accountant', 'finance_manager', 'super_admin'],
    module: 'assets',
    items: [
      { label: 'menu.item6_1', to: '/fixed-assets/register', icon: 'pi pi-list' },
      { label: 'menu.item6_2', to: '/fixed-assets/depreciation', icon: 'pi pi-sort-amount-down' },
      { label: 'menu.item6_3', to: '/fixed-assets/inventory-check', icon: 'pi pi-check-square' },
      { label: 'menu.item6_4', to: '/fixed-assets/disposal', icon: 'pi pi-trash' },
      { label: 'menu.item6_5', to: '/fixed-assets/reports', icon: 'pi pi-chart-bar' },
    ],
  },

  // ═══════════ 七、进销存管理 ═══════════
  {
    icon: 'pi pi-shopping-cart',
    title: 'menu.section7_title',
    shortTitle: 'menu.section7_short',
    roles: ['accountant', 'admin_staff', 'super_admin'],
    module: 'inventory',
    items: [
      { label: 'menu.item7_1', to: '/inventory-trade/purchases', icon: 'pi pi-cart-plus' },
      { label: 'menu.item7_2', to: '/inventory-trade/sales', icon: 'pi pi-cart-arrow-down' },
      { label: 'menu.item7_3', to: '/inventory-trade/stock', icon: 'pi pi-box' },
      { label: 'menu.item7_4', to: '/inventory-trade/costing', icon: 'pi pi-calculator' },
      { label: 'menu.item7_5', to: '/inventory-trade/reports', icon: 'pi pi-chart-bar' },
    ],
  },

  // ═══════════ 八、应收账款管理 ═══════════
  {
    icon: 'pi pi-money-bill',
    title: 'menu.section8_title',
    shortTitle: 'menu.section8_short',
    roles: ['accountant', 'finance_manager', 'finance_director', 'super_admin'],
    module: 'receivables',
    items: [
      { label: 'menu.item8_1', to: '/receivables/customers', icon: 'pi pi-users' },
      { label: 'menu.item8_2', to: '/receivables/invoices', icon: 'pi pi-file' },
      { label: 'menu.item8_3', to: '/receivables/payments', icon: 'pi pi-credit-card' },
      { label: 'menu.item8_4', to: '/receivables/aging', icon: 'pi pi-clock' },
      { label: 'menu.item8_5', to: '/receivables/bad-debts', icon: 'pi pi-exclamation-triangle' },
    ],
  },

  // ═══════════ 九、应付账款管理 ═══════════
  {
    icon: 'pi pi-credit-card',
    title: 'menu.section9_title',
    shortTitle: 'menu.section9_short',
    roles: ['accountant', 'finance_manager', 'finance_director', 'super_admin'],
    module: 'payables',
    items: [
      { label: 'menu.item9_1', to: '/payables/suppliers', icon: 'pi pi-truck' },
      { label: 'menu.item9_2', to: '/payables/invoices', icon: 'pi pi-file' },
      { label: 'menu.item9_3', to: '/payables/payments', icon: 'pi pi-wallet' },
      { label: 'menu.item9_4', to: '/payables/aging', icon: 'pi pi-clock' },
      { label: 'menu.item9_5', to: '/payables/schedule', icon: 'pi pi-calendar' },
    ],
  },

  // ═══════════ 十、费用报销管理 ═══════════
  {
    icon: 'pi pi-receipt',
    title: 'menu.section10_title',
    shortTitle: 'menu.section10_short',
    roles: ['cashier', 'accountant', 'finance_manager', 'finance_director', 'super_admin', 'department_head'],
    module: 'expenses',
    items: [
      { label: 'menu.item10_1', to: '/expenses/report-form', icon: 'pi pi-pencil' },
      { label: 'menu.item10_2', to: '/expenses/report-list', icon: 'pi pi-list' },
      { label: 'menu.item10_3', to: '/expenses/loans', icon: 'pi pi-wallet' },
      { label: 'menu.item10_4', to: '/expenses/items', icon: 'pi pi-tags' },
      { label: 'menu.item10_5', to: '/expenses/policies', icon: 'pi pi-sliders-h' },
      { label: 'menu.item10_6', to: '/expenses/reports', icon: 'pi pi-chart-bar' },
    ],
  },

  // ═══════════ 十一、会计管理系统 ═══════════
  {
    icon: 'pi pi-book',
    title: 'menu.section11_title',
    shortTitle: 'menu.section11_short',
    roles: ['accountant', 'finance_manager', 'finance_director', 'super_admin'],
    module: 'accounting',
    items: [
      {
        label: 'menu.item11_0',
        to: '/cockpit/accounting',
        icon: 'pi pi-desktop',
        roles: ['accountant', 'finance_manager', 'finance_director', 'super_admin'],
        lockedMessage: 'menu.lockedAccountingCockpit',
      },
      {
        label: 'menu.item11_1',
        icon: 'pi pi-cog',
        children: [
          { label: 'menu.item11_1_1', to: '/settings/basic' },
          { label: 'menu.item11_1_2', to: '/accounts' },
          { label: 'menu.item11_1_3', to: '/settings/voucher-types' },
          { label: 'menu.item11_1_4', to: '/settings/common-vouchers' },
          { label: 'menu.item11_1_5', to: '/settings/common-summaries' },
          { label: 'menu.item11_1_6', to: '/settings/cash-flow-items' },
          { label: 'menu.item11_1_7', to: '/settings/payment' },
          { label: 'menu.item11_1_8', to: '/departments' },
          { label: 'menu.item11_1_9', to: '/settings/options' },
        ],
      },
      {
        label: 'menu.item11_2',
        icon: 'pi pi-file-edit',
        children: [
          { label: 'menu.item11_2_1', to: '/vouchers' },
          { label: 'menu.item11_2_2', to: '/gl/auto-transfer' },
          { label: 'menu.item11_2_3', to: '/gl/subject-ledger' },
          { label: 'menu.item11_2_4', to: '/gl/aux-ledger' },
          { label: 'menu.item11_2_5', to: '/gl/custom-ledger' },
          { label: 'menu.item11_2_6', to: '/gl/custom-detail' },
          { label: 'menu.item11_2_7', to: '/gl/transactions' },
          { label: 'menu.item11_2_8', to: '/reports' },
          { label: 'menu.item11_2_9', to: '/print' },
          { label: 'menu.item11_2_10', to: '/init' },
        ],
      },
      {
        label: 'menu.item11_3',
        icon: 'pi pi-calculator',
        children: [
          { label: 'menu.item11_3_1', to: '/tax/customers' },
          { label: 'menu.item11_3_2', to: '/tax/invoice/sales' },
          { label: 'menu.item11_3_3', to: '/tax/invoice/purchase' },
          { label: 'menu.item11_3_4', to: '/tax/invoice/query' },
          { label: 'menu.item11_3_5', to: '/tax/vat' },
          { label: 'menu.item11_3_6', to: '/tax/surcharge/urban' },
          { label: 'menu.item11_3_7', to: '/tax/surcharge/education' },
          { label: 'menu.item11_3_8', to: '/tax/surcharge/local-edu' },
          { label: 'menu.item11_3_9', to: '/tax/corporate-income' },
          { label: 'menu.item11_3_10', to: '/tax/iit' },
          { label: 'menu.item11_3_11', to: '/tax/stamp-duty' },
          { label: 'menu.item11_3_12', to: '/tax/property-tax' },
          { label: 'menu.item11_3_13', to: '/tax/land-use-tax' },
          { label: 'menu.item11_3_14', to: '/tax/vehicle-tax' },
          { label: 'menu.item11_3_15', to: '/tax/land-vat' },
          { label: 'menu.item11_3_16', to: '/tax/penalty' },
          { label: 'menu.item11_3_17', to: '/tax/reports/vat' },
          { label: 'menu.item11_3_18', to: '/tax/reports/cit' },
          { label: 'menu.item11_3_19', to: '/tax/reports/other' },
        ],
      },
      {
        label: 'menu.item11_4',
        icon: 'pi pi-chart-bar',
        children: [
          { label: 'menu.item11_4_1', to: '/reports/monthly' },
          { label: 'menu.item11_4_2', to: '/reports/quarterly' },
          { label: 'menu.item11_4_3', to: '/reports/yearly' },
          { label: 'menu.item11_4_4', to: '/audit' },
        ],
      },
      { label: 'menu.item11_5', to: '/todo', icon: 'pi pi-inbox' },
      {
        label: 'menu.item11_6',
        icon: 'pi pi-wrench',
        children: [
          { label: 'menu.item11_6_1', to: '/users' },
          { label: 'menu.item11_6_2', to: '/servers', icon: 'pi pi-server' },
          { label: 'menu.item11_6_3', to: '/settings' },
          { label: 'menu.item11_6_4', to: '/system/data-export' },
          { label: 'menu.item11_6_5', to: '/system/monthly-backup' },
          { label: 'menu.item11_6_6', to: '/system/yearly-backup' },
          { label: 'menu.item11_6_7', to: '/period/monthly-close' },
        ],
      },
    ],
  },

  // ═══════════ 十二、财务管理系统 ═══════════
  {
    icon: 'pi pi-chart-line',
    title: 'menu.section12_title',
    shortTitle: 'menu.section12_short',
    roles: ['finance_manager', 'finance_director', 'super_admin'],
    module: 'finance',
    items: [
      {
        label: 'menu.item12_0',
        to: '/cockpit/finance',
        icon: 'pi pi-desktop',
        roles: ['finance_manager', 'finance_director', 'super_admin'],
        lockedMessage: 'menu.lockedFinanceCockpit',
      },
      { label: 'menu.item12_1', to: '/cockpit/budget', icon: 'pi pi-chart-line' },
      { label: 'menu.item12_2', to: '/cockpit/cashflow', icon: 'pi pi-money-bill' },
      { label: 'menu.item12_3', to: '/cockpit/indicators', icon: 'pi pi-chart-bar' },
    ],
  },

  // ═══════════ 十三、董事办工作 ═══════════
  {
    icon: 'pi pi-briefcase',
    title: 'menu.section13_title',
    shortTitle: 'menu.section13_short',
    roles: ['finance_director', 'super_admin'],
    module: 'board',
    items: [
      { label: 'menu.item13_0', to: '/board/cockpit', icon: 'pi pi-desktop' },
      { label: 'menu.item13_1', to: '/board/policy', icon: 'pi pi-file' },
      {
        label: 'menu.item13_2',
        icon: 'pi pi-sitemap',
        children: [
          { label: 'menu.item13_2_1', to: '/board/committees/nomination' },
          { label: 'menu.item13_2_2', to: '/board/committees/compensation' },
          { label: 'menu.item13_2_3', to: '/board/committees/strategy' },
          { label: 'menu.item13_2_4', to: '/board/committees/audit' },
        ],
      },
      { label: 'menu.item13_3', to: '/board/policy', icon: 'pi pi-user' },
      { label: 'menu.item13_4', to: '/board/filings', icon: 'pi pi-globe' },
      { label: 'menu.item13_5', to: '/board/approvals', icon: 'pi pi-send' },
      { label: 'menu.item13_6', to: '/board/meetings', icon: 'pi pi-calendar' },
      { label: 'menu.item13_7', to: '/board/shareholders', icon: 'pi pi-users' },
      { label: 'menu.item13_8', to: '/board/filings', icon: 'pi pi-comments' },
      { label: 'menu.item13_9', to: '/board/archives', icon: 'pi pi-folder' },
      { label: 'menu.item13_10', to: '/board/contacts', icon: 'pi pi-phone' },
    ],
  },

  // ═══════════ 内容导航 ═══════════
  {
    icon: 'pi pi-bookmark',
    title: 'menu.sectionNav_title',
    shortTitle: 'menu.sectionNav_short',
    items: [{ label: '', to: '/knowledge-base', icon: 'pi pi-book' }],
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
