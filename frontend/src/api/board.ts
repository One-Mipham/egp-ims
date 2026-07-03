import api from './index'

export interface BoardFilingData {
  id: number
  company_id: number
  doc_type: string
  doc_subtype?: string | null
  title: string
  target_org?: string | null
  deadline?: string | null
  submit_date?: string | null
  status: string
  approver?: string | null
  contact_person?: string | null
  contact_method?: string | null
  party_name?: string | null
  summary?: string | null
  content?: string | null
  file_path?: string | null
  extra_data?: any
  created_by?: number | null
  created_at?: string
  updated_at?: string
}

export interface BoardFilingCreateData {
  company_id: number
  doc_type: string
  doc_subtype?: string | null
  title: string
  target_org?: string | null
  deadline?: string | null
  submit_date?: string | null
  status?: string
  approver?: string | null
  contact_person?: string | null
  contact_method?: string | null
  party_name?: string | null
  summary?: string | null
  content?: string | null
  file_path?: string | null
  extra_data?: any
}

export interface BoardFilingUpdateData {
  doc_type?: string
  doc_subtype?: string | null
  title?: string
  target_org?: string | null
  deadline?: string | null
  submit_date?: string | null
  status?: string
  approver?: string | null
  contact_person?: string | null
  contact_method?: string | null
  party_name?: string | null
  summary?: string | null
  content?: string | null
  file_path?: string | null
  extra_data?: any
}

export interface BoardShareholderData {
  id: number
  company_id: number
  name: string
  share_type: string
  share_count: number
  share_ratio: number
  contact_person?: string | null
  contact_phone?: string | null
  contact_email?: string | null
  entry_date?: string | null
  notes?: string | null
  status: string
  created_at?: string
  updated_at?: string
}

export interface BoardShareholderCreateData {
  company_id: number
  name: string
  share_type?: string
  share_count?: number
  share_ratio?: number
  contact_person?: string | null
  contact_phone?: string | null
  contact_email?: string | null
  entry_date?: string | null
  notes?: string | null
  status?: string
}

export interface BoardShareholderUpdateData {
  name?: string
  share_type?: string
  share_count?: number
  share_ratio?: number
  contact_person?: string | null
  contact_phone?: string | null
  contact_email?: string | null
  entry_date?: string | null
  notes?: string | null
  status?: string
}

export interface CockpitLight {
  label: string
  status: string
}

export interface BoardCockpitData {
  lights: CockpitLight[]
}

// ── 驾驶舱 ──
export const getCockpitLights = (companyId: number) =>
  api.get('/board/cockpit-lights', { params: { company_id: companyId } })

// ── BoardFiling ──
export const listFilings = (companyId: number, docType?: string, docSubtype?: string) =>
  api.get('/board/filings', {
    params: {
      company_id: companyId,
      ...(docType ? { doc_type: docType } : {}),
      ...(docSubtype ? { doc_subtype: docSubtype } : {}),
    },
  })

export const getFiling = (id: number) => api.get(`/board/filings/${id}`)
export const createFiling = (data: BoardFilingCreateData) => api.post('/board/filings', data)
export const updateFiling = (id: number, data: BoardFilingUpdateData) => api.put(`/board/filings/${id}`, data)
export const deleteFiling = (id: number) => api.delete(`/board/filings/${id}`)
export const upsertFiling = (data: BoardFilingCreateData) => api.post('/board/filings/upsert', data)

// ── BoardShareholder ──
export const listShareholders = (companyId: number) =>
  api.get('/board/shareholders', { params: { company_id: companyId } })

export const createShareholder = (data: BoardShareholderCreateData) => api.post('/board/shareholders', data)
export const updateShareholder = (id: number, data: BoardShareholderUpdateData) =>
  api.put(`/board/shareholders/${id}`, data)
export const deleteShareholder = (id: number) => api.delete(`/board/shareholders/${id}`)
