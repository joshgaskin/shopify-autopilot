"""Analytics endpoints — computed from local SQLite data."""
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Order

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _parse_period(period: str) -> int:
    """Convert period string to number of days."""
    mapping = {"7d": 7, "30d": 30, "90d": 90}
    return mapping.get(period, 30)


def _parse_date(date_str: str) -> datetime | None:
    """Parse an ISO date string, returning None on failure."""
    if not date_str:
        return None
    try:
        # Handle various ISO formats
        cleaned = date_str.replace("Z", "+00:00")
        return datetime.fromisoformat(cleaned)
    except (ValueError, AttributeError):
        return None


@router.get("/revenue")
async def get_revenue(
    period: str = Query("30d", description="7d, 30d, or 90d"),
    db: AsyncSession = Depends(get_db),
):
    """Revenue time series for the given period."""
    days = _parse_period(period)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    cutoff_str = cutoff.isoformat()

    result = await db.execute(
        select(Order).where(Order.processed_at >= cutoff_str)
    )
    orders = result.scalars().all()

    # Group by date
    daily: dict[str, dict] = defaultdict(lambda: {"revenue": 0.0, "orders": 0})

    for order in orders:
        dt = _parse_date(order.processed_at)
        if not dt:
            continue
        date_key = dt.strftime("%Y-%m-%d")
        daily[date_key]["revenue"] += order.total_price
        daily[date_key]["orders"] += 1

    # Build series for all days in the period
    series = []
    for i in range(days):
        date = (cutoff + timedelta(days=i + 1)).strftime("%Y-%m-%d")
        entry = daily.get(date, {"revenue": 0.0, "orders": 0})
        aov = entry["revenue"] / entry["orders"] if entry["orders"] > 0 else 0.0
        series.append({
            "date": date,
            "revenue": round(entry["revenue"], 2),
            "orders": entry["orders"],
            "aov": round(aov, 2),
        })

    return {"series": series}


@router.get("/top-products")
async def get_top_products(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Top products by revenue, computed from order line items."""
    result = await db.execute(select(Order))
    orders = result.scalars().all()

    product_stats: dict[str, dict] = {}

    for order in orders:
        line_items = order.line_items or []
        for item in line_items:
            pid = item.get("product_id") or "unknown"
            if pid not in product_stats:
                product_stats[pid] = {
                    "id": pid,
                    "title": item.get("title", "Unknown"),
                    "revenue": 0.0,
                    "units_sold": 0,
                }
            product_stats[pid]["revenue"] += float(item.get("amount", 0))
            product_stats[pid]["units_sold"] += int(item.get("quantity", 0))

    # Sort by revenue descending
    sorted_products = sorted(
        product_stats.values(), key=lambda x: x["revenue"], reverse=True
    )[:limit]

    for p in sorted_products:
        p["revenue"] = round(p["revenue"], 2)

    return {"products": sorted_products}


@router.get("/hourly-patterns")
async def get_hourly_patterns(db: AsyncSession = Depends(get_db)):
    """Average orders and revenue by hour of day."""
    result = await db.execute(select(Order))
    orders = result.scalars().all()

    # Collect data per hour per day
    hourly_data: dict[int, dict] = {h: {"total_orders": 0, "total_revenue": 0.0, "days": set()} for h in range(24)}

    for order in orders:
        dt = _parse_date(order.processed_at)
        if not dt:
            continue
        hour = dt.hour
        date_key = dt.strftime("%Y-%m-%d")
        hourly_data[hour]["total_orders"] += 1
        hourly_data[hour]["total_revenue"] += order.total_price
        hourly_data[hour]["days"].add(date_key)

    hours = []
    for h in range(24):
        data = hourly_data[h]
        num_days = max(len(data["days"]), 1)
        hours.append({
            "hour": h,
            "avg_orders": round(data["total_orders"] / num_days, 2),
            "avg_revenue": round(data["total_revenue"] / num_days, 2),
        })

    return {"hours": hours}


@router.get("/customer-cohorts")
async def get_customer_cohorts(db: AsyncSession = Depends(get_db)):
    """Weekly customer cohorts with retention rates."""
    result = await db.execute(select(Order).order_by(Order.processed_at.asc()))
    orders = result.scalars().all()

    # Group customers by the week of their first order
    customer_first_order: dict[str, datetime] = {}
    customer_order_weeks: dict[str, set[str]] = defaultdict(set)

    for order in orders:
        cid = order.customer_id or order.customer_email or "anonymous"
        dt = _parse_date(order.processed_at)
        if not dt:
            continue

        # Track first order date
        if cid not in customer_first_order or dt < customer_first_order[cid]:
            customer_first_order[cid] = dt

        # Track all weeks this customer ordered
        week_key = dt.strftime("%Y-W%W")
        customer_order_weeks[cid].add(week_key)

    # Build cohorts by week of first order
    cohorts_data: dict[str, list[str]] = defaultdict(list)
    for cid, first_dt in customer_first_order.items():
        week_key = first_dt.strftime("%Y-W%W")
        cohorts_data[week_key].append(cid)

    # Calculate retention for each cohort
    sorted_weeks = sorted(cohorts_data.keys())
    cohorts = []
    for week in sorted_weeks[-12:]:  # Last 12 weeks max
        customers = cohorts_data[week]
        retention = []
        for offset in range(min(8, len(sorted_weeks) - sorted_weeks.index(week))):
            target_week_idx = sorted_weeks.index(week) + offset
            if target_week_idx >= len(sorted_weeks):
                break
            target_week = sorted_weeks[target_week_idx]
            active = sum(
                1 for cid in customers
                if target_week in customer_order_weeks[cid]
            )
            rate = round(active / len(customers) * 100, 1) if customers else 0
            retention.append(rate)

        cohorts.append({
            "week": week,
            "customers": len(customers),
            "retention_rates": retention,
        })

    return {"cohorts": cohorts}
