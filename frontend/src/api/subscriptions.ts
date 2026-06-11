import api from './index'

export interface SubscriptionPlan {
  id: number
  name: string
  slug: string
  description: string
  billing_cycle: string
  price_cny: number
  price_usd: number
  modules: string[]
}

export const listPlans = () => api.get('/subscriptions/plans')

export const getCurrentSubscription = (companyId: number) =>
  api.get('/subscriptions/current', { params: { company_id: companyId } })

export const activateTrial = (companyId: number) =>
  api.post('/subscriptions/activate-trial', null, { params: { company_id: companyId } })

export const subscribe = (data: { company_id: number; plan_slug: string; billing_cycle: string }) =>
  api.post('/subscriptions/subscribe', data)

export const renewSubscription = (companyId: number) =>
  api.post('/subscriptions/renew', null, { params: { company_id: companyId } })

export const cancelSubscription = (companyId: number) =>
  api.post('/subscriptions/cancel', null, { params: { company_id: companyId } })

export const getBillingHistory = (companyId: number) =>
  api.get('/subscriptions/history', { params: { company_id: companyId } })
