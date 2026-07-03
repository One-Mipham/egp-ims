import api from './index'

// ── 合同 CRUD ──

export const listContracts = (params: {
  company_id: number
  contract_type?: string
  contract_category?: string
  department_id?: number
  status?: string
  search?: string
}) => api.get('/contracts', { params })

export const getContractCategories = () => api.get('/contracts/categories')

export const getLegalBasisOptions = () => api.get('/contracts/legal-basis')

export const getContract = (id: number) => api.get(`/contracts/${id}`)

export const createContract = (data: {
  company_id: number
  contract_no: string
  contract_type: string
  contract_category?: string
  contract_name?: string
  subject?: string
  legal_basis?: string
  party_a?: string
  party_a_address?: string
  party_a_phone?: string
  party_a_representative?: string
  party_a_signatory?: string
  party_b?: string
  party_b_address?: string
  party_b_phone?: string
  party_b_representative?: string
  party_b_signatory?: string
  amount?: number
  sign_date?: string
  start_date?: string
  end_date?: string
  payment_terms?: string
  force_majeure?: string
  arbitration_venue?: string
  status?: string
  department_id?: number
  owner_id?: number
  notes?: string
}) => api.post('/contracts', data)

export const updateContract = (id: number, data: Record<string, any>) => api.put(`/contracts/${id}`, data)

export const deleteContract = (id: number) => api.delete(`/contracts/${id}`)

// ── 审批流程（非强制） ──

export const reviewContract = (contractId: number) => api.post(`/contracts/${contractId}/review`)

export const approveContract = (contractId: number) => api.post(`/contracts/${contractId}/approve`)

export const sealContract = (contractId: number) => api.post(`/contracts/${contractId}/seal`)

// ── 扫描件 ──

export const uploadContractScan = (contractId: number, file: File) => {
  const fd = new FormData()
  fd.append('file', file)
  return api.post(`/contracts/${contractId}/scan`, fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

// ── 闭环确认 ──

export const confirmContractClosure = (contractId: number) => api.post(`/contracts/${contractId}/closure-confirm`)

// ── 统计 ──

export const getContractStats = (companyId: number) =>
  api.get('/contracts/stats', { params: { company_id: companyId } })
