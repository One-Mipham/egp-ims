export interface MenuChild {
  label: string
  to: string
  icon?: string
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
  shortTitle: string
  roles?: string[] // 哪些角色可见此模块
  module?: string // 关联的模块标识（用于订阅检查）
  items: MenuItem[]
}

export const menuSections: MenuSection[] = [
  // ═══════════ 一、人力资源管理系统 ═══════════
  {
    icon: 'pi pi-users',
    title: '一、人力资源管理系统',
    shortTitle: '人力资源',
    roles: ['hr_manager', 'super_admin'],
    module: 'hr',
    items: [
      { label: '1.0 人力资源管理制度', to: '/hr/policy', icon: 'pi pi-file' },
      { label: '1.1 员工入职', to: '/hr/onboarding', icon: 'pi pi-user-plus' },
      { label: '1.2 员工培训', to: '/hr/training', icon: 'pi pi-book' },
      { label: '1.3 员工考核', to: '/hr/evaluation', icon: 'pi pi-star' },
      { label: '1.4 薪酬管理', to: '/hr/compensation', icon: 'pi pi-dollar' },
      { label: '1.5 员工奖惩', to: '/hr/rewards', icon: 'pi pi-thumbs-up' },
      { label: '1.6 员工离职', to: '/hr/offboarding', icon: 'pi pi-sign-out' },
      { label: '1.7 人力资源预算管理', to: '/hr/budget', icon: 'pi pi-chart-bar' },
    ],
  },

  // ═══════════ 二、行政综合管理系统 ═══════════
  {
    icon: 'pi pi-building',
    title: '二、行政综合管理系统',
    shortTitle: '行政综合',
    roles: ['admin_staff', 'hr_manager', 'super_admin'],
    module: 'admin',
    items: [
      { label: '2.1 文件管理', to: '/admin/documents', icon: 'pi pi-file' },
      {
        label: '2.2 车辆管理',
        icon: 'pi pi-car',
        children: [
          { label: '车辆采购审批', to: '/admin/vehicles/purchases' },
          { label: '车辆档案管理', to: '/admin/vehicles/registry' },
          { label: '维修保养审批', to: '/admin/vehicles/maintenance' },
          { label: '供应商管理', to: '/admin/vehicles/suppliers' },
        ],
      },
      { label: '2.3 财产保险', to: '/admin/insurance', icon: 'pi pi-shield' },
      { label: '2.4 门禁管理', to: '/admin/access', icon: 'pi pi-lock' },
      {
        label: '2.5 资产管理',
        icon: 'pi pi-box',
        children: [
          { label: '实物资产台账', to: '/admin/stock/assets' },
          { label: '资产采购审批', to: '/admin/stock/assets/purchases' },
          { label: '资产领用审批', to: '/admin/stock/assets/requisitions' },
          { label: '入库管理', to: '/admin/stock/assets/inbound' },
          { label: '出库管理', to: '/admin/stock/assets/outbound' },
          { label: '盘库管理', to: '/admin/stock/assets/counts' },
          { label: '礼品管理', to: '/admin/stock/gifts' },
          { label: '礼品采购审批', to: '/admin/stock/gifts/purchases' },
          { label: '礼品领用审批', to: '/admin/stock/gifts/requisitions' },
          { label: '礼品入库管理', to: '/admin/stock/gifts/inbound' },
          { label: '礼品出库管理', to: '/admin/stock/gifts/outbound' },
        ],
      },
    ],
  },

  // ═══════════ 三、招投标管理 ═══════════
  {
    icon: 'pi pi-gavel',
    title: '三、招投标管理',
    shortTitle: '招投标',
    roles: ['admin_staff', 'super_admin'],
    module: 'bids',
    items: [
      {
        label: '招标管理',
        icon: 'pi pi-file-edit',
        children: [
          { label: '3.1.1 招标立项', to: '/bids/tendering/projects' },
          { label: '3.1.2 招标文件', to: '/bids/tendering/documents' },
          { label: '3.1.3 开标管理', to: '/bids/tendering/openings' },
          { label: '3.1.4 评标管理', to: '/bids/tendering/evaluations' },
          { label: '3.1.5 定标管理', to: '/bids/tendering/awards' },
          { label: '3.1.6 例外事项', to: '/bids/tendering/exceptions' },
        ],
      },
      {
        label: '投标管理',
        icon: 'pi pi-briefcase',
        children: [
          { label: '3.2.1 投标登记', to: '/bids/bidding/registrations' },
          { label: '3.2.2 投标文件', to: '/bids/bidding/documents' },
          { label: '3.2.3 投标报价', to: '/bids/bidding/pricing' },
          { label: '3.2.4 投标保证金', to: '/bids/bidding/bonds' },
          { label: '3.2.5 例外事项', to: '/bids/bidding/exceptions' },
        ],
      },
    ],
  },

  // ═══════════ 四、投资管理系统 ═══════════
  {
    icon: 'pi pi-chart-bar',
    title: '四、投资管理系统',
    shortTitle: '投资管理',
    roles: ['finance_manager', 'finance_director', 'super_admin'],
    module: 'investments',
    items: [
      {
        label: '4.0 投资仪表盘',
        icon: 'pi pi-chart-line',
        to: '/investments/dashboard',
      },
      {
        label: '4.1 投资组合总览',
        icon: 'pi pi-folder',
        children: [
          { label: '投资组合总览', to: '/investments/portfolio' },
          { label: '投资持仓', to: '/investments/positions' },
          { label: '投资交易', to: '/investments/transactions' },
          { label: '投资收益', to: '/investments/income' },
          { label: '公允价值调整', to: '/investments/adjustments' },
          { label: '投资报表', to: '/investments/reports' },
          { label: '基金管理', to: '/investments/funds' },
          { label: '证券主数据', to: '/investments/securities' },
          { label: '绩效分析', to: '/investments/performance' },
          { label: '分配瀑布', to: '/investments/waterfall' },
          { label: 'LP投资人', to: '/investments/investors' },
          { label: '房地产资产', to: '/investments/real-estate' },
          { label: '基础设施资产', to: '/investments/infrastructure' },
          { label: '私募信贷资产', to: '/investments/private-credit' },
        ],
      },
    ],
  },

  // ═══════════ 五、合同管理系统 ═══════════
  {
    icon: 'pi pi-file',
    title: '五、合同管理系统',
    shortTitle: '合同管理',
    roles: ['admin_staff', 'accountant', 'super_admin'],
    module: 'contracts',
    items: [
      { label: '5.1 供应商合同', to: '/contracts/supplier', icon: 'pi pi-truck' },
      { label: '5.2 客户合同', to: '/contracts/customer', icon: 'pi pi-users' },
      { label: '5.3 劳动合同', to: '/contracts/labor', icon: 'pi pi-id-card' },
      { label: '5.4 租赁合同', to: '/contracts/lease', icon: 'pi pi-home' },
      { label: '5.5 合同查询统计', to: '/contracts/query', icon: 'pi pi-search' },
    ],
  },

  // ═══════════ 六、固定资产管理 ═══════════
  {
    icon: 'pi pi-box',
    title: '六、固定资产管理',
    shortTitle: '固定资产',
    roles: ['accountant', 'finance_manager', 'super_admin'],
    module: 'assets',
    items: [
      { label: '6.1 资产台账', to: '/fixed-assets/register', icon: 'pi pi-list' },
      { label: '6.2 折旧管理', to: '/fixed-assets/depreciation', icon: 'pi pi-sort-amount-down' },
      { label: '6.3 资产盘点', to: '/fixed-assets/inventory-check', icon: 'pi pi-check-square' },
      { label: '6.4 资产处置', to: '/fixed-assets/disposal', icon: 'pi pi-trash' },
      { label: '6.5 资产报表', to: '/fixed-assets/reports', icon: 'pi pi-chart-bar' },
    ],
  },

  // ═══════════ 七、进销存管理 ═══════════
  {
    icon: 'pi pi-shopping-cart',
    title: '七、进销存管理',
    shortTitle: '进销存',
    roles: ['accountant', 'admin_staff', 'super_admin'],
    module: 'inventory',
    items: [
      { label: '7.1 采购管理', to: '/inventory-trade/purchases', icon: 'pi pi-cart-plus' },
      { label: '7.2 销售管理', to: '/inventory-trade/sales', icon: 'pi pi-cart-arrow-down' },
      { label: '7.3 库存管理', to: '/inventory-trade/stock', icon: 'pi pi-box' },
      { label: '7.4 成本核算', to: '/inventory-trade/costing', icon: 'pi pi-calculator' },
      { label: '7.5 库存报表', to: '/inventory-trade/reports', icon: 'pi pi-chart-bar' },
    ],
  },

  // ═══════════ 八、应收账款管理 ═══════════
  {
    icon: 'pi pi-money-bill',
    title: '八、应收账款管理',
    shortTitle: '应收账款',
    roles: ['accountant', 'finance_manager', 'finance_director', 'super_admin'],
    module: 'receivables',
    items: [
      { label: '8.1 客户信息', to: '/receivables/customers', icon: 'pi pi-users' },
      { label: '8.2 应收发票', to: '/receivables/invoices', icon: 'pi pi-file' },
      { label: '8.3 收款管理', to: '/receivables/payments', icon: 'pi pi-credit-card' },
      { label: '8.4 账龄分析', to: '/receivables/aging', icon: 'pi pi-clock' },
      { label: '8.5 坏账管理', to: '/receivables/bad-debts', icon: 'pi pi-exclamation-triangle' },
    ],
  },

  // ═══════════ 九、应付账款管理 ═══════════
  {
    icon: 'pi pi-credit-card',
    title: '九、应付账款管理',
    shortTitle: '应付账款',
    roles: ['accountant', 'finance_manager', 'finance_director', 'super_admin'],
    module: 'payables',
    items: [
      { label: '9.1 供应商信息', to: '/payables/suppliers', icon: 'pi pi-truck' },
      { label: '9.2 应付发票', to: '/payables/invoices', icon: 'pi pi-file' },
      { label: '9.3 付款管理', to: '/payables/payments', icon: 'pi pi-wallet' },
      { label: '9.4 账龄分析', to: '/payables/aging', icon: 'pi pi-clock' },
      { label: '9.5 付款计划', to: '/payables/schedule', icon: 'pi pi-calendar' },
    ],
  },

  // ═══════════ 十、费用报销管理 ═══════════
  {
    icon: 'pi pi-receipt',
    title: '十、费用报销管理',
    shortTitle: '费用报销',
    roles: ['cashier', 'accountant', 'finance_manager', 'finance_director', 'super_admin', 'department_head'],
    module: 'expenses',
    items: [
      { label: '10.1 报销申请', to: '/expenses/report-form', icon: 'pi pi-pencil' },
      { label: '10.2 报销列表', to: '/expenses/report-list', icon: 'pi pi-list' },
      { label: '10.3 借款管理', to: '/expenses/loans', icon: 'pi pi-wallet' },
      { label: '10.4 费用项目', to: '/expenses/items', icon: 'pi pi-tags' },
      { label: '10.5 费用标准', to: '/expenses/policies', icon: 'pi pi-sliders-h' },
      { label: '10.6 查询统计', to: '/expenses/reports', icon: 'pi pi-chart-bar' },
    ],
  },

  // ═══════════ 十一、会计管理系统 ═══════════
  {
    icon: 'pi pi-book',
    title: '十一、会计管理系统',
    shortTitle: '会计管理',
    roles: ['accountant', 'finance_manager', 'finance_director', 'super_admin'],
    module: 'accounting',
    items: [
      {
        label: '11.0 会计管理驾驶舱',
        to: '/cockpit/accounting',
        icon: 'pi pi-desktop',
        roles: ['accountant', 'finance_manager', 'finance_director', 'super_admin'],
        lockedMessage: '您无权访问会计管理驾驶舱。需要：会计、财务经理、财务总监或系统管理员权限。',
      },
      {
        label: '11.1 基础设置',
        icon: 'pi pi-cog',
        children: [
          { label: '公司信息', to: '/settings/basic' },
          { label: '科目', to: '/accounts' },
          { label: '凭证类别', to: '/settings/voucher-types' },
          { label: '常用凭证', to: '/settings/common-vouchers' },
          { label: '常用摘要', to: '/settings/common-summaries' },
          { label: '现金流量项目', to: '/settings/cash-flow-items' },
          { label: '收付信息', to: '/settings/payment' },
          { label: '部门管理', to: '/departments' },
          { label: '选项设置', to: '/settings/options' },
        ],
      },
      {
        label: '11.2 总账',
        icon: 'pi pi-file-edit',
        children: [
          { label: '凭证', to: '/vouchers' },
          { label: '自动转账', to: '/gl/auto-transfer' },
          { label: '科目账', to: '/gl/subject-ledger' },
          { label: '辅助账', to: '/gl/aux-ledger' },
          { label: '自定义账', to: '/gl/custom-ledger' },
          { label: '自定义明细表', to: '/gl/custom-detail' },
          { label: '往来管理', to: '/gl/transactions' },
          { label: '现金流量', to: '/reports' },
          { label: '账簿打印', to: '/print' },
          { label: '初始化导航', to: '/init' },
        ],
      },
      {
        label: '11.3 税务管理',
        icon: 'pi pi-calculator',
        children: [
          { label: '客户信息维护', to: '/tax/customers' },
          { label: '销项发票', to: '/tax/invoice/sales' },
          { label: '进项发票', to: '/tax/invoice/purchase' },
          { label: '发票查询统计', to: '/tax/invoice/query' },
          { label: '增值税管理', to: '/tax/vat' },
          { label: '城市维护建设税', to: '/tax/surcharge/urban' },
          { label: '教育费附加', to: '/tax/surcharge/education' },
          { label: '地方教育附加', to: '/tax/surcharge/local-edu' },
          { label: '企业所得税', to: '/tax/corporate-income' },
          { label: '个人所得税代扣代缴', to: '/tax/iit' },
          { label: '印花税', to: '/tax/stamp-duty' },
          { label: '房产税', to: '/tax/property-tax' },
          { label: '土地使用税', to: '/tax/land-use-tax' },
          { label: '车船税', to: '/tax/vehicle-tax' },
          { label: '土地增值税', to: '/tax/land-vat' },
          { label: '罚款与滞纳金', to: '/tax/penalty' },
          { label: '增值税申报表', to: '/tax/reports/vat' },
          { label: '所得税申报表', to: '/tax/reports/cit' },
          { label: '其他税种申报汇总', to: '/tax/reports/other' },
        ],
      },
      {
        label: '11.4 报表中心',
        icon: 'pi pi-chart-bar',
        children: [
          { label: '财务报表', to: '/reports' },
          { label: '月度报表', to: '/reports/monthly' },
          { label: '季度报表', to: '/reports/quarterly' },
          { label: '年度报表', to: '/reports/yearly' },
          { label: '审计日志', to: '/audit' },
        ],
      },
      { label: '11.5 协同办公', to: '/todo', icon: 'pi pi-inbox' },
      {
        label: '11.6 系统设置',
        icon: 'pi pi-wrench',
        children: [
          { label: '用户管理', to: '/users' },
          { label: '服务器管理', to: '/servers', icon: 'pi pi-server' },
          { label: '系统设置', to: '/settings' },
          { label: '数据导出', to: '/system/data-export' },
          { label: '月度数据备份', to: '/system/monthly-backup' },
          { label: '年度数据备份', to: '/system/yearly-backup' },
          { label: '期末处理', to: '/period/monthly-close' },
        ],
      },
    ],
  },

  // ═══════════ 十二、财务管理系统 ═══════════
  {
    icon: 'pi pi-chart-line',
    title: '十二、财务管理系统',
    shortTitle: '财务管理',
    roles: ['finance_manager', 'finance_director', 'super_admin'],
    module: 'finance',
    items: [
      {
        label: '12.0 财务管理驾驶舱',
        to: '/cockpit/finance',
        icon: 'pi pi-desktop',
        roles: ['finance_manager', 'finance_director', 'super_admin'],
        lockedMessage: '您无权访问财务管理驾驶舱。需要：财务经理、财务总监或系统管理员权限。',
      },
      { label: '12.1 预算管理与绩效评价', to: '/cockpit/budget', icon: 'pi pi-chart-line' },
      { label: '12.2 现金流计划与融资计划', to: '/cockpit/cashflow', icon: 'pi pi-money-bill' },
      { label: '12.3 经营分析指标', to: '/cockpit/indicators', icon: 'pi pi-chart-bar' },
    ],
  },

  // ═══════════ 十三、董事办工作 ═══════════
  {
    icon: 'pi pi-briefcase',
    title: '十三、董事办工作',
    shortTitle: '董事办',
    roles: ['finance_director', 'super_admin'],
    module: 'board',
    items: [
      { label: '13.0 董事办驾驶舱', to: '/board/cockpit', icon: 'pi pi-desktop' },
      { label: '13.1 董事会工作条例', to: '/board/policy', icon: 'pi pi-file' },
      {
        label: '13.2 董事会专业委员会',
        icon: 'pi pi-sitemap',
        children: [
          { label: '提名委员会', to: '/board/committees/nomination' },
          { label: '薪酬与绩效考核委员会', to: '/board/committees/compensation' },
          { label: '战略发展委员会', to: '/board/committees/strategy' },
          { label: '审计与稽核委员会', to: '/board/committees/audit' },
        ],
      },
      { label: '13.3 董秘工作职责', to: '/board/policy', icon: 'pi pi-user' },
      { label: '13.4 合规报送管理', to: '/board/filings', icon: 'pi pi-globe' },
      { label: '13.5 内部报批流程', to: '/board/approvals', icon: 'pi pi-send' },
      { label: '13.6 三会决议管理', to: '/board/meetings', icon: 'pi pi-calendar' },
      { label: '13.7 股东名册', to: '/board/shareholders', icon: 'pi pi-users' },
      { label: '13.8 投资者关系', to: '/board/filings', icon: 'pi pi-comments' },
      { label: '13.9 档案管理', to: '/board/archives', icon: 'pi pi-folder' },
      { label: '13.10 对接联络日志', to: '/board/contacts', icon: 'pi pi-phone' },
    ],
  },

  // ═══════════ 内容导航 ═══════════
  {
    icon: 'pi pi-bookmark',
    title: '内容导航',
    shortTitle: '知识库',
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
