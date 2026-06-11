import api from './index'

// ── 费用项目 ──

export const listExpenseItems = (companyId: number) =>
  api.get('/expenses/items', { params: { company_id: companyId } })

export const createExpenseItem = (data: {
  company_id: number; code: string; name: string
  parent_code?: string; tax_rate?: number; is_active?: boolean
}) => api.post('/expenses/items', data)

export const updateExpenseItem = (itemId: number, data: Record<string, any>) =>
  api.put(`/expenses/items/${itemId}`, data)

// ── 费用标准 ──

export const listExpensePolicies = (companyId: number) =>
  api.get('/expenses/policies', { params: { company_id: companyId } })

export const createExpensePolicy = (data: {
  company_id: number; expense_item_id?: number; country?: string
  region?: string; department_id?: number; position_level?: number
  policy_type: string; max_amount: number; currency?: string
  effective_from: string; effective_to?: string; notes?: string
}) => api.post('/expenses/policies', data)

export const updateExpensePolicy = (policyId: number, data: Record<string, any>) =>
  api.put(`/expenses/policies/${policyId}`, data)

export const deleteExpensePolicy = (policyId: number) =>
  api.delete(`/expenses/policies/${policyId}`)

// ── 报销单 ──

export const listExpenseReports = (companyId: number, status?: string) =>
  api.get('/expenses/reports', { params: { company_id: companyId, status } })

export const createExpenseReport = (data: {
  company_id: number; expense_date: string; department_id?: number
  notes?: string; items: { row_seq: number; expense_item_id?: number
  date: string; amount: number; description?: string; receipt_count: number }[]
}) => api.post('/expenses/reports', data)

export const getExpenseReport = (reportId: number) =>
  api.get(`/expenses/reports/${reportId}`)

export const updateExpenseReport = (reportId: number, data: {
  expense_date?: string; department_id?: number; notes?: string
  items?: { row_seq: number; expense_item_id?: number
  date: string; amount: number; description?: string; receipt_count: number }[]
}) => api.put(`/expenses/reports/${reportId}`, data)

export const getReportItems = (reportId: number) =>
  api.get(`/expenses/reports/${reportId}/items`)

// ── 审批操作 ──

export const submitReport = (reportId: number) =>
  api.post(`/expenses/reports/${reportId}/submit`)

export const approveReport = (reportId: number, comment?: string) =>
  api.post(`/expenses/reports/${reportId}/approve`, { comment })

export const rejectReport = (reportId: number, comment?: string) =>
  api.post(`/expenses/reports/${reportId}/reject`, { comment })

export const payReport = (reportId: number) =>
  api.post(`/expenses/reports/${reportId}/pay`)

export const cancelReport = (reportId: number) =>
  api.post(`/expenses/reports/${reportId}/cancel`)

// ── 借款管理 ──

export const listExpenseLoans = (companyId: number) =>
  api.get('/expenses/loans', { params: { company_id: companyId } })

export const createExpenseLoan = (data: {
  company_id: number; loan_date: string; amount: number
  reason?: string; department_id?: number
  expected_repay_date?: string; notes?: string
}) => api.post('/expenses/loans', data)

export const approveLoan = (loanId: number) =>
  api.post(`/expenses/loans/${loanId}/approve`)

export const repayLoan = (loanId: number, amount: number, notes?: string) =>
  api.post(`/expenses/loans/${loanId}/repay`, { amount, notes })

// ── 附件 ──

export const listAttachments = (reportId: number) =>
  api.get(`/expenses/reports/${reportId}/attachments`)

export const uploadAttachment = (reportId: number, file: File, category: string, docNumber: string) => {
  const form = new FormData()
  form.append('report_id', String(reportId))
  form.append('file', file)
  form.append('category', category)
  form.append('doc_number', docNumber)
  return api.post('/expenses/attachments', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export const deleteAttachment = (attachmentId: number) =>
  api.delete(`/expenses/attachments/${attachmentId}`)

// ── 统计 ──

export const expenseStats = (companyId: number, startDate?: string, endDate?: string) =>
  api.get('/expenses/stats', { params: { company_id: companyId, start_date: startDate, end_date: endDate } })

// ── 强制跳过审批 ──

export const bypassReport = (id: number, reason: string) =>
  api.post(`/expenses/reports/${id}/bypass`, { reason })

export const bypassLoan = (id: number, reason: string) =>
  api.post(`/expenses/loans/${id}/bypass`, { reason })
