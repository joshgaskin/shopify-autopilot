import React from 'react'

interface EmptyStateProps {
  title: string
  description: string
  action?: React.ReactNode
}

export default function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4">
      {/* Icon */}
      <svg
        width="40"
        height="40"
        viewBox="0 0 40 40"
        fill="none"
        className="mb-4 text-text-tertiary"
      >
        <rect
          x="4"
          y="4"
          width="32"
          height="32"
          rx="8"
          stroke="currentColor"
          strokeWidth="1.5"
        />
        <path
          d="M14 20h12M20 14v12"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
        />
      </svg>
      <h3 className="text-base font-medium text-text-primary mb-1">{title}</h3>
      <p className="text-sm text-text-tertiary text-center max-w-xs mb-4">
        {description}
      </p>
      {action && <div>{action}</div>}
    </div>
  )
}
