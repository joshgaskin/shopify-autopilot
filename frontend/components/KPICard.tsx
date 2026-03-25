import React from 'react'
import { cn } from '../lib/utils'

interface KPICardProps {
  title: string
  value: string | number
  change?: number
  prefix?: string
  suffix?: string
}

export default function KPICard({ title, value, change, prefix, suffix }: KPICardProps) {
  return (
    <div className="bg-surface-1 border border-border rounded-lg p-4">
      <p className="text-xs text-text-tertiary mb-2">{title}</p>
      <div className="flex items-baseline gap-1">
        {prefix && <span className="text-lg text-text-secondary">{prefix}</span>}
        <span className="text-2xl font-semibold text-text-primary">{value}</span>
        {suffix && <span className="text-lg text-text-secondary">{suffix}</span>}
      </div>
      {change !== undefined && (
        <div className="flex items-center gap-1 mt-2">
          {change >= 0 ? (
            <svg width="12" height="12" viewBox="0 0 12 12" className="text-status-success">
              <path d="M6 2l4 5H2l4-5z" fill="currentColor" />
            </svg>
          ) : (
            <svg width="12" height="12" viewBox="0 0 12 12" className="text-status-error">
              <path d="M6 10l4-5H2l4 5z" fill="currentColor" />
            </svg>
          )}
          <span
            className={cn(
              'text-xs font-medium',
              change >= 0 ? 'text-status-success' : 'text-status-error'
            )}
          >
            {Math.abs(change).toFixed(1)}%
          </span>
          <span className="text-xs text-text-tertiary">vs prev</span>
        </div>
      )}
    </div>
  )
}
