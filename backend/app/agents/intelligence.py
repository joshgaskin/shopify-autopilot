"""
Intelligence layer — pure math functions for scoring, detection, and segmentation.
Server-side port of frontend/lib/intelligence.ts.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone


@dataclass
class ScoredProduct:
    id: str
    title: str
    handle: str
    status: str
    price: float
    inventory: int
    score: int
    tier: str  # Core, Strong, Slow, Exit
    velocity: float
    days_left: int
    trend: str  # growing, stable, declining
    trend_ratio: float
    revenue_total: float
    image: str | None = None


@dataclass
class HealthIssue:
    product_id: str
    product_title: str
    issue: str
    severity: str  # critical, warning, info


@dataclass
class DiscountSuggestion:
    product: ScoredProduct
    discount_pct: int


def _power_scale(value: float, max_value: float) -> int:
    if value <= 0 or max_value <= 0:
        return 0
    return min(100, round(math.pow(value / max_value, 0.25) * 100))


def _get_tier(score: int) -> str:
    if score >= 70:
        return "Core"
    if score >= 55:
        return "Strong"
    if score >= 40:
        return "Slow"
    return "Exit"


def score_products(products: list[dict], orders: list[dict], inventory: list[dict]) -> list[ScoredProduct]:
    """Score all products by revenue, velocity, stock health, and trend."""
    now = datetime.now(timezone.utc)
    seven_days_ago = now - timedelta(days=7)
    fourteen_days_ago = now - timedelta(days=14)

    # Aggregate sales per product
    product_sales: dict[str, dict] = {}
    for order in orders:
        if order.get("financial_status") == "refunded":
            continue
        order_time_str = order.get("processed_at") or order.get("created_at", "")
        try:
            order_time = datetime.fromisoformat(order_time_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            continue

        for item in (order.get("line_items") or []):
            # Match by title
            matched_product = None
            for p in products:
                if p.get("title") == item.get("title"):
                    matched_product = p
                    break
                variants = p.get("variants") or []
                if isinstance(variants, list):
                    for v in variants:
                        if isinstance(v, dict) and v.get("title") == item.get("variant_title"):
                            matched_product = p
                            break
                if matched_product:
                    break
            if not matched_product:
                continue

            pid = matched_product["id"]
            qty = item.get("quantity", 0)
            price = item.get("price", 0)
            if isinstance(price, str):
                price = float(price)

            sales = product_sales.setdefault(pid, {"units": 0, "revenue": 0.0, "recent": 0, "prior": 0})
            sales["units"] += qty
            sales["revenue"] += price * qty
            if order_time >= seven_days_ago:
                sales["recent"] += qty
            elif order_time >= fourteen_days_ago:
                sales["prior"] += qty

    # Inventory lookup
    inv_map: dict[str, int] = {}
    for level in inventory:
        pid = level.get("product_id", "")
        inv_map[pid] = inv_map.get(pid, 0) + level.get("quantity", 0)
    for p in products:
        if p["id"] not in inv_map:
            inv_map[p["id"]] = p.get("inventory_total", 0)

    # Max values for normalization
    max_revenue = max((s["revenue"] for s in product_sales.values()), default=1) or 1
    max_velocity = max((s["recent"] / 7 for s in product_sales.values()), default=1) or 1

    scored: list[ScoredProduct] = []
    for p in products:
        pid = p["id"]
        sales = product_sales.get(pid, {"units": 0, "revenue": 0.0, "recent": 0, "prior": 0})
        stock = inv_map.get(pid, 0)

        velocity = round(sales["recent"] / 7, 2)
        days_left = round(stock / velocity) if velocity > 0 else (999 if stock > 0 else 0)

        # Trend
        trend = "stable"
        trend_ratio = 1.0
        if sales["prior"] > 0:
            trend_ratio = round(sales["recent"] / sales["prior"], 2)
            if trend_ratio > 1.15:
                trend = "growing"
            elif trend_ratio < 0.85:
                trend = "declining"
        elif sales["recent"] > 0:
            trend = "growing"
            trend_ratio = 2.0

        # Score components
        rev_score = _power_scale(sales["revenue"], max_revenue)
        vel_score = _power_scale(velocity, max_velocity)
        stock_score = 0 if days_left <= 0 else 20 if days_left <= 3 else 50 if days_left <= 7 else 70 if days_left <= 14 else 90
        trend_score = min(100, max(0, round(50 + (trend_ratio - 1) * 25)))

        composite = round(rev_score * 0.3 + vel_score * 0.3 + stock_score * 0.2 + trend_score * 0.2)
        tier = _get_tier(composite)

        scored.append(ScoredProduct(
            id=pid, title=p.get("title", ""), handle=p.get("handle", ""),
            status=p.get("status", "active"), price=p.get("price_min", 0),
            inventory=stock, score=composite, tier=tier, velocity=velocity,
            days_left=days_left, trend=trend, trend_ratio=trend_ratio,
            revenue_total=round(sales["revenue"], 2),
            image=p.get("featured_image_url"),
        ))

    scored.sort(key=lambda s: (-1 if s.days_left <= 7 else 0, -s.score))
    return scored


def detect_stockout_risk(scored: list[ScoredProduct]) -> list[ScoredProduct]:
    return [p for p in scored if 0 < p.days_left <= 3 and p.velocity > 0]


def detect_slow_movers(scored: list[ScoredProduct]) -> list[ScoredProduct]:
    return [p for p in scored if p.trend == "declining" and p.inventory > 0 and p.days_left > 14 and p.tier != "Core"]


def check_product_health(products: list[dict], inventory: list[dict]) -> list[HealthIssue]:
    issues: list[HealthIssue] = []
    for p in products:
        if not p.get("featured_image_url"):
            issues.append(HealthIssue(p["id"], p.get("title", ""), "Missing product image", "warning"))
        if p.get("status") == "active" and p.get("inventory_total", 0) <= 0:
            issues.append(HealthIssue(p["id"], p.get("title", ""), "Active product with zero stock", "critical"))
        if p.get("status") == "draft" and p.get("inventory_total", 0) > 0:
            issues.append(HealthIssue(p["id"], p.get("title", ""), "Draft product has stock — consider publishing", "info"))
        if p.get("price_min", 0) <= 0 and p.get("status") == "active":
            issues.append(HealthIssue(p["id"], p.get("title", ""), "Active product with $0 price", "critical"))
    return issues


def suggest_discounts(slow_movers: list[ScoredProduct]) -> list[DiscountSuggestion]:
    suggestions: list[DiscountSuggestion] = []
    for product in slow_movers:
        pct = 10
        if product.trend_ratio < 0.5:
            pct = 30
        elif product.trend_ratio < 0.7:
            pct = 20
        elif product.trend_ratio < 0.85:
            pct = 15
        if product.tier == "Exit":
            pct = min(40, pct + 10)
        suggestions.append(DiscountSuggestion(product=product, discount_pct=pct))
    return suggestions


# ── Customer Segmentation (RFM) ──────────────────────────────────────────────

@dataclass
class SegmentedCustomer:
    id: str
    email: str
    name: str
    segment: str  # Champions, Loyal, At Risk, New, Lost
    rfm_score: float
    order_count: int
    total_spent: float
    days_since_last_order: int


def segment_customers(customers: list[dict], orders: list[dict]) -> list[SegmentedCustomer]:
    """RFM segmentation of customers."""
    now = datetime.now(timezone.utc)

    # Aggregate orders per customer
    customer_orders: dict[str, dict] = {}
    for order in orders:
        cid = order.get("customer_id")
        if not cid or order.get("financial_status") == "refunded":
            continue
        agg = customer_orders.setdefault(cid, {"last_at": 0, "count": 0, "spent": 0.0})
        try:
            ts = datetime.fromisoformat((order.get("processed_at") or order.get("created_at", "")).replace("Z", "+00:00")).timestamp()
        except (ValueError, AttributeError):
            ts = 0
        agg["last_at"] = max(agg["last_at"], ts)
        agg["count"] += 1
        agg["spent"] += order.get("total_price", 0)

    rfm_data = []
    for c in customers:
        agg = customer_orders.get(c["id"], {"last_at": 0, "count": c.get("orders_count", 0), "spent": c.get("total_spent", 0.0)})
        days_since = int((now.timestamp() - agg["last_at"]) / 86400) if agg["last_at"] > 0 else 999
        rfm_data.append({
            "customer": c,
            "days_since": days_since,
            "count": agg["count"],
            "spent": agg["spent"],
        })

    # Simple quintile scoring
    def score(values, val, invert=False):
        if not values:
            return 3
        sorted_v = sorted(values)
        idx = next((i for i, v in enumerate(sorted_v) if v >= val), len(sorted_v))
        pct = idx / len(sorted_v)
        s = min(5, max(1, math.ceil(pct * 5)))
        return 6 - s if invert else s

    all_days = [d["days_since"] for d in rfm_data]
    all_counts = [d["count"] for d in rfm_data]
    all_spent = [d["spent"] for d in rfm_data]

    result: list[SegmentedCustomer] = []
    for d in rfm_data:
        r = score(all_days, d["days_since"], invert=True)
        f = score(all_counts, d["count"])
        m = score(all_spent, d["spent"])
        rfm = round((r + f + m) / 3, 1)

        if r >= 4 and f >= 4 and m >= 4:
            segment = "Champions"
        elif f >= 3 and m >= 3 and r >= 3:
            segment = "Loyal"
        elif r <= 2 and f >= 3:
            segment = "At Risk"
        elif r >= 4 and f <= 2:
            segment = "New"
        else:
            segment = "Lost"

        c = d["customer"]
        result.append(SegmentedCustomer(
            id=c["id"],
            email=c.get("email", ""),
            name=f"{c.get('first_name', '')} {c.get('last_name', '')}".strip(),
            segment=segment,
            rfm_score=rfm,
            order_count=d["count"],
            total_spent=round(d["spent"], 2),
            days_since_last_order=d["days_since"],
        ))

    return result
