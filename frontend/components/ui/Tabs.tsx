import React from 'react'
import { cn } from '../../lib/utils'

interface TabsProps {
  tabs: { key: string; label: string }[]
  active: string
  onChange: (key: string) => void
}

export default function Tabs({ tabs, active, onChange }: TabsProps) {
  return (
    <div className="flex gap-0 border-b border-border">
      {tabs.map((tab) => (
        <button
          key={tab.key}
          onClick={() => onChange(tab.key)}
          className={cn(
            'px-3 py-2 text-sm transition-colors duration-150 ease-out border-b-2 -mb-px',
            active === tab.key
              ? 'border-accent text-text-primary'
              : 'border-transparent text-text-tertiary hover:text-text-secondary'
          )}
        >
          {tab.label}
        </button>
      ))}
    </div>
  )
}
