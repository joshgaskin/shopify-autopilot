import React from 'react'
import { cn } from '../../lib/utils'

interface ButtonProps {
  children: React.ReactNode
  variant?: 'primary' | 'secondary' | 'ghost'
  size?: 'sm' | 'md'
  onClick?: () => void
  disabled?: boolean
  className?: string
}

const variantClasses: Record<string, string> = {
  primary: 'bg-accent text-surface-0 hover:bg-accent/90 font-medium',
  secondary: 'bg-surface-2 border border-border text-text-primary hover:bg-surface-3',
  ghost: 'bg-transparent text-text-secondary hover:bg-surface-2 hover:text-text-primary',
}

const sizeClasses: Record<string, string> = {
  sm: 'px-3 py-1.5 text-xs',
  md: 'px-4 py-2 text-sm',
}

export default function Button({
  children,
  variant = 'secondary',
  size = 'md',
  onClick,
  disabled = false,
  className,
}: ButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={cn(
        'inline-flex items-center justify-center rounded-md transition-all duration-150 ease-out',
        'disabled:opacity-40 disabled:cursor-not-allowed',
        variantClasses[variant],
        sizeClasses[size],
        className
      )}
    >
      {children}
    </button>
  )
}
