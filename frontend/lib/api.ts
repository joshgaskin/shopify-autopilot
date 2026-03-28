import { API_BASE } from './constants'
import type {
  Product,
  Order,
  Customer,
  StoreInfo,
  InventoryLevel,
  RevenueDataPoint,
  TopProduct,
  PaginatedResponse,
  LiveEvent,
} from './types'

class ApiClient {
  private baseUrl: string

  constructor() {
    this.baseUrl = API_BASE
  }

  private async fetch<T>(path: string, options?: RequestInit): Promise<T> {
    const res = await fetch(`${this.baseUrl}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    })
    if (!res.ok) {
      throw new Error(`API Error: ${res.status} ${res.statusText}`)
    }
    return res.json()
  }

  // Store
  async getStore(): Promise<StoreInfo> {
    return this.fetch('/store')
  }

  // Products
  async getProducts(params?: {
    page?: number
    limit?: number
    search?: string
    status?: string
  }): Promise<PaginatedResponse<Product>> {
    const qs = new URLSearchParams()
    if (params?.page) qs.set('page', String(params.page))
    if (params?.limit) qs.set('limit', String(params.limit))
    if (params?.search) qs.set('search', params.search)
    if (params?.status) qs.set('status', params.status)
    return this.fetch(`/products?${qs}`)
  }

  async getProduct(id: string): Promise<Product> {
    return this.fetch(`/products/${encodeURIComponent(id)}`)
  }

  // Orders
  async getOrders(params?: {
    page?: number
    limit?: number
    status?: string
    since?: string
  }): Promise<PaginatedResponse<Order>> {
    const qs = new URLSearchParams()
    if (params?.page) qs.set('page', String(params.page))
    if (params?.limit) qs.set('limit', String(params.limit))
    if (params?.status) qs.set('status', params.status)
    if (params?.since) qs.set('since', params.since)
    return this.fetch(`/orders?${qs}`)
  }

  async getOrder(id: string): Promise<Order> {
    return this.fetch(`/orders/${encodeURIComponent(id)}`)
  }

  // Customers
  async getCustomers(params?: {
    page?: number
    limit?: number
    search?: string
  }): Promise<PaginatedResponse<Customer>> {
    const qs = new URLSearchParams()
    if (params?.page) qs.set('page', String(params.page))
    if (params?.limit) qs.set('limit', String(params.limit))
    if (params?.search) qs.set('search', params.search)

    return this.fetch(`/customers?${qs}`)
  }

  // Inventory
  async getInventory(): Promise<InventoryLevel[]> {
    return this.fetch('/inventory')
  }

  // Analytics
  async getRevenue(
    period: '7d' | '30d' | '90d' = '30d'
  ): Promise<{ series: RevenueDataPoint[] }> {
    return this.fetch(`/analytics/revenue?period=${period}`)
  }

  async getTopProducts(limit = 10): Promise<{ products: TopProduct[] }> {
    return this.fetch(`/analytics/top-products?limit=${limit}`)
  }

  async getHourlyPatterns(): Promise<{
    hours: { hour: number; avg_orders: number; avg_revenue: number }[]
  }> {
    return this.fetch('/analytics/hourly-patterns')
  }

  async getCustomerCohorts(): Promise<{
    cohorts: { week: string; customers: number; retention_rates: number[] }[]
  }> {
    return this.fetch('/analytics/customer-cohorts')
  }

  // Events
  async getEventHistory(limit = 100): Promise<LiveEvent[]> {
    return this.fetch(`/events/history?limit=${limit}`)
  }

  // Actions
  async createDraftOrder(
    lineItems: { variant_id: string; quantity: number }[]
  ): Promise<any> {
    return this.fetch('/orders/draft', {
      method: 'POST',
      body: JSON.stringify({ line_items: lineItems }),
    })
  }

  async createDiscount(code: string, percentage: number): Promise<any> {
    return this.fetch('/discounts', {
      method: 'POST',
      body: JSON.stringify({ code, percentage }),
    })
  }

  async sendEmail(to: string, subject: string, html: string): Promise<any> {
    return this.fetch('/notifications/email', {
      method: 'POST',
      body: JSON.stringify({ to, subject, html }),
    })
  }

  async injectStorefrontScript(src: string): Promise<any> {
    return this.fetch('/storefront/inject', {
      method: 'POST',
      body: JSON.stringify({ src }),
    })
  }

  // Shopify passthrough (advanced)
  async shopifyGraphQL(
    query: string,
    variables?: Record<string, any>
  ): Promise<any> {
    return this.fetch('/shopify/graphql', {
      method: 'POST',
      body: JSON.stringify({ query, variables }),
    })
  }
}

export const api = new ApiClient()
