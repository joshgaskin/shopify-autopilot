/**
 * Hank — Supply Chain Agent
 *
 * Domain: Inventory scoring, demand forecasting, reorder recommendations
 * Triggers: Page load (full scan)
 * Ported from: scoring.ts, forecasting.ts
 */

import { scoreProducts } from '../intelligence'
import type { Product, Order, InventoryLevel } from '../types'
import type { AgentAction, AgentResult, ScoredProduct } from './types'

let actionCounter = 0
function nextId() { return `hank-${++actionCounter}` }

export function evaluateOnLoad(
  products: Product[],
  orders: Order[],
  inventory: InventoryLevel[],
  hasActed: Set<string>
): AgentResult {
  const actions: AgentAction[] = []
  const now = new Date().toISOString()

  // Score all products
  const scored = scoreProducts(products, orders, inventory)

  // Log scoring completion
  const scoringKey = 'scored-all'
  if (!hasActed.has(scoringKey)) {
    hasActed.add(scoringKey)

    const coreCount = scored.filter((p) => p.tier === 'Core').length
    const exitCount = scored.filter((p) => p.tier === 'Exit').length

    actions.push({
      id: nextId(),
      timestamp: now,
      agent: 'Hank',
      type: 'product_scored',
      title: `Scored ${scored.length} products`,
      details: `${coreCount} Core, ${scored.filter((p) => p.tier === 'Strong').length} Strong, ${scored.filter((p) => p.tier === 'Slow').length} Slow, ${exitCount} Exit`,
      status: 'success',
    })
  }

  // Generate reorder recommendations for critical items
  const critical = scored.filter((p) => p.daysLeft <= 7 && p.daysLeft > 0 && p.tier !== 'Exit')
  for (const product of critical) {
    const key = `reorder-${product.id}`
    if (hasActed.has(key)) continue
    hasActed.add(key)

    // Recommend reorder quantity: 14 days of stock at current velocity
    const reorderQty = Math.max(1, Math.ceil(product.velocity * 14))

    actions.push({
      id: nextId(),
      timestamp: now,
      agent: 'Hank',
      type: 'reorder_recommendation',
      title: `Reorder needed: ${product.title}`,
      details: `${product.daysLeft} days of stock remaining. Recommend ordering ${reorderQty} units (14-day supply at ${product.velocity}/day).`,
      status: 'success',
      productId: product.id,
    })
  }

  return { agent: 'Hank', actions }
}
