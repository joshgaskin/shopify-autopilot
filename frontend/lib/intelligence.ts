/**
 * Intelligence Layer — Product scoring, velocity, stockout prediction, discount suggestions.
 *
 * Ported from Plus2's production scoring system (src/lib/products/scoring.ts).
 * Pure functions — no DB, no API calls, just math on arrays.
 */

import type { Product, Order, InventoryLevel } from './types'
import type { ScoredProduct, Tier, SegmentedCustomer, SegmentName } from './agents/types'
import type { Customer } from './types'

// ── Power Scale ─────────────────────────────────────────────────────────────
// Fourth-root scaling so $1K revenue scores ~50 while the top product scores 100.
// Sub-$100 products score low but the curve is gentler than square root.

function powerScale(value: number, maxValue: number): number {
  if (value <= 0 || maxValue <= 0) return 0
  return Math.min(100, Math.round(Math.pow(value / maxValue, 0.25) * 100))
}

function getTier(score: number): Tier {
  if (score >= 70) return 'Core'
  if (score >= 55) return 'Strong'
  if (score >= 40) return 'Slow'
  return 'Exit'
}

// ── Scoring ─────────────────────────────────────────────────────────────────

export function scoreProducts(
  products: Product[],
  orders: Order[],
  inventory: InventoryLevel[]
): ScoredProduct[] {
  // Build order line-item aggregates per product
  const productSales = new Map<string, { units: number; revenue: number; recentUnits: number; priorUnits: number }>()

  const now = Date.now()
  const sevenDaysAgo = now - 7 * 24 * 60 * 60 * 1000
  const fourteenDaysAgo = now - 14 * 24 * 60 * 60 * 1000

  for (const order of orders) {
    if (order.financial_status === 'refunded') continue
    const orderTime = new Date(order.processed_at || order.created_at).getTime()

    for (const item of order.line_items) {
      // Match line item to product by title (Shopify line items don't carry product_id)
      const product = products.find(
        (p) => p.title === item.title || p.variants.some((v) => v.title === item.variant_title)
      )
      if (!product) continue

      const existing = productSales.get(product.id) || { units: 0, revenue: 0, recentUnits: 0, priorUnits: 0 }
      existing.units += item.quantity
      existing.revenue += item.price * item.quantity

      if (orderTime >= sevenDaysAgo) {
        existing.recentUnits += item.quantity
      } else if (orderTime >= fourteenDaysAgo) {
        existing.priorUnits += item.quantity
      }

      productSales.set(product.id, existing)
    }
  }

  // Build inventory lookup (sum across variants)
  const inventoryMap = new Map<string, number>()
  for (const level of inventory) {
    const current = inventoryMap.get(level.product_id) || 0
    inventoryMap.set(level.product_id, current + level.quantity)
  }

  // Also sum from product.variants as fallback
  for (const product of products) {
    if (!inventoryMap.has(product.id)) {
      inventoryMap.set(product.id, product.inventory_total)
    }
  }

  // Pre-compute maximums for power-scale normalization
  const maxRevenue = Math.max(1, ...Array.from(productSales.values()).map((s) => s.revenue))
  const maxVelocity = Math.max(1, ...Array.from(productSales.values()).map((s) => s.recentUnits / 7))

  const scored: ScoredProduct[] = products.map((product) => {
    const sales = productSales.get(product.id) || { units: 0, revenue: 0, recentUnits: 0, priorUnits: 0 }
    const stock = inventoryMap.get(product.id) ?? product.inventory_total

    // Velocity: units sold per day over last 7 days
    const velocity = Math.round((sales.recentUnits / 7) * 100) / 100

    // Days until stockout
    const daysLeft = velocity > 0 ? Math.round(stock / velocity) : stock > 0 ? 999 : 0

    // Trend: compare last 7d vs prior 7d
    let trend: 'growing' | 'stable' | 'declining' = 'stable'
    let trendRatio = 1.0
    if (sales.priorUnits > 0) {
      trendRatio = Math.round((sales.recentUnits / sales.priorUnits) * 100) / 100
      if (trendRatio > 1.15) trend = 'growing'
      else if (trendRatio < 0.85) trend = 'declining'
    } else if (sales.recentUnits > 0) {
      trend = 'growing'
      trendRatio = 2.0
    }

    // Score components (each 0-100)
    const revenueScore = powerScale(sales.revenue, maxRevenue)       // 30%
    const velocityScore = powerScale(velocity, maxVelocity > 0 ? maxVelocity : 1)  // 30%
    const stockHealthScore = daysLeft <= 0 ? 0 : daysLeft <= 3 ? 20 : daysLeft <= 7 ? 50 : daysLeft <= 14 ? 70 : 90  // 20%
    const trendScore = Math.min(100, Math.max(0, Math.round(50 + (trendRatio - 1) * 25)))  // 20%

    const compositeScore = Math.round(
      revenueScore * 0.3 +
      velocityScore * 0.3 +
      stockHealthScore * 0.2 +
      trendScore * 0.2
    )

    const tier = getTier(compositeScore)

    return {
      id: product.id,
      title: product.title,
      handle: product.handle,
      status: product.status,
      price: product.price_min,
      inventory: stock,
      score: compositeScore,
      tier,
      velocity,
      daysLeft,
      trend,
      trendRatio,
      revenueTotal: Math.round(sales.revenue * 100) / 100,
      image: product.featured_image_url,
      variants: product.variants.map((v) => ({
        id: v.id,
        title: v.title,
        sku: v.sku,
        inventory_quantity: v.inventory_quantity,
        price: v.price,
      })),
    }
  })

  // Sort by days-until-stockout ascending (most urgent first), then by score descending
  scored.sort((a, b) => {
    if (a.daysLeft <= 7 && b.daysLeft > 7) return -1
    if (b.daysLeft <= 7 && a.daysLeft > 7) return 1
    return b.score - a.score
  })

  return scored
}

