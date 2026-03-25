import { useState, useEffect, useRef } from 'react'
import { API_BASE } from '../lib/constants'
import type { LiveEvent } from '../lib/types'

export function useEventStream(maxEvents = 50) {
  const [events, setEvents] = useState<LiveEvent[]>([])
  const [connected, setConnected] = useState(false)
  const eventSourceRef = useRef<EventSource | null>(null)

  useEffect(() => {
    const es = new EventSource(`${API_BASE}/events/stream`)
    eventSourceRef.current = es

    es.onopen = () => setConnected(true)
    es.onmessage = (e) => {
      try {
        const event: LiveEvent = JSON.parse(e.data)
        setEvents((prev) => [event, ...prev].slice(0, maxEvents))
      } catch {
        // ignore malformed events
      }
    }
    es.onerror = () => setConnected(false)

    return () => {
      es.close()
      setConnected(false)
    }
  }, [maxEvents])

  const lastEvent = events[0] || null

  return { events, lastEvent, connected }
}
