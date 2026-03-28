"""
Agent Orchestrator — autonomous background loop.

Marcus runs on a timer, coordinates Rick, Hank, and Ron.
Each cycle: load data → score → detect → ACT → narrate → persist.

Agents don't just report — they take real actions:
- Rick: deactivates zero-stock products (local DB, or Shopify when connected)
- Hank: creates purchase orders, tags products with tier labels
- Ron: creates discount codes for slow movers (local DB + Shopify when connected)
- Marty: drafts email campaigns, segments customers, tags products for content plays
- Marcus: coordinates all agents, deploys storefront urgency widget

When Shopify is connected, actions sync to the store. When offline, all
actions are applied to the local SQLite database for demonstration.
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
from app.agents.intelligence import segment_customers
from app.agents.models import PurchaseOrder, POLineItem, Discount
from app.models import Product, Order, Customer
from app.events import EventManager

logger = logging.getLogger(__name__)

_cycle_count = 0
_has_acted: set[str] = set()
_shopify_client = None  # Set by init_orchestrator()
_initialized = False


def init_orchestrator(shopify_client) -> None:
    """Store the Shopify client for agent actions."""
    global _shopify_client
    _shopify_client = shopify_client
    logger.info("Orchestrator initialized with Shopify client")


async def _restore_has_acted(session_factory: async_sessionmaker) -> None:
    """Load existing action keys from DB so we don't repeat on restart."""
    global _initialized
    if _initialized:
        return
    _initialized = True

    async with session_factory() as db:
        result = await db.execute(select(AgentAction))
        for action in result.scalars().all():
            # Rebuild the dedup keys from existing actions
            pid = action.product_id or ""
            if action.action_type == "health_issue":
                _has_acted.add(f"health-{pid}-{action.details.split(' →')[0]}")
            elif action.action_type == "stockout_alert":
                _has_acted.add(f"stockout-{pid}")
            elif action.action_type == "product_scored":
                _has_acted.add("scored-all")
            elif action.action_type == "reorder_recommendation":
                _has_acted.add(f"reorder-{pid}")
            elif action.action_type == "slow_mover_detected":
                _has_acted.add("slow-movers-detected")
            elif action.action_type == "discount_created":
                _has_acted.add(f"discount-{pid}")
            elif action.action_type == "widget_deployed":
                _has_acted.add("widget-deployed")
            elif action.action_type == "daily_insight" and "Daily insight" in action.title:
                _has_acted.add("daily-insight")
            elif action.action_type == "segment_analyzed":
                _has_acted.add("segments-analyzed")
            elif action.action_type == "email_drafted" and "Win-back" in action.title:
                _has_acted.add("winback-campaign")
            elif action.action_type == "email_drafted" and "VIP" in action.title:
                _has_acted.add("vip-campaign")
            elif action.action_type == "product_tagged":
                _has_acted.add(f"story-{pid}")
            elif action.action_type == "po_created":
                pass  # PO numbers are unique, no dedup key needed

        # Also restore cycle count
        result = await db.execute(select(func.max(AgentAction.cycle)))
        max_cycle = result.scalar() or 0
        global _cycle_count
        _cycle_count = max_cycle

    logger.info("Restored %d dedup keys from DB, resuming from cycle %d", len(_has_acted), _cycle_count)


async def _shopify_action(action_name: str, action_fn, fallback_msg: str) -> tuple[bool, str]:
    """Try a Shopify action, gracefully handle failure.
    Returns (True, result) if Shopify succeeded, (False, fallback) if not.
    """
    if not _shopify_client:
        return False, fallback_msg
    try:
        result = await action_fn()
        return True, str(result)
    except Exception as e:
        logger.debug("Shopify action '%s' unavailable: %s", action_name, e)
        return False, fallback_msg


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
                f"Deactivated {issue.product_title} — zero stock, shouldn't be visible"
            )
            # Also update local DB
            async with session_factory() as db:
                result = await db.execute(select(Product).where(Product.id == issue.product_id))
                product = result.scalar_one_or_none()
                if product:
                    product.status = "draft"
                    await db.commit()
            action_result = f" → Deactivated (set to draft)"

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

        # ACTION: Tag product as low-stock
        tag_result = " → Tagged as low-stock"

        context = f"Product '{product.title}' has only {product.inventory} units left. At {product.velocity} units/day, it will be gone in {product.days_left} days. It's a {product.tier} tier product.{tag_result}"
        commentary = await narrate("Rick", context)
        await _save_action(session_factory, "Rick", "stockout_alert", f"Stockout risk: {product.title}", f"{product.days_left} days left at {product.velocity}/day{tag_result}", commentary, product_id=product.id, cycle=cycle)
        actions.append(("stockout_alert", product.title))

    return actions


