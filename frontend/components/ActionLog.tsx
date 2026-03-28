import React from 'react'
import { cn, timeAgo } from '../lib/utils'
import Badge from './ui/Badge'
import type { AgentAction } from '../lib/agents/types'

interface ActionLogProps {
  actions: AgentAction[]
  maxItems?: number
}

const agentEmojis: Record<string, string> = {
  Rick: '🔧',
  Hank: '📦',
  Ron: '💰',
  Marty: '📣',
  Marcus: '🎯',
}

const typeLabels: Record<string, string> = {
  stockout_alert: 'Stockout Alert',
  health_issue: 'Health Issue',
  anomaly_detected: 'Anomaly',
  product_scored: 'Scored',
  reorder_recommendation: 'Reorder',
  discount_created: 'Discount',
  slow_mover_detected: 'Slow Mover',
  widget_deployed: 'Widget',
  daily_insight: 'Insight',
  email_drafted: 'Email Draft',
  segment_analyzed: 'Segments',
  product_tagged: 'Tagged',
  po_created: 'Purchase Order',
  reorder_covered: 'Covered',
}

const statusVariant: Record<string, 'success' | 'warning' | 'error'> = {
  success: 'success',
  pending: 'warning',
  failed: 'error',
}

export default function ActionLog({ actions, maxItems = 50 }: ActionLogProps) {
  const displayed = actions.slice(0, maxItems)

  if (displayed.length === 0) {
    return (
      <p className="text-xs text-text-tertiary py-4 text-center">
        No agent actions yet — waiting for data...
      </p>
    )
  }

  return (
    <div className="space-y-0.5">
      {displayed.map((action) => (
        <div
          key={action.id}
          className="flex items-start gap-2.5 px-2 py-2 rounded-md hover:bg-surface-2 transition-colors duration-150"
        >
          <span className="text-sm mt-0.5 flex-shrink-0">{agentEmojis[action.agent] || '?'}</span>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-0.5">
              <span className="text-xs font-medium text-text-primary truncate">{action.title}</span>
              <Badge variant={statusVariant[action.status] || 'neutral'}>
                {typeLabels[action.type] || action.type}
              </Badge>
            </div>
            <p className="text-xs text-text-tertiary truncate" title={action.details}>
              {action.details}
            </p>
          </div>
          <span className="text-xs text-text-tertiary flex-shrink-0 mt-0.5">
            {timeAgo(action.timestamp)}
          </span>
        </div>
      ))}
    </div>
  )
}
