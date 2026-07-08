import axios from 'axios'

const BASE = import.meta.env.VITE_BASE || '/'
const API_BASE = BASE === '/' ? '/api' : `${BASE}api`

const api = axios.create({
  baseURL: API_BASE,
})

api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = (import.meta.env.VITE_BASE || '/') + 'login'
    }
    return Promise.reject(err)
  },
)

export default api

// Auth
export const login = (data: {
  username: string
  password: string
  company_id: number
  period: string
  is_admin?: boolean
}) => api.post('/auth/login', data)

export const getMe = () => api.get('/auth/me')
export const register = (data: { phone: string; company_name: string; password: string }) =>
  api.post('/auth/register', data)
export const lookupCompany = (companyId: number) => api.get(`/auth/company-lookup/${companyId}`)

// Companies (仅 super_admin)
export const listCompanies = () => api.get('/companies/')
export const createCompany = (data: {
  name: string
  short_name?: string
  industry?: string
  internal_control_mode?: string
  currency?: string
}) => api.post('/companies/', data)
export const updateCompany = (companyId: number, data: Record<string, any>) => api.put(`/companies/${companyId}`, data)

// Departments
export const listDepartments = (companyId: number) => api.get('/departments/', { params: { company_id: companyId } })
export const createDepartment = (data: { company_id: number; name: string; code: string; manager?: string; parent_id?: number }) =>
  api.post('/departments/', data)
export const updateDepartment = (deptId: number, data: Record<string, any>) =>
  api.put(`/departments/${deptId}`, data)
export const deleteDepartment = (deptId: number) => api.delete(`/departments/${deptId}`)
export const bulkImportDepartments = (companyId: number, rows: any[]) =>
  api.post('/departments/bulk-import', rows, { params: { company_id: companyId } })

// Accounts
export const listAccounts = (companyId: number) => api.get('/accounts/', { params: { company_id: companyId } })
export const getAccountBalance = (companyId: number) =>
  api.get('/accounts/balance', { params: { company_id: companyId } })
export const createAccount = (data: {
  company_id: number
  code: string
  name: string
  level: number
  parent_code?: string
  category: string
  balance_direction: string
  initial_balance?: number
}) => api.post('/accounts/', data)
export const updateAccount = (accountId: number, data: Record<string, any>) =>
  api.put(`/accounts/${accountId}`, data)
export const deleteAccount = (accountId: number) => api.delete(`/accounts/${accountId}`)
export const setInitialBalance = (accountId: number, balance: number) =>
  api.patch(`/accounts/${accountId}/initial-balance`, { initial_balance: balance })
export const bulkSetInitialBalance = (companyId: number, accounts: { code: string; initial_balance: number }[]) =>
  api.post('/accounts/bulk-initial-balance', { company_id: companyId, accounts })
// Vouchers
export const listVouchers = (
  companyId: number,
  params?: { start_date?: string; end_date?: string; voucher_no?: string; voucher_type?: string; status?: string },
) => api.get('/vouchers/', { params: { company_id: companyId, ...params } })
export const createVoucher = (data: {
  company_id: number
  date: string
  voucher_type: string
  summary: string
  entries: {
    account_code: string
    department_id?: number
    counterparty_id?: number
    person_id?: number
    project_id?: number
    debit: number
    credit: number
    description?: string
  }[]
}) => api.post('/vouchers/', data)
export const updateVoucher = (
  voucherId: number,
  data: {
    summary?: string
    date?: string
    voucher_type?: string
    entries?: {
      account_code: string
      department_id?: number
      counterparty_id?: number
      person_id?: number
      project_id?: number
      debit: number
      credit: number
      description?: string
    }[]
  },
) => api.put(`/vouchers/${voucherId}`, data)
export const approveVoucher = (voucherId: number) => api.post(`/vouchers/${voucherId}/approve`)
export const postVoucher = (voucherId: number) => api.post(`/vouchers/${voucherId}/post`)
export const reverseVoucher = (voucherId: number, reason: string) =>
  api.post(`/vouchers/${voucherId}/reverse`, { reason })

// Periods
export const listPeriods = (companyId: number) => api.get('/periods/', { params: { company_id: companyId } })
export const closePeriod = (companyId: number, period: string) =>
  api.post('/periods/close', { company_id: companyId, period })
export const unclosePeriod = (companyId: number, period: string, reason: string) =>
  api.post('/periods/un-close', null, { params: { company_id: companyId, period, reason } })

// Reports
export const getBalanceSheet = (companyId: number, period: string) =>
  api.get('/reports/balance', { params: { company_id: companyId, period } })
export const getIncomeStatement = (companyId: number, period: string) =>
  api.get('/reports/income', { params: { company_id: companyId, period } })
export const getCashFlow = (companyId: number, period: string) =>
  api.get('/reports/cashflow', { params: { company_id: companyId, period } })

// Cash-flow items
export const listCashFlowItems = (companyId: number) =>
  api.get('/cashflow-items/', { params: { company_id: companyId } })
export const createCashFlowItem = (data: any) => api.post('/cashflow-items/', data)
export const updateCashFlowItem = (id: number, data: any) => api.put(`/cashflow-items/${id}`, data)
export const deleteCashFlowItem = (id: number) => api.delete(`/cashflow-items/${id}`)
export const seedDefaultCashFlowItems = (companyId: number) =>
  api.post('/cashflow-items/seed-defaults', null, { params: { company_id: companyId } })

// Audit
export const listAuditLogs = (companyId: number) => api.get('/audit/', { params: { company_id: companyId } })

// Users
export const listUsers = () => api.get('/users/')
export const createUser = (data: { username: string; email: string; password: string; role: string }) =>
  api.post('/users/', data)
export const updateUser = (userId: number, data: { role?: string; is_active?: boolean }) =>
  api.put(`/users/${userId}`, null, { params: data })
export const deleteUser = (userId: number) => api.delete(`/users/${userId}`)
export const resetUserPassword = (userId: number, newPassword: string) =>
  api.post(`/users/${userId}/reset-password`, null, { params: { new_password: newPassword } })
