import React, { useMemo } from 'react'
import Shell from '../components/Shell'
import Card from '../components/ui/Card'
import Badge from '../components/ui/Badge'
import KPICard from '../components/KPICard'
import DataTable, { Column } from '../components/DataTable'
import DonutChart from '../components/charts/DonutChart'
import { useCustomers } from '../hooks/useCustomers'
import { useOrders } from '../hooks/useOrders'
import { segmentCustomers } from '../lib/intelligence'
import { formatCurrency } from '../lib/utils'
import type { SegmentName, SegmentedCustomer } from '../lib/agents/types'

const SEGMENT_COLORS: Record<SegmentName, string> = {
  Champions: '#00FF94',
  Loyal: '#3B82F6',
  'At Risk': '#FFB224',
  New: '#8B5CF6',
  Lost: '#FF4444',
}

const SEGMENT_VARIANTS: Record<SegmentName, 'success' | 'warning' | 'error' | 'neutral'> = {
  Champions: 'success',
  Loyal: 'neutral',
  'At Risk': 'warning',
  New: 'neutral',
  Lost: 'error',
}

const columns: Column[] = [
  { key: 'name', label: 'Customer', sortable: true },
  { key: 'email', label: 'Email' },
  {
    key: 'segment',
    label: 'Segment',
    sortable: true,
    render: (v: SegmentName) => <Badge variant={SEGMENT_VARIANTS[v]}>{v}</Badge>,
  },
  {
    key: 'rfmScore',
    label: 'RFM Score',
    sortable: true,
    render: (v: number) => <span className="font-medium">{v.toFixed(1)}</span>,
  },
  { key: 'orderCount', label: 'Orders', sortable: true },
  {
    key: 'totalSpent',
    label: 'Total Spent',
    sortable: true,
    render: (v: number) => formatCurrency(v),
  },
  {
    key: 'daysSinceLastOrder',
    label: 'Days Since Order',
    sortable: true,
    render: (v: number) => (
      <span className={v > 90 ? 'text-status-error' : v > 30 ? 'text-status-warning' : ''}>
        {v >= 999 ? 'Never' : v}
      </span>
    ),
  },
]

export default function SegmentsPage() {
  const { data: customersData, loading: customersLoading } = useCustomers({ limit: 250 })
  const { data: ordersData, loading: ordersLoading } = useOrders({ limit: 250 })

  const segmented = useMemo(() => {
    if (!customersData?.data?.length || !ordersData?.data?.length) return []
    return segmentCustomers(customersData.data, ordersData.data)
  }, [customersData, ordersData])

  const segmentCounts = useMemo(() => {
    const counts: Record<SegmentName, number> = {
      Champions: 0, Loyal: 0, 'At Risk': 0, New: 0, Lost: 0,
    }
    for (const c of segmented) counts[c.segment]++
    return counts
  }, [segmented])

  const donutSegments = Object.entries(segmentCounts).map(([label, value]) => ({
    label,
    value,
    color: SEGMENT_COLORS[label as SegmentName],
  }))

  const totalCustomers = segmented.length
  const avgLTV = totalCustomers > 0
    ? segmented.reduce((sum, c) => sum + c.totalSpent, 0) / totalCustomers
    : 0
  const atRiskCount = segmentCounts['At Risk']
  const championsCount = segmentCounts.Champions

  const loading = customersLoading || ordersLoading

  return (
    <Shell title="Customer Segments">
      <div className="space-y-4">
        {/* KPIs */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <KPICard title="Total Customers" value={totalCustomers} />
          <KPICard title="Champions" value={championsCount} />
          <KPICard title="At Risk" value={atRiskCount} />
          <KPICard title="Avg LTV" value={formatCurrency(avgLTV)} />
        </div>

        {/* Chart + Table */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <Card title="Segment Distribution" className="lg:col-span-1">
            <div className="flex justify-center py-4">
              <DonutChart
                segments={donutSegments}
                centerValue={String(totalCustomers)}
                centerLabel="customers"
                size={180}
              />
            </div>
          </Card>
          <Card title="Customer Table" className="lg:col-span-2">
            {loading ? (
              <p className="text-xs text-text-tertiary py-8 text-center">Loading customer data...</p>
            ) : (
              <DataTable columns={columns} data={segmented} />
            )}
          </Card>
        </div>
      </div>
    </Shell>
  )
}
