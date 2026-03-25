"""
In-memory event manager for SSE (Server-Sent Events).

Singleton pattern — call EventManager.get() from anywhere.
Events are published to all active subscribers and buffered in a ring buffer for history.
"""
import asyncio
import json
import logging
import uuid
from collections import deque
from datetime import datetime, timezone
from typing import Any, AsyncGenerator

logger = logging.getLogger(__name__)


class EventManager:
    """Manages real-time event broadcasting via SSE."""

    _instance: "EventManager | None" = None

    def __init__(self, max_history: int = 500) -> None:
        self._subscribers: list[asyncio.Queue] = []
        self._history: deque[dict[str, Any]] = deque(maxlen=max_history)

    @classmethod
    def get(cls) -> "EventManager":
        """Get or create the singleton EventManager."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def publish(self, event_type: str, payload: dict[str, Any]) -> None:
        """Publish an event to all subscribers and add to history."""
        event = {
            "id": str(uuid.uuid4()),
            "event_type": event_type,
            "payload": payload,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._history.append(event)

        dead: list[asyncio.Queue] = []
        for queue in self._subscribers:
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                dead.append(queue)

        for q in dead:
            self._subscribers.remove(q)

        logger.debug("Published %s to %d subscribers", event_type, len(self._subscribers))

    async def subscribe(self) -> AsyncGenerator[dict[str, Any], None]:
        """Subscribe to the event stream. Yields SSE-formatted dicts."""
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._subscribers.append(queue)
        logger.info("New SSE subscriber (total: %d)", len(self._subscribers))

        try:
            while True:
                event = await queue.get()
                yield {
                    "event": event["event_type"],
                    "id": event["id"],
                    "data": json.dumps(event),
                }
        except asyncio.CancelledError:
            pass
        finally:
            if queue in self._subscribers:
                self._subscribers.remove(queue)
            logger.info("SSE subscriber disconnected (remaining: %d)", len(self._subscribers))

    def get_history(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get recent events from the ring buffer."""
        items = list(self._history)
        return items[-limit:]
