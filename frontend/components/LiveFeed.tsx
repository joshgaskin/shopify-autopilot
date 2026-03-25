import React from 'react'
import { useEventStream } from '../hooks/useEventStream'
import { timeAgo } from '../lib/utils'
import type { LiveEvent } from '../lib/types'

function getEventIcon(type: LiveEvent['event_type']) {
  switch (type) {
    case 'new_order':
      return (
        <svg width="14" height="14" viewBox="0 0 14 14" className="text-status-success">
          <circle cx="7" cy="7" r="6" stroke="currentColor" strokeWidth="1.2" fill="none" />
          <path d="M4.5 7l2 2 3-3.5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" fill="none" />
        </svg>
      )
    case 'refund_issued':
      return (
        <svg width="14" height="14" viewBox="0 0 14 14" className="text-status-error">
          <circle cx="7" cy="7" r="6" stroke="currentColor" strokeWidth="1.2" fill="none" />
          <path d="M5 5l4 4M9 5l-4 4" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" fill="none" />
        </svg>
      )
    case 'product_update':
      return (
        <svg width="14" height="14" viewBox="0 0 14 14" className="text-status-info">
          <rect x="2" y="2" width="10" height="10" rx="2" stroke="currentColor" strokeWidth="1.2" fill="none" />
          <path d="M5 7h4" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" fill="none" />
        </svg>
      )
    case 'inventory_change':
      return (
        <svg width="14" height="14" viewBox="0 0 14 14" className="text-status-warning">
          <path d="M3 10V5l4-3 4 3v5" stroke="currentColor" strokeWidth="1.2" strokeLinejoin="round" fill="none" />
          <path d="M5 10V8h4v2" stroke="currentColor" strokeWidth="1.2" fill="none" />
        </svg>
      )
    case 'customer_created':
      return (
        <svg width="14" height="14" viewBox="0 0 14 14" className="text-status-info">
          <circle cx="7" cy="5" r="2.5" stroke="currentColor" strokeWidth="1.2" fill="none" />
          <path d="M3 12c0-2.2 1.8-4 4-4s4 1.8 4 4" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" fill="none" />
        </svg>
      )
  }
}

function getEventDescription(event: LiveEvent): string {
  const p = event.payload
  switch (event.event_type) {
    case 'new_order':
      return `Order #${p.order_number || '—'} — $${p.total_price?.toFixed(2) || '0.00'}`
    case 'refund_issued':
      return `Refund on #${p.order_number || '—'}`
    case 'product_update':
      return `${p.title || 'Product'} updated`
    case 'inventory_change':
      return `${p.product_title || 'Item'} stock changed`
    case 'customer_created':
      return `New customer: ${p.email || 'unknown'}`
    default:
      return event.event_type
  }
}

interface LiveFeedProps {
  maxEvents?: number
  mockEvents?: LiveEvent[]
}

export default function LiveFeed({ maxEvents = 20, mockEvents }: LiveFeedProps) {
  const { events: liveEvents, connected } = useEventStream(maxEvents)
  const events = mockEvents && liveEvents.length === 0 ? mockEvents : liveEvents

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-text-primary">Live Feed</h3>
        <div className="flex items-center gap-1.5">
          <span
            className={`w-1.5 h-1.5 rounded-full ${
              connected ? 'bg-status-success' : 'bg-status-error'
            }`}
          />
          <span className="text-xs text-text-tertiary">
            {connected ? 'Connected' : 'Offline'}
          </span>
        </div>
      </div>

      {/* Events list */}
      <div className="flex-1 overflow-y-auto space-y-0.5">
        {events.length === 0 ? (
          <p className="text-xs text-text-tertiary py-4 text-center">
            No events yet
          </p>
        ) : (
          events.slice(0, maxEvents).map((event) => (
            <div
              key={event.id}
              className="flex items-start gap-2.5 px-2 py-2 rounded-md hover:bg-surface-2 transition-colors duration-150 ease-out"
            >
              <div className="mt-0.5 flex-shrink-0">{getEventIcon(event.event_type)}</div>
              <div className="flex-1 min-w-0">
                <p className="text-xs text-text-primary truncate">
                  {getEventDescription(event)}
                </p>
                <p className="text-xs text-text-tertiary">
                  {timeAgo(event.created_at)}
                </p>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
