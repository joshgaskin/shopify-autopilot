import { api } from '../lib/api'
import { useApi } from './useApi'

export function useProducts(params?: { page?: number; search?: string; status?: string }) {
  return useApi(
    () => api.getProducts(params),
    [params?.page, params?.search, params?.status]
  )
}
