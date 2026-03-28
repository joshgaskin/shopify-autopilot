"""Agent API endpoints — read agent state and actions from the DB."""
import logging

from fastapi import APIRouter, Depends
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.agents.models import AgentAction, AgentState, Discount
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
            "reverted": a.reverted,
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


@router.get("/discounts")
async def get_discounts(db: AsyncSession = Depends(get_db)):
    """Get all discount codes created by Ron."""
    result = await db.execute(select(Discount).order_by(desc(Discount.id)))
    return [
        {
            "id": d.id,
            "code": d.code,
            "percentage": d.percentage,
            "productId": d.product_id,
            "productTitle": d.product_title,
            "createdBy": d.created_by,
            "status": d.status,
            "createdAt": d.created_at,
        }
        for d in result.scalars().all()
    ]


@router.post("/trigger")
async def trigger_cycle():
    """Manually trigger an agent orchestration cycle."""
    result = await run_cycle(async_session_factory)
    return {"triggered": True, **result}


@router.post("/reset")
async def reset_agents(db: AsyncSession = Depends(get_db)):
    """Reset all agent state and trigger a fresh cycle with new Claude commentary."""
    import app.agents.orchestrator as orch
    from app.agents.models import PurchaseOrder, POLineItem

    await db.execute(AgentAction.__table__.delete())
    await db.execute(AgentState.__table__.delete())
    await db.execute(Discount.__table__.delete())
    await db.execute(POLineItem.__table__.delete())
    await db.execute(PurchaseOrder.__table__.delete())
    await db.commit()

    orch._has_acted.clear()
    orch._cycle_count = 0
    orch._initialized = False

    result = await run_cycle(async_session_factory)
    return {"reset": True, **result}


@router.post("/actions/{action_id}/revert")
async def revert_action(action_id: str, db: AsyncSession = Depends(get_db)):
    """Revert an agent action. Marks it as reverted and removes the dedup key so it can be re-evaluated."""
    from datetime import datetime, timezone
    from app.agents.orchestrator import _has_acted

    result = await db.execute(select(AgentAction).where(AgentAction.action_id == action_id))
    action = result.scalar_one_or_none()
    if not action:
        return {"error": "Action not found"}

    if action.reverted:
        return {"error": "Already reverted"}

    action.reverted = True
    action.reverted_at = datetime.now(timezone.utc).isoformat()
    action.revert_note = "Reverted by user"
    action.status = "reverted"
    await db.commit()

    # Remove the dedup key so the agent can re-evaluate on next cycle
    pid = action.product_id or ""
    keys_to_remove = []
    if action.action_type == "health_issue":
        keys_to_remove.append(f"health-{pid}-{action.details.split(' →')[0]}")
    elif action.action_type == "stockout_alert":
        keys_to_remove.append(f"stockout-{pid}")
    elif action.action_type == "discount_created":
        keys_to_remove.append(f"discount-{pid}")
    elif action.action_type == "reorder_recommendation":
        keys_to_remove.append(f"reorder-{pid}")
    elif action.action_type == "product_tagged":
        keys_to_remove.append(f"story-{pid}")
    elif action.action_type == "widget_deployed":
        keys_to_remove.append("widget-deployed")

    for key in keys_to_remove:
        _has_acted.discard(key)

    return {
        "reverted": True,
        "actionId": action_id,
        "agent": action.agent,
        "type": action.action_type,
        "keysCleared": keys_to_remove,
    }
