import React, { useState, useEffect, useCallback } from 'react'
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
import { api } from '../lib/api'
import type { AgentState, AgentAction, ScoredProduct, Tier } from '../lib/agents/types'

const TABS = [
  { key: 'agents', label: 'Agents' },
  { key: 'inventory', label: 'Inventory' },
  { key: 'actions', label: 'Actions' },
  { key: 'live', label: 'Live' },
]

const AGENT_META: Record<string, { emoji: string; domain: string }> = {
  Rick: { emoji: '🔧', domain: 'Operations' },
  Hank: { emoji: '📦', domain: 'Supply Chain' },
  Ron: { emoji: '💰', domain: 'Finance' },
  Marcus: { emoji: '🎯', domain: 'Chief of Staff' },
}

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

// Backend API types for agent data
interface BackendAgentState {
  name: string
  status: string
  lastAction: string | null
  actionCount: number
  lastCycleAt: string | null
}

interface BackendAgentAction {
  id: string
  timestamp: string
  agent: string
  type: string
  title: string
  details: string
  commentary: string
  status: string
  productId?: string
  cycle: number
}

export default function AutopilotPage() {
  const [tab, setTab] = useState('agents')
  const [agents, setAgents] = useState<AgentState[]>(
    Object.entries(AGENT_META).map(([name, meta]) => ({
      name: name as AgentState['name'],
      ...meta,
      status: 'idle' as const,
      lastAction: null,
      actionCount: 0,
    }))
  )
  const [actions, setActions] = useState<AgentAction[]>([])
  const [scored, setScored] = useState<ScoredProduct[]>([])
  const [dailyInsight, setDailyInsight] = useState<{ commentary: string; title: string } | null>(null)
  const [stats, setStats] = useState<{ totalActions: number; currentCycle: number; byType: Record<string, number> } | null>(null)

  const { data: productsData } = useProducts({ limit: 250 })
  const { data: ordersData } = useOrders({ limit: 250 })
  const { data: inventoryData } = useInventory()
  const { events, connected } = useEventStream()

  // Poll backend for agent states + actions every 5 seconds
  const fetchAgentData = useCallback(async () => {
    try {
      const [statesRes, actionsRes, statsRes] = await Promise.all([
        fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/agents/states`),
        fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/agents/actions?limit=100`),
        fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/agents/stats`),
      ])

      if (statesRes.ok) {
        const backendStates: BackendAgentState[] = await statesRes.json()
        setAgents((prev) =>
          prev.map((a) => {
            const bs = backendStates.find((s) => s.name === a.name)
            if (!bs) return a
            return {
              ...a,
              status: (bs.status as AgentState['status']) || 'idle',
              lastAction: bs.lastAction,
              actionCount: bs.actionCount,
            }
          })
        )
      }

      if (actionsRes.ok) {
        const backendActions: BackendAgentAction[] = await actionsRes.json()
        const mapped: AgentAction[] = backendActions.map((a) => ({
          id: a.id,
          timestamp: a.timestamp,
          agent: a.agent as AgentAction['agent'],
          type: a.type as AgentAction['type'],
          title: a.title,
          details: a.commentary || a.details, // Show Claude commentary when available
          status: a.status as AgentAction['status'],
          productId: a.productId,
        }))
        setActions(mapped)

        // Find latest daily insight for the DailyInsight card
        const insight = backendActions.find((a) => a.type === 'daily_insight' && a.agent === 'Marcus' && a.commentary)
        if (insight) {
          setDailyInsight({ commentary: insight.commentary, title: insight.title })
        }
      }

      if (statsRes.ok) {
        setStats(await statsRes.json())
      }
    } catch {
      // Backend not available — that's fine, we'll retry
    }
  }, [])

  useEffect(() => {
    fetchAgentData()
    const interval = setInterval(fetchAgentData, 5000)
    return () => clearInterval(interval)
  }, [fetchAgentData])

  // Score products client-side for the inventory tab
  useEffect(() => {
    if (!productsData?.data?.length || !ordersData?.data?.length) return
    const inventory = inventoryData || []
    setScored(scoreProducts(productsData.data, ordersData.data, inventory))
  }, [productsData, ordersData, inventoryData])

  // KPI stats
  const totalStock = scored.reduce((sum, p) => sum + p.inventory, 0)
  const atRiskCount = scored.filter((p) => p.daysLeft <= 3 && p.daysLeft > 0).length
  const coreCount = scored.filter((p) => p.tier === 'Core').length
  const totalRevenue = scored.reduce((sum, p) => sum + p.revenueTotal, 0)

  return (
    <Shell title="AutoPilot">
      <div className="space-y-4">
        {/* Daily Insight — Claude-narrated by Marcus */}
        {dailyInsight ? (
          <DailyInsight emoji="🎯" text={dailyInsight.commentary} category="Marcus — Daily Insight" />
        ) : (
          <DailyInsight emoji="⏳" text="Agents are warming up... first cycle will start momentarily." category="Standby" />
        )}

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
            <Card
              title="Activity Feed"
              subtitle={`${stats?.totalActions || actions.length} actions across ${stats?.currentCycle || 0} cycles`}
            >
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
              <KPICard title="Total Actions" value={stats?.totalActions || actions.length} />
              <KPICard title="Discounts Created" value={stats?.byType?.discount_created || 0} />
              <KPICard title="Alerts Sent" value={(stats?.byType?.stockout_alert || 0) + (stats?.byType?.email_sent || 0)} />
              <KPICard title="Health Issues" value={stats?.byType?.health_issue || 0} />
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
              <KPICard title="Agent Cycles" value={stats?.currentCycle || 0} />
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
