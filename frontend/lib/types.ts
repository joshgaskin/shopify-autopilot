export interface Product {
  id: string
  title: string
  handle: string
  status: 'active' | 'draft' | 'archived'
  vendor: string
  product_type: string
  price_min: number
  price_max: number
  variants: Variant[]
  collections: string[]
  featured_image_url: string | null
  inventory_total: number
  created_at: string
  updated_at: string
}

export interface Variant {
  id: string
  title: string
  price: number
  sku: string
  inventory_quantity: number
}

export interface Order {
  id: string
  order_number: string
  total_price: number
  subtotal_price: number
  total_discounts: number
  total_tax: number
  currency: string
  financial_status: 'paid' | 'pending' | 'refunded' | 'partially_refunded'
  fulfillment_status: 'fulfilled' | 'partial' | 'unfulfilled' | null
  line_items: LineItem[]
  customer_id: string | null
  customer_email: string | null
  customer_name: string | null
  discount_codes: string[]
  landing_site: string | null
  referring_site: string | null
  processed_at: string
  created_at: string
  is_simulated: boolean
}

export interface LineItem {
  title: string
  variant_title: string
  quantity: number
  price: number
}

export interface Customer {
  id: string
  email: string
  first_name: string
  last_name: string
  orders_count: number
  total_spent: number
  tags: string[]
  created_at: string
  last_order_at: string | null
}

export interface InventoryLevel {
  variant_id: string
  product_id: string
  product_title: string
  variant_title: string
  sku: string
  quantity: number
  location: string
}

export interface RevenueDataPoint {
  date: string
  revenue: number
  orders: number
  aov: number
}

export interface TopProduct {
  id: string
  title: string
  revenue: number
  units_sold: number
}

export interface StoreInfo {
  domain: string
  name: string
  currency: string
  product_count: number
  order_count: number
  customer_count: number
  last_sync_at: string | null
}

export interface LiveEvent {
  id: string
  event_type: 'new_order' | 'product_update' | 'inventory_change' | 'refund_issued' | 'customer_created'
  payload: Record<string, any>
  created_at: string
}

export interface PaginatedResponse<T> {
  data: T[]
  total: number
  page: number
  limit: number
  pages: number
}
