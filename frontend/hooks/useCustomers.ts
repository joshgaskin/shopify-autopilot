import { api } from '../lib/api'
import { useApi } from './useApi'

export function useCustomers(params?: { page?: number; search?: string }) {
  return useApi(
    () => api.getCustomers(params),
    [params?.page, params?.search]
  )
}
