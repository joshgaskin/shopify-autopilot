import React, { useState, useEffect, useRef, useCallback } from 'react'
import Shell from '../components/Shell'
import Tabs from '../components/ui/Tabs'
import Card from '../components/ui/Card'
import Badge from '../components/ui/Badge'
import KPICard from '../components/KPICard'
import DataTable, { Column } from '../components/DataTable'
import LiveFeed from '../components/LiveFeed'
import AgentCard from '../components/AgentCard'
import ActionLog from '../components/ActionLog'
import DailyInsight from '../components/DailyInsight'
import { useProducts } from '../hooks/useProducts'
import { useOrders } from '../hooks/useOrders'
import { useInventory } from '../hooks/useInventory'
import { useEventStream } from '../hooks/useEventStream'
import { formatCurrency } from '../lib/utils'
import { scoreProducts } from '../lib/intelligence'
import * as marcus from '../lib/agents/marcus'
import type { AgentState, AgentAction, ScoredProduct, StoreState, Tier } from '../lib/agents/types'

const TABS = [
  { key: 'agents', label: 'Agents' },
  { key: 'inventory', label: 'Inventory' },
  { key: 'actions', label: 'Actions' },
  { key: 'live', label: 'Live' },
]

const INITIAL_AGENTS: AgentState[] = [
  { name: 'Rick', domain: 'Operations', emoji: '🔧', status: 'idle', lastAction: null, actionCount: 0 },
  { name: 'Hank', domain: 'Supply Chain', emoji: '📦', status: 'idle', lastAction: null, actionCount: 0 },
  { name: 'Ron', domain: 'Finance', emoji: '💰', status: 'idle', lastAction: null, actionCount: 0 },
  { name: 'Marcus', domain: 'Chief of Staff', emoji: '🎯', status: 'idle', lastAction: null, actionCount: 0 },
]

const tierVariant: Record<Tier, 'success' | 'warning' | 'error' | 'neutral'> = {
  Core: 'success',
  Strong: 'neutral',
  Slow: 'warning',
  Exit: 'error',
}

const inventoryColumns: Column[] = [
  {
    key: 'title',
    label: 'Product',
    sortable: true,
    render: (_: string, row: ScoredProduct) => (
      <div className="flex items-center gap-2">
        {row.image && (
          <img src={row.image} alt="" className="w-7 h-7 rounded object-cover flex-shrink-0" />
        )}
        <span className="truncate max-w-[200px]" title={row.title}>{row.title}</span>
      </div>
    ),
  },
  {
    key: 'score',
    label: 'Score',
    sortable: true,
    render: (v: number) => <span className="font-medium">{v}</span>,
  },
  {
    key: 'tier',
    label: 'Tier',
    sortable: true,
    render: (v: Tier) => <Badge variant={tierVariant[v]}>{v}</Badge>,
  },
  {
    key: 'inventory',
    label: 'Stock',
    sortable: true,
    render: (v: number) => (
      <span className={v <= 0 ? 'text-status-error' : v <= 5 ? 'text-status-warning' : ''}>
        {v}
      </span>
    ),
  },
  {
    key: 'velocity',
    label: 'Velocity/day',
    sortable: true,
    render: (v: number) => v.toFixed(2),
  },
  {
    key: 'daysLeft',
    label: 'Days Left',
    sortable: true,
    render: (v: number) => (
      <span className={v <= 3 ? 'text-status-error font-medium' : v <= 7 ? 'text-status-warning' : ''}>
        {v >= 999 ? '∞' : v}
      </span>
    ),
  },
  {
    key: 'trend',
    label: 'Trend',
    render: (v: string) => (
      <span className={v === 'growing' ? 'text-status-success' : v === 'declining' ? 'text-status-error' : 'text-text-tertiary'}>
        {v === 'growing' ? '↑' : v === 'declining' ? '↓' : '→'} {v}
      </span>
    ),
  },
  {
    key: 'revenueTotal',
    label: 'Revenue',
    sortable: true,
    render: (v: number) => formatCurrency(v),
  },
  {
    key: 'price',
    label: 'Price',
    render: (v: number) => formatCurrency(v),
  },
]