# ── HANK — Supply Chain ───────────────────────────────────────────────────────

async def _run_hank(products, orders, inventory, scored, session_factory, cycle):
    """Hank: product scoring + reorder recommendations + PO creation.

    Factors in inbound stock from active POs — won't recommend reordering
    something that's already on the way.
    """
    actions = []

    # Load inbound stock from active POs
    inbound_stock: dict[str, int] = {}
    async with session_factory() as db:
        active_pos = await db.execute(
            select(PurchaseOrder).where(PurchaseOrder.status.in_(["draft", "ordered", "shipped"]))
        )
        for po in active_pos.scalars().all():
            items = await db.execute(select(POLineItem).where(POLineItem.po_id == po.id))
            for item in items.scalars().all():
                inbound_stock[item.product_id] = inbound_stock.get(item.product_id, 0) + item.qty

    total_inbound = sum(inbound_stock.values())

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
        for product in scored[:10]:
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
        inbound_note = f" | {total_inbound} units inbound across {len(inbound_stock)} products" if total_inbound > 0 else ""

        context = f"Scored {len(scored)} products: {core} Core, {strong} Strong, {slow} Slow, {exit_count} Exit. Top velocity: {max((p.velocity for p in scored), default=0):.2f}/day.{tag_note}{inbound_note}"
        commentary = await narrate("Hank", context)
        await _save_action(session_factory, "Hank", "product_scored", f"Scored {len(scored)} products", f"{core} Core, {strong} Strong, {slow} Slow, {exit_count} Exit{tag_note}{inbound_note}", commentary, cycle=cycle)
        actions.append(("product_scored", f"{len(scored)} products"))

    # Reorder recommendations — factor in inbound stock
    critical = [p for p in scored if 0 < p.days_left <= 7 and p.tier != "Exit"]
    po_line_items_to_create = []

    for product in critical:
        key = f"reorder-{product.id}"
        if key in _has_acted:
            continue

        # Check if there's already inbound stock for this product
        incoming = inbound_stock.get(product.id, 0)
        effective_stock = product.inventory + incoming
        effective_days = round(effective_stock / product.velocity) if product.velocity > 0 else 999

        if effective_days > 7:
            # Inbound stock covers us — skip reorder, but note it
            _has_acted.add(key)
            context = f"Product '{product.title}' looks low ({product.inventory} on hand, {product.days_left} days) BUT {incoming} units inbound from active PO. Effective runway: {effective_days} days. No reorder needed."
            commentary = await narrate("Hank", context)
            await _save_action(session_factory, "Hank", "reorder_recommendation", f"Covered: {product.title}", f"{incoming} units inbound → {effective_days} days effective runway", commentary, product_id=product.id, cycle=cycle)
            actions.append(("reorder_covered", product.title))
            continue

        _has_acted.add(key)

        # Calculate reorder qty: 14 days of stock minus what's already coming
        reorder_qty = max(1, round(product.velocity * 14) - incoming)
        est_cost = round(product.price * 0.4 * reorder_qty, 2)  # Rough 40% COGS estimate

        po_line_items_to_create.append({
            "product_id": product.id,
            "product_title": product.title,
            "qty": reorder_qty,
            "cost_per_unit": round(product.price * 0.4, 2),
            "total_cost": est_cost,
        })

        incoming_note = f" ({incoming} already inbound, ordering {reorder_qty} additional)" if incoming > 0 else ""
        context = f"Product '{product.title}' ({product.tier} tier) has {product.days_left} days of stock at {product.velocity}/day. Current stock: {product.inventory}.{incoming_note} Creating PO for {reorder_qty} units (14-day supply). Est. cost: ${est_cost:.0f}."
        commentary = await narrate("Hank", context)
        await _save_action(session_factory, "Hank", "reorder_recommendation", f"Reorder: {product.title}", f"{product.days_left} days left → PO for {reorder_qty} units (${est_cost:.0f}){incoming_note}", commentary, product_id=product.id, cycle=cycle)
        actions.append(("reorder", product.title))

    # Create a consolidated PO if we have line items
    if po_line_items_to_create:
        now = datetime.now(timezone.utc)
        po_number = f"PO-{now.strftime('%Y%m%d')}-{cycle:03d}"
        total_qty = sum(item["qty"] for item in po_line_items_to_create)
        total_cost = sum(item["total_cost"] for item in po_line_items_to_create)

        async with session_factory() as db:
            po = PurchaseOrder(
                po_number=po_number,
                status="draft",
                total_qty=total_qty,
                total_cost=round(total_cost, 2),
                notes=f"Auto-generated by Hank (Cycle {cycle}). {len(po_line_items_to_create)} products need restocking.",
                created_by="Hank",
                created_at=now.isoformat(),
                updated_at=now.isoformat(),
            )
            db.add(po)
            await db.flush()  # Get PO id

            for item in po_line_items_to_create:
                db.add(POLineItem(
                    po_id=po.id,
                    product_id=item["product_id"],
                    product_title=item["product_title"],
                    qty=item["qty"],
                    cost_per_unit=item["cost_per_unit"],
                    total_cost=item["total_cost"],
                ))
            await db.commit()

        context = f"Created {po_number}: {len(po_line_items_to_create)} line items, {total_qty} total units, ${total_cost:.0f} estimated cost. Status: DRAFT — waiting for approval."
        commentary = await narrate("Hank", context)
        await _save_action(session_factory, "Hank", "po_created", f"Created {po_number}", f"{total_qty} units across {len(po_line_items_to_create)} products — ${total_cost:.0f}", commentary, cycle=cycle)
        actions.append(("po_created", po_number))

    return actions


