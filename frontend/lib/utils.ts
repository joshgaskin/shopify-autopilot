export function formatCurrency(amount: number, currency = 'USD'): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency }).format(amount)
}

export function formatNumber(n: number): string {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M'
  if (n >= 1_000) return (n / 1_000).toFixed(1) + 'K'
  return n.toLocaleString()
}

export function formatDate(date: string): string {
  return new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

export function formatTime(date: string): string {
  return new Date(date).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
}

export function timeAgo(date: string): string {
  const seconds = Math.floor((Date.now() - new Date(date).getTime()) / 1000)
  if (seconds < 60) return `${seconds}s ago`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
  return `${Math.floor(seconds / 86400)}d ago`
}

export function cn(...classes: (string | boolean | undefined | null)[]): string {
  return classes.filter(Boolean).join(' ')
}

export function getStatusColor(status: string): string {
  switch (status) {
    case 'paid': case 'fulfilled': case 'active': return 'text-status-success'
    case 'pending': case 'partial': return 'text-status-warning'
    case 'refunded': case 'unfulfilled': case 'archived': return 'text-status-error'
    default: return 'text-text-secondary'
  }
}

export function getStatusBg(status: string): string {
  switch (status) {
    case 'paid': case 'fulfilled': case 'active': return 'bg-status-success/10 text-status-success'
    case 'pending': case 'partial': return 'bg-status-warning/10 text-status-warning'
    case 'refunded': case 'unfulfilled': case 'archived': return 'bg-status-error/10 text-status-error'
    default: return 'bg-surface-2 text-text-secondary'
  }
}
