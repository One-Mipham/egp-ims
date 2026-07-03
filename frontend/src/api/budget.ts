import api from './index'

export interface BudgetItemData {
  account_code: string
  department_id?: number | null
  month: string
  amount: number
}

export interface BudgetItemResponse extends BudgetItemData {
  id: number
  budget_id: number
}

export interface BudgetData {
  id: number
  company_id: number
  name: string
  year: number
  status: string
  created_by?: number | null
  created_at?: string
  items: BudgetItemResponse[]
}

export interface BudgetCreateData {
  company_id: number
  name: string
  year: number
  items?: BudgetItemData[]
}

export interface BudgetUpdateData {
  name?: string
  status?: string
  items?: BudgetItemData[]
}

export const listBudgets = (companyId: number, year?: number) =>
  api.get('/budgets', { params: { company_id: companyId, ...(year ? { year } : {}) } })

export const getBudget = (id: number) => api.get(`/budgets/${id}`)

export const createBudget = (data: BudgetCreateData) => api.post('/budgets', data)

export const updateBudget = (id: number, data: BudgetUpdateData) => api.put(`/budgets/${id}`, data)

export const deleteBudget = (id: number) => api.delete(`/budgets/${id}`)