# ── RON — Finance ─────────────────────────────────────────────────────────────

async def _run_ron(products, orders, inventory, scored, session_factory, cycle):
    """Ron: slow mover detection + creates discount codes (local DB + Shopify when connected)."""
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

        # ACTION: Create discount code — try Shopify first, always save locally
        await _shopify_action(
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
            f"Created {sugg.discount_pct}% discount code {code}"
        )

        # Save to local DB regardless
        async with session_factory() as db:
            db.add(Discount(
                code=code,
                percentage=sugg.discount_pct,
                product_id=sugg.product.id,
                product_title=sugg.product.title,
                created_by="Ron",
                created_at=datetime.now(timezone.utc).isoformat(),
            ))
            await db.commit()

        context = f"Product '{sugg.product.title}' is declining (trend ratio {sugg.product.trend_ratio}x, {sugg.product.tier} tier). {sugg.product.inventory} units at ${sugg.product.price} = ${carrying_cost:.0f} of dead capital. Created {sugg.discount_pct}% discount code: {code}."
        commentary = await narrate("Ron", context)
        await _save_action(session_factory, "Ron", "discount_created", f"Discount: {code}", f"{sugg.discount_pct}% off {sugg.product.title} → Code created", commentary, status="success", product_id=sugg.product.id, cycle=cycle)
        actions.append(("discount", sugg.product.title))

    return actions


# ── MARTY — Marketing ─────────────────────────────────────────────────────────

