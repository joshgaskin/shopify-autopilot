"""Agent API endpoints — read agent state and actions from the DB."""
import logging

from fastapi import APIRouter, Depends
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.agents.models import AgentAction, AgentState
from app.agents.orchestrator import run_cycle
from app.database import async_session_factory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("/states")
async def get_agent_states(db: AsyncSession = Depends(get_db)):
    """Get current state of all agents."""
    result = await db.execute(select(AgentState))
    states = result.scalars().all()
    return [
        {
            "name": s.name,
            "status": s.status,
            "lastAction": s.last_action,
            "actionCount": s.action_count,
            "lastCycleAt": s.last_cycle_at,
        }
        for s in states
    ]


@router.get("/actions")
async def get_agent_actions(
    limit: int = 50,
    agent: str | None = None,
    action_type: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Get recent agent actions with optional filters."""
    query = select(AgentAction).order_by(desc(AgentAction.id))
    if agent:
        query = query.where(AgentAction.agent == agent)
    if action_type:
        query = query.where(AgentAction.action_type == action_type)
    query = query.limit(limit)

    result = await db.execute(query)
    actions = result.scalars().all()
    return [
        {
            "id": a.action_id,
            "timestamp": a.timestamp,
            "agent": a.agent,
            "type": a.action_type,
            "title": a.title,
            "details": a.details,
            "commentary": a.commentary,
            "status": a.status,
            "productId": a.product_id,
            "cycle": a.cycle,
        }
        for a in actions
    ]


@router.get("/stats")
async def get_agent_stats(db: AsyncSession = Depends(get_db)):
    """Get aggregate agent statistics."""
    # Total actions
    total = await db.execute(select(func.count()).select_from(AgentAction))
    total_count = total.scalar() or 0

    # Per-agent counts
    per_agent = await db.execute(
        select(AgentAction.agent, func.count())
        .group_by(AgentAction.agent)
    )
    agent_counts = {row[0]: row[1] for row in per_agent.all()}

    # Per-type counts
    per_type = await db.execute(
        select(AgentAction.action_type, func.count())
        .group_by(AgentAction.action_type)
    )
    type_counts = {row[0]: row[1] for row in per_type.all()}

    # Latest cycle
    latest_cycle = await db.execute(
        select(func.max(AgentAction.cycle))
    )
    current_cycle = latest_cycle.scalar() or 0

    return {
        "totalActions": total_count,
        "currentCycle": current_cycle,
        "byAgent": agent_counts,
        "byType": type_counts,
    }


@router.post("/trigger")
async def trigger_cycle():
    """Manually trigger an agent orchestration cycle."""
    result = await run_cycle(async_session_factory)
    return {"triggered": True, **result}
