import React from 'react'
import { cn } from '../../lib/utils'

interface CardProps {
  children: React.ReactNode
  title?: string
  subtitle?: string
  className?: string
  action?: React.ReactNode
}

export default function Card({ children, title, subtitle, className, action }: CardProps) {
  return (
    <div
      className={cn(
        'bg-surface-1 border border-border rounded-lg p-4',
        className
      )}
    >
      {(title || action) && (
        <div className="flex items-center justify-between mb-3">
          <div>
            {title && (
              <h3 className="text-sm font-medium text-text-primary">{title}</h3>
            )}
            {subtitle && (
              <p className="text-xs text-text-tertiary mt-0.5">{subtitle}</p>
            )}
          </div>
          {action && <div>{action}</div>}
        </div>
      )}
      {children}
    </div>
  )
}
