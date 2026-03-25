"""Order endpoints."""
import math

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Order

router = APIRouter(tags=["orders"])


@router.get("/orders")
async def list_orders(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=250),
    status: str = Query("", description="Filter by financial_status"),
    since: str = Query("", description="Filter orders after this ISO date"),
    db: AsyncSession = Depends(get_db),
):
    """List orders with pagination and filters."""
    query = select(Order)
    count_query = select(func.count()).select_from(Order)

    if status:
        query = query.where(Order.financial_status == status.lower())
        count_query = count_query.where(Order.financial_status == status.lower())

    if since:
        query = query.where(Order.processed_at >= since)
        count_query = count_query.where(Order.processed_at >= since)

    total = (await db.execute(count_query)).scalar() or 0
    pages = math.ceil(total / limit) if total > 0 else 1
    offset = (page - 1) * limit

    result = await db.execute(
        query.order_by(Order.processed_at.desc()).offset(offset).limit(limit)
    )
    orders = result.scalars().all()

    return {
        "data": [_order_to_dict(o) for o in orders],
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages,
    }


@router.get("/orders/{order_id:path}")
async def get_order(
    order_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a single order by ID (Shopify GID)."""
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return _order_to_dict(order)


@router.post("/orders/draft")
async def create_draft_order(request: Request):
    """Create a draft order on Shopify."""
    shopify = request.app.state.shopify
    body = await request.json()
    line_items = body.get("line_items", [])

    result = await shopify.create_order(
        line_items=line_items,
        customer=body.get("customer"),
        discount_code=body.get("discount_code"),
        tags=body.get("tags", "hackathon"),
    )
    return result


def _order_to_dict(o: Order) -> dict:
    return {
        "id": o.id,
        "order_number": o.order_number,
        "total_price": o.total_price,
        "subtotal_price": o.subtotal_price,
        "total_discounts": o.total_discounts,
        "total_tax": o.total_tax,
        "currency": o.currency,
        "financial_status": o.financial_status,
        "fulfillment_status": o.fulfillment_status,
        "line_items": o.line_items or [],
        "customer_id": o.customer_id,
        "customer_email": o.customer_email,
        "customer_name": o.customer_name,
        "discount_codes": o.discount_codes or [],
        "landing_site": o.landing_site,
        "referring_site": o.referring_site,
        "processed_at": o.processed_at,
        "created_at": o.created_at,
        "is_simulated": o.is_simulated,
    }
