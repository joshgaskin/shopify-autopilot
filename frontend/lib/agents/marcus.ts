/**
 * Marcus — Chief of Staff
 *
 * Domain: Orchestrates all agents, deploys storefront widget, generates daily insight
 * Always active — coordinates Rick, Hank, Ron
 */

import { api } from '../api'
import * as rick from './rick'
import * as hank from './hank'
import * as ron from './ron'
import type { AgentAction, AgentResult, StoreState } from './types'
import type { Product, Order, InventoryLevel, LiveEvent } from '../types'

let actionCounter = 0
function nextId() { return `marcus-${++actionCounter}` }

// ── Daily Insight — merchandising tips (from Plus2's Pickle of the Day) ─────

const INSIGHTS = [
  { emoji: '🛒', text: 'Peak ordering time is typically 7–10pm. Schedule promotions 30 minutes before peak hour for maximum impact.', category: 'Shopping Behaviour' },
  { emoji: '📅', text: 'Mid-week days (Tue-Thu) drive more orders than weekends. Plan flash sales accordingly.', category: 'Shopping Behaviour' },
  { emoji: '💰', text: 'Customers who buy 3+ items have 2.5x higher lifetime value. Encourage bundle deals.', category: 'Shopping Behaviour' },
  { emoji: '📦', text: 'The most common order quantity is 1 item — single-item buyers are testing you out. Nail their first impression.', category: 'Shopping Behaviour' },
  { emoji: '🔄', text: 'Repeat customers spend 67% more per order than first-timers. A loyalty program pays for itself fast.', category: 'Shopping Behaviour' },
  { emoji: '⬛', text: 'Dark colours outsell light colours 1.7 to 1. When in doubt about what to feature, go darker.', category: 'Product Insights' },
  { emoji: '🏆', text: 'Your top 10% of products generate ~40% of revenue. Protect their stock levels above all else.', category: 'Product Insights' },
  { emoji: '🔗', text: 'Products bought together should be displayed together. Cross-sell recommendations lift AOV by 10-20%.', category: 'Product Insights' },
  { emoji: '📊', text: 'Products with declining velocity for 2+ weeks are candidates for clearance. Act before they become dead stock.', category: 'Inventory' },
  { emoji: '🏷️', text: 'A 15% discount on slow movers generates more profit than a 30% discount — diminishing returns kick in fast.', category: 'Pricing' },
  { emoji: '⏳', text: '"Only X left!" urgency badges convert 3x better than generic sale badges. Scarcity sells.', category: 'Pricing' },
  { emoji: '🎯', text: 'The sweet spot for free shipping thresholds is 15-20% above your average order value.', category: 'Pricing' },
  { emoji: '📐', text: 'Size M and L are always your safest inventory bet — they account for 45%+ of units in most apparel stores.', category: 'Product Insights' },
  { emoji: '🌙', text: 'Most customers shop after dinner — the evening window generates more orders than the entire morning.', category: 'Shopping Behaviour' },
  { emoji: '🧣', text: 'Seasonal products need to be front-and-centre 4 weeks before the season starts, not when it arrives.', category: 'Store & Merchandising' },
  { emoji: '🛍️', text: 'Your best-selling products often run out first — keep an eye on their stock vs actual demand velocity.', category: 'Store & Merchandising' },
  { emoji: '☀️', text: 'Year-round staples outsell seasonal items 3:1 on an annualized basis. They deserve the most prominent placement.', category: 'Store & Merchandising' },
  { emoji: '🧢', text: 'Small accessories near checkout boost average cart value with almost zero effort.', category: 'Store & Merchandising' },
  { emoji: '📱', text: '72% of e-commerce traffic is mobile. If your product images look bad on a phone, you are losing sales.', category: 'Store & Merchandising' },
  { emoji: '🗓️', text: 'Email campaigns sent Tuesday at 10am get the highest open rates. Thursday at 2pm is second best.', category: 'Shopping Behaviour' },
]

export function getDailyInsight(): { emoji: string; text: string; category: string } {
  const now = new Date()
  const start = new Date(now.getFullYear(), 0, 0)
  const diff = now.getTime() - start.getTime()
  const dayOfYear = Math.floor(diff / (1000 * 60 * 60 * 24))
  return INSIGHTS[dayOfYear % INSIGHTS.length]
}