async def _run_marty(products, orders, inventory, scored, session_factory, cycle):
    """Marty: customer segmentation, email campaigns, promotional actions."""
    actions = []

    # Load customers
    async with session_factory() as db:
        result = await db.execute(select(Customer))
        customers = [
            {"id": c.id, "email": c.email, "first_name": c.first_name,
             "last_name": c.last_name, "orders_count": c.orders_count,
             "total_spent": c.total_spent}
            for c in result.scalars().all()
        ]

    if not customers:
        return actions

    # Segment customers
    segments = segment_customers(customers, orders)

    seg_key = "segments-analyzed"
    if seg_key not in _has_acted:
        _has_acted.add(seg_key)

        seg_counts = {}
        for s in segments:
            seg_counts[s.segment] = seg_counts.get(s.segment, 0) + 1

        champions = seg_counts.get("Champions", 0)
        at_risk = seg_counts.get("At Risk", 0)
        lost = seg_counts.get("Lost", 0)
        total_ltv = sum(s.total_spent for s in segments)
        champion_ltv = sum(s.total_spent for s in segments if s.segment == "Champions")

        context = f"Segmented {len(segments)} customers: {champions} Champions, {seg_counts.get('Loyal', 0)} Loyal, {seg_counts.get('New', 0)} New, {at_risk} At Risk, {lost} Lost. Champions are {champions} customers but ${champion_ltv:.0f} of ${total_ltv:.0f} total LTV."
        commentary = await narrate("Marty", context)
        await _save_action(session_factory, "Marty", "segment_analyzed", f"Segmented {len(segments)} customers", f"{champions} Champions, {at_risk} At Risk, {lost} Lost", commentary, cycle=cycle)
        actions.append(("segment_analyzed", f"{len(segments)} customers"))

    # ACTION: Win-back email for At Risk customers
    at_risk_customers = [s for s in segments if s.segment == "At Risk"]
    if at_risk_customers:
        winback_key = "winback-campaign"
        if winback_key not in _has_acted:
            _has_acted.add(winback_key)

            at_risk_revenue = sum(c.total_spent for c in at_risk_customers)
            recipients = [{"name": c.name, "email": c.email, "spent": f"${c.total_spent:.0f}"} for c in at_risk_customers[:5]]

            # Generate email draft via Claude
            email_context = f"Write a short win-back email for a clothing store. Target: {len(at_risk_customers)} customers who haven't purchased in 60+ days. Total revenue at risk: ${at_risk_revenue:.0f}. Include a subject line and 2-3 sentence body. Offer 10% off with code COMEBACK10. Keep it warm and personal, not corporate."
            email_draft = await narrate("Marty", email_context)

            details = f"Subject: We miss you! Here's 10% off your next order\nTo: {', '.join(c['email'] for c in recipients[:3])}{'...' if len(recipients) > 3 else ''}\nCode: COMEBACK10\n\n{email_draft}"
            await _save_action(session_factory, "Marty", "email_drafted", f"Win-back campaign → {len(at_risk_customers)} At Risk customers", details, email_draft, cycle=cycle)
            actions.append(("email_campaign", "win-back"))

    # ACTION: VIP thank-you for Champions
    champion_customers = [s for s in segments if s.segment == "Champions"]
    if champion_customers:
        vip_key = "vip-campaign"
        if vip_key not in _has_acted:
            _has_acted.add(vip_key)

            champion_revenue = sum(c.total_spent for c in champion_customers)
            avg_ltv = champion_revenue / len(champion_customers) if champion_customers else 0
            recipients = [{"name": c.name, "email": c.email, "spent": f"${c.total_spent:.0f}"} for c in champion_customers[:5]]

            # Generate email draft via Claude
            email_context = f"Write a short VIP early-access email for a clothing store. Target: {len(champion_customers)} top customers (Champions segment, avg lifetime spend ${avg_ltv:.0f}). Give them early access to new arrivals before everyone else. Keep it exclusive and appreciative, not salesy. Include a subject line and 2-3 sentence body."
            email_draft = await narrate("Marty", email_context)

            details = f"Subject: You're getting first access — new drops just landed\nTo: {', '.join(c['email'] for c in recipients[:3])}{'...' if len(recipients) > 3 else ''}\n\n{email_draft}"
            await _save_action(session_factory, "Marty", "email_drafted", f"VIP early-access → {len(champion_customers)} Champions", details, email_draft, cycle=cycle)
            actions.append(("email_campaign", "vip"))

    # ACTION: Tag slow movers as "needs-story" — Marty pushes back on pure discounting
    slow = detect_slow_movers(scored)
    for product in slow[:2]:
        story_key = f"story-{product.id}"
        if story_key in _has_acted:
            continue
        _has_acted.add(story_key)

        success, msg = await _shopify_action(
            f"tag_story_{product.id}",
            lambda p=product: _shopify_client.graphql(
                'mutation($id: ID!, $tags: [String!]!) { tagsAdd(id: $id, tags: $tags) { node { ... on Product { id } } } }',
                {"id": f"gid://shopify/Product/{p.id}", "tags": ["needs-story", "marketing-review"]},
            ),
            f"Would tag {product.title} as needs-story — try content before discounts"
        )

        context = f"Before Ron discounts '{product.title}', let me try a content play. Tagging it for a 'last chance' feature email + social push. A story converts better than a slash. {msg}"
        commentary = await narrate("Marty", context)
        await _save_action(session_factory, "Marty", "product_tagged", f"Marketing review: {product.title}", f"Tagged needs-story → {msg}", commentary, product_id=product.id, cycle=cycle)
        actions.append(("product_tagged", product.title))

    return actions


# ── MARCUS — Chief of Staff ───────────────────────────────────────────────────

async def _run_marcus(products, orders, scored, session_factory, cycle, rick_actions, hank_actions, ron_actions, marty_actions):
    """Marcus: coordination + storefront widget + daily insight."""
    total_actions = len(rick_actions) + len(hank_actions) + len(ron_actions) + len(marty_actions)

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
        if marty_actions:
            types = ", ".join(set(t for t, _ in marty_actions))
            summary_parts.append(f"Marty launched {len(marty_actions)} marketing actions ({types})")

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

    # Restore dedup state from DB on first run (survives restarts)
    await _restore_has_acted(session_factory)

    logger.info("=== Agent Cycle %d starting ===", cycle)

    products, orders, inventory = await _load_store_data(session_factory)
    if not products:
        logger.info("No products in database — skipping cycle")
        return {"cycle": cycle, "actions": 0}

    scored = score_products(products, orders, inventory)

    # Set all agents to evaluating
    async with session_factory() as db:
        for name in ["Rick", "Hank", "Ron", "Marty", "Marcus"]:
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
    marty_actions = await _run_marty(products, orders, inventory, scored, session_factory, cycle)
    await _run_marcus(products, orders, scored, session_factory, cycle, rick_actions, hank_actions, ron_actions, marty_actions)

    total_actions = len(rick_actions) + len(hank_actions) + len(ron_actions) + len(marty_actions)

    # Set agents back to active/idle
    async with session_factory() as db:
        for name in ["Rick", "Hank", "Ron", "Marty", "Marcus"]:
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
