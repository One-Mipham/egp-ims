import api from './index'

// ── 招标项目 CRUD ──

export const listTenderProjects = (params: {
  company_id: number
  tender_type?: string
  procurement_category?: string
  department_id?: number
  status?: string
  search?: string
}) => api.get('/bids/tender-projects', { params })

export const getTenderOptions = () => api.get('/bids/tender-projects/options')

export const getTenderProject = (id: number) => api.get(`/bids/tender-projects/${id}`)

export const createTenderProject = (data: Record<string, any>) => api.post('/bids/tender-projects', data)

export const updateTenderProject = (id: number, data: Record<string, any>) =>
  api.put(`/bids/tender-projects/${id}`, data)

export const deleteTenderProject = (id: number) => api.delete(`/bids/tender-projects/${id}`)

export const reviewTenderProject = (id: number) => api.post(`/bids/tender-projects/${id}/review`)

export const approveTenderProject = (id: number) => api.post(`/bids/tender-projects/${id}/approve`)

// ── 投标登记 CRUD ──

export const listBidSubmissions = (params: {
  company_id: number
  bid_type?: string
  bond_status?: string
  department_id?: number
  status?: string
  search?: string
}) => api.get('/bids/submissions', { params })

export const getBidOptions = () => api.get('/bids/submissions/options')

export const getBidSubmission = (id: number) => api.get(`/bids/submissions/${id}`)

export const createBidSubmission = (data: Record<string, any>) => api.post('/bids/submissions', data)

export const updateBidSubmission = (id: number, data: Record<string, any>) => api.put(`/bids/submissions/${id}`, data)

export const deleteBidSubmission = (id: number) => api.delete(`/bids/submissions/${id}`)

// ── 统计 ──

export const getBidStats = (companyId: number) => api.get('/bids/stats', { params: { company_id: companyId } })

// ── 例外事项 CRUD ──

export const listExceptionEvents = (params: {
  company_id: number
  target_type?: string
  exception_type?: string
  target_id?: number
  status?: string
  search?: string
}) => api.get('/bids/exceptions', { params })

export const getExceptionOptions = (target_type?: string) =>
  api.get('/bids/exceptions/options', { params: target_type ? { target_type } : {} })

export const getExceptionEvent = (id: number) => api.get(`/bids/exceptions/${id}`)

export const createExceptionEvent = (data: Record<string, any>) => api.post('/bids/exceptions', data)

export const updateExceptionEvent = (id: number, data: Record<string, any>) => api.put(`/bids/exceptions/${id}`, data)

export const deleteExceptionEvent = (id: number) => api.delete(`/bids/exceptions/${id}`)

export const reviewExceptionEvent = (id: number) => api.post(`/bids/exceptions/${id}/review`)

export const approveExceptionEvent = (id: number) => api.post(`/bids/exceptions/${id}/approve`)

export const rejectExceptionEvent = (id: number) => api.post(`/bids/exceptions/${id}/reject`)

// ── 强制跳过审批 ──

export const bypassTenderProject = (id: number, reason: string) =>
  api.post(`/bids/tender-projects/${id}/bypass`, { reason })

export const bypassExceptionEvent = (id: number, reason: string) =>
  api.post(`/bids/exceptions/${id}/bypass`, { reason })
