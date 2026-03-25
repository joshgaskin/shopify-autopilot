import React from 'react'

interface SelectProps {
  options: { value: string; label: string }[]
  value: string
  onChange: (value: string) => void
  placeholder?: string
}

export default function Select({ options, value, onChange, placeholder }: SelectProps) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="bg-surface-2 border border-border rounded-md px-3 py-1.5 text-sm text-text-primary
        appearance-none cursor-pointer transition-colors duration-150 ease-out
        hover:border-border-hover focus:border-border-active focus:outline-none"
    >
      {placeholder && (
        <option value="" disabled>
          {placeholder}
        </option>
      )}
      {options.map((opt) => (
        <option key={opt.value} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
  )
}
