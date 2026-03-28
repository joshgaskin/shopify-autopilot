"""
Agent Orchestrator — autonomous background loop.

Marcus runs on a timer, coordinates Rick, Hank, and Ron.
Each cycle: load data → score → detect issues → narrate → persist.
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.agents.intelligence import (
    score_products,
    detect_stockout_risk,
    detect_slow_movers,
    check_product_health,
    suggest_discounts,
)
from app.agents.voice import narrate, narrate_coordination
from app.agents.models import AgentAction, AgentState
from app.agents.personas import DAILY_INSIGHTS
from app.models import Product, Order, Customer
from app.events import EventManager

logger = logging.getLogger(__name__)

_cycle_count = 0
_has_acted: set[str] = set()


async def _load_store_data(session_factory: async_sessionmaker) -> tuple[list[dict], list[dict], list[dict]]:
    """Load products, orders, inventory from SQLite."""
    async with session_factory() as db:
        # Products
        result = await db.execute(select(Product))
        products = [
            {
                "id": p.id, "title": p.title, "handle": p.handle,
                "status": p.status, "price_min": p.price_min,
                "inventory_total": p.inventory_total,
                "featured_image_url": p.featured_image_url,
                "variants": p.variants or [],
            }
            for p in result.scalars().all()
        ]

        # Orders
        result = await db.execute(select(Order))
        orders = [
            {
                "id": o.id, "order_number": o.order_number,
                "total_price": o.total_price, "financial_status": o.financial_status,
                "line_items": o.line_items or [], "customer_id": o.customer_id,
                "processed_at": o.processed_at, "created_at": o.created_at,
            }
            for o in result.scalars().all()
        ]

        # Inventory from product variants
        inventory = []
        for p in products:
            for v in (p.get("variants") or []):
                if isinstance(v, dict):
                    inventory.append({
                        "product_id": p["id"],
                        "variant_id": v.get("id", ""),
                        "quantity": v.get("inventory_quantity", 0),
                    })

    return products, orders, inventory


async def _save_action(
    session_factory: async_sessionmaker,
    agent: str,
    action_type: str,
    title: str,
    details: str,
    commentary: str,
    status: str = "success",
    product_id: str | None = None,
    cycle: int = 0,
) -> None:
    """Persist an agent action to SQLite and publish SSE event."""
    action_id = f"{agent.lower()}-{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc).isoformat()

    async with session_factory() as db:
        db.add(AgentAction(
            action_id=action_id,
            timestamp=now,
            agent=agent,
            action_type=action_type,
            title=title,
            details=details,
            commentary=commentary,
            status=status,
            product_id=product_id,
            cycle=cycle,
        ))

        # Update agent state
        result = await db.execute(select(AgentState).where(AgentState.name == agent))
        state = result.scalar_one_or_none()
        if state:
            state.status = "active"
            state.last_action = title
            state.action_count += 1
            state.last_cycle_at = now
        else:
            db.add(AgentState(
                name=agent, status="active",
                last_action=title, action_count=1, last_cycle_at=now,
            ))

        await db.commit()

    # Publish to SSE
    em = EventManager.get()
    await em.publish("agent_action", {
        "action_id": action_id,
        "agent": agent,
        "type": action_type,
        "title": title,
        "commentary": commentary,
        "status": status,
        "product_id": product_id,
    })


async def _run_rick(products, orders, inventory, scored, session_factory, cycle):
    """Rick: health checks + stockout alerts."""
    actions = []

    # Health checks
    health_issues = check_product_health(products, inventory)
    for issue in health_issues:
        key = f"health-{issue.product_id}-{issue.issue}"
        if key in _has_acted:
            continue
        _has_acted.add(key)

        context = f"Product '{issue.product_title}' has issue: {issue.issue} (severity: {issue.severity})"
        commentary = await narrate("Rick", context)
        await _save_action(session_factory, "Rick", "health_issue", f"Health issue: {issue.product_title}", issue.issue, commentary, product_id=issue.product_id, cycle=cycle)
        actions.append(("health_issue", issue.product_title))

    # Stockout risk
    at_risk = detect_stockout_risk(scored)
    for product in at_risk:
        key = f"stockout-{product.id}"
        if key in _has_acted:
            continue
        _has_acted.add(key)

        context = f"Product '{product.title}' has only {product.inventory} units left. At {product.velocity} units/day, it will be gone in {product.days_left} days. It's a {product.tier} tier product with trend: {product.trend}."
        commentary = await narrate("Rick", context)
        await _save_action(session_factory, "Rick", "stockout_alert", f"Stockout risk: {product.title}", f"{product.days_left} days left at {product.velocity}/day", commentary, product_id=product.id, cycle=cycle)
        actions.append(("stockout_alert", product.title))

    return actions


async def _run_hank(products, orders, inventory, scored, session_factory, cycle):
    """Hank: product scoring + reorder recommendations."""
    actions = []

    # Log scoring
    key = "scored-all"
    if key not in _has_acted:
        _has_acted.add(key)
        core = sum(1 for p in scored if p.tier == "Core")
        strong = sum(1 for p in scored if p.tier == "Strong")
        slow = sum(1 for p in scored if p.tier == "Slow")
        exit_count = sum(1 for p in scored if p.tier == "Exit")

        context = f"Scored {len(scored)} products: {core} Core, {strong} Strong, {slow} Slow, {exit_count} Exit. Top velocity: {max((p.velocity for p in scored), default=0):.2f}/day."
        commentary = await narrate("Hank", context)
        await _save_action(session_factory, "Hank", "product_scored", f"Scored {len(scored)} products", f"{core} Core, {strong} Strong, {slow} Slow, {exit_count} Exit", commentary, cycle=cycle)
        actions.append(("product_scored", f"{len(scored)} products"))

    # Reorder recommendations
    critical = [p for p in scored if 0 < p.days_left <= 7 and p.tier != "Exit"]
    for product in critical:
        key = f"reorder-{product.id}"
        if key in _has_acted:
            continue
        _has_acted.add(key)

        reorder_qty = max(1, round(product.velocity * 14))
        context = f"Product '{product.title}' ({product.tier} tier) has {product.days_left} days of stock at {product.velocity}/day. Current stock: {product.inventory}. I'd recommend ordering {reorder_qty} units for 14 days of runway."
        commentary = await narrate("Hank", context)
        await _save_action(session_factory, "Hank", "reorder_recommendation", f"Reorder: {product.title}", f"{product.days_left} days left, recommend {reorder_qty} units", commentary, product_id=product.id, cycle=cycle)
        actions.append(("reorder", product.title))

    return actions


async def _run_ron(products, orders, inventory, scored, session_factory, cycle):
    """Ron: slow mover detection + discount suggestions."""
    actions = []

    slow_movers = detect_slow_movers(scored)
    if slow_movers:
        key = "slow-movers-detected"
        if key not in _has_acted:
            _has_acted.add(key)
            names = ", ".join(p.title for p in slow_movers[:3])
            total_value = sum(p.price * p.inventory for p in slow_movers)
            context = f"Found {len(slow_movers)} slow movers: {names}. That's ${total_value:.0f} of capital tied up in declining products."
            commentary = await narrate("Ron", context)
            await _save_action(session_factory, "Ron", "slow_mover_detected", f"Found {len(slow_movers)} slow movers", names, commentary, cycle=cycle)
            actions.append(("slow_movers", len(slow_movers)))

    # Discount suggestions
    suggestions = suggest_discounts(slow_movers)
    for sugg in suggestions[:3]:
        key = f"discount-{sugg.product.id}"
        if key in _has_acted:
            continue
        _has_acted.add(key)

        code = f"CLEAR-{sugg.product.handle[:15].upper()}-{sugg.discount_pct}"
        carrying_cost = sugg.product.price * sugg.product.inventory
        context = f"Product '{sugg.product.title}' is declining (trend ratio {sugg.product.trend_ratio}x, {sugg.product.tier} tier). {sugg.product.inventory} units at ${sugg.product.price} = ${carrying_cost:.0f} of dead capital. Suggesting {sugg.discount_pct}% discount code: {code}"
        commentary = await narrate("Ron", context)
        await _save_action(session_factory, "Ron", "discount_created", f"Discount: {code}", f"{sugg.discount_pct}% off {sugg.product.title}", commentary, product_id=sugg.product.id, cycle=cycle)
        actions.append(("discount", sugg.product.title))

    return actions


async def run_cycle(session_factory: async_sessionmaker) -> dict:
    """Run one full orchestration cycle. Called by the background loop."""
    global _cycle_count
    _cycle_count += 1
    cycle = _cycle_count

    logger.info("=== Agent Cycle %d starting ===", cycle)

    # Load data
    products, orders, inventory = await _load_store_data(session_factory)
    if not products:
        logger.info("No products in database — skipping cycle")
        return {"cycle": cycle, "actions": 0}

    # Score products
    scored = score_products(products, orders, inventory)

    # Set all agents to evaluating
    async with session_factory() as db:
        for name in ["Rick", "Hank", "Ron", "Marcus"]:
            result = await db.execute(select(AgentState).where(AgentState.name == name))
            state = result.scalar_one_or_none()
            if state:
                state.status = "evaluating"
            else:
                db.add(AgentState(name=name, status="evaluating", action_count=0))
        await db.commit()

    # Run agents
    rick_actions = await _run_rick(products, orders, inventory, scored, session_factory, cycle)
    hank_actions = await _run_hank(products, orders, inventory, scored, session_factory, cycle)
    ron_actions = await _run_ron(products, orders, inventory, scored, session_factory, cycle)

    total_actions = len(rick_actions) + len(hank_actions) + len(ron_actions)

    # Marcus coordination summary
    if total_actions > 0:
        summary_parts = []
        if rick_actions:
            summary_parts.append(f"Rick found {len(rick_actions)} issues ({', '.join(t for t, _ in rick_actions)})")
        if hank_actions:
            summary_parts.append(f"Hank completed {len(hank_actions)} assessments")
        if ron_actions:
            summary_parts.append(f"Ron identified {len(ron_actions)} financial actions")

        # Check for conflicts (e.g., stockout + discount on same product)
        rick_products = {n for t, n in rick_actions if t == "stockout_alert"}
        ron_products = {n for t, n in ron_actions if t == "discount"}
        conflicts = rick_products & ron_products

        conflict_note = ""
        if conflicts:
            conflict_note = f" CONFLICT: {', '.join(conflicts)} flagged for both stockout AND discount. I'm overriding the discount — we don't discount products that are selling well."

        context = f"Cycle {cycle} complete. {'; '.join(summary_parts)}.{conflict_note} Total actions this cycle: {total_actions}."
        commentary = await narrate_coordination(context)
        await _save_action(session_factory, "Marcus", "daily_insight", f"Cycle {cycle} summary", context, commentary, cycle=cycle)

    # Daily insight (once per session)
    insight_key = "daily-insight"
    if insight_key not in _has_acted:
        _has_acted.add(insight_key)
        day_of_year = datetime.now(timezone.utc).timetuple().tm_yday
        insight = DAILY_INSIGHTS[day_of_year % len(DAILY_INSIGHTS)]
        context = f"Daily merchandising insight — {insight['topic']}: {insight['data']}. Relate this to what we're seeing in the store data right now. We have {len(products)} products, {len(orders)} orders."
        commentary = await narrate_coordination(context)
        await _save_action(session_factory, "Marcus", "daily_insight", f"Daily insight: {insight['topic']}", insight["data"], commentary, cycle=cycle)

    # Set agents back to active/idle
    async with session_factory() as db:
        for name in ["Rick", "Hank", "Ron", "Marcus"]:
            result = await db.execute(select(AgentState).where(AgentState.name == name))
            state = result.scalar_one_or_none()
            if state:
                state.status = "active" if state.action_count > 0 else "idle"
        await db.commit()

    logger.info("=== Agent Cycle %d complete — %d actions ===", cycle, total_actions)
    return {"cycle": cycle, "actions": total_actions}


async def run_agent_loop(session_factory: async_sessionmaker, interval: int = 60) -> None:
    """Background loop — runs orchestration cycles forever."""
    logger.info("Agent orchestration loop started (interval: %ds)", interval)

    # Run first cycle immediately
    try:
        await run_cycle(session_factory)
    except Exception as e:
        logger.error("Agent cycle failed: %s", e, exc_info=True)

    # Then run on interval
    while True:
        await asyncio.sleep(interval)
        try:
            await run_cycle(session_factory)
        except Exception as e:
            logger.error("Agent cycle failed: %s", e, exc_info=True)
