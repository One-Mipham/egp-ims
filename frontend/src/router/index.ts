import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/login', component: () => import('../views/Login.vue') },
  { path: '/register', component: () => import('../views/Register.vue') },
  { path: '', component: () => import('../views/Dashboard.vue'), meta: { requiresAuth: true } },
  { path: '/accounts', component: () => import('../views/Accounts.vue'), meta: { requiresAuth: true } },
  { path: '/vouchers', component: () => import('../views/Vouchers.vue'), meta: { requiresAuth: true } },
  // 总账模块
  { path: '/gl/journal', redirect: '/vouchers' },
  { path: '/gl/journal-reverse', redirect: '/vouchers' },
  { path: '/gl/voucher-review', redirect: '/vouchers' },
  {
    path: '/gl/auto-transfer',
    component: () => import('../views/gl/AutoTransfer.vue'),
    meta: { requiresAuth: true, pageTitle: '自动转账' },
  },
  {
    path: '/gl/subject-ledger',
    component: () => import('../views/gl/SubjectLedger.vue'),
    meta: { requiresAuth: true, pageTitle: '科目账' },
  },
  {
    path: '/gl/aux-ledger',
    component: () => import('../views/gl/AuxLedger.vue'),
    meta: { requiresAuth: true, pageTitle: '辅助账' },
  },
  {
    path: '/gl/custom-ledger',
    component: () => import('../views/gl/CustomLedger.vue'),
    meta: { requiresAuth: true, pageTitle: '自定义账' },
  },
  {
    path: '/gl/custom-detail',
    component: () => import('../views/gl/CustomDetail.vue'),
    meta: { requiresAuth: true, pageTitle: '自定义明细表' },
  },
  {
    path: '/gl/transactions',
    component: () => import('../views/gl/Transactions.vue'),
    meta: { requiresAuth: true, pageTitle: '往来管理' },
  },
  { path: '/gl/cashflow', redirect: '/reports/monthly' },
  { path: '/gl/print-books', redirect: '/print/company' },
  { path: '/print', redirect: '/print/company' },
  { path: '/departments', component: () => import('../views/Departments.vue'), meta: { requiresAuth: true } },
  { path: '/periods', component: () => import('../views/Periods.vue'), meta: { requiresAuth: true } },
  { path: '/reports', redirect: '/reports/monthly' },
  { path: '/audit', component: () => import('../views/AuditLog.vue'), meta: { requiresAuth: true } },
  { path: '/users', component: () => import('../views/Users.vue'), meta: { requiresAuth: true } },
  // Settings pages
  { path: '/settings', component: () => import('../views/Settings.vue'), meta: { requiresAuth: true } },
  { path: '/settings/basic', component: () => import('../views/BasicSettings.vue'), meta: { requiresAuth: true } },
  { path: '/settings/payment', component: () => import('../views/PaymentSettings.vue'), meta: { requiresAuth: true } },
  {
    path: '/settings/voucher-types',
    component: () => import('../views/VoucherTypeSettings.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/settings/common-vouchers',
    component: () => import('../views/CommonVouchers.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/settings/common-summaries',
    component: () => import('../views/CommonSummaries.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/settings/cash-flow-items',
    component: () => import('../views/CashFlowItems.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/settings/options',
    component: () => import('../views/OptionsSettings.vue'),
    meta: { requiresAuth: true },
  },
  { path: '/servers', component: () => import('../views/Servers.vue'), meta: { requiresAuth: true } },
  // 初始化导航
  { path: '/init', component: () => import('../views/InitNavigation.vue'), meta: { requiresAuth: true } },
  {
    path: '/permissions',
    component: () => import('../views/Permissions.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/init/opening-balances',
    component: () => import('../views/OpeningBalances.vue'),
    meta: { requiresAuth: true },
  },
  // 初始化 → 基础档案 children
  { path: '/init/contracts', component: () => import('../views/InitContracts.vue'), meta: { requiresAuth: true } },
  { path: '/init/invoices', component: () => import('../views/InitInvoices.vue'), meta: { requiresAuth: true } },
  {
    path: '/init/voucher-archive',
    component: () => import('../views/VoucherArchive.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/init/monthly-reports',
    redirect: '/reports/monthly',
  },
  {
    path: '/init/annual-audit',
    component: () => import('../views/AnnualAudit.vue'),
    meta: { requiresAuth: true, pageTitle: '年度审计报告' },
  },
  // 报表中心 — 三期报表
  {
    path: '/reports/monthly',
    component: () => import('../views/PrintPeriodic.vue'),
    meta: { requiresAuth: true, pageTitle: '月度报表' },
  },
  {
    path: '/reports/quarterly',
    component: () => import('../views/PrintPeriodic.vue'),
    meta: { requiresAuth: true, pageTitle: '季度报表' },
  },
  {
    path: '/reports/yearly',
    component: () => import('../views/PrintPeriodic.vue'),
    meta: { requiresAuth: true, pageTitle: '年度报表' },
  },
  // 期末处理
  {
    path: '/period/monthly-close',
    component: () => import('../views/MonthlyClose.vue'),
    meta: { requiresAuth: true, pageTitle: '月度结账' },
  },
  {
    path: '/period/quarterly-close',
    component: () => import('../views/QuarterlyClose.vue'),
    meta: { requiresAuth: true, pageTitle: '季度结账' },
  },
  {
    path: '/period/yearly-close',
    component: () => import('../views/YearlyClose.vue'),
    meta: { requiresAuth: true, pageTitle: '年度结账' },
  },
  {
    path: '/period/carry-forward',
    component: () => import('../views/CarryForward.vue'),
    meta: { requiresAuth: true, pageTitle: '期末结转' },
  },
  // 系统管理 — 数据管理
  {
    path: '/system/data-export',
    component: () => import('../views/system/DataExport.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/system/monthly-backup',
    component: () => import('../views/system/MonthlyBackup.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/system/yearly-backup',
    component: () => import('../views/system/YearlyBackup.vue'),
    meta: { requiresAuth: true },
  },
  // 税务管理
  {
    path: '/tax/customers',
    component: () => import('../views/TaxCustomers.vue'),
    meta: { requiresAuth: true, pageTitle: '客户信息维护' },
  },
  // 发票管理 — single component, 3 modes
  {
    path: '/tax/invoice/sales',
    component: () => import('../views/TaxInvoiceList.vue'),
    meta: { requiresAuth: true, pageTitle: '销项发票' },
  },
  {
    path: '/tax/invoice/purchase',
    component: () => import('../views/TaxInvoiceList.vue'),
    meta: { requiresAuth: true, pageTitle: '进项发票' },
  },
  {
    path: '/tax/invoice/query',
    component: () => import('../views/TaxInvoiceList.vue'),
    meta: { requiresAuth: true, pageTitle: '发票查询统计' },
  },
  // 税种管理 — single component, 12 modes
  {
    path: '/tax/vat',
    component: () => import('../views/TaxDeclarationList.vue'),
    meta: { requiresAuth: true, pageTitle: '增值税管理' },
  },
  {
    path: '/tax/surcharge/urban',
    component: () => import('../views/TaxDeclarationList.vue'),
    meta: { requiresAuth: true, pageTitle: '城市维护建设税' },
  },
  {
    path: '/tax/surcharge/education',
    component: () => import('../views/TaxDeclarationList.vue'),
    meta: { requiresAuth: true, pageTitle: '教育费附加' },
  },
  {
    path: '/tax/surcharge/local-edu',
    component: () => import('../views/TaxDeclarationList.vue'),
    meta: { requiresAuth: true, pageTitle: '地方教育附加' },
  },
  {
    path: '/tax/corporate-income',
    component: () => import('../views/TaxDeclarationList.vue'),
    meta: { requiresAuth: true, pageTitle: '企业所得税' },
  },
  {
    path: '/tax/iit',
    component: () => import('../views/TaxDeclarationList.vue'),
    meta: { requiresAuth: true, pageTitle: '个人所得税代扣代缴' },
  },
  {
    path: '/tax/stamp-duty',
    component: () => import('../views/TaxDeclarationList.vue'),
    meta: { requiresAuth: true, pageTitle: '印花税' },
  },
  {
    path: '/tax/property-tax',
    component: () => import('../views/TaxDeclarationList.vue'),
    meta: { requiresAuth: true, pageTitle: '房产税' },
  },
  {
    path: '/tax/land-use-tax',
    component: () => import('../views/TaxDeclarationList.vue'),
    meta: { requiresAuth: true, pageTitle: '土地使用税' },
  },
  {
    path: '/tax/vehicle-tax',
    component: () => import('../views/TaxDeclarationList.vue'),
    meta: { requiresAuth: true, pageTitle: '车船税' },
  },
  {
    path: '/tax/land-vat',
    component: () => import('../views/TaxDeclarationList.vue'),
    meta: { requiresAuth: true, pageTitle: '土地增值税' },
  },
  {
    path: '/tax/penalty',
    component: () => import('../views/TaxDeclarationList.vue'),
    meta: { requiresAuth: true, pageTitle: '罚款与滞纳金' },
  },
  // 申报表 — single component, 3 modes
  {
    path: '/tax/reports/vat',
    component: () => import('../views/TaxReport.vue'),
    meta: { requiresAuth: true, pageTitle: '增值税申报表' },
  },
  {
    path: '/tax/reports/cit',
    component: () => import('../views/TaxReport.vue'),
    meta: { requiresAuth: true, pageTitle: '所得税申报表' },
  },
  {
    path: '/tax/reports/other',
    component: () => import('../views/TaxReport.vue'),
    meta: { requiresAuth: true, pageTitle: '其他税种申报汇总' },
  },
  // 投资管理
  {
    path: '/investments/dashboard',
    component: () => import('../views/InvestmentDashboard.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/investments/portfolio',
    component: () => import('../views/InvestmentPortfolio.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/investments/positions',
    component: () => import('../views/InvestmentPositions.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/investments/transactions',
    component: () => import('../views/InvestmentTransactions.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/investments/income',
    component: () => import('../views/InvestmentIncome.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/investments/reports',
    component: () => import('../views/InvestmentReports.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/investments/adjustments',
    component: () => import('../views/InvestmentAdjustments.vue'),
    meta: { requiresAuth: true },
  },
  // 投资管理 — 基金与分配
  { path: '/investments/funds', component: () => import('../views/FundList.vue'), meta: { requiresAuth: true } },
  {
    path: '/investments/funds/:fundId',
    component: () => import('../views/FundDetail.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/investments/performance',
    component: () => import('../views/PerformanceAnalysis.vue'),
    meta: { requiresAuth: true },
  },
  { path: '/investments/waterfall', component: () => import('../views/Waterfall.vue'), meta: { requiresAuth: true } },
  {
    path: '/investments/securities',
    component: () => import('../views/SecuritiesMaster.vue'),
    meta: { requiresAuth: true },
  },
  // 投资管理 — LP/另类资产
  { path: '/investments/investors', component: () => import('../views/LpInvestor.vue'), meta: { requiresAuth: true } },
  {
    path: '/investments/real-estate',
    component: () => import('../views/RealEstate.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/investments/infrastructure',
    component: () => import('../views/Infrastructure.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/investments/private-credit',
    component: () => import('../views/PrivateCredit.vue'),
    meta: { requiresAuth: true },
  },
  // Placeholder routes — legacy
  {
    path: '/init/monthly-reports',
    redirect: '/reports/monthly',
  },
  {
    path: '/mobile-stock',
    redirect: '/cockpit/accounting',
  },
  {
    path: '/todo',
    component: () => import('../views/PlaceholderPage.vue'),
    meta: { requiresAuth: true, pageTitle: '协同办公' },
  },
  // HR module (placeholder)
  // HR 人力资源模块
  { path: '/hr/policy', component: () => import('../views/hr/HrPolicy.vue'), meta: { requiresAuth: true } },
  { path: '/hr/onboarding', component: () => import('../views/hr/HrOnboarding.vue'), meta: { requiresAuth: true } },
  { path: '/hr/training', component: () => import('../views/hr/HrTraining.vue'), meta: { requiresAuth: true } },
  { path: '/hr/evaluation', component: () => import('../views/hr/HrEvaluation.vue'), meta: { requiresAuth: true } },
  { path: '/hr/compensation', component: () => import('../views/hr/HrCompensation.vue'), meta: { requiresAuth: true } },
  { path: '/hr/rewards', component: () => import('../views/hr/HrRewards.vue'), meta: { requiresAuth: true } },
  { path: '/hr/offboarding', component: () => import('../views/hr/HrOffboarding.vue'), meta: { requiresAuth: true } },
  { path: '/hr/budget', component: () => import('../views/hr/HrBudget.vue'), meta: { requiresAuth: true } },
  // ═══════════ 二、合同管理系统 ═══════════
  {
    path: '/contracts/supplier',
    component: () => import('../views/contracts/ContractList.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/contracts/customer',
    component: () => import('../views/contracts/ContractList.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/contracts/labor',
    component: () => import('../views/contracts/ContractList.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/contracts/lease',
    component: () => import('../views/contracts/ContractList.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/contracts/query',
    component: () => import('../views/contracts/ContractQuery.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/contracts/print/:id',
    component: () => import('../views/contracts/ContractPrint.vue'),
    meta: { requiresAuth: true },
  },
  // ═══════════ 三、行政综合管理系统 ═══════════
  {
    path: '/admin/documents',
    component: () => import('../views/admin/AdminDocuments.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/admin/vehicles/purchases',
    component: () => import('../views/admin/VehiclePurchases.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/admin/vehicles/registry',
    component: () => import('../views/admin/VehicleRegistry.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/admin/vehicles/maintenance',
    component: () => import('../views/admin/VehicleMaintenance.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/admin/vehicles/suppliers',
    component: () => import('../views/admin/VehicleSuppliers.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/admin/insurance',
    component: () => import('../views/admin/AdminInsurance.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/admin/access',
    component: () => import('../views/PlaceholderPage.vue'),
    meta: { requiresAuth: true, pageTitle: '门禁管理' },
  },
  {
    path: '/admin/stock/assets',
    component: () => import('../views/admin/StockAssets.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/admin/stock/assets/purchases',
    component: () => import('../views/admin/StockAssetPurchases.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/admin/stock/assets/requisitions',
    component: () => import('../views/admin/StockAssetRequisitions.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/admin/stock/assets/inbound',
    component: () => import('../views/admin/StockAssetInbound.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/admin/stock/assets/outbound',
    component: () => import('../views/admin/StockAssetOutbound.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/admin/stock/assets/counts',
    component: () => import('../views/admin/StockAssetCounts.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/admin/stock/gifts',
    component: () => import('../views/admin/StockGifts.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/admin/stock/gifts/purchases',
    component: () => import('../views/admin/StockGiftPurchases.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/admin/stock/gifts/requisitions',
    component: () => import('../views/admin/StockGiftRequisitions.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/admin/stock/gifts/inbound',
    component: () => import('../views/admin/StockGiftInbound.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/admin/stock/gifts/outbound',
    component: () => import('../views/admin/StockGiftOutbound.vue'),
    meta: { requiresAuth: true },
  },
  // ═══════════ 四、固定资产管理 ═══════════
  {
    path: '/fixed-assets/register',
    component: () => import('../views/fixed_assets/FixedAssetRegister.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/fixed-assets/depreciation',
    component: () => import('../views/fixed_assets/FixedAssetDepreciation.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/fixed-assets/inventory-check',
    component: () => import('../views/fixed_assets/FixedAssetCheck.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/fixed-assets/disposal',
    component: () => import('../views/fixed_assets/FixedAssetDisposal.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/fixed-assets/reports',
    component: () => import('../views/fixed_assets/FixedAssetReports.vue'),
    meta: { requiresAuth: true },
  },
  // ═══════════ 五、应收账款管理 ═══════════
  {
    path: '/receivables/customers',
    component: () => import('../views/receivables/ReceivableCustomers.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/receivables/invoices',
    component: () => import('../views/receivables/ReceivableInvoices.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/receivables/payments',
    component: () => import('../views/receivables/ReceivablePayments.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/receivables/aging',
    component: () => import('../views/receivables/ReceivableAging.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/receivables/bad-debts',
    component: () => import('../views/receivables/ReceivableBadDebts.vue'),
    meta: { requiresAuth: true },
  },
  // ═══════════ 六、应付账款管理 ═══════════
  {
    path: '/payables/suppliers',
    component: () => import('../views/payables/PayableSuppliers.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/payables/invoices',
    component: () => import('../views/payables/PayableInvoices.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/payables/payments',
    component: () => import('../views/payables/PayablePayments.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/payables/aging',
    component: () => import('../views/payables/PayableAging.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/payables/schedule',
    component: () => import('../views/payables/PayableSchedule.vue'),
    meta: { requiresAuth: true },
  },
  // ═══════════ 七、费用报销管理 ═══════════
  {
    path: '/expenses/report-form',
    component: () => import('../views/expenses/ExpenseReportForm.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/expenses/report-form/:id',
    component: () => import('../views/expenses/ExpenseReportForm.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/expenses/report-list',
    component: () => import('../views/expenses/ExpenseReportList.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/expenses/loans',
    component: () => import('../views/expenses/ExpenseLoanList.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/expenses/items',
    component: () => import('../views/expenses/ExpenseItems.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/expenses/policies',
    component: () => import('../views/expenses/ExpensePolicies.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/expenses/reports',
    component: () => import('../views/expenses/ExpenseReports.vue'),
    meta: { requiresAuth: true },
  },
  // ═══════════ 八、进销存管理 ═══════════
  {
    path: '/inventory-trade/purchases',
    component: () => import('../views/inventory_trade/InvPurchases.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/inventory-trade/sales',
    component: () => import('../views/inventory_trade/InvSales.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/inventory-trade/stock',
    component: () => import('../views/inventory_trade/InvStock.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/inventory-trade/costing',
    component: () => import('../views/inventory_trade/InvCosting.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/inventory-trade/reports',
    component: () => import('../views/inventory_trade/InvReports.vue'),
    meta: { requiresAuth: true },
  },
  // ═══════════ 知识管理 ═══════════
  { path: '/knowledge-base', component: () => import('../views/KnowledgeBase.vue'), meta: { requiresAuth: true } },
  // ═══════════ 订阅与支付 ═══════════
  {
    path: '/subscription/plans',
    component: () => import('../views/SubscriptionPlans.vue'),
    meta: { requiresAuth: true },
  },
  { path: '/subscription/checkout', component: () => import('../views/Checkout.vue'), meta: { requiresAuth: true } },
  {
    path: '/subscription/billing',
    component: () => import('../views/BillingHistory.vue'),
    meta: { requiresAuth: true },
  },
  // ═══════════ 十三、董事办工作 ═══════════
  { path: '/board/cockpit', component: () => import('../views/board/BoardCockpit.vue'), meta: { requiresAuth: true } },
  { path: '/board/policy', component: () => import('../views/board/BoardPolicy.vue'), meta: { requiresAuth: true } },
  {
    path: '/board/committees/nomination',
    component: () => import('../views/board/BoardPolicy.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/board/committees/compensation',
    component: () => import('../views/board/BoardPolicy.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/board/committees/strategy',
    component: () => import('../views/board/BoardPolicy.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/board/committees/audit',
    component: () => import('../views/board/BoardPolicy.vue'),
    meta: { requiresAuth: true },
  },
  { path: '/board/filings', component: () => import('../views/board/BoardFiling.vue'), meta: { requiresAuth: true } },
  { path: '/board/approvals', component: () => import('../views/board/BoardFiling.vue'), meta: { requiresAuth: true } },
  { path: '/board/meetings', component: () => import('../views/board/BoardFiling.vue'), meta: { requiresAuth: true } },
  { path: '/board/archives', component: () => import('../views/board/BoardFiling.vue'), meta: { requiresAuth: true } },
  { path: '/board/contacts', component: () => import('../views/board/BoardFiling.vue'), meta: { requiresAuth: true } },
  {
    path: '/board/shareholders',
    component: () => import('../views/board/BoardShareholder.vue'),
    meta: { requiresAuth: true },
  },
  // Cockpit module
  { path: '/cockpit/budget', component: () => import('../views/BudgetCockpit.vue'), meta: { requiresAuth: true } },
  { path: '/cockpit/cashflow', component: () => import('../views/CashflowCockpit.vue'), meta: { requiresAuth: true } },
  {
    path: '/cockpit/indicators',
    component: () => import('../views/IndicatorsCockpit.vue'),
    meta: { requiresAuth: true },
  },
  // Cockpit — standalone pages with role permissions
  {
    path: '/cockpit/accounting',
    component: () => import('../views/AccountingCockpit.vue'),
    meta: { requiresAuth: true, allowedRoles: ['accountant', 'finance_manager', 'finance_director', 'super_admin'] },
  },
  {
    path: '/cockpit/finance',
    component: () => import('../views/FinanceCockpit.vue'),
    meta: { requiresAuth: true, allowedRoles: ['finance_manager', 'finance_director', 'super_admin'] },
  },
  // Print module
  { path: '/print/company', component: () => import('../views/PrintCompany.vue'), meta: { requiresAuth: true } },
  {
    path: '/print/departments',
    component: () => import('../views/PrintDepartments.vue'),
    meta: { requiresAuth: true },
  },
  { path: '/print/subjects', component: () => import('../views/PrintSubjects.vue'), meta: { requiresAuth: true } },
  {
    path: '/print/subject-balance',
    component: () => import('../views/PrintSubjectBalance.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/print/general-ledger',
    component: () => import('../views/PrintGeneralLedger.vue'),
    meta: { requiresAuth: true },
  },
  { path: '/print/vouchers', component: () => import('../views/PrintVouchers.vue'), meta: { requiresAuth: true } },
  { path: '/print/monthly', component: () => import('../views/PrintPeriodic.vue'), meta: { requiresAuth: true } },
  { path: '/print/quarterly', component: () => import('../views/PrintPeriodic.vue'), meta: { requiresAuth: true } },
  { path: '/print/yearly', component: () => import('../views/PrintPeriodic.vue'), meta: { requiresAuth: true } },
  // ═══════════ 十四、招投标管理 ═══════════
  // 招标管理
  {
    path: '/bids/tendering/projects',
    component: () => import('../views/bids/TenderProjectList.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/bids/tendering/documents',
    component: () => import('../views/bids/TenderProjectList.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/bids/tendering/openings',
    component: () => import('../views/bids/TenderProjectList.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/bids/tendering/evaluations',
    component: () => import('../views/bids/TenderProjectList.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/bids/tendering/awards',
    component: () => import('../views/bids/TenderProjectList.vue'),
    meta: { requiresAuth: true },
  },
  // 投标管理
  {
    path: '/bids/bidding/registrations',
    component: () => import('../views/bids/BidSubmissionList.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/bids/bidding/documents',
    component: () => import('../views/bids/BidSubmissionList.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/bids/bidding/pricing',
    component: () => import('../views/bids/BidSubmissionList.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/bids/bidding/bonds',
    component: () => import('../views/bids/BidSubmissionList.vue'),
    meta: { requiresAuth: true },
  },
  // 例外事项
  {
    path: '/bids/tendering/exceptions',
    component: () => import('../views/bids/BidExceptionList.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/bids/bidding/exceptions',
    component: () => import('../views/bids/BidExceptionList.vue'),
    meta: { requiresAuth: true },
  },
]

const BASE = import.meta.env.BASE_URL

const router = createRouter({
  history: createWebHistory(BASE),
  routes,
})

router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('token')

  // 访问登录/注册页：主动清除旧 token，确保能看到登录界面
  if (to.path === '/login' || to.path === '/register') {
    if (token) {
      localStorage.removeItem('token')
      localStorage.removeItem('companyId')
    }
    return next()
  }

  // 首页根路径：有 token 也重定向到登录页（除刚登录的 fresh 标记外）
  if ((to.path === '' || to.path === '/') && !to.query.fresh) {
    if (token) {
      localStorage.removeItem('token')
      localStorage.removeItem('companyId')
    }
    return next('/login')
  }

  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else if (to.meta.allowedRoles) {
    const role = localStorage.getItem('role') || ''
    const roles = to.meta.allowedRoles as string[]
    if (!roles.includes(role)) {
      next('/')
    } else {
      next()
    }
  } else {
    next()
  }
})

export default router
