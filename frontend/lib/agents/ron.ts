/**
 * Ron — Finance Agent
 *
 * Domain: Margin analysis, slow mover detection, discount ROI
 * Triggers: Page load + inventory_change events
 * Ported from: fire-sale-detection.ts, discount logic
 */

import { detectSlowMovers, suggestDiscounts } from '../intelligence'
import { api } from '../api'
import type { AgentAction, AgentResult, StoreState } from './types'
import type { LiveEvent } from '../types'

let actionCounter = 0
function nextId() { return `ron-${++actionCounter}` }

export async function evaluateOnLoad(
  state: StoreState,
  hasActed: Set<string>
): Promise<AgentResult> {
  const actions: AgentAction[] = []
  const now = new Date().toISOString()

  // Detect slow movers
  const slowMovers = detectSlowMovers(state.scored)

  if (slowMovers.length > 0) {
    const key = 'slow-movers-detected'
    if (!hasActed.has(key)) {
      hasActed.add(key)
      actions.push({
        id: nextId(),
        timestamp: now,
        agent: 'Ron',
        type: 'slow_mover_detected',
        title: `Found ${slowMovers.length} slow movers`,
        details: slowMovers.slice(0, 3).map((p) => p.title).join(', ') + (slowMovers.length > 3 ? ` + ${slowMovers.length - 3} more` : ''),
        status: 'success',
      })
    }
  }

  // Create clearance discounts for slow movers
  const discountSuggestions = suggestDiscounts(slowMovers)
  for (const { product, discountPct } of discountSuggestions.slice(0, 3)) {
    const key = `discount-${product.id}`
    if (hasActed.has(key)) continue
    hasActed.add(key)

    const code = `CLEAR-${product.handle.slice(0, 15).toUpperCase()}-${discountPct}`

    try {
      await api.createDiscount(code, discountPct)
      actions.push({
        id: nextId(),
        timestamp: now,
        agent: 'Ron',
        type: 'discount_created',
        title: `Created discount: ${code}`,
        details: `${discountPct}% off ${product.title} (trend ratio: ${product.trendRatio}, tier: ${product.tier})`,
        status: 'success',
        productId: product.id,
      })
    } catch {
      actions.push({
        id: nextId(),
        timestamp: now,
        agent: 'Ron',
        type: 'discount_created',
        title: `Failed to create discount: ${code}`,
        details: `Attempted ${discountPct}% off ${product.title}`,
        status: 'failed',
        productId: product.id,
      })
    }
  }

  return { agent: 'Ron', actions }
}

export function evaluateOnEvent(
  event: LiveEvent,
  state: StoreState,
  hasActed: Set<string>
): AgentResult {
  const actions: AgentAction[] = []

  // Only react to inventory changes
  if (event.event_type !== 'inventory_change') {
    return { agent: 'Ron', actions }
  }

  // Re-check slow movers after inventory change (lightweight)
  const slowMovers = detectSlowMovers(state.scored)
  const now = new Date().toISOString()

  for (const product of slowMovers.slice(0, 1)) {
    const key = `event-slow-${product.id}`
    if (hasActed.has(key)) continue
    hasActed.add(key)

    actions.push({
      id: nextId(),
      timestamp: now,
      agent: 'Ron',
      type: 'slow_mover_detected',
      title: `Inventory change flagged slow mover: ${product.title}`,
      details: `Velocity declining (${product.trendRatio}x) with ${product.daysLeft} days of stock`,
      status: 'success',
      productId: product.id,
    })
  }

  return { agent: 'Ron', actions }
}
