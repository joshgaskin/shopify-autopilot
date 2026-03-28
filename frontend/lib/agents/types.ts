import type { Product, Order, InventoryLevel, LiveEvent } from '../types'

// ── Shared Agent Types ──────────────────────────────────────────────────────

export type AgentName = 'Rick' | 'Hank' | 'Ron' | 'Marty' | 'Marcus'

export type AgentStatus = 'active' | 'idle' | 'evaluating'

export interface AgentState {
  name: AgentName
  domain: string
  emoji: string
  avatar?: string
  status: AgentStatus
  lastAction: string | null
  actionCount: number
}

export type ActionType =
  | 'stockout_alert'
  | 'health_issue'
  | 'anomaly_detected'
  | 'product_scored'
  | 'reorder_recommendation'
  | 'discount_created'
  | 'slow_mover_detected'
  | 'widget_deployed'
  | 'daily_insight'
  | 'email_drafted'
  | 'segment_analyzed'
  | 'product_tagged'
  | 'po_created'
  | 'reorder_covered'

export interface AgentAction {
  id: string
  timestamp: string
  agent: AgentName
  type: ActionType
  title: string
  details: string
  status: 'success' | 'failed' | 'pending' | 'reverted'
  productId?: string
}

export interface AgentResult {
  agent: AgentName
  actions: AgentAction[]
}

// ── Scored Product (output of intelligence layer) ───────────────────────────

export type Tier = 'Core' | 'Strong' | 'Slow' | 'Exit'

export interface ScoredProduct {
  id: string
  title: string
  handle: string
  status: string
  price: number
  inventory: number
  score: number
  tier: Tier
  velocity: number        // units per day (7d)
  daysLeft: number        // days until stockout at current velocity
  trend: 'growing' | 'stable' | 'declining'
  trendRatio: number
  revenueTotal: number
  image: string | null
  variants: { id: string; title: string; sku: string; inventory_quantity: number; price: number }[]
}

// ── Store State (shared across agents) ──────────────────────────────────────

export interface StoreState {
  products: Product[]
  orders: Order[]
  inventory: InventoryLevel[]
  scored: ScoredProduct[]
  hourlyBaseline: { hour: number; avg_orders: number; avg_revenue: number }[]
}

// ── Customer Segments ───────────────────────────────────────────────────────

export type SegmentName = 'Champions' | 'Loyal' | 'At Risk' | 'New' | 'Lost'

export interface SegmentedCustomer {
  id: string
  email: string
  name: string
  segment: SegmentName
  recencyScore: number
  frequencyScore: number
  monetaryScore: number
  rfmScore: number
  orderCount: number
  totalSpent: number
  daysSinceLastOrder: number
}