// ── Orchestration ───────────────────────────────────────────────────────────

export async function orchestrateOnLoad(
  products: Product[],
  orders: Order[],
  inventory: InventoryLevel[],
  state: StoreState,
  hasActed: Set<string>,
  widgetUrl?: string
): Promise<{ allActions: AgentAction[]; scored: StoreState['scored'] }> {
  const actions: AgentAction[] = []
  const now = new Date().toISOString()

  // 1. Hank scores products first (others depend on scored data)
  const hankResult = hank.evaluateOnLoad(products, orders, inventory, hasActed)
  actions.push(...hankResult.actions)

  // Update state with fresh scores
  const { scoreProducts } = await import('../intelligence')
  state.scored = scoreProducts(products, orders, inventory)

  // 2. Rick health + stockout scan
  const rickResult = rick.evaluateOnLoad(state, hasActed)
  actions.push(...rickResult.actions)

  // 3. Ron slow mover detection + discounts
  const ronResult = await ron.evaluateOnLoad(state, hasActed)
  actions.push(...ronResult.actions)

  // 4. Marcus — deploy storefront widget
  if (widgetUrl) {
    const widgetKey = 'widget-deployed'
    if (!hasActed.has(widgetKey)) {
      hasActed.add(widgetKey)
      try {
        await api.injectStorefrontScript(widgetUrl)
        actions.push({
          id: nextId(),
          timestamp: now,
          agent: 'Marcus',
          type: 'widget_deployed',
          title: 'Deployed storefront low-stock widget',
          details: `Injected urgency badges on product pages via ${widgetUrl}`,
          status: 'success',
        })
      } catch {
        actions.push({
          id: nextId(),
          timestamp: now,
          agent: 'Marcus',
          type: 'widget_deployed',
          title: 'Failed to deploy storefront widget',
          details: `Could not inject script at ${widgetUrl}`,
          status: 'failed',
        })
      }
    }
  }

  // 5. Marcus — daily insight
  const insightKey = 'daily-insight'
  if (!hasActed.has(insightKey)) {
    hasActed.add(insightKey)
    const insight = getDailyInsight()
    actions.push({
      id: nextId(),
      timestamp: now,
      agent: 'Marcus',
      type: 'daily_insight',
      title: 'Generated daily merchandising insight',
      details: insight.text,
      status: 'success',
    })
  }

  // 6. Rick — send stockout alert emails
  const stockoutAlerts = actions.filter((a) => a.agent === 'Rick' && a.type === 'stockout_alert' && a.status === 'pending')
  for (const alert of stockoutAlerts) {
    const emailKey = `email-${alert.productId}`
    if (hasActed.has(emailKey)) continue
    hasActed.add(emailKey)

    try {
      await api.sendEmail(
        'store-manager@example.com',
        `⚠️ Stockout Risk: ${alert.title.replace('Stockout risk: ', '')}`,
        `<h2>Stockout Alert</h2><p>${alert.details}</p><p>Please reorder from your supplier ASAP.</p>`
      )
      alert.status = 'success'
      actions.push({
        id: nextId(),
        timestamp: now,
        agent: 'Rick',
        type: 'email_sent',
        title: `Sent reorder alert email for ${alert.title.replace('Stockout risk: ', '')}`,
        details: 'Notified store-manager@example.com',
        status: 'success',
        productId: alert.productId,
      })
    } catch {
      alert.status = 'failed'
    }
  }

  return { allActions: actions, scored: state.scored }
}

export function orchestrateOnEvent(
  event: LiveEvent,
  state: StoreState,
  hasActed: Set<string>
): AgentAction[] {
  const actions: AgentAction[] = []

  // Rick evaluates every event
  const rickResult = rick.evaluateOnEvent(event, state, hasActed)
  actions.push(...rickResult.actions)

  // Ron evaluates inventory changes
  const ronResult = ron.evaluateOnEvent(event, state, hasActed)
  actions.push(...ronResult.actions)

  return actions
}