// ── Slow Mover Detection ────────────────────────────────────────────────────

export function detectSlowMovers(scored: ScoredProduct[]): ScoredProduct[] {
  return scored.filter(
    (p) => p.trend === 'declining' && p.inventory > 0 && p.daysLeft > 14 && p.tier !== 'Core'
  )
}

// ── Stockout Risk Detection ─────────────────────────────────────────────────

export function detectStockoutRisk(scored: ScoredProduct[]): ScoredProduct[] {
  return scored.filter((p) => p.daysLeft <= 3 && p.daysLeft > 0 && p.velocity > 0)
}

// ── Discount Suggestions ────────────────────────────────────────────────────

export function suggestDiscounts(slowMovers: ScoredProduct[]): { product: ScoredProduct; discountPct: number }[] {
  return slowMovers.map((product) => {
    // Deeper discount for worse trend + lower tier
    let pct = 10
    if (product.trendRatio < 0.5) pct = 30
    else if (product.trendRatio < 0.7) pct = 20
    else if (product.trendRatio < 0.85) pct = 15

    // Bump up for Exit tier
    if (product.tier === 'Exit') pct = Math.min(40, pct + 10)

    return { product, discountPct: pct }
  })
}

// ── Health Checks (from Plus2's shop-health.ts) ─────────────────────────────

export interface HealthIssue {
  productId: string
  productTitle: string
  issue: string
  severity: 'critical' | 'warning' | 'info'
}

export function checkProductHealth(products: Product[], inventory: InventoryLevel[]): HealthIssue[] {
  const issues: HealthIssue[] = []

  for (const product of products) {
    // Missing image
    if (!product.featured_image_url) {
      issues.push({
        productId: product.id,
        productTitle: product.title,
        issue: 'Missing product image',
        severity: 'warning',
      })
    }

    // Active with zero stock
    if (product.status === 'active' && product.inventory_total <= 0) {
      issues.push({
        productId: product.id,
        productTitle: product.title,
        issue: 'Active product with zero stock',
        severity: 'critical',
      })
    }

    // Draft with stock (should be published)
    if (product.status === 'draft' && product.inventory_total > 0) {
      issues.push({
        productId: product.id,
        productTitle: product.title,
        issue: 'Draft product has stock — consider publishing',
        severity: 'info',
      })
    }

    // Price at $0
    if (product.price_min <= 0 && product.status === 'active') {
      issues.push({
        productId: product.id,
        productTitle: product.title,
        issue: 'Active product with $0 price',
        severity: 'critical',
      })
    }
  }

  return issues
}

