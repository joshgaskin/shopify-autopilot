import { useState } from 'react'

interface DateRangeProps {
  value: string
  onChange: (value: string) => void
  options?: { value: string; label: string }[]
}

const DEFAULT_OPTIONS = [
  { value: '7d', label: '7 days' },
  { value: '30d', label: '30 days' },
  { value: '90d', label: '90 days' },
]

export default function DateRange({
  value,
  onChange,
  options = DEFAULT_OPTIONS,
}: DateRangeProps) {
  return (
    <div className="flex items-center gap-1 rounded-lg bg-surface-1 p-1">
      {options.map((opt) => (
        <button
          key={opt.value}
          onClick={() => onChange(opt.value)}
          className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
            value === opt.value
              ? 'bg-surface-2 text-text-primary'
              : 'text-text-secondary hover:text-text-primary'
          }`}
        >
          {opt.label}
        </button>
      ))}
    </div>
  )
}
