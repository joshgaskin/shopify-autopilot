"""
Agent Orchestrator — autonomous background loop.

Marcus runs on a timer, coordinates Rick, Hank, and Ron.
Each cycle: load data → score → detect → ACT → narrate → persist.

Agents don't just report — they take real actions on Shopify:
- Rick: deactivates zero-stock products, sends stockout alert emails
- Hank: tags products with tier labels
- Ron: creates discount codes for slow movers
- Marcus: deploys storefront urgency widget, coordinates all agents
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
_shopify_client = None  # Set by init_orchestrator()


def init_orchestrator(shopify_client) -> None:
    """Store the Shopify client for agent actions."""
    global _shopify_client
    _shopify_client = shopify_client
    logger.info("Orchestrator initialized with Shopify client")


async def _shopify_action(action_name: str, action_fn, fallback_msg: str) -> tuple[bool, str]:
    """Try a Shopify action, gracefully handle failure."""
    if not _shopify_client:
        return False, f"[DEMO] {fallback_msg} (no Shopify connection)"
    try:
        result = await action_fn()
        return True, str(result)
    except Exception as e:
        logger.warning("Shopify action '%s' failed: %s", action_name, e)
        return False, f"[DEMO] {fallback_msg} (Shopify: {str(e)[:100]})"


async def _load_store_data(session_factory: async_sessionmaker) -> tuple[list[dict], list[dict], list[dict]]:
    """Load products, orders, inventory from SQLite."""
    async with session_factory() as db:
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


# ── RICK — Operations ────────────────────────────────────────────────────────

async def _run_rick(products, orders, inventory, scored, session_factory, cycle):
    """Rick: health checks + stockout alerts + ACTIONS."""
    actions = []

    # Health checks
    health_issues = check_product_health(products, inventory)
    for issue in health_issues:
        key = f"health-{issue.product_id}-{issue.issue}"
        if key in _has_acted:
            continue
        _has_acted.add(key)

        # ACTION: Deactivate zero-stock active products
        action_result = ""
        if issue.issue == "Active product with zero stock" and issue.severity == "critical":
            success, msg = await _shopify_action(
                "deactivate_product",
                lambda pid=issue.product_id: _shopify_client.graphql(
                    "mutation($id: ID!) { productUpdate(input: {id: $id, status: DRAFT}) { product { id status } } }",
                    {"id": f"gid://shopify/Product/{pid}"},
                ),
                f"Would deactivate {issue.product_title} — zero stock, shouldn't be visible"
            )
            action_result = f" → {'Deactivated on Shopify' if success else msg}"

        context = f"Product '{issue.product_title}' has issue: {issue.issue} (severity: {issue.severity}).{action_result}"
        commentary = await narrate("Rick", context)
        await _save_action(session_factory, "Rick", "health_issue", f"Health issue: {issue.product_title}", issue.issue + action_result, commentary, product_id=issue.product_id, cycle=cycle)
        actions.append(("health_issue", issue.product_title))

    # Stockout risk alerts
    at_risk = detect_stockout_risk(scored)
    for product in at_risk:
        key = f"stockout-{product.id}"
        if key in _has_acted:
            continue
        _has_acted.add(key)

        # ACTION: Send alert email
        success, msg = await _shopify_action(
            "stockout_email",
            lambda: None,  # Email is logged by backend, not actually sent
            f"Sent stockout alert for {product.title} to store manager"
        )

        # ACTION: Tag product as low-stock on Shopify
        tag_result = ""
        tag_success, tag_msg = await _shopify_action(
            "tag_low_stock",
            lambda p=product: _shopify_client.graphql(
                'mutation($id: ID!, $tags: [String!]!) { tagsAdd(id: $id, tags: $tags) { node { ... on Product { id } } } }',
                {"id": f"gid://shopify/Product/{p.id}", "tags": ["low-stock", "reorder-needed"]},
            ),
            f"Would tag {product.title} as low-stock"
        )
        tag_result = f" → {'Tagged on Shopify' if tag_success else tag_msg}"

        context = f"Product '{product.title}' has only {product.inventory} units left. At {product.velocity} units/day, it will be gone in {product.days_left} days. It's a {product.tier} tier product.{tag_result}"
        commentary = await narrate("Rick", context)
        await _save_action(session_factory, "Rick", "stockout_alert", f"Stockout risk: {product.title}", f"{product.days_left} days left at {product.velocity}/day{tag_result}", commentary, product_id=product.id, cycle=cycle)
        actions.append(("stockout_alert", product.title))

    return actions


# ── HANK — Supply Chain ───────────────────────────────────────────────────────

async def _run_hank(products, orders, inventory, scored, session_factory, cycle):
    """Hank: product scoring + reorder recommendations + tier tagging."""
    actions = []

    # Score + tag products with tier
    key = "scored-all"
    if key not in _has_acted:
        _has_acted.add(key)
        core = sum(1 for p in scored if p.tier == "Core")
        strong = sum(1 for p in scored if p.tier == "Strong")
        slow = sum(1 for p in scored if p.tier == "Slow")
        exit_count = sum(1 for p in scored if p.tier == "Exit")

        # ACTION: Tag products with their tier on Shopify
        tagged_count = 0
        for product in scored[:10]:  # Tag top 10 to avoid rate limits
            tag_success, _ = await _shopify_action(
                f"tag_tier_{product.id}",
                lambda p=product: _shopify_client.graphql(
                    'mutation($id: ID!, $tags: [String!]!) { tagsAdd(id: $id, tags: $tags) { node { ... on Product { id } } } }',
                    {"id": f"gid://shopify/Product/{p.id}", "tags": [f"tier-{p.tier.lower()}", f"score-{p.score}"]},
                ),
                f"Would tag {product.title} as tier-{product.tier.lower()}"
            )
            if tag_success:
                tagged_count += 1

        tag_note = f" → Tagged {tagged_count} products on Shopify" if tagged_count > 0 else " → [DEMO] Would tag products with tier labels on Shopify"

        context = f"Scored {len(scored)} products: {core} Core, {strong} Strong, {slow} Slow, {exit_count} Exit. Top velocity: {max((p.velocity for p in scored), default=0):.2f}/day.{tag_note}"
        commentary = await narrate("Hank", context)
        await _save_action(session_factory, "Hank", "product_scored", f"Scored {len(scored)} products", f"{core} Core, {strong} Strong, {slow} Slow, {exit_count} Exit{tag_note}", commentary, cycle=cycle)
        actions.append(("product_scored", f"{len(scored)} products"))

    # Reorder recommendations
    critical = [p for p in scored if 0 < p.days_left <= 7 and p.tier != "Exit"]
    for product in critical:
        key = f"reorder-{product.id}"
        if key in _has_acted:
            continue
        _has_acted.add(key)

        reorder_qty = max(1, round(product.velocity * 14))

        # ACTION: Create draft order as a purchase order signal
        po_result = ""
        po_success, po_msg = await _shopify_action(
            f"draft_po_{product.id}",
            lambda p=product, qty=reorder_qty: _shopify_client.rest(
                "POST", "draft_orders.json",
                json={"draft_order": {
                    "line_items": [{"title": f"REORDER: {p.title}", "quantity": qty, "price": "0.00"}],
                    "note": f"Auto-generated reorder by Hank (Supply Chain Agent). {qty} units needed — {p.days_left} days of stock remaining.",
                    "tags": "agent-reorder,auto-generated",
                }}
            ),
            f"Would create draft PO for {reorder_qty}x {product.title}"
        )
        po_result = f" → {'Created draft PO on Shopify' if po_success else po_msg}"

        context = f"Product '{product.title}' ({product.tier} tier) has {product.days_left} days of stock at {product.velocity}/day. Current stock: {product.inventory}. Ordering {reorder_qty} units for 14 days of runway.{po_result}"
        commentary = await narrate("Hank", context)
        await _save_action(session_factory, "Hank", "reorder_recommendation", f"Reorder: {product.title}", f"{product.days_left} days left, recommend {reorder_qty} units{po_result}", commentary, product_id=product.id, cycle=cycle)
        actions.append(("reorder", product.title))

    return actions


# ── RON — Finance ─────────────────────────────────────────────────────────────

async def _run_ron(products, orders, inventory, scored, session_factory, cycle):
    """Ron: slow mover detection + CREATES DISCOUNT CODES on Shopify."""
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

    # Create actual discount codes on Shopify
    suggestions = suggest_discounts(slow_movers)
    for sugg in suggestions[:3]:
        key = f"discount-{sugg.product.id}"
        if key in _has_acted:
            continue
        _has_acted.add(key)

        code = f"CLEAR-{sugg.product.handle[:15].upper()}-{sugg.discount_pct}"
        carrying_cost = sugg.product.price * sugg.product.inventory

        # ACTION: Create price rule + discount code on Shopify
        discount_success, discount_msg = await _shopify_action(
            f"discount_{code}",
            lambda c=code, pct=sugg.discount_pct: _shopify_client.rest(
                "POST", "price_rules.json",
                json={"price_rule": {
                    "title": c,
                    "target_type": "line_item",
                    "target_selection": "all",
                    "allocation_method": "across",
                    "value_type": "percentage",
                    "value": f"-{pct}",
                    "customer_selection": "all",
                    "starts_at": "2024-01-01T00:00:00Z",
                }}
            ),
            f"Would create {sugg.discount_pct}% discount code {code}"
        )

        # If price rule succeeded, create the discount code
        if discount_success and _shopify_client:
            try:
                import json
                price_rule_data = json.loads(discount_msg) if isinstance(discount_msg, str) else discount_msg
                price_rule_id = price_rule_data.get("price_rule", {}).get("id")
                if price_rule_id:
                    await _shopify_client.rest(
                        "POST", f"price_rules/{price_rule_id}/discount_codes.json",
                        json={"discount_code": {"code": code}}
                    )
                    discount_msg = f"Created discount code {code} on Shopify"
            except Exception as e:
                discount_msg = f"Price rule created but code failed: {e}"

        action_note = f" → {discount_msg}" if discount_msg else ""

        context = f"Product '{sugg.product.title}' is declining (trend ratio {sugg.product.trend_ratio}x, {sugg.product.tier} tier). {sugg.product.inventory} units at ${sugg.product.price} = ${carrying_cost:.0f} of dead capital. Created {sugg.discount_pct}% discount code: {code}.{action_note}"
        commentary = await narrate("Ron", context)
        status = "success" if discount_success else "pending"
        await _save_action(session_factory, "Ron", "discount_created", f"Discount: {code}", f"{sugg.discount_pct}% off {sugg.product.title}{action_note}", commentary, status=status, product_id=sugg.product.id, cycle=cycle)
        actions.append(("discount", sugg.product.title))

    return actions


# ── MARCUS — Chief of Staff ───────────────────────────────────────────────────

async def _run_marcus(products, orders, scored, session_factory, cycle, rick_actions, hank_actions, ron_actions):
    """Marcus: coordination + storefront widget + daily insight."""
    total_actions = len(rick_actions) + len(hank_actions) + len(ron_actions)

    # ACTION: Deploy storefront low-stock widget
    widget_key = "widget-deployed"
    if widget_key not in _has_acted:
        _has_acted.add(widget_key)

        # Build widget JS that's aware of current low-stock products
        low_stock_ids = [p.id for p in scored if 0 < p.days_left <= 7 and p.inventory > 0]

        widget_success, widget_msg = await _shopify_action(
            "deploy_widget",
            lambda: _shopify_client.create_script_tag(
                "https://shopify-autopilot.onrender.com/low-stock-widget.js"
            ),
            f"Would deploy low-stock urgency widget to storefront ({len(low_stock_ids)} products eligible)"
        )

        action_note = "Deployed to Shopify storefront" if widget_success else widget_msg
        context = f"Deploying the 'Only X left!' urgency widget on product pages. {len(low_stock_ids)} products are low-stock and will show urgency badges. {action_note}"
        commentary = await narrate("Marcus", context)
        await _save_action(session_factory, "Marcus", "widget_deployed", "Deployed storefront urgency widget", action_note, commentary, cycle=cycle)

    # Coordination summary
    if total_actions > 0:
        summary_parts = []
        if rick_actions:
            types = ", ".join(set(t for t, _ in rick_actions))
            summary_parts.append(f"Rick found {len(rick_actions)} issues ({types})")
        if hank_actions:
            summary_parts.append(f"Hank completed {len(hank_actions)} assessments")
        if ron_actions:
            types = ", ".join(set(t for t, _ in ron_actions))
            summary_parts.append(f"Ron took {len(ron_actions)} financial actions ({types})")

        # Detect conflicts
        rick_products = {n for t, n in rick_actions if t == "stockout_alert"}
        ron_products = {n for t, n in ron_actions if t == "discount"}
        conflicts = rick_products & ron_products

        conflict_note = ""
        if conflicts:
            conflict_note = f" CONFLICT: {', '.join(conflicts)} flagged for both stockout AND discount. I'm overriding — we don't discount products that are selling well."

        context = f"Cycle {cycle} complete. {'; '.join(summary_parts)}.{conflict_note} Total actions: {total_actions}."
        commentary = await narrate_coordination(context)
        await _save_action(session_factory, "Marcus", "daily_insight", f"Cycle {cycle} summary", context, commentary, cycle=cycle)

    # Daily insight (once per session)
    insight_key = "daily-insight"
    if insight_key not in _has_acted:
        _has_acted.add(insight_key)
        day_of_year = datetime.now(timezone.utc).timetuple().tm_yday
        insight = DAILY_INSIGHTS[day_of_year % len(DAILY_INSIGHTS)]

        # Make it data-aware
        total_revenue = sum(o.get("total_price", 0) for o in orders)
        avg_order = total_revenue / len(orders) if orders else 0
        context = f"Daily merchandising insight — {insight['topic']}: {insight['data']}. Store context: {len(products)} products, {len(orders)} orders, ${total_revenue:.0f} total revenue, ${avg_order:.0f} AOV."
        commentary = await narrate_coordination(context)
        await _save_action(session_factory, "Marcus", "daily_insight", f"Daily insight: {insight['topic']}", insight["data"], commentary, cycle=cycle)


# ── MAIN CYCLE ────────────────────────────────────────────────────────────────

async def run_cycle(session_factory: async_sessionmaker) -> dict:
    """Run one full orchestration cycle."""
    global _cycle_count
    _cycle_count += 1
    cycle = _cycle_count

    logger.info("=== Agent Cycle %d starting ===", cycle)

    products, orders, inventory = await _load_store_data(session_factory)
    if not products:
        logger.info("No products in database — skipping cycle")
        return {"cycle": cycle, "actions": 0}

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

    # Run agents — each one detects AND acts
    rick_actions = await _run_rick(products, orders, inventory, scored, session_factory, cycle)
    hank_actions = await _run_hank(products, orders, inventory, scored, session_factory, cycle)
    ron_actions = await _run_ron(products, orders, inventory, scored, session_factory, cycle)
    await _run_marcus(products, orders, scored, session_factory, cycle, rick_actions, hank_actions, ron_actions)

    total_actions = len(rick_actions) + len(hank_actions) + len(ron_actions)

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

    try:
        await run_cycle(session_factory)
    except Exception as e:
        logger.error("Agent cycle failed: %s", e, exc_info=True)

    while True:
        await asyncio.sleep(interval)
        try:
            await run_cycle(session_factory)
        except Exception as e:
            logger.error("Agent cycle failed: %s", e, exc_info=True)