// ── RFM Customer Segmentation ───────────────────────────────────────────────

export function segmentCustomers(customers: Customer[], orders: Order[]): SegmentedCustomer[] {
  const now = Date.now()

  // Build per-customer aggregates from orders
  const customerOrders = new Map<string, { lastOrderAt: number; orderCount: number; totalSpent: number }>()

  for (const order of orders) {
    if (!order.customer_id || order.financial_status === 'refunded') continue
    const existing = customerOrders.get(order.customer_id) || { lastOrderAt: 0, orderCount: 0, totalSpent: 0 }
    const orderTime = new Date(order.processed_at || order.created_at).getTime()
    existing.lastOrderAt = Math.max(existing.lastOrderAt, orderTime)
    existing.orderCount += 1
    existing.totalSpent += order.total_price
    customerOrders.set(order.customer_id, existing)
  }

  // Compute RFM values
  const rfmData = customers.map((c) => {
    const agg = customerOrders.get(c.id) || {
      lastOrderAt: c.last_order_at ? new Date(c.last_order_at).getTime() : 0,
      orderCount: c.orders_count,
      totalSpent: c.total_spent,
    }
    const daysSinceLastOrder = agg.lastOrderAt > 0 ? Math.floor((now - agg.lastOrderAt) / (1000 * 60 * 60 * 24)) : 999
    return { customer: c, daysSinceLastOrder, orderCount: agg.orderCount, totalSpent: agg.totalSpent }
  })

  // Quintile scoring
  const recencyValues = rfmData.map((d) => d.daysSinceLastOrder).sort((a, b) => a - b)
  const frequencyValues = rfmData.map((d) => d.orderCount).sort((a, b) => a - b)
  const monetaryValues = rfmData.map((d) => d.totalSpent).sort((a, b) => a - b)

  function quintile(sortedVals: number[], value: number, invert = false): number {
    if (sortedVals.length === 0) return 3
    const idx = sortedVals.findIndex((v) => v >= value)
    const rank = idx === -1 ? sortedVals.length : idx
    const pct = rank / sortedVals.length
    const score = Math.min(5, Math.max(1, Math.ceil(pct * 5)))
    return invert ? 6 - score : score
  }

  return rfmData.map(({ customer, daysSinceLastOrder, orderCount, totalSpent }) => {
    // Recency: lower days = higher score (invert)
    const recencyScore = quintile(recencyValues, daysSinceLastOrder, true)
    const frequencyScore = quintile(frequencyValues, orderCount)
    const monetaryScore = quintile(monetaryValues, totalSpent)
    const rfmScore = Math.round((recencyScore + frequencyScore + monetaryScore) / 3 * 10) / 10

    let segment: SegmentName
    if (recencyScore >= 4 && frequencyScore >= 4 && monetaryScore >= 4) {
      segment = 'Champions'
    } else if (frequencyScore >= 3 && monetaryScore >= 3 && recencyScore >= 3) {
      segment = 'Loyal'
    } else if (recencyScore <= 2 && frequencyScore >= 3) {
      segment = 'At Risk'
    } else if (recencyScore >= 4 && frequencyScore <= 2) {
      segment = 'New'
    } else {
      segment = 'Lost'
    }

    return {
      id: customer.id,
      email: customer.email,
      name: `${customer.first_name} ${customer.last_name}`.trim(),
      segment,
      recencyScore,
      frequencyScore,
      monetaryScore,
      rfmScore,
      orderCount,
      totalSpent,
      daysSinceLastOrder,
    }
  })
}
