"""Events endpoints — SSE stream and history."""
from fastapi import APIRouter, Query
from sse_starlette.sse import EventSourceResponse

from app.events import EventManager

router = APIRouter(tags=["events"])


@router.get("/events/stream")
async def event_stream():
    """Server-Sent Events stream for real-time updates."""
    events = EventManager.get()
    return EventSourceResponse(events.subscribe())


@router.get("/events/history")
async def event_history(limit: int = Query(100, ge=1, le=500)):
    """Get recent events from the in-memory buffer."""
    events = EventManager.get()
    return events.get_history(limit=limit)
