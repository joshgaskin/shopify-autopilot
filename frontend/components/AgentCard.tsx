import React from 'react'
import { cn } from '../lib/utils'
import type { AgentState } from '../lib/agents/types'

interface AgentCardProps {
  agent: AgentState
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

export default function AgentCard({ agent }: AgentCardProps) {
  return (
    <div className="bg-surface-1 border border-border rounded-lg p-4 hover:border-border-hover transition-colors duration-150">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          {agent.avatar ? (
            <img
              src={agent.avatar}
              alt={agent.name}
              className="w-10 h-10 rounded-full object-cover border border-border flex-shrink-0"
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
        <span className="text-sm font-semibold text-accent">{agent.actionCount}</span>
      </div>
    </div>
  )
}
