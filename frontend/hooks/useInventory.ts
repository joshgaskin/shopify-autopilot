import { api } from '../lib/api'
import { useApi } from './useApi'

export function useInventory() {
  return useApi(() => api.getInventory(), [])
}
