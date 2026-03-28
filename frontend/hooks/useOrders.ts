import { api } from '../lib/api'
import { useApi } from './useApi'

export function useOrders(params?: { page?: number; limit?: number; status?: string; since?: string }) {
  return useApi(
    () => api.getOrders(params),
    [params?.page, params?.limit, params?.status, params?.since]
  )
}
