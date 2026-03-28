import React, { useCallback } from 'react'
import { cn, timeAgo } from '../lib/utils'
import Badge from './ui/Badge'
import type { AgentAction } from '../lib/agents/types'

interface AgentDialogueProps {
  actions: AgentAction[]
  maxItems?: number
  onRevert?: (actionId: string) => void
}

const agentAvatars: Record<string, string> = {
  Rick: '/agents/rick.png',
  Hank: '/agents/hank.png',
  Ron: '/agents/ron.webp',
  Marty: '/agents/marty.webp',
  Marcus: '/agents/marcus.jpg',
}

const agentColors: Record<string, string> = {
  Rick: 'border-l-red-500',
  Hank: 'border-l-blue-500',
  Ron: 'border-l-amber-500',
  Marty: 'border-l-purple-500',
  Marcus: 'border-l-accent',
}

const typeLabels: Record<string, { label: string; variant: 'success' | 'warning' | 'error' | 'neutral' }> = {
  stockout_alert: { label: 'Stockout', variant: 'error' },
  health_issue: { label: 'Health', variant: 'warning' },
  product_scored: { label: 'Scored', variant: 'neutral' },
  reorder_recommendation: { label: 'Reorder', variant: 'warning' },
  discount_created: { label: 'Discount', variant: 'success' },
  slow_mover_detected: { label: 'Slow Mover', variant: 'warning' },
  widget_deployed: { label: 'Widget', variant: 'success' },
  daily_insight: { label: 'Insight', variant: 'neutral' },
  email_drafted: { label: 'Email Draft', variant: 'success' },
  segment_analyzed: { label: 'Segments', variant: 'neutral' },
  product_tagged: { label: 'Tagged', variant: 'neutral' },
  po_created: { label: 'PO Created', variant: 'success' },
  reorder_covered: { label: 'Covered', variant: 'success' },
}

// Action types that can be reverted
const REVERTABLE_TYPES = new Set([
  'discount_created', 'health_issue', 'stockout_alert',
  'product_tagged', 'widget_deployed', 'reorder_recommendation',
  'po_created',
])

export default function AgentDialogue({ actions, maxItems = 30, onRevert }: AgentDialogueProps) {
  const displayed = actions.slice(0, maxItems)

  if (displayed.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-text-tertiary">
        <div className="w-8 h-8 border-2 border-accent/30 border-t-accent rounded-full animate-spin mb-3" />
        <p className="text-xs">Agents are thinking...</p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {displayed.map((action, i) => {
        const avatar = agentAvatars[action.agent]
        const borderColor = agentColors[action.agent] || 'border-l-text-tertiary'
        const typeInfo = typeLabels[action.type] || { label: action.type, variant: 'neutral' as const }
        const isMarcos = action.agent === 'Marcus'
        const isReverted = action.status === 'reverted'
        const canRevert = onRevert && REVERTABLE_TYPES.has(action.type) && !isReverted

        return (
          <div
            key={action.id}
            className={cn(
              'flex gap-3 group',
              i === 0 && 'animate-fade-in',
              isReverted && 'opacity-40',
            )}
          >
            {/* Avatar */}
            <div className="flex-shrink-0 pt-0.5">
              {avatar ? (
                <img
                  src={avatar}
                  alt={action.agent}
                  className={cn(
                    'w-8 h-8 rounded-full object-cover border-2',
                    isReverted ? 'border-status-error/50 grayscale' :
                    action.status === 'failed' ? 'border-status-error/50' : 'border-border',
                  )}
                />
              ) : (
                <div className="w-8 h-8 rounded-full bg-surface-2 flex items-center justify-center text-sm">
                  ?
                </div>
              )}
            </div>

            {/* Message bubble */}
            <div className={cn('flex-1 min-w-0')}>
              {/* Header */}
              <div className="flex items-center gap-2 mb-1">
                <span className={cn(
                  'text-xs font-semibold',
                  isReverted ? 'text-text-tertiary line-through' :
                  isMarcos ? 'text-accent' : 'text-text-primary',
                )}>
                  {action.agent}
                </span>
                {isReverted ? (
                  <Badge variant="error">Reverted</Badge>
                ) : (
                  <Badge variant={typeInfo.variant}>{typeInfo.label}</Badge>
                )}
                <span className="text-xs text-text-tertiary opacity-0 group-hover:opacity-100 transition-opacity">
                  {timeAgo(action.timestamp)}
                </span>
                {canRevert && (
                  <button
                    onClick={(e) => { e.stopPropagation(); onRevert(action.id) }}
                    className="text-xs text-status-error/60 hover:text-status-error opacity-0 group-hover:opacity-100 transition-opacity ml-auto"
                    title="Revert this action — removes the change and lets the agent re-evaluate"
                  >
                    ↩ Revert
                  </button>
                )}
              </div>

              {/* Content */}
              <div className={cn(
                'rounded-lg rounded-tl-sm px-3 py-2 border-l-2',
                isReverted ? 'border-l-status-error/30 bg-status-error/5' : borderColor,
                !isReverted && (isMarcos ? 'bg-accent/5' : 'bg-surface-2/50'),
              )}>
                <p className={cn(
                  'text-xs font-medium mb-0.5',
                  isReverted ? 'text-text-tertiary line-through' : 'text-text-primary',
                )}>
                  {action.title}
                </p>
                <p className={cn(
                  'text-xs leading-relaxed',
                  isReverted ? 'text-text-tertiary' : 'text-text-secondary',
                )}>
                  {action.details}
                </p>
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