export const changeMyPassword = (currentPassword: string, newPassword: string) =>
  api.post('/auth/change-password', null, { params: { current_password: currentPassword, new_password: newPassword } })

// Print module
export const printCompany = (companyId: number) => api.get('/prints/company', { params: { company_id: companyId } })
export const printDepartments = (companyId: number) =>
  api.get('/prints/departments', { params: { company_id: companyId } })
export const printSubjects = (companyId: number, level?: number) =>
  api.get('/prints/subjects', { params: { company_id: companyId, ...(level ? { level } : {}) } })
export const printSubjectBalance = (companyId: number, period: string) =>
  api.get('/prints/subject-balance', { params: { company_id: companyId, period } })
export const printGeneralLedger = (companyId: number, period: string) =>
  api.get('/prints/general-ledger', { params: { company_id: companyId, period } })
export const printVouchers = (companyId: number, range: string = 'month', extraParams: Record<string, string> = {}) =>
  api.get('/prints/vouchers', { params: { company_id: companyId, range, ...extraParams } })
export const printPeriodic = (companyId: number, period: string, report: string, type: string = 'monthly') =>
  api.get('/prints/periodic', { params: { company_id: companyId, period, report, type } })

export const exportPeriodicExcel = async (companyId: number, period: string, report: string, type: string = 'monthly') => {
  const res = await api.get('/prints/periodic/export', {
    params: { company_id: companyId, period, report, type },
    responseType: 'blob',
  })
  // Check if server returned an error as JSON instead of Excel
  if (res.data instanceof Blob && res.data.type === 'application/json') {
    const text = await res.data.text()
    let detail = '导出失败'
    try { detail = JSON.parse(text).detail || detail } catch { /* ignore parse error */ }
    throw new Error(detail)
  }
  const url = URL.createObjectURL(res.data)
  const link = document.createElement('a')
  link.href = url
  const names: Record<string, string> = { balance: '资产负债表', income: '利润表', cashflow: '现金流量表' }
  link.download = `${names[report] || report}_${period}.xlsx`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

// Counterparties & Persons
export const listCounterparties = (companyId: number) =>
  api.get('/counterparties/', { params: { company_id: companyId } })
export const listPersons = (companyId: number, departmentCode?: string) =>
  api.get('/persons/', {
    params: { company_id: companyId, ...(departmentCode ? { department_code: departmentCode } : {}) },
  })
export const importAuxConfig = (companyId: number) =>
  api.post('/accounts/import-aux-config', null, { params: { company_id: companyId } })

// Projects
export const listProjects = (companyId: number) => api.get('/projects/', { params: { company_id: companyId } })
export const createProject = (companyId: number, data: any) =>
  api.post('/projects/', data, { params: { company_id: companyId } })
export const updateProject = (projectId: number, data: any) => api.put(`/projects/${projectId}`, data)
export const deleteProject = (projectId: number) => api.delete(`/projects/${projectId}`)

// Investment - Portfolios
export const listPortfolios = (companyId: number) =>
  api.get('/investments/portfolios', { params: { company_id: companyId } })
export const createPortfolio = (
  companyId: number,
  data: { name: string; investment_type: string; currency: string; description?: string },
) => api.post('/investments/portfolios', data, { params: { company_id: companyId } })
export const updatePortfolio = (portfolioId: number, data: Record<string, any>) =>
  api.put(`/investments/portfolios/${portfolioId}`, data)
export const deletePortfolio = (portfolioId: number) => api.delete(`/investments/portfolios/${portfolioId}`)

// Investment - Positions
export const listPositions = (companyId: number, portfolioId?: number) =>
  api.get('/investments/positions', {
    params: { company_id: companyId, ...(portfolioId ? { portfolio_id: portfolioId } : {}) },
  })
export const createPosition = (companyId: number, data: any) =>
  api.post('/investments/positions', data, { params: { company_id: companyId } })
export const updatePosition = (positionId: number, data: any) => api.put(`/investments/positions/${positionId}`, data)
export const deletePosition = (positionId: number) => api.delete(`/investments/positions/${positionId}`)

// Investment - Transactions
export const listTransactions = (companyId: number, positionId?: number) =>
  api.get('/investments/transactions', {
    params: { company_id: companyId, ...(positionId ? { position_id: positionId } : {}) },
  })
export const createTransaction = (companyId: number, data: any) =>
  api.post('/investments/transactions', data, { params: { company_id: companyId } })
export const updateTransaction = (id: number, data: any) => api.put(`/investments/transactions/${id}`, data)
export const deleteTransaction = (id: number) => api.delete(`/investments/transactions/${id}`)

// Investment - Adjustments
export const listAdjustments = (companyId: number, positionId?: number) =>
  api.get('/investments/adjustments', {
    params: { company_id: companyId, ...(positionId ? { position_id: positionId } : {}) },
  })
export const createAdjustment = (companyId: number, data: any) =>
  api.post('/investments/adjustments', data, { params: { company_id: companyId } })
export const updateAdjustment = (id: number, data: any) => api.put(`/investments/adjustments/${id}`, data)
export const deleteAdjustment = (id: number) => api.delete(`/investments/adjustments/${id}`)

// Investment - Income
export const listInvestmentIncome = (companyId: number, positionId?: number) =>
  api.get('/investments/income', {
    params: { company_id: companyId, ...(positionId ? { position_id: positionId } : {}) },
  })
export const createInvestmentIncome = (companyId: number, data: any) =>
  api.post('/investments/income', data, { params: { company_id: companyId } })
export const updateInvestmentIncome = (id: number, data: any) => api.put(`/investments/income/${id}`, data)
export const deleteInvestmentIncome = (id: number) => api.delete(`/investments/income/${id}`)

// Investment - Reports
export const getPositionsReport = (companyId: number, investmentType?: string) =>
  api.get('/investments/reports/positions', {
    params: { company_id: companyId, ...(investmentType ? { investment_type: investmentType } : {}) },
  })

// Investment - Securities Master
export const listSecurities = (companyId: number, securityType?: string, exchange?: string) =>
  api.get('/investments/securities', {
    params: {
      company_id: companyId,
      ...(securityType ? { security_type: securityType } : {}),
      ...(exchange ? { exchange } : {}),
    },
  })
export const createSecurity = (companyId: number, data: any) =>
  api.post('/investments/securities', data, { params: { company_id: companyId } })
export const updateSecurity = (id: number, data: any) => api.put(`/investments/securities/${id}`, data)
export const deleteSecurity = (id: number) => api.delete(`/investments/securities/${id}`)

// Investment - Fund Management
export const listFunds = (companyId: number) => api.get('/investments/funds', { params: { company_id: companyId } })
export const createFund = (companyId: number, data: any) =>
  api.post('/investments/funds', data, { params: { company_id: companyId } })
export const updateFund = (id: number, data: any) => api.put(`/investments/funds/${id}`, data)
export const deleteFund = (id: number) => api.delete(`/investments/funds/${id}`)
export const listCapitalAccounts = (fundId: number) => api.get(`/investments/funds/${fundId}/capital-accounts`)
export const createCapitalAccount = (fundId: number, companyId: number, data: any) =>
  api.post(`/investments/funds/${fundId}/capital-accounts`, data, { params: { company_id: companyId } })
export const updateCapitalAccount = (fundId: number, id: number, data: any) =>
  api.put(`/investments/funds/${fundId}/capital-accounts/${id}`, data)
export const deleteCapitalAccount = (fundId: number, id: number) =>
  api.delete(`/investments/funds/${fundId}/capital-accounts/${id}`)
export const listCapitalCalls = (fundId: number) => api.get(`/investments/funds/${fundId}/capital-calls`)
export const createCapitalCall = (fundId: number, companyId: number, data: any) =>
  api.post(`/investments/funds/${fundId}/capital-calls`, data, { params: { company_id: companyId } })
export const updateCapitalCall = (fundId: number, id: number, data: any) =>
  api.put(`/investments/funds/${fundId}/capital-calls/${id}`, data)
export const deleteCapitalCall = (fundId: number, id: number) =>
  api.delete(`/investments/funds/${fundId}/capital-calls/${id}`)
export const listFundDistributions = (fundId: number) => api.get(`/investments/funds/${fundId}/distributions`)
export const createFundDistribution = (fundId: number, companyId: number, data: any) =>
  api.post(`/investments/funds/${fundId}/distributions`, data, { params: { company_id: companyId } })
export const updateFundDistribution = (fundId: number, id: number, data: any) =>
  api.put(`/investments/funds/${fundId}/distributions/${id}`, data)
export const deleteFundDistribution = (fundId: number, id: number) =>
  api.delete(`/investments/funds/${fundId}/distributions/${id}`)
export const getIncomeReport = (companyId: number, startDate?: string, endDate?: string) =>
  api.get('/investments/reports/income', {
    params: {
      company_id: companyId,
      ...(startDate ? { start_date: startDate } : {}),
      ...(endDate ? { end_date: endDate } : {}),
    },
  })
export const getFairValueReport = (companyId: number, startDate?: string, endDate?: string) =>
  api.get('/investments/reports/fair-value', {
    params: {
      company_id: companyId,
      ...(startDate ? { start_date: startDate } : {}),
      ...(endDate ? { end_date: endDate } : {}),
    },
  })

// ── HR 人力资源模块 ──
export const listHrPositions = (companyId: number) => api.get('/hr/positions', { params: { company_id: companyId } })
export const createHrPosition = (data: any) => api.post('/hr/positions', data)
export const updateHrPosition = (id: number, data: any) => api.put(`/hr/positions/${id}`, data)
export const deleteHrPosition = (id: number) => api.delete(`/hr/positions/${id}`)

export const listHrEmployees = (companyId: number, status?: string, departmentId?: number) =>
  api.get('/hr/employees', {
    params: {
      company_id: companyId,
      ...(status ? { status } : {}),
      ...(departmentId ? { department_id: departmentId } : {}),
    },
  })
export const createHrEmployee = (data: any) => api.post('/hr/employees', data)
export const updateHrEmployee = (id: number, data: any) => api.put(`/hr/employees/${id}`, data)
export const deleteHrEmployee = (id: number) => api.delete(`/hr/employees/${id}`)

export const listHrTrainings = (companyId: number, employeeId?: number) =>
  api.get('/hr/trainings', { params: { company_id: companyId, ...(employeeId ? { employee_id: employeeId } : {}) } })
export const createHrTraining = (data: any) => api.post('/hr/trainings', data)
export const updateHrTraining = (id: number, data: any) => api.put(`/hr/trainings/${id}`, data)
export const deleteHrTraining = (id: number) => api.delete(`/hr/trainings/${id}`)

export const listHrEvaluations = (companyId: number, employeeId?: number) =>
  api.get('/hr/evaluations', { params: { company_id: companyId, ...(employeeId ? { employee_id: employeeId } : {}) } })
export const createHrEvaluation = (data: any) => api.post('/hr/evaluations', data)
export const updateHrEvaluation = (id: number, data: any) => api.put(`/hr/evaluations/${id}`, data)
export const deleteHrEvaluation = (id: number) => api.delete(`/hr/evaluations/${id}`)

export const listHrSalaries = (companyId: number, employeeId?: number, yearMonth?: string) =>
  api.get('/hr/salaries', {
    params: {
      company_id: companyId,
      ...(employeeId ? { employee_id: employeeId } : {}),
      ...(yearMonth ? { year_month: yearMonth } : {}),
    },
  })
export const createHrSalary = (data: any) => api.post('/hr/salaries', data)
export const updateHrSalary = (id: number, data: any) => api.put(`/hr/salaries/${id}`, data)
export const deleteHrSalary = (id: number) => api.delete(`/hr/salaries/${id}`)

export const listHrRewards = (companyId: number, employeeId?: number) =>
  api.get('/hr/rewards', { params: { company_id: companyId, ...(employeeId ? { employee_id: employeeId } : {}) } })
export const createHrReward = (data: any) => api.post('/hr/rewards', data)
export const updateHrReward = (id: number, data: any) => api.put(`/hr/rewards/${id}`, data)
export const deleteHrReward = (id: number) => api.delete(`/hr/rewards/${id}`)

export const listHrOffboarding = (companyId: number, employeeId?: number) =>
  api.get('/hr/offboarding', { params: { company_id: companyId, ...(employeeId ? { employee_id: employeeId } : {}) } })
export const createHrOffboarding = (data: any) => api.post('/hr/offboarding', data)
export const updateHrOffboarding = (id: number, data: any) => api.put(`/hr/offboarding/${id}`, data)
export const deleteHrOffboarding = (id: number) => api.delete(`/hr/offboarding/${id}`)

export const listHrBudgets = (companyId: number, year?: number) =>
  api.get('/hr/budgets', { params: { company_id: companyId, ...(year ? { year } : {}) } })
export const upsertHrBudget = (data: any) => api.post('/hr/budgets', data)
export const deleteHrBudget = (id: number) => api.delete(`/hr/budgets/${id}`)

export const listHrPolicies = (companyId: number) => api.get('/hr/policies', { params: { company_id: companyId } })
export const upsertHrPolicy = (data: any) => api.post('/hr/policies', data)

// ═══════════ 固定资产管理 ═══════════
export const listFixedAssets = (companyId: number, params?: Record<string, any>) =>
  api.get('/fixed-assets/assets', { params: { company_id: companyId, ...params } })
export const getFixedAsset = (id: number) => api.get(`/fixed-assets/assets/${id}`)
export const createFixedAsset = (data: any) => api.post('/fixed-assets/assets', data)
export const updateFixedAsset = (id: number, data: any) => api.put(`/fixed-assets/assets/${id}`, data)
export const deleteFixedAsset = (id: number) => api.delete(`/fixed-assets/assets/${id}`)
export const disposeFixedAsset = (id: number, data: any) => api.post(`/fixed-assets/assets/${id}/dispose`, data)

export const listDepreciations = (companyId: number, params?: Record<string, any>) =>
  api.get('/fixed-assets/depreciations', { params: { company_id: companyId, ...params } })
export const createDepreciation = (data: any) => api.post('/fixed-assets/depreciations', data)
export const updateDepreciation = (id: number, data: any) => api.put(`/fixed-assets/depreciations/${id}`, data)
export const deleteDepreciation = (id: number) => api.delete(`/fixed-assets/depreciations/${id}`)
export const batchDepreciate = (data: any) => api.post('/fixed-assets/depreciations/batch', data)

// ═══════════ 应收账款管理 ═══════════
export const listReceivables = (companyId: number, params?: Record<string, any>) =>
  api.get('/receivables/invoices', { params: { company_id: companyId, ...params } })
export const createReceivable = (data: any) => api.post('/receivables/invoices', data)
export const updateReceivable = (id: number, data: any) => api.put(`/receivables/invoices/${id}`, data)
export const deleteReceivable = (id: number) => api.delete(`/receivables/invoices/${id}`)
export const batchDeleteReceivables = (data: { ids: number[] }) => api.post('/receivables/invoices/batch-delete', data)

export const listReceivablePayments = (companyId: number, params?: Record<string, any>) =>
  api.get('/receivables/payments', { params: { company_id: companyId, ...params } })
export const createReceivablePayment = (data: any) => api.post('/receivables/payments', data)

export const getReceivablesSummary = (companyId: number) =>
  api.get('/receivables/summary', { params: { company_id: companyId } })

export const listReceivableCounterparties = (companyId: number) =>
  api.get('/receivables/counterparties', { params: { company_id: companyId } })

// ═══════════ 应付账款管理 ═══════════
export const listPayables = (companyId: number, params?: Record<string, any>) =>
  api.get('/payables/invoices', { params: { company_id: companyId, ...params } })
export const createPayable = (data: any) => api.post('/payables/invoices', data)
export const updatePayable = (id: number, data: any) => api.put(`/payables/invoices/${id}`, data)
export const deletePayable = (id: number) => api.delete(`/payables/invoices/${id}`)

export const listPayablePayments = (companyId: number, params?: Record<string, any>) =>
  api.get('/payables/payments', { params: { company_id: companyId, ...params } })
export const createPayablePayment = (data: any) => api.post('/payables/payments', data)

export const listPayableCounterparties = (companyId: number) =>
  api.get('/payables/counterparties', { params: { company_id: companyId } })

export const getPayablesSummary = (companyId: number) =>
  api.get('/payables/summary', { params: { company_id: companyId } })

// ═══════════ 进销存管理 ═══════════
export const listPurchases = (companyId: number, params?: Record<string, any>) =>
  api.get('/inventory-trade/purchases', { params: { company_id: companyId, ...params } })
export const createPurchase = (data: any) => api.post('/inventory-trade/purchases', data)
export const updatePurchase = (id: number, data: any) => api.put(`/inventory-trade/purchases/${id}`, data)
export const deletePurchase = (id: number) => api.delete(`/inventory-trade/purchases/${id}`)

export const listInvSales = (companyId: number, params?: Record<string, any>) =>
  api.get('/inventory-trade/sales', { params: { company_id: companyId, ...params } })
export const createInvSale = (data: any) => api.post('/inventory-trade/sales', data)
export const updateInvSale = (id: number, data: any) => api.put(`/inventory-trade/sales/${id}`, data)
export const deleteInvSale = (id: number) => api.delete(`/inventory-trade/sales/${id}`)

export const listInvStock = (companyId: number, params?: Record<string, any>) =>
  api.get('/inventory-trade/stock', { params: { company_id: companyId, ...params } })
export const createInvStock = (data: any) => api.post('/inventory-trade/stock', data)
export const updateInvStock = (id: number, data: any) => api.put(`/inventory-trade/stock/${id}`, data)
export const deleteInvStock = (id: number) => api.delete(`/inventory-trade/stock/${id}`)

// 进销存主数据
export const listWarehouses = (companyId: number) =>
  api.get('/inventory-trade/warehouses', { params: { company_id: companyId } })
export const listInventoryCategories = (companyId: number) =>
  api.get('/inventory-trade/categories', { params: { company_id: companyId } })
export const listInventory = (companyId: number) =>
  api.get('/inventory-trade/inventory', { params: { company_id: companyId } })
export const listUnitsOfMeasure = (companyId: number) =>
  api.get('/inventory-trade/units', { params: { company_id: companyId } })

// ── 行政综合管理 Admin ──

// Approval
export const listPendingApprovals = (companyId: number) =>
  api.get('/admin/approvals/pending', { params: { company_id: companyId } })
export const listApprovals = (companyId: number, targetType: string, targetId: number) =>
  api.get('/admin/approvals', { params: { company_id: companyId, target_type: targetType, target_id: targetId } })
export const approveStep = (recordId: number, comment?: string) =>
  api.post(`/admin/approvals/${recordId}/approve`, { comment })
export const rejectStep = (recordId: number, comment?: string) =>
  api.post(`/admin/approvals/${recordId}/reject`, { comment })

// Documents
export const listAdminDocuments = (companyId: number, status?: string) =>
  api.get('/admin/documents', { params: { company_id: companyId, ...(status ? { status } : {}) } })
export const createAdminDocument = (data: any) => api.post('/admin/documents', data)
export const updateAdminDocument = (id: number, data: any) => api.put(`/admin/documents/${id}`, data)
export const deleteAdminDocument = (id: number) => api.delete(`/admin/documents/${id}`)
export const submitDocument = (id: number, approverIds: number[]) =>
  api.post(`/admin/documents/${id}/submit`, { approver_ids: approverIds })
export const issueDocument = (id: number) => api.post(`/admin/documents/${id}/issue`)

// Vehicle Suppliers
export const listVehicleSuppliers = (companyId: number) =>
  api.get('/admin/vehicles/suppliers', { params: { company_id: companyId } })
export const createVehicleSupplier = (data: any) => api.post('/admin/vehicles/suppliers', data)
export const updateVehicleSupplier = (id: number, data: any) => api.put(`/admin/vehicles/suppliers/${id}`, data)
export const deleteVehicleSupplier = (id: number) => api.delete(`/admin/vehicles/suppliers/${id}`)

// Vehicle Purchases
export const listVehiclePurchases = (companyId: number) =>
  api.get('/admin/vehicles/purchases', { params: { company_id: companyId } })
export const createVehiclePurchase = (data: any) => api.post('/admin/vehicles/purchases', data)
export const updateVehiclePurchase = (id: number, data: any) => api.put(`/admin/vehicles/purchases/${id}`, data)
export const deleteVehiclePurchase = (id: number) => api.delete(`/admin/vehicles/purchases/${id}`)
export const submitVehiclePurchase = (id: number, approverIds: number[]) =>
  api.post(`/admin/vehicles/purchases/${id}/submit`, { approver_ids: approverIds })

// Vehicles
export const listVehicles = (companyId: number, status?: string) =>
  api.get('/admin/vehicles', { params: { company_id: companyId, ...(status ? { status } : {}) } })
export const createVehicle = (data: any) => api.post('/admin/vehicles', data)
export const updateVehicle = (id: number, data: any) => api.put(`/admin/vehicles/${id}`, data)
export const deleteVehicle = (id: number) => api.delete(`/admin/vehicles/${id}`)

// Vehicle Maintenance
export const listVehicleMaintenance = (companyId: number) =>
  api.get('/admin/vehicles/maintenance', { params: { company_id: companyId } })
export const createVehicleMaintenance = (data: any) => api.post('/admin/vehicles/maintenance', data)
export const updateVehicleMaintenance = (id: number, data: any) => api.put(`/admin/vehicles/maintenance/${id}`, data)
export const deleteVehicleMaintenance = (id: number) => api.delete(`/admin/vehicles/maintenance/${id}`)
export const submitVehicleMaintenance = (id: number, approverIds: number[]) =>
  api.post(`/admin/vehicles/maintenance/${id}/submit`, { approver_ids: approverIds })

// Insurance
export const listInsurance = (companyId: number, status?: string) =>
  api.get('/admin/insurance', { params: { company_id: companyId, ...(status ? { status } : {}) } })
export const createInsurance = (data: any) => api.post('/admin/insurance', data)
export const updateInsurance = (id: number, data: any) => api.put(`/admin/insurance/${id}`, data)
export const deleteInsurance = (id: number) => api.delete(`/admin/insurance/${id}`)
export const submitInsurance = (id: number, approverIds: number[]) =>
  api.post(`/admin/insurance/${id}/submit`, { approver_ids: approverIds })
export const listExpiringInsurance = (companyId: number, days: number = 30) =>
  api.get('/admin/insurance/expiring', { params: { company_id: companyId, days } })

// Stock Categories
export const listStockCategories = (companyId: number) =>
  api.get('/admin/stock/categories', { params: { company_id: companyId } })
export const createStockCategory = (data: any) => api.post('/admin/stock/categories', data)
export const updateStockCategory = (id: number, data: any) => api.put(`/admin/stock/categories/${id}`, data)
export const deleteStockCategory = (id: number) => api.delete(`/admin/stock/categories/${id}`)

// Stock Assets
export const listStockAssets = (companyId: number, status?: string, categoryId?: number) =>
  api.get('/admin/stock/assets', {
    params: {
      company_id: companyId,
      ...(status ? { status } : {}),
      ...(categoryId ? { category_id: categoryId } : {}),
    },
  })
export const createStockAsset = (data: any) => api.post('/admin/stock/assets', data)
export const updateStockAsset = (id: number, data: any) => api.put(`/admin/stock/assets/${id}`, data)
export const deleteStockAsset = (id: number) => api.delete(`/admin/stock/assets/${id}`)

// Stock Purchases
export const listStockPurchases = (companyId: number) =>
  api.get('/admin/stock/assets/purchases', { params: { company_id: companyId } })
export const createStockPurchase = (data: any) => api.post('/admin/stock/assets/purchases', data)
export const updateStockPurchase = (id: number, data: any) => api.put(`/admin/stock/assets/purchases/${id}`, data)
export const deleteStockPurchase = (id: number) => api.delete(`/admin/stock/assets/purchases/${id}`)
export const submitStockPurchase = (id: number, approverIds: number[]) =>
  api.post(`/admin/stock/assets/purchases/${id}/submit`, { approver_ids: approverIds })

// Stock Requisitions
export const listStockRequisitions = (companyId: number) =>
  api.get('/admin/stock/assets/requisitions', { params: { company_id: companyId } })
export const createStockRequisition = (data: any) => api.post('/admin/stock/assets/requisitions', data)
export const updateStockRequisition = (id: number, data: any) => api.put(`/admin/stock/assets/requisitions/${id}`, data)
export const deleteStockRequisition = (id: number) => api.delete(`/admin/stock/assets/requisitions/${id}`)
export const submitStockRequisition = (id: number, approverIds: number[]) =>
  api.post(`/admin/stock/assets/requisitions/${id}/submit`, { approver_ids: approverIds })

// Stock Inbound
export const listStockInbound = (companyId: number) =>
  api.get('/admin/stock/assets/inbound', { params: { company_id: companyId } })
export const createStockInbound = (data: any) => api.post('/admin/stock/assets/inbound', data)
export const updateStockInbound = (id: number, data: any) => api.put(`/admin/stock/assets/inbound/${id}`, data)
export const deleteStockInbound = (id: number) => api.delete(`/admin/stock/assets/inbound/${id}`)
export const submitStockInbound = (id: number, approverIds: number[]) =>
  api.post(`/admin/stock/assets/inbound/${id}/submit`, { approver_ids: approverIds })

// Stock Outbound
export const listStockOutbound = (companyId: number) =>
  api.get('/admin/stock/assets/outbound', { params: { company_id: companyId } })
export const createStockOutbound = (data: any) => api.post('/admin/stock/assets/outbound', data)
export const updateStockOutbound = (id: number, data: any) => api.put(`/admin/stock/assets/outbound/${id}`, data)
export const deleteStockOutbound = (id: number) => api.delete(`/admin/stock/assets/outbound/${id}`)
export const submitStockOutbound = (id: number, approverIds: number[]) =>
  api.post(`/admin/stock/assets/outbound/${id}/submit`, { approver_ids: approverIds })

// Stock Counts
export const listStockCounts = (companyId: number) =>
  api.get('/admin/stock/assets/counts', { params: { company_id: companyId } })
export const createStockCount = (data: any) => api.post('/admin/stock/assets/counts', data)
export const updateStockCount = (id: number, data: any) => api.put(`/admin/stock/assets/counts/${id}`, data)
export const deleteStockCount = (id: number) => api.delete(`/admin/stock/assets/counts/${id}`)

// Gift Categories
export const listGiftCategories = (companyId: number) =>
  api.get('/admin/stock/gifts/categories', { params: { company_id: companyId } })
export const createGiftCategory = (data: any) => api.post('/admin/stock/gifts/categories', data)
export const updateGiftCategory = (id: number, data: any) => api.put(`/admin/stock/gifts/categories/${id}`, data)
export const deleteGiftCategory = (id: number) => api.delete(`/admin/stock/gifts/categories/${id}`)

// Stock Gifts
export const listStockGifts = (companyId: number, categoryId?: number) =>
  api.get('/admin/stock/gifts', {
    params: { company_id: companyId, ...(categoryId ? { category_id: categoryId } : {}) },
  })
export const createStockGift = (data: any) => api.post('/admin/stock/gifts', data)
export const updateStockGift = (id: number, data: any) => api.put(`/admin/stock/gifts/${id}`, data)
export const deleteStockGift = (id: number) => api.delete(`/admin/stock/gifts/${id}`)

// Gift Purchases
export const listGiftPurchases = (companyId: number) =>
  api.get('/admin/stock/gifts/purchases', { params: { company_id: companyId } })
export const createGiftPurchase = (data: any) => api.post('/admin/stock/gifts/purchases', data)
export const updateGiftPurchase = (id: number, data: any) => api.put(`/admin/stock/gifts/purchases/${id}`, data)
export const deleteGiftPurchase = (id: number) => api.delete(`/admin/stock/gifts/purchases/${id}`)
export const submitGiftPurchase = (id: number, approverIds: number[]) =>
  api.post(`/admin/stock/gifts/purchases/${id}/submit`, { approver_ids: approverIds })

// Gift Requisitions
export const listGiftRequisitions = (companyId: number) =>
  api.get('/admin/stock/gifts/requisitions', { params: { company_id: companyId } })
export const createGiftRequisition = (data: any) => api.post('/admin/stock/gifts/requisitions', data)
export const updateGiftRequisition = (id: number, data: any) => api.put(`/admin/stock/gifts/requisitions/${id}`, data)
export const deleteGiftRequisition = (id: number) => api.delete(`/admin/stock/gifts/requisitions/${id}`)
export const submitGiftRequisition = (id: number, approverIds: number[]) =>
  api.post(`/admin/stock/gifts/requisitions/${id}/submit`, { approver_ids: approverIds })

// Gift Inbound
export const listGiftInbound = (companyId: number) =>
  api.get('/admin/stock/gifts/inbound', { params: { company_id: companyId } })
export const createGiftInbound = (data: any) => api.post('/admin/stock/gifts/inbound', data)
export const updateGiftInbound = (id: number, data: any) => api.put(`/admin/stock/gifts/inbound/${id}`, data)
export const deleteGiftInbound = (id: number) => api.delete(`/admin/stock/gifts/inbound/${id}`)
export const submitGiftInbound = (id: number, approverIds: number[]) =>
  api.post(`/admin/stock/gifts/inbound/${id}/submit`, { approver_ids: approverIds })

// Gift Outbound
export const listGiftOutbound = (companyId: number) =>
  api.get('/admin/stock/gifts/outbound', { params: { company_id: companyId } })
export const createGiftOutbound = (data: any) => api.post('/admin/stock/gifts/outbound', data)
export const updateGiftOutbound = (id: number, data: any) => api.put(`/admin/stock/gifts/outbound/${id}`, data)
export const deleteGiftOutbound = (id: number) => api.delete(`/admin/stock/gifts/outbound/${id}`)
export const submitGiftOutbound = (id: number, approverIds: number[]) =>
  api.post(`/admin/stock/gifts/outbound/${id}/submit`, { approver_ids: approverIds })

// ═══════════ 服务器管理 ═══════════
export const listServers = (companyId: number) => api.get('/servers/', { params: { company_id: companyId } })
export const getServer = (id: number) => api.get(`/servers/${id}`)
export const createServer = (data: any) => api.post('/servers/', data)
export const updateServer = (id: number, data: any) => api.put(`/servers/${id}`, data)
export const deleteServer = (id: number) => api.delete(`/servers/${id}`)

// 服务管理
export const listServices = (serverId: number) => api.get(`/servers/${serverId}/services`)
export const createService = (serverId: number, data: any) => api.post(`/servers/${serverId}/services`, data)
export const updateService = (id: number, data: any) => api.put(`/servers/services/${id}`, data)
export const deleteService = (id: number) => api.delete(`/servers/services/${id}`)
export const controlService = (id: number, action: 'start' | 'stop' | 'restart') =>
  api.post(`/servers/services/${id}/control`, { action })
export const listAllServices = (companyId: number) =>
  api.get('/servers/all/services', { params: { company_id: companyId } })

// ═══════════ 知识库管理 ═══════════
export const listKbArticles = (
  companyId: number,
  params?: { category_id?: number; status?: string; search?: string; limit?: number; offset?: number },
) => api.get('/kb/articles', { params: { company_id: companyId, ...params } })
export const getKbArticle = (id: number) => api.get(`/kb/articles/${id}`)
export const createKbArticle = (data: any) => api.post('/kb/articles', data)
export const updateKbArticle = (id: number, data: any) => api.put(`/kb/articles/${id}`, data)
export const deleteKbArticle = (id: number) => api.delete(`/kb/articles/${id}`)

// KB 分类
export const listKbCategories = (companyId: number) => api.get('/kb/categories', { params: { company_id: companyId } })
export const getKbCategory = (id: number) => api.get(`/kb/categories/${id}`)
export const createKbCategory = (data: { company_id: number; name: string; parent_id: number }) =>
  api.post('/kb/categories', data)
export const updateKbCategory = (id: number, companyId: number, data: { name?: string; sort_order?: number }) =>
  api.put(`/kb/categories/${id}`, data, { params: { company_id: companyId } })
export const deleteKbCategory = (id: number, companyId: number) =>
  api.delete(`/kb/categories/${id}`, { params: { company_id: companyId } })

// Permissions
export const getUserPermissions = (userId: number, companyId: number) =>
  api.get(`/permissions/${userId}`, { params: { company_id: companyId } })
export const setUserPermissions = (userId: number, data: any) => api.put(`/permissions/${userId}`, data)
export const listAllPermissions = (companyId: number) =>
  api.get('/permissions/', { params: { company_id: companyId } })

// ── 历史凭证 ──
export const batchImportVouchers = (data: any[]) => api.post('/vouchers/batch-import', data)
export const listVoucherArchive = (companyId: number, year: number) =>
  api.get('/vouchers/archive', { params: { company_id: companyId, year } })

// ── 期末处理扩展 ──

export const getCloseChecks = (companyId: number, period: string) =>
  api.get('/periods/close-checks', { params: { company_id: companyId, period } })

export const getQuarterlySummary = (companyId: number, year: number) =>
  api.get('/periods/quarterly-summary', { params: { company_id: companyId, year } })

export const getYearlySummary = (companyId: number, year: number) =>
  api.get('/periods/yearly-summary', { params: { company_id: companyId, year } })

export const listCarryForwards = (companyId: number, period?: string) =>
  api.get('/periods/carry-forwards', { params: { company_id: companyId, period } })

export const createCarryForward = (data: {
  company_id: number
  period: string
  entry_type: string
  debit_account_id?: number
  credit_account_id?: number
  amount: number
}) => api.post('/periods/carry-forward', data)

export const executeCarryForward = (entryId: number) => api.post(`/periods/carry-forward/${entryId}/execute`)

export const deleteCarryForward = (entryId: number) => api.delete(`/periods/carry-forwards/${entryId}`)

// ═══════════ 总账模块 ═══════════

// Auto-transfer templates
export const listAutoTransferTemplates = (companyId: number) =>
  api.get('/gl/auto-transfer-templates', { params: { company_id: companyId } })
export const createAutoTransferTemplate = (data: any) => api.post('/gl/auto-transfer-templates', data)
export const updateAutoTransferTemplate = (id: number, data: any) => api.put(`/gl/auto-transfer-templates/${id}`, data)
export const deleteAutoTransferTemplate = (id: number) => api.delete(`/gl/auto-transfer-templates/${id}`)
export const executeAutoTransfer = (id: number, companyId: number, period: string) =>
  api.post(`/gl/auto-transfer-templates/${id}/execute`, null, { params: { company_id: companyId, period } })

// Subject ledger
export const getSubjectLedger = (
  companyId: number,
  start_period: string,
  end_period: string,
  params?: { account_code?: string; level?: number; include_zero?: boolean },
) => api.get('/gl/subject-ledger', { params: { company_id: companyId, start_period, end_period, ...params } })
export const getSingleSubjectLedger = (companyId: number, code: string, start_period: string, end_period: string) =>
  api.get(`/gl/subject-ledger/${code}`, { params: { company_id: companyId, start_period, end_period } })

// Aux ledger
export const getAuxLedger = (
  companyId: number,
  aux_type: string,
  aux_id: number,
  start_period: string,
  end_period: string,
  account_code?: string,
) =>
  api.get('/gl/aux-ledger', {
    params: {
      company_id: companyId,
      aux_type,
      aux_id,
      start_period,
      end_period,
      ...(account_code ? { account_code } : {}),
    },
  })

// Custom queries
export const listCustomQueries = (companyId: number, query_type?: string) =>
  api.get('/gl/custom-queries', { params: { company_id: companyId, ...(query_type ? { query_type } : {}) } })
export const createCustomQuery = (data: any) => api.post('/gl/custom-queries', data)
export const updateCustomQuery = (id: number, data: any) => api.put(`/gl/custom-queries/${id}`, data)
export const deleteCustomQuery = (id: number) => api.delete(`/gl/custom-queries/${id}`)
export const executeCustomQuery = (id: number, companyId: number, start_period: string, end_period: string) =>
  api.get(`/gl/custom-queries/${id}/execute`, { params: { company_id: companyId, start_period, end_period } })

// Custom detail
export const getCustomDetailColumns = () => api.get('/gl/custom-detail/columns')
export const queryCustomDetail = (companyId: number, data: any) =>
  api.post('/gl/custom-detail/query', data, { params: { company_id: companyId } })
export const exportCustomDetail = (companyId: number, start_date: string, end_date: string, account_code?: string) =>
  api.get('/gl/custom-detail/export', {
    params: { company_id: companyId, start_date, end_date, ...(account_code ? { account_code } : {}) },
    responseType: 'blob',
  })

// Transactions
export const getTransactionBalances = (
  companyId: number,
  start_period: string,
  end_period: string,
  account_code?: string,
) =>
  api.get('/gl/transactions/balance', {
    params: { company_id: companyId, start_period, end_period, ...(account_code ? { account_code } : {}) },
  })
export const getTransactionDetail = (
  companyId: number,
  counterpartyId: number,
  start_period: string,
  end_period: string,
  account_code?: string,
) =>
  api.get(`/gl/transactions/${counterpartyId}`, {
    params: { company_id: companyId, start_period, end_period, ...(account_code ? { account_code } : {}) },
  })
export const getTransactionAging = (companyId: number, end_period: string, account_code?: string) =>
  api.get('/gl/transactions/aging', {
    params: { company_id: companyId, end_period, ...(account_code ? { account_code } : {}) },
  })

// ── 系统管理：备份与导出 ──
export const listBackups = (type: string = 'monthly') =>
  api.get('/system/backups', { params: { type } })

export const createBackup = (type: string = 'monthly', label: string = '') =>
  api.post('/system/backup', null, { params: { type, label } })

export const exportData = (companyId: number, tables: string, format: string = 'csv') =>
  api.get('/system/export', {
    params: { company_id: companyId, tables, format },
    responseType: 'blob',
  }).then(res => {
    const blob = new Blob([res.data], { type: format === 'json' ? 'application/json' : 'text/csv; charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `egp_export.${format === 'json' ? 'json' : 'csv'}`
    a.click()
    URL.revokeObjectURL(url)
  })

// ── 年度审计报告 ──
export const getAuditReport = (companyId: number, year: number) =>
  api.get('/audit-reports/', { params: { company_id: companyId, year } })

export const saveAuditReport = (companyId: number, year: number, data: Record<string, any>) => {
  const formData = new FormData()
  Object.entries(data).forEach(([k, v]) => {
    if (v !== undefined && v !== null) formData.append(k, String(v))
  })
  return api.put('/audit-reports/', formData, { params: { company_id: companyId, year } })
}

export const uploadAuditReportFile = (companyId: number, year: number, file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  return api.post('/audit-reports/upload', formData, {
    params: { company_id: companyId, year },
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export const downloadAuditReportFile = (companyId: number, year: number) =>
  api.get('/audit-reports/download', {
    params: { company_id: companyId, year },
    responseType: 'blob',
  }).then(res => {
    const disposition = res.headers['content-disposition'] || ''
    const match = disposition.match(/filename="?(.+?)"?$/)
    const filename = match ? match[1] : 'audit_report.pdf'
    const blob = new Blob([res.data], { type: 'application/octet-stream' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  })

// ── 协同办公 (Todo) ──
export const listTasks = (companyId: number, status?: string | null, priority?: string | null) =>
  api.get('/todo/', { params: { company_id: companyId, ...(status ? { status } : {}), ...(priority ? { priority } : {}) } })

export const createTask = (companyId: number, title: string, description?: string, priority?: string, due_date?: string) =>
  api.post('/todo/', null, { params: { company_id: companyId, title, ...(description ? { description } : {}), ...(priority ? { priority } : {}), ...(due_date ? { due_date } : {}) } })

export const updateTask = (taskId: number, title?: string, description?: string, status?: string, priority?: string, due_date?: string) =>
  api.put(`/todo/${taskId}`, null, { params: { ...(title !== undefined ? { title } : {}), ...(description !== undefined ? { description } : {}), ...(status !== undefined ? { status } : {}), ...(priority !== undefined ? { priority } : {}), ...(due_date !== undefined ? { due_date } : {}) } })

export const deleteTask = (taskId: number) => api.delete(`/todo/${taskId}`)

// ── 门禁管理 (Access Control) ──
export const listAccessRecords = (companyId: number, page?: number, page_size?: number, direction?: string | null, person_name?: string) =>
  api.get('/access-control/', { params: { company_id: companyId, ...(page ? { page } : {}), ...(page_size ? { page_size } : {}), ...(direction ? { direction } : {}), ...(person_name ? { person_name } : {}) } })

export const createAccessRecord = (companyId: number, person_name: string, direction: string, department?: string, phone?: string, access_point?: string, reason?: string, notes?: string) =>
  api.post('/access-control/', null, { params: { company_id: companyId, person_name, direction, ...(department ? { department } : {}), ...(phone ? { phone } : {}), ...(access_point ? { access_point } : {}), ...(reason ? { reason } : {}), ...(notes ? { notes } : {}) } })

export const deleteAccessRecord = (recordId: number) => api.delete(`/access-control/${recordId}`)

export const exportFullDb = () =>
  api.get('/system/export/full', { responseType: 'blob' }).then(res => {
    const blob = new Blob([res.data], { type: 'application/octet-stream' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'egp_ims_full.db'
    a.click()
    URL.revokeObjectURL(url)
  })
