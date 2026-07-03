import api from './index'

// ── TaxDeclaration CRUD ──

export interface TaxDeclarationParams {
  company_id: number
  tax_type?: string
  status?: string
  period_start?: string
  period_end?: string
}

export const listDeclarations = (params: TaxDeclarationParams) => api.get('/taxes/declarations', { params })

export const getDeclaration = (id: number) => api.get(`/taxes/declarations/${id}`)

export const createDeclaration = (data: Record<string, any>) => api.post('/taxes/declarations', data)

export const updateDeclaration = (id: number, data: Record<string, any>) => api.put(`/taxes/declarations/${id}`, data)

export const deleteDeclaration = (id: number) => api.delete(`/taxes/declarations/${id}`)

export const getDeclarationsSummary = (params: { company_id: number; period_start?: string; period_end?: string }) =>
  api.get('/taxes/declarations/summary', { params })

// ── TaxInvoice CRUD ──

export interface TaxInvoiceParams {
  company_id: number
  invoice_type?: string
  status?: string
  counterparty_id?: number
  date_from?: string
  date_to?: string
}

export const listInvoices = (params: TaxInvoiceParams) => api.get('/taxes/invoices', { params })

export const getInvoice = (id: number) => api.get(`/taxes/invoices/${id}`)

export const createInvoice = (data: Record<string, any>) => api.post('/taxes/invoices', data)

export const updateInvoice = (id: number, data: Record<string, any>) => api.put(`/taxes/invoices/${id}`, data)

export const deleteInvoice = (id: number) => api.delete(`/taxes/invoices/${id}`)

export const getInvoicesSummary = (params: {
  company_id: number
  invoice_type?: string
  date_from?: string
  date_to?: string
}) => api.get('/taxes/invoices/summary', { params })
