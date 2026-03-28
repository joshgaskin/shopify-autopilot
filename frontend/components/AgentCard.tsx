import React from 'react'
import { cn } from '../lib/utils'
import type { AgentState } from '../lib/agents/types'

interface AgentCardProps {
  agent: AgentState
  selected?: boolean
  onClick?: () => void
}

const statusColors: Record<string, string> = {
  active: 'bg-status-success',
  idle: 'bg-text-tertiary',
  evaluating: 'bg-status-warning',
}

const statusLabels: Record<string, string> = {
  active: 'Active',
  idle: 'Idle',
  evaluating: 'Evaluating...',
}

export default function AgentCard({ agent, selected, onClick }: AgentCardProps) {
  return (
    <div
      className={cn(
        'bg-surface-1 border rounded-lg p-4 transition-all duration-150',
        selected
          ? 'border-accent ring-1 ring-accent/30'
          : 'border-border hover:border-border-hover',
        onClick && 'cursor-pointer',
      )}
      onClick={onClick}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          {agent.avatar ? (
            <img
              src={agent.avatar}
              alt={agent.name}
              className={cn(
                'w-10 h-10 rounded-full object-cover border-2 flex-shrink-0',
                selected ? 'border-accent' : 'border-border',
              )}
            />
          ) : (
            <span className="text-xl w-10 h-10 flex items-center justify-center">{agent.emoji}</span>
          )}
          <div>
            <h3 className="text-sm font-medium text-text-primary">{agent.name}</h3>
            <p className="text-xs text-text-tertiary">{agent.domain}</p>
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          <span className={cn(
            'w-2 h-2 rounded-full',
            statusColors[agent.status],
            agent.status === 'active' && 'animate-pulse'
          )} />
          <span className="text-xs text-text-tertiary">{statusLabels[agent.status]}</span>
        </div>
      </div>

      {agent.lastAction && (
        <p className="text-xs text-text-secondary truncate mb-2" title={agent.lastAction}>
          {agent.lastAction}
        </p>
      )}

      <div className="flex items-center justify-between">
        <span className="text-xs text-text-tertiary">Actions taken</span>
        <span className={cn(
          'text-sm font-semibold',
          selected ? 'text-accent' : agent.actionCount > 0 ? 'text-accent' : 'text-text-tertiary',
        )}>
          {agent.actionCount}
        </span>
      </div>
    </div>
  )
}