export default function AutopilotPage() {
  const [tab, setTab] = useState('agents')
  const [agents, setAgents] = useState<AgentState[]>(INITIAL_AGENTS)
  const [actions, setActions] = useState<AgentAction[]>([])
  const [scored, setScored] = useState<ScoredProduct[]>([])
  const hasActedRef = useRef(new Set<string>())
  const orchestratedRef = useRef(false)

  const { data: productsData } = useProducts({ limit: 250 })
  const { data: ordersData } = useOrders({ limit: 250 })
  const { data: inventoryData } = useInventory()
  const { events, connected } = useEventStream()

  const insight = marcus.getDailyInsight()

  // Build store state ref for event handlers
  const storeStateRef = useRef<StoreState>({
    products: [],
    orders: [],
    inventory: [],
    scored: [],
    hourlyBaseline: [],
  })

  // Update agent state helper
  const updateAgent = useCallback((name: string, updates: Partial<AgentState>) => {
    setAgents((prev) =>
      prev.map((a) => (a.name === name ? { ...a, ...updates } : a))
    )
  }, [])

  // Count actions per agent
  const countActions = useCallback((allActions: AgentAction[]) => {
    const counts: Record<string, number> = {}
    for (const a of allActions) {
      counts[a.agent] = (counts[a.agent] || 0) + 1
    }
    return counts
  }, [])

  // Orchestrate on load when data is ready
  useEffect(() => {
    if (orchestratedRef.current) return
    if (!productsData?.data?.length || !ordersData?.data?.length) return

    orchestratedRef.current = true

    const products = productsData.data
    const orders = ordersData.data
    const inventory = inventoryData || []

    const state: StoreState = {
      products,
      orders,
      inventory,
      scored: scoreProducts(products, orders, inventory),
      hourlyBaseline: [],
    }
    storeStateRef.current = state

    // Mark all agents evaluating
    setAgents((prev) => prev.map((a) => ({ ...a, status: 'evaluating' as const })))

    const widgetUrl = typeof window !== 'undefined'
      ? `${window.location.origin}/low-stock-widget.js`
      : undefined

    marcus
      .orchestrateOnLoad(products, orders, inventory, state, hasActedRef.current, widgetUrl)
      .then(({ allActions, scored: freshScored }) => {
        setActions(allActions)
        setScored(freshScored)
        storeStateRef.current.scored = freshScored

        // Update agent states
        const counts = countActions(allActions)
        setAgents((prev) =>
          prev.map((a) => {
            const agentActions = allActions.filter((act) => act.agent === a.name)
            const last = agentActions[agentActions.length - 1]
            return {
              ...a,
              status: 'active',
              actionCount: counts[a.name] || 0,
              lastAction: last?.title || null,
            }
          })
        )
      })
      .catch(() => {
        setAgents((prev) => prev.map((a) => ({ ...a, status: 'idle' as const })))
      })
  }, [productsData, ordersData, inventoryData, countActions])

  // React to SSE events
  useEffect(() => {
    if (events.length === 0 || !orchestratedRef.current) return
    const latestEvent = events[0]

    const newActions = marcus.orchestrateOnEvent(
      latestEvent,
      storeStateRef.current,
      hasActedRef.current
    )

    if (newActions.length > 0) {
      setActions((prev) => [...newActions, ...prev])

      // Update agent counts
      for (const action of newActions) {
        updateAgent(action.agent, {
          actionCount: actions.filter((a) => a.agent === action.agent).length + 1,
          lastAction: action.title,
        })
      }
    }
  }, [events])

  // KPI stats
  const totalStock = scored.reduce((sum, p) => sum + p.inventory, 0)
  const atRiskCount = scored.filter((p) => p.daysLeft <= 3 && p.daysLeft > 0).length
  const coreCount = scored.filter((p) => p.tier === 'Core').length
  const totalRevenue = scored.reduce((sum, p) => sum + p.revenueTotal, 0)

  return (
    <Shell title="AutoPilot">
      <div className="space-y-4">
        {/* Daily Insight */}
        <DailyInsight emoji={insight.emoji} text={insight.text} category={insight.category} />

        {/* Tabs */}
        <Tabs tabs={TABS} active={tab} onChange={setTab} />

        {/* ─── Agents Tab ─── */}
        {tab === 'agents' && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
              {agents.map((agent) => (
                <AgentCard key={agent.name} agent={agent} />
              ))}
            </div>
            <Card title="Activity Feed" subtitle={`${actions.length} actions taken`}>
              <ActionLog actions={actions} maxItems={20} />
            </Card>
          </div>
        )}

        {/* ─── Inventory Tab ─── */}
        {tab === 'inventory' && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
              <KPICard title="Total Stock" value={totalStock} />
              <KPICard title="At Risk" value={atRiskCount} suffix="products" />
              <KPICard title="Core Products" value={coreCount} />
              <KPICard title="Total Revenue" value={formatCurrency(totalRevenue)} />
            </div>
            <Card title="Product Intelligence" subtitle="Scored by velocity, revenue, stock health, and trend">
              <DataTable columns={inventoryColumns} data={scored} />
            </Card>
          </div>
        )}

        {/* ─── Actions Tab ─── */}
        {tab === 'actions' && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
              <KPICard title="Total Actions" value={actions.length} />
              <KPICard title="Discounts Created" value={actions.filter((a) => a.type === 'discount_created').length} />
              <KPICard title="Alerts Sent" value={actions.filter((a) => a.type === 'stockout_alert' || a.type === 'email_sent').length} />
              <KPICard title="Health Issues" value={actions.filter((a) => a.type === 'health_issue').length} />
            </div>
            <Card title="Full Action Log">
              <ActionLog actions={actions} maxItems={100} />
            </Card>
          </div>
        )}

        {/* ─── Live Tab ─── */}
        {tab === 'live' && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
              <KPICard title="SSE Status" value={connected ? 'Connected' : 'Offline'} />
              <KPICard title="Events Received" value={events.length} />
              <KPICard title="Agent Actions" value={actions.length} />
              <KPICard title="Active Agents" value={agents.filter((a) => a.status === 'active').length} suffix="/ 4" />
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <Card title="Live Events" className="min-h-[300px]">
                <LiveFeed maxEvents={30} />
              </Card>
              <Card title="Agent Reactions" className="min-h-[300px]">
                <ActionLog actions={actions.filter((a) => a.timestamp > new Date(Date.now() - 3600000).toISOString())} maxItems={20} />
              </Card>
            </div>
          </div>
        )}
      </div>
    </Shell>
  )
}
