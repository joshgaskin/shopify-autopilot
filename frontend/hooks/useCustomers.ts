import { api } from '../lib/api'
import { useApi } from './useApi'

export function useCustomers(params?: { page?: number; limit?: number; search?: string }) {
  return useApi(
    () => api.getCustomers(params),
    [params?.page, params?.limit, params?.search]
  )
}
