/**
 * Rick — Operations Agent
 *
 * Domain: Stock health monitoring, anomaly detection, OOS alerts
 * Triggers: Every SSE event (incremental) + page load (full scan)
 * Ported from: shop-health.ts, order-alerts.ts, stockout-detection.ts
 */

import { detectStockoutRisk, checkProductHealth } from '../intelligence'
import type { AgentAction, AgentResult, StoreState } from './types'
import type { LiveEvent } from '../types'

let actionCounter = 0
function nextId() { return `rick-${++actionCounter}` }

export function evaluateOnLoad(
  state: StoreState,
  hasActed: Set<string>
): AgentResult {
  const actions: AgentAction[] = []
  const now = new Date().toISOString()

  // 1. Health check scan
  const healthIssues = checkProductHealth(state.products, state.inventory)
  for (const issue of healthIssues) {
    const key = `health-${issue.productId}-${issue.issue}`
    if (hasActed.has(key)) continue
    hasActed.add(key)

    actions.push({
      id: nextId(),
      timestamp: now,
      agent: 'Rick',
      type: 'health_issue',
      title: `Health issue: ${issue.productTitle}`,
      details: issue.issue,
      status: 'success',
      productId: issue.productId,
    })
  }

  // 2. Stockout risk alerts
  const atRisk = detectStockoutRisk(state.scored)
  for (const product of atRisk) {
    const key = `stockout-${product.id}`
    if (hasActed.has(key)) continue
    hasActed.add(key)

    actions.push({
      id: nextId(),
      timestamp: now,
      agent: 'Rick',
      type: 'stockout_alert',
      title: `Stockout risk: ${product.title}`,
      details: `Only ${product.daysLeft} days of stock left at ${product.velocity} units/day. Sending reorder alert.`,
      status: 'pending',
      productId: product.id,
    })
  }

  return { agent: 'Rick', actions }
}

export function evaluateOnEvent(
  event: LiveEvent,
  state: StoreState,
  hasActed: Set<string>
): AgentResult {
  const actions: AgentAction[] = []
  const now = new Date().toISOString()

  if (event.event_type === 'new_order') {
    // Check if any ordered product is now at stockout risk
    const payload = event.payload as { line_items?: { title: string }[] }
    const lineItems = payload.line_items || []

    for (const item of lineItems) {
      const scored = state.scored.find((p) => p.title === item.title)
      if (!scored || scored.daysLeft > 3 || scored.velocity <= 0) continue

      const key = `event-stockout-${scored.id}`
      if (hasActed.has(key)) continue
      hasActed.add(key)

      actions.push({
        id: nextId(),
        timestamp: now,
        agent: 'Rick',
        type: 'stockout_alert',
        title: `Order triggered stockout warning: ${scored.title}`,
        details: `New order reduced stock. ${scored.inventory} units remain — ${scored.daysLeft} days at current velocity.`,
        status: 'success',
        productId: scored.id,
      })
    }
  }

  // Sales gap detection — if no orders for >2 hours based on hourly baseline
  if (event.event_type === 'new_order' && state.hourlyBaseline.length > 0) {
    const currentHour = new Date().getHours()
    const baseline = state.hourlyBaseline.find((h) => h.hour === currentHour)
    if (baseline && baseline.avg_orders > 2) {
      // Just log awareness — don't alert unless we have a real gap tracker
    }
  }

  return { agent: 'Rick', actions }
}
