import { api } from '../lib/api'
import { useApi } from './useApi'

export function useRevenue(period: '7d' | '30d' | '90d' = '30d') {
  return useApi(() => api.getRevenue(period), [period])
}

export function useTopProducts(limit = 10) {
  return useApi(() => api.getTopProducts(limit), [limit])
}
