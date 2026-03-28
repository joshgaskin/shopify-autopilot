import { api } from '../lib/api'
import { useApi } from './useApi'

export function useProducts(params?: { page?: number; limit?: number; search?: string; status?: string }) {
  return useApi(
    () => api.getProducts(params),
    [params?.page, params?.limit, params?.search, params?.status]
  )
}
